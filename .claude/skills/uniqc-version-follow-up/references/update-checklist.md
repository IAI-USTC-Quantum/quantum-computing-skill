# Version Follow-Up Checklist

Use this as a gate before opening a PR.

## Release Discovery

- [ ] `gh release view` or equivalent confirms latest UnifiedQuantum tag, date, and release notes.
- [ ] Local UnifiedQuantum checkout is on the release tag or contains the release commit.
- [ ] `CHANGELOG.md`, `README.md`, `README_en.md`, `pyproject.toml`, and release docs were checked.
- [ ] Any sandbox-related GitHub CLI failure was retried outside the sandbox before reporting auth/network failure.

## Best Practices

- [ ] `docs/source/guide/best_practices.md` was read.
- [ ] `docs/source/best_practices/index.md` was read.
- [ ] Every notebook in `docs/source/best_practices/*.ipynb` was scanned for imports, commands, backend ids, and outputs.
- [ ] `references/best-practices.md` reflects the latest recommended paths.
- [ ] README states the skill has followed up the latest UnifiedQuantum version.

## CLI Help Alignment

- [ ] Root `uniqc --help` checked.
- [ ] `python -m uniqc.cli --help` checked or source-confirmed.
- [ ] Every visible subcommand help checked.
- [ ] Nested backend command help checked.
- [ ] `--ai-hints` / `--ai-hint`, `UNIQC_AI_HINTS=1`, and `uniqc config always-ai-hint` checked when present.
- [ ] `references/cli-guide.md` matches help output.
- [ ] Examples and scripts use supported CLI commands only.
- [ ] No nonexistent CLI commands such as `uniqc workflow` are introduced unless help confirms them.

## API and Module Alignment

- [ ] `SKILL.md` imports/snippets use current recommended top-level APIs.
- [ ] Deprecated or old entries are not recommended in the happy path.
- [ ] Dummy backend id semantics match upstream docs.
- [ ] Config, task cache, backend cache, chip cache, and calibration cache paths match upstream docs/code.
- [ ] Cloud/real-device guidance includes dry-run and low-shot verification.
- [ ] IBM proxy configuration is documented if upstream exposes it through `uniqc config`.
- [ ] Frontend/Gateway behavior is mentioned if release notes or docs changed it.

## Validation

- [ ] `python3 -m py_compile examples/*.py`
- [ ] `bash -n examples/cli_demo.sh`
- [ ] `bash -n scripts/setup_uniqc.sh`
- [ ] `git diff --check`
- [ ] Any skipped check has a concrete reason.

## PR Hygiene

- [ ] Branch name mentions the UnifiedQuantum version.
- [ ] Commit message is terse and release-specific.
- [ ] Only intended skill files are staged.
- [ ] PR body lists inspected upstream sources and validation commands.
