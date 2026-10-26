"""Brute Genius MCP Server.

Exhaustive combinatorial search on a fleet of accelerators.
One mode only: try every combination known to man.

Safety rules (enforced):
  - plan() refuses if estimated cost > max_cost_usd
  - launch() re-checks balance before dispatching
  - kill() always available and stops every node for a plan
  - Hard caps: MAX_NODES = 64, MAX_COMBINATIONS = 10**9
  - Objective functions are looked up by name from a registry only
  - Never write to stdout in stdio mode; use ctx logging / stderr
"""
from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from fastmcp import Context, FastMCP

import enumerator
import objectives
import xpu
from mock_provider import MockProvider

# ─── Hard safety limits ────────────────────────────────────────────────────
MAX_NODES = 64
MAX_COMBINATIONS = enumerator.MAX_COMBINATIONS

# Rough planning heuristic: combinations scored per node per minute.
# Tune against real objective cost before trusting the ceiling in production.
COMBOS_PER_NODE_PER_MINUTE = 100_000

mcp = FastMCP(
    "brute-genius",
    instructions=(
        "Brute Genius performs exhaustive Cartesian search over a discrete "
        "space on a fleet of accelerators. Always call brute_genius_plan "
        "first and respect the cost ceiling. Never launch without a plan_id."
    ),
)

provider = MockProvider(balance=25.0)

# In-memory plan store. Keys are plan_id strings.
_plans: dict[str, dict[str, Any]] = {}


def _log(msg: str) -> None:
    """Write to stderr so we never pollute stdout in stdio transport."""
    print(msg, file=sys.stderr, flush=True)


# ─── TOOLS ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def brute_genius_plan(
    space: dict[str, list[Any]],
    objective: str,
    max_cost_usd: float,
    chip: str = "h100",
    nodes: int = 1,
) -> dict[str, Any]:
    """Enumerate the full Cartesian product and return a cost estimate.

    Does NOT execute anything. Refuses to return a plan_id when the
    estimated cost exceeds max_cost_usd.

    Args:
        space: Mapping of axis name → list of discrete values.
        objective: Name of a registered objective (see objectives registry).
        max_cost_usd: Hard ceiling in USD. Plan is refused above this.
        chip: Accelerator type (h100, a100, l40s, cpu).
        nodes: Number of nodes to shard across (1–64).
    """
    # Validate objective name early (raises KeyError if unknown)
    objectives.get(objective)

    total = enumerator.count(space)
    if total == 0:
        raise ValueError("Search space is empty (at least one axis has no values)")
    if total > MAX_COMBINATIONS:
        raise ValueError(
            f"Space has {total:,} combinations, exceeds hard limit of "
            f"{MAX_COMBINATIONS:,}"
        )
    if nodes < 1:
        raise ValueError("nodes must be >= 1")
    if nodes > MAX_NODES:
        raise ValueError(f"nodes={nodes} exceeds MAX_NODES={MAX_NODES}")

    chip = chip.lower()
    rate = provider.hourly_rate(chip)
    # Wall-clock estimate in minutes, then convert to cost
    est_minutes = max(total / (nodes * COMBOS_PER_NODE_PER_MINUTE), 0.01)
    est_hours = est_minutes / 60.0
    est_cost = est_hours * rate * nodes

    if est_cost > max_cost_usd:
        raise ValueError(
            f"Estimated cost ${est_cost:.4f} exceeds ceiling "
            f"${max_cost_usd:.2f}. Reduce space, increase nodes, "
            f"or raise max_cost_usd."
        )

    plan_id = str(uuid.uuid4())
    _plans[plan_id] = {
        "plan_id": plan_id,
        "space": space,
        "objective": objective,
        "chip": chip,
        "nodes": nodes,
        "total": total,
        "est_cost_usd": round(est_cost, 6),
        "est_minutes": round(est_minutes, 4),
        "state": "planned",
        "shards": [],          # filled on launch
        "results": [],         # list of (combo, score)
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "combinations_evaluated": 0,
        "best_so_far": None,
        "device_used": None,
    }

    return {
        "plan_id": plan_id,
        "total_combinations": total,
        "estimated_cost_usd": round(est_cost, 4),
        "estimated_minutes": round(est_minutes, 4),
        "chip": chip,
        "nodes": nodes,
        "state": "planned",
        "objective": objective,
    }


@mcp.tool()
async def brute_genius_launch(
    plan_id: str,
    ctx: Context,
    chip: str | None = None,
    nodes: int | None = None,
) -> dict[str, Any]:
    """Shard the enumerated space and score every combination.

    Re-checks balance and cost ceiling before any work is dispatched.
    Streams progress via ctx.report_progress and logs via ctx.info.

    Args:
        plan_id: Identifier returned by brute_genius_plan.
        chip: Optional override of the chip chosen at plan time.
        nodes: Optional override of the node count chosen at plan time.
    """
    plan = _plans.get(plan_id)
    if plan is None:
        raise ValueError(f"Unknown plan_id '{plan_id}'")
    if plan["state"] not in ("planned", "killed"):
        raise ValueError(
            f"Plan '{plan_id}' is in state '{plan['state']}' and cannot be launched"
        )

    # Allow late overrides
    if chip is not None:
        plan["chip"] = chip.lower()
    if nodes is not None:
        if nodes < 1 or nodes > MAX_NODES:
            raise ValueError(f"nodes must be 1–{MAX_NODES}")
        plan["nodes"] = nodes

    await ctx.info(
        f"Launching plan {plan_id}: {plan['total']:,} combinations on "
        f"{plan['nodes']}×{plan['chip']} (est. ${plan['est_cost_usd']:.4f})"
    )

    # Safety: re-check balance
    balance = await provider.get_balance()
    if balance <= 0:
        raise RuntimeError(
            "Account balance is $0. Top up before launching. "
            "Use the provider payment link."
        )
    if plan["est_cost_usd"] > balance:
        raise RuntimeError(
            f"Estimated cost ${plan['est_cost_usd']:.4f} exceeds "
            f"current balance ${balance:.2f}"
        )

    # Provision simulated nodes
    node_names: list[str] = []
    for i in range(plan["nodes"]):
        name = f"{plan_id[:8]}-node-{i}"
        await provider.create_instance(name, plan["chip"])
        node_names.append(name)
        plan["shards"].append(
            {"node": name, "index": i, "status": "running", "scored": 0}
        )

    plan["state"] = "running"
    plan["started_at"] = time.time()
    plan["results"] = []
    plan["combinations_evaluated"] = 0
    plan["best_so_far"] = None

    fn = objectives.get(plan["objective"])
    device = xpu.pick_device(preferred=plan["chip"] if plan["chip"] != "cpu" else "cpu")
    plan["device_used"] = device
    await ctx.info(f"Scoring device for this run: {device}")

    shards = enumerator.shard(plan["space"], plan["nodes"])
    all_scored: list[tuple[dict[str, Any], float]] = []

    for i, shard_iter in enumerate(shards):
        if plan["state"] == "killed":
            await ctx.info(f"Plan {plan_id} killed before shard {i + 1}")
            break

        await ctx.report_progress(
            progress=i,
            total=plan["nodes"],
            message=f"Dispatching shard {i + 1}/{plan['nodes']}",
        )
        await ctx.info(f"Shard {i} → node {node_names[i]} on {device}")

        try:
            scored = xpu.batch_score(shard_iter, fn, device, plan=plan)
        except RuntimeError:
            await ctx.info(
                f"Plan {plan_id} killed mid-shard {i + 1}; "
                f"keeping {len(all_scored)} partial results"
            )
            plan["shards"][i]["status"] = "stopped"
            break

        all_scored.extend(scored)

        plan["shards"][i]["status"] = "done"
        plan["shards"][i]["scored"] = len(scored)
        plan["combinations_evaluated"] = len(all_scored)

        # Keep a running best
        if scored:
            local_best = max(scored, key=lambda x: x[1])
            if plan["best_so_far"] is None or local_best[1] > plan["best_so_far"]["score"]:
                plan["best_so_far"] = {"combo": local_best[0], "score": local_best[1]}

        await ctx.report_progress(
            progress=i + 1,
            total=plan["nodes"],
            message=f"Shard {i + 1}/{plan['nodes']} complete ({len(scored)} scored)",
        )

    # Final ranking
    all_scored.sort(key=lambda x: x[1], reverse=True)
    plan["results"] = all_scored
    plan["combinations_evaluated"] = len(all_scored)

    if plan["state"] != "killed":
        plan["state"] = "done"
    plan["finished_at"] = time.time()

    # Stop billing on the simulated nodes
    for name in node_names:
        try:
            await provider.stop_instance(name)
        except Exception:
            pass

    await ctx.info(
        f"Plan {plan_id} finished with state={plan['state']}. "
        f"Evaluated {plan['combinations_evaluated']:,} combinations on {device}."
    )

    return {
        "plan_id": plan_id,
        "state": plan["state"],
        "combinations_evaluated": plan["combinations_evaluated"],
        "device": device,
        "best_so_far": plan["best_so_far"],
    }


@mcp.tool()
async def brute_genius_status(plan_id: str) -> dict[str, Any]:
    """Return live progress, shards done, combinations evaluated, best-so-far."""
    plan = _plans.get(plan_id)
    if plan is None:
        raise ValueError(f"Unknown plan_id '{plan_id}'")

    shards_done = sum(1 for s in plan["shards"] if s.get("status") == "done")
    return {
        "plan_id": plan_id,
        "state": plan["state"],
        "total_combinations": plan["total"],
        "combinations_evaluated": plan["combinations_evaluated"],
        "shards_total": plan["nodes"],
        "shards_done": shards_done,
        "best_so_far": plan["best_so_far"],
        "estimated_cost_usd": plan["est_cost_usd"],
        "device_used": plan.get("device_used"),
        "started_at": plan.get("started_at"),
        "finished_at": plan.get("finished_at"),
        "killed_at": plan.get("killed_at"),
    }


@mcp.tool()
async def brute_genius_results(
    plan_id: str,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Return the top_k highest-scoring combinations (descending score)."""
    plan = _plans.get(plan_id)
    if plan is None:
        raise ValueError(f"Unknown plan_id '{plan_id}'")
    if top_k < 1:
        raise ValueError("top_k must be >= 1")

    results = plan["results"][:top_k]
    return [{"combo": c, "score": s} for c, s in results]


@mcp.tool()
async def brute_genius_kill(plan_id: str) -> dict[str, Any]:
    """Stop every node and shard belonging to a plan. Ends billing.

    Partial results already scored are preserved. Always available even
    if the calling agent goes silent.
    """
    plan = _plans.get(plan_id)
    if plan is None:
        raise ValueError(f"Unknown plan_id '{plan_id}'")

    # Mark killed first so any in-flight launch / batch_score loop will abort
    plan["state"] = "killed"
    plan["killed_at"] = time.time()
    plan["finished_at"] = plan["killed_at"]

    # Stop every node associated with this plan
    stopped = 0
    for shard_meta in plan["shards"]:
        name = shard_meta.get("node")
        if name:
            try:
                await provider.stop_instance(name)
                shard_meta["status"] = "stopped"
                stopped += 1
            except Exception:
                pass

    return {
        "plan_id": plan_id,
        "state": "killed",
        "killed_at": plan["killed_at"],
        "nodes_stopped": stopped,
        "partial_results": len(plan["results"]),
        "combinations_evaluated": plan["combinations_evaluated"],
    }


@mcp.tool()
async def xpu_probe(chip: str = "h100") -> dict[str, Any]:
    """Detect and report available accelerators on the current machine/fleet.

    Args:
        chip: Preferred chip name (informational; detection is exhaustive).
    """
    report = xpu.detect_accelerators()
    report["requested_chip"] = chip.lower()
    report["provider_rates"] = dict(provider.RATES)
    report["balance_usd"] = await provider.get_balance()
    return report


# ─── RESOURCES ─────────────────────────────────────────────────────────────

@mcp.resource("brutegenius://plans")
def list_plans() -> dict[str, Any]:
    """List of all plans and their current states."""
    return {
        pid: {
            "state": p["state"],
            "total": p["total"],
            "objective": p["objective"],
            "chip": p["chip"],
            "nodes": p["nodes"],
            "est_cost_usd": p["est_cost_usd"],
            "combinations_evaluated": p["combinations_evaluated"],
        }
        for pid, p in _plans.items()
    }


@mcp.resource("brutegenius://plans/{plan_id}/combinations")
def plan_combinations(plan_id: str) -> dict[str, Any]:
    """Paginated view of the combination set for a plan.

    Returns the first 1 000 combinations together with total count.
    Full materialisation of multi-million spaces is intentionally avoided.
    """
    plan = _plans.get(plan_id)
    if plan is None:
        raise ValueError(f"Unknown plan_id '{plan_id}'")

    # Stream only the first page
    page: list[dict[str, Any]] = []
    for i, combo in enumerate(enumerator.cartesian(plan["space"])):
        if i >= 1000:
            break
        page.append(combo)

    return {
        "plan_id": plan_id,
        "total": plan["total"],
        "page_size": 1000,
        "returned": len(page),
        "combinations": page,
        "note": "First 1 000 combinations only. Use sharding for full evaluation.",
    }


@mcp.resource("brutegenius://hardware")
def hardware_inventory() -> dict[str, Any]:
    """Live inventory of accelerators visible to this process."""
    return xpu.detect_accelerators()


@mcp.resource("brutegenius://pricing")
def pricing() -> dict[str, Any]:
    """Current burn rate per chip type (USD per hour)."""
    return {
        "rates_usd_per_hour": dict(provider.RATES),
        "balance_usd": provider.balance,  # sync read is fine for mock
        "currency": "USD",
    }


# ─── PROMPTS ───────────────────────────────────────────────────────────────

@mcp.prompt()
def define_search() -> str:
    """Walk the user through specifying a search space, objective, and cost ceiling."""
    available = ", ".join(objectives.list_objectives())
    return f"""You are helping the user define an exhaustive combinatorial search for Brute Genius.

Collect the following information step by step:

1. **Search-space axes**  
   Ask the user for each discrete axis name and the list of values it can take.  
   Example: {{"lr": [1e-4, 3e-4, 1e-3], "batch": [16, 32, 64], "dropout": [0.0, 0.1, 0.2]}}

2. **Objective function**  
   The objective must be one of the registered names: {available}.  
   Explain briefly what each does if the user is unsure.

3. **Cost ceiling**  
   Ask for a hard maximum spend in USD (max_cost_usd).  
   Brute Genius will refuse to create a plan that exceeds this number.

4. **Optional hardware**  
   Chip type (default h100) and node count (default 1, max 64).

Once you have the answers, call the tool `brute_genius_plan` with the collected arguments and present the returned cost estimate and plan_id to the user. Do NOT call `brute_genius_launch` until the user explicitly confirms they accept the cost.
"""


@mcp.prompt()
def interpret_results() -> str:
    """Ask the LLM to explain the top results and any visible patterns."""
    return """The user has finished a Brute Genius run. You will be given the top_k results (combinations + scores).

Your job:
1. Identify the single best combination and state its score clearly.
2. Look for patterns across the top results (e.g. "every winner used lr=3e-4", "batch size 32 dominates").
3. Call out any surprising losers or plateaus.
4. Suggest one or two follow-up search spaces that would refine the current winners (narrower ranges around the best values).
5. Remind the user of the total combinations evaluated and the final state of the plan.

Be concise and quantitative. Do not invent results that were not supplied.
"""


# ─── ENTRY POINT ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Default transport is stdio (local clients). For remote/HTTP:
    #   mcp.run(transport="http", host="0.0.0.0", port=8000)
    mcp.run()
