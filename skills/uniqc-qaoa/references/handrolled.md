# Hand-rolled QAOA (your own loop)

Use this when you want to swap in a custom optimiser, a different
measurement strategy (sampling vs. statevector), batched parameter
sweeps, or visualization of the optimization landscape.

## Skeleton

```python
import numpy as np
from scipy.optimize import minimize
from uniqc import qaoa_ansatz
from uniqc.algorithms.core.measurement import pauli_expectation


def run(cost_hamiltonian, p, n_qubits, *, shots=None, seed=0, maxiter=200):
    rng = np.random.default_rng(seed)

    def objective(x):
        gammas = x[:p]
        betas  = x[p:]
        circuit = qaoa_ansatz(cost_hamiltonian, p=p, betas=betas, gammas=gammas)
        return sum(coeff * pauli_expectation(circuit, ps, shots=shots)
                   for ps, coeff in cost_hamiltonian)

    x0 = rng.uniform(0, np.pi, size=2 * p)
    history: list[float] = []

    def callback(xk):
        history.append(objective(xk))

    out = minimize(objective, x0, method="COBYLA",
                   options={"maxiter": maxiter}, callback=callback)
    return out, history
```

## Statevector loss (exact)

`pauli_expectation(circuit, ps)` with `shots=None` uses the OriginIR
statevector simulator and returns the exact expectation. This is the
right default during *development* — converged energy is a faithful
indicator of whether your Hamiltonian is correct.

## Sample-based loss (noisy)

```python
val = pauli_expectation(circuit, "Z0Z1", shots=4096)
```

Each call samples `shots` times; standard error is
`sqrt((1 - val^2) / shots)`. For 1% precision near zero you need ~10000
shots — adjust your optimiser's tolerance.

## Manual MaxCut decoding

```python
import numpy as np
from uniqc import qaoa_ansatz
from uniqc.simulator import Simulator

circuit = qaoa_ansatz(cost_h, p=p, gammas=best_gammas, betas=best_betas)
for q in range(n_qubits):
    circuit.measure(q)

sim = Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(circuit.originir)

def cut_value(bits, edges):
    return sum(1 for i, j in edges if bits[-1 - i] != bits[-1 - j])

ranked = sorted(
    ((format(i, f"0{n_qubits}b"), float(p)) for i, p in enumerate(probs) if p > 1e-4),
    key=lambda kv: kv[1], reverse=True,
)
for bits, prob in ranked[:5]:
    print(f"{bits}  prob={prob:.4f}  cut={cut_value(bits, edges)}")
```

## Custom optimiser (SPSA for shot-noise)

`scipy.optimize` does not include SPSA; pin a small implementation:

```python
def spsa(objective, x0, *, n_iter=100, a=0.2, c=0.1, alpha=0.602, gamma=0.101, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x0, dtype=float).copy()
    history = []
    for k in range(1, n_iter + 1):
        ak = a / (k ** alpha)
        ck = c / (k ** gamma)
        delta = rng.choice([-1.0, +1.0], size=x.shape)
        f_plus  = objective(x + ck * delta)
        f_minus = objective(x - ck * delta)
        g = (f_plus - f_minus) / (2.0 * ck * delta)
        x = x - ak * g
        history.append(objective(x))
    return x, history
```

Use SPSA when shots are expensive — each step costs only 2 function
evaluations regardless of dimension.

## Coordinate descent (no gradient)

```python
def coordinate_descent(objective, x0, *, step=0.2, max_outer=30):
    x = np.asarray(x0, dtype=float).copy()
    history = [objective(x)]
    for _ in range(max_outer):
        improved = False
        for i in range(len(x)):
            best = history[-1]
            for d in (+step, -step):
                trial = x.copy(); trial[i] += d
                v = objective(trial)
                if v < best:
                    best = v; x = trial; improved = True
            history.append(best)
        if not improved:
            step *= 0.5
            if step < 1e-6:
                break
    return x, history
```

Robust on flat statevector landscapes, slow but always makes progress.

## Plotting the optimization curve

```python
import matplotlib.pyplot as plt
plt.plot(history)
plt.xlabel("iteration")
plt.ylabel("⟨H_C⟩")
plt.title(f"QAOA p={p} convergence")
plt.tight_layout()
plt.savefig("qaoa_curve.png", dpi=160)
```

## Speed tips

- Cache `qaoa_ansatz` only when `p` and `cost_hamiltonian` do not change
  (parameters do, so the ansatz needs to rebuild every iteration).
- For `n_qubits ≤ 18`, statevector is faster than any sampling.
- For `n_qubits ≥ 20`, switch to MPS via `Simulator(backend_type="mps")`
  if your circuit is shallow and chain-like; otherwise ship to a real
  backend or a cloud simulator.
