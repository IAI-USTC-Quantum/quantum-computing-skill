# Variational Algorithms Reference

Complete reference for variational quantum algorithms in QPanda-lite.

## Available Ansatzes

### HEA - Hardware-Efficient Ansatz

Hardware-efficient parameterized circuit suitable for NISQ devices.

```python
from qpandalite.algorithmics.ansatz import hea

circuit = hea(
    n_qubits=4,       # Number of qubits
    depth=2,           # Number of repeated layers (default: 1)
    qubits=None,       # Qubit indices (default: list(range(n_qubits)))
    params=None        # Rotation angles (default: random initialization)
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_qubits` | `int` | required | Number of qubits |
| `depth` | `int` | 1 | Number of repeated layers |
| `qubits` | `list[int]` | `None` | Qubit indices (default: `list(range(n_qubits))`) |
| `params` | `np.ndarray` | `None` | 1-D array of rotation angles |

**Total parameters**: `2 * n_qubits * depth`

#### Circuit Structure

Each layer consists of:

1. **Single-qubit rotations** on every qubit:
   - `Rz(q_i, θ_{2i})`
   - `Ry(q_i, θ_{2i+1})`

2. **Entangling layer** (ring topology):
   - `CNOT(q_i, q_{(i+1) % n})` for i = 0, 1, ..., n-1

#### Example

```python
import numpy as np
from qpandalite.algorithmics.ansatz import hea

# Create 4-qubit HEA with 2 layers (16 parameters)
circuit = hea(n_qubits=4, depth=2)

# With specific parameters
params = np.zeros(16)  # 2 * 4 * 2 = 16
circuit = hea(n_qubits=4, depth=2, params=params)

# Random initialization (default)
circuit = hea(n_qubits=4, depth=3)
# Total params: 2 * 4 * 3 = 24
```

### UCCSD - Unitary Coupled-Cluster Singles and Doubles

Chemistry-native ansatz for molecular simulation.

```python
from qpandalite.algorithmics.ansatz import uccsd_ansatz

circuit = uccsd_ansatz(
    n_qubits=4,       # Number of qubits
    n_electrons=2      # Number of electrons
)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `n_qubits` | `int` | Number of qubits (spin orbitals) |
| `n_electrons` | `int` | Number of electrons |

Use for: molecular ground state search, chemistry VQE.

### QAOA - Quantum Approximate Optimization Algorithm

Ansatz for combinatorial optimization problems.

```python
from qpandalite.algorithmics.ansatz import qaoa_ansatz

circuit = qaoa_ansatz(
    cost_terms,        # Cost Hamiltonian terms
    p=2                # Number of QAOA layers (depth)
)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cost_terms` | `list[tuple[str, float]]` | Pauli string and coefficient pairs |
| `p` | `int` | Number of QAOA layers |

#### Cost Hamiltonian Format

```python
# MaxCut on triangle graph
cost_terms = [
    ("Z0Z1", 0.5),
    ("Z1Z2", 0.5),
    ("Z0Z2", 0.5),
]
```

## Optimization Patterns

### Gradient-Free Optimization (COBYLA/Nelder-Mead)

```python
import numpy as np
from scipy.optimize import minimize
from qpandalite.algorithmics.ansatz import hea
from qpandalite.simulator import OriginIR_Simulator

sim = OriginIR_Simulator(backend_type='statevector')

def objective(params):
    circuit = hea(n_qubits=4, depth=2, params=params)
    sv = sim.simulate_statevector(circuit.originir)
    # Compute energy or cost from statevector
    energy = compute_energy(sv, hamiltonian)
    return energy

n_params = 2 * 4 * 2  # 16 for 4-qubit depth-2 HEA
result = minimize(
    objective,
    x0=np.random.uniform(0, 2*np.pi, n_params),
    method='COBYLA',
    options={'maxiter': 200}
)
print(f"Optimal energy: {result.fun}")
print(f"Optimal params: {result.x}")
```

### Coordinate Descent Optimization

```python
def coordinate_descent(objective, n_params, max_iter=50):
    """Optimize one parameter at a time."""
    params = np.random.uniform(0, 2*np.pi, n_params)
    best_value = objective(params)

    for iteration in range(max_iter):
        improved = False
        for i in range(n_params):
            # Try shifting parameter i
            original = params[i]
            for delta in [0.1, -0.1, 0.5, -0.5]:
                params[i] = original + delta
                new_value = objective(params)
                if new_value < best_value:
                    best_value = new_value
                    improved = True
                    break
            else:
                params[i] = original

        if not improved:
            break

    return params, best_value
```

### Parameter-Shift Gradient

```python
from qpandalite.pytorch import compute_all_gradients

def gradient_based_optimization(circuit_template, expectation_fn, n_steps=100, lr=0.01):
    """Optimize using parameter-shift rule for gradients."""
    params = np.random.uniform(0, 2*np.pi, n_params)

    for step in range(n_steps):
        # Compute gradients via parameter-shift rule
        circuit = build_circuit(params)
        grads = compute_all_gradients(circuit, expectation_fn)

        # Gradient descent update
        for name, grad in grads.items():
            idx = param_name_to_index(name)
            params[idx] -= lr * grad

    return params
```

## VQE Workflow Pattern

```python
from qpandalite.algorithmics.ansatz import hea
from qpandalite.simulator import OriginIR_Simulator
from scipy.optimize import minimize

def vqe(hamiltonian, n_qubits, ansatz_depth=2, maxiter=200):
    """Variational Quantum Eigensolver workflow."""
    sim = OriginIR_Simulator(backend_type='statevector')
    n_params = 2 * n_qubits * ansatz_depth

    def objective(params):
        circuit = hea(n_qubits, depth=ansatz_depth, params=params)
        sv = sim.simulate_statevector(circuit.originir)
        energy = 0.0
        for pauli_str, coeff in hamiltonian:
            exp_val = compute_pauli_expectation(sv, pauli_str)
            energy += coeff * exp_val
        return energy

    result = minimize(
        objective,
        x0=np.random.uniform(0, 2*np.pi, n_params),
        method='COBYLA',
        options={'maxiter': maxiter}
    )
    return result.fun, result.x
```

## QAOA Workflow Pattern

```python
def qaoa_maxcut(edges, p=2, maxiter=100):
    """QAOA for MaxCut problem."""
    # Build cost Hamiltonian
    cost_terms = [(f"Z{i}Z{j}", 0.5) for i, j in edges]
    for i, j in edges:
        cost_terms.append((f"I", -0.5))  # Constant offset

    # Create QAOA circuit
    circuit = qaoa_ansatz(cost_terms, p=p)

    # Optimize
    sim = OriginIR_Simulator()
    # ... optimization loop ...
```

## Choosing an Ansatz

| Ansatz | Best For | Parameters | Hardware Friendly |
|--------|----------|------------|-------------------|
| HEA | General VQE, QML | `2*n_qubits*depth` | Yes |
| UCCSD | Molecular simulation | Varies with system | No (deep circuits) |
| QAOA | Combinatorial optimization | `2*p` | Moderate |

### HEA vs UCCSD for Chemistry

- **HEA**: Shallow circuits, hardware-efficient, more parameters needed, may converge to local minima
- **UCCSD**: Physics-informed, fewer parameters for chemistry, deep circuits, better accuracy for small molecules
