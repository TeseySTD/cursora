# Source of the `marimo-batch` skill

Third-party skill adapted to this repository. To update it, re-import from upstream, review the
diff, re-apply the local modifications below, and record the new commit here and in the skills
table of `AGENTS.md`.

| Field    | Value                                                                                                                         |
| -------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Upstream | [marimo-team/skills](https://github.com/marimo-team/skills/tree/06770e79d83d934ef44efd5540332ebcae20a900/skills/marimo-batch) |
| Path     | `skills/marimo-batch`                                                                                                         |
| Commit   | `06770e79d83d934ef44efd5540332ebcae20a900`                                                                                    |
| License  | Apache-2.0, modified (upstream licence text in `LICENSE`)                                                                     |
| Reviewed | 2026-11-09, AI-assisted review (see below)                                                                                    |

Review: every file was read; no hidden or prompt-injection instructions, `allowed-tools` grants
or commands that run automatically were found; files were checked byte-for-byte against the
upstream git tree at the commit above before the local modifications.

Findings:

- The examples make network calls and use credentials: Weights & Biases (`wandb.login`,
  `wandb.init`, `WANDB_API_KEY`), Hugging Face Jobs (`run_uv_job` in `references/grid.py`,
  `HF_TOKEN`, only with `--launch`) and an OpenAI key validator in `SKILL.md`. No W&B or remote
  jobs without a team decision.
- The examples read `.env` through python-dotenv, which agents in this repo must not read.

## Local modifications

Formatted with Prettier, and Python (files and Markdown code blocks) with
`ruff format --preview`. Upstream's `LICENSE` is copied from the repository root. Also:

- `SKILL.md`: added a "Cursora" note (no W&B or remote jobs without a team decision, no `.env`
  reads, how to run notebooks); fixed the undefined `cli_args` in the CLI example; the example
  run command uses the `notebook` dependency group.
