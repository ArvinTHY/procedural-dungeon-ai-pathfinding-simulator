from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import random
from statistics import mean

from pathfinding import (
    astar,
    bfs,
    bidirectional_bfs,
    dfs,
    dijkstra,
    greedy_best_first,
    manhattan,
    weighted_astar,
)

Point = tuple[int, int]


@dataclass
class BenchmarkSummary:
    algorithm: str
    runs: int
    avg_time_ms: float
    avg_visited_nodes: float
    avg_path_length: float


def _make_pairs(walkable: set[Point], runs: int, seed: int) -> list[tuple[Point, Point]]:
    rng = random.Random(seed)
    nodes = sorted(walkable)
    pairs: list[tuple[Point, Point]] = []
    if len(nodes) < 2:
        return pairs

    attempts = 0
    while len(pairs) < runs and attempts < runs * 100:
        a, b = rng.sample(nodes, 2)
        attempts += 1
        if manhattan(a, b) >= 8:
            pairs.append((a, b))

    while len(pairs) < runs:
        pairs.append(tuple(rng.sample(nodes, 2)))
    return pairs


def run_benchmark_suite(
    walkable: set[Point],
    runs: int = 50,
    seed: int = 1234,
    output_path: str | None = None,
) -> list[BenchmarkSummary]:
    pairs = _make_pairs(walkable, runs, seed)
    algorithms = (
        ("A*", astar),
        ("Dijkstra", dijkstra),
        ("BFS", bfs),
        ("Greedy", greedy_best_first),
        ("DFS", dfs),
        ("Bidirectional BFS", bidirectional_bfs),
        ("Weighted A*", weighted_astar),
    )
    summaries: list[BenchmarkSummary] = []

    for name, algorithm in algorithms:
        times: list[float] = []
        visited: list[int] = []
        lengths: list[int] = []

        for start, goal in pairs:
            result = algorithm(start, goal, walkable)
            if not result.path:
                continue
            times.append(result.elapsed_ms)
            visited.append(result.visited_nodes)
            lengths.append(len(result.path) - 1)

        completed = len(times)
        if completed:
            summaries.append(
                BenchmarkSummary(
                    name,
                    completed,
                    mean(times),
                    mean(visited),
                    mean(lengths),
                )
            )
        else:
            summaries.append(BenchmarkSummary(name, 0, 0.0, 0.0, 0.0))

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "algorithm",
                    "runs",
                    "avg_time_ms",
                    "avg_visited_nodes",
                    "avg_path_length",
                ],
            )
            writer.writeheader()
            for item in summaries:
                writer.writerow(
                    {
                        "algorithm": item.algorithm,
                        "runs": item.runs,
                        "avg_time_ms": f"{item.avg_time_ms:.6f}",
                        "avg_visited_nodes": f"{item.avg_visited_nodes:.2f}",
                        "avg_path_length": f"{item.avg_path_length:.2f}",
                    }
                )

    return summaries
