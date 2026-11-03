import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import polars as pl

    return (pl,)


@app.cell
def _(pl):
    from pathlib import Path

    from huggingface_hub import hf_hub_download

    # Downloads on first run, reuses the local copy afterwards.
    # Relative to this file, not the cwd, so it always lands in ml/data/ (gitignored).
    path = hf_hub_download(
        repo_id="Capycap-AI/CaptchaSolve30k",
        repo_type="dataset",
        filename="train.jsonl",
        local_dir=Path(__file__).resolve().parent.parent / "data" / "captchasolve30k",
    )
    df = pl.read_ndjson(path)
    df
    return (df,)


@app.cell
def _():
    import base64

    import numpy as np

    def decode_input_stream(b64_stream: str, sample_count: int) -> np.ndarray:
        """Decode `inputStream` as documented in the dataset README.

        README layout: 9 bytes per sample = float32 x, float32 y, uint8 button.
        NOTE: the data does not follow it, see the bytes-per-sample cell below.
        """
        data = base64.b64decode(b64_stream)
        if len(data) != sample_count * 9:
            raise ValueError(
                f"{len(data)} bytes for {sample_count} samples is "
                f"{len(data) / sample_count:.1f} bytes/sample, README says 9"
            )
        dtype = np.dtype([("x", "<f4"), ("y", "<f4"), ("is_down", "u1")])
        return np.frombuffer(data, dtype=dtype)

    return base64, np


@app.cell
def _(base64, df, pl):
    # Observation: bytes per raw sample actually stored vs. README's 9.
    df.select(
        bytes_per_sample=pl.struct("inputStream", "inputSampleCount").map_elements(
            lambda r: len(base64.b64decode(r["inputStream"])) / r["inputSampleCount"],
            return_dtype=pl.Float64,
        )
    ).to_series().value_counts()
    return


@app.cell
def _(np, pl):
    TICK_HZ = 240  # README: physics ticks at 240 Hz; tick i happens at i / 240 s
    # TODO(team): choose the observation window the widget will collect.
    WINDOW_TICKS = 720  # 3 s, provisional

    def session_features(ticks: list[dict]) -> dict[str, float] | None:
        """Behavioural features over a fixed window starting at the first movement.

        Time comes from the tick position (240 Hz), not from `sampleIndex`, which
        only indexes the raw input stream. Consecutive ticks can repeat a sample,
        so keep the first tick of each distinct `sampleIndex` and use its tick time.
        """
        xy_all = np.array([[t["x"], t["y"]] for t in ticks])
        moving = np.flatnonzero(np.abs(xy_all).sum(axis=1) > 0)
        start = moving[0]
        if len(ticks) - start < WINDOW_TICKS:
            return None  # too short for the window
        win = ticks[start : start + WINDOW_TICKS]
        first_tick = {}
        for i, t in enumerate(win):
            first_tick.setdefault(t["sampleIndex"], i)
        tick_idx = np.array(sorted(first_tick.values()))
        xy = np.array([[win[i]["x"], win[i]["y"]] for i in tick_idx])

        dt = np.diff(tick_idx) / TICK_HZ  # seconds
        dist = np.hypot(*np.diff(xy, axis=0).T)
        speed = dist / dt
        accel = np.abs(np.diff(speed)) / dt[1:]
        return {
            "speed_mean": float(speed.mean()),
            "speed_std": float(speed.std()),
            "speed_max": float(speed.max()),
            "accel_mean": float(accel.mean()),
            "pause_frac": float((dist == 0).mean()),
        }

    def featurize(frame: pl.DataFrame) -> pl.DataFrame:
        rows = [session_features(t) for t in frame["tickInputs"].to_list()]
        keep = [r is not None for r in rows]
        return pl.DataFrame([r for r in rows if r is not None]).with_columns(
            frame.filter(pl.Series(keep)).select("index", "gameType", "touchscreen")
        )

    return WINDOW_TICKS, featurize


@app.cell
def _(df, featurize):
    X = featurize(df)
    X
    return (X,)


@app.cell
def _(X, pl):
    from sklearn.ensemble import IsolationForest

    FEATURES = ["speed_mean", "speed_std", "speed_max", "accel_mean", "pause_frac"]

    forest = IsolationForest(n_estimators=300, random_state=0).fit(X[FEATURES])
    # score_samples: lower = more anomalous. decision_function < 0 means "outlier"
    # under contamination="auto" (offset fitted so ~ -0.5 is the cutoff).
    scored = X.with_columns(
        score=pl.Series(forest.score_samples(X[FEATURES])),
        flagged=pl.Series(forest.predict(X[FEATURES]) == -1),
    )
    scored.select("score").describe()
    return FEATURES, IsolationForest, scored


@app.cell
def _(pl, scored):
    # Where do flagged sessions come from? If they are all just long/odd-but-human
    # sessions, the tail is natural variation rather than a hidden bot population.
    scored.group_by("gameType", "touchscreen").agg(
        n=pl.len(),
        flagged_rate=pl.col("flagged").mean(),
        score_p01=pl.col("score").quantile(0.01),
        score_median=pl.col("score").median(),
    ).sort("gameType", "touchscreen")
    return


@app.cell
def _(scored):
    # The 20 most isolated sessions, to eyeball.
    scored.sort("score").head(20)
    return


@app.cell
def _(FEATURES, IsolationForest, X, pl):
    # Same forest, refit on mouse sessions only: touchscreen sessions form their own
    # human population and dominated the first fit's tail.
    mouse = X.filter(~pl.col("touchscreen"))
    mouse_forest = IsolationForest(n_estimators=300, random_state=0).fit(mouse[FEATURES])
    mouse_scored = mouse.with_columns(
        score=pl.Series(mouse_forest.score_samples(mouse[FEATURES])),
        flagged=pl.Series(mouse_forest.predict(mouse[FEATURES]) == -1),
    )
    mouse_scored.group_by("gameType").agg(
        n=pl.len(),
        flagged_rate=pl.col("flagged").mean(),
        score_p01=pl.col("score").quantile(0.01),
        score_median=pl.col("score").median(),
        score_min=pl.col("score").min(),
    ).sort("gameType")
    return (mouse_scored,)


@app.cell
def _(mouse_scored):
    mouse_scored.sort("score").head(20)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo, mouse_scored, pl):
    # Two groups of mouse sessions (ids are the dataset's `index`, for reproducing):
    #   most isolated  - the 10 lowest isolation-forest scores
    #   typical        - the 10 scores closest to the median
    top10 = mouse_scored.sort("score").head(10)
    median_score = mouse_scored["score"].median()
    avg10 = (
        mouse_scored.with_columns((pl.col("score") - median_score).abs().alias("dist"))
        .sort("dist")
        .head(10)
    )
    mo.md(
        f"Most isolated ids: `{top10['index'].to_list()}`  \n"
        f"Typical ids (median score {median_score:.3f}): `{avg10['index'].to_list()}`"
    )
    return avg10, top10


@app.cell
def _():
    import random

    from cursora_ml.replay import render_replay, simulate

    return random, render_replay, simulate


@app.cell
def _(WINDOW_TICKS, df, mouse_scored, render_replay, simulate):
    from functools import lru_cache

    @lru_cache(maxsize=32)
    def replay_html(session_id: int) -> str:
        """Self-contained replay page for one dataset session (`index`)."""
        row = df.filter(df["index"] == session_id).row(0, named=True)
        score = mouse_scored.filter(mouse_scored["index"] == session_id)["score"][0]
        ticks = row["tickInputs"]
        first = next(i for i, t in enumerate(ticks) if t["x"] or t["y"])
        data = simulate(row["gameType"], row["puzzleSeed"], ticks)
        title = (
            f"session #{session_id} · {row['gameType']}<br>"
            f"<small>puzzleSeed {row['puzzleSeed']} · score {score:.3f} · "
            f"blue bar = {WINDOW_TICKS}-tick feature window</small>"
        )
        return render_replay(data, title=title, window=(first, first + WINDOW_TICKS))

    return (replay_html,)


@app.cell
def _(avg10, mo, top10):
    def session_label(row: dict) -> str:
        return f"#{row['index']} · {row['gameType']} · score {row['score']:.3f}"

    out_labels = {session_label(r): r["index"] for r in top10.iter_rows(named=True)}
    avg_labels = {session_label(r): r["index"] for r in avg10.iter_rows(named=True)}
    get_out, set_out = mo.state(top10["index"][0])
    get_avg, set_avg = mo.state(avg10["index"][0])
    return avg_labels, get_avg, get_out, out_labels, set_avg, set_out


@app.cell
def _(get_out, mo, out_labels, random, set_out):
    out_by_id = {v: k for k, v in out_labels.items()}
    out_pick = mo.ui.dropdown(
        out_labels, value=out_by_id[get_out()], on_change=set_out, label="Most isolated"
    )
    out_random = mo.ui.button(
        label="Pick random",
        on_click=lambda _: set_out(random.choice(list(out_labels.values()))),
    )
    return out_pick, out_random


@app.cell
def _(avg_labels, get_avg, mo, random, set_avg):
    avg_by_id = {v: k for k, v in avg_labels.items()}
    avg_pick = mo.ui.dropdown(
        avg_labels, value=avg_by_id[get_avg()], on_change=set_avg, label="Typical"
    )
    avg_random = mo.ui.button(
        label="Pick random",
        on_click=lambda _: set_avg(random.choice(list(avg_labels.values()))),
    )
    return avg_pick, avg_random


@app.cell
def _(
    avg_pick,
    avg_random,
    get_avg,
    get_out,
    mo,
    out_pick,
    out_random,
    replay_html,
):
    mo.hstack(
        [
            mo.vstack(
                [
                    mo.md("### Most isolated"),
                    mo.hstack([out_pick, out_random]),
                    mo.iframe(replay_html(get_out()), height="560px"),
                ]
            ),
            mo.vstack(
                [
                    mo.md("### Typical (closest to median score)"),
                    mo.hstack([avg_pick, avg_random]),
                    mo.iframe(replay_html(get_avg()), height="560px"),
                ]
            ),
        ],
        widths="equal",
        align="start",
    )
    return


if __name__ == "__main__":
    app.run()
