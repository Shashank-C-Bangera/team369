# Assignment 1.2 – Play FAUhalma (AI1 System Project, FAU)

## Author Information

| Team | Author 1 | Author 2 |
|-------|--------|--------------------|
| Name | Shashank Chandraksha Bangera | Sahana Byregowda |
| FAU Username | my96naqy | ez21ipog |
| Matrikel-Nr. | 23734944 | 23080946 |
| Course | AI1 System Project | AI1 System Project |
| Semester | WS 2025/26 | WS 2025/26 |
| Assignment | 1.2 – Play FAUhalma | 1.2 – Play FAUhalma |

---

## Dependencies

| Requirement | Version |
|------------|---------|
| Python | 3.10+ |
| External Libraries | `requests` |

The code is platform-independent and runs on macOS, Linux, and Windows.

---

## Repository Structure

```bash
├── agent.py
├── client.py
├── agent-configs/
│   ├── ws2526.1.2.1.json
│   ├── ws2526.1.2.2.json
│   ├── ws2526.1.2.3.json
│   ├── ws2526.1.2.4.json
│   ├── ws2526.1.2.5.json
│   ├── ws2526.1.2.6.json
│   ├── ws2526.1.2.7.json
│   └── ws2526.1.2.8.json
│
├── fauhalma/
│   ├── __init__.py
│   ├── constants.py
│   ├── heuristics.py
│   ├── moves.py
│   ├── state.py
│   └── agents/
│       ├── __init__.py
│       └── greedy_agent.py
│
├── solution-summary.md
└── README.md
```

## How to Run

To run the agent against a server environment (example: `ws2526.1.2.7`):

```bash
python agent.py agent-configs/ws2526.1.2.7.json
```

Any of the provided configuration files can be used, e.g.:

```bash
python agent.py agent-configs/ws2526.1.2.1.json
python agent.py agent-configs/ws2526.1.2.8.json
```

What happens when you run it:

* The client connects to `https://aisysproj.kwarc.info/` using the credentials from the config JSON.
* The server sends the current game state (positions as JSON).
* The agent computes one legal move for player **A**.
* The move is sent back to the server in the required JSON format: `[[sx, sy], [tx, ty]]`.
* The process repeats until the run finishes (or `run_limit` is reached if configured).

---

## Code Overview

* `client.py`
  Implements the AISysProj server protocol (HTTP polling, receiving percepts, sending actions).
  It handles server responses, messages, finished runs, and supports running multiple runs
  sequentially or via multiprocessing.

* `agent.py`
  Entry point for running the agent.
  Loads the config file, starts the client, converts percept JSON to a `State`, and calls the
  chosen agent policy function to return a move.

* `fauhalma/constants.py`
  Defines board-related constants and utilities:

  * axial direction vectors (`DIRS`)
  * center coordinate (removed cell)
  * board validity generation for shapes (star/rhombus)
  * home regions used by the heuristic agent

* `fauhalma/state.py`
  Contains the immutable game state representation:

  * `State.from_position_dict(...)` converts server JSON to internal tuples
  * `occupied_map()` builds a coordinate → player map
  * `apply_move(...)` applies a move to a state (including swap rule when applicable)

* `fauhalma/moves.py`
  Generates legal moves for a player:

  * adjacent moves (one-step in any axial direction)
  * jump moves along straight axial lines with symmetric occupied/empty intermediate pattern
  * prevents illegal moves through non-board cells / removed center

* `fauhalma/heuristics.py`
  Utility functions for evaluation:

  * hex distance on axial/cube coordinates
  * distance of a peg to a target set (e.g., home)

* `fauhalma/agents/greedy_agent.py`
  Greedy move selection agent for player A:

  * enumerates all legal moves for A
  * scores each move using distance-to-home improvement and jump length bonus
  * prefers moves that progress toward home and reward longer jumps

---

## Notes

* The agent is always player **A** (as specified by the server).
* Moves are returned in server format: `[[sx, sy], [tx, ty]]`.
* If no legal moves exist, the agent raises an error (this corresponds to a losing state).
