# Calibration cache

Calibration / XEB results are persisted to `~/.uniqc/calibration_cache/`
as JSON files with ISO-8601 timestamps in the filename. Both the CLI and
the workflows read & write this directory.

## Layout

```
~/.uniqc/calibration_cache/
├── readout/
│   ├── dummy_local_simulator__q0-1-2-3__2026-05-10T15-22-44Z.json
│   └── originq_WK_C180__q0-1-2-3__2026-05-10T15-30-12Z.json
└── xeb/
    ├── 1q/
    │   └── dummy_local_simulator__q0__2026-05-10T15-22-44Z.json
    └── 2q/
        └── dummy_local_simulator__pair0-1__2026-05-10T15-22-44Z.json
```

(File-naming may evolve; treat the layout above as illustrative — always
inspect `~/.uniqc/calibration_cache/` directly when in doubt.)

## Programmatic lookup

```python
from uniqc.calibration import find_cached_results

readout_hits = find_cached_results(
    backend="dummy:local:virtual-line-3", result_type="readout"
)
xeb_1q_hits = find_cached_results(
    backend="dummy:local:virtual-line-3", result_type="xeb_1q"
)
xeb_2q_hits = find_cached_results(
    backend="dummy:local:virtual-line-3", result_type="xeb_2q"
)

# `result_type` literal values are 'readout' / 'xeb_1q' / 'xeb_2q' / 'xeb_2q_parallel'.
```

> ⚠️ The keyword is `result_type=`, not `type=`. The latter raises
> `TypeError`.

## Freshness

`max_age_hours` (default 24.0) is enforced at every workflow entry point
that consults the cache. If the latest hit is older than the threshold,
the workflow runs a fresh calibration and writes a new JSON file.

```python
from uniqc.algorithms.workflows import readout_em_workflow

# Force a fresh measurement by setting max_age_hours=0:
cal = readout_em_workflow.run_readout_em_workflow(
    backend="dummy:local:virtual-line-3", qubits=[0, 1], shots=1000, max_age_hours=0)
```

`StaleCalibrationError` from `uniqc.qem` is raised when a mitigator is
asked to apply a result older than the threshold — not when one is *missing*.

## Manual invalidation

```bash
# nuclear: drop everything
rm -rf ~/.uniqc/calibration_cache/

# selective: drop one backend's history
rm -f ~/.uniqc/calibration_cache/{readout,xeb/*}/dummy_local_simulator__*.json
```

After deleting, the next `run_*_workflow(...)` call will repopulate.

## Migrating a calibration to a new machine

The directory is plain JSON; copy it whole. The file metadata records
`backend` and `qubits` / `pairs`, so reuse only works when the new
machine targets the same backend identifier (and you trust that the chip
characterization has not drifted since the original measurement).

## Inspecting one entry by hand

```bash
ls -lt ~/.uniqc/calibration_cache/readout/ | head
cat ~/.uniqc/calibration_cache/readout/<file>.json | python -m json.tool | head -40
```

Useful keys: `calibrated_at`, `backend`, `qubits` / `pairs`,
`fidelity_per_layer` (XEB), `confusion_matrices` (readout).
