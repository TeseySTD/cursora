# Source of the `shadcn` skill

Vendored third-party skill. Do not edit it in place: update it from upstream, review the diff,
and record the new commit here and in the skills table of `AGENTS.md`.

| Field    | Value                                                  |
| -------- | ------------------------------------------------------ |
| Upstream | [shadcn-ui/ui](https://github.com/shadcn-ui/ui/tree/481d523374745e77d0cf9c53a4115ab5dd7c8481/skills/shadcn)                                        |
| Path     | `skills/shadcn`                                               |
| Commit   | `481d523374745e77d0cf9c53a4115ab5dd7c8481`                                                |
| License  | MIT (upstream licence text in `LICENSE`)            |
| Reviewed | 2026-10-25, AI-assisted review at import (see below) |

Review at import: every file was read; no hidden or prompt-injection instructions, telemetry,
credential access or commands that run automatically were left in; files were checked
byte-for-byte against the upstream git tree at the commit above.

## Local modifications

- `SKILL.md`: removed `allowed-tools` (it pre-approved running `npx shadcn@latest`, i.e. the
  latest npm release, without a prompt) and replaced the dynamic-context block under "Current
  Project Context", which ran `npx shadcn@latest info --json` automatically whenever the skill
  loaded, with an instruction to run the CLI version pinned in the app. Added a "Cursora" note
  under the title: use the pinned CLI instead of `npx`/`pnpm dlx`/`bunx shadcn@latest`, run
  `info` yourself, Radix (not Base UI), ask before registries/presets, widget caveats.
- `SKILL.md` and `cli.md`: the "IMPORTANT" package-runner sentence (which sent pnpm projects to
  `pnpm dlx shadcn@latest`) now tells the agent to use the CLI pinned in the project.
- Removed `agents/openai.yml`, `assets/shadcn.png`, `assets/shadcn-small.png` (Codex UI metadata
  and its icons) and `evals/evals.json` (upstream evaluation data). Nothing references them.

