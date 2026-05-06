# Uniqc Basic Usage Skill — Fix Summary

Verified against `uniqc 0.0.11.dev10` in `.venv-test`.
All edits applied to `quantum-computing.skill/skills/uniqc-basic-usage/` and mirrored to
`.agents/skills/uniqc-basic-usage/` (`diff -rq` between the two trees is clean).

> Note: the user-requested target path was `/tmp/skill-fix-summary.md`, but the runtime
> forbids writes to `/tmp`. The summary lives at the repo root instead.

| ID    | Status       | Notes |
|-------|--------------|-------|
| A-S1  | [FIXED]      | SKILL.md compile snippet rewritten to `compile(circuit, backend_info, level=2, basis_gates=[...])` with `find_backend`. |
| A-S2  | [FIXED]      | timeline-visualization.md compile snippet uses the same pattern; `schedule_circuit(compiled, backend_info=backend_info)`. |
| A-S3  | [FIXED]      | `BackendInfo.get(...)` example replaced with `find_backend("originq:WK_C180")`. |
| A-S4  | [FIXED]      | `TimelineSchedule` field list synced to runtime introspection (`gates, qubits, total_duration, unit, gate_durations`, plus `time_points` property). Dropped `n_layers` and `resources`; documented `max(g.layer ...) + 1`. |
| A-S5  | [FIXED]      | qiskit-extras callout added at the top of the file; bottom note about `circuit_to_html` / `plot_time_line_html` updated to flag the `[qiskit]` requirement for scheduling logical circuits. |
| B-S1  | [FIXED]      | `MPSConfig()` default `chi_max=64` documented inline; older "256" claim flagged as incorrect. |
| B-S2  | [FIXED]      | New "OriginIR_Simulator 方法速查" subsection lists `simulate_shots`, `simulate_pmeasure`, `simulate_statevector`, `simulate_density_matrix` and explicitly calls out that there is no `simulate(...)` method. |
| C-S1  | [FIXED]      | variational-algorithms.md and h2-molecular-simulation.md both gained the `Z`/`I` positional vs indexed-Pauli paragraph for `calculate_expectation`. |
| C-S2  | [FIXED]      | C-S2 note added in variational-algorithms.md (skill did not previously mention `calculate_multi_basis_expectation`; added preventive note alongside C-S1). |
| C-S3  | [FIXED]      | circuit-building.md gained the gotcha: `Circuit.originir` is a property; `c.qasm` likewise. |
| D-S1  | [FIXED]      | cloud-platforms.md OriginQ example now compiles before submit; `examples/cloud_submission.py` real-OriginQ helper imports `compile`/`find_backend` and compiles before submission; known-issue note about `auto_compile=True` added (refers to `uniqc-report.md` D2). |
| D-S2  | [FIXED]      | cloud-platforms.md adds a "wait_for_result 的返回结构" subsection clarifying counts dict vs `UnifiedResult`; `cloud_submission.py::print_result` simplified to flat counts and module docstring spells it out. |
| D-S3  | [FIXED]      | SKILL.md "Practical Defaults" bullet for `dummy:<platform>:<backend>` now lists the `[qiskit]` requirement; cloud-platforms.md header callout covers the same ground. |
| D-S4  | [FIXED]      | cloud-platforms.md notes that `dummy:originq:<chip>` ids are submit-only and absent from `find_backend` / `list_backends`; verified via `python -c` (raises `ValueError`). |
| D-S5  | [FIXED]      | RegionSelector minimal example added with `find_best_1D_chain`; performance note about `find_best_2D_from_circuit(..., max_search_seconds=10.0)` for large chips. |
| D-S6  | [FIXED]      | SKILL.md "Names To Remember" mentions `BackendOptionsFactory().create_default('originq')` and `from_kwargs(...)`. |
| D-S7  | [FIXED]      | SKILL.md "Practical Defaults" gained a platform-extras bullet; cloud-platforms.md header repeats it as a callout. |
| D-S8  | [FIXED]      | SKILL.md adds the `UNIQC_DUMMY` / `UNIQC_SKIP_VALIDATION` import-time bullet; cloud-platforms.md repeats inside the env-vars callout. |
| D-S9  | [FIXED]      | cloud-platforms.md replaces the `export ORIGINQ_API_KEY=...` block with the truth (uniqc only reads `UNIQC_PROFILE`/`UNIQC_DUMMY`/`UNIQC_SKIP_VALIDATION`/proxies); `examples/cloud_submission.py` renamed helper to `_sync_env_to_config` (kept old name as alias) and added explanatory module + helper docstrings. |
| E-S1  | [FIXED]      | calibration-qem.md `xeb_workflow.run_1q_xeb_workflow` and `run_2q_xeb_workflow` examples use `backend=<str>` and `pairs=`; verified signatures via `inspect.signature`. |
| E-S2  | [FIXED]      | `readout_em_workflow.run_readout_em_workflow(backend=..., qubits=..., shots=...)` shown as the recommended path; `apply_readout_em(result, readout_em, measured_qubits=...)` documented separately. |
| E-S3  | [FIXED]      | `find_cached_results(..., result_type=...)` everywhere; verified via `inspect.signature`. |
| E-S4  | [FIXED]      | Removed `--parallel` CLI example; replaced with note pointing to `xeb_workflow.run_parallel_xeb_workflow(backend=..., target_qubits=...)`. Verified `--parallel` absent in `uniqc calibrate xeb --help`. |
| E-S5  | [FIXED]      | XEBResult field list now includes `calibrated_at, type, qubit, pairs` (full dataclass); verified via `dataclasses.fields(XEBResult)`. |
| E-S6  | [FIXED]      | Smoke-tested `M3Mitigator(calibration_result=ReadoutCalibrationResult(...))` on 0.0.11.dev10 — works. Example kept the `calibration_result=...` form and notes the version where it was verified. |
| E-S7  | [FIXED]      | CLI section adds the `--qubits 0 1 --type 2q → pair (qubits[0], qubits[1])` behavior note plus the pointer to `run_2q_xeb_workflow(pairs=[...])` for non-trivial cases. |
| F-S1  | [FIXED]      | `uniqc task status TASK_ID` → `uniqc task show TASK_ID` in cli-guide.md and troubleshooting.md; `uniqc result TASK_ID --wait` documented for the wait-and-fetch workflow. Verified via `uniqc task --help`. |
| F-S2  | [FIXED]      | SKILL.md "Names To Remember" gained the `uniqc gateway start/status/stop/restart` bullet; verified via `uniqc gateway --help`. |
| F-S3  | [FIXED]      | "v0.0.9" replaced by "current 0.0.11.x" / "current release" in SKILL.md, best-practices.md, circuit-building.md, pytorch-integration.md, calibration-qem.md, timeline-visualization.md, cli-guide.md, troubleshooting.md. Verified via `python -c "import importlib.metadata; print(m.requires('unified-quantum'))"` that `[all]` still does not include quafu — the Quafu-deprecated bullet was kept and re-anchored to the current release. |
| F-S4  | [FIXED]      | cli-guide.md notes that Quark requires `QUARK_API_KEY` (not `token`) and that `uniqc config validate` enforces it via `PLATFORM_REQUIRED_FIELDS`. |
| F-S5  | [FIXED]      | `python -c "issubclass(StaleCalibrationError, UnifiedQuantumError)"` returned `False`; troubleshooting.md and calibration-qem.md both note "directly inherits from `Exception` — catch explicitly." |
| F-S6  | [FIXED]      | pytorch-integration.md adds the runnable `QuantumLayer(circuit=qc, expectation_fn=expectation, init_params=torch.zeros(1))` snippet plus the `param_names` / signature / `n_outputs` / `shift=π/2` notes. |
| F-S7  | [FIXED]      | examples/cli_demo.sh switched from `mktemp -d` to `DEMO_DIR="${UNIQC_DEMO_DIR:-./.uniqc-demo}"`, `mkdir -p`, no `trap rm -rf`, and prints the path at the end. `bash -n` clean. |

## Mirror status

```
$ diff -rq quantum-computing.skill/skills/uniqc-basic-usage/ .agents/skills/uniqc-basic-usage/
(no output — trees identical)
```

## Verification commands run

* `python -c "import uniqc; print(uniqc.__version__)"` → `0.0.11.dev10`
* `python -c "from uniqc.visualization.timeline import TimelineSchedule; ..."` → confirmed fields
* `python -c "from uniqc import StaleCalibrationError, UnifiedQuantumError; print(issubclass(...))"` → `False`
* `python -c "import importlib.metadata as m; print(m.requires('unified-quantum'))"` → `[all]` excludes quafu
* `python -c "from uniqc.qem import M3Mitigator; ... M3Mitigator(calibration_result=...)"` → works
* `python -c "from uniqc import find_backend; find_backend('dummy:originq:WK_C180')"` → `ValueError`
* `python -c "import inspect; print(inspect.signature(find_cached_results))"` → `result_type=` keyword
* `python -c "import inspect; print(inspect.signature(xeb_workflow.run_2q_xeb_workflow))"` → `pairs=` keyword
* `uniqc task --help` → `show` (no `status` subcommand)
* `uniqc calibrate xeb --help` → no `--parallel` flag
* `uniqc gateway --help` → `start`, `stop`, `restart`, `status`
* `python -m py_compile examples/cloud_submission.py` → OK
* `bash -n examples/cli_demo.sh` → OK
* `python -c "from uniqc import Circuit, Parameter; ..."` → F-S6 snippet executes
