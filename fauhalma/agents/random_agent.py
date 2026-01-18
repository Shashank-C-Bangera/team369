import random
from fauhalma.moves import legal_moves
from fauhalma.state import State

def choose_move(state: State, shape: str):
    moves = legal_moves(state, "A", shape)
    return random.choice(moves)
