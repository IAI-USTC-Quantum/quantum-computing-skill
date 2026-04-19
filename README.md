# quantum-computing.skill

基于 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) 的 Claude Code 量子编程 Skill

A Claude Code skill for quantum programming with [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum).


## Overview

This skill guides AI agents to effectively use UnifiedQuantum, a lightweight Python-native quantum computing aggregation framework for NISQ devices. It covers:

- Quantum circuit construction with the `Circuit` class
- Local simulation (statevector, density matrix, noisy)
- CLI commands for simulation and cloud submission
- Variational algorithms (VQE, QAOA) with HEA/UCCSD ansatzes
- PyTorch integration for quantum machine learning
- Cloud platform submission (OriginQ, Quafu, IBM Quantum)

## Quick Start

### Installation

```bash
pip install unified-quantum
```

### Hello Quantum World

```python
from uniqc.circuit_builder import Circuit
from uniqc.simulator import OriginIR_Simulator

# Build a Bell state
c = Circuit(2)
c.h(0)
c.cnot(0, 1)
c.measure(0, 1)

# Simulate
sim = OriginIR_Simulator()
result = sim.simulate_shots(c.originir, shots=1000)
print(result)
```

### CLI Usage

```bash
# Simulate a circuit file
uniqc simulate circuit.oir --shots 1024

# Submit to cloud
uniqc submit circuit.oir --platform originq --shots 1000 --wait
```

## Project Structure

```
quantum-computing-skill/
├── SKILL.md                 # Main skill definition
├── references/              # Detailed API documentation
│   ├── circuit-building.md
│   ├── cli-guide.md
│   ├── simulators.md
│   ├── cloud-platforms.md
│   ├── variational-algorithms.md
│   ├── pytorch-integration.md
│   └── h2-molecular-simulation.md
├── examples/                # Working code examples
│   ├── basic_circuit.py
│   ├── cli_demo.sh
│   ├── mnist_classifier.py
│   ├── h2_hea_vqe.py
│   ├── cloud_submission.py
│   └── qaoa_maxcut.py
└── scripts/
    └── setup_uniqc.sh       # Installation verification
```

## Examples

| Example | Description |
|---------|-------------|
| `basic_circuit.py` | Bell state creation and local simulation |
| `cli_demo.sh` | CLI format conversion and simulation |
| `mnist_classifier.py` | VQC for MNIST binary classification |
| `h2_hea_vqe.py` | H2 ground state energy curve with HEA |
| `cloud_submission.py` | Submit circuits to quantum cloud platforms |
| `qaoa_maxcut.py` | QAOA for MaxCut optimization |

## License

Apache License 2.0
