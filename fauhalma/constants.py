from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set, Tuple, Literal

# ---------- Types ----------
Coord = Tuple[int, int]
Shape = Literal["star", "rhombus"]

# ---------- Hex grid directions (axial) ----------
DIRS: tuple[Coord, ...] = (
    (1, 0), (-1, 0),
    (0, 1), (0, -1),
    (1, -1), (-1, 1),
)

CENTER: Coord = (0, 0)

# Triangle side length: 1 + 2 + 3 = 6 pegs
N = 3


# ---------- Environment info ----------
@dataclass(frozen=True)
class EnvInfo:
    env: str
    shape: Shape
    players: int


ENV_INFO: Dict[str, EnvInfo] = {
    "ws2526.1.2.1": EnvInfo("ws2526.1.2.1", "rhombus", 2),
    "ws2526.1.2.2": EnvInfo("ws2526.1.2.2", "star", 2),
    "ws2526.1.2.3": EnvInfo("ws2526.1.2.3", "star", 2),
    "ws2526.1.2.4": EnvInfo("ws2526.1.2.4", "star", 2),
    "ws2526.1.2.5": EnvInfo("ws2526.1.2.5", "star", 3),
    "ws2526.1.2.6": EnvInfo("ws2526.1.2.6", "star", 3),
    "ws2526.1.2.7": EnvInfo("ws2526.1.2.7", "star", 3),
    "ws2526.1.2.8": EnvInfo("ws2526.1.2.8", "star", 3),
}


def env_info_from_config(config: dict) -> EnvInfo:
    env = config["env"]
    if env not in ENV_INFO:
        raise ValueError(f"Unknown env '{env}'")
    return ENV_INFO[env]


# ---------- Coordinate helpers ----------
def _cube_from_axial(x: int, y: int) -> tuple[int, int, int]:
    return (x, y, -x - y)


def _opposite(c: Coord) -> Coord:
    return (-c[0], -c[1])


# ---------- Board shape checks ----------
def _is_star_cell(x: int, y: int, n: int = N) -> bool:
    cx, cy, cz = _cube_from_axial(x, y)
    a = sorted([abs(cx), abs(cy), abs(cz)])
    return a[2] <= 2 * n and a[1] <= n


def _is_rhombus_cell(x: int, y: int, n: int = N) -> bool:
    cx, cy, cz = _cube_from_axial(x, y)
    a = sorted([abs(cx), abs(cy), abs(cz)])
    if a[2] <= n:
        return True
    return abs(cy) > n and abs(cx) <= n and abs(cz) <= n and a[2] <= 2 * n


def _generate_valid(shape: Shape) -> Set[Coord]:
    valid: Set[Coord] = set()
    for x in range(-2 * N, 2 * N + 1):
        for y in range(-2 * N, 2 * N + 1):
            if (x, y) == CENTER:
                continue
            if shape == "star" and _is_star_cell(x, y):
                valid.add((x, y))
            elif shape == "rhombus" and _is_rhombus_cell(x, y):
                valid.add((x, y))
    return valid


# ---------- Valid boards ----------
VALID_STAR: Set[Coord] = _generate_valid("star")
VALID_RHOMBUS: Set[Coord] = _generate_valid("rhombus")


def valid_cells_for_shape(shape: Shape) -> Set[Coord]:
    return VALID_STAR if shape == "star" else VALID_RHOMBUS


# ---------- START / HOME (rule-correct) ----------
# Corners:
#   y < -N -> bottom
#   x < -N -> top-left
#   z < -N -> top-right  (z = -x - y)

START: Dict[str, Set[Coord]] = {
    "A": {c for c in VALID_STAR if c[1] < -N},
    "B": {c for c in VALID_STAR if c[0] < -N},
    "C": {c for c in VALID_STAR if (-c[0] - c[1]) < -N},
}

# HOME is exactly opposite corner of START
HOME: Dict[str, Set[Coord]] = {
    "A": {_opposite(c) for c in START["A"]},
    "B": {_opposite(c) for c in START["B"]},
    "C": {_opposite(c) for c in START["C"]},
}


# ---------- Sanity checks ----------
def validate_constants() -> None:
    assert CENTER not in VALID_STAR
    assert CENTER not in VALID_RHOMBUS

    assert len(VALID_STAR) == 72, f"Expected 72 star cells, got {len(VALID_STAR)}"
    assert len(VALID_RHOMBUS) == 48, f"Expected 48 rhombus cells, got {len(VALID_RHOMBUS)}"

    # Each corner must have exactly 6 cells
    assert all(len(START[p]) == 6 for p in "ABC"), {p: len(START[p]) for p in "ABC"}
    assert all(len(HOME[p]) == 6 for p in "ABC"), {p: len(HOME[p]) for p in "ABC"}