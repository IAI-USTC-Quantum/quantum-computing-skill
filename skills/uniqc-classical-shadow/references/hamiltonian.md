# Estimating ⟨H⟩ for a Hamiltonian via shadow

A Hamiltonian is a sum `H = Σ c_i P_i` of weighted Pauli strings.
Classical shadow lets you estimate ⟨H⟩ from a single snapshot
dataset.

## Recipe

```python
from uniqc import Circuit
from uniqc.algorithms.workflows import classical_shadow_workflow as csw

# H = -1.05 II + 0.40 ZI - 0.40 IZ - 0.01 ZZ + 0.18 XX  (toy reduced H2)
hamiltonian = [
    (-1.0524, "II"),
    ( 0.3979, "ZI"),
    (-0.3979, "IZ"),
    (-0.0113, "ZZ"),
    ( 0.1810, "XX"),
]

# Build the trial state (UCCSD-like ansatz placeholder — your real ansatz here)
def trial(theta):
    c = Circuit(2)
    c.ry(0, theta); c.cx(0, 1); c.measure(0); c.measure(1)
    return c

c = trial(theta=0.30)

# 1) Run shadow once for ALL non-identity strings present in H
non_identity = [p for _, p in hamiltonian if any(ch != "I" for ch in p)]
result = csw.run_classical_shadow_workflow(
    c, pauli_observables=list(set(non_identity)), shots=4000
)

# 2) Sum up ⟨H⟩ = c_I + Σ c_i ⟨P_i⟩
energy = 0.0
for coeff, pauli in hamiltonian:
    if all(ch == "I" for ch in pauli):
        energy += coeff                         # ⟨I...I⟩ = 1
    else:
        energy += coeff * result.expectations[pauli]

print(f"<H> = {energy:.4f}  (from {result.n_snapshots} snapshots)")
```

## When to choose shadow over per-term `pauli_expectation`

| Setup                                        | Cheaper path                               |
| -------------------------------------------- | ------------------------------------------ |
| Few Pauli terms (≤ 5), need exact values     | `pauli_expectation` per term (deterministic basis rotations, lower variance per shot) |
| Many Pauli terms (≥ 10), VQE-style sweep     | One `classical_shadow` dataset + many `shadow_expectation` calls |
| Multiple Hamiltonians on the same trial state | One shadow dataset, multiple sums          |
| Trotter sweep over time slices               | Shadow per slice — re-using snapshots across slices is incorrect |

## Variance scaling

`Var[⟨P⟩_shadow] ≤ 3^k / N` for a Pauli of weight `k` (single-qubit
Clifford-randomized shadows). For a Hamiltonian
`H = Σ c_i P_i`, by Cauchy-Schwarz:

```
Var[⟨H⟩] ≤ ( Σ |c_i| · 3^(k_i/2) )^2 / N
```

Practical implication: estimating a Hamiltonian with high-weight
terms (e.g. depth-`n` Jordan-Wigner string) at fixed precision
requires `N ∝ 3^k`. For molecular systems, the locality structure
often keeps the worst weight modest (≤ `n/2`).

## Variational integration

Plug `energy(theta)` into any classical optimizer (SciPy / PyTorch).
Re-collect snapshots **per parameter point** (snapshot-reuse across
parameter values is biased because the underlying state changes).

```python
from scipy.optimize import minimize

def energy_at(theta_vec):
    c = trial(theta=float(theta_vec[0]))
    res = csw.run_classical_shadow_workflow(
        c, pauli_observables=list(set(p for _, p in hamiltonian
                                       if any(ch != "I" for ch in p))),
        shots=4000,
    )
    return sum(coeff if all(ch == "I" for ch in p) else coeff * res.expectations[p]
               for coeff, p in hamiltonian)

opt = minimize(energy_at, x0=[0.30], method="COBYLA",
               options={"maxiter": 30, "rhobeg": 0.1})
print(opt.x, opt.fun)
```

For real-hardware optimization, batch the random-basis circuits per
parameter point via `ClassicalShadow.get_readout_circuits()` +
`submit_batch(...)` to keep queueing cost linear in iterations.
