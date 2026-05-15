# Fidelity audit

Compare **claimed** (vendor-published, in `bi.qubits.qubit_info`)
against **measured** (XEB + readout calibration). Report the delta with
its sign.

## Claimed source — what's in the cache

```python
from uniqc import find_backend

bi = find_backend("originq:WK_C180")
for q in sorted(bi.qubits.available_qubits)[:4]:
    info = bi.qubits.qubit_info[q]
    print(f"q{q}  T1={info.T1}  T2={info.T2}  "
          f"single_qubit_gate_error={info.single_qubit_gate_error}  "
          f"readout_error_p01={info.readout_error_p01}  "
          f"readout_error_p10={info.readout_error_p10}")

for (i, j), info in bi.qubits.qubit_info.items() if hasattr(bi.qubits.qubit_info, "items") else []:
    if isinstance((i, j), tuple):
        print(f"({i},{j})  two_qubit_gate_error={info.two_qubit_gate_error}")
```

(The exact attribute names on `qubit_info[...]` vary slightly per
adapter; consult the doc-generated `BackendInfo` page if you need a
field that isn't present.)

## Measured source — three workflows

```python
from uniqc.algorithms.workflows import xeb_workflow, readout_em_workflow

CHIP = "originq:WK_C180"
target = sorted(bi.qubits.available_qubits)[:4]

xeb_1q  = xeb_workflow.run_1q_xeb_workflow(
    backend=CHIP, target_qubits=target,
    depths=[5, 10, 20, 40], n_circuits=30, shots=1000)        # dict[str, XEBResult]

xeb_2q  = xeb_workflow.run_2q_xeb_workflow(
    backend=CHIP, pairs=[(target[i], target[i+1]) for i in range(len(target)-1)],
    depths=[5, 10, 20], n_circuits=30, shots=1000)

readout = readout_em_workflow.run_readout_em_workflow(
    backend=CHIP, qubits=target, shots=2000)                  # ReadoutEM (not the dataclass)
```

## Building the comparison table

```python
def f_to_e(f):                      # F = 1 - error per layer
    return max(0.0, 1.0 - f)

print(f"{'qubit':>6} {'claimed_e_1q':>12} {'measured_e_1q':>13} {'delta':>10}")
for q in target:
    info = bi.qubits.qubit_info[q]
    claimed = float(getattr(info, "single_qubit_gate_error", float("nan")))
    measured = f_to_e(xeb_1q[f"q{q}"].fidelity_per_layer)
    print(f"{q:>6} {claimed:>12.4f} {measured:>13.4f} {measured - claimed:>+10.4f}")
```

For 2q, swap `xeb_1q[f"q{q}"]` for `xeb_2q[f"({i},{j})"]`. For
readout, build the confusion matrix and compare its off-diagonals to
`info.readout_error_p01` / `info.readout_error_p10`.

## Parallel-CZ crosstalk (uniqc 0.0.13 new module)

Vendor metadata typically reports per-pair 2q error in **isolation**.
The chip-in-production reality is that simultaneous CZs interfere.
0.0.13 adds `uniqc.calibration.xeb.parallel_cz` to measure exactly
this gap.

```python
from uniqc.algorithms.workflows.xeb_workflow import run_parallel_cz_xeb_workflow

results_cz = run_parallel_cz_xeb_workflow(
    backend=CHIP, target_qubits=target,
    depths=[5, 10, 20], n_circuits=20, shots=1000,
)
for k, v in results_cz.items():
    print(k, v.fidelity_per_layer, "vs isolated:",
          xeb_2q[k].fidelity_per_layer if k in xeb_2q else "n/a")
```

A consistent gap (parallel < isolated) is normal; the absolute size is
the audit finding. If parallel ≈ isolated, the chip has remarkable
isolation; if parallel ≪ isolated, the vendor 2q numbers are
misleading for any algorithm that uses parallel CZs.

## Interpreting the deltas

| measured − claimed | What it usually means                                      |
| ------------------ | ---------------------------------------------------------- |
| `0.000 ± shot noise` | Vendor characterization is up to date.                   |
| `+0.001 .. +0.005` | Chip is slightly better than published; published is conservative. |
| `−0.001 .. −0.005` | Mild drift; still safe for most algorithms.                |
| `−0.005 .. −0.020` | Significant drift; readout EM helps; consider re-running calibration. |
| `< −0.020`         | Chip is in degraded state; flag and switch backend or wait. |
| `pre-flight raised` | Vendor metadata claims a calibrated pair, but uniqc's pre-flight policy disagrees. **Trust uniqc**, not the vendor cache. |

## Sample output snippet

```
Chip: originq:WK_C180  cached_at=2026-05-14T08:00Z  measured_at=2026-05-14T15:42Z

1q gate error (per layer):
   qubit  claimed  measured     Δ
       0   0.0014    0.0021  +0.0007
       1   0.0012    0.0018  +0.0006
       2   0.0015    0.0023  +0.0008
       3   0.0011    0.0014  +0.0003

2q gate error (per layer, isolated):
   pair      claimed  measured     Δ
   (0,1)      0.0089    0.0102  +0.0013
   (1,2)      0.0091    0.0117  +0.0026
   (2,3)      0.0094    0.0123  +0.0029

2q gate error (per layer, parallel):
   pair      isolated  parallel  gap
   (0,1)      0.0102    0.0148  +0.0046
   (1,2)      0.0117    0.0192  +0.0075
   (2,3)      0.0123    0.0185  +0.0062

Readout (assignment fidelity):
   qubit  claimed_F  measured_F     Δ
       0    0.9870    0.9842   −0.0028
       1    0.9881    0.9852   −0.0029
       2    0.9879    0.9849   −0.0030
       3    0.9874    0.9851   −0.0023

Verdict: cache is ~7h stale; mild systematic drift; safe for
        algorithms that tolerate 2q error around 1.2%; **not** safe for
        depth-50 random circuits without QEM. Consider running readout
        EM workflow before publishing results.
```

## Pitfalls

- **Sample size matters.** With `n_circuits=10, shots=200`, the XEB
  fit error is large enough to swallow real drift. Use ≥ 30 circuits
  and ≥ 1000 shots for an audit you intend to act on.
- **Compare like for like.** XEB measures *fidelity per layer of the
  random pattern* — this is not exactly the same number as the
  vendor's "single-qubit gate error" if the vendor uses RB instead of
  XEB. Treat XEB-vs-claimed comparisons as **lower-bound** on agreement.
- **Use the parallel-CZ workflow only on chips that advertise CZ as a
  basis gate.** On a `cnot`-basis chip (rare), the pre-flight will
  reject the request — that's expected.
- **Calibration cache** lives at `~/.uniqc/calibration_cache/`; reuse
  results within `max_age_hours` to keep the audit cheap.
