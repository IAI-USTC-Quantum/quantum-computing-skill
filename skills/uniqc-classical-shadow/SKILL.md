---
name: uniqc-classical-shadow
description: "Use when the user wants sample-efficient many-observable estimation in UnifiedQuantum (uniqc ≥ 0.0.13) via classical shadow tomography: collect random-Pauli snapshots with `classical_shadow(circuit, shots=...)`, estimate ⟨P⟩ for many Pauli strings from the same dataset using `shadow_expectation`, drive the workflow via `run_classical_shadow_workflow(circuit, pauli_observables, shots=...)` (returns `ShadowWorkflowResult` with snapshots + per-observable estimates), or use the `ClassicalShadow` class API. Compares to `state_tomography` (full state, much more expensive). Pauli string length must equal the circuit's qubit count."
---

# Uniqc Classical Shadow Skill

Classical shadow tomography is the right tool when the user wants
**many** observable expectations from a **single** experimental
dataset, without paying for full-state tomography. uniqc ships
classical shadow under `uniqc.algorithms.core.measurement`
(functions + `ClassicalShadow` class) plus a workflow driver in
`uniqc.algorithms.workflows.classical_shadow_workflow`.

## Decision tree

| User goal                                                        | Read first                                              |
| ---------------------------------------------------------------- | ------------------------------------------------------- |
| "Estimate ⟨P⟩ for one Pauli string"                              | [references/api.md](references/api.md) (`shadow_expectation`) |
| "Estimate many ⟨P⟩ values from one dataset"                      | [references/api.md](references/api.md) (`run_classical_shadow_workflow`) |
| "I have a Hamiltonian — give me ⟨H⟩"                             | [references/hamiltonian.md](references/hamiltonian.md)  |
| "When should I use shadow vs full state tomography?"             | [references/vs-tomography.md](references/vs-tomography.md) |
| "What's the variance / how many shots do I need?"                | [references/sample-complexity.md](references/sample-complexity.md) |

## Mental model

```
                                      ┌────────────────────────────────┐
   Circuit (with measurements         │  classical_shadow(c, shots=N)  │
   on every qubit you'll observe)  ──►│                                │
                                      │  N independent random-Pauli    │
                                      │  bases sampled per shot;       │
                                      │  returns list[ShadowSnapshot]  │
                                      └───────────────┬────────────────┘
                                                      │
                          ┌───────────────────────────┴───────────────────────┐
                          │                                                   │
            shadow_expectation(snapshots, "ZIZ") ─► float ⟨ZIZ⟩
            shadow_expectation(snapshots, "XX")  ─► float ⟨XX⟩
                          (estimate as many Pauli strings as you like
                           from the SAME dataset)
```

For the workflow driver:

```
run_classical_shadow_workflow(c, ["ZZ", "XX", "YY"], shots=1000)
  → ShadowWorkflowResult(
       snapshots=[ShadowSnapshot, ...],
       expectations={"ZZ": float, "XX": float, "YY": float},
       n_snapshots=1000,
    )
```

## Cheat sheet

```python
from uniqc import Circuit
from uniqc.algorithms.core.measurement import classical_shadow, shadow_expectation
from uniqc.algorithms.workflows import classical_shadow_workflow as csw

# 1. Bell state circuit — measure every qubit you'll later observe.
c = Circuit(2); c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)

# 2. Workflow API — collect snapshots + estimate observables in one call.
result = csw.run_classical_shadow_workflow(c, ["ZZ", "XX", "YY", "ZI", "IZ"], shots=2000)
print(result.expectations)
# Bell state: ⟨ZZ⟩ = +1, ⟨XX⟩ = +1, ⟨YY⟩ = -1, ⟨ZI⟩ = ⟨IZ⟩ = 0

# 3. Lower-level: collect once, estimate many times.
snapshots = classical_shadow(c, shots=2000)              # list[ShadowSnapshot]
print("ZZ:", shadow_expectation(snapshots, "ZZ"))
print("XX:", shadow_expectation(snapshots, "XX"))
# Add any Pauli string later from the same `snapshots` list — no re-run.
```

## Practical defaults

- **Pauli string length must equal `n_qubit`.** `"ZZ"` on a 3-qubit
  circuit is a `ValueError`. Use indexed form via the workflow only
  if every observable has the same width as the circuit (the shadow
  estimator needs full-width strings; pad with `I`).
- **Measure every qubit** that appears (non-`I`) in any observable
  you intend to estimate. Missing measurements → `pauli_expectation`-
  style errors at estimation time.
- **`shots` doubles as `n_snapshots`** for the workflow driver — each
  shot draws an independent random Pauli basis. Pass
  `n_shadow=...` when you want decoupled control.
- **Variance ~ 4^(weight) / shots** for a single Pauli string of
  weight `k`. For a sum of `M` strings (e.g. a Hamiltonian), variance
  scales with the largest individual term times `M^2` in the worst
  case. Use `shadow_norm` heuristics if accuracy matters.
- **Shadow vs state tomography**: use shadow if `# observables ≫ 1`
  or `n_qubit ≥ 6`. Full state tomography needs `~ 4^n_qubit`
  experiments and is impractical past ~6 qubits; shadow stays
  poly(`n_qubit`) per Pauli observable of bounded weight.
- **Run on `dummy:local:simulator` first** to validate Pauli-string
  formatting (lengths, position-vs-index conventions) before spending
  shots on cloud hardware.
- **Hardware execution**: `classical_shadow` internally executes
  `shots` distinct random-basis circuits — that's `shots` separate
  cloud submissions unless you batch. For real hardware, use
  `submit_batch` of the random-basis circuits explicitly (see
  `references/api.md`).

## Names to remember

- `uniqc.classical_shadow(circuit, shots=..., n_shadow=..., qubits=...)`
  → `list[ShadowSnapshot]`. (Re-exported from top-level `uniqc`.)
- `uniqc.shadow_expectation(snapshots, pauli_string)` → `float`.
  Pauli string is **compact** (`"ZIZ"`, length = `n_qubit`).
- `uniqc.algorithms.core.measurement.ClassicalShadow` — class API
  with `.get_readout_circuits()` + `.execute(backend)`.
- `uniqc.algorithms.workflows.classical_shadow_workflow.run_classical_shadow_workflow(circuit, pauli_observables, shots=, n_shadow=, qubits=)`
  → `ShadowWorkflowResult(snapshots, expectations, n_snapshots)`.
- Comparison: `uniqc.state_tomography`, `uniqc.tomography_summary`,
  `uniqc.pauli_expectation` (one Pauli at a time, deterministic basis
  rotation; cheaper than shadow if you only need one observable).

## Response style

- Lead with the **workflow driver** (`run_classical_shadow_workflow`)
  for any "estimate these N observables" request — it returns
  snapshots **and** expectations and is the lowest-friction path.
- For algorithmic users (e.g. variational chemists computing ⟨H⟩),
  show how to feed a Hamiltonian (list of `(pauli_str, coeff)`) into
  shadow estimation — see `hamiltonian.md`.
- Always print `n_snapshots` along with the estimates so the user
  sees the sample size baked into the variance.
- For "should I use shadow?" questions, ask first whether the
  observable count is 1 (use `pauli_expectation`), small handful
  (`pauli_expectation` per term), or many (`shadow`).
