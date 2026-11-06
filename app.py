from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import sys

import pygame

from algorithm_selector import choose_algorithm
from benchmark import BenchmarkSummary, run_benchmark_suite
from dungeon import Dungeon
from entities import Enemy, Player
from pathfinding import (
    PathResult,
    TraceResult,
    astar,
    astar_trace,
    bfs,
    bfs_trace,
    bidirectional_bfs,
    bidirectional_bfs_trace,
    dfs,
    dfs_trace,
    dijkstra,
    dijkstra_trace,
    greedy_best_first,
    greedy_trace,
    weighted_astar,
    weighted_astar_trace,
)
from settings import (
    ALGORITHM_OPTIONS,
    AUTO_PLAYER_MOVE_DELAY_MS,
    DIFFICULTIES,
    ENEMY_MOVE_DELAY_MS,
    FPS,
    GRID_HEIGHT,
    GRID_WIDTH,
    HEIGHT,
    INSPECTOR_WIDTH,
    MAP_WIDTH,
    PLAYER_MOVE_DELAY_MS,
    SPEED_OPTIONS,
    TILE_SIZE,
    WALL,
    WIDTH,
)

Point = tuple[int, int]

pygame.init()
pygame.display.set_caption("Procedural Dungeon AI Pathfinding Simulator")

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
CLOCK = pygame.time.Clock()

FONT_SMALL = pygame.font.SysFont("consolas", 14)
FONT = pygame.font.SysFont("consolas", 18)
FONT_MID = pygame.font.SysFont("consolas", 24, bold=True)
FONT_BIG = pygame.font.SysFont("consolas", 38, bold=True)

C_BG = pygame.Color("#0b0d12")
C_PANEL = pygame.Color("#141821")
C_PANEL_2 = pygame.Color("#1c2230")
C_WALL = pygame.Color("#252b38")
C_FLOOR = pygame.Color("#4b5568")
C_TEXT = pygame.Color("#f3f5f7")
C_MUTED = pygame.Color("#aeb6c3")
C_PLAYER = pygame.Color("#27b8ff")
C_ENEMY = pygame.Color("#ff5b5b")
C_GOAL = pygame.Color("#46d17a")
C_PATH_A = pygame.Color("#5de0e6")
C_PATH_D = pygame.Color("#ffd166")
C_PATH_BFS = pygame.Color("#7ee787")
C_PATH_GREEDY = pygame.Color("#ff8cc8")
C_PATH_DFS = pygame.Color("#c792ea")
C_PATH_BIDIR = pygame.Color("#ff9f43")
C_PATH_WEIGHTED = pygame.Color("#ff6b6b")
C_VISITED = pygame.Color("#3566a8")
C_OPEN = pygame.Color("#d2a93b")
C_CURRENT = pygame.Color("#d65ad1")
C_SELECT = pygame.Color("#394663")
C_BAR_A = pygame.Color("#55c7d8")
C_BAR_D = pygame.Color("#f3c969")
C_BAR_BFS = pygame.Color("#7ee787")
C_BAR_GREEDY = pygame.Color("#ff8cc8")
C_BAR_DFS = pygame.Color("#c792ea")
C_BAR_BIDIR = pygame.Color("#ff9f43")
C_BAR_WEIGHTED = pygame.Color("#ff6b6b")


@dataclass
class AppConfig:
    player_algorithm_mode: str = "AUTO"
    enemy_algorithm_mode: str = "AUTO"
    difficulty: str = "MEDIUM"
    speed: float = 1.0
    show_paths: bool = True
    show_visited: bool = True
    show_inspector: bool = True


@dataclass
class RuntimeInfo:
    run_mode: str
    player_algorithm: str = "-"
    player_reason: str = "-"
    enemy_algorithm: str = "-"
    enemy_reason: str = "-"
    paused: bool = False


@dataclass(frozen=True)
class ReplayFrame:
    player_pos: Point
    enemy_pos: Point
    player_path: tuple[Point, ...]
    enemy_path: tuple[Point, ...]
    player_visited: frozenset[Point]
    enemy_visited: frozenset[Point]
    player_algorithm: str
    player_reason: str
    enemy_algorithm: str
    enemy_reason: str
    status: str


def tile_rect(pos: Point) -> pygame.Rect:
    x, y = pos
    return pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)


def draw_text(
    text: str,
    x: int,
    y: int,
    font: pygame.font.Font = FONT,
    color: pygame.Color = C_TEXT,
) -> None:
    SCREEN.blit(font.render(text, True, color), (x, y))


def center_text(
    text: str,
    y: int,
    font: pygame.font.Font = FONT,
    color: pygame.Color = C_TEXT,
) -> None:
    image = font.render(text, True, color)
    SCREEN.blit(image, (WIDTH // 2 - image.get_width() // 2, y))


def wrap_text(
    text: str,
    font: pygame.font.Font,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = word if not current else current + " " + word
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def draw_dungeon(dungeon: Dungeon) -> None:
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = tile_rect((x, y))
            color = C_WALL if dungeon.grid[y][x] == WALL else C_FLOOR
            pygame.draw.rect(SCREEN, color, rect)


def draw_nodes(nodes: set[Point] | frozenset[Point], color: pygame.Color, inset: int = 8) -> None:
    for node in nodes:
        pygame.draw.rect(SCREEN, color, tile_rect(node).inflate(-inset, -inset))


def draw_path(path: list[Point] | None, color: pygame.Color, inset: int = 12) -> None:
    if not path:
        return
    for node in path[1:-1]:
        pygame.draw.rect(SCREEN, color, tile_rect(node).inflate(-inset, -inset))


def algorithm_for(
    mode: str,
    start: Point,
    goal: Point,
    walkable: set[Point],
):
    if mode == "A*":
        return "A*", astar, "Forced by Settings/keyboard. Uses G + H and is optimal with the Manhattan heuristic."
    if mode == "DIJKSTRA":
        return "Dijkstra", dijkstra, "Forced by Settings/keyboard. Expands the cheapest known distance first."
    if mode == "BFS":
        return "BFS", bfs, "Forced by Settings/keyboard. Unit-cost grid means BFS is shortest-path optimal."
    if mode == "GREEDY":
        return "Greedy", greedy_best_first, "Forced by Settings/keyboard. Uses only H, so it can be fast but non-optimal."
    if mode == "DFS":
        return "DFS", dfs, "Forced by Settings/keyboard. Goes deep before backtracking and does not guarantee a shortest path."
    if mode == "BIDIRECTIONAL":
        return "Bidirectional BFS", bidirectional_bfs, "Forced by Settings/keyboard. Two BFS waves search from start and goal and meet in the middle."
    if mode == "WEIGHTED_A*":
        return "Weighted A*", weighted_astar, "Forced by Settings/keyboard. Uses G + 2H, prioritizing speed over guaranteed optimality."

    decision = choose_algorithm(start, goal, walkable)
    return decision.name, decision.algorithm, decision.reason


class App:
    def __init__(self):
        self.config = AppConfig()
        self.main_selection = 0
        self.running = True

    def quit(self) -> None:
        pygame.quit()
        sys.exit()

    def run(self) -> None:
        while self.running:
            action = self.main_menu()

            if action == "MANUAL":
                self.game_screen("MANUAL")
            elif action == "SIMULATION":
                self.game_screen("SIMULATION")
            elif action == "VISUALIZER":
                self.visualizer_screen()
            elif action == "COMPARE":
                self.compare_screen()
            elif action == "BENCHMARK":
                self.benchmark_screen()
            elif action == "SETTINGS":
                self.settings_screen()
            elif action == "QUIT":
                self.quit()

    def main_menu(self) -> str:
        options = [
            ("Manual Play", "Move the player yourself; the enemy uses pathfinding."),
            ("AI Simulation", "Computer moves the player toward the goal while enemy chases."),
            ("Algorithm Visualizer", "Watch seven search algorithms expand nodes step by step."),
            ("Compare Algorithms", "Compare seven pathfinding algorithms on identical conditions."),
            ("Benchmark Dashboard", "Run repeated searches and visualize aggregate metrics."),
            ("Settings", "Algorithm, difficulty, simulation speed, and overlays."),
            ("Exit", "Close the application."),
        ]

        while True:
            SCREEN.fill(C_BG)
            center_text("PROCEDURAL DUNGEON", 62, FONT_BIG)
            center_text("AI PATHFINDING SIMULATOR", 112, FONT_MID, C_MUTED)

            y = 185
            for index, (title, desc) in enumerate(options):
                rect = pygame.Rect(WIDTH // 2 - 350, y, 700, 58)
                if index == self.main_selection:
                    pygame.draw.rect(SCREEN, C_SELECT, rect, border_radius=8)

                draw_text(title, rect.x + 18, rect.y + 8, FONT)
                draw_text(desc, rect.x + 18, rect.y + 33, FONT_SMALL, C_MUTED)
                y += 67

            center_text(
                "UP/DOWN = Select    ENTER = Open    ESC = Exit",
                HEIGHT - 35,
                FONT_SMALL,
                C_MUTED,
            )

            pygame.display.flip()
            CLOCK.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "QUIT"
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.main_selection = (self.main_selection - 1) % len(options)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.main_selection = (self.main_selection + 1) % len(options)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        return [
                            "MANUAL",
                            "SIMULATION",
                            "VISUALIZER",
                            "COMPARE",
                            "BENCHMARK",
                            "SETTINGS",
                            "QUIT",
                        ][self.main_selection]

    def settings_screen(self) -> None:
        rows = [
            "Player Algorithm",
            "Enemy Algorithm",
            "Difficulty",
            "Simulation Speed",
            "Show Paths",
            "Show Visited Nodes",
            "Show Inspector",
            "Back",
        ]
        selected = 0

        def cycle(values: list, current, direction: int):
            index = values.index(current)
            return values[(index + direction) % len(values)]

        while True:
            SCREEN.fill(C_BG)
            center_text("SETTINGS", 75, FONT_BIG)
            center_text(
                "LEFT/RIGHT changes a value. ENTER toggles boolean options.",
                128,
                FONT_SMALL,
                C_MUTED,
            )

            values = [
                self.config.player_algorithm_mode,
                self.config.enemy_algorithm_mode,
                self.config.difficulty,
                f"{self.config.speed:g}x",
                "ON" if self.config.show_paths else "OFF",
                "ON" if self.config.show_visited else "OFF",
                "ON" if self.config.show_inspector else "OFF",
                "",
            ]

            y = 170
            for i, label in enumerate(rows):
                rect = pygame.Rect(WIDTH // 2 - 300, y, 600, 50)
                if i == selected:
                    pygame.draw.rect(SCREEN, C_SELECT, rect, border_radius=8)
                draw_text(label, rect.x + 18, rect.y + 15)
                if values[i]:
                    image = FONT.render(values[i], True, C_TEXT)
                    SCREEN.blit(image, (rect.right - image.get_width() - 18, rect.y + 15))
                y += 58

            center_text("ESC = Back", HEIGHT - 35, FONT_SMALL, C_MUTED)
            pygame.display.flip()
            CLOCK.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(rows)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(rows)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        if selected == 0:
                            self.config.player_algorithm_mode = cycle(
                                ALGORITHM_OPTIONS, self.config.player_algorithm_mode, -1
                            )
                        elif selected == 1:
                            self.config.enemy_algorithm_mode = cycle(
                                ALGORITHM_OPTIONS, self.config.enemy_algorithm_mode, -1
                            )
                        elif selected == 2:
                            self.config.difficulty = cycle(
                                list(DIFFICULTIES.keys()), self.config.difficulty, -1
                            )
                        elif selected == 3:
                            self.config.speed = cycle(
                                SPEED_OPTIONS, self.config.speed, -1
                            )
                        elif selected == 4:
                            self.config.show_paths = not self.config.show_paths
                        elif selected == 5:
                            self.config.show_visited = not self.config.show_visited
                        elif selected == 6:
                            self.config.show_inspector = not self.config.show_inspector
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        if selected == 0:
                            self.config.player_algorithm_mode = cycle(
                                ALGORITHM_OPTIONS, self.config.player_algorithm_mode, 1
                            )
                        elif selected == 1:
                            self.config.enemy_algorithm_mode = cycle(
                                ALGORITHM_OPTIONS, self.config.enemy_algorithm_mode, 1
                            )
                        elif selected == 2:
                            self.config.difficulty = cycle(
                                list(DIFFICULTIES.keys()), self.config.difficulty, 1
                            )
                        elif selected == 3:
                            self.config.speed = cycle(
                                SPEED_OPTIONS, self.config.speed, 1
                            )
                        elif selected == 4:
                            self.config.show_paths = not self.config.show_paths
                        elif selected == 5:
                            self.config.show_visited = not self.config.show_visited
                        elif selected == 6:
                            self.config.show_inspector = not self.config.show_inspector
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if selected == 4:
                            self.config.show_paths = not self.config.show_paths
                        elif selected == 5:
                            self.config.show_visited = not self.config.show_visited
                        elif selected == 6:
                            self.config.show_inspector = not self.config.show_inspector
                        elif selected == 7:
                            return

    def new_world(self):
        dungeon = Dungeon(self.config.difficulty)
        player = Player(dungeon.player_spawn)
        enemy = Enemy(dungeon.enemy_spawn)
        goal = dungeon.goal_spawn
        return dungeon, player, enemy, goal

    def _capture_replay_frame(
        self,
        player: Player,
        enemy: Enemy,
        runtime: RuntimeInfo,
        status: str,
    ) -> ReplayFrame:
        return ReplayFrame(
            player_pos=player.pos,
            enemy_pos=enemy.pos,
            player_path=tuple(player.auto_path or []),
            enemy_path=tuple(enemy.path or []),
            player_visited=player.last_result.visited if player.last_result else frozenset(),
            enemy_visited=enemy.last_result.visited if enemy.last_result else frozenset(),
            player_algorithm=runtime.player_algorithm,
            player_reason=runtime.player_reason,
            enemy_algorithm=runtime.enemy_algorithm,
            enemy_reason=runtime.enemy_reason,
            status=status,
        )

    def _set_actor_algorithm(self, actor: str, mode: str, logs: deque[str]) -> None:
        if actor == "PLAYER":
            self.config.player_algorithm_mode = mode
            logs.append(f"Player algorithm -> {mode}")
        else:
            self.config.enemy_algorithm_mode = mode
            logs.append(f"Enemy algorithm -> {mode}")

    def _cycle_actor_algorithm(self, actor: str, direction: int, logs: deque[str]) -> None:
        current = (
            self.config.player_algorithm_mode
            if actor == "PLAYER"
            else self.config.enemy_algorithm_mode
        )
        index = ALGORITHM_OPTIONS.index(current)
        new_mode = ALGORITHM_OPTIONS[(index + direction) % len(ALGORITHM_OPTIONS)]
        self._set_actor_algorithm(actor, new_mode, logs)

    def game_screen(self, run_mode: str) -> None:
        dungeon, player, enemy, goal = self.new_world()
        runtime = RuntimeInfo(run_mode=run_mode)
        logs: deque[str] = deque(maxlen=7)
        status = "Running"
        paused = False
        finished = False
        algorithm_target = "ENEMY" if run_mode == "MANUAL" else "PLAYER"

        replay_frames: list[ReplayFrame] = []
        if run_mode == "SIMULATION":
            replay_frames.append(self._capture_replay_frame(player, enemy, runtime, status))

        last_player_move = 0
        last_enemy_move = 0
        replay_button = pygame.Rect(MAP_WIDTH - 105, HEIGHT - 27, 96, 23)

        while True:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if run_mode == "SIMULATION" and len(replay_frames) > 1 and replay_button.collidepoint(event.pos):
                        self.replay_screen(dungeon, goal, replay_frames)
                        last_player_move = pygame.time.get_ticks()
                        last_enemy_move = pygame.time.get_ticks()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.quit()
                    elif event.key == pygame.K_m:
                        return
                    elif event.key == pygame.K_t and run_mode == "SIMULATION":
                        algorithm_target = "ENEMY" if algorithm_target == "PLAYER" else "PLAYER"
                        logs.append(f"Algorithm controls target -> {algorithm_target}")
                    elif event.key == pygame.K_COMMA:
                        self._cycle_actor_algorithm(algorithm_target, -1, logs)
                    elif event.key == pygame.K_PERIOD:
                        self._cycle_actor_algorithm(algorithm_target, 1, logs)
                    elif event.key == pygame.K_1:
                        self._set_actor_algorithm(algorithm_target, "A*", logs)
                    elif event.key == pygame.K_2:
                        self._set_actor_algorithm(algorithm_target, "DIJKSTRA", logs)
                    elif event.key == pygame.K_3:
                        self._set_actor_algorithm(algorithm_target, "BFS", logs)
                    elif event.key == pygame.K_4:
                        self._set_actor_algorithm(algorithm_target, "GREEDY", logs)
                    elif event.key == pygame.K_5:
                        self._set_actor_algorithm(algorithm_target, "DFS", logs)
                    elif event.key == pygame.K_6:
                        self._set_actor_algorithm(algorithm_target, "BIDIRECTIONAL", logs)
                    elif event.key == pygame.K_7:
                        self._set_actor_algorithm(algorithm_target, "WEIGHTED_A*", logs)
                    elif event.key == pygame.K_0:
                        self._set_actor_algorithm(algorithm_target, "AUTO", logs)
                    elif event.key == pygame.K_y and run_mode == "SIMULATION" and len(replay_frames) > 1:
                        self.replay_screen(dungeon, goal, replay_frames)
                        last_player_move = pygame.time.get_ticks()
                        last_enemy_move = pygame.time.get_ticks()
                    elif event.key == pygame.K_p:
                        self.config.show_paths = not self.config.show_paths
                    elif event.key == pygame.K_v:
                        self.config.show_visited = not self.config.show_visited
                    elif event.key == pygame.K_TAB:
                        self.config.show_inspector = not self.config.show_inspector
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                        runtime.paused = paused
                        logs.append("Paused" if paused else "Resumed")
                    elif event.key == pygame.K_r:
                        dungeon, player, enemy, goal = self.new_world()
                        status = "New dungeon generated"
                        logs.clear()
                        finished = False
                        replay_frames.clear()
                        if run_mode == "SIMULATION":
                            replay_frames.append(self._capture_replay_frame(player, enemy, runtime, status))
                    elif event.key == pygame.K_LEFTBRACKET:
                        self._change_speed(-1)
                        logs.append(f"Speed -> {self.config.speed:g}x")
                    elif event.key == pygame.K_RIGHTBRACKET:
                        self._change_speed(1)
                        logs.append(f"Speed -> {self.config.speed:g}x")

            state_changed = False

            if not paused and not finished:
                player_delay = int(AUTO_PLAYER_MOVE_DELAY_MS / self.config.speed)
                enemy_delay = int(ENEMY_MOVE_DELAY_MS / self.config.speed)

                if run_mode == "MANUAL":
                    keys = pygame.key.get_pressed()
                    manual_delay = int(PLAYER_MOVE_DELAY_MS / self.config.speed)
                    if now - last_player_move >= manual_delay:
                        dx = dy = 0
                        if keys[pygame.K_w] or keys[pygame.K_UP]:
                            dy = -1
                        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                            dy = 1
                        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                            dx = -1
                        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                            dx = 1
                        if dx or dy:
                            old = player.pos
                            player.try_move(dx, dy, dungeon.walkable)
                            state_changed = state_changed or player.pos != old
                            last_player_move = now
                else:
                    if now - last_player_move >= player_delay:
                        name, algorithm, reason = algorithm_for(self.config.player_algorithm_mode, player.pos, goal, dungeon.walkable)
                        runtime.player_algorithm = name
                        runtime.player_reason = reason
                        old = player.pos
                        player.calculate_path(goal, dungeon.walkable, algorithm)
                        player.step()
                        state_changed = state_changed or player.pos != old
                        last_player_move = now

                if now - last_enemy_move >= enemy_delay:
                    name, algorithm, reason = algorithm_for(self.config.enemy_algorithm_mode, enemy.pos, player.pos, dungeon.walkable)
                    runtime.enemy_algorithm = name
                    runtime.enemy_reason = reason
                    old = enemy.pos
                    enemy.calculate_path(player.pos, dungeon.walkable, algorithm)
                    enemy.step()
                    state_changed = state_changed or enemy.pos != old
                    last_enemy_move = now

                if enemy.pos == player.pos:
                    status = "Enemy caught the player. Replay is available."
                    logs.append("Run finished: enemy caught player.")
                    finished = True
                    state_changed = True
                elif player.pos == goal:
                    status = "Player reached the goal. Replay is available."
                    logs.append("Run finished: player reached goal.")
                    finished = True
                    state_changed = True

                if run_mode == "SIMULATION" and state_changed:
                    replay_frames.append(self._capture_replay_frame(player, enemy, runtime, status))

            self.draw_game(dungeon, player, enemy, goal, runtime, logs, status, algorithm_target)

            if run_mode == "SIMULATION":
                pygame.draw.rect(SCREEN, C_SELECT, replay_button, border_radius=5)
                draw_text("Replay (Y)", replay_button.x + 10, replay_button.y + 3, FONT_SMALL)

            pygame.display.flip()
            CLOCK.tick(FPS)

    def replay_screen(self, dungeon: Dungeon, goal: Point, frames: list[ReplayFrame]) -> None:
        if not frames:
            return

        index = 0
        playing = False
        last_advance = 0
        replay_speed = 1.0
        speed_values = [0.5, 1.0, 2.0, 4.0]

        buttons = {
            'first': pygame.Rect(MAP_WIDTH + 18, 570, 48, 36),
            'back': pygame.Rect(MAP_WIDTH + 72, 570, 48, 36),
            'play': pygame.Rect(MAP_WIDTH + 126, 570, 92, 36),
            'forward': pygame.Rect(MAP_WIDTH + 224, 570, 48, 36),
            'last': pygame.Rect(MAP_WIDTH + 278, 570, 48, 36),
        }
        timeline = pygame.Rect(30, HEIGHT - 54, MAP_WIDTH - 60, 10)

        while True:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.quit()
                    elif event.key in (pygame.K_m, pygame.K_y):
                        return
                    elif event.key == pygame.K_SPACE:
                        playing = not playing
                    elif event.key == pygame.K_LEFT:
                        playing = False
                        index = max(0, index - 1)
                    elif event.key == pygame.K_RIGHT:
                        playing = False
                        index = min(len(frames) - 1, index + 1)
                    elif event.key == pygame.K_j:
                        playing = False
                        index = max(0, index - 5)
                    elif event.key == pygame.K_l:
                        playing = False
                        index = min(len(frames) - 1, index + 5)
                    elif event.key == pygame.K_HOME:
                        playing = False
                        index = 0
                    elif event.key == pygame.K_END:
                        playing = False
                        index = len(frames) - 1
                    elif event.key == pygame.K_LEFTBRACKET:
                        si = speed_values.index(replay_speed)
                        replay_speed = speed_values[(si - 1) % len(speed_values)]
                    elif event.key == pygame.K_RIGHTBRACKET:
                        si = speed_values.index(replay_speed)
                        replay_speed = speed_values[(si + 1) % len(speed_values)]

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if buttons['first'].collidepoint(pos):
                        playing = False; index = 0
                    elif buttons['back'].collidepoint(pos):
                        playing = False; index = max(0, index - 1)
                    elif buttons['play'].collidepoint(pos):
                        playing = not playing
                    elif buttons['forward'].collidepoint(pos):
                        playing = False; index = min(len(frames) - 1, index + 1)
                    elif buttons['last'].collidepoint(pos):
                        playing = False; index = len(frames) - 1
                    elif timeline.collidepoint(pos):
                        ratio = (pos[0] - timeline.x) / max(1, timeline.width)
                        index = min(len(frames)-1, max(0, round(ratio * (len(frames)-1))))
                        playing = False

            delay = int(240 / replay_speed)
            if playing and now - last_advance >= delay:
                if index < len(frames) - 1:
                    index += 1
                else:
                    playing = False
                last_advance = now

            frame = frames[index]
            SCREEN.fill(C_BG)
            draw_dungeon(dungeon)

            if self.config.show_visited:
                draw_nodes(frame.enemy_visited, C_VISITED, 16)
                draw_nodes(frame.player_visited, pygame.Color('#2d7b78'), 18)
            if self.config.show_paths:
                draw_path(list(frame.enemy_path), C_PATH_D, 12)
                draw_path(list(frame.player_path), C_PATH_A, 8)

            pygame.draw.rect(SCREEN, C_GOAL, tile_rect(goal).inflate(-8, -8))
            pygame.draw.rect(SCREEN, C_PLAYER, tile_rect(frame.player_pos).inflate(-6, -6))
            pygame.draw.rect(SCREEN, C_ENEMY, tile_rect(frame.enemy_pos).inflate(-6, -6))

            panel = pygame.Rect(MAP_WIDTH, 0, INSPECTOR_WIDTH, HEIGHT)
            pygame.draw.rect(SCREEN, C_PANEL, panel)
            x = MAP_WIDTH + 16
            y = 18
            draw_text('SIMULATION REPLAY', x, y, FONT_MID)
            y += 42
            draw_text(f'Frame: {index + 1}/{len(frames)}', x, y)
            y += 27
            draw_text(f'Playback: {"PLAY" if playing else "PAUSE"}', x, y)
            y += 27
            draw_text(f'Speed: {replay_speed:g}x', x, y)
            y += 35
            draw_text('Player', x, y, FONT, C_PATH_A); y += 25
            draw_text(f'Position: {frame.player_pos}', x, y, FONT_SMALL); y += 19
            draw_text(f'Algorithm: {frame.player_algorithm}', x, y, FONT_SMALL); y += 19
            for line in wrap_text(frame.player_reason, FONT_SMALL, INSPECTOR_WIDTH - 32)[:3]:
                draw_text(line, x, y, FONT_SMALL, C_MUTED); y += 17
            y += 10
            draw_text('Enemy', x, y, FONT, C_PATH_D); y += 25
            draw_text(f'Position: {frame.enemy_pos}', x, y, FONT_SMALL); y += 19
            draw_text(f'Algorithm: {frame.enemy_algorithm}', x, y, FONT_SMALL); y += 19
            for line in wrap_text(frame.enemy_reason, FONT_SMALL, INSPECTOR_WIDTH - 32)[:3]:
                draw_text(line, x, y, FONT_SMALL, C_MUTED); y += 17
            y += 12
            draw_text('Status', x, y, FONT); y += 24
            for line in wrap_text(frame.status, FONT_SMALL, INSPECTOR_WIDTH - 32):
                draw_text(line, x, y, FONT_SMALL, C_MUTED); y += 17

            labels = {'first': '|<', 'back': '<', 'play': 'Pause' if playing else 'Play', 'forward': '>', 'last': '>|'}
            for key, rect in buttons.items():
                pygame.draw.rect(SCREEN, C_SELECT, rect, border_radius=5)
                text = FONT_SMALL.render(labels[key], True, C_TEXT)
                SCREEN.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))

            pygame.draw.rect(SCREEN, C_PANEL_2, timeline, border_radius=5)
            progress = 0 if len(frames) == 1 else index / (len(frames)-1)
            filled = pygame.Rect(timeline.x, timeline.y, int(timeline.width * progress), timeline.height)
            pygame.draw.rect(SCREEN, C_PATH_A, filled, border_radius=5)
            knob_x = timeline.x + int(timeline.width * progress)
            pygame.draw.circle(SCREEN, C_TEXT, (knob_x, timeline.centery), 7)

            draw_text('LEFT/RIGHT frame | J/L +/-5 | SPACE play | HOME/END | [ ] speed | Y/M back', 26, HEIGHT - 31, FONT_SMALL)
            pygame.display.flip()
            CLOCK.tick(FPS)

    def _change_speed(self, direction: int) -> None:
        index = SPEED_OPTIONS.index(self.config.speed)
        self.config.speed = SPEED_OPTIONS[(index + direction) % len(SPEED_OPTIONS)]

    def draw_game(
        self,
        dungeon: Dungeon,
        player: Player,
        enemy: Enemy,
        goal: Point,
        runtime: RuntimeInfo,
        logs: deque[str],
        status: str,
        algorithm_target: str,
    ) -> None:
        SCREEN.fill(C_BG)
        draw_dungeon(dungeon)

        if self.config.show_visited:
            if enemy.last_result:
                draw_nodes(enemy.last_result.visited, C_VISITED, 16)
            if runtime.run_mode == "SIMULATION" and player.last_result:
                draw_nodes(player.last_result.visited, pygame.Color("#2d7b78"), 18)

        if self.config.show_paths:
            draw_path(enemy.path, C_PATH_D, 12)
            if runtime.run_mode == "SIMULATION":
                draw_path(player.auto_path, C_PATH_A, 8)

        pygame.draw.rect(SCREEN, C_GOAL, tile_rect(goal).inflate(-8, -8))
        pygame.draw.rect(SCREEN, C_PLAYER, tile_rect(player.pos).inflate(-6, -6))
        pygame.draw.rect(SCREEN, C_ENEMY, tile_rect(enemy.pos).inflate(-6, -6))

        panel = pygame.Rect(MAP_WIDTH, 0, INSPECTOR_WIDTH, HEIGHT)
        pygame.draw.rect(SCREEN, C_PANEL, panel)

        if self.config.show_inspector:
            self.draw_game_inspector(
                panel,
                dungeon,
                player,
                enemy,
                goal,
                runtime,
                logs,
                status,
                algorithm_target,
            )
        else:
            draw_text("Inspector hidden", MAP_WIDTH + 18, 24, FONT_MID)
            draw_text("TAB = show", MAP_WIDTH + 18, 58, FONT_SMALL, C_MUTED)

        pygame.draw.rect(SCREEN, C_PANEL, pygame.Rect(0, HEIGHT - 30, MAP_WIDTH, 30))
        draw_text(
            f"Target: {algorithm_target} | T switch actor | 1-7 algorithm | 0 Auto | ,/. cycle | P Paths | V Visited",
            8,
            HEIGHT - 23,
            FONT_SMALL,
        )

    def draw_game_inspector(
        self,
        rect: pygame.Rect,
        dungeon: Dungeon,
        player: Player,
        enemy: Enemy,
        goal: Point,
        runtime: RuntimeInfo,
        logs: deque[str],
        status: str,
        algorithm_target: str,
    ) -> None:
        x = rect.x + 15
        y = 14
        width = rect.width - 30

        def section(title: str, color: pygame.Color = C_TEXT):
            nonlocal y
            draw_text(title, x, y, FONT_MID, color)
            y += 31

        def line(label: str, value: str, muted: bool = False):
            nonlocal y
            color = C_MUTED if muted else C_TEXT
            for wrapped in wrap_text(f"{label}: {value}", FONT_SMALL, width):
                draw_text(wrapped, x, y, FONT_SMALL, color)
                y += 17
            y += 2

        section("ALGORITHM INSPECTOR")
        line("Mode", runtime.run_mode)
        line("Control target", algorithm_target)
        line("Player setting", self.config.player_algorithm_mode)
        line("Enemy setting", self.config.enemy_algorithm_mode)
        line("Difficulty", self.config.difficulty)
        line("Speed", f"{self.config.speed:g}x")
        line("Status", status, True)

        y += 3
        section("PLAYER", C_PATH_A)

        if runtime.run_mode == "MANUAL":
            line("Control", "Human / keyboard")
            line("Pathfinding", "Not used for player")
        else:
            line("Algorithm", runtime.player_algorithm)
            line("Why", runtime.player_reason, True)
            self._result_lines(player.last_result, line)
            if player.auto_path and len(player.auto_path) > 1:
                line("Next tile", str(player.auto_path[1]))

        y += 3
        section("ENEMY", C_PATH_D)
        line("Algorithm", runtime.enemy_algorithm)
        line("Why", runtime.enemy_reason, True)
        self._result_lines(enemy.last_result, line)
        if enemy.path and len(enemy.path) > 1:
            line("Next tile", str(enemy.path[1]))

        y += 3
        line("Player", str(player.pos))
        line("Enemy", str(enemy.pos))
        line("Goal", str(goal))
        line("Walkable nodes", str(len(dungeon.walkable)))
        line("Rooms", str(len(dungeon.rooms)))
        line("Seed", str(dungeon.seed))

        if y < HEIGHT - 105:
            section("EVENT LOG")
            for item in list(logs)[-4:]:
                for wrapped in wrap_text(item, FONT_SMALL, width):
                    draw_text(wrapped, x, y, FONT_SMALL, C_MUTED)
                    y += 16

    def _result_lines(self, result: PathResult | None, line) -> None:
        if not result:
            line("Search", "Waiting...", True)
            return
        line("Visited nodes", str(result.visited_nodes))
        line("Path length", str(max(0, len(result.path) - 1)))
        line("Search time", f"{result.elapsed_ms:.4f} ms")

    def visualizer_screen(self) -> None:
        dungeon = Dungeon(self.config.difficulty)
        start = dungeon.player_spawn
        goal = dungeon.goal_spawn
        algorithm_name = "A*"
        autoplay = False
        step_index = 0
        last_step_time = 0

        def make_trace(name: str) -> TraceResult:
            mapping = {
                "A*": astar_trace,
                "Dijkstra": dijkstra_trace,
                "BFS": bfs_trace,
                "Greedy": greedy_trace,
                "DFS": dfs_trace,
                "Bidirectional BFS": bidirectional_bfs_trace,
                "Weighted A*": weighted_astar_trace,
            }
            return mapping[name](start, goal, dungeon.walkable)

        trace = make_trace(algorithm_name)

        while True:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.quit()
                    elif event.key == pygame.K_m:
                        return
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7):
                        algorithm_name = {
                            pygame.K_1: "A*",
                            pygame.K_2: "Dijkstra",
                            pygame.K_3: "BFS",
                            pygame.K_4: "Greedy",
                            pygame.K_5: "DFS",
                            pygame.K_6: "Bidirectional BFS",
                            pygame.K_7: "Weighted A*",
                        }[event.key]
                        trace = make_trace(algorithm_name)
                        step_index = 0
                        autoplay = False
                    elif event.key in (pygame.K_n, pygame.K_RIGHT):
                        step_index = min(step_index + 1, max(0, len(trace.steps) - 1))
                    elif event.key == pygame.K_LEFT:
                        step_index = max(0, step_index - 1)
                    elif event.key == pygame.K_HOME:
                        step_index = 0
                    elif event.key == pygame.K_END:
                        step_index = max(0, len(trace.steps) - 1)
                    elif event.key == pygame.K_SPACE:
                        autoplay = not autoplay
                    elif event.key == pygame.K_r:
                        dungeon = Dungeon(self.config.difficulty)
                        start = dungeon.player_spawn
                        goal = dungeon.goal_spawn
                        trace = make_trace(algorithm_name)
                        step_index = 0
                    elif event.key == pygame.K_LEFTBRACKET:
                        self._change_speed(-1)
                    elif event.key == pygame.K_RIGHTBRACKET:
                        self._change_speed(1)

            step_delay = int(220 / self.config.speed)
            if autoplay and trace.steps and now - last_step_time >= step_delay:
                if step_index < len(trace.steps) - 1:
                    step_index += 1
                else:
                    autoplay = False
                last_step_time = now

            SCREEN.fill(C_BG)
            draw_dungeon(dungeon)
            step = trace.steps[step_index] if trace.steps else None
            if step:
                if self.config.show_visited:
                    draw_nodes(step.closed_nodes, C_VISITED, 10)
                    draw_nodes(step.open_nodes, C_OPEN, 12)
                pygame.draw.rect(SCREEN, C_CURRENT, tile_rect(step.current).inflate(-4, -4))

            if trace.steps and step_index == len(trace.steps) - 1:
                draw_path(trace.result.path, C_TEXT, 8)

            pygame.draw.rect(SCREEN, C_PLAYER, tile_rect(start).inflate(-6, -6))
            pygame.draw.rect(SCREEN, C_GOAL, tile_rect(goal).inflate(-6, -6))
            panel = pygame.Rect(MAP_WIDTH, 0, INSPECTOR_WIDTH, HEIGHT)
            pygame.draw.rect(SCREEN, C_PANEL, panel)

            x = MAP_WIDTH + 16; y = 16
            draw_text("STEP VISUALIZER", x, y, FONT_MID); y += 42
            draw_text(f"Algorithm: {algorithm_name}", x, y); y += 27
            draw_text(f"Step: {step_index + 1}/{max(1, len(trace.steps))}", x, y); y += 27
            draw_text(f"Speed: {self.config.speed:g}x", x, y); y += 34

            if step:
                labels = [
                    ("Current node", str(step.current)),
                    ("G / cost-so-far", str(step.g_cost)),
                    ("H / heuristic", str(step.h_cost)),
                    ("Priority value", str(step.f_cost)),
                    ("Open set", str(len(step.open_nodes))),
                    ("Closed set", str(len(step.closed_nodes))),
                ]
                for label, value in labels:
                    draw_text(f"{label}: {value}", x, y, FONT_SMALL); y += 20
                if step.note:
                    for note_line in wrap_text(step.note, FONT_SMALL, INSPECTOR_WIDTH - 32):
                        draw_text(note_line, x, y, FONT_SMALL, C_MUTED); y += 16

            y += 8
            draw_text("Meaning", x, y, FONT); y += 26
            meaning = {
                "A*": "Priority = G + H. Shortest-path optimal with this Manhattan heuristic.",
                "Dijkstra": "Priority = G. Explores by cheapest known distance.",
                "BFS": "FIFO layers. Shortest-path optimal because every move costs 1.",
                "Greedy": "Priority = H only. Goal-directed and often fast, but can be non-optimal.",
                "DFS": "LIFO stack. Goes deep until a dead end, then backtracks. Path may be far from shortest.",
                "Bidirectional BFS": "Two BFS waves expand from Start and Goal until they meet. Optimal on this unit-cost grid.",
                "Weighted A*": "Priority = G + 2H. Stronger heuristic bias usually expands fewer nodes, but can lose optimality.",
            }[algorithm_name]
            for line in wrap_text(meaning, FONT_SMALL, INSPECTOR_WIDTH - 32):
                draw_text(line, x, y, FONT_SMALL, C_MUTED); y += 17

            y += 12
            draw_text("Controls", x, y, FONT); y += 26
            controls = [
                "1 A* | 2 Dijkstra | 3 BFS",
                "4 Greedy | 5 DFS",
                "6 Bidirectional | 7 Weighted A*",
                "N/RIGHT next | LEFT previous",
                "SPACE autoplay | [ / ] speed",
                "R new dungeon | M menu",
            ]
            for item in controls:
                draw_text(item, x, y, FONT_SMALL, C_MUTED); y += 20

            pygame.display.flip(); CLOCK.tick(FPS)

    def compare_screen(self) -> None:
        dungeon = Dungeon(self.config.difficulty)
        selected = 0
        algorithms = [
            ("A*", astar, C_PATH_A),
            ("Dijkstra", dijkstra, C_PATH_D),
            ("BFS", bfs, C_PATH_BFS),
            ("Greedy", greedy_best_first, C_PATH_GREEDY),
            ("DFS", dfs, C_PATH_DFS),
            ("Bidirectional BFS", bidirectional_bfs, C_PATH_BIDIR),
            ("Weighted A*", weighted_astar, C_PATH_WEIGHTED),
        ]

        while True:
            start = dungeon.player_spawn
            goal = dungeon.goal_spawn
            results = [(name, fn(start, goal, dungeon.walkable), color) for name, fn, color in algorithms]

            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.quit()
                        elif event.key == pygame.K_m:
                            return
                        elif event.key == pygame.K_r:
                            dungeon = Dungeon(self.config.difficulty); waiting = False
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            selected = (selected - 1) % len(results)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            selected = (selected + 1) % len(results)

                SCREEN.fill(C_BG)
                draw_dungeon(dungeon)
                name, selected_result, selected_color = results[selected]
                draw_path(selected_result.path, selected_color, 8)
                pygame.draw.rect(SCREEN, C_PLAYER, tile_rect(start).inflate(-6, -6))
                pygame.draw.rect(SCREEN, C_GOAL, tile_rect(goal).inflate(-6, -6))

                panel = pygame.Rect(MAP_WIDTH, 0, INSPECTOR_WIDTH, HEIGHT)
                pygame.draw.rect(SCREEN, C_PANEL, panel)
                x = MAP_WIDTH + 14; y = 14
                draw_text("COMPARE 7 ALGORITHMS", x, y, FONT_MID); y += 34
                draw_text(f"Highlighted path: {name}", x, y, FONT_SMALL, selected_color); y += 28

                for idx, (alg_name, result, color) in enumerate(results):
                    card = pygame.Rect(x, y, INSPECTOR_WIDTH - 28, 69)
                    if idx == selected:
                        pygame.draw.rect(SCREEN, C_PANEL_2, card, border_radius=7)
                    draw_text(alg_name, x + 7, y + 6, FONT_SMALL, color)
                    draw_text(
                        f"Len {max(0, len(result.path)-1)} | Vis {result.visited_nodes}",
                        x + 7, y + 27, FONT_SMALL
                    )
                    optimal_note = "optimal" if alg_name in ("A*", "Dijkstra", "BFS", "Bidirectional BFS") else "not guaranteed optimal"
                    draw_text(f"{result.elapsed_ms:.4f} ms | {optimal_note}", x + 7, y + 47, FONT_SMALL, C_MUTED)
                    y += 73

                draw_text(f"Difficulty: {self.config.difficulty} | Seed: {dungeon.seed}", x, y, FONT_SMALL, C_MUTED); y += 18
                draw_text("LEFT/RIGHT highlight | R new map | M menu", x, y, FONT_SMALL, C_MUTED)
                pygame.display.flip(); CLOCK.tick(FPS)

    def benchmark_screen(self) -> None:
        dungeon = Dungeon(self.config.difficulty)
        summaries = self._run_benchmark(dungeon)
        runs = 50
        colors = {
            "A*": C_BAR_A,
            "Dijkstra": C_BAR_D,
            "BFS": C_BAR_BFS,
            "Greedy": C_BAR_GREEDY,
            "DFS": C_BAR_DFS,
            "Bidirectional BFS": C_BAR_BIDIR,
            "Weighted A*": C_BAR_WEIGHTED,
        }

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.quit()
                    elif event.key == pygame.K_m:
                        return
                    elif event.key == pygame.K_r:
                        dungeon = Dungeon(self.config.difficulty); summaries = self._run_benchmark(dungeon)
                    elif event.key == pygame.K_b:
                        summaries = self._run_benchmark(dungeon)

            SCREEN.fill(C_BG)
            center_text("BENCHMARK DASHBOARD", 28, FONT_BIG)
            center_text(
                        f"{runs} identical start/goal pairs per algorithm | "
                        f"{self.config.difficulty} | Seed: {dungeon.seed}",
                        77,
                        FONT_SMALL,
                        C_MUTED,
                        )

            self._multi_metric_bars(55, 105, "Average execution time (ms)", summaries, lambda s: s.avg_time_ms, colors)
            self._multi_metric_bars(55, 290, "Average visited nodes", summaries, lambda s: s.avg_visited_nodes, colors)
            self._multi_metric_bars(55, 475, "Average path length", summaries, lambda s: s.avg_path_length, colors)

            draw_text("Optimal here: A*, Dijkstra, BFS, Bidirectional BFS. Greedy/DFS/Weighted A* may trade path quality for search behavior.", 55, HEIGHT - 45, FONT_SMALL, C_MUTED)
            draw_text("B rerun | R new dungeon + rerun | M menu | CSV: results/benchmark.csv", 55, HEIGHT - 23, FONT_SMALL, C_MUTED)
            pygame.display.flip(); CLOCK.tick(FPS)

    def _multi_metric_bars(self, x, y, title, summaries, getter, colors) -> None:
        draw_text(title, x, y, FONT)
        values = [getter(s) for s in summaries]
        max_value = max(values + [0.000001])
        label_width = 150
        bar_x = x + label_width
        max_bar = 650
        row_y = y + 28
        for summary in summaries:
            value = getter(summary)
            draw_text(summary.algorithm, x, row_y + 1, FONT_SMALL, colors[summary.algorithm])
            pygame.draw.rect(SCREEN, C_PANEL_2, pygame.Rect(bar_x, row_y, max_bar, 14))
            width = int(max_bar * value / max_value)
            pygame.draw.rect(SCREEN, colors[summary.algorithm], pygame.Rect(bar_x, row_y, width, 14))
            draw_text(f"{value:.4f}", bar_x + max_bar + 10, row_y - 1, FONT_SMALL)
            row_y += 20

    def _run_benchmark(self, dungeon: Dungeon) -> list[BenchmarkSummary]:
        return run_benchmark_suite(
            dungeon.walkable,
            runs=50,
            seed=dungeon.seed,
            output_path="results/benchmark.csv",
        )



def run() -> None:
    App().run()
