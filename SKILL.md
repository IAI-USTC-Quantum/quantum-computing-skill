---
name: quantum-computing
description: "Use when the user asks about UnifiedQuantum, uniqc, OriginIR, OpenQASM, quantum circuit construction, local simulation, dummy backend, cloud submission, backend discovery/cache, RegionSelector, VQE, QAOA, UCCSD, quantum ML, or PyTorch integration. Provide practical UnifiedQuantum workflows for algorithm development, simulation, and real-device experiments."
---

# Quantum-Computing Skill

Use this skill to help agents build useful quantum-computing work with UnifiedQuantum. Prefer direct, runnable workflows over package history.

## Core Mental Model

UnifiedQuantum has four common surfaces:

1. **Circuit authoring**: build circuits with `uniqc.circuit_builder.Circuit`, then export OriginIR or OpenQASM.
2. **Local simulation**: validate circuits with `uniqc simulate` or `OriginIR_Simulator` before spending cloud quota.
3. **Algorithm development**: compose ansatz helpers, simulators, analyzers, SciPy/PyTorch, and optimization loops.
4. **Cloud experiments**: discover a backend, map/select qubits, submit through CLI or `uniqc.task_manager`, then query and record results.

For new projects, assume a current UnifiedQuantum release. Do not discuss old release history unless the user is explicitly debugging an old environment.

## First Decision

Choose the path from the user's goal:

- **Learn or prototype a circuit**: read [references/circuit-building.md](references/circuit-building.md), then use [references/simulators.md](references/simulators.md).
- **Run shell workflows or convert formats**: read [references/cli-guide.md](references/cli-guide.md).
- **Develop VQE/QAOA/UCCSD-style algorithms**: read [references/variational-algorithms.md](references/variational-algorithms.md); use [references/h2-molecular-simulation.md](references/h2-molecular-simulation.md) for H2-style VQE.
- **Use PyTorch or batching helpers**: read [references/pytorch-integration.md](references/pytorch-integration.md).
- **Run dummy, cloud simulator, or real hardware**: read [references/cloud-platforms.md](references/cloud-platforms.md).
- **Something fails after following the feature reference**: read [references/troubleshooting.md](references/troubleshooting.md).

## Practical Defaults

Use these defaults unless the user gives a reason not to:

- Install full functionality with `pip install "unified-quantum[all]"` in an isolated project environment.
- Build circuits in Python, export `originir`, then run CLI or simulator workflows on that normalized file.
- Use dummy backend as the first task-manager rehearsal: `submit_task(circuit, backend="dummy", shots=...)`.
- Use `uniqc backend list/show/chip-display` before real-device submission.
- Use `RegionSelector` or backend characterization data when hardware quality and topology matter.
- Keep shot counts low for initial real-device checks; increase only after the workflow and backend choice are verified.

## Core Snippets

Circuit:

```python
from uniqc.circuit_builder import Circuit

circuit = Circuit(2)
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure(0, 1)
print(circuit.originir)
```

Local simulation:

```python
from uniqc.simulator import OriginIR_Simulator

sim = OriginIR_Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(circuit.originir)
```

Dummy/cloud task API:

```python
from uniqc import submit_task, wait_for_result

task_id = submit_task(circuit, backend="dummy", shots=1000)
result = wait_for_result(task_id, timeout=60)
```

Variational building blocks:

```python
from uniqc.algorithmics.ansatz import hea, qaoa_ansatz, uccsd_ansatz
```

## Environment Guidance

Do not silently modify a user's Python environment. If setup is needed, first identify whether they are using `venv`, Conda, Pixi, uv, or system Python. For a fresh project, recommend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "unified-quantum[all]"
```

If the user only needs the CLI, an isolated tool install is also reasonable. If the user is debugging an existing project, inspect the active interpreter, `uniqc` path, package version, and import path before changing dependencies.

## Names To Remember

- PyPI package: `unified-quantum`
- Python import package: `uniqc`
- CLI command: `uniqc`
- Config file: `~/.uniqc/uniqc.yml`
- Local task cache: `~/.uniqc/cache/tasks.sqlite`
- Backend cache: `~/.uniqc/cache/backends.json`
- Chip characterization cache: `~/.uniqc/backend-cache/*.json`

## Response Style

- Give the user a runnable path first, then mention optional refinements.
- Prefer small complete examples over long API inventories.
- For hardware work, include backend selection, shots, wait/query flow, and where results are cached.
- For algorithm work, include the objective function shape, simulator/analyzer choice, and optimizer loop.
- For suspected library bugs, reduce to a minimal reproducer, check current docs/issues, and only then suggest filing an upstream issue.
