---
name: uniqc-version-follow-up
description: "Use when updating the quantum-computing skill after a new UnifiedQuantum/uniqc release. Reads release notes, best-practices docs, notebooks, and CLI help, then updates SKILL.md, references, README, examples, and scripts so the skill follows the latest recommended UnifiedQuantum workflows."
---

# UnifiedQuantum Version Follow-Up Skill

Use this skill to update `quantum-computing.skill` after every UnifiedQuantum release. The result should be a focused PR that makes the skill match the latest release, especially the official best-practices chapter and CLI help.

## Goal

Make the skill answer current UnifiedQuantum questions correctly. Do not only update version text. Check the release notes, best-practices docs, CLI help, examples, and code entry points, then update this skill's instructions, references, examples, and README.

Use [references/update-checklist.md](references/update-checklist.md) as the required checklist and [references/follow-up-report-template.md](references/follow-up-report-template.md) for the PR summary or final handoff.

## Inputs to Discover

1. Latest UnifiedQuantum release:
   - Prefer `gh release view --repo IAI-USTC-Quantum/UnifiedQuantum --json tagName,name,publishedAt,url,body`.
   - Also run `git fetch --tags` and inspect the release tag locally.
   - If `gh` says auth is invalid inside a sandbox, rerun it outside the sandbox before concluding auth is broken.
2. UnifiedQuantum source checkout:
   - Use an existing local checkout if current and clean enough.
   - Otherwise clone `IAI-USTC-Quantum/UnifiedQuantum`.
3. Current skill checkout:
   - Check `git status -sb`.
   - Do not stage unrelated local changes.

## Source Material Order

Read in this order. Stop only when enough evidence is collected; do not skip best practices.

1. Release metadata:
   - `CHANGELOG.md`
   - `docs/source/releases/`
   - `README.md` and `README_en.md`
   - `pyproject.toml`
2. Best practices:
   - `docs/source/guide/best_practices.md`
   - `docs/source/best_practices/index.md`
   - `docs/source/best_practices/*.ipynb`
3. CLI help:
   - `uv run uniqc --help`
   - `uv run python -m uniqc.cli --help`
   - help for every visible subcommand and nested command.
4. Implementation entry points when docs are ambiguous:
   - `uniqc/__init__.py`
   - `uniqc/config.py`
   - `uniqc/cli/`
   - `uniqc/backend_adapter/`
   - `uniqc/gateway/`
   - `uniqc/calibration/`
   - `uniqc/qem/`
   - `uniqc/algorithms/workflows/`

## CLI Help Capture

Use CLI help as progressive disclosure, not as a one-time root command. Capture at least:

```bash
uv run uniqc --help
uv run python -m uniqc.cli --help
uv run uniqc circuit --help
uv run uniqc simulate --help
uv run uniqc submit --help
uv run uniqc result --help
uv run uniqc config --help
uv run uniqc task --help
uv run uniqc backend --help
uv run uniqc backend list --help
uv run uniqc backend show --help
uv run uniqc backend update --help
uv run uniqc backend chip-display --help
uv run uniqc calibrate --help
uv run uniqc gateway --help
uv run uniqc config always-ai-hint --help
```

There is no `uniqc workflow` command unless the latest help explicitly shows one. Treat docs pages named `workflow` as prose guides, not CLI subcommands.

Also inspect the AI guidance path:

- `--ai-hints` and `--ai-hint` command-local flags.
- `UNIQC_AI_HINTS=1`.
- `uniqc config always-ai-hint on/off/status`.
- What the CLI suggests when an agent is uncertain, a command is missing, or an option is rejected. If parser errors cannot print hints directly, document the fallback: run the nearest valid command with `--ai-hint` and inspect parent `--help`.

If local dependencies prevent running CLI help, inspect `pyproject.toml` and `uniqc/cli/`, record the blocker, and still update docs from source. Do not invent commands.

## What to Update in This Skill Repo

Update only files that should change for the new release.

Common targets:

- `README.md`: state the UnifiedQuantum version that has been followed up.
- `SKILL.md`: update the mental model, practical defaults, names, snippets, and navigation.
- `references/best-practices.md`: summarize the latest best-practices chapter.
- `references/cli-guide.md`: align commands, module fallback, subcommands, and examples with CLI help.
- `references/cloud-platforms.md`: update backend ids, dry-run, real-device guidance, task/cache behavior.
- `references/simulators.md`: update local/dummy simulation behavior.
- `references/troubleshooting.md`: update known install/config/dependency failures.
- Algorithm and integration references when release notes changed them.
- `examples/` and `scripts/`: update imports, CLI commands, config paths, and deprecated names.

## Rules for Content Changes

- Prefer top-level imports from `uniqc` when the latest release exposes them.
- Preserve exact package/import naming:
  - PyPI package: `unified-quantum`
  - Python import: `uniqc`
  - CLI command: `uniqc`
  - supported module fallback: `python -m uniqc.cli`
- Never recommend `python -m uniqc` unless the latest CLI help explicitly supports it.
- Never invent `uniqc workflow`; use `--ai-hint(s)` and workflow docs as progressive disclosure unless the release adds a real command.
- Keep old API history out of the main path. Mention old names only in troubleshooting or migration notes.
- Treat best-practices docs as the highest-priority source for recommended user paths.
- For real hardware workflows, include dry-run, backend discovery, low shots, result query, and cache/result recording.
- For AI-agent workflows, recommend `uniqc config always-ai-hint on` as a best-practice one-time setup so hints appear without repeating `--ai-hint`.
- Treat `uniqc.config` as the preferred project-level Python config module when upstream exposes it; mention `uniqc.backend_adapter.config` only as a legacy-compatible path.
- For IBM, check whether docs/help describe proxy config such as `uniqc config set ibm.proxy.https <URL>` and mirror it in this skill when available.
- If Quafu is still deprecated in upstream docs, do not present it as a default path.

## Validation

Run checks that fit the changed files:

```bash
python3 -m py_compile examples/*.py
bash -n examples/cli_demo.sh
bash -n scripts/setup_uniqc.sh
git diff --check
```

If examples depend on optional packages unavailable locally, at least compile them and document unexecuted runtime paths.

## PR Requirements

Create a dedicated branch such as `codex/follow-up-uniqc-vX.Y.Z`. Commit only intended files. Open a draft PR unless the maintainer asks otherwise.

The PR body must include:

- UnifiedQuantum release followed.
- Source material inspected, especially best practices and CLI help.
- User-visible changes in the skill.
- Validation commands run.
- Known gaps or commands that could not be executed.
