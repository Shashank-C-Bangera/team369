import json
import sys
import logging
from pathlib import Path

from client import run
from fauhalma.constants import ENV_INFO, validate_constants
from fauhalma.state import State

from fauhalma.agents.greedy_agent import choose_move as choose_greedy

logging.basicConfig(level=logging.INFO)
validate_constants()

_ENV_SHAPE_CACHE: dict[str, str] = {}

def _env_from_run_url(run_url: str) -> str:
    parts = run_url.strip("/").split("/")
    i = parts.index("run")
    return parts[i + 1]

def _shape_for_request(info) -> str:
    env = _env_from_run_url(info.run_url)
    if env in _ENV_SHAPE_CACHE:
        return _ENV_SHAPE_CACHE[env]
    if env not in ENV_INFO:
        raise RuntimeError(f"Unknown env '{env}' in run_url: {info.run_url}")
    shape = ENV_INFO[env].shape
    _ENV_SHAPE_CACHE[env] = shape
    return shape

def agent_function(percept, info):
    pos = percept.get("position", percept) if isinstance(percept, dict) else percept
    state = State.from_position_dict(pos)

    shape = _shape_for_request(info)
    env = _env_from_run_url(info.run_url)

    return choose_greedy(state, shape)


if __name__ == "__main__":
    config_path = sys.argv[1]
    cfg = json.loads(Path(config_path).read_text())
    print("Starting agent with config env:", cfg["env"])

    run(
        config_path,
        agent_function,
        parallel_runs=False,
        processes=1,
        abandon_old_runs=True,
        run_limit=60,
    )

    print("Exited cleanly.")
