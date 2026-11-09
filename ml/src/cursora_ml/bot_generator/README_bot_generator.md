# Synthetic bot trajectory generator

CaptchaSolve30k contains only human sessions, so `generate_bot_dataset.py`
creates labelled bot sessions for training a human-vs-bot model.

## Output format

JSONL, one session per line (same fields as the dataset):

```json
{"index": 0, "gameType": "sheep-herding", "label": "bot", "botType": "bezier_bot",
 "duration": 1219, "physicsTickCount": 73,
 "tickInputs": [{"x": 43.5, "y": 25.89, "isDown": true}, ...]}
```

- Grid is 200x200; coordinates are clamped to it and rounded to 2 decimals.
- Ticks are sampled at the requested fps, with at least 2 ticks: `physicsTickCount = max(2, int(duration / 1000 * fps))`.
- `label` is always `"bot"`; `botType` holds the bot type.

## Bot types (increasing realism)

| botType      | Behaviour                                                                                                                                                                   |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `linear_bot` | Straight line from start to end at constant speed. No noise, no pauses, button always down.                                                                                 |
| `noisy_bot`  | Straight scripted path + correlated (AR(1)) noise, 0-3 random pauses where the cursor holds still, occasional short button lift during a pause.                             |
| `bezier_bot` | Cubic Bezier path with random curvature, minimum-jerk (bell-shaped) speed profile, correlated jitter that fades near the target, and a 30% chance of overshoot-and-correct. |

Start/end points are random by default; duration is derived from distance and a
random speed (so speed is consistent with distance).

## Run

From the repo root (works in cmd, PowerShell and bash):

```sh
uv run --package cursora-ml python -m cursora_ml.bot_generator.generate_bot_dataset -n 3000 --seed 42 -o ml/data/bots.jsonl
uv run --package cursora-ml python -m cursora_ml.bot_generator.generate_bot_dataset -n 9000 --bot-mix linear_bot:1,noisy_bot:1,bezier_bot:1 -o ml/data/bots.jsonl
uv run --package cursora-ml python -m cursora_ml.bot_generator.generate_bot_dataset -n 100 --endpoint-mode fixed -o ml/data/bots_fixed.jsonl
```

`ml/data/` is gitignored, so generated datasets are never committed; use the
same `--seed` to reproduce a file. The last command is the legacy mode
(every bot goes top-left to bottom-right).

Tests: `uv run --package cursora-ml pytest ml`

Options: `-n/--num-samples`, `-o/--output`, `--seed`, `--bot-mix`, `--game-types`,
`--fps`, `--grid`, `--margin`, `--min-distance`, `--endpoint-mode {random,fixed}`,
`--min-speed`, `--max-speed`, `--min-duration`, `--max-duration`.
Uses only the Python standard library.

## Notes for training

- Calibrate start/end, duration and tick-count distributions against the real
  human sessions so the model cannot separate classes on those alone.
- Evaluate per bot type, and hold out one type to test generalisation.
