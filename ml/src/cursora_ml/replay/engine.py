"""Replay recorded sessions through the vendored CapyCap engine and render them."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from capycap import GameSession
from capycap.f32 import round_4_decimals
from capycap.games.ps_b2 import PolygonStackingGameB2
from capycap.games.thread_needle import HAND_RADIUS
from capycap.rng import wasm_seed_from_puzzle_seed

GAME_TYPES = ("thread-the-needle", "sheep-herding", "polygon-stacking")
STRIDE = 4  # keep every 4th tick = 60 frames/s of replay at 1x
_PLAYER = Path(__file__).with_name("player.html")


def _r(v: Any) -> float:
    return round(float(v), 1)


def _poly_world(body: Any) -> list[list[float]]:
    c, s = float(body.rot_c), float(body.rot_s)
    ox, oy = float(body.x), float(body.y)  # physics metres, y up
    return [
        [
            _r((ox + c * float(vx) - s * float(vy)) * 100),
            _r(200 - (oy + s * float(vx) + c * float(vy)) * 100),
        ]
        for vx, vy in body.shapes[0].poly.verts
    ]


def simulate(
    game_type: str, puzzle_seed: int, ticks: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Replay recorded pointer ticks through the engine, snapshotting every STRIDE ticks.

    Each tick needs `x`, `y` and `isDown` (the dataset's `tickInputs`). The last tick is
    always snapshotted too, so the final frame shows the state `solved` describes.
    """
    if game_type not in GAME_TYPES:
        raise ValueError(f"unknown game type: {game_type!r}")

    game: Any
    if game_type == "polygon-stacking":
        # bit-exact Box2D backend (the default polygon engine drifts)
        game = PolygonStackingGameB2(wasm_seed_from_puzzle_seed(puzzle_seed), 200, 200)
    else:
        game = GameSession(game_type, puzzle_seed).game

    static: dict[str, Any]
    if game_type == "thread-the-needle":
        static = {
            "needles": [
                {"shape": nd.shape, "color": nd.color, "target": nd.is_target}
                for nd in game.needles
            ],
            "r": float(HAND_RADIUS),
        }
    elif game_type == "sheep-herding":
        static = {
            "goal": [_r(game.goal_x), _r(game.goal_y)],
            "walls": [[[_r(x), _r(y)] for x, y in w] for w in game.walls],
            "capture_r": float(game.capture_radius),
            "vacuum_r": float(game.vacuum_radius),
        }
    else:
        static = {"colors": [p["color"] for p in game.polys]}

    def snapshot(tick: Mapping[str, Any]) -> dict[str, Any]:
        ptr = [_r(tick["x"]), _r(tick["y"]), int(tick["isDown"])]
        if game_type == "thread-the-needle":
            return {
                "i": ptr,
                "p": [[_r(p.x), _r(p.y)] for p in game.points],
                "n": [[_r(nd.pos.x), _r(nd.pos.y)] for nd in game.needles],
            }
        if game_type == "sheep-herding":
            return {"i": ptr, "s": [[_r(sh.x), _r(sh.y), int(sh.captured)] for sh in game.sheep]}
        return {"i": ptr, "q": [_poly_world(p["body"]) for p in game.polys]}

    frames: list[dict[str, Any]] = []
    for t, tick in enumerate(ticks):
        game.apply_input(
            round_4_decimals(tick["x"]), round_4_decimals(tick["y"]), bool(tick["isDown"])
        )
        game.step(t)
        if t % STRIDE == 0:
            frames.append(snapshot(tick))
    if ticks and (len(ticks) - 1) % STRIDE:
        frames.append(snapshot(ticks[-1]))
    return {
        "game": game_type,
        "static": static,
        "frames": frames,
        "stride": STRIDE,
        "n_ticks": len(ticks),
        "solved": bool(game.is_solved()),
    }


def render_replay(data: Mapping[str, Any], *, title: str, window: tuple[int, int]) -> str:
    """Fill player.html with `simulate()` output.

    `title` is shown above the scene (HTML allowed); `window` is the (start, end)
    tick range to highlight under the scene.
    """
    payload = {**data, "title": title, "win": list(window)}
    # The payload lands inside a <script>, so a title containing </script> must not close it.
    data_json = json.dumps(payload).replace("<", "\\u003c")
    return _PLAYER.read_text(encoding="utf-8").replace("__DATA__", data_json)
