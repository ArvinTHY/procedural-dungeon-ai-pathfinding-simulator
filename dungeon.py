from __future__ import annotations

from dataclasses import dataclass
import random

from settings import (
    DIFFICULTIES,
    FLOOR,
    GRID_HEIGHT,
    GRID_WIDTH,
    WALL,
)

Point = tuple[int, int]


@dataclass
class Room:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Point:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other: "Room", padding: int = 1) -> bool:
        return not (
            self.x + self.w + padding <= other.x
            or other.x + other.w + padding <= self.x
            or self.y + self.h + padding <= other.y
            or other.y + other.h + padding <= self.y
        )


class Dungeon:
    def __init__(self, difficulty: str = "MEDIUM", seed: int | None = None):
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"Unknown difficulty: {difficulty}")

        self.difficulty = difficulty
        self.config = DIFFICULTIES[difficulty]
        self.seed = seed if seed is not None else random.randrange(1, 10_000_000)
        self.rng = random.Random(self.seed)

        self.grid: list[list[int]] = []
        self.rooms: list[Room] = []
        self.walkable: set[Point] = set()

        self.generate()

    def generate(self) -> None:
        self.grid = [[WALL for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.rooms = []

        attempts = self.config.room_count * 30
        padding = 0 if self.difficulty == "HARD" else 1

        for _ in range(attempts):
            if len(self.rooms) >= self.config.room_count:
                break

            w = self.rng.randint(
                self.config.room_min_size,
                self.config.room_max_size,
            )
            h = self.rng.randint(
                self.config.room_min_size,
                self.config.room_max_size,
            )

            x = self.rng.randint(1, GRID_WIDTH - w - 2)
            y = self.rng.randint(1, GRID_HEIGHT - h - 2)

            room = Room(x, y, w, h)

            if any(room.intersects(existing, padding) for existing in self.rooms):
                continue

            self._carve_room(room)

            if self.rooms:
                self._connect(self.rooms[-1].center, room.center)

            self.rooms.append(room)

        if len(self.rooms) < 3:
            raise RuntimeError("Dungeon generation failed to create enough rooms.")

        self.walkable = {
            (x, y)
            for y, row in enumerate(self.grid)
            for x, tile in enumerate(row)
            if tile == FLOOR
        }

    def _carve_room(self, room: Room) -> None:
        for y in range(room.y, room.y + room.h):
            for x in range(room.x, room.x + room.w):
                self.grid[y][x] = FLOOR

    def _connect(self, a: Point, b: Point) -> None:
        ax, ay = a
        bx, by = b

        if self.rng.random() < 0.5:
            self._carve_h(ax, bx, ay)
            self._carve_v(ay, by, bx)
        else:
            self._carve_v(ay, by, ax)
            self._carve_h(ax, bx, by)

    def _carve_h(self, x1: int, x2: int, y: int) -> None:
        lo, hi = sorted((x1, x2))
        for x in range(lo, hi + 1):
            self.grid[y][x] = FLOOR

    def _carve_v(self, y1: int, y2: int, x: int) -> None:
        lo, hi = sorted((y1, y2))
        for y in range(lo, hi + 1):
            self.grid[y][x] = FLOOR

    @property
    def player_spawn(self) -> Point:
        return self.rooms[0].center

    @property
    def enemy_spawn(self) -> Point:
        return self.rooms[len(self.rooms) // 2].center

    @property
    def goal_spawn(self) -> Point:
        return self.rooms[-1].center
