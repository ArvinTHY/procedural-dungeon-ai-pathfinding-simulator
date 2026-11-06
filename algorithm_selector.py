from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pathfinding import PathResult, astar, bfs, bidirectional_bfs, dijkstra, manhattan

Point = tuple[int, int]
Algorithm = Callable[[Point, Point, set[Point]], PathResult]


@dataclass
class AlgorithmDecision:
    name: str
    algorithm: Algorithm
    reason: str
    distance: int
    search_space: int


def choose_algorithm(start: Point, goal: Point, walkable: set[Point]) -> AlgorithmDecision:
    """Transparent rule-based selector using only shortest-path-safe choices."""
    distance = manhattan(start, goal)
    search_space = len(walkable)

    if distance <= 6:
        return AlgorithmDecision(
            "BFS",
            bfs,
            (
                f"BFS selected: target is very close (Manhattan distance={distance}). "
                "On a unit-cost grid BFS is simple and guarantees a shortest path."
            ),
            distance,
            search_space,
        )

    if distance <= 12 and search_space < 500:
        return AlgorithmDecision(
            "Dijkstra",
            dijkstra,
            (
                f"Dijkstra selected: medium-short route (distance={distance}) in a "
                f"moderate search space ({search_space} walkable nodes)."
            ),
            distance,
            search_space,
        )

    if distance >= 24 and search_space >= 350:
        return AlgorithmDecision(
            "Bidirectional BFS",
            bidirectional_bfs,
            (
                f"Bidirectional BFS selected: route is long (distance={distance}) and "
                f"the search space is large ({search_space} nodes). Two BFS waves can "
                "meet in the middle while preserving shortest-path optimality."
            ),
            distance,
            search_space,
        )

    return AlgorithmDecision(
        "A*",
        astar,
        (
            f"A* selected: distance={distance}, search space={search_space}. "
            "The Manhattan heuristic guides the search toward the target while "
            "preserving shortest-path optimality on this grid."
        ),
        distance,
        search_space,
    )
