from __future__ import annotations

import time
from typing import List, Optional, Tuple

from fauhalma.moves import legal_moves
from fauhalma.state import State, apply_move, Coord
from fauhalma.constants import HOME
from fauhalma.heuristics import dist_to_set
from fauhalma.agents.greedy_agent import choose_move as choose_greedy


# -------------------------
# Time / safety controls
# -------------------------
TIME_BUDGET_SEC = 0.12  # keep tight; raise to 0.18 if you see no timeouts and want strength


# -------------------------
# Helpers
# -------------------------
def _total_dist(coords: tuple[Coord, ...], home: set[Coord]) -> int:
    if not coords:
        return 10**9
    return sum(dist_to_set(c, home) for c in coords)


def _pegs_in_home(state: State, player: str) -> int:
    home = HOME[player]
    return sum(1 for c in state.pegs.get(player, ()) if c in home)


def _jump_len_from_move(mv) -> int:
    (sx, sy), (tx, ty) = mv
    sz = -sx - sy
    tz = -tx - ty
    return max(abs(tx - sx), abs(ty - sy), abs(tz - sz))


def _top_k(moves: List, scores: List[int], k: int) -> List:
    if len(moves) <= k:
        return moves
    idx = sorted(range(len(moves)), key=lambda i: scores[i], reverse=True)[:k]
    return [moves[i] for i in idx]


# -------------------------
# Evaluation: good for A, and stable endgame behavior
# -------------------------
def _eval_for_A(state: State) -> float:
    A = state.pegs.get("A", ())
    B = state.pegs.get("B", ())
    C = state.pegs.get("C", ())

    distA = _total_dist(A, HOME["A"])
    distB = _total_dist(B, HOME["B"]) if B else 10**9
    distC = _total_dist(C, HOME["C"]) if C else 10**9

    inA = _pegs_in_home(state, "A")
    inB = _pegs_in_home(state, "B")
    inC = _pegs_in_home(state, "C")

    best_opp_dist = min(distB, distC)
    best_opp_home = max(inB, inC)

    return (-distA) + 150.0 * inA + 1.10 * best_opp_dist - 120.0 * best_opp_home


# -------------------------
# A move ordering (beam)
# -------------------------
def _order_A(state: State, mv) -> int:
    (sx, sy), (tx, ty) = mv
    s = (sx, sy)
    t = (tx, ty)

    A0 = state.pegs.get("A", ())
    if s not in A0:
        return -10**9

    dist0 = _total_dist(A0, HOME["A"])
    newA = list(A0)
    newA[newA.index(s)] = t
    dist1 = _total_dist(tuple(newA), HOME["A"])
    improvement = dist0 - dist1

    bonus = 0
    if (s not in HOME["A"]) and (t in HOME["A"]):
        bonus += 160
    if (s in HOME["A"]) and (t not in HOME["A"]):
        bonus -= 300

    jl = _jump_len_from_move(mv)
    bonus += min(7, max(0, jl - 1)) * 22

    return improvement * 100 + bonus


# -------------------------
# Opponent mixed model:
# among good racing moves, prefer those that also hurt A.
# This matches "smarter" opponents much better.
# -------------------------
def _opp_race_score(state: State, player: str, mv) -> int:
    s1 = apply_move(state, player, mv)
    distP = _total_dist(s1.pegs.get(player, ()), HOME[player])
    inP = _pegs_in_home(s1, player)
    jl = _jump_len_from_move(mv)
    return int(200 * inP - 70 * distP + min(7, max(0, jl - 1)) * 10)


def _best_opp_move_mixed(state: State, player: str, shape: str, k: int, t0: float):
    moves = legal_moves(state, player, shape)
    if not moves:
        return None

    # Beam by opponent racing score
    scores = [_opp_race_score(state, player, mv) for mv in moves]
    cand = _top_k(moves, scores, k)

    # Among those, pick the one that minimizes A's eval (i.e., hurts A),
    # but only within the good-race set.
    best_mv = cand[0]
    best_valA = 10**18

    for mv in cand:
        if time.perf_counter() - t0 > TIME_BUDGET_SEC:
            break
        s1 = apply_move(state, player, mv)
        valA = _eval_for_A(s1)
        if valA < best_valA:
            best_valA = valA
            best_mv = mv

    return best_mv


# -------------------------
# Main: A -> B -> C (correct turn order), budgeted, with greedy safety net
# -------------------------
def choose_move(state: State, shape: str):
    t0 = time.perf_counter()

    # Always have a safe fallback
    mv_greedy = choose_greedy(state, shape)

    movesA = legal_moves(state, "A", shape)
    if not movesA:
        return mv_greedy

    # Beam widths (keep moderate; raise slowly)
    K_A = 18
    K_B = 10
    K_C = 10

    scoresA = [_order_A(state, mv) for mv in movesA]
    candA = _top_k(movesA, scoresA, K_A)

    best_mv = mv_greedy
    best_val = -10**18

    for mvA in candA:
        if time.perf_counter() - t0 > TIME_BUDGET_SEC:
            break

        sA = apply_move(state, "A", mvA)

        mvB = _best_opp_move_mixed(sA, "B", shape, K_B, t0)
        if mvB is None:
            val = _eval_for_A(sA)
            if val > best_val:
                best_val = val
                best_mv = mvA
            continue
        sB = apply_move(sA, "B", mvB)

        mvC = _best_opp_move_mixed(sB, "C", shape, K_C, t0)
        if mvC is None:
            val = _eval_for_A(sB)
            if val > best_val:
                best_val = val
                best_mv = mvA
            continue
        sC = apply_move(sB, "C", mvC)

        val = _eval_for_A(sC)
        if val > best_val:
            best_val = val
            best_mv = mvA

    # Safety net: if our chosen move is way worse than greedy by ordering score, keep greedy.
    # (prevents "over-defensive but losing race" catastrophes)
    if _order_A(state, best_mv) < _order_A(state, mv_greedy) - 120:
        return mv_greedy

    return best_mv
