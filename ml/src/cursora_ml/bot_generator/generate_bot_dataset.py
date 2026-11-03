#!/usr/bin/env python3
"""Synthetic bot trajectory generator (CaptchaSolve30k-style format).

Bot types (increasing realism):
  linear_bot  - straight line, constant speed, no noise, no pauses
  noisy_bot   - straight scripted path + correlated noise + real pauses
  bezier_bot  - cubic Bezier + minimum-jerk speed profile + correlated jitter
                + optional overshoot-and-correct near the target

Output: JSONL, one session per line:
  {index, gameType, label, botType, duration, physicsTickCount,
   tickInputs: [{x, y, isDown}, ...]}

Example (from the repo root):
  uv run --package cursora-ml python -m cursora_ml.bot_generator.generate_bot_dataset \\
      -n 3000 --seed 42 -o ml/data/bots.jsonl
"""

import argparse
import json
import math
import random
from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any

type Point = tuple[float, float]
type Tick = dict[str, float | bool]
type Session = dict[str, Any]
type BotFn = Callable[[random.Random, Point, Point, int, int, float], list[Tick]]

BOT_TYPES = ["linear_bot", "noisy_bot", "bezier_bot"]
GAME_TYPES = ["sheep-herding", "thread-the-needle", "polygon-stacking"]


# ---------------------------------------------------------------- helpers
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def min_jerk(t: float) -> float:
    """Minimum-jerk position profile: bell-shaped velocity, zero at both ends."""
    return 10 * t**3 - 15 * t**4 + 6 * t**5


def correlated_noise(rng: random.Random, n: int, sigma: float, phi: float = 0.85) -> list[float]:
    """AR(1) noise with stationary std `sigma` (smooth, like hand tremor)."""
    out: list[float] = []
    prev = 0.0
    innov = sigma * math.sqrt(1 - phi * phi)
    for _ in range(n):
        prev = phi * prev + rng.gauss(0, innov)
        out.append(prev)
    return out


def num_steps(duration_ms: int, fps: int) -> int:
    return max(2, int((duration_ms / 1000.0) * fps))


def to_ticks(
    points: Sequence[Point], grid: float, down: Sequence[bool] | None = None
) -> list[Tick]:
    ticks: list[Tick] = []
    for i, (x, y) in enumerate(points):
        ticks.append(
            {
                "x": round(clamp(x, 0, grid), 2),
                "y": round(clamp(y, 0, grid), 2),
                "isDown": True if down is None else down[i],
            }
        )
    return ticks


# ----------------------------------------------------------- bot generators
def gen_linear(
    rng: random.Random, start: Point, end: Point, duration_ms: int, fps: int, grid: float
) -> list[Tick]:
    n = num_steps(duration_ms, fps)
    pts: list[Point] = []
    for i in range(n):
        t = i / (n - 1)
        pts.append((start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t))
    return to_ticks(pts, grid)


def gen_noisy(
    rng: random.Random, start: Point, end: Point, duration_ms: int, fps: int, grid: float
) -> list[Tick]:
    n = num_steps(duration_ms, fps)

    # Pauses: hold position (progress increment = 0), random place/length.
    weights = [1.0] * n
    for _ in range(rng.choice([0, 1, 1, 2, 3])):
        length = rng.randint(2, max(3, int(0.12 * n)))
        pos = rng.randint(1, max(1, n - length - 2))
        for k in range(pos, min(n - 1, pos + length)):
            weights[k] = 0.0
    weights[0] = 0.0
    total = sum(weights) or 1.0
    progress: list[float] = []
    acc = 0.0
    for w in weights:
        acc += w
        progress.append(acc / total)

    sigma = rng.uniform(0.6, 2.0)
    nx = correlated_noise(rng, n, sigma)
    ny = correlated_noise(rng, n, sigma)

    pts: list[Point] = []
    for i in range(n):
        t = progress[i]
        pts.append(
            (start[0] + (end[0] - start[0]) * t + nx[i], start[1] + (end[1] - start[1]) * t + ny[i])
        )
    # keep exact endpoints so the session starts/ends where intended
    pts[0], pts[-1] = start, end
    # a pause is a real hold: freeze the cursor (noise included)
    for k in range(1, n - 1):
        if weights[k] == 0.0:
            pts[k] = pts[k - 1]
    # occasional short button lift in the middle of a pause (scripted "re-click")
    down = [True] * n
    if rng.random() < 0.3:
        for k in range(n):
            if weights[k] == 0.0 and 0 < k < n - 1 and rng.random() < 0.5:
                down[k] = False
    return to_ticks(pts, grid, down)


def _cubic(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
    )


def _bezier_controls(rng: random.Random, a: Point, b: Point) -> tuple[Point, Point]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    nx, ny = -uy, ux
    c: list[Point] = []
    for frac in (rng.uniform(0.15, 0.4), rng.uniform(0.6, 0.85)):
        off = rng.uniform(-0.25, 0.25) * dist
        c.append((a[0] + dx * frac + nx * off, a[1] + dy * frac + ny * off))
    return c[0], c[1]


def _segment(rng: random.Random, a: Point, b: Point, n: int) -> list[Point]:
    c1, c2 = _bezier_controls(rng, a, b)
    return [_cubic(a, c1, c2, b, min_jerk(i / max(1, n - 1))) for i in range(n)]


def gen_bezier(
    rng: random.Random, start: Point, end: Point, duration_ms: int, fps: int, grid: float
) -> list[Tick]:
    n = num_steps(duration_ms, fps)
    overshoot = rng.random() < 0.3 and n >= 20
    if overshoot:
        dx, dy = end[0] - start[0], end[1] - start[1]
        dist = math.hypot(dx, dy) or 1.0
        d = rng.uniform(2, 8)
        peak = (
            end[0] + dx / dist * d + rng.uniform(-2, 2),
            end[1] + dy / dist * d + rng.uniform(-2, 2),
        )
        n1 = int(n * rng.uniform(0.82, 0.92))
        seg1 = _segment(rng, start, peak, n1)
        seg2 = _segment(rng, peak, end, n - n1)
        pts = seg1 + seg2[1:] + [end] * (n - len(seg1) - len(seg2) + 1)
    else:
        pts = _segment(rng, start, end, n)

    sigma = rng.uniform(0.2, 0.8)
    nx = correlated_noise(rng, n, sigma, phi=0.9)
    ny = correlated_noise(rng, n, sigma, phi=0.9)
    # fade the jitter out near the target (people steady the hand when aiming)
    out: list[Point] = []
    for i, (x, y) in enumerate(pts[:n]):
        fade = min(1.0, (n - 1 - i) / (0.1 * n))
        out.append((x + nx[i] * fade, y + ny[i] * fade))
    out[0], out[-1] = start, end
    return to_ticks(out, grid)


GENERATORS: dict[str, BotFn] = {
    "linear_bot": gen_linear,
    "noisy_bot": gen_noisy,
    "bezier_bot": gen_bezier,
}


# -------------------------------------------------------------- sampling
def sample_endpoints(rng: random.Random, args: argparse.Namespace) -> tuple[Point, Point]:
    g, m = args.grid, args.margin
    if args.endpoint_mode == "fixed":  # legacy: top-left -> bottom-right
        return (
            (rng.uniform(10, 50), rng.uniform(10, 50)),
            (rng.uniform(150, 190), rng.uniform(150, 190)),
        )
    while True:
        a = (rng.uniform(m, g - m), rng.uniform(m, g - m))
        b = (rng.uniform(m, g - m), rng.uniform(m, g - m))
        if math.hypot(b[0] - a[0], b[1] - a[1]) >= args.min_distance:
            return a, b


def sample_duration(rng: random.Random, a: Point, b: Point, args: argparse.Namespace) -> int:
    """Duration follows distance / speed so speed is physically consistent."""
    dist = math.hypot(b[0] - a[0], b[1] - a[1])
    speed = rng.uniform(args.min_speed, args.max_speed)  # grid units / second
    ms = dist / speed * 1000.0
    return int(clamp(ms, args.min_duration, args.max_duration))


def parse_mix(text: str) -> dict[str, float]:
    mix: dict[str, float] = {}
    for part in text.split(","):
        name, _, w = part.partition(":")
        name = name.strip()
        if name not in GENERATORS:
            raise argparse.ArgumentTypeError(f"unknown bot type '{name}'")
        mix[name] = float(w or 1)
    return mix


def generate_dataset(args: argparse.Namespace) -> list[Session]:
    rng = random.Random(args.seed)
    names = list(args.bot_mix)
    weights = [args.bot_mix[k] for k in names]
    games = args.game_types.split(",")
    data: list[Session] = []
    for idx in range(args.num_samples):
        bot = rng.choices(names, weights)[0]
        a, b = sample_endpoints(rng, args)
        duration = sample_duration(rng, a, b, args)
        ticks = GENERATORS[bot](rng, a, b, duration, args.fps, args.grid)
        data.append(
            {
                "index": idx,
                "gameType": rng.choice(games),
                "label": "bot",
                "botType": bot,
                "duration": duration,
                "physicsTickCount": len(ticks),
                "tickInputs": ticks,
            }
        )
    return data


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("-n", "--num-samples", type=int, default=100)
    p.add_argument("-o", "--output", default="synthetic_bot_dataset.jsonl")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument(
        "--bot-mix",
        type=parse_mix,
        default={k: 1.0 for k in BOT_TYPES},
        help="e.g. linear_bot:1,noisy_bot:2,bezier_bot:3",
    )
    p.add_argument("--game-types", default=",".join(GAME_TYPES))
    p.add_argument("--fps", type=int, default=60)
    p.add_argument("--grid", type=float, default=200)
    p.add_argument("--margin", type=float, default=5)
    p.add_argument("--min-distance", type=float, default=60)
    p.add_argument("--endpoint-mode", choices=["random", "fixed"], default="random")
    p.add_argument("--min-speed", type=float, default=80, help="grid units/s")
    p.add_argument("--max-speed", type=float, default=300, help="grid units/s")
    p.add_argument("--min-duration", type=int, default=500)
    p.add_argument("--max-duration", type=int, default=2500)
    return p


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    data = generate_dataset(args)
    with open(args.output, "w") as f:
        for rec in data:
            f.write(json.dumps(rec) + "\n")
    counts = Counter(r["botType"] for r in data)
    print(f"Wrote {len(data)} sessions to {args.output}: {dict(counts)}")


if __name__ == "__main__":
    main()
