# cursora-ml

ML stream: synthetic bot generation and training of the scikit-learn risk model. Feature
extraction comes from [`cursora-features`](../packages/features) so the api and the model use
the same code (no train/serve skew).

## Setup

Prerequisites are the repo's: [uv](https://docs.astral.sh/uv/) and pnpm (see the root
[README](../README.md)). Run everything from the repo root.

```sh
# 1. Fetch the vendored CapyCap engine (git submodule).
#    Fresh clone: `git clone --recurse-submodules ...` does this for you.
git submodule update --init ml/vendor/capycap/upstream

# 2. Install the uv workspace (includes cursora-ml, but not the optional `notebook` group).
pnpm bootstrap

# 3. Open the notebooks (installs the `notebook` dependency group on demand).
pnpm ml:notebook
```

CapyCap is in the optional `notebook` dependency group, so the rest of the monorepo works without
the submodule. If `import capycap` fails with `ModuleNotFoundError`, the submodule is empty or
the group isn't installed: repeat step 1 and use `pnpm ml:notebook` or `pnpm test:ml:replay`.

## Layout

```
ml/
  src/cursora_ml/
    bot_generator/      synthetic bot sessions
    training/           scikit-learn baseline
    replay/             replays dataset sessions through CapyCap, renders an HTML player
  notebooks/            marimo notebooks (exploration)
  vendor/capycap/       packaging wrapper for the vendored engine
    pyproject.toml      makes `import capycap` work (uv path source in ../pyproject.toml)
    upstream/           git submodule: huzpsb/capy_cap_py, do not edit
  data/                 datasets, gitignored
  models/               trained models, gitignored
  tests/
```

## Data

[CaptchaSolve30k](https://huggingface.co/datasets/Capycap-AI/CaptchaSolve30k) is downloaded
on first run by `notebooks/playground.py` (`huggingface_hub.hf_hub_download`) into
`data/captchasolve30k/` and reused afterwards. Nothing under `data/` is committed.

30k human sessions of three CapyCap games, as JSONL with `train` / `validation` / `test` splits.
The notebook only fetches `train.jsonl`, pinned to a dataset commit. Full card: the
[Hugging Face page](https://huggingface.co/datasets/Capycap-AI/CaptchaSolve30k).

| Field              | Type   | Notes                                                      |
| ------------------ | ------ | ---------------------------------------------------------- |
| `index`            | int    | session id                                                 |
| `gameType`         | string | `sheep-herding`, `thread-the-needle` or `polygon-stacking` |
| `puzzleSeed`       | int    | regenerates the puzzle; `cursora_ml.replay` uses it        |
| `duration`         | int    | ms                                                         |
| `physicsTickCount` | int    | ticks at 240 Hz                                            |
| `tickInputs`       | array  | one `{x, y, isDown, sampleIndex}` per physics tick         |
| `inputStream`      | string | base64 raw pointer samples at 1000 Hz                      |
| `inputSampleCount` | int    | number of raw samples                                      |
| `touchscreen`      | bool   | touch rather than mouse input                              |

- Coordinates are on a 200×200 logical grid. Render size was randomised per session, so
  there are no device-specific pixels.
- Tick `i` happens at `i / 240` s. `sampleIndex` points into `inputStream`, and consecutive
  ticks can repeat the same sample.
- The card says `inputStream` is 9 bytes per sample (`<f4` x, `<f4` y, `u1` button), but
  the data doesn't match. See the bytes-per-sample cell in `notebooks/playground.py`.
- Terms of use: bot detection and model training are allowed. Re-identification and
  biometric profiling of individuals are not.

## Vendored CapyCap engine

`vendor/capycap/upstream` is a clean-room, bit-exact Python reimplementation of the CapyCap
games. Upstream ships no `pyproject.toml`, so `vendor/capycap/pyproject.toml` packages it
(`module-root = "upstream"`, depends on numpy). It is excluded from ruff and Prettier, and
mypy treats it as untyped.

Only `cursora_ml/replay/engine.py` imports `capycap`. The api must not depend on it.

To move to a newer upstream commit:

```sh
git -C ml/vendor/capycap/upstream fetch
git -C ml/vendor/capycap/upstream checkout <commit>
git add ml/vendor/capycap/upstream
```

## Checks

```sh
pnpm test:ml        # ml tests only
pnpm check          # everything; run before pushing
```
