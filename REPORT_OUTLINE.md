# Bachelor Project Report Outline — V4

## Suggested English Title
**Procedural Dungeon Pathfinding Simulator: Visualization, Replay, and Comparative Analysis of Seven Search Algorithms**

## Suggested Persian Title
**شبیه‌ساز مسیریابی در محیط‌های رویه‌ای با قابلیت مصورسازی، بازپخش و مقایسه هفت الگوریتم جستجو**

## 1. Introduction
- problem definition
- motivation
- objectives
- project scope

## 2. Background
- tile maps and graphs
- node and edge
- shortest path
- procedural content generation
- uninformed vs informed search
- heuristic functions
- Manhattan distance

## 3. Algorithms

### 3.1 Breadth-First Search (BFS)
- FIFO queue
- layer-by-layer expansion
- shortest path on unweighted/unit-cost graphs

### 3.2 Depth-First Search (DFS)
- LIFO stack
- deep exploration and backtracking
- completeness in finite connected graphs
- lack of shortest-path guarantee

### 3.3 Dijkstra
- cumulative path cost
- priority queue
- shortest path with non-negative costs

### 3.4 Greedy Best-First Search
- heuristic-only priority
- goal-directed search
- speed/path-quality trade-off

### 3.5 A*
- `F = G + H`
- Manhattan heuristic
- optimality with admissible/consistent heuristic in this environment

### 3.6 Weighted A*
- `F = G + W*H`
- project uses `W = 2`
- greater heuristic influence
- potential reduction in search effort
- loss of guaranteed optimality

### 3.7 Bidirectional BFS
- simultaneous search from start and goal
- meeting point
- reconstruction of two partial paths
- shortest path in unit-cost graph

## 4. Procedural Dungeon Generation
- random rooms
- intersection prevention
- corridor creation
- connectivity
- difficulty presets
- seeds and reproducibility

## 5. Software Architecture
- settings
- dungeon layer
- entity layer
- pathfinding layer
- selector layer
- benchmark layer
- Pygame application/UI layer

## 6. AI Simulation
- autonomous player -> goal
- autonomous enemy -> player
- dynamic replanning
- run termination conditions

## 7. Explainable Auto Selection
Describe the rule-based policy and why only shortest-path-safe algorithms are candidates in Auto mode.

## 8. Replay System
- immutable historical frames
- forward/backward playback
- timeline seeking
- deterministic inspection of a completed run

## 9. Step-by-Step Visualization
- frontier/open set
- closed/visited set
- current node
- G, H and priority values
- bidirectional search waves

## 10. Experimental Methodology
Run all seven algorithms using identical conditions.

Metrics:
- execution time
- visited nodes
- path length

Test on:
- Easy
- Medium
- Hard
- multiple seeds

## 11. Results and Discussion
Compare:
- optimal algorithms
- non-optimal algorithms
- heuristic vs uninformed algorithms
- path quality vs visited-node count
- search-space effects

Important expected patterns, not guaranteed on every individual map:
- A* often expands fewer nodes than Dijkstra/BFS.
- BFS and Dijkstra have similar behavior when every edge cost equals 1.
- Bidirectional BFS can reduce expansion for longer routes.
- Greedy can be very directed but can return longer routes.
- DFS can produce substantially longer paths.
- Weighted A* trades stronger heuristic bias for possible path suboptimality.

## 12. Limitations
- four-direction movement
- unit movement cost
- one enemy
- no moving obstacles inside the graph
- rule-based Auto selector

## 13. Future Work
- weighted terrain
- Uniform Cost Search experiments on weighted maps
- Jump Point Search
- D* Lite / dynamic replanning
- multiple agents
- behavior trees
- reinforcement learning
- learning-based algorithm selection

## 14. Conclusion
Summarize the algorithmic, game-development, visualization, replay, and experimental contributions.

## Additional Experiment: Heterogeneous Agent Algorithms
Run Player and Enemy with different pathfinding strategies in the same simulation. Example pairs include A* vs Greedy, Bidirectional BFS vs DFS, and Auto vs Weighted A*. Discuss how algorithm choice changes search effort, path quality, and pursuit behavior.
