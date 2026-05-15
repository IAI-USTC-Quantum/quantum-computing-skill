# Chip-backed dummy backends

`dummy:<provider>:<chip>` runs the circuit through the chip's compile
pass (basis-gate transpile + topology mapping), then executes it in a
local noisy density-matrix simulator whose channels are built from
the **cached chip characterization**. It is the most chip-faithful
local execution path uniqc offers — and it spends no quota.

| Identifier                    | Behaviour                                                      |
| ----------------------------- | -------------------------------------------------------------- |
| `dummy:originq:WK_C180`       | OriginQ WK_C180 topology + cached fidelities.                  |
| `dummy:originq:PQPUMESH8`     | OriginQ small chip (3-qubit) — handy for quick experiments.    |
| `dummy:quark:Baihua`          | Quark Baihua topology + cached fidelities.                     |
| `dummy:ibm:ibm_fez`           | IBM Fez topology + cached fidelities.                          |

## Workflow

```python
from uniqc import submit_task, wait_for_result, Circuit

c = Circuit(2)
c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)

uid = submit_task(c, backend="dummy:originq:WK_C180", shots=2000)
result = wait_for_result(uid, timeout=30)
print(result.counts)
```

Because chip-backed dummy goes through the full compile path, you
get the same gate set / topology errors you'd see on real hardware.

## What changed in 0.0.13

- **`_compile_for_chip_backed_dummy` early-return bug fixed.** Pre-0.0.13,
  if the active qubits were all inside `available_qubits` the compile
  pass returned the source IR verbatim — so a Bell circuit reached the
  density-matrix simulator as raw `H + CNOT` and crashed with
  `TopologyError("Unsupported topology")`. The early-return is gone;
  every circuit now actually transpiles to native gates.
- **No `[qiskit]` extra needed.** The chip-backed compile uses qiskit,
  which is now a **core dependency** in uniqc 0.0.13 (the `[qiskit]`
  extra has been removed). A plain `pip install unified-quantum` is
  enough.
- **`available_qubits` is honored.** Pre-0.0.11.post1, the qiskit layout
  pass could re-map the user's hand-picked safe qubits onto excluded
  ones (e.g. q[58]/q[68] silently moved onto broken q[13]/q[21]). Fixed
  in 0.0.11.post1; preserved in 0.0.13.

## When to prefer chip-backed dummy over hand-built `ErrorLoader_*`

| Scenario                                                  | Recommended path                                 |
| --------------------------------------------------------- | ------------------------------------------------ |
| Reproduce *this specific chip's* behavior                 | `dummy:<provider>:<chip>`                        |
| Sweep a hypothetical noise level (e.g. 0.1% → 5%)         | hand-built `ErrorLoader_*`                       |
| Distinguish AmplitudeDamping vs Depolarizing contributions | hand-built `ErrorLoader_*`                       |
| Compare two chips by submitting identical circuits         | both `dummy:provider:chipA` and `dummy:provider:chipB` |
| Validate readout EM mitigation algorithm                   | either, but chip-backed gives realistic biases  |

## Refreshing the cache that powers the noise model

If your chip-backed dummy results stop matching real-hardware results,
the cached chip characterization is probably stale:

```bash
uniqc backend update --platform originq        # 0.0.13 fix: actually refreshes for ibm/quark too
uniqc backend chip-display originq/WK_C180 --update
```

Then re-run your `dummy:originq:WK_C180` workflow.

## Inspecting the noise model

The exact channels are an implementation detail (driven by
`bi.qubits.qubit_info[*]`), but you can inspect what was applied via
the dummy's underlying simulator:

```python
from uniqc.backend_adapter import get_backend
from uniqc.simulator import NoisySimulator

# This API is internal-ish; treat it as exploratory rather than stable.
backend = get_backend("dummy:originq:WK_C180")
print(type(backend), getattr(backend, "noise_summary", None))
```

For most users, the right approach is the audit recipe in
`uniqc-platform-verify` — submit identical circuits to both
`originq:WK_C180` and `dummy:originq:WK_C180` and compare counts /
fidelities.

## Pitfalls

- **`dummy:originq:wk_c180` lowercase is accepted on the dummy path
  only.** On the **real** `originq:WK_C180` submit, lowercase raises
  `BackendNotFoundError`. Standardize on uppercase chip names in your
  source code.
- **Pre-flight policy applies here too.** uniqc 0.0.13's strict
  pre-flight in `xeb_workflow` will refuse to dispatch experiments
  against a chip-backed dummy if the cached metadata says the
  required CZ pair is uncalibrated. That's intentional — the
  dummy mirrors the chip's published constraints.
- **No quota; not free of cost.** `dummy:<provider>:<chip>` runs in
  density-matrix mode; cost grows as `4^n_qubits`. Stay ≤ 12 qubits
  for snappy iteration; ≤ 18 if you can wait.
