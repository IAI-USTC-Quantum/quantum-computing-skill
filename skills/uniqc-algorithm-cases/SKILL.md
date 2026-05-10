---
name: uniqc-algorithm-cases
description: "Use when the user wants to run a *named* canonical quantum algorithm in UnifiedQuantum: VQE (H2 / TFIM), QPE / phase estimation, Grover, QFT, Deutsch-Jozsa, GHZ / W / Dicke state preparation, classical shadow / state tomography, amplitude estimation, VQD, thermal state. Provides ready-to-run templates that you can adapt to the user's problem."
---

# Uniqc Algorithm Cases Skill

This skill is the **catalog** of canonical quantum-algorithm templates
shipped via `uniqc.algorithms.core.circuits` (and `*.workflows`). Each
algorithm has a one-line entry, a recommended template, and a pointer
to the relevant reference page.

For QAOA: see the dedicated `uniqc-qaoa` skill.
For QML: see `uniqc-quantum-ml`.

## Algorithm catalog

| Algorithm            | Top-level entry point                                       | Reference                                    |
| -------------------- | ----------------------------------------------------------- | -------------------------------------------- |
| Bell / GHZ / W       | `ghz_state`, `w_state`                                      | [refs/state-prep.md](references/state-prep.md) |
| Dicke state          | `dicke_state_circuit(k=...)`                                | [refs/state-prep.md](references/state-prep.md) |
| Cluster state        | `cluster_state(edges=...)`                                  | [refs/state-prep.md](references/state-prep.md) |
| Thermal state (toy)  | `thermal_state_circuit(beta=...)`                           | [refs/state-prep.md](references/state-prep.md) |
| QFT                  | `qft_circuit(qubits=..., swaps=True)`                       | [refs/qft-and-qpe.md](references/qft-and-qpe.md) |
| QPE                  | `uniqc.algorithms.core.circuits.qpe_circuit(n_precision, unitary)` | [refs/qft-and-qpe.md](references/qft-and-qpe.md) |
| Grover               | `grover_oracle(...)` + `grover_diffusion(...)`              | [refs/grover.md](references/grover.md)       |
| Amplitude estimation | `amplitude_estimation_circuit(oracle=..., eval_qubits=...)` | [refs/grover.md](references/grover.md)       |
| Deutsch-Jozsa        | `deutsch_jozsa_circuit(qubits=..., oracle=...)`             | [refs/deutsch-jozsa.md](references/deutsch-jozsa.md) |
| VQE (H2)             | `uniqc.algorithms.workflows.vqe_workflow.run_vqe_workflow(H, ...)` | [refs/vqe-and-vqd.md](references/vqe-and-vqd.md) |
| VQD                  | `vqd_ansatz`, `vqd_circuit`, `vqd_overlap_circuit`          | [refs/vqe-and-vqd.md](references/vqe-and-vqd.md) |
| State tomography     | `state_tomography(...)` (or `StateTomography` class)        | [refs/measurement-cases.md](references/measurement-cases.md) |
| Classical shadow     | `classical_shadow(...)`, `shadow_expectation(...)`          | [refs/measurement-cases.md](references/measurement-cases.md) |

## Common usage shape

```python
from uniqc import Circuit, ghz_state                  # any fragment

frag = ghz_state(qubits=[0, 1, 2])                    # returns a fresh Circuit
prog = Circuit(3)
prog.add_circuit(frag)
for q in range(3):
    prog.measure(q)

# Now any of:
#   uniqc simulate (CLI), Simulator (Python), submit_task to a backend.
```

> All of `ghz_state`, `w_state`, `qft_circuit`, `dicke_state_circuit`,
> `grover_oracle`, `grover_diffusion`, `deutsch_jozsa_circuit`,
> `amplitude_estimation_circuit`, `cluster_state`, `thermal_state_circuit`,
> `vqd_ansatz`, `qaoa_ansatz`, `uccsd_ansatz`, `hea` — return a **new
> `Circuit`**. The legacy in-place form `fn(circuit, ...)` still works
> but emits `DeprecationWarning`. New code should use the fragment form.

## Practical defaults

- For first run, target `dummy:local:simulator`. It costs nothing and
  reproduces exact statevector behaviour.
- For algorithms that depend on a chip's basis gate set (most variational
  loops on real hardware), compile against the target backend before
  submitting (`uniqc-cloud-submit` skill).
- Save circuits as `.originir` files so you can rerun the algorithm from
  any environment without re-importing the Python module.
- For sampling-based algorithms (Grover, AE, classical shadow), keep
  `shots ≥ 1024` to avoid noise drowning out the signal.

## Cheat sheet — VQE on a 2-qubit Hamiltonian

```python
from uniqc.algorithms.workflows.vqe_workflow import run_vqe_workflow

# H = X⊗X + Y⊗Y + Z⊗Z  (toy)
H = [("XX", 1.0), ("YY", 1.0), ("ZZ", 1.0)]
result = run_vqe_workflow(H, n_qubits=2, depth=3, method="COBYLA",
                          options={"maxiter": 200})
print("min energy:", result.energy)
print("params:", result.params)
print("history (last 5):", result.history[-5:])
```

`VQEResult(energy, params, history, n_iter, success, message)`.

## Cheat sheet — Grover for a marked bitstring

```python
from uniqc import Circuit, grover_oracle, grover_diffusion

n = 3
marked = 5             # the bitstring to amplify
oracle = grover_oracle(marked_state=marked, n_qubits=n)
diff   = grover_diffusion(n_qubits=n)

prog = Circuit(n)
for q in range(n):
    prog.h(q)
# Optimal Grover iteration count for N=2^n: round(π/4 * sqrt(N))
import math
iters = round(math.pi / 4 * math.sqrt(2 ** n))
for _ in range(iters):
    prog.add_circuit(oracle)
    prog.add_circuit(diff)
for q in range(n):
    prog.measure(q)
print(prog.originir)
```

## Cheat sheet — QPE for a known unitary

```python
from uniqc import Circuit
from uniqc.algorithms.core.circuits import qpe_circuit

# Build the unitary U = R_Z(2π * φ) on 1 qubit; eigenphase φ.
phi = 0.375
U = Circuit(1)
U.rz(0, 2 * 3.141592653589793 * phi)

# State prep: |1> is an eigenstate of R_Z(.) with phase = ±phi.
prep = Circuit(1); prep.x(0)

n_precision = 4
prog = qpe_circuit(n_precision=n_precision, unitary_circuit=U,
                   state_prep=prep, measure=True)
print(prog.originir)
# Decoded integer m from measured cbits gives φ ≈ m / 2^n_precision.
```

## Names to remember

- Most fragments are top-level: `from uniqc import qft_circuit, ghz_state, ...`
  except `qpe_circuit`, which is `from uniqc.algorithms.core.circuits import qpe_circuit`.
- Workflow runners: `uniqc.algorithms.workflows.vqe_workflow.run_vqe_workflow`,
  `qaoa_workflow.run_qaoa_workflow`,
  `classical_shadow_workflow.run_classical_shadow_workflow`,
  `xeb_workflow.run_*_workflow`,
  `readout_em_workflow.run_readout_em_workflow`.
- Measurement helpers: `uniqc.algorithms.core.measurement.{pauli_expectation,
  classical_shadow, shadow_expectation, state_tomography, tomography_summary}`.

## Response style

- For each algorithm, cite the entry point first, then show
  state-prep + algorithm + measurement in 5–15 lines.
- Always include the local validation step (`Simulator` or
  `dummy`) before mentioning hardware.
- Never re-derive the algorithm theory inline; link to the existing
  upstream `examples/2_advanced/algorithms/<name>.md` notes if the user
  asks why.
