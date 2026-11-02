import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl

    return (pl,)


@app.cell
def _(pl):
    from huggingface_hub import hf_hub_download

    # Downloads on first run, reuses the local copy afterwards.
    path = hf_hub_download(
        repo_id="Capycap-AI/CaptchaSolve30k",
        repo_type="dataset",
        filename="train.jsonl",
        local_dir="data/captchasolve30k",
    )
    df = pl.read_ndjson(path)
    df
    return


if __name__ == "__main__":
    app.run()
