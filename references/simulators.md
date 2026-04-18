# Simulators Reference

Complete reference for QPanda-lite simulation backends.

## Simulator Classes

### OriginIR_Simulator

Primary simulator for circuits in OriginIR format.

```python
from qpandalite.simulator import OriginIR_Simulator

sim = OriginIR_Simulator(
    backend_type='statevector',
    available_qubits=None,
    available_topology=None,
    **extra_kwargs
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend_type` | `str` | `'statevector'` | `'statevector'` or `'densitymatrix'` |
| `available_qubits` | `list[int]` | `None` | Allowed qubit indices for topology validation |
| `available_topology` | `list[list[int]]` | `None` | Allowed two-qubit gate pairs, e.g., `[[0,1], [1,2]]` |

### QASM_Simulator

Simulator for circuits in OpenQASM 2.0 format.

```python
from qpandalite.simulator import QASM_Simulator

sim = QASM_Simulator(
    backend_type='statevector',
    available_qubits=None,
    available_topology=None
)
```

### Noisy Simulators

```python
from qpandalite.simulator import OriginIR_NoisySimulator, QASM_Noisy_Simulator

sim = OriginIR_NoisySimulator(
    backend_type='statevector',
    available_qubits=None,
    available_topology=None,
    error_loader=None,
    readout_error={}
)
```

#### Noise Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `error_loader` | `ErrorLoader` | Gate error model loader |
| `readout_error` | `dict[int, list[float]]` | Per-qubit readout error probabilities |

## Simulation Methods

### simulate_statevector

```python
statevector = sim.simulate_statevector(quantum_code)
# Returns: np.ndarray (2^n complex amplitudes)
```

Compute the full statevector of the quantum state after circuit execution.

### simulate_pmeasure

```python
probabilities = sim.simulate_pmeasure(quantum_code)
# Returns: np.ndarray (2^n probabilities)
```

Compute measurement probabilities for all computational basis states.

### simulate_shots

```python
counts = sim.simulate_shots(quantum_code, shots=1000)
# Returns: dict[int, int] mapping basis state index -> count
```

Simulate multiple measurement shots, returning a histogram of outcomes.

### simulate_density_matrix

```python
density = sim.simulate_density_matrix(quantum_code)
# Returns: np.ndarray (2^n x 2^n density matrix)
```

Compute the density matrix (requires `backend_type='densitymatrix'`).

### simulate_stateprob

```python
probs = sim.simulate_stateprob(quantum_code)
# Returns: np.ndarray (2^n probabilities)
```

Alias for `simulate_pmeasure` with explicit naming.

### simulate_single_shot

```python
outcome = sim.simulate_single_shot(quantum_code)
# Returns: int (basis state index)
```

Simulate a single measurement shot.

### simulate_preprocess

```python
opcodes, measured_qubits = sim.simulate_preprocess(quantum_code)
# Returns: tuple[list[OpcodeType], list[int]]
```

Parse and preprocess the circuit without executing. Useful for debugging.

## Backend Types

### statevector

Default backend. Maintains pure quantum state as a complex vector.

- Efficient for noiseless circuits
- Supports all gate operations
- Use for: VQE expectation values, circuit debugging, algorithm development

```python
sim = OriginIR_Simulator(backend_type='statevector')
```

### densitymatrix

Maintains quantum state as a density matrix (2^n x 2^n).

- Required for noisy simulation
- Supports mixed states
- Higher memory usage: O(4^n) vs O(2^n) for statevector
- Use for: noise modeling, error analysis, open quantum systems

```python
sim = OriginIR_Simulator(backend_type='densitymatrix')
```

## Topology Validation

Restrict circuits to hardware-compatible qubit layouts:

```python
# Only allow qubits 0-3
sim = OriginIR_Simulator(available_qubits=[0, 1, 2, 3])

# Only allow specific two-qubit gate connections
sim = OriginIR_Simulator(
    available_qubits=[0, 1, 2, 3],
    available_topology=[[0, 1], [1, 2], [2, 3], [3, 0]]
)
```

When topology validation is active, circuits using disallowed qubits or connections will raise errors during simulation.

## Noise Modeling

### Readout Error

Model measurement readout errors per qubit:

```python
# Each qubit has [P(read 0 | true 1), P(read 1 | true 0)]
readout_errors = {
    0: [0.02, 0.03],  # Qubit 0: 2% false 0, 3% false 1
    1: [0.01, 0.02],  # Qubit 1: 1% false 0, 2% false 1
}

sim = OriginIR_NoisySimulator(readout_error=readout_errors)
result = sim.simulate_shots(circuit.originir, shots=1000)
```

### ErrorLoader

Custom gate error models via the `ErrorLoader` interface:

```python
from qpandalite.simulator import ErrorLoader

class CustomErrorLoader(ErrorLoader):
    def get_gate_error(self, gate_name, qubits):
        # Return error channel for specific gate/qubit combination
        ...
```

## Backend Factory

Use `get_backend` for a unified interface:

```python
from qpandalite.simulator import get_backend

# OriginIR statevector backend
sim = get_backend(program_type='originir', backend_type='statevector')

# QASM density matrix backend
sim = get_backend(program_type='qasm', backend_type='densitymatrix')
```

## Common Patterns

### Expectation Value from Statevector

```python
import numpy as np
from qpandalite.simulator import OriginIR_Simulator

def compute_expectation(circuit_originir, pauli_string):
    """Compute <psi|P|psi> for a Pauli operator P."""
    sim = OriginIR_Simulator(backend_type='statevector')
    sv = sim.simulate_statevector(circuit_originir)
    # Compute based on Pauli string (e.g., 'Z0Z1')
    ...
    return expectation
```

### Shot-Based Measurement

```python
from qpandalite.simulator import OriginIR_Simulator

sim = OriginIR_Simulator()
counts = sim.simulate_shots(circuit.originir, shots=8192)

# Convert to probabilities
total = sum(counts.values())
probs = {k: v / total for k, v in counts.items()}
```

### Noisy Circuit Simulation

```python
from qpandalite.simulator import OriginIR_NoisySimulator

sim = OriginIR_NoisySimulator(
    backend_type='statevector',
    readout_error={0: [0.01, 0.02], 1: [0.015, 0.025]}
)

# Compare noisy vs noiseless
noisy_counts = sim.simulate_shots(circuit.originir, shots=1000)

clean_sim = OriginIR_Simulator()
clean_counts = clean_sim.simulate_shots(circuit.originir, shots=1000)
```
