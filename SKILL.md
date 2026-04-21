---
name: quantum-computing-skill
description: Guide quantum programming with QPanda-lite. Use when the user asks about "quantum circuit", "QPanda", "VQE", "QAOA", "variational quantum", "NISQ", "quantum machine learning", "submit to quantum cloud", "H2 simulation", "HEA ansatz", "UCCSD", "originir", "qasm", "quantum simulator", or discusses building quantum programs, variational algorithms, quantum neural networks, or molecular simulation. Covers circuit construction, CLI commands, local simulation, cloud task submission, and algorithm implementation.
version: 1.1.0
---

# QPanda-lite Quantum Programming Skill

> **版本要求**: 本SKILL.md基于qpandalite源码编译版本(v0.3.0+)编写。pip安装的qpandalite 0.2.5/0.3.0存在bug，无法提供完整API。

## 安装方式（推荐源码编译）

pip安装版本存在以下问题：
- **qpandalite 0.2.5**: 缺少`algorithmics`、`pytorch`模块，CLI命令不可用
- **qpandalite 0.3.0 (pip)**: wheel包包含Python 3.7编译的.so文件，与所有Python版本不兼容

**源码编译安装步骤**：
```bash
# 克隆源码（需要git submodules）
git clone --recurse-submodules https://github.com/Agony5757/QPanda-lite.git
cd QPanda-lite

# 编译（需要CMake >= 3.26，如系统cmake版本过低请用pip install cmake --upgrade）
cmake -B build -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=$(which python3)
cmake --build build

# 安装
pip install .
# 或开发模式
pip install -e . --no-build-isolation
```

**验证安装**：
```bash
python3 -c "import qpandalite; print(qpandalite.__version__)"
qpandalite --help  # 应显示CLI帮助信息
```

---

Provide guidance for quantum programming using QPanda-lite, a lightweight Python-native quantum computing framework for NISQ devices.

## Overview

QPanda-lite enables quantum circuit construction, simulation, and execution on real quantum hardware. Core workflow:

1. **Build circuits** using the `Circuit` class with intuitive gate methods
2. **Simulate locally** with statevector or density matrix backends
3. **Submit to clouds** via OriginQ, Quafu, or IBM Quantum adapters

Installation:
```bash
pip install qpandalite
```

## Circuit Construction Quick Reference

Create circuits with the `Circuit` class:

```python
from qpandalite.circuit_builder import Circuit

# Basic initialization (源码版本)
c = Circuit()          # Empty circuit
c = Circuit(4)         # 4-qubit circuit (源码编译版本支持)
c = Circuit(qregs={"data": 4, "ancilla": 2})  # Named registers

# 注意：pip安装的0.2.5版本Circuit()不接受任何参数
```

### Single-Qubit Gates

```python
c.h(0)      # Hadamard
c.x(0)      # Pauli-X
c.y(0)      # Pauli-Y
c.z(0)      # Pauli-Z
c.s(0)      # S gate
c.sdg(0)    # S-dagger
c.t(0)      # T gate
c.tdg(0)    # T-dagger
c.sx(0)     # Square-root-X
```

### Parametric Single-Qubit Gates

```python
c.rx(0, theta)     # X rotation
c.ry(0, theta)     # Y rotation
c.rz(0, theta)     # Z rotation
c.u1(0, lam)       # U1 gate
c.u2(0, phi, lam)  # U2 gate
c.u3(0, theta, phi, lam)  # U3 gate
```

### Two- and Three-Qubit Gates

```python
c.cnot(0, 1)       # CNOT (controlled-X)
c.cx(0, 1)         # Alias for CNOT
c.cz(0, 1)         # Controlled-Z
c.swap(0, 1)       # SWAP
c.iswap(0, 1)      # iSWAP
c.toffoli(0, 1, 2) # Toffoli (CCNOT)
c.cswap(0, 1, 2)   # Fredkin (controlled SWAP)
```

### Measurement

```python
c.measure(0)           # Measure qubit 0
c.measure(0, 1, 2)     # Measure multiple qubits
```

### Context Managers

```python
# Controlled operations
with c.control(0):
    c.x(1)    # Becomes CNOT(0, 1)
    c.y(2)    # Becomes controlled-Y(0, 2)

# Dagger (adjoint) operations
with c.dagger():
    c.h(0)    # Applies H-dagger
```

### Output Formats

```python
originir = c.originir  # OriginIR format string
qasm = c.qasm          # OpenQASM 2.0 format string
```

## CLI Commands Quick Reference

QPanda-lite provides a Typer-based CLI accessible via `qpandalite` or `python -m qpandalite`.

### circuit - Format Conversion

```bash
qpandalite circuit input.oir --format qasm -o output.qasm
qpandalite circuit input.oir --info  # Show circuit statistics
```

### simulate - Local Simulation

```bash
qpandalite simulate circuit.oir --backend statevector --shots 1024
qpandalite simulate circuit.oir --backend density --format json
```

Options:
- `--backend, -b`: `statevector` (default) or `density`
- `--shots, -s`: Number of shots (default: 1024)
- `--format, -f`: `table` (default) or `json`
- `--output, -o`: Output file (default: stdout)

### submit - Cloud Submission

```bash
qpandalite submit circuit.oir --platform originq --shots 1000
qpandalite submit circuit.oir --platform quafu --chip-id ScQ-P10 --wait
```

Options:
- `--platform, -p`: `originq`, `quafu`, `ibm`, or `dummy`
- `--chip-id`: Target chip identifier
- `--shots, -s`: Number of shots
- `--wait, -w`: Wait for result after submission
- `--timeout`: Timeout in seconds (default: 300)

### result - Query Results

```bash
qpandalite result <task-id> --platform originq --wait --timeout 60
```

### task - Task Management

```bash
qpandalite task list --status running --platform originq
qpandalite task show <task-id>
qpandalite task clear
```

### config - Configuration

```bash
qpandalite config init                    # Initialize config file
qpandalite config set originq.token TOKEN # Set API token
qpandalite config list                    # Show all settings
qpandalite config validate                # Validate configuration
```

## Simulator Usage Patterns

### OriginIR Simulator

```python
from qpandalite.simulator import OriginIR_Simulator

# Statevector backend (pure states)
sim = OriginIR_Simulator(backend_type='statevector')

# Density matrix backend (mixed states)
sim = OriginIR_Simulator(backend_type='densitymatrix')

# Simulation methods
statevector = sim.simulate_statevector(circuit.originir)
probabilities = sim.simulate_pmeasure(circuit.originir)
counts = sim.simulate_shots(circuit.originir, shots=1000)
```

### Topology Validation

```python
sim = OriginIR_Simulator(
    backend_type='statevector',
    available_qubits=[0, 1, 2, 3],
    available_topology=[[0, 1], [1, 2], [2, 3]]
)
```

### QASM Simulator

```python
from qpandalite.simulator import QASM_Simulator

sim = QASM_Simulator(backend_type='statevector')
result = sim.simulate_shots(qasm_circuit, shots=1000)
```

## Cloud Platform Integration

### Configuration

**Environment variables:**
```bash
export QPANDA_API_KEY="your-originq-token"
export QUAFU_API_TOKEN="your-quafu-token"
export IBM_TOKEN="your-ibm-token"
```

**Config file (`~/.qpandalite/qpandalite.yml`):**
```yaml
originq:
  token: your-originq-token
  submit_url: https://...
  query_url: https://...
quafu:
  token: your-quafu-token
```

### Programmatic Submission

```python
from qpandalite import submit_task, wait_for_result
from qpandalite.circuit_builder import Circuit

# Build circuit
c = Circuit(2)
c.h(0)
c.cnot(0, 1)
c.measure(0, 1)

# Submit to cloud
task_id = submit_task(c.originir, backend='originq', shots=1000)

# Wait for result
result = wait_for_result(task_id, backend='originq', timeout=300)
```

### Dummy Mode (Local Testing)

```python
# Via environment variable
import os
os.environ['QPANDALITE_DUMMY'] = 'true'

# Or explicitly
task_id = submit_task(c.originir, backend='originq', dummy=True)
```

### Supported Platforms

| Platform | Backend Name | Adapter |
|----------|-------------|---------|
| Origin Quantum | `originq` | `OriginQAdapter` |
| BAQIS Quafu | `quafu` | `QuafuAdapter` |
| IBM Quantum | `ibm` | `QiskitAdapter` |
| Local (test) | `dummy` | `DummyAdapter` |

## Algorithm Components

### HEA - Hardware-Efficient Ansatz

```python
from qpandalite.algorithmics.ansatz import hea

# Create HEA circuit
circuit = hea(n_qubits=4, depth=2)
# Total parameters: 2 * n_qubits * depth = 16

# With custom parameters
import numpy as np
params = np.random.uniform(0, 2*np.pi, 16)
circuit = hea(n_qubits=4, depth=2, params=params)
```

Structure per layer:
1. `Rz(q, θ)` → `Ry(q, θ)` on every qubit
2. Ring of CNOT gates: `CNOT(i, (i+1) % n)`

### UCCSD - Unitary Coupled-Cluster

```python
from qpandalite.algorithmics.ansatz import uccsd_ansatz

circuit = uccsd_ansatz(n_qubits=4, n_electrons=2)
```

### QAOA - Quantum Approximate Optimization

```python
from qpandalite.algorithmics.ansatz import qaoa_ansatz

# Define cost Hamiltonian terms
cost_terms = [("Z0Z1", 0.5), ("Z1Z2", 0.5), ("Z0Z2", 0.5)]
circuit = qaoa_ansatz(cost_terms, p=2)
```

## PyTorch Integration

### QuantumLayer

```python
from qpandalite.pytorch import QuantumLayer
from qpandalite.algorithmics.ansatz import hea

# Create ansatz circuit template
circuit_template = hea(n_qubits=4, depth=2)

# Define expectation function
def expectation_fn(circuit):
    from qpandalite.simulator import OriginIR_Simulator
    sim = OriginIR_Simulator()
    probs = sim.simulate_pmeasure(circuit.originir)
    return probs[0]  # Probability of |00...0>

# Create PyTorch layer
qlayer = QuantumLayer(
    circuit=circuit_template,
    expectation_fn=expectation_fn,
    n_outputs=1
)
```

### Parameter-Shift Gradient

```python
from qpandalite.pytorch import parameter_shift_gradient, compute_all_gradients

# Single parameter gradient
grad = parameter_shift_gradient(circuit, param_name, expectation_fn)

# All gradients
grads = compute_all_gradients(circuit, expectation_fn)
```

### Batch Execution

```python
from qpandalite.pytorch import batch_execute, batch_execute_with_params

# Execute multiple circuits in parallel
results = batch_execute(circuits, executor, n_workers=4)

# Execute with different parameter values
results = batch_execute_with_params(
    circuit_template,
    param_values_list,
    executor,
    n_workers=4
)
```

## Reference Files Guidance

For detailed information, consult the following reference files:

- **`references/circuit-building.md`**: Complete Circuit class API, all gate methods, QReg/Qubit types, Parameters
- **`references/cli-guide.md`**: Full CLI command reference with all flags and options
- **`references/simulators.md`**: Simulator backends, noisy simulation, error models
- **`references/cloud-platforms.md`**: Detailed cloud platform setup, adapter APIs, task management
- **`references/variational-algorithms.md`**: HEA, UCCSD, QAOA ansatz details, optimization patterns
- **`references/pytorch-integration.md`**: QuantumLayer, gradient computation, hybrid architectures
- **`references/h2-molecular-simulation.md`**: H2 molecular simulation with HEA ansatz

## Examples

Working code examples are available in the `examples/` directory:

- `basic_circuit.py` - Bell state creation and simulation
- `cli_demo.sh` - CLI usage demonstration script
- `mnist_classifier.py` - Variational quantum classifier for MNIST
- `h2_hea_vqe.py` - H2 ground state energy with HEA ansatz
- `cloud_submission.py` - Cloud platform submission example
- `qaoa_maxcut.py` - QAOA for MaxCut problem
