# PyTorch Integration Reference

Complete reference for using UnifiedQuantum with PyTorch for quantum machine learning.

## Overview

UnifiedQuantum provides PyTorch integration for hybrid quantum-classical models:

- `QuantumLayer`: PyTorch `nn.Module` wrapping a quantum circuit
- `parameter_shift_gradient`: Compute gradients via parameter-shift rule
- `compute_all_gradients`: Compute all parameter gradients at once
- `batch_execute`: Parallel circuit evaluation

## QuantumLayer

Wraps a quantum circuit as a differentiable PyTorch layer.

```python
from uniqc.pytorch import QuantumLayer

qlayer = QuantumLayer(
    circuit,              # Circuit template (with Parameter objects)
    expectation_fn,       # Callable: Circuit -> float
    n_outputs=1,          # Number of output values
    init_params=None,     # Initial parameter values (torch.Tensor)
    shift=np.pi / 2       # Parameter-shift step size
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `circuit` | `Circuit` | required | Circuit template with named Parameters |
| `expectation_fn` | `Callable[[Circuit], float]` | required | Function computing expectation value |
| `n_outputs` | `int` | 1 | Number of output features |
| `init_params` | `torch.Tensor` | `None` | Initial parameter values |
| `shift` | `float` | `π/2` | Parameter-shift step size |

### Usage

```python
import torch
import torch.nn as nn
from uniqc.circuit_builder import Circuit, Parameter
from uniqc.pytorch import QuantumLayer
from uniqc.simulator import OriginIR_Simulator

# Create circuit template with Parameters
circuit = Circuit(4)
theta = Parameter("theta")
circuit.ry(0, theta)
# ... more gates ...

# Define expectation function
sim = OriginIR_Simulator()

def expectation_fn(circuit):
    probs = sim.simulate_pmeasure(circuit.originir)
    return probs[0]  # P(|00...0>)

# Create quantum layer
qlayer = QuantumLayer(circuit, expectation_fn, n_outputs=1)

# Use in PyTorch model
output = qlayer()  # Forward pass
output.backward()  # Automatic gradient computation
```

## Gradient Computation

### parameter_shift_gradient

Compute the gradient of an expectation value with respect to a single parameter using the parameter-shift rule:

```
∂f/∂θ = [f(θ + s) - f(θ - s)] / (2s)
```

where `s` is the shift (default: π/2).

```python
from uniqc.pytorch import parameter_shift_gradient

grad = parameter_shift_gradient(
    circuit,              # Circuit with bound parameter
    param_name,           # Name of the parameter to differentiate
    expectation_fn,       # Expectation value function
    shift=np.pi / 2       # Shift step size
)
# Returns: float (gradient value)
```

### compute_all_gradients

Compute gradients for all parameters simultaneously:

```python
from uniqc.pytorch import compute_all_gradients

grads = compute_all_gradients(
    circuit,              # Circuit with parameters
    expectation_fn,       # Expectation value function
    shift=np.pi / 2       # Shift step size
)
# Returns: dict[str, float] mapping parameter names to gradient values
```

## Batch Execution

### batch_execute

Evaluate multiple circuits in parallel:

```python
from uniqc.pytorch import batch_execute

results = batch_execute(
    circuits,             # list[Circuit] to evaluate
    executor,             # Callable: Circuit -> np.ndarray
    n_workers=4           # Number of parallel workers
)
# Returns: list[np.ndarray]
```

### batch_execute_with_params

Evaluate a circuit template with different parameter values:

```python
from uniqc.pytorch import batch_execute_with_params

results = batch_execute_with_params(
    circuit_template,                    # Circuit with Parameters
    param_values=[                       # List of parameter dicts
        {"theta": 0.1, "phi": 0.2},
        {"theta": 0.3, "phi": 0.4},
        {"theta": 0.5, "phi": 0.6},
    ],
    executor=sim.simulate_pmeasure,      # Execution function
    n_workers=4
)
# Returns: list[np.ndarray]
```

## Hybrid QNN Architecture

### Pattern: Classical Pre-processing + Quantum Layer

```python
import torch
import torch.nn as nn
from uniqc.pytorch import QuantumLayer

class HybridModel(nn.Module):
    def __init__(self, n_qubits, qlayer):
        super().__init__()
        self.pre = nn.Sequential(
            nn.Linear(784, 128),
            nn.ReLU(),
            nn.Linear(128, n_qubits),
            nn.Tanh()  # Scale to [-1, 1] for angle encoding
        )
        self.qlayer = qlayer
        self.post = nn.Sequential(
            nn.Linear(1, 2),  # Binary classification
            nn.Softmax(dim=-1)
        )

    def forward(self, x):
        x = self.pre(x)      # Classical: 784 -> n_qubits
        # Use outputs as rotation angles in quantum circuit
        x = self.qlayer(x)   # Quantum: expectation value
        x = self.post(x)     # Classical: 1 -> 2 (classes)
        return x
```

### Pattern: Multiple Quantum Layers

```python
class MultiQuantumModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.qlayer1 = QuantumLayer(circuit1, exp_fn1, n_outputs=2)
        self.qlayer2 = QuantumLayer(circuit2, exp_fn2, n_outputs=2)
        self.classical = nn.Linear(4, 2)

    def forward(self, x):
        q1 = self.qlayer1(x)
        q2 = self.qlayer2(x)
        combined = torch.cat([q1, q2], dim=-1)
        return self.classical(combined)
```

## Training Loop

```python
import torch
from torch.utils.data import DataLoader, TensorDataset

def train_hybrid_model(model, X_train, y_train, epochs=50, lr=0.01):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.LongTensor(y_train)
    )
    loader = DataLoader(dataset, batch_size=32, shuffle=True)

    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        total = 0

        for X_batch, y_batch in loader:
            optimizer.zero_grad()
            output = model(X_batch)
            loss = criterion(output, y_batch)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            pred = output.argmax(dim=1)
            correct += (pred == y_batch).sum().item()
            total += len(y_batch)

        acc = correct / total
        print(f"Epoch {epoch+1}/{epochs} | Loss: {total_loss:.4f} | Acc: {acc:.4f}")
```

## Performance Tips

1. **Batch execution**: Use `batch_execute_with_params` for evaluating circuits with different parameters in parallel
2. **Reduce circuit depth**: Shallower circuits compute faster in simulation
3. **Cache simulators**: Create simulator once and reuse across calls
4. **Minimize parameters**: Fewer parameters means fewer gradient evaluations
5. **Use GPU for classical parts**: Move classical layers to GPU while quantum simulation runs on CPU
