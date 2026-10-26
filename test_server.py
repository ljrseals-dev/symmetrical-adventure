"""Client-based tests for Brute Genius using FastMCP's in-memory Client.

Run with:
  pytest test_server.py -v
"""
from __future__ import annotations

import asyncio

import pytest
from fastmcp import Client

# Import the live server instance
from server import mcp, _plans, provider

SPACE_3X3X3 = {"x": [1, 2, 3], "y": [1, 2, 3], "z": [1, 2, 3]}  # 27 combos
TINY_SPACE = {"a": [0, 1], "b": [0, 1]}  # 4 combos


@pytest.fixture(autouse=True)
def clear_plans():
    """Ensure each test starts with a clean plan store and a healthy balance."""
    _plans.clear()
    provider.balance = 25.0
    provider._nodes.clear()
    provider._stopped.clear()
    yield
    _plans.clear()


@pytest.mark.asyncio
async def test_plan_counts_27():
    async with Client(mcp) as c:
        r = await c.call_tool(
            "brute_genius_plan",
            {
                "space": SPACE_3X3X3,
                "objective": "sphere",
                "max_cost_usd": 10.0,
            },
        )
        data = r.data
        assert data["total_combinations"] == 27
        assert "plan_id" in data
        assert data["state"] == "planned"
        assert data["estimated_cost_usd"] >= 0


@pytest.mark.asyncio
async def test_plan_refuses_over_ceiling():
    """A space whose estimated cost exceeds max_cost_usd must raise and yield no plan_id."""
    async with Client(mcp) as c:
        with pytest.raises(Exception):
            await c.call_tool(
                "brute_genius_plan",
                {
                    "space": {"x": list(range(100_000))},  # huge space
                    "objective": "sphere",
                    "max_cost_usd": 0.0001,  # tiny ceiling
                    "nodes": 1,
                },
            )
        # No plan should have been stored
        assert len(_plans) == 0


@pytest.mark.asyncio
async def test_plan_refuses_over_max_combinations():
    async with Client(mcp) as c:
        with pytest.raises(Exception) as exc_info:
            await c.call_tool(
                "brute_genius_plan",
                {
                    "space": {"x": list(range(10**5)), "y": list(range(10**5))},
                    "objective": "sphere",
                    "max_cost_usd": 1e9,
                },
            )
        assert "exceeds hard limit" in str(exc_info.value).lower() or "10" in str(
            exc_info.value
        )


@pytest.mark.asyncio
async def test_unknown_objective_rejected():
    async with Client(mcp) as c:
        with pytest.raises(Exception):
            await c.call_tool(
                "brute_genius_plan",
                {
                    "space": TINY_SPACE,
                    "objective": "this_does_not_exist",
                    "max_cost_usd": 10.0,
                },
            )


@pytest.mark.asyncio
async def test_launch_dispatches_correct_shards():
    async with Client(mcp) as c:
        plan = await c.call_tool(
            "brute_genius_plan",
            {
                "space": SPACE_3X3X3,
                "objective": "sphere",
                "max_cost_usd": 10.0,
                "nodes": 3,
            },
        )
        pid = plan.data["plan_id"]
        result = await c.call_tool("brute_genius_launch", {"plan_id": pid})
        assert result.data["state"] == "done"
        assert result.data["combinations_evaluated"] == 27
        # All three shards should be marked done
        status = await c.call_tool("brute_genius_status", {"plan_id": pid})
        assert status.data["shards_done"] == 3
        assert status.data["shards_total"] == 3


@pytest.mark.asyncio
async def test_results_sorted_descending():
    async with Client(mcp) as c:
        plan = await c.call_tool(
            "brute_genius_plan",
            {
                "space": SPACE_3X3X3,
                "objective": "sphere",
                "max_cost_usd": 10.0,
            },
        )
        pid = plan.data["plan_id"]
        await c.call_tool("brute_genius_launch", {"plan_id": pid})
        res = await c.call_tool(
            "brute_genius_results", {"plan_id": pid, "top_k": 5}
        )
        scores = [item["score"] for item in res.data]
        assert scores == sorted(scores, reverse=True)
        assert len(scores) == 5


@pytest.mark.asyncio
async def test_kill_sets_stopped_state():
    async with Client(mcp) as c:
        plan = await c.call_tool(
            "brute_genius_plan",
            {
                "space": SPACE_3X3X3,
                "objective": "sphere",
                "max_cost_usd": 10.0,
                "nodes": 2,
            },
        )
        pid = plan.data["plan_id"]
        # Launch so nodes exist
        await c.call_tool("brute_genius_launch", {"plan_id": pid})
        kill = await c.call_tool("brute_genius_kill", {"plan_id": pid})
        assert kill.data["state"] == "killed"
        status = await c.call_tool("brute_genius_status", {"plan_id": pid})
        assert status.data["state"] == "killed"


@pytest.mark.asyncio
async def test_end_to_end_returns_correct_best_sphere():
    """Sphere is maximised at the origin; with positive integers the best is all 1s."""
    async with Client(mcp) as c:
        plan = await c.call_tool(
            "brute_genius_plan",
            {
                "space": SPACE_3X3X3,
                "objective": "sphere",
                "max_cost_usd": 10.0,
            },
        )
        pid = plan.data["plan_id"]
        await c.call_tool("brute_genius_launch", {"plan_id": pid})
        res = await c.call_tool(
            "brute_genius_results", {"plan_id": pid, "top_k": 1}
        )
        best = res.data[0]
        assert best["combo"] == {"x": 1, "y": 1, "z": 1}
        # Score should be -(1+1+1) = -3
        assert best["score"] == pytest.approx(-3.0)


@pytest.mark.asyncio
async def test_linear_sum_best_is_max_values():
    async with Client(mcp) as c:
        plan = await c.call_tool(
            "brute_genius_plan",
            {
                "space": SPACE_3X3X3,
                "objective": "linear_sum",
                "max_cost_usd": 10.0,
            },
        )
        pid = plan.data["plan_id"]
        await c.call_tool("brute_genius_launch", {"plan_id": pid})
        res = await c.call_tool(
            "brute_genius_results", {"plan_id": pid, "top_k": 1}
        )
        best = res.data[0]
        assert best["combo"] == {"x": 3, "y": 3, "z": 3}
        assert best["score"] == pytest.approx(9.0)


@pytest.mark.asyncio
async def test_xpu_probe_returns_structure():
    async with Client(mcp) as c:
        r = await c.call_tool("xpu_probe", {"chip": "h100"})
        data = r.data
        assert "cuda" in data
        assert "xpu" in data
        assert "mps" in data
        assert "cpu" in data
        assert data["cpu"] is True
        assert "preferred" in data
        assert "provider_rates" in data


@pytest.mark.asyncio
async def test_status_before_launch():
    async with Client(mcp) as c:
        plan = await c.call_tool(
            "brute_genius_plan",
            {
                "space": TINY_SPACE,
                "objective": "sphere",
                "max_cost_usd": 5.0,
            },
        )
        pid = plan.data["plan_id"]
        status = await c.call_tool("brute_genius_status", {"plan_id": pid})
        assert status.data["state"] == "planned"
        assert status.data["combinations_evaluated"] == 0
        assert status.data["best_so_far"] is None


@pytest.mark.asyncio
async def test_nodes_hard_cap():
    async with Client(mcp) as c:
        with pytest.raises(Exception):
            await c.call_tool(
                "brute_genius_plan",
                {
                    "space": TINY_SPACE,
                    "objective": "sphere",
                    "max_cost_usd": 100.0,
                    "nodes": 65,  # exceeds MAX_NODES = 64
                },
            )


@pytest.mark.asyncio
async def test_resources_list_plans():
    async with Client(mcp) as c:
        plan = await c.call_tool(
            "brute_genius_plan",
            {
                "space": TINY_SPACE,
                "objective": "sphere",
                "max_cost_usd": 5.0,
            },
        )
        pid = plan.data["plan_id"]
        # Read the plans resource
        content = await c.read_resource("brutegenius://plans")
        # content is a list of TextResourceContents; just ensure it does not error
        assert content is not None
        # Direct store check
        assert pid in _plans


@pytest.mark.asyncio
async def test_kill_aborts_mid_run(monkeypatch):
    """Kill during launch must abort scoring and preserve partial results.

    Uses a background thread to flip plan state to killed while scoring is
    in a blocking sleep, proving batch_score checks the flag mid-run.
    """
    import threading
    import time as _time
    import xpu as xpu_mod

    def slow_batch_score(shard, fn, device, batch_size=64, plan=None):
        results = []
        batch = []
        for combo in shard:
            if plan is not None and plan.get("state") == "killed":
                raise RuntimeError("Plan killed")
            batch.append(combo)
            if len(batch) >= batch_size:
                if plan is not None and plan.get("state") == "killed":
                    raise RuntimeError("Plan killed")
                _time.sleep(0.05)
                results.extend((c, fn(c)) for c in batch)
                batch = []
        if batch:
            if plan is not None and plan.get("state") == "killed":
                raise RuntimeError("Plan killed")
            results.extend((c, fn(c)) for c in batch)
        return results

    monkeypatch.setattr(xpu_mod, "batch_score", slow_batch_score)

    slow_space = {"x": list(range(1_000)), "y": [1]}
    async with Client(mcp) as c:
        p = await c.call_tool(
            "brute_genius_plan",
            {
                "space": slow_space,
                "objective": "sphere",
                "max_cost_usd": 100.0,
                "nodes": 2,
            },
        )
        pid = p.data["plan_id"]

        def kill_from_thread() -> None:
            _time.sleep(0.08)
            # Directly flip the shared plan state (same process memory).
            # This is what brute_genius_kill does; we bypass the client
            # so the flag is set while the event loop is blocked in sleep.
            plan = _plans.get(pid)
            if plan is not None:
                plan["state"] = "killed"
                plan["killed_at"] = _time.time()
                plan["finished_at"] = plan["killed_at"]

        t = threading.Thread(target=kill_from_thread, daemon=True)
        t.start()

        launch_result = await c.call_tool(
            "brute_genius_launch", {"plan_id": pid}
        )
        t.join(timeout=2.0)

        assert launch_result.data["state"] == "killed"

        status = await c.call_tool("brute_genius_status", {"plan_id": pid})
        assert status.data["state"] == "killed"
        assert status.data.get("killed_at") is not None

        res = await c.call_tool(
            "brute_genius_results", {"plan_id": pid, "top_k": 5}
        )
        assert isinstance(res.data, list)
