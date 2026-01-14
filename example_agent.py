import random
from collections import deque

DEBUG = False

DIRS = [(1,0), (-1,0), (0,1), (0,-1), (1,-1), (-1,1)]

_GOAL = None
_LAST_MOVE = None
RECENT_A_STATES = deque(maxlen=40)
KNOWN_ON_BOARD = set()
# Start with known bad coordinates and add more based on rhombus pattern
KNOWN_OFF_BOARD = {
    (-4, 2), (0, 0), (-4, 1), (-4, 4), (-4, 3), (-4, 5), (-4, 6),  # From observed errors
    # Comprehensive rhombus boundary patterns - entire perimeter
    (0, -4), (1, -5), (2, -6), (3, -7), (4, -7), (4, -6), (4, -5), 
    (4, -4), (4, -3), (4, -2), (4, -1), (4, 0), (3, 1), (2, 2), (1, 3), 
    (0, 4), (-1, 5), (-2, 6), (-3, 7), (-4, 7), (-4, 8), (-5, 7), (-5, 6), (-6, 5), (-7, 4),
    (-5, 4), (-5, 3), (-5, 2), (-5, 1), (-5, 0), (-5, -1), (-5, -2), (-5, -3),
    (-4, 0), (-4, -1), (-4, -2), (-4, -3), (-3, -1), (-3, -2), (-3, -3), (-3, -4),
    (-2, -2), (-2, -3), (-2, -4), (-2, -5), (-1, -3), (-1, -4), (-1, -5), (-1, -6),
    (0, -5), (0, -6), (0, -7), (0, -8), (1, -6), (1, -7), (1, -8), (1, -9),
    (2, -7), (2, -8), (2, -9), (3, -8), (3, -9), (4, -8), (4, -9), (5, -8), (5, -7),
    (5, -6), (5, -5), (5, -4), (5, -3), (5, -2), (5, -1), (5, 0), (5, 1), (5, 2),
    (5, 3), (5, 4), (5, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (3, 2), (3, 3),
    (3, 4), (3, 5), (3, 6), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (1, 4), (1, 5),
    (1, 6), (1, 7), (1, 8), (0, 5), (0, 6), (0, 7), (0, 8), (-1, 6), (-1, 7),
    (-1, 8), (-2, 7), (-2, 8), (-3, 8), (-3, 9), (-4, 9), (-4, 10), (-5, 8), (-5, 9),
    (-6, 6), (-6, 7), (-6, 8), (-7, 5), (-7, 6), (-7, 7), (-8, 4), (-8, 5), (-8, 6)
}

def add(p, d):
    return [p[0] + d[0], p[1] + d[1]]

def dist2(p, goal):
    dx = p[0] - goal[0]
    dy = p[1] - goal[1]
    return dx*dx + dy*dy

def A_state_key(pos):
    return tuple(sorted(tuple(p) for p in pos["A"]))

def apply_move_to_A(A, src, dst):
    A2 = [p[:] for p in A]
    for i, p in enumerate(A2):
        if p[0] == src[0] and p[1] == src[1]:
            A2[i] = dst[:]
            break
    return tuple(sorted(tuple(p) for p in A2))

def gen_simple_and_hop_moves(pos):
    A = pos["A"]
    occ = set(tuple(p) for plist in pos.values() for p in plist)

    moves = []

    # simple moves
    for src in A:
        sx, sy = src
        for dx, dy in DIRS:
            dst = (sx+dx, sy+dy)
            if dst not in occ and dst not in KNOWN_OFF_BOARD:
                # Extra safety: avoid obviously bad coordinates
                if abs(dst[0]) > 10 or abs(dst[1]) > 10:
                    continue
                moves.append([src, [dst[0], dst[1]]])

    # hop moves (2-step)
    for src in A:
        sx, sy = src
        for dx, dy in DIRS:
            mid = (sx+dx, sy+dy)
            dst = (sx+2*dx, sy+2*dy)
            if mid in occ and dst not in occ and dst not in KNOWN_OFF_BOARD:
                # Extra safety: avoid obviously bad coordinates
                if abs(dst[0]) > 10 or abs(dst[1]) > 10:
                    continue
                moves.append([src, [dst[0], dst[1]]])

    return moves

def agent_function(request_dict, _info):
    global _GOAL, _LAST_MOVE, RECENT_A_STATES

    # Reset global state at the start of each new run
    if _info and hasattr(_info, 'action_number') and _info.action_number == 0:
        _GOAL = None
        _LAST_MOVE = None
        RECENT_A_STATES.clear()

    if DEBUG and not hasattr(agent_function, "_printed_info"):
        print("_info sample:", _info)
        agent_function._printed_info = True

    A = request_dict["A"]
    
    # Track board positions we see
    for plist in request_dict.values():
        for p in plist:
            KNOWN_ON_BOARD.add(tuple(p))

    # Track recent A states to prevent loops
    current_state = A_state_key(request_dict)
    RECENT_A_STATES.append(current_state)

    # Goal: opponent corner (centroid of B) – established ONCE from initial position
    if _GOAL is None and "B" in request_dict and request_dict["B"]:
        # Only set goal at start of run to avoid changing targets
        if _info and hasattr(_info, 'action_number') and _info.action_number == 0:
            bx = sum(p[0] for p in request_dict["B"]) / len(request_dict["B"])
            by = sum(p[1] for p in request_dict["B"]) / len(request_dict["B"])
            _GOAL = (bx, by)
            if DEBUG:
                print("Goal established at start:", _GOAL)
        elif _GOAL is None:  # Fallback if action_number not available
            bx = sum(p[0] for p in request_dict["B"]) / len(request_dict["B"])
            by = sum(p[1] for p in request_dict["B"]) / len(request_dict["B"])
            _GOAL = (bx, by)
            if DEBUG:
                print("Goal established (fallback):", _GOAL)

    # Generate both simple and hop moves
    candidates = gen_simple_and_hop_moves(request_dict)
    
    # Filter out immediate undos
    if _LAST_MOVE is not None:
        last_src, last_dst = _LAST_MOVE
        candidates = [
            move for move in candidates 
            if not (tuple(move[0]) == last_dst and tuple(move[1]) == last_src)
        ]

    if not candidates:
        # Emergency fallback: try simple adjacent moves only
        for src in A:
            sx, sy = src
            for dx, dy in DIRS:
                dst = (sx+dx, sy+dy)
                # Only check basic occupancy, ignore off-board list as last resort
                occ = set(tuple(p) for plist in request_dict.values() for p in plist)
                if dst not in occ:
                    if DEBUG:
                        print(f"Emergency fallback move: {src} -> {list(dst)}")
                    return [src, list(dst)]
        # If even that fails, do a non-move
        return [A[0], A[0]]

    # Score candidates: prefer distance improvement, avoid repeat states
    best = None
    best_score = None
    for src, dst in candidates:
        if _GOAL is None:
            base_delta = 0
        else:
            base_delta = dist2(dst, _GOAL) - dist2(src, _GOAL)  # negative is good
        
        # Add huge penalty for repeating recent states
        new_key = apply_move_to_A(A, src, dst)
        penalty = 10_000 if new_key in RECENT_A_STATES else 0
        
        score = base_delta + penalty
        
        if best is None or score < best_score:
            best = [src, dst]
            best_score = score

    _LAST_MOVE = (tuple(best[0]), tuple(best[1]))
    if DEBUG:
        print(f"Moving {best[0]} -> {best[1]} (score: {best_score})")
    return best


if __name__ == '__main__':
    try:
        from client import run
    except ImportError:
        raise ImportError('You need to have the client.py file in the same directory as this file')

    import logging
    logging.basicConfig(level=logging.INFO)

    import sys
    config_file = sys.argv[1]

    run(
        config_file,
        agent_function,
        processes=4,
        run_limit=50,
        parallel_runs=True,
        abandon_old_runs=True
    )
