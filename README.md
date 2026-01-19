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
