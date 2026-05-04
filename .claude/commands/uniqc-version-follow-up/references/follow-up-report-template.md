# Version Follow-Up Report Template

Use this for the final handoff or PR body.

## UnifiedQuantum Release

- Version/tag:
- Release URL:
- Release date:
- UnifiedQuantum commit:

## Sources Inspected

- Release notes:
- Best-practices guide:
- Best-practices notebooks:
- CLI help commands:
- AI hint/config commands:
- Source files inspected for ambiguous behavior:

## Skill Updates

- `README.md`:
- `skills/uniqc-basic-usage/SKILL.md`:
- `skills/uniqc-basic-usage/references/best-practices.md`:
- CLI/cloud/simulator/troubleshooting references:
- Examples/scripts:

## Important Behavioral Changes Reflected

List concrete behavior changes, not generic statements.

Examples:

- New or changed top-level imports.
- CLI command or module fallback changes.
- AI hint / progressive-disclosure changes.
- Backend id semantics.
- Config/cache path changes.
- IBM proxy configuration changes.
- Real-device, dry-run, Calibration/QEM/XEB changes.
- Deprecated integrations.

## Validation

| Command | Status | Notes |
|---|---|---|
| `python3 -m py_compile skills/uniqc-basic-usage/examples/*.py` |  |  |
| `bash -n skills/uniqc-basic-usage/examples/cli_demo.sh` |  |  |
| `bash -n skills/uniqc-basic-usage/scripts/setup_uniqc.sh` |  |  |
| `git diff --check` |  |  |

## Known Gaps

Record any upstream command that could not be executed, any optional dependency not installed, and whether the skill update depended on source inspection instead.

## PR

- Branch:
- Commit:
- PR URL:
