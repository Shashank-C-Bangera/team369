from __future__ import annotations
from typing import List, Tuple, Dict, Set

from .state import State, Coord
from .constants import DIRS, CENTER, HOME, valid_cells_for_shape

EMPTY = " "


def _add(a: Coord, b: Coord) -> Coord:
    return (a[0] + b[0], a[1] + b[1])


def _mul(d: Coord, k: int) -> Coord:
    return (d[0] * k, d[1] * k)


def is_straight_line(s: Coord, t: Coord) -> Tuple[bool, Coord, int]:
    dx, dy = t[0] - s[0], t[1] - s[1]
    for d in DIRS:
        if d[0] != 0:
            if dx % d[0] != 0:
                continue
            k = dx // d[0]
            if k < 1:
                continue
            if d[1] * k == dy:
                return True, d, k
        else:
            if dx != 0:
                continue
            if d[1] != 0 and dy % d[1] == 0:
                k = dy // d[1]
                if k >= 1:
                    return True, d, k
    return False, (0, 0), 0


def points_between(s: Coord, t: Coord, d: Coord) -> List[Coord]:
    pts: List[Coord] = []
    cur = _add(s, d)
    while cur != t:
        pts.append(cur)
        cur = _add(cur, d)
    return pts


def _landing_is_free_or_swappable(occ: Dict[Coord, str], player: str, t: Coord) -> bool:
    landing = occ.get(t, EMPTY)
    if landing == EMPTY:
        return True
    return (t in HOME[player]) and (landing != player)


def legal_adjacent_moves(state: State, player: str, valid: Set[Coord]) -> List[List[List[int]]]:
    occ = state.occupied_map()
    moves: List[List[List[int]]] = []
    for s in state.pegs.get(player, ()):
        if s == CENTER:
            continue
        for d in DIRS:
            t = _add(s, d)
            if t == CENTER or t not in valid:
                continue
            if not _landing_is_free_or_swappable(occ, player, t):
                continue
            moves.append([[s[0], s[1]], [t[0], t[1]]])
    return moves


def legal_jump_moves(state: State, player: str, valid: Set[Coord]) -> List[List[List[int]]]:
    occ = state.occupied_map()
    moves: List[List[List[int]]] = []

    for s in state.pegs.get(player, ()):
        if s == CENTER:
            continue

        for d in DIRS:
            k = 2
            while True:
                t = _add(s, _mul(d, k))
                if t == CENTER or t not in valid:
                    break

                between = points_between(s, t, d)
                if CENTER in between:
                    k += 1
                    continue

                seq = [occ.get(p, EMPTY) for p in between]

                if any(x != EMPTY for x in seq) and seq == list(reversed(seq)):
                    if _landing_is_free_or_swappable(occ, player, t):
                        moves.append([[s[0], s[1]], [t[0], t[1]]])

                k += 1

    return moves


def legal_moves(state: State, player: str, shape: str) -> List[List[List[int]]]:
    valid = valid_cells_for_shape(shape)
    return legal_adjacent_moves(state, player, valid) + legal_jump_moves(state, player, valid)
