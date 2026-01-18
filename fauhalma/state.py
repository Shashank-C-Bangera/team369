from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple

Coord = Tuple[int, int]

@dataclass(frozen=True)
class State:
    pegs: dict[str, tuple[Coord, ...]]

    @staticmethod
    def from_position_dict(pos: dict) -> "State":
        return State({p: tuple((x, y) for x, y in pos.get(p, [])) for p in ["A", "B", "C"]})

    def occupied_map(self) -> Dict[Coord, str]:
        occ: Dict[Coord, str] = {}
        for p, coords in self.pegs.items():
            for c in coords:
                occ[c] = p
        return occ


def apply_move(state: State, player: str, move_json):
    """
    Apply [[sx,sy],[tx,ty]] for player. Implements swap rule:
    If destination is in player's HOME and occupied by opponent -> swap.
    """
    (sx, sy), (tx, ty) = move_json
    s = (sx, sy)
    t = (tx, ty)

    pegs = {p: list(state.pegs.get(p, ())) for p in ["A", "B", "C"]}
    occ = state.occupied_map()

    if s not in pegs[player]:
        raise ValueError("Moving a non-owned peg")

    # remove source peg
    pegs[player].remove(s)

    landing_owner = occ.get(t, None)

    # swap rule
    from fauhalma.constants import HOME
    if landing_owner is not None and landing_owner != player and (t in HOME[player]):
        pegs[landing_owner].remove(t)
        pegs[landing_owner].append(s)

    # place moved peg
    pegs[player].append(t)

    return State({p: tuple(pegs[p]) for p in ["A", "B", "C"]})