# Source of the `marimo-notebook` skill

Third-party skill adapted to this repository. To update it, re-import from upstream, review the
diff, re-apply the local modifications below, and record the new commit here and in the skills
table of `AGENTS.md`.

| Field    | Value                                                                                                                            |
| -------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Upstream | [marimo-team/skills](https://github.com/marimo-team/skills/tree/06770e79d83d934ef44efd5540332ebcae20a900/skills/marimo-notebook) |
| Path     | `skills/marimo-notebook`                                                                                                         |
| Commit   | `06770e79d83d934ef44efd5540332ebcae20a900`                                                                                       |
| License  | Apache-2.0, modified (upstream licence text in `LICENSE`)                                                                        |
| Reviewed | 2026-11-09, AI-assisted review (see below)                                                                                       |

Review: every file was read; no hidden or prompt-injection instructions, `allowed-tools` grants
or commands that run automatically were found; files were checked byte-for-byte against the
upstream git tree at the commit above before the local modifications.

Findings:

- Examples run unpinned tools (`uvx marimo`, `uv --with marimo`) and install packages directly
  (`pip install`, `uv pip install`, `playwright install`). This repo runs marimo through
  `pnpm ml:notebook` or `uv run`.
- `references/SQL.md` mentions SQLModel; this repo uses SQLAlchemy 2.0 async only.

## Local modifications

Formatted with Prettier, and Python (files and Markdown code blocks) with
`ruff format --preview`. Upstream's `LICENSE` is copied from the repository root. Also:

- `SKILL.md`: added a "Cursora" note on `ml/notebooks` and the `notebook` dependency group; fixed
  the mislabelled `COLUMNS.md` link.
- All commands: `uvx marimo` and `uv --with marimo` replaced by
  `uv run --package cursora-ml --group notebook`; `pip install` and `uv pip install` by `uv add`.
- `references/SQL.md`: removed the SQLModel sentence; made the `mo.sql` signature valid Python.
- `references/ANYWIDGET.md`: fixed the `b8utton` typo.
- `references/WATCHING.md`: the second `mo.watch.file` is `mo.watch.directory`.
