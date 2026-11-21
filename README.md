# AI Disaster Rescue Simulator

An interactive Python-based AI application that simulates disaster rescue operations using Artificial Intelligence search algorithms, optimization techniques, and Constraint Satisfaction Problems (CSP).

The simulator helps emergency response teams identify optimal rescue routes, prioritize victims based on severity and travel distance, and allocate rescue teams according to their skills and available capacity.

## 📌 Project Overview

During disaster situations, rescue teams must make critical decisions under limited time and resources.

This project models a disaster-affected area as a grid-based environment containing roads, blocked paths, danger zones, a rescue base, and victims requiring assistance.

It applies multiple AI algorithms to solve three major problems:

- **Pathfinding:** Finding routes from the rescue base to victims.
- **Victim Ordering:** Determining the most effective sequence for rescuing victims.
- **Team Allocation:** Assigning suitable rescue teams to victims while respecting skill requirements and capacity constraints.

The application provides a graphical interface where users can modify disaster scenarios and compare the performance of different AI algorithms.

## Key Features

### 1. Interactive Disaster Map
- Grid-based disaster environment.
- Paint cells as roads, blocked areas, or danger zones.
- Move the rescue base to different locations.
- Add, edit, and remove victims.
- Assign severity levels and required skills to victims.
- Generate random disaster maps.
- Restore the default scenario or clear the map.

### 2. AI-Based Pathfinding

Six search algorithms are implemented:

| Algorithm | Description |
|---|---|
| BFS | Explores nodes level by level. |
| DFS | Explores deeper nodes before backtracking. |
| Greedy Best-First Search | Selects nodes using a heuristic. |
| UCS | Finds the minimum-cost path using accumulated path cost. |
| A* | Combines path cost and heuristic information. |
| Weighted A* | Uses a weighted heuristic to influence search behavior. |

**Additional functionality:**
- Route visualization.
- Animated search exploration.
- Path cost calculation.
- Number of expanded nodes.
- Execution time measurement.
- Comparison of search algorithms.

Danger zones have a movement cost of 5, while normal roads have a movement cost of 1.

Manhattan distance is used as the heuristic for informed search algorithms.

### 3. Victim Ordering and Optimization

The simulator implements five algorithms to determine the order in which victims should be rescued.

| Algorithm | Purpose |
|---|---|
| Severity First | Prioritizes victims with higher severity. |
| Nearest First | Selects the closest remaining victim. |
| Hill Climbing | Improves the rescue sequence through local search. |
| Simulated Annealing | Explores alternative rescue sequences using probabilistic acceptance. |
| Brute Force | Evaluates all possible victim orderings to find the minimum score. |

The optimization objective considers:

- Total travel distance.
- Victim severity.
- Time spent waiting for rescue.

A lower mission score indicates a better rescue sequence.

Brute Force is limited to a maximum of 7 victims.

### 4. Constraint Satisfaction Problem (CSP)

Rescue teams must be assigned to victims based on their required skills and team capacities.

Three allocation strategies are implemented:

1. **Plain Backtracking:** Assigns teams using recursive backtracking.
2. **MRV + Forward Checking:** Selects the most constrained victim first and eliminates invalid future assignments.
3. **Greedy Allocation:** Assigns available teams without backtracking.

The application displays:

- Team assignments.
- Number of assignment attempts.
- Execution time.
- Whether a valid allocation exists.

### 5. Performance Comparison

The application provides comparison interfaces for:

- Pathfinding algorithms.
- Victim ordering algorithms.
- Team allocation algorithms.

Performance measurements include execution time, path cost, expanded nodes, and optimization scores where applicable.

### 6. Scenario Management

- Save disaster scenarios as JSON files.
- Load previously saved scenarios.
- Preserve the grid, rescue base, victims, and rescue teams.
- Modify and experiment with different disaster environments.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Tkinter | Graphical user interface |
| ttk | GUI components and styling |
| Heapq | Priority queue implementation |
| Collections | Queue and deque operations |
| JSON | Scenario storage and retrieval |
| Math | Mathematical calculations |
| Random | Randomized maps and optimization |
| Itertools | Permutations and brute-force search |
| Time | Algorithm execution-time measurement |

## 🧠 AI Concepts Implemented

- Uninformed Search
- Informed Search
- Heuristic Search
- Optimal Pathfinding
- Local Search
- Hill Climbing
- Simulated Annealing
- Constraint Satisfaction Problems
- Backtracking
- Minimum Remaining Values (MRV)
- Forward Checking
- Optimization and Performance Analysis

##  Project Structure

```text
disaster-rescue-simulator/
│
├── project.py       # Main application and AI algorithms
├── README.md        # Project documentation
```



## Project Objectives

- Demonstrate practical applications of Artificial Intelligence algorithms.
- Compare uninformed and informed search strategies.
- Understand heuristic-based optimization.
- Apply local search algorithms to scheduling problems.
- Model resource allocation using Constraint Satisfaction Problems.
- Analyze algorithm performance through execution time and search statistics.
- Develop an interactive AI-based decision-support application.

.

## 👩‍💻 Authors

**SURABHI SRI VYSHNAVI
  ROHINI PRIYA
  GEETHA**

Computer Science and Engineering  
IIITDM Kancheepuram

## 📜 License

This project is developed for educational and academic purposes.# disaster-rescue-simulator
project for rescuing disaster victims
