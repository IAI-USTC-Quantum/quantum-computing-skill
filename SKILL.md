---
name: quantum-computing
description: "Use when the user asks about UnifiedQuantum, uniqc, OriginIR, OpenQASM, quantum circuit construction, local simulation, dummy backend ids, dry-run, cloud submission, backend discovery/cache, RegionSelector, compile/transpile, calibration, QEM, XEB, VQE, QAOA, UCCSD, quantum ML, or PyTorch integration. Provide practical UnifiedQuantum workflows for algorithm development, simulation, and real-device experiments."
---

# Quantum-Computing Skill

Use this skill to help agents build useful quantum-computing work with UnifiedQuantum. Prefer direct, runnable workflows over package history.

## Core Mental Model

UnifiedQuantum v0.0.8 has five common surfaces:

1. **Circuit authoring**: build circuits with top-level `uniqc.Circuit`, then export OriginIR or OpenQASM.
2. **Local simulation**: validate circuits with `uniqc simulate` or `OriginIR_Simulator` before spending cloud quota.
3. **Algorithm development**: compose ansatz helpers, simulators, analyzers, SciPy/PyTorch, and optimization loops.
4. **Compile and dummy workflows**: use explicit dummy backend ids to check task, topology, and chip-backed noisy paths locally.
5. **Cloud and calibration experiments**: discover a backend, dry-run, map/select qubits, submit through CLI/API, then query and record results.

For new projects, assume a current UnifiedQuantum release. Do not discuss old release history unless the user is explicitly debugging an old environment.

## First Decision

Choose the path from the user's goal:

- **Ask for current recommended usage or release-check paths**: read [references/best-practices.md](references/best-practices.md) first.
- **Learn or prototype a circuit**: read [references/circuit-building.md](references/circuit-building.md), then use [references/simulators.md](references/simulators.md).
- **Run shell workflows or convert formats**: read [references/cli-guide.md](references/cli-guide.md).
- **Develop VQE/QAOA/UCCSD-style algorithms**: read [references/variational-algorithms.md](references/variational-algorithms.md); use [references/h2-molecular-simulation.md](references/h2-molecular-simulation.md) for H2-style VQE.
- **Use PyTorch or batching helpers**: read [references/pytorch-integration.md](references/pytorch-integration.md).
- **Run dummy, cloud simulator, or real hardware**: read [references/cloud-platforms.md](references/cloud-platforms.md).
- **Something fails after following the feature reference**: read [references/troubleshooting.md](references/troubleshooting.md).

## Practical Defaults

Use these defaults unless the user gives a reason not to:

- For CLI-only use, prefer `uv tool install unified-quantum`; for Python API use `uv pip install unified-quantum` inside the user's project environment.
- Import common objects from `uniqc` directly: `Circuit`, `compile`, `submit_task`, `wait_for_result`, `dry_run_task`, `BackendInfo`, `Platform`, `QubitTopology`, ansatz helpers, and expectation helpers.
- Build circuits in Python, export `originir`, then run CLI or simulator workflows on that normalized file.
- Use explicit dummy backend ids:
  - `dummy`: unconstrained, noiseless local virtual machine.
  - `dummy:virtual-line-N` / `dummy:virtual-grid-RxC`: constrained virtual topology, noiseless.
  - `dummy:<platform>:<backend>`: real backend topology and calibration, compile/transpile, then local noisy execution.
- Run `dry_run_task(...)` or `uniqc submit --dry-run` before real-device submission.
- For CLI-heavy AI-agent work, enable progressive hints once with `uniqc config always-ai-hint on`, or pass `--ai-hints` / `--ai-hint` on individual commands.
- Use `uniqc backend update`, `list`, `show`, and `chip-display` before real-device submission.
- Use `RegionSelector` or backend characterization data when hardware quality and topology matter.
- Keep shot counts low for initial real-device checks; increase only after the workflow and backend choice are verified.
- Treat Quafu as deprecated and install `[quafu]` only when explicitly needed; `[all]` does not include it in v0.0.8.
- Configure IBM proxy through `uniqc config set ibm.proxy.https <URL>` / `ibm.proxy.http <URL>` when the network path requires it.

## Core Snippets

Circuit:

```python
from uniqc import Circuit

circuit = Circuit()
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
from uniqc import dry_run_task, submit_task, wait_for_result

dry_run = dry_run_task(circuit, backend="dummy", shots=1000)
task_id = submit_task(circuit, backend="dummy", shots=1000)
result = wait_for_result(task_id, timeout=60)
```

Variational building blocks:

```python
from uniqc import calculate_expectation, hea, qaoa_ansatz, uccsd_ansatz
```

## Environment Guidance

Do not silently modify a user's Python environment. If setup is needed, first identify whether they are using `venv`, Conda, Pixi, uv, or system Python. For a fresh project, recommend:

```bash
uv venv
source .venv/bin/activate
uv pip install unified-quantum
```

If the user only needs the CLI, use `uv tool install unified-quantum`. If the user is debugging an existing project, inspect the active interpreter, `uniqc` path, package version, and import path before changing dependencies. The package root no longer supports `python -m uniqc`; the module fallback is `python -m uniqc.cli`.

## Names To Remember

- PyPI package: `unified-quantum`
- Python import package: `uniqc`
- CLI command: `uniqc`
- CLI module fallback: `python -m uniqc.cli`
- Config file: `~/.uniqc/config.yaml`
- AI CLI hints: `--ai-hints` / `--ai-hint`, `UNIQC_AI_HINTS=1`, or `uniqc config always-ai-hint on`
- Local task cache: `~/.uniqc/cache/tasks.sqlite`
- Backend cache: `~/.uniqc/cache/backends.json`
- Chip characterization cache: `~/.uniqc/backend-cache/*.json`
- Calibration cache: `~/.uniqc/calibration_cache/`

## Response Style

- Give the user a runnable path first, then mention optional refinements.
- Prefer small complete examples over long API inventories.
- For hardware work, include backend selection, shots, wait/query flow, and where results are cached.
- For algorithm work, include the objective function shape, simulator/analyzer choice, and optimizer loop.
- For suspected library bugs, reduce to a minimal reproducer, check current docs/issues, and only then suggest filing an upstream issue.
