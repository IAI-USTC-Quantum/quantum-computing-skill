# Readout calibration and QEM

Readout error mitigation removes detector classification errors from a
`UnifiedResult`. uniqc 0.0.13.dev0 has two implementations:

- **`ReadoutEM`** — straightforward marginal mitigation. Holds a backend
  adapter and a calibration result internally.
- **`M3Mitigator`** — Bravyi-style M3 (matrix-free measurement
  mitigation), built from a `ReadoutCalibrationResult`. Lower memory
  for many qubits.

Both expose `.apply(unified_result)` and return a *new* `UnifiedResult`
with mitigated counts/probabilities.

> ⚠️ **What `run_readout_em_workflow` actually returns**: a
> `ReadoutEM` instance — *not* a `ReadoutCalibrationResult`. So you can
> call `cal.apply(...)` directly without constructing a separate
> mitigator. To build an `M3Mitigator` instead, you need to access the
> raw `ReadoutCalibrationResult` (e.g. via the calibrator API directly,
> or via `find_cached_results(..., result_type="readout")`).

## Step 1 — calibrate (or reuse cache) → ready-to-use `ReadoutEM`

```python
from uniqc.algorithms.workflows import readout_em_workflow

em = readout_em_workflow.run_readout_em_workflow(
    backend="dummy:local:virtual-line-3",
    qubits=[0, 1, 2, 3],
    shots=1000,
    max_age_hours=24.0,
)                              # -> ReadoutEM (already wired with calibration)
```

This call is **idempotent** for `max_age_hours` — reuses the cached
JSON in `~/.uniqc/calibration_cache/` if a fresh-enough entry exists.

For pair-wise mitigation (used by M3 with crosstalk-aware groups):

```python
em = readout_em_workflow.run_readout_em_workflow(
    backend="dummy:local:virtual-line-3",
    pairs=[(0, 1), (2, 3)],
    shots=1000,
)
```

## Step 2 — mitigate (pipeline form, recommended)

```python
clean = em.apply(noisy_result)               # -> UnifiedResult

print("raw      :", dict(sorted(noisy_result.counts.items())))
print("mitigated:", dict(sorted(clean.counts.items())))
```

`clean` is a fresh `UnifiedResult`; counts/probabilities are mitigated,
`raw_result` still points at the original platform payload, and
`task_id` is unchanged.

## `M3Mitigator` (when you specifically want M3)

`M3Mitigator(calibration_result=...)` requires a
`ReadoutCalibrationResult` (subscriptable / dict-like). You can fetch
one from the cache:

```python
from uniqc.calibration import find_cached_results
from uniqc.qem import M3Mitigator

hits = find_cached_results(backend="dummy:local:virtual-line-3", result_type="readout")
cal_result = hits[0]                       # ReadoutCalibrationResult
mitigator = M3Mitigator(calibration_result=cal_result)
clean = mitigator.apply(noisy_result)
```

If you instead try `M3Mitigator(calibration_result=em)` (passing the
`ReadoutEM` instance returned by `run_readout_em_workflow`), uniqc
0.0.13.dev0 raises
`TypeError: 'ReadoutEM' object is not subscriptable` — because M3
indexes the calibration result by field name.

## `ReadoutEM` constructed directly (no workflow helper)

```python
from uniqc.qem import ReadoutEM
from uniqc.backend_adapter import get_adapter

adapter = get_adapter("dummy:local:virtual-line-3")
em = ReadoutEM(adapter, max_age_hours=24.0, shots=1000)

clean = em.apply(noisy_result)               # calibrates lazily on first call
```

This is the easiest "just mitigate me" path when you do not already
have a workflow result around.

## Raw-dict form (legacy, still supported)

```python
mitigated_counts = em.mitigate_counts(noisy_result.counts, measured_qubits=[0, 1])
mitigated_probs  = em.mitigate_probabilities(noisy_result.probabilities, measured_qubits=[0, 1])
```

Use this only when you have a `dict` from outside uniqc; otherwise
`em.apply(unified_result)` is cleaner and propagates metadata.

## Catching stale calibration

```python
from uniqc.qem import StaleCalibrationError

try:
    clean = em.apply(noisy_result)
except StaleCalibrationError as exc:
    print(f"recalibrate: {exc}")
    em = readout_em_workflow.run_readout_em_workflow(
        backend="dummy:local:virtual-line-3", qubits=[0, 1, 2, 3])
    clean = em.apply(noisy_result)
```

> ⚠️ `StaleCalibrationError` inherits directly from `Exception`, **not**
> from `UnifiedQuantumError`. Catch it explicitly.

## Apply mitigation to a list (`apply_readout_em`)

```python
from uniqc.algorithms.workflows.readout_em_workflow import apply_readout_em

mitigated_counts = apply_readout_em(noisy_result, em, measured_qubits=[0, 1])
# -> dict[int, float] keyed by integer index, useful for downstream stats
```

## Combined XEB → ReadoutEM example

```python
from uniqc.algorithms.workflows import xeb_workflow

# Run XEB with use_readout_em=True so the reported r is gate-only.
results = xeb_workflow.run_1q_xeb_workflow(
    backend="dummy:originq:WK_C180",
    qubits=[0, 1, 2, 3],
    use_readout_em=True,           # auto-fits readout calibration first
    shots=1000,
)
```

Inside `run_1q_xeb_workflow`, this triggers `run_readout_em_workflow(...)`
on the same backend, then composes the mitigator before fitting the decay.

## What about ZNE?

```python
from uniqc.qem import ZNE
zne = ZNE()
zne.apply(noisy_result)        # raises NotImplementedError
```

`ZNE` is a placeholder. The skill should not promise ZNE — only readout
mitigation is real today. Track upstream for when this lands.

## Common mistakes

- Passing a `ReadoutEM` (workflow return) to
  `M3Mitigator(calibration_result=...)` — needs a
  `ReadoutCalibrationResult`. See above.
- Passing a `dict` directly to `M3Mitigator.apply(...)` — `.apply`
  expects a `UnifiedResult`. Use
  `mitigate_counts(dict, measured_qubits=[...])` for raw dicts.
- Forgetting `measured_qubits=` on `mitigate_counts` /
  `mitigate_probabilities` when only a subset of qubits was measured.
- Building a fresh `M3Mitigator` per call inside a tight loop — the
  calibration JSON is cached, but constructing the matrix is not free.
  Build it once and reuse.
- Catching `UnifiedQuantumError` and expecting to also catch
  `StaleCalibrationError` — they are unrelated.
