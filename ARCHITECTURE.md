# Architecture — V4

## 1. Procedural Environment Layer — `dungeon.py`

Creates a connected tile-based dungeon from random rooms and corridors. Every walkable tile becomes a graph node; legal four-direction movement creates graph edges.

Difficulty changes room count and room size, producing different search spaces.

## 2. Search Layer — `pathfinding.py`

Contains seven search algorithms:

- A*
- Dijkstra
- BFS
- Greedy Best-First Search
- DFS
- Bidirectional BFS
- Weighted A* (`weight = 2`)

A normal search returns `PathResult`:

- path
- number of expanded/visited nodes
- elapsed search time
- visited-node set

Visualizer versions return `TraceResult`, which contains individual `SearchStep` snapshots.

## 3. Explainable Decision Layer — `algorithm_selector.py`

`AUTO` is a transparent rule-based policy rather than machine learning.

Inputs:

- Manhattan distance
- number of walkable nodes

Possible automatic choices:

- BFS
- Dijkstra
- Bidirectional BFS
- A*

Greedy, DFS, and Weighted A* are excluded from Auto because they do not guarantee shortest paths in the configured form.

## 4. Entity Layer — `entities.py`

`Player` and `Enemy` store positions, calculated paths, and last search results. They receive a search function instead of owning pathfinding logic themselves.

## 5. Simulation + Replay Layer — `app.py`

Simulation repeatedly:

1. chooses an algorithm,
2. calculates player -> goal,
3. moves the player,
4. chooses an enemy algorithm,
5. calculates enemy -> player,
6. moves the enemy,
7. captures a replay frame,
8. renders live diagnostics.

`ReplayFrame` stores the actual historical state. Therefore forward/backward replay is deterministic and does not rerun the algorithms.

## 6. Visualization Layer — `app.py`

The Step Visualizer consumes trace snapshots from `pathfinding.py` and draws:

- frontier/open nodes
- closed/visited nodes
- current expanded node
- costs / priority
- final path

For Bidirectional BFS the visualized frontier/closed sets combine the two search waves; the step note indicates which side is being expanded.

## 7. Experimental Layer — `benchmark.py`

The benchmark generates one list of start/goal pairs and runs **every algorithm on exactly those same pairs**.

Metrics:

- execution time
- visited/expanded nodes
- path length

This provides controlled comparative experiments.

## 8. Comparison Layer — `app.py`

Compare Mode runs all seven algorithms on one identical map/start/goal configuration and highlights one resulting path at a time.

## Algorithm Families

### Uninformed searches

- BFS
- DFS
- Dijkstra
- Bidirectional BFS

### Heuristic / informed searches

- Greedy Best-First
- A*
- Weighted A*

## Optimality in this project

Because all four-direction moves currently cost 1:

- BFS: optimal
- Dijkstra: optimal
- A* with Manhattan heuristic: optimal
- Bidirectional BFS: optimal

The following are not guaranteed optimal:

- DFS
- Greedy Best-First
- Weighted A* with weight > 1

## Independent actor algorithm configuration

`AppConfig` stores two independent values:

- `player_algorithm_mode`
- `enemy_algorithm_mode`

In AI Simulation, the Player selects/calculates its route to the Goal using the Player setting, while the Enemy independently selects/calculates its route to the Player using the Enemy setting. This enables heterogeneous algorithm experiments in a single run.

The active keyboard target can be switched during Simulation, so one actor's algorithm can change without changing the other actor. Replay frames record the resolved algorithm and explanation for each actor independently.
