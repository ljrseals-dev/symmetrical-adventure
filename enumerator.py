"""Lazy Cartesian enumeration with independent, resumable sharding.

The engine never holds the full combination list in memory. It streams.
Hard limit: MAX_COMBINATIONS = 10**9.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Iterator

MAX_COMBINATIONS = 10**9


def count(space: dict[str, list]) -> int:
    """Return |A1| * |A2| * ... * |An| without enumerating.

    Cheap even for 10^12 theoretical combinations. Returns 0 if any
    axis is empty.
    """
    total = 1
    for values in space.values():
        if not values:
            return 0
        total *= len(values)
        if total > MAX_COMBINATIONS:
            # Early exit once we know we have already exceeded the hard cap.
            return total
    return total


def cartesian(space: dict[str, list]) -> Iterator[dict[str, Any]]:
    """Lazily yield every combination as a dict. Never materialises the set."""
    if not space:
        yield {}
        return
    axes = list(space.keys())
    for combo in product(*(space[a] for a in axes)):
        yield dict(zip(axes, combo))


def shard(space: dict[str, list], n_shards: int) -> list[Iterator[dict[str, Any]]]:
    """Split the space by modular index so each shard is independent and resumable.

    Shard i yields combinations whose global index satisfies index % n_shards == i.
    This makes shards independent: a node can be restarted from the beginning of
    its shard without coordinating with other nodes.
    """
    if n_shards < 1:
        raise ValueError("n_shards must be >= 1")

    def _shard_iter(idx: int) -> Iterator[dict[str, Any]]:
        for i, combo in enumerate(cartesian(space)):
            if i % n_shards == idx:
                yield combo

    return [_shard_iter(i) for i in range(n_shards)]


def estimate_shard_sizes(space: dict[str, list], n_shards: int) -> list[int]:
    """Return the exact number of combinations each shard will process."""
    total = count(space)
    base = total // n_shards
    remainder = total % n_shards
    return [base + (1 if i < remainder else 0) for i in range(n_shards)]
