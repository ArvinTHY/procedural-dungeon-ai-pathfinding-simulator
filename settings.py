from __future__ import annotations

from dataclasses import dataclass

MAP_WIDTH = 960
INSPECTOR_WIDTH = 360
WIDTH = MAP_WIDTH + INSPECTOR_WIDTH
HEIGHT = 720
FPS = 60

TILE_SIZE = 24
GRID_WIDTH = MAP_WIDTH // TILE_SIZE
GRID_HEIGHT = HEIGHT // TILE_SIZE

WALL = 1
FLOOR = 0

PLAYER_MOVE_DELAY_MS = 90
AUTO_PLAYER_MOVE_DELAY_MS = 220
ENEMY_MOVE_DELAY_MS = 260
WEIGHTED_ASTAR_WEIGHT = 2.0


@dataclass(frozen=True)
class DifficultyConfig:
    name: str
    room_count: int
    room_min_size: int
    room_max_size: int


DIFFICULTIES = {
    "EASY": DifficultyConfig("EASY", room_count=7, room_min_size=6, room_max_size=10),
    "MEDIUM": DifficultyConfig("MEDIUM", room_count=12, room_min_size=5, room_max_size=9),
    "HARD": DifficultyConfig("HARD", room_count=17, room_min_size=4, room_max_size=8),
}

SPEED_OPTIONS = [0.5, 1.0, 2.0, 4.0]
ALGORITHM_OPTIONS = [
    "AUTO",
    "A*",
    "DIJKSTRA",
    "BFS",
    "GREEDY",
    "DFS",
    "BIDIRECTIONAL",
    "WEIGHTED_A*",
]
