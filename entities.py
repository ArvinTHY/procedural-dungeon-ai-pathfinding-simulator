from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pathfinding import PathResult

Point = tuple[int, int]
Algorithm = Callable[[Point, Point, set[Point]], PathResult]


@dataclass
class Player:
    pos: Point
    auto_path: list[Point] | None = None
    last_result: PathResult | None = None

    def try_move(self, dx: int, dy: int, walkable: set[Point]) -> None:
        target = (self.pos[0] + dx, self.pos[1] + dy)
        if target in walkable:
            self.pos = target

    def calculate_path(
        self,
        goal: Point,
        walkable: set[Point],
        algorithm: Algorithm,
    ) -> None:
        self.last_result = algorithm(self.pos, goal, walkable)
        self.auto_path = self.last_result.path

    def step(self) -> None:
        if self.auto_path and len(self.auto_path) > 1:
            self.pos = self.auto_path[1]
            self.auto_path = self.auto_path[1:]


@dataclass
class Enemy:
    pos: Point
    path: list[Point] | None = None
    last_result: PathResult | None = None

    def calculate_path(
        self,
        target: Point,
        walkable: set[Point],
        algorithm: Algorithm,
    ) -> None:
        self.last_result = algorithm(self.pos, target, walkable)
        self.path = self.last_result.path

    def step(self) -> None:
        if self.path and len(self.path) > 1:
            self.pos = self.path[1]
            self.path = self.path[1:]
