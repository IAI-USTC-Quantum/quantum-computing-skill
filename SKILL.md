---
name: quantum-computing-skill
description: Guide quantum programming with UnifiedQuantum. Use when the user asks about UnifiedQuantum, uniqc, OriginIR, OpenQASM, circuit building, local simulation, cloud submission, dummy mode, VQE, QAOA, UCCSD, quantum ML, or PyTorch integration with UnifiedQuantum. Focus on the current public workflow: build circuits, export IR/QASM, run with uniqc CLI or task_manager, and add optional extras only when needed.
version: 1.1.0
---

# UnifiedQuantum Skill

Use this skill when the user is working with the current UnifiedQuantum public API, CLI, or examples.

## Default Approach

Prefer the current high-level workflow:

1. Build a circuit with `uniqc.circuit_builder.Circuit`
2. Export `circuit.originir` or `circuit.qasm`
3. Use `uniqc` CLI or `uniqc.task_manager`
4. Add extras only for the features that actually need them

When the user gives a QASM circuit, the safest operational path is often:

1. Convert it to OriginIR with `uniqc circuit`
2. Simulate or submit the normalized OriginIR

That avoids mismatches between different input paths.

## Things To Keep Straight

- Package name: `unified-quantum`
- CLI name: `uniqc`
- Main Python package: `uniqc`
- Config file: `~/.uniqc/uniqc.yml`
- Local task cache: `~/.uniqc/cache/tasks.sqlite`

## Dependency Boundaries

Do not assume every feature is available in a base install.

- Core package: `pip install unified-quantum`
- Local simulation / dummy mode commonly needs: `pip install "unified-quantum[simulation]"`
- OriginQ adapter: `pip install "unified-quantum[originq]"`
- Quafu adapter: `pip install "unified-quantum[quafu]"`
- IBM adapter: `pip install "unified-quantum[qiskit]"`
- PyTorch helpers: `pip install "unified-quantum[pytorch]"`
- TorchQuantum integration: `pip install "unified-quantum[torchquantum]"`

If the user reports import failures around `qutip`, `torch`, `qiskit`, `quafu`, or `pyqpanda3`, treat them as missing optional dependencies first, not as proof the core package is broken.

## CLI Guidance

The current CLI groups are:

- `uniqc circuit`
- `uniqc simulate`
- `uniqc submit`
- `uniqc result`
- `uniqc task`
- `uniqc config`

Prefer `uniqc` over ad-hoc helper scripts when the user is doing format conversion, local execution, or cloud task management from the shell.

Important current nuance:

- `uniqc submit` uses `--platform` plus optional `--backend`
- For OriginQ, the CLI option is `--backend`, not the older `--chip-id`
- For Quafu, `chip_id` is still relevant in Python APIs, but the current CLI surface does not expose a dedicated `--chip-id`
- `simulate` is safest with OriginIR input; normalize QASM first if needed

## Python API Guidance

For programmatic task workflows, prefer:

```python
from uniqc import submit_task, submit_batch, query_task, wait_for_result
```

For ansatz construction, prefer the current exports:

```python
from uniqc.algorithmics.ansatz import hea, qaoa_ansatz, uccsd_ansatz
```

Do not use stale names like `uccsd`.

For PyTorch integration, prefer:

```python
from uniqc.pytorch import (
    QuantumLayer,
    batch_execute,
    batch_execute_with_params,
    parameter_shift_gradient,
    compute_all_gradients,
)
```

## What To Read Next

- For circuits and exports: [references/circuit-building.md](references/circuit-building.md)
- For CLI usage: [references/cli-guide.md](references/cli-guide.md)
- For local simulation and dummy mode: [references/simulators.md](references/simulators.md)
- For config, cloud backends, and task cache: [references/cloud-platforms.md](references/cloud-platforms.md)
- For ansatz and variational workflows: [references/variational-algorithms.md](references/variational-algorithms.md)
- For PyTorch helpers: [references/pytorch-integration.md](references/pytorch-integration.md)
- For H2-style VQE tasks: [references/h2-molecular-simulation.md](references/h2-molecular-simulation.md)

## Response Heuristics

- If the user wants a quick start, start with `Circuit -> originir -> uniqc`.
- If the user is stuck on cloud execution, verify config and backend-specific kwargs before discussing algorithms.
- If the user asks about a failing local simulation, check `simulation` dependencies first.
- If the user asks for a modern variational example, start from `hea`, `qaoa_ansatz`, or `uccsd_ansatz`, not legacy helper names.
- If the user wants a shell workflow, prefer `uniqc` CLI examples over custom wrappers.
