# Procedural Dungeon AI Pathfinding Simulator — V4

A Python/Pygame bachelor-project prototype for visualizing, replaying, comparing, and benchmarking pathfinding algorithms inside procedurally generated dungeons.

## Algorithms

The project now contains **7 algorithms**:

1. **A\*** — priority `G + H`; optimal here with Manhattan heuristic.
2. **Dijkstra** — expands the cheapest known distance; optimal.
3. **BFS** — explores layer by layer; optimal because every move costs 1.
4. **Greedy Best-First Search** — priority `H`; often goal-directed, but not guaranteed optimal.
5. **DFS** — explores deeply then backtracks; finds a path, but not necessarily the shortest.
6. **Bidirectional BFS** — BFS from both Start and Goal until the searches meet; optimal on this unit-cost grid.
7. **Weighted A\*** — priority `G + 2H`; stronger heuristic bias can reduce search but shortest-path optimality is not guaranteed.

## Auto Algorithm Mode

`AUTO` remains intentionally explainable and only selects algorithms that preserve shortest-path optimality in the current unit-cost grid:

- very close target -> **BFS**
- medium-short route -> **Dijkstra**
- long route + large search space -> **Bidirectional BFS**
- otherwise -> **A\***

The live Inspector shows the exact reason for each automatic choice.

## Main Features

- Procedural room-and-corridor dungeon generation
- Easy / Medium / Hard environments
- Manual Play
- AI Simulation
- Simulation Replay
- Algorithm Inspector
- Step-by-Step Algorithm Visualizer
- Compare 7 Algorithms
- Benchmark Dashboard
- CSV benchmark export
- Visited-node visualization
- Path visualization
- Pause and simulation-speed controls


## Independent Player and Enemy Algorithms

Player and Enemy no longer share one global pathfinding mode. They can use different algorithms during the same Simulation.

Examples:
- Player = A*, Enemy = Greedy
- Player = Bidirectional BFS, Enemy = DFS
- Player = Auto, Enemy = Weighted A*

In **Settings**, choose `Player Algorithm` and `Enemy Algorithm` separately.

During Manual/Simulation:
- `T` switches the algorithm-control target between Player and Enemy (Simulation only).
- `1` A*
- `2` Dijkstra
- `3` BFS
- `4` Greedy
- `5` DFS
- `6` Bidirectional BFS
- `7` Weighted A*
- `0` Auto
- `,` previous algorithm
- `.` next algorithm

In Manual mode the player is human-controlled, so algorithm hotkeys target the Enemy.
The Algorithm Inspector displays both configured modes separately, and Replay stores the actual Player and Enemy algorithms used in every frame.

## Simulation Replay

Simulation states are captured as real replay frames. Replay does **not** recalculate the simulation.

Each frame stores:

- player position
- enemy position
- player path
- enemy path
- visited nodes
- selected algorithms
- automatic-selection explanation
- simulation status

Replay controls:

- `LEFT` / `RIGHT` — previous / next frame
- `J` / `L` — jump 5 frames backward / forward
- `SPACE` — play / pause
- `HOME` / `END` — first / last frame
- `[` / `]` — replay speed
- mouse timeline — seek directly
- `Y` or `M` — return from replay

## Manual / Simulation Algorithm Keys

- `1` — A\*
- `2` — Dijkstra
- `3` — BFS
- `4` — Greedy Best-First
- `5` — DFS
- `6` — Bidirectional BFS
- `7` — Weighted A\*
- `0` — Auto

Other controls:

- `P` — paths on/off
- `V` — visited nodes on/off
- `TAB` — Inspector on/off
- `SPACE` — pause/resume
- `[` / `]` — simulation speed
- `R` — new dungeon
- `Y` — open Replay in Simulation mode
- `M` — main menu
- `ESC` — exit

## Algorithm Visualizer

Keys `1` through `7` select the seven algorithms.

The visualizer shows:

- current node
- open/frontier nodes
- closed/visited nodes
- G cost / depth
- H heuristic when relevant
- priority value
- final path
- explanatory note for the algorithm's current priority/search behavior

Visualizer controls:

- `N` / `RIGHT` — next search step
- `LEFT` — previous step
- `SPACE` — autoplay
- `HOME` / `END` — first / final step
- `[` / `]` — speed
- `R` — new dungeon
- `M` — menu

## Compare Mode

All seven algorithms run on the **same dungeon, same start, and same goal**.

For each algorithm the program reports:

- path length
- visited nodes
- execution time
- whether shortest-path optimality is guaranteed in this project setup

Use `LEFT` / `RIGHT` to highlight each algorithm's path on the map.

## Benchmark Dashboard

The benchmark uses identical random start/goal pairs for every algorithm and measures:

- average execution time
- average visited nodes
- average path length

Results are displayed in the application and exported to:

`results/benchmark.csv`

## Installation

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependency:

```bash
pip install -r requirements.txt
```

Run:

```bash
python main.py
```

## Files

- `main.py` — entry point
- `app.py` — menus, game/simulation, replay, visualizer, compare, benchmark UI
- `settings.py` — constants, difficulty, speed, algorithm options
- `dungeon.py` — procedural dungeon generator
- `entities.py` — player and enemy
- `pathfinding.py` — all seven pathfinding algorithms and visualizer traces
- `algorithm_selector.py` — explainable Auto-selection rules
- `benchmark.py` — fair repeated experiments and CSV output
- `ARCHITECTURE.md` — system design
- `REPORT_OUTLINE.md` — suggested bachelor-project report structure
- `TEST_REPORT.txt` — automated core-test results

## Important Academic Interpretation

The seven algorithms are intentionally not all equivalent.

### Optimal on the current unit-cost grid

- A\*
- Dijkstra
- BFS
- Bidirectional BFS

### Not guaranteed to return the shortest path

- Greedy Best-First Search
- DFS
- Weighted A\* with weight 2

This difference makes the project useful for discussing the trade-off between **path quality, search effort, heuristic guidance, and execution behavior**.
