from __future__ import annotations
from fauhalma.moves import legal_moves
from fauhalma.state import State, Coord
from fauhalma.constants import HOME
from fauhalma.heuristics import dist_to_set


def _jump_len(s: Coord, t: Coord) -> int:
    sx, sy = s
    tx, ty = t
    sz = -sx - sy
    tz = -tx - ty
    return max(abs(tx - sx), abs(ty - sy), abs(tz - sz))


def _total_dist(coords: tuple[Coord, ...], home: set[Coord]) -> int:
    if not home:
        return 10**9
    return sum(dist_to_set(c, home) for c in coords)


def choose_move(state: State, shape: str):
    moves = legal_moves(state, "A", shape)
    if not moves:
        raise RuntimeError("No legal moves for A")

    homeA = HOME["A"]
    homeB = HOME["B"]
    homeC = HOME["C"]

    A0 = state.pegs.get("A", ())
    B0 = state.pegs.get("B", ())
    C0 = state.pegs.get("C", ())

    distA0 = _total_dist(A0, homeA)
    distB0 = _total_dist(B0, homeB) if B0 else 10**9
    distC0 = _total_dist(C0, homeC) if C0 else 10**9

    leader0 = min(distB0, distC0)

    best_move = moves[0]
    best_score = -10**18

    for mv in moves:
        (sx, sy), (tx, ty) = mv
        s = (sx, sy)
        t = (tx, ty)

        newA = list(A0)
        idx = newA.index(s)
        newA[idx] = t
        distA1 = _total_dist(tuple(newA), homeA)

        improvementA = distA0 - distA1
        jl = _jump_len(s, t)

        score = (
            improvementA * 110
            + 55 * max(0, jl - 1)
            + (ty - sy) * 4
        )

        advantage_gain = (leader0 - distA1) - (leader0 - distA0)
        score += 55 * advantage_gain

        if (s not in homeA) and (t in homeA):
            score += 100

        if score > best_score:
            best_score = score
            best_move = mv

    return best_move