from __future__ import annotations

from fauhalma.moves import legal_moves
from fauhalma.state import State, Coord, apply_move
from fauhalma.constants import HOME
from fauhalma.heuristics import dist_to_set


def _total_dist(st: State, player: str) -> int:
    home = HOME[player]
    coords = st.pegs.get(player, ())
    if not home:
        return 10**9
    return sum(dist_to_set(c, home) for c in coords)


def _best_greedy_reply(st: State, player: str, shape: str):
    """Pick the move that minimizes that player's total distance to its HOME."""
    moves = legal_moves(st, player, shape)
    if not moves:
        return None

    d0 = _total_dist(st, player)
    best_mv = moves[0]
    best = -10**18

    for mv in moves:
        st2 = apply_move(st, player, mv)
        d1 = _total_dist(st2, player)
        improvement = d0 - d1
        # greedy reply: maximize improvement
        if improvement > best:
            best = improvement
            best_mv = mv

    return best_mv


def choose_move(state: State, shape: str):
    """
    Stronger than pure greedy:
      - For each A move, simulate B greedy reply, then C greedy reply.
      - Pick A move that maximizes "race advantage" after replies.
    """
    a_moves = legal_moves(state, "A", shape)
    if not a_moves:
        raise RuntimeError("No legal moves for A")

    best_mv = a_moves[0]
    best_score = -10**18

    # Precompute current distances (optional)
    for mv in a_moves:
        # A plays mv
        st1 = apply_move(state, "A", mv)

        # B reply
        if "B" in st1.pegs and st1.pegs.get("B"):
            b_mv = _best_greedy_reply(st1, "B", shape)
            if b_mv is not None:
                st1 = apply_move(st1, "B", b_mv)

        # C reply
        if "C" in st1.pegs and st1.pegs.get("C"):
            c_mv = _best_greedy_reply(st1, "C", shape)
            if c_mv is not None:
                st1 = apply_move(st1, "C", c_mv)

        # Evaluate: prefer being ahead of the best opponent
        dA = _total_dist(st1, "A")
        dB = _total_dist(st1, "B") if st1.pegs.get("B") else 10**9
        dC = _total_dist(st1, "C") if st1.pegs.get("C") else 10**9
        leader = min(dB, dC)

        # The smaller dA is, the better. Also the bigger (leader - dA), the better.
        # Weighting encourages "finish first" rather than "finish not last".
        score = (leader - dA) * 200 - dA * 20

        if score > best_score:
            best_score = score
            best_mv = mv

    return best_mv
