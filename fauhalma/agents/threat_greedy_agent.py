from __future__ import annotations

from typing import List

from fauhalma.moves import legal_moves
from fauhalma.state import State, apply_move, Coord
from fauhalma.constants import HOME
from fauhalma.heuristics import dist_to_set


def _total_dist(coords: tuple[Coord, ...], home: set[Coord]) -> int:
    if not coords:
        return 10**9
    return sum(dist_to_set(c, home) for c in coords)


def _jump_len(mv) -> int:
    (sx, sy), (tx, ty) = mv
    sz = -sx - sy
    tz = -tx - ty
    return max(abs(tx - sx), abs(ty - sy), abs(tz - sz))


def _best_one_move_improvement(state: State, player: str, shape: str) -> int:
    coords0 = state.pegs.get(player, ())
    if not coords0:
        return 0
    dist0 = _total_dist(coords0, HOME[player])

    moves = legal_moves(state, player, shape)
    best = 0
    for mv in moves:
        s1 = apply_move(state, player, mv)
        dist1 = _total_dist(s1.pegs.get(player, ()), HOME[player])
        best = max(best, dist0 - dist1)
    return best


def _opponent_max_jump_len(state: State, player: str, shape: str) -> int:
    """
    Cheap proxy for jump-ladder threat: what's the longest jump available next move?
    """
    moves = legal_moves(state, player, shape)
    if not moves:
        return 0
    return max(_jump_len(mv) for mv in moves)


def _is_central_lane(c: Coord) -> bool:
    """
    Central 'highway' region (very strong in 3-player star).
    This matches the small center hex cluster around (0,0).
    """
    x, y = c
    z = -x - y
    return abs(x) <= 1 and abs(y) <= 1 and abs(z) <= 1


def choose_move(state: State, shape: str):
    movesA = legal_moves(state, "A", shape)
    if not movesA:
        raise RuntimeError("No legal moves for A")

    A0 = state.pegs.get("A", ())
    distA0 = _total_dist(A0, HOME["A"])

    best_mv = movesA[0]
    best_score = -10**18

    # ---------- weights ----------
    W_SELF = 120
    W_JUMP = 18
    W_ENTER_HOME = 160
    W_LEAVE_HOME = -260

    # Threat: opponent immediate improvement and jump-ladder potential
    W_THREAT_IMPROVE = 120
    THREAT_IMPROVE_CAP = 8

    W_THREAT_JUMP = 55
    THREAT_JUMP_CAP = 7

    # Lane control (the big missing ingredient)
    W_LANE_ENTER = 180
    W_LANE_LEAVE = -250

    for mv in movesA:
        (sx, sy), (tx, ty) = mv
        s = (sx, sy)
        t = (tx, ty)

        sA = apply_move(state, "A", mv)

        distA1 = _total_dist(sA.pegs.get("A", ()), HOME["A"])
        improvementA = distA0 - distA1

        score = 0
        score += W_SELF * improvementA
        score += W_JUMP * min(7, max(0, _jump_len(mv) - 1))

        if (s not in HOME["A"]) and (t in HOME["A"]):
            score += W_ENTER_HOME
        if (s in HOME["A"]) and (t not in HOME["A"]):
            score += W_LEAVE_HOME

        # ----- lane control -----
        if _is_central_lane(t) and not _is_central_lane(s):
            score += W_LANE_ENTER
        if _is_central_lane(s) and not _is_central_lane(t):
            score += W_LANE_LEAVE

        # ----- opponent threats next turn -----
        bestB = _best_one_move_improvement(sA, "B", shape)
        bestC = _best_one_move_improvement(sA, "C", shape)
        threat_improve = min(THREAT_IMPROVE_CAP, max(bestB, bestC))
        score -= W_THREAT_IMPROVE * threat_improve

        jumpB = _opponent_max_jump_len(sA, "B", shape)
        jumpC = _opponent_max_jump_len(sA, "C", shape)
        threat_jump = min(THREAT_JUMP_CAP, max(jumpB, jumpC))
        score -= W_THREAT_JUMP * threat_jump

        if score > best_score:
            best_score = score
            best_mv = mv

    return best_mv
