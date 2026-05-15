# XEB benchmarking

Cross-entropy benchmarking estimates 1q / 2q gate fidelity by running random
circuits at increasing depth and fitting an exponential decay
`F(m) = A * r^m + B`. The per-layer fidelity `r` is what gets reported.

## CLI

```bash
# 1q XEB on qubits 0..3 against dummy
uniqc calibrate xeb --qubits 0 1 2 3 --type 1q --backend dummy:local:simulator --shots 1000 --depths 5 10 20 40

# 2q XEB — when --type 2q, the qubits list is paired (qubits[0], qubits[1])
uniqc calibrate xeb --qubits 0 1 --type 2q --backend dummy:local:simulator --shots 1000

# Real chip (uses cached chip characterization)
uniqc calibrate xeb --backend originq:WK_C180 --qubits 0 1 --type 2q --shots 1000
```

Note: there is **no** `--parallel` flag on the CLI. For parallel multi-pair
runs, use the Python API below.

## Python — 1q

```python
from uniqc.algorithms.workflows import xeb_workflow

results_1q = xeb_workflow.run_1q_xeb_workflow(
    backend="dummy:local:virtual-line-3",
    qubits=[0, 1, 2],
    depths=[5, 10, 20, 40],
    n_circuits=50,
    shots=1000,
    use_readout_em=True,         # mitigate readout first; report gate-only fidelity
    max_age_hours=24.0,
    seed=42,
)                                  # -> dict[int, XEBResult]  keyed by qubit
for q, r in results_1q.items():
    print(f"q{q}: F_per_layer = {r.fidelity_per_layer:.4f} ± {r.fidelity_std_error:.4f}")
```

## Python — 2q

```python
results_2q = xeb_workflow.run_2q_xeb_workflow(
    backend="dummy:local:virtual-line-3",
    pairs=[(0, 1), (1, 2)],       # the kwarg is `pairs=`, NOT `qubit_pairs=`
    depths=[5, 10, 20],
    n_circuits=50,
    shots=1000,
    use_readout_em=True,
)                                  # -> dict[tuple[int, int], XEBResult]
for pair, r in results_2q.items():
    print(f"{pair}: F = {r.fidelity_per_layer:.4f}")
```

## Python — parallel 2q on a whole chip

```python
results_par = xeb_workflow.run_parallel_xeb_workflow(
    backend="dummy:originq:WK_C180",
    target_qubits=[0, 1, 2, 3, 4, 5, 6, 7],
    depths=[5, 10, 20],
    n_circuits=30,
    shots=1000,
)                                  # -> dict[str, XEBResult] keyed by pair label
```

For an entangling-gate-specific pass (CZ-only) — uniqc 0.0.13 ships a dedicated `parallel_cz` benchmarking module under `uniqc.calibration.xeb.parallel_cz` with a **strict pre-flight policy**: `xeb_workflow` refuses to dispatch experiments whose chip-level prerequisites (calibrated CZ pairs, in-region qubits, basis-gate availability) are not satisfied, instead of failing silently downstream. The high-level workflow entry point is unchanged:

```python
from uniqc.algorithms.workflows.xeb_workflow import run_parallel_cz_xeb_workflow
results_cz = run_parallel_cz_xeb_workflow(
    backend="dummy:originq:WK_C180",
    target_qubits=[0, 1, 2, 3],
    depths=[5, 10, 20],
)
```

CLI variant (parallel-CZ XEB is exposed under the same `uniqc calibrate xeb` family as of 0.0.13; the `--type` enum now includes `parallel_cz`):

```bash
uniqc calibrate xeb --qubits 0 1 2 3 --type parallel_cz --backend dummy:originq:WK_C180 --shots 1000
```

## `XEBResult` fields

```python
from uniqc import XEBResult
# verify with: from dataclasses import fields; print(fields(XEBResult))

result.calibrated_at        # str: ISO-8601 UTC timestamp
result.backend              # str: backend identifier
result.type                 # str: 'xeb_1q' | 'xeb_2q' | 'xeb_2q_parallel'
result.qubit                # int | None: target qubit (1q runs)
result.pairs                # tuple[tuple[int, int], ...] | None: target pairs (2q)
result.fidelity_per_layer   # float: per-layer fidelity = r in F(m) = A*r^m + B
result.fidelity_std_error   # float: standard error from the fit
result.fit_a                # float
result.fit_b                # float
result.fit_r                # float (== fidelity_per_layer)
result.depths               # tuple[int, ...]
result.n_circuits           # int per depth
result.shots                # int per circuit
```

## Plotting the decay

```python
import matplotlib.pyplot as plt
import numpy as np

depths = np.array(result.depths)
fit = result.fit_a * (result.fit_r ** depths) + result.fit_b

# `result.fidelity_per_depth` exists when present; otherwise compute from raw counts
if hasattr(result, "fidelity_per_depth"):
    plt.plot(depths, result.fidelity_per_depth, "o", label="measured")
plt.plot(depths, fit, "-", label=f"fit r={result.fit_r:.4f}")
plt.xlabel("depth (layers)")
plt.ylabel("XEB fidelity")
plt.legend()
plt.tight_layout()
plt.savefig("xeb_decay.png", dpi=160)
```

## Cached XEB lookup

```python
from uniqc.calibration import find_cached_results

# Note the keyword: result_type= (NOT type=)
hits = find_cached_results(backend="dummy:local:virtual-line-3", result_type="xeb_1q")
for h in hits:
    print(h.calibrated_at, h.qubit, h.fidelity_per_layer)
```

## Common mistakes

- Passing `qubit_pairs=` to `run_2q_xeb_workflow` — the keyword is `pairs=`.
- Treating `result.type` literals as `'1q'` / `'2q'` — they are
  `'xeb_1q'` / `'xeb_2q'` / `'xeb_2q_parallel'`.
- Using the CLI `--parallel` flag — does not exist; use the Python
  `run_parallel_xeb_workflow`.
- Running XEB against a chip-backed dummy (`dummy:originq:WK_C180`) — qiskit
  is the transpiler. As of uniqc 0.0.13 qiskit is a **core dependency**, no
  `[qiskit]` extra needed; `submit_task` only raises `CompilationFailedError`
  for genuine basis-gate / topology issues (e.g. an un-calibrated CZ pair
  caught by the new pre-flight policy).
