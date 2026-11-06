from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import heapq
from time import perf_counter
from typing import Dict, Iterable

Point = tuple[int, int]


@dataclass
class PathResult:
    path: list[Point]
    visited_nodes: int
    elapsed_ms: float
    visited: frozenset[Point]


@dataclass
class SearchStep:
    current: Point
    open_nodes: frozenset[Point]
    closed_nodes: frozenset[Point]
    g_cost: float
    h_cost: float
    f_cost: float
    note: str = ""


@dataclass
class TraceResult:
    steps: list[SearchStep]
    result: PathResult


def neighbors(node: Point, walkable: set[Point]) -> Iterable[Point]:
    x, y = node
    for candidate in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if candidate in walkable:
            yield candidate


def manhattan(a: Point, b: Point) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct(came_from: Dict[Point, Point], current: Point) -> list[Point]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def _result(started: float, path: list[Point], closed: set[Point]) -> PathResult:
    return PathResult(path, len(closed), (perf_counter() - started) * 1000, frozenset(closed))


def astar(start: Point, goal: Point, walkable: set[Point]) -> PathResult:
    started = perf_counter()
    frontier: list[tuple[float, int, Point]] = [(0.0, 0, start)]
    counter = 0
    came_from: Dict[Point, Point] = {}
    g_score: Dict[Point, int] = {start: 0}
    closed: set[Point] = set()

    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current in closed:
            continue
        closed.add(current)

        if current == goal:
            return _result(started, reconstruct(came_from, current), closed)

        for nxt in neighbors(current, walkable):
            tentative = g_score[current] + 1
            if tentative < g_score.get(nxt, 10**12):
                came_from[nxt] = current
                g_score[nxt] = tentative
                counter += 1
                heapq.heappush(
                    frontier,
                    (tentative + manhattan(nxt, goal), counter, nxt),
                )

    return _result(started, [], closed)


def dijkstra(start: Point, goal: Point, walkable: set[Point]) -> PathResult:
    started = perf_counter()
    frontier: list[tuple[int, int, Point]] = [(0, 0, start)]
    counter = 0
    came_from: Dict[Point, Point] = {}
    distance: Dict[Point, int] = {start: 0}
    closed: set[Point] = set()

    while frontier:
        cost, _, current = heapq.heappop(frontier)
        if current in closed:
            continue
        closed.add(current)

        if current == goal:
            return _result(started, reconstruct(came_from, current), closed)

        for nxt in neighbors(current, walkable):
            new_cost = cost + 1
            if new_cost < distance.get(nxt, 10**12):
                distance[nxt] = new_cost
                came_from[nxt] = current
                counter += 1
                heapq.heappush(frontier, (new_cost, counter, nxt))

    return _result(started, [], closed)


def bfs(start: Point, goal: Point, walkable: set[Point]) -> PathResult:
    """Breadth-First Search. Optimal on this unit-cost grid."""
    started = perf_counter()
    frontier = deque([start])
    discovered = {start}
    closed: set[Point] = set()
    came_from: Dict[Point, Point] = {}

    while frontier:
        current = frontier.popleft()
        closed.add(current)

        if current == goal:
            return _result(started, reconstruct(came_from, current), closed)

        for nxt in neighbors(current, walkable):
            if nxt not in discovered:
                discovered.add(nxt)
                came_from[nxt] = current
                frontier.append(nxt)

    return _result(started, [], closed)


def dfs(start: Point, goal: Point, walkable: set[Point]) -> PathResult:
    """Depth-First Search. Finds a path if one exists, but not necessarily the shortest."""
    started = perf_counter()
    stack = [start]
    discovered = {start}
    closed: set[Point] = set()
    came_from: Dict[Point, Point] = {}

    while stack:
        current = stack.pop()
        closed.add(current)

        if current == goal:
            return _result(started, reconstruct(came_from, current), closed)

        for nxt in neighbors(current, walkable):
            if nxt not in discovered:
                discovered.add(nxt)
                came_from[nxt] = current
                stack.append(nxt)

    return _result(started, [], closed)


def greedy_best_first(start: Point, goal: Point, walkable: set[Point]) -> PathResult:
    """Greedy Best-First Search. Goal-directed but not guaranteed shortest."""
    started = perf_counter()
    frontier: list[tuple[int, int, Point]] = []
    counter = 0
    heapq.heappush(frontier, (manhattan(start, goal), counter, start))
    discovered = {start}
    closed: set[Point] = set()
    came_from: Dict[Point, Point] = {}

    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current in closed:
            continue
        closed.add(current)

        if current == goal:
            return _result(started, reconstruct(came_from, current), closed)

        for nxt in neighbors(current, walkable):
            if nxt not in discovered:
                discovered.add(nxt)
                came_from[nxt] = current
                counter += 1
                heapq.heappush(frontier, (manhattan(nxt, goal), counter, nxt))

    return _result(started, [], closed)


def weighted_astar(
    start: Point,
    goal: Point,
    walkable: set[Point],
    weight: float = 2.0,
) -> PathResult:
    """Weighted A*. Uses f = g + weight*h. With weight > 1, shortest-path optimality is not guaranteed."""
    started = perf_counter()
    frontier: list[tuple[float, int, Point]] = [(weight * manhattan(start, goal), 0, start)]
    counter = 0
    came_from: Dict[Point, Point] = {}
    g_score: Dict[Point, int] = {start: 0}
    closed: set[Point] = set()

    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current in closed:
            continue
        closed.add(current)

        if current == goal:
            return _result(started, reconstruct(came_from, current), closed)

        for nxt in neighbors(current, walkable):
            tentative = g_score[current] + 1
            if tentative < g_score.get(nxt, 10**12):
                came_from[nxt] = current
                g_score[nxt] = tentative
                counter += 1
                priority = tentative + weight * manhattan(nxt, goal)
                heapq.heappush(frontier, (priority, counter, nxt))

    return _result(started, [], closed)


def _join_bidirectional_paths(
    meet: Point,
    parents_start: Dict[Point, Point],
    parents_goal: Dict[Point, Point],
) -> list[Point]:
    first_half = reconstruct(parents_start, meet)
    second_half: list[Point] = []
    current = meet
    while current in parents_goal:
        current = parents_goal[current]
        second_half.append(current)
    return first_half + second_half


def bidirectional_bfs(start: Point, goal: Point, walkable: set[Point]) -> PathResult:
    """Bidirectional BFS. Expands BFS layers from both start and goal and is optimal on this unit-cost grid."""
    started = perf_counter()

    if start == goal:
        return PathResult([start], 1, (perf_counter() - started) * 1000, frozenset({start}))

    front_start: set[Point] = {start}
    front_goal: set[Point] = {goal}
    visited_start: set[Point] = {start}
    visited_goal: set[Point] = {goal}
    parents_start: Dict[Point, Point] = {}
    parents_goal: Dict[Point, Point] = {}
    expanded: set[Point] = set()

    while front_start and front_goal:
        expand_from_start = len(front_start) <= len(front_goal)

        if expand_from_start:
            current_front = front_start
            next_front: set[Point] = set()
            for current in current_front:
                expanded.add(current)
                for nxt in neighbors(current, walkable):
                    if nxt in visited_start:
                        continue
                    visited_start.add(nxt)
                    parents_start[nxt] = current
                    if nxt in visited_goal:
                        expanded.add(nxt)
                        return _result(
                            started,
                            _join_bidirectional_paths(nxt, parents_start, parents_goal),
                            expanded,
                        )
                    next_front.add(nxt)
            front_start = next_front
        else:
            current_front = front_goal
            next_front = set()
            for current in current_front:
                expanded.add(current)
                for nxt in neighbors(current, walkable):
                    if nxt in visited_goal:
                        continue
                    visited_goal.add(nxt)
                    parents_goal[nxt] = current
                    if nxt in visited_start:
                        expanded.add(nxt)
                        return _result(
                            started,
                            _join_bidirectional_paths(nxt, parents_start, parents_goal),
                            expanded,
                        )
                    next_front.add(nxt)
            front_goal = next_front

    return _result(started, [], expanded)


def _priority_trace(
    start: Point,
    goal: Point,
    walkable: set[Point],
    mode: str,
    weight: float = 2.0,
) -> TraceResult:
    started = perf_counter()
    frontier: list[tuple[float, int, Point]] = []
    counter = 0
    came_from: Dict[Point, Point] = {}
    g_score: Dict[Point, int] = {start: 0}
    closed: set[Point] = set()
    open_members: set[Point] = {start}
    discovered: set[Point] = {start}
    steps: list[SearchStep] = []

    if mode == "ASTAR":
        start_priority = manhattan(start, goal)
    elif mode == "WEIGHTED_ASTAR":
        start_priority = weight * manhattan(start, goal)
    elif mode == "GREEDY":
        start_priority = manhattan(start, goal)
    else:  # DIJKSTRA
        start_priority = 0

    heapq.heappush(frontier, (start_priority, counter, start))

    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current in closed:
            continue

        open_members.discard(current)
        closed.add(current)
        g = g_score.get(current, 0)
        h = manhattan(current, goal) if mode in ("ASTAR", "WEIGHTED_ASTAR", "GREEDY") else 0

        if mode == "ASTAR":
            f = g + h
            note = "Priority = G + H"
        elif mode == "WEIGHTED_ASTAR":
            f = g + weight * h
            note = f"Priority = G + {weight:g}×H"
        elif mode == "GREEDY":
            f = h
            note = "Priority = H"
        else:
            f = g
            note = "Priority = G"

        if current != goal:
            for nxt in neighbors(current, walkable):
                tentative = g + 1
                if mode in ("ASTAR", "WEIGHTED_ASTAR", "DIJKSTRA"):
                    if tentative < g_score.get(nxt, 10**12):
                        came_from[nxt] = current
                        g_score[nxt] = tentative
                        counter += 1
                        if mode == "ASTAR":
                            priority = tentative + manhattan(nxt, goal)
                        elif mode == "WEIGHTED_ASTAR":
                            priority = tentative + weight * manhattan(nxt, goal)
                        else:
                            priority = tentative
                        heapq.heappush(frontier, (priority, counter, nxt))
                        if nxt not in closed:
                            open_members.add(nxt)
                else:  # GREEDY
                    if nxt not in discovered:
                        discovered.add(nxt)
                        came_from[nxt] = current
                        g_score[nxt] = tentative
                        counter += 1
                        heapq.heappush(frontier, (manhattan(nxt, goal), counter, nxt))
                        if nxt not in closed:
                            open_members.add(nxt)

        steps.append(
            SearchStep(
                current,
                frozenset(open_members),
                frozenset(closed),
                g,
                h,
                f,
                note,
            )
        )

        if current == goal:
            break

    path = reconstruct(came_from, goal) if goal in closed else []
    return TraceResult(steps, _result(started, path, closed))


def _deque_trace(start: Point, goal: Point, walkable: set[Point], mode: str) -> TraceResult:
    started = perf_counter()
    container = deque([start])
    discovered = {start}
    came_from: Dict[Point, Point] = {}
    depth: Dict[Point, int] = {start: 0}
    closed: set[Point] = set()
    open_members: set[Point] = {start}
    steps: list[SearchStep] = []

    while container:
        if mode == "BFS":
            current = container.popleft()
        else:
            current = container.pop()

        open_members.discard(current)
        closed.add(current)
        g = depth[current]

        if current != goal:
            for nxt in neighbors(current, walkable):
                if nxt not in discovered:
                    discovered.add(nxt)
                    came_from[nxt] = current
                    depth[nxt] = g + 1
                    container.append(nxt)
                    open_members.add(nxt)

        note = "FIFO queue / layer-by-layer" if mode == "BFS" else "LIFO stack / depth-first"
        steps.append(
            SearchStep(
                current,
                frozenset(open_members),
                frozenset(closed),
                g,
                0,
                g,
                note,
            )
        )

        if current == goal:
            break

    path = reconstruct(came_from, goal) if goal in closed else []
    return TraceResult(steps, _result(started, path, closed))


def bidirectional_bfs_trace(start: Point, goal: Point, walkable: set[Point]) -> TraceResult:
    started = perf_counter()

    if start == goal:
        step = SearchStep(start, frozenset(), frozenset({start}), 0, 0, 0, "Start already equals goal")
        result = PathResult([start], 1, (perf_counter() - started) * 1000, frozenset({start}))
        return TraceResult([step], result)

    front_start: set[Point] = {start}
    front_goal: set[Point] = {goal}
    visited_start: set[Point] = {start}
    visited_goal: set[Point] = {goal}
    parents_start: Dict[Point, Point] = {}
    parents_goal: Dict[Point, Point] = {}
    depth_start: Dict[Point, int] = {start: 0}
    depth_goal: Dict[Point, int] = {goal: 0}
    expanded: set[Point] = set()
    steps: list[SearchStep] = []
    meet: Point | None = None

    while front_start and front_goal and meet is None:
        expand_from_start = len(front_start) <= len(front_goal)
        current_front = front_start if expand_from_start else front_goal
        next_front: set[Point] = set()

        for current in sorted(current_front):
            expanded.add(current)
            current_depth = (depth_start if expand_from_start else depth_goal)[current]
            target = goal if expand_from_start else start
            side_name = "START side" if expand_from_start else "GOAL side"

            for nxt in neighbors(current, walkable):
                own_visited = visited_start if expand_from_start else visited_goal
                other_visited = visited_goal if expand_from_start else visited_start
                own_parents = parents_start if expand_from_start else parents_goal
                own_depth = depth_start if expand_from_start else depth_goal

                if nxt in own_visited:
                    continue

                own_visited.add(nxt)
                own_parents[nxt] = current
                own_depth[nxt] = current_depth + 1
                next_front.add(nxt)

                if nxt in other_visited:
                    meet = nxt
                    expanded.add(nxt)
                    break

            combined_open = (
                (next_front | front_goal) if expand_from_start else (front_start | next_front)
            )
            combined_closed = expanded.copy()
            h = manhattan(current, target)
            steps.append(
                SearchStep(
                    current,
                    frozenset(combined_open),
                    frozenset(combined_closed),
                    current_depth,
                    h,
                    current_depth,
                    f"Expanding {side_name}; two BFS waves search toward each other",
                )
            )

            if meet is not None:
                break

        if expand_from_start:
            front_start = next_front
        else:
            front_goal = next_front

    path = _join_bidirectional_paths(meet, parents_start, parents_goal) if meet is not None else []
    return TraceResult(steps, _result(started, path, expanded))


def astar_trace(start: Point, goal: Point, walkable: set[Point]) -> TraceResult:
    return _priority_trace(start, goal, walkable, "ASTAR")


def dijkstra_trace(start: Point, goal: Point, walkable: set[Point]) -> TraceResult:
    return _priority_trace(start, goal, walkable, "DIJKSTRA")


def bfs_trace(start: Point, goal: Point, walkable: set[Point]) -> TraceResult:
    return _deque_trace(start, goal, walkable, "BFS")


def dfs_trace(start: Point, goal: Point, walkable: set[Point]) -> TraceResult:
    return _deque_trace(start, goal, walkable, "DFS")


def greedy_trace(start: Point, goal: Point, walkable: set[Point]) -> TraceResult:
    return _priority_trace(start, goal, walkable, "GREEDY")


def weighted_astar_trace(
    start: Point,
    goal: Point,
    walkable: set[Point],
    weight: float = 2.0,
) -> TraceResult:
    return _priority_trace(start, goal, walkable, "WEIGHTED_ASTAR", weight=weight)
