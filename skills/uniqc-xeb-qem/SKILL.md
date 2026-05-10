---
name: uniqc-xeb-qem
description: "Use when the user wants to characterize hardware (XEB benchmarking) or apply quantum error mitigation (QEM) to readout results in UnifiedQuantum. Covers `xeb_workflow.run_1q/2q/parallel_xeb_workflow`, `readout_em_workflow.run_readout_em_workflow`, and the `ReadoutEM.apply` / `M3Mitigator.apply` pipeline. Includes the CLI (`uniqc calibrate xeb / readout / pattern`) and the calibration cache layout."
---

# Uniqc XEB & QEM Skill

This skill covers two adjacent topics:

1. **Calibration / benchmarking** — measure hardware error rates with XEB
   (1q, 2q, parallel) and readout calibration. Results are cached to
   `~/.uniqc/calibration_cache/`.
2. **Mitigation** — apply readout error mitigation to a `UnifiedResult`
   via `ReadoutEM.apply()` or `M3Mitigator.apply()` (pipeline-style,
   returns a fresh `UnifiedResult`).

> ⚠️ `uniqc.qem.ZNE` exists but **raises `NotImplementedError`** —
> only readout mitigation is real today. Do not promise ZNE.

## First decision

| User goal                                                  | Read first                                                |
| ---------------------------------------------------------- | --------------------------------------------------------- |
| "Measure 1-qubit / 2-qubit gate fidelity"                  | [references/xeb.md](references/xeb.md) (`run_1q_xeb_workflow`, `run_2q_xeb_workflow`) |
| "Run XEB on every pair of a chip in parallel"              | [references/xeb.md](references/xeb.md) (`run_parallel_xeb_workflow`) |
| "Calibrate readout once, then mitigate many results"       | [references/qem.md](references/qem.md)                    |
| "I just want one-shot mitigation on a `UnifiedResult`"     | [references/qem.md](references/qem.md) — `.apply()` pipeline |
| "How is XEB / readout cached and how do I invalidate it?"  | [references/cache.md](references/cache.md)                |

## Mental model

```
              ┌──────────────────┐                ┌──────────────────┐
backend  ──►  │  calibration     │ ──►  cache  ──►│ mitigation       │ ──► clean result
              │  (XEB / readout) │       JSON     │ ReadoutEM / M3   │
              └──────────────────┘                └──────────────────┘
```

- Calibration is a *measurement* — it costs shots on the target backend.
- The result is **cached** with an ISO-8601 timestamp; subsequent calls
  reuse it as long as `max_age_hours` is not exceeded.
- Mitigation is *post-processing* on a separate `UnifiedResult`.

## Practical defaults

- For first-time users on a chip: run readout calibration once, then
  use it for the day. `max_age_hours=24.0` is the default and usually
  fine.
- XEB shots default 1000 / depth, n_circuits 50. For NISQ chips with
  ~99% gate fidelity that is a reasonable signal-to-noise point.
- `use_readout_em=True` (the default) makes XEB report gate-only fidelity
  by mitigating the readout error first.
- `M3Mitigator` is for marginal mitigation (per-qubit-or-pair); construct
  it with `calibration_result=ReadoutCalibrationResult(...)`. `ReadoutEM`
  takes a backend adapter and runs its own calibration on first use.
- Backend is always a string id: `dummy:local:simulator`,
  `dummy:local:virtual-line-3`, `dummy:originq:WK_C180`, `originq:WK_C180`, etc.

## CLI cheat sheet

```bash
# 1q XEB on qubits 0..3, dummy
uniqc calibrate xeb --qubits 0 1 2 3 --type 1q --backend dummy:local:simulator --shots 1000 --depths 5 10 20 40

# 2q XEB on the pair (0, 1) — when --type 2q, the qubits list is paired
uniqc calibrate xeb --qubits 0 1 --type 2q --backend dummy:local:simulator --shots 1000

# Readout calibration (cached)
uniqc calibrate readout --qubits 0 1 2 3 --backend dummy:local:simulator --shots 1000

# Inspect cached entries
ls ~/.uniqc/calibration_cache/
```

> There is **no** `--parallel` flag on `uniqc calibrate xeb`. For
> parallel XEB use the Python `xeb_workflow.run_parallel_xeb_workflow(...)`.

## Python cheat sheet

```python
from uniqc.algorithms.workflows import xeb_workflow, readout_em_workflow

# XEB
results_1q = xeb_workflow.run_1q_xeb_workflow(
    backend="dummy:local:virtual-line-3", qubits=[0, 1, 2], shots=1000)
results_2q = xeb_workflow.run_2q_xeb_workflow(
    backend="dummy:local:virtual-line-3", pairs=[(0, 1), (1, 2)], shots=1000)

# Readout calibration — returns a ready-to-use ReadoutEM (not a
# ReadoutCalibrationResult). Apply directly via .apply().
em = readout_em_workflow.run_readout_em_workflow(
    backend="dummy:local:virtual-line-3", qubits=[0, 1, 2], shots=1000)

# QEM as a pipeline transformation
clean = em.apply(noisy_unified_result)        # -> UnifiedResult

# To use M3Mitigator instead, fetch the underlying ReadoutCalibrationResult
# from the cache (see references/qem.md).
```

## Names to remember

- Calibration workflows:
  `xeb_workflow.run_1q_xeb_workflow`,
  `xeb_workflow.run_2q_xeb_workflow`,
  `xeb_workflow.run_parallel_xeb_workflow`,
  `xeb_workflow.run_parallel_cz_xeb_workflow`,
  `readout_em_workflow.run_readout_em_workflow`,
  `readout_em_workflow.apply_readout_em`.
- Result types: `XEBResult`, `ReadoutCalibrationResult`,
  `find_cached_results(...)` (uses `result_type=` keyword).
- Mitigators: `uniqc.qem.ReadoutEM(adapter, max_age_hours, cache_dir, shots)`,
  `uniqc.qem.M3Mitigator(calibration_result, cache_path, max_age_hours, backend, qubit, cache_dir)`.
- Cache: `~/.uniqc/calibration_cache/` (JSON files, ISO-8601 timestamps).
- Errors: `uniqc.qem.StaleCalibrationError` (inherits from `Exception`,
  **not** `UnifiedQuantumError` — catch explicitly).

## Response style

- Lead with "is this calibration cached?" — almost always the user already
  has a recent run and just wants to apply it.
- For mitigation requests, prefer the `.apply(unified_result)` pipeline
  style; only mention `mitigate_counts` / `mitigate_probabilities` when
  the user has a raw dict.
- For XEB results, always plot the per-depth fidelity decay along with
  the fitted `r` (per-layer fidelity).
