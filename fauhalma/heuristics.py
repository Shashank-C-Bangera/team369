from __future__ import annotations
from typing import Iterable, Tuple


Coord = Tuple[int, int]

def cube_from_axial(x: int, y: int) -> tuple[int, int, int]:
    return (x, y, -x - y)

def hex_distance(a: Coord, b: Coord) -> int:
    ax, ay = a
    bx, by = b
    az = -ax - ay
    bz = -bx - by
    return max(abs(ax - bx), abs(ay - by), abs(az - bz))

def dist_to_set(p: Coord, targets: Iterable[Coord]) -> int:
    return min(hex_distance(p, t) for t in targets)