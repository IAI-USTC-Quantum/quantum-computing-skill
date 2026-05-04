# Calibration and QEM Reference

Calibration experiments characterize hardware error rates; QEM (Quantum Error Mitigation) applies those results to correct measurement outcomes. UnifiedQuantum v0.0.9 exposes both as CLI commands and Python APIs.

## Quick Path

1. **Run calibration** (readout + XEB) via CLI or Python.
2. **Apply QEM** to measurement counts via `ReadoutEM` or `M3Mitigator`.
3. Results are cached to `~/.uniqc/calibration_cache/` with ISO-8601 timestamps.

---

## XEB Benchmarking

Cross-entropy benchmarking measures 1q and 2q gate fidelity by running random circuits at increasing depth and fitting an exponential decay.

### CLI

```bash
# 1q XEB on qubits 0,1,2,3
uniqc calibrate xeb --qubits 0 1 2 3 --type 1q --backend dummy --shots 1000 --depths 5 10 20 40

# 2q XEB on qubit pair (0,1)
uniqc calibrate xeb --qubits 0 1 --type 2q --backend dummy --shots 1000

# Parallel 2q XEB on multiple pairs
uniqc calibrate xeb --qubits 0 1 2 3 --type 2q --parallel --backend dummy --shots 1000

# Real chip (uses cached characterization data)
uniqc calibrate xeb --backend origin:wuyuan:WK_C180 --shots 1000
```

### Python API

```python
from uniqc.algorithms.workflows import xeb_workflow

result = xeb_workflow.run_1q_xeb_workflow(
    adapter=dummy_adapter,
    qubits=[0, 1, 2, 3],
    shots=1000,
    depths=[5, 10, 20, 40],
)
print(result.fidelity_per_layer)  # r from exponential fit
print(result.fit_r)               # same value
```

### Result Type: `XEBResult`

```python
from uniqc import XEBResult

# Fields:
result.fidelity_per_layer   # float: per-layer fidelity (exponential decay rate r)
result.fidelity_std_error   # float: standard error of the fit
result.fit_a, result.fit_b  # float: exponential fit parameters (F(m) = A * r^m + B)
result.fit_r                # float: same as fidelity_per_layer
result.depths               # tuple[int]: circuit depths used
result.n_circuits           # int: random circuits per depth
result.shots                # int: shots per circuit
result.backend              # str: backend identifier
```

---

## Readout Calibration

Measures the confusion matrix for single-qubit or two-qubit joint measurements by preparing known states and recording measurement outcomes.

### CLI

```bash
# 1q readout calibration on qubits 0,1
uniqc calibrate readout --qubits 0 1 --backend dummy --shots 1000

# 2q joint readout calibration on pair (0,1)
uniqc calibrate readout --qubits 0 1 --type 2q --backend dummy --shots 1000
```

### Python API

```python
from uniqc.calibration.readout import ReadoutCalibrator

calibrator = ReadoutCalibrator(adapter=dummy_adapter, shots=1000)
result = calibrator.calibrate_1q(qubit=0)
print(result.confusion_matrix)      # [[p00, p10], [p01, p11]]
print(result.assignment_fidelity)   # (p00 + p11) / 2
```

### Result Type: `ReadoutCalibrationResult`

```python
from uniqc import ReadoutCalibrationResult

result.confusion_matrix     # list[list[float]]: row=measured, col=prepared
result.assignment_fidelity  # float: average diagonal element
result.qubit                # int (1q) or tuple[int,int] (2q)
result.type                 # "readout_1q" or "readout_2q"
result.backend              # str: backend identifier
result.calibrated_at        # str: ISO-8601 UTC timestamp
```

---

## Pattern Analysis

Analyzes 2-qubit gate structure to determine parallel execution groups using DSatur graph coloring.

```bash
# Analyze qubit connectivity patterns
uniqc calibrate pattern --qubits 0 1 2 3 4 5

# Analyze a specific circuit
uniqc calibrate pattern --type circuit --circuit my_circuit.ir
```

Output: shows which 2q gate pairs can execute in parallel (layer groups) and the chromatic number of the interaction graph.

---

## QEM: ReadoutEM and M3Mitigator

### ReadoutEM — Unified Interface

`ReadoutEM` is the primary interface for applying readout error mitigation to measurement counts. It wraps `ReadoutCalibrator` internally and dispatches to 1q, 2q, or per-qubit sequential mitigation automatically.

```python
from uniqc import ReadoutEM

# Requires a QuantumAdapter for running calibration circuits
em = ReadoutEM(adapter, max_age_hours=24.0, shots=1000)

# Mitigate raw measurement counts
corrected_counts = em.mitigate_counts(raw_counts, measured_qubits=[0, 1])
```

Dispatch logic:
- **1 qubit**: uses 1q calibration for that qubit
- **2 qubits**: uses 2q joint calibration
- **>2 qubits**: applies per-qubit 1q calibration sequentially (tensor-product approximation)

### M3Mitigator — Confusion Matrix Inversion

`M3Mitigator` uses a pre-computed calibration confusion matrix to correct measurement outcomes via linear inversion.

```python
from uniqc import M3Mitigator

# From a pre-loaded result
mitigator = M3Mitigator(calibration_result=readout_result)

# Or from a cached file
mitigator = M3Mitigator(
    cache_path="~/.uniqc/calibration_cache/readout_1q_dummy_0_20250101T120000Z.json",
    max_age_hours=48.0,
)

corrected = mitigator.mitigate(raw_counts)
```

### StaleCalibrationError

Both `M3Mitigator` and `ReadoutEM` enforce TTL-based freshness. If the calibration data is older than `max_age_hours`, a `StaleCalibrationError` is raised.

```python
from uniqc import StaleCalibrationError

try:
    mitigator = M3Mitigator(cache_path=path, max_age_hours=1.0)
except StaleCalibrationError:
    # Re-run calibration
    ...
```

---

## Workflows Module

High-level functions that combine calibration steps:

```python
from uniqc.algorithms.workflows import xeb_workflow, readout_em_workflow

# XEB workflows
result_1q = xeb_workflow.run_1q_xeb_workflow(adapter, qubits=[0, 1], shots=1000)
result_2q = xeb_workflow.run_2q_xeb_workflow(adapter, qubit_pairs=[(0, 1)], shots=1000)
result_par = xeb_workflow.run_parallel_xeb_workflow(adapter, qubits=[0, 1, 2, 3], shots=1000)

# Readout EM workflow
em_result = readout_em_workflow.run_readout_em_workflow(adapter, qubits=[0, 1], shots=1000)
corrected = readout_em_workflow.apply_readout_em(adapter, raw_counts, measured_qubits=[0, 1])
```

---

## Calibration Cache

- **Location**: `~/.uniqc/calibration_cache/`
- **Naming**: `{type}_{backend}_{qubit}_{timestamp}.json` (e.g. `readout_1q_dummy_0_20250101T120000Z.json`)
- **Persistence**: `save_calibration_result()` and `load_calibration_result()` from `uniqc`
- **Discovery**: `find_cached_results(cache_dir=None, backend=None, type=None)` returns a list of cached results

```python
from uniqc import find_cached_results, load_calibration_result

# Find all cached readout results for the dummy backend
cached = find_cached_results(backend="dummy", type="readout_1q")
if cached:
    result = load_calibration_result(cached[0])
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `StaleCalibrationError` | Calibration data exceeds `max_age_hours` | Re-run `uniqc calibrate readout` or increase `max_age_hours` |
| `FileNotFoundError` in `M3Mitigator` | Missing calibration cache file | Run `uniqc calibrate readout` first |
| Confusion matrix all zeros | Adapter returned empty counts | Check adapter connectivity and shot count |
| `TimelineDurationError` | Duration data missing for a gate | Pass explicit `gate_durations` dict or use backend metadata |
