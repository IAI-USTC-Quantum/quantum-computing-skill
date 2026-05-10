# VQE and VQD

## VQE — `run_vqe_workflow`

```python
from uniqc.algorithms.workflows.vqe_workflow import run_vqe_workflow

# Toy 2-qubit Hamiltonian H = X⊗X + Y⊗Y + Z⊗Z
H = [("XX", 1.0), ("YY", 1.0), ("ZZ", 1.0)]
result = run_vqe_workflow(
    H,
    n_qubits=2,
    depth=3,                       # HEA depth
    method="COBYLA",
    options={"maxiter": 200},
    shots=None,                    # statevector
)
print("E_min:", result.energy)
print("params:", result.params)
print("history (last 5):", result.history[-5:])
print("converged?", result.success, "n_iter:", result.n_iter)
```

`VQEResult(energy, params, history, n_iter, success, message)`.

### Hand-rolled VQE (custom ansatz)

```python
import numpy as np
from scipy.optimize import minimize
from uniqc import hea
from uniqc.algorithms.core.measurement import pauli_expectation


def hamiltonian_expectation(circuit, terms, *, shots=None):
    return sum(c * pauli_expectation(circuit, ps, shots=shots) for ps, c in terms)


def run(H, n_qubits, depth, *, shots=None, seed=0):
    rng = np.random.default_rng(seed)
    n_params = 2 * n_qubits * depth
    x0 = rng.uniform(0, np.pi, size=n_params)

    def obj(params):
        circuit = hea(n_qubits=n_qubits, depth=depth, params=params)
        return hamiltonian_expectation(circuit, H, shots=shots)

    out = minimize(obj, x0, method="COBYLA", options={"maxiter": 200})
    return out
```

`hea` is the hardware-efficient ansatz — width × depth × 2 parameters.
Substitute with `uccsd_ansatz` for chemistry, or your own circuit
factory for problem-specific structure.

### H2 molecular VQE

For a worked H2 example using JW-mapped Hamiltonian + UCCSD ansatz, see
the [H2 reference in `uniqc-basic-usage`](../../uniqc-basic-usage/references/h2-molecular-simulation.md)
— it covers the chemistry pipeline (qiskit-nature → uniqc Pauli list).

## VQD — Variational Quantum Deflation

VQD finds the lowest-energy state, then progressively deflates against
it to find the next eigenstate. The building blocks:

```python
from uniqc import vqd_ansatz, vqd_circuit, vqd_overlap_circuit
```

### Find the ground state, then the first excited

```python
import numpy as np
from scipy.optimize import minimize
from uniqc import vqd_ansatz
from uniqc.algorithms.core.measurement import pauli_expectation
from uniqc.simulator import Simulator

H = [("XX", 1.0), ("YY", 1.0), ("ZZ", 1.0)]
n_qubits = 2

sim = Simulator(backend_type="statevector")

def state_for(params, prev_states):
    circuit = vqd_ansatz(n_qubits=n_qubits, ansatz_params=list(params),
                          prev_states=prev_states, n_layers=2, penalty=10.0)
    sv = np.asarray(sim.simulate_statevector(circuit.originir), dtype=complex)
    return sv

def vqd_step(prev_states):
    rng = np.random.default_rng(0)
    x0 = rng.uniform(0, np.pi, size=n_qubits * 2 * 2)

    def obj(params):
        circuit = vqd_ansatz(n_qubits=n_qubits, ansatz_params=list(params),
                              prev_states=prev_states, n_layers=2, penalty=10.0)
        return sum(c * pauli_expectation(circuit, ps) for ps, c in H)

    out = minimize(obj, x0, method="COBYLA", options={"maxiter": 300})
    return out.fun, state_for(out.x, prev_states)

prev = []
energies = []
for k in range(3):
    e, sv = vqd_step(prev)
    energies.append(e)
    prev.append(sv)
    print(f"E_{k} ≈ {e:.6f}")
```

### Notes

- `penalty` controls how strongly previous-state overlap is suppressed;
  too small → contamination, too large → optimiser instability. 10–50
  is a common range.
- `prev_states` is a list of normalised statevectors (NumPy arrays); the
  ansatz appends overlap-suppression terms during evaluation.
- `vqd_overlap_circuit` is the building block that prepares the swap-test
  / overlap measurement when you want a hardware-friendly evaluator
  instead of statevector.

## Practical defaults

- Validate the Hamiltonian on a known eigenstate first (e.g. exact
  diagonalisation for small `n_qubits`); a wrong sign or a missed term
  is the most common bug.
- Start with `depth=2` for HEA; bump to 3–4 if loss plateaus high.
- COBYLA is robust for noiseless statevector. For shot-based loops,
  switch to `method="Nelder-Mead"` with `xatol=1e-3` and a higher
  `maxiter`.

## Common mistakes

- Passing `H` with `(coeff, pauli)` order — uniqc expects
  `(pauli, coeff)`. Check the first element of every term.
- Mixing compact (`"XX"`) and indexed (`"X0X1"`) forms — pick one.
- Forgetting that `pauli_expectation` measures observables; you do not
  need to add measurements to the circuit yourself.
