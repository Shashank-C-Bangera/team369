from __future__ import annotations

from fauhalma.moves import legal_moves
from fauhalma.state import State, apply_move
from fauhalma.constants import HOME
from fauhalma.heuristics import dist_to_set

def a_total_dist(st: State) -> int:
    homeA = HOME["A"]
    return sum(dist_to_set(c, homeA) for c in st.pegs.get("A", ()))

def b_total_dist(st: State) -> int:
    homeB = HOME["B"]
    return sum(dist_to_set(c, homeB) for c in st.pegs.get("B", ()))

def choose_move(state: State, shape: str, k_my: int = 12, k_opp: int = 12):
    """
    1-ply "race" version:
      - Primary: minimize A distance to A-home after B's greedy reply
      - Secondary: break ties by making B's distance larger (optional)
    Uses Top-K to stay fast.
    """
    my_moves = legal_moves(state, "A", shape)
    if not my_moves:
        raise RuntimeError("No legal moves for A")

    baseA = a_total_dist(state)

    # --- Pick top-k_my candidate moves by A-improvement (fast) ---
    cand = []
    for mv in my_moves:
        s1 = apply_move(state, "A", mv)
        impA = baseA - a_total_dist(s1)
        cand.append((impA, mv, s1))
    cand.sort(reverse=True, key=lambda x: x[0])
    cand = cand[: min(k_my, len(cand))]

    best_mv = cand[0][1]
    best_key = (10**18, -10**18)  # (A_dist_after, B_dist_after) lower A_dist is better

    for _impA, mv, s1 in cand:
        opp_moves = legal_moves(s1, "B", shape)

        if not opp_moves:
            # B stuck -> great; evaluate as is
            a_after = a_total_dist(s1)
            b_after = b_total_dist(s1)
            key = (a_after, -b_after)
        else:
            # B greedy reply among top k_opp: minimize B distance
            baseB = b_total_dist(s1)
            replies = []
            for omv in opp_moves:
                s2 = apply_move(s1, "B", omv)
                impB = baseB - b_total_dist(s2)
                replies.append((impB, s2))
            replies.sort(reverse=True, key=lambda x: x[0])
            best_reply = replies[0][1]  # B chooses best-for-B

            a_after = a_total_dist(best_reply)
            b_after = b_total_dist(best_reply)

            # Primary objective: smallest A distance
            # Tie-break: larger B distance (i.e., smaller -b_after)
            key = (a_after, -b_after)

        if key < best_key:
            best_key = key
            best_mv = mv

    return best_mv
