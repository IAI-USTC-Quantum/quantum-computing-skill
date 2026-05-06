---
name: uniqc-basic-usage
description: "Use when the user asks about UnifiedQuantum or uniqc basic usage: installation, Python imports, Circuit construction, OriginIR/OpenQASM export, local simulation (incl. MPS / matrix-product-state / tensor network on linear topology), CLI help, config, dummy backends (`dummy:virtual-line-N`, `dummy:mps:linear-N`), dry-run, backend discovery/cache, simple cloud submission, result queries, calibration, QEM, timeline visualization, and first-pass troubleshooting. Provide practical runnable workflows for getting started and validating common UnifiedQuantum tasks."
---

# Uniqc Basic Usage Skill

Use this skill to help agents handle common UnifiedQuantum usage. Prefer direct, runnable workflows over package history. Keep the guidance broad enough for first-pass usage; deep algorithm development, QEM, and real-hardware operations can move into dedicated skills as they are added.

## Core Mental Model

UnifiedQuantum (current 0.0.11.x release) has six common surfaces:

1. **Circuit authoring**: build circuits with top-level `uniqc.Circuit`, then export OriginIR or OpenQASM.
2. **Local simulation**: validate circuits with `uniqc simulate` or `OriginIR_Simulator` before spending cloud quota.
3. **Algorithm development**: compose ansatz helpers, simulators, analyzers, SciPy/PyTorch, and optimization loops.
4. **Compile and dummy workflows**: use explicit dummy backend ids to check task, topology, and chip-backed noisy paths locally.
5. **Calibration and QEM**: characterize chip errors with XEB and readout calibration, then mitigate measurement errors with ReadoutEM or M3Mitigator.
6. **Cloud experiments**: discover a backend, dry-run, map/select qubits, submit through CLI/API (OriginQ, Quafu, Quark, IBM), then query and record results.

For new projects, assume a current UnifiedQuantum release. Do not discuss old release history unless the user is explicitly debugging an old environment.

## First Decision

Choose the path from the user's goal:

- **Ask for current recommended usage or release-check paths**: read [references/best-practices.md](references/best-practices.md) first.
- **Learn or prototype a circuit**: read [references/circuit-building.md](references/circuit-building.md), then use [references/simulators.md](references/simulators.md).
- **Run shell workflows or convert formats**: read [references/cli-guide.md](references/cli-guide.md).
- **Develop VQE/QAOA/UCCSD-style algorithms**: read [references/variational-algorithms.md](references/variational-algorithms.md); use [references/h2-molecular-simulation.md](references/h2-molecular-simulation.md) for H2-style VQE.
- **Use PyTorch or batching helpers**: read [references/pytorch-integration.md](references/pytorch-integration.md).
- **Run dummy, cloud simulator, or real hardware**: read [references/cloud-platforms.md](references/cloud-platforms.md).
- **Calibrate, benchmark, or mitigate readout errors**: read [references/calibration-qem.md](references/calibration-qem.md).
- **Visualize circuit timelines or render to HTML**: read [references/timeline-visualization.md](references/timeline-visualization.md).
- **Something fails after following the feature reference**: read [references/troubleshooting.md](references/troubleshooting.md).

## Practical Defaults

Use these defaults unless the user gives a reason not to:

- For CLI-only use, prefer `uv tool install unified-quantum`; for Python API use `uv pip install unified-quantum` inside the user's project environment.
- Import common objects from `uniqc` directly: `Circuit`, `compile`, `submit_task`, `wait_for_result`, `dry_run_task`, `BackendInfo`, `Platform`, `QubitTopology`, ansatz helpers, and expectation helpers.
- Build circuits in Python, export `originir`, then run CLI or simulator workflows on that normalized file.
- Use explicit dummy backend ids:
  - `dummy`: unconstrained, noiseless local virtual machine.
  - `dummy:virtual-line-N` / `dummy:virtual-grid-RxC`: constrained virtual topology, noiseless.
  - `dummy:<platform>:<backend>`: real backend topology and calibration, compile/transpile, then local noisy execution. Requires `unified-quantum[qiskit]` for the topology-aware compile pass; without it `submit_task` raises `CompilationFailedException`.
- Run `dry_run_task(...)` or `uniqc submit --dry-run` before real-device submission.
- For CLI-heavy AI-agent work, enable progressive hints once with `uniqc config always-ai-hint on`, or pass `--ai-hints` / `--ai-hint` on individual commands.
- Use `uniqc backend update`, `list`, `show`, and `chip-display` before real-device submission.
- Use `RegionSelector` or backend characterization data when hardware quality and topology matter.
- Use `uniqc calibrate xeb/readout/pattern` CLI commands for chip characterization experiments; results are cached to `~/.uniqc/calibration_cache/`.
- Use `ReadoutEM` or `M3Mitigator` from `uniqc.qem` for readout error mitigation on measurement results.
- Quark platform requires `QUARK_API_KEY` in config (not `token`); use `--platform quark` in CLI or `backend="quark"` in Python. Install with `unified-quantum[quark]` (Python ≥ 3.12).
- Keep shot counts low for initial real-device checks; increase only after the workflow and backend choice are verified.
- Treat Quafu as deprecated and install `[quafu]` only when explicitly needed; `[all]` does not include it (still true on 0.0.11.x).
- Configure IBM proxy through `uniqc config set ibm.proxy.https <URL>` / `ibm.proxy.http <URL>` when the network path requires it.
- Real `originq` paths (cloud simulator AND hardware AND chip-backed dummy compile) require `pip install unified-quantum[originq]` (pulls `pyqpanda3`); likewise `[quafu]` for Quafu, `[quark]` for Quark, `[qiskit]` for IBM and for chip-backed dummy backends (`dummy:originq:<chip>`, `dummy:quark:<chip>`).
- `UNIQC_DUMMY` and `UNIQC_SKIP_VALIDATION` are read **at module import time**. Set them BEFORE `import uniqc` (or in the shell environment); changing them at runtime via `os.environ[...]` has no effect.

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

Compile:

```python
from uniqc import compile, find_backend
backend_info = find_backend('originq:WK_C180')
compiled = compile(circuit, backend_info, level=2,
                   basis_gates=['cz', 'sx', 'rz'])  # returns a Circuit
```

`compile()` returns a `Circuit` directly. `TranspilerConfig` still exists for advanced flows but `compile()` does not accept `config=`. Chip-backed compile passes (e.g. against `originq:WK_C180`) require `unified-quantum[qiskit]`.

QEM:

```python
from uniqc import ReadoutEM

em = ReadoutEM(adapter, max_age_hours=24.0, shots=1000)
corrected_counts = em.mitigate_counts(raw_counts, measured_qubits=[0, 1])
```

## Environment Guidance

Do not silently modify a user's Python environment. If setup is needed, first identify whether they are using `venv`, Conda, Pixi, uv, or system Python. For a fresh project, recommend:

```bash
uv venv
source .venv/bin/activate
uv pip install unified-quantum
```

If the user only needs the CLI, use `uv tool install unified-quantum`. If the user is debugging an existing project, inspect the active interpreter, `uniqc` path, package version, and import path before changing dependencies. The package root no longer supports `python -m uniqc`; the module fallback is `python -m uniqc.cli` (still true on the current release).

## Names To Remember

- PyPI package: `unified-quantum`
- Python import package: `uniqc`
- CLI command: `uniqc`
- CLI module fallback: `python -m uniqc.cli`
- Config file: `~/.uniqc/config.yaml`
- Python config module: `uniqc.config` (canonical; `uniqc.backend_adapter.config` is a pure re-export shim)
- Compile entry point: `uniqc.compile` (`compile()`, `TranspilerConfig`, `CompilationResult`)
- Calibration module: `uniqc.calibration` (XEB, readout calibration, `XEBResult`, `ReadoutCalibrationResult`)
- QEM module: `uniqc.qem` (`M3Mitigator`, `ReadoutEM`, `StaleCalibrationError`)
- Visualization module: `uniqc.visualization` (`circuit_to_html`, `plot_time_line_html`, `schedule_circuit`)
- Algorithms workflows: `uniqc.algorithms.workflows` (`xeb_workflow`, `readout_em_workflow`)
- BackendOptions hierarchy: `BackendOptions`, `OriginQOptions`, `QuafuOptions`, `QuarkOptions`, `IBMOptions`, `DummyOptions`. Use `BackendOptionsFactory().create_default('originq')` for a sane default; `BackendOptionsFactory().from_kwargs(platform, **kwargs)` builds from explicit kwargs.
- Gateway / web UI: `uniqc gateway start [--port N --host HOST]` starts the local task dashboard; manage it with `uniqc gateway status / stop / restart`.
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
