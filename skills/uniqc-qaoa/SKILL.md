---
name: uniqc-qaoa
description: "Use when the user wants to design, run, or extend a QAOA (Quantum Approximate Optimization Algorithm) workflow with UnifiedQuantum. Covers the high-level `qaoa_workflow.run_qaoa_workflow`, hand-rolled `qaoa_ansatz` + `pauli_expectation` + SciPy loops, MaxCut Hamiltonian construction, parameter initialization, and bridging the result to real hardware."
---

# Uniqc QAOA Skill

QAOA is the canonical near-term variational solver for combinatorial
problems (MaxCut, Max-3SAT, portfolio optimisation). UnifiedQuantum gives
you three layers of abstraction; pick the lowest one that meets your
need.

## Three abstraction levels

| Level | What you write                                          | Use when                                                    |
| ----- | ------------------------------------------------------- | ----------------------------------------------------------- |
| 1     | `qaoa_workflow.run_qaoa_workflow(cost_h, p=...)`        | You have a Hamiltonian and want energy/parameters back.     |
| 2     | `qaoa_ansatz(...)` + `pauli_expectation(...)` + SciPy   | You want to override the loss, optimiser, or simulator.     |
| 3     | Hand-build cost / mixer layers + statevector simulation | Algorithmic research; you need access to amplitudes.        |

## First decision

| User goal                                                          | Read first                                              |
| ------------------------------------------------------------------ | ------------------------------------------------------- |
| "Just give me MaxCut energy on a small graph"                      | [references/quickstart.md](references/quickstart.md)    |
| "I have a Hamiltonian, run QAOA at p=2"                            | [references/quickstart.md](references/quickstart.md)    |
| "Hand-roll the loop, my own optimiser / measurement strategy"      | [references/handrolled.md](references/handrolled.md)    |
| "Run QAOA on real hardware (compile + submit + sample)"            | [references/hardware.md](references/hardware.md)        |
| "Add PyTorch autograd / hybrid training"                           | See `uniqc-quantum-ml` skill                            |

## Mental model

QAOA prepares
`|ψ(γ, β)⟩ = U_M(β_p) U_C(γ_p) … U_M(β_1) U_C(γ_1) |+⟩^{⊗n}` and minimises
`⟨ψ|H_C|ψ⟩` over `(γ, β) ∈ ℝ^{2p}`. uniqc parameterises:

- `cost_hamiltonian: list[(pauli_string, coefficient)]` — Pauli-string
  form (e.g. `"Z0Z1"` for the indexed form, or `"ZZ"` for the compact form
  on 2 qubits).
- `p` — number of QAOA layers.
- `betas`, `gammas` — both length `p` (kwarg names: `betas=`, `gammas=`).

`qaoa_ansatz(cost_h, p=p, betas=betas, gammas=gammas)` returns a fresh
`Circuit`. Add measurements yourself before sampling.

## Practical defaults

- Start with `p=1` to see whether the optimiser converges; jump to `p=2`
  for tighter bounds. `p=3+` only if you can sustain the deeper compiled
  circuit.
- Initial parameters: random in `[0, π]` for both betas and gammas, with
  a fixed seed for reproducibility. The high-level workflow does this if
  you omit `init_betas` / `init_gammas`.
- Optimiser: COBYLA (default) is robust on noiseless statevector. For
  shot-noise loops use SPSA or Nelder-Mead with a higher `maxiter`.
- Always validate the loss on the simulator before submitting any QAOA
  iterate to real hardware — one wrong sign in the cost Hamiltonian and
  you maximise a quantity you intended to minimise.
- `pauli_expectation(circuit, "Z0Z1")` is statevector by default; pass
  `shots=N` to sample.

> ⚠️ **Pauli-string form gotcha** (verified against uniqc 0.0.13.dev0):
> `run_qaoa_workflow(cost_h, n_qubits=N, ...)` requires the **compact**
> form (every term has length `N`, e.g. `"ZZI"` / `"IZZ"` / `"ZIZ"` for
> a 3-qubit triangle). `qaoa_ansatz(cost_h, ...)` requires the **indexed**
> form (e.g. `"Z0Z1"`). They are *not* interchangeable. If you mix them
> you get either `ValueError: All Pauli terms must have length N` or
> `invalid literal for int() with base 10: ''`. Build both forms when
> you intend to (a) optimise via the workflow, then (b) re-build the
> ansatz manually for sampling.

## Cheat sheet — high-level

```python
from uniqc.algorithms.workflows.qaoa_workflow import run_qaoa_workflow

# Compact form (length = n_qubits) — required by run_qaoa_workflow
cost_h = [("ZZI", 1.0), ("IZZ", 1.0), ("ZIZ", 1.0)]   # triangle MaxCut on 3 qubits
result = run_qaoa_workflow(cost_h, n_qubits=3, p=2, method="COBYLA")
print("energy", result.energy)
print("γ", result.gammas, "β", result.betas)
print("converged?", result.success, result.message)
```

`QAOAResult` fields: `energy`, `gammas`, `betas`, `history`, `n_iter`,
`success`, `message`.

## Cheat sheet — hand-rolled (statevector)

```python
import numpy as np
from scipy.optimize import minimize
from uniqc import qaoa_ansatz
from uniqc.algorithms.core.measurement import pauli_expectation

# Indexed form — required by qaoa_ansatz
cost_h = [("Z0Z1", 1.0), ("Z1Z2", 1.0), ("Z0Z2", 1.0)]
p = 2
n_qubits = 3

def objective(x):
    gammas, betas = x[:p], x[p:]
    circuit = qaoa_ansatz(cost_h, p=p, betas=betas, gammas=gammas)
    return sum(c * pauli_expectation(circuit, ps) for ps, c in cost_h)

x0 = np.random.default_rng(7).uniform(0, np.pi, size=2 * p)
out = minimize(objective, x0, method="COBYLA", options={"maxiter": 200})
print("min energy", out.fun)
```

## Names to remember

- High-level: `uniqc.algorithms.workflows.qaoa_workflow.run_qaoa_workflow`
  (returns `QAOAResult`).
- Ansatz: `uniqc.qaoa_ansatz(cost_hamiltonian, p, qubits, betas, gammas)`.
- Measurement: `uniqc.algorithms.core.measurement.pauli_expectation` (or
  the class form `PauliExpectation`).
- Result type: `QAOAResult(energy, gammas, betas, history, n_iter, success, message)`.

## Response style

- Always show the cost Hamiltonian construction with explicit
  `(pauli_string, coeff)` tuples; the user often gets the sign or the
  form wrong.
- Print intermediate energy at the end of each optimiser iteration, not
  just the final value.
- For real-hardware QAOA, recommend statevector validation first and
  only submit the final iterate (or a small batch around it).
