from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List

from fauhalma.state import State, Coord, apply_move
from fauhalma.moves import legal_moves
from fauhalma.constants import HOME
from fauhalma.heuristics import dist_to_set

# Internal move type for hashing/dicts:
Move = Tuple[Coord, Coord]   # ((sx,sy),(tx,ty))


# ---------- move normalization ----------
def _mv_to_tuple(mv) -> Move:
    # mv may be [[sx,sy],[tx,ty]] or ((sx,sy),(tx,ty))
    (sx, sy), (tx, ty) = mv
    return ((int(sx), int(sy)), (int(tx), int(ty)))


def _mv_to_list(mv: Move):
    (sx, sy), (tx, ty) = mv
    return [[sx, sy], [tx, ty]]


def _legal_moves_tuples(st: State, player: str, shape: str) -> List[Move]:
    return [_mv_to_tuple(m) for m in legal_moves(st, player, shape)]


# ---------- helpers ----------
def _total_dist(st: State, player: str) -> int:
    home = HOME[player]
    coords = st.pegs.get(player, ())
    if not home:
        return 10**9
    return sum(dist_to_set(c, home) for c in coords)


def _best_greedy_reply(st: State, player: str, shape: str) -> Optional[Move]:
    """Fast opponent model: pick move that maximizes distance improvement."""
    moves = _legal_moves_tuples(st, player, shape)
    if not moves:
        return None
    d0 = _total_dist(st, player)
    best_mv = moves[0]
    best_imp = -10**18
    for mv in moves:
        st2 = apply_move(st, player, _mv_to_list(mv))
        d1 = _total_dist(st2, player)
        imp = d0 - d1
        if imp > best_imp:
            best_imp = imp
            best_mv = mv
    return best_mv


def _step_A_then_BC(st: State, shape: str, a_mv: Move) -> State:
    """Transition model for one A decision: A move then greedy B+C replies."""
    st1 = apply_move(st, "A", _mv_to_list(a_mv))

    if st1.pegs.get("B"):
        mvB = _best_greedy_reply(st1, "B", shape)
        if mvB is not None:
            st1 = apply_move(st1, "B", _mv_to_list(mvB))

    if st1.pegs.get("C"):
        mvC = _best_greedy_reply(st1, "C", shape)
        if mvC is not None:
            st1 = apply_move(st1, "C", _mv_to_list(mvC))

    return st1


def _evaluate(st: State) -> float:
    """
    Heuristic reward: positive is good for A.
    Encourage being ahead of the closest opponent + absolute progress.
    """
    dA = _total_dist(st, "A")
    dB = _total_dist(st, "B") if st.pegs.get("B") else 10**9
    dC = _total_dist(st, "C") if st.pegs.get("C") else 10**9
    leader = min(dB, dC)

    return 3.0 * (leader - dA) - 0.2 * dA


def _rollout(st: State, shape: str, plies: int) -> float:
    """
    Simulate a few A-turns with stochastic greedy choice (sample 8 moves),
    with greedy B/C replies in between.
    """
    cur = st
    for _ in range(plies):
        movesA = _legal_moves_tuples(cur, "A", shape)
        if not movesA:
            break

        sample = movesA if len(movesA) <= 8 else random.sample(movesA, 8)

        best_mv = sample[0]
        best_val = -10**18
        for mv in sample:
            nxt = _step_A_then_BC(cur, shape, mv)
            val = _evaluate(nxt)
            if val > best_val:
                best_val = val
                best_mv = mv

        cur = _step_A_then_BC(cur, shape, best_mv)

    return _evaluate(cur)


# ---------- MCTS node ----------
@dataclass
class Node:
    st: State
    parent: Optional["Node"] = None
    parent_move: Optional[Move] = None
    children: Dict[Move, "Node"] = field(default_factory=dict)
    untried: List[Move] = field(default_factory=list)
    N: int = 0
    W: float = 0.0

    def is_fully_expanded(self) -> bool:
        return len(self.untried) == 0

    def best_child_ucb(self, c: float) -> "Node":
        logN = math.log(self.N + 1)
        best_child = None
        best_score = -10**18
        for mv, ch in self.children.items():
            if ch.N == 0:
                return ch
            exploit = ch.W / ch.N
            explore = c * math.sqrt(logN / ch.N)
            score = exploit + explore
            if score > best_score:
                best_score = score
                best_child = ch
        return best_child  # type: ignore


def choose_move(
    state: State,
    shape: str,
    *,
    time_limit_s: float = 0.20,
    rollout_plies: int = 3,
    ucb_c: float = 1.1,
    seed: Optional[int] = None,
):
    """
    MCTS over A-moves only.
    Returns move in server format: [[sx,sy],[tx,ty]]
    """
    if seed is not None:
        random.seed(seed)

    root_moves = _legal_moves_tuples(state, "A", shape)
    if not root_moves:
        raise RuntimeError("No legal moves for A")

    root = Node(st=state, untried=list(root_moves))

    t_end = time.time() + time_limit_s

    while time.time() < t_end:
        node = root

        # 1) Selection
        while node.is_fully_expanded() and node.children:
            node = node.best_child_ucb(ucb_c)

        # 2) Expansion
        if node.untried:
            mv = node.untried.pop()
            st2 = _step_A_then_BC(node.st, shape, mv)
            child = Node(
                st=st2,
                parent=node,
                parent_move=mv,
                untried=list(_legal_moves_tuples(st2, "A", shape)),
            )
            node.children[mv] = child
            node = child

        # 3) Simulation
        reward = _rollout(node.st, shape, rollout_plies)

        # 4) Backpropagation
        while node is not None:
            node.N += 1
            node.W += reward
            node = node.parent

    # Choose move with max visits (robust), tie-break by mean value
    best_mv: Optional[Move] = None
    best_visits = -1
    best_mean = -10**18

    for mv, ch in root.children.items():
        if ch.N > best_visits:
            best_visits = ch.N
            best_mean = ch.W / ch.N if ch.N else -10**18
            best_mv = mv
        elif ch.N == best_visits:
            mean = ch.W / ch.N if ch.N else -10**18
            if mean > best_mean:
                best_mean = mean
                best_mv = mv

    chosen = best_mv if best_mv is not None else root_moves[0]
    return _mv_to_list(chosen)
