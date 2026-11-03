"""Replay recorded CaptchaSolve30k sessions and render them as a self-contained HTML player.

Backed by the vendored CapyCap engine (`ml/vendor/capycap`); only `engine.py` imports it.
"""

from cursora_ml.replay.engine import STRIDE, render_replay, simulate

__all__ = ["STRIDE", "render_replay", "simulate"]
