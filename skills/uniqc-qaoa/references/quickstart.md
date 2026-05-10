# QAOA quickstart

The fastest path from "I have a problem" to "I have an answer" is
`uniqc.algorithms.workflows.qaoa_workflow.run_qaoa_workflow`.

> ⚠️ Pauli-string form (verified against uniqc 0.0.13.dev0):
> `run_qaoa_workflow` requires the **compact** form (length = `n_qubits`).
> `qaoa_ansatz` requires the **indexed** form. Mixing the two raises
> `ValueError: All Pauli terms must have length N` or
> `invalid literal for int() with base 10: ''`. The examples below build
> the compact form for the workflow and the indexed form for ansatz
> sampling.

## End-to-end (3 nodes triangle MaxCut)

```python
from uniqc.algorithms.workflows.qaoa_workflow import run_qaoa_workflow

# Compact form for the workflow (every term has length n_qubits)
cost_hamiltonian_compact = [
    ("ZZI", 1.0),    # edge (0, 1)  -> Z on qubits 0 and 1, I on qubit 2
    ("IZZ", 1.0),    # edge (1, 2)
    ("ZIZ", 1.0),    # edge (0, 2)
]

result = run_qaoa_workflow(
    cost_hamiltonian_compact,
    n_qubits=3,
    p=2,
    method="COBYLA",
    options={"maxiter": 200},
    shots=None,        # statevector exact when None
)

print("energy:", result.energy)
print("γ:", result.gammas)
print("β:", result.betas)
print("history:", result.history[-5:])
print("converged?", result.success, result.message, result.n_iter)
```

`QAOAResult` is a dataclass with: `energy`, `gammas`, `betas`,
`history` (per-iteration energy), `n_iter`, `success`, `message`.

## Build a MaxCut Hamiltonian from an edge list

```python
def maxcut_hamiltonian_compact(edges, n_qubits, sign=+1.0):
    """Standard MaxCut: H = Σ Z_i Z_j (compact form, length = n_qubits)."""
    terms = []
    for i, j in edges:
        ops = ["I"] * n_qubits
        ops[i] = "Z"
        ops[j] = "Z"
        terms.append(("".join(ops), sign))
    return terms

def maxcut_hamiltonian_indexed(edges, sign=+1.0):
    """Same Hamiltonian in indexed form, for qaoa_ansatz."""
    return [(f"Z{i}Z{j}", sign) for i, j in edges]

square = [(0, 1), (1, 2), (2, 3), (3, 0)]
cost_compact = maxcut_hamiltonian_compact(square, n_qubits=4)
cost_indexed = maxcut_hamiltonian_indexed(square)

result = run_qaoa_workflow(cost_compact, n_qubits=4, p=2)
```

The constant offset (`-len(edges) / 2` in standard MaxCut) does not
change the optimiser path; add it back only when you want the
wall-clock cut count.

## Custom initial parameters

```python
import numpy as np
init_gammas = np.array([0.1, 0.2])
init_betas  = np.array([0.5, 0.7])

result = run_qaoa_workflow(
    cost_compact, n_qubits=4, p=2,
    init_gammas=init_gammas, init_betas=init_betas,
)
```

If you omit them, `run_qaoa_workflow` draws from `Uniform(0, π)` with
NumPy's default RNG. For reproducibility, set the seed at the call site:

```python
np.random.seed(42)
result = run_qaoa_workflow(cost_compact, n_qubits=4, p=2)
```

## Switching the optimiser

```python
result = run_qaoa_workflow(
    cost_compact, n_qubits=4, p=2,
    method="Nelder-Mead",
    options={"maxiter": 500, "xatol": 1e-4},
)
```

Any `scipy.optimize.minimize` method string is accepted. For shot-noise
loops where COBYLA gets stuck:

- "Nelder-Mead" — good when `f` is noisy and dim ≤ 6.
- "Powell" — derivative-free, no hyperparameters.
- "SLSQP" — only useful with smooth statevector loss + bounds.

## Sampling-based loss (`shots=...`)

```python
result = run_qaoa_workflow(cost_compact, n_qubits=4, p=2, shots=4096)
```

This routes `pauli_expectation` to the dummy simulator with finite
shots. Energy will be noisy; expect more iterations to converge.

## Decoding the bitstring

```python
import numpy as np
from uniqc import qaoa_ansatz
from uniqc.simulator import Simulator

# Use the indexed form here — qaoa_ansatz requires it.
circuit = qaoa_ansatz(cost_indexed, p=2, gammas=result.gammas, betas=result.betas)
for q in range(4):
    circuit.measure(q)

sim = Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(circuit.originir)

n = 4
top = sorted(
    ((format(i, f"0{n}b"), float(p)) for i, p in enumerate(probs) if p > 1e-3),
    key=lambda kv: kv[1], reverse=True,
)
for bits, p in top[:8]:
    cut = sum(1 for i, j in square if bits[-1 - i] != bits[-1 - j])
    print(f"  {bits}  prob={p:.4f}  cut={cut}")
```

This is the moment to tell the user: a high-probability bitstring with
maximum cut is the QAOA answer; the energy alone is just the proxy.

## Common mistakes

- **Pauli form mismatch** — see the warning at the top. Compact form for
  `run_qaoa_workflow`, indexed form for `qaoa_ansatz`. Build both.
- Sign confusion: optimisers minimise; if your `H_C` should be
  *maximised*, multiply coefficients by `-1` before passing in, or
  return `-energy` from the user-supplied objective when hand-rolling.
- `betas` / `gammas` length mismatch — both must equal `p`.
- Forgetting `n_qubits` — the workflow defaults to inferring from the
  Pauli strings, but compact form pins width unambiguously.
