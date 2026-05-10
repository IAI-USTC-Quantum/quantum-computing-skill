---
name: uniqc-cloud-submit
description: "Use when the user wants an end-to-end cloud / real-hardware submission with UnifiedQuantum: validate API keys, ask for / load a quantum-program file (.originir / .qasm / .py), dry-run, `submit_task`, query status, `wait_for_result`. Also covers writing a circuit in Python and persisting it as a quantum-program file. Apply for OriginQ / Quafu / Quark / IBM and chip-backed dummy backends."
---

# Uniqc Cloud Submission Skill

This skill is the **operational** counterpart to `uniqc-basic-usage`. Use it when
the user wants to actually push a circuit to a backend (real hardware, cloud
simulator, or chip-backed dummy) and then track the task to results.

The end-to-end shape is always the same:

1. **Health-check** the configured platforms (`uniqc config validate` /
   `uniqc config list`).
2. **Pick or build** a quantum-program file — `.originir`, `.qasm`,
   or a Python script that constructs a `Circuit` and writes one of the above.
3. **Dry-run** the submission to catch backend / IR / topology errors locally.
4. **Submit** via `uniqc submit` (CLI) or `submit_task` / `submit_batch`
   (Python). Always returns a uniqc-managed task id `uqt_<32-hex>` (uniqc
   ≥ 0.0.12).
5. **Query** with `uniqc task show <uid>` / `query_task(uid)`.
6. **Wait & fetch** with `uniqc result <uid> --wait` /
   `wait_for_result(uid, timeout=...)`.

> ⚠️ The user may say "use `uniqc doctor`" — there is **no** `uniqc doctor`
> subcommand. Use `uniqc config validate` (and `uniqc config list`) instead.
> Tell the user, then proceed.

## First decision — branch by user intent

| User goal                                              | Read first                                              |
| ------------------------------------------------------ | -------------------------------------------------------- |
| "Check my keys / why is my submit failing on auth?"   | [references/health-check.md](references/health-check.md) |
| "I have a circuit in Python — how do I save it?"      | [references/authoring-program-files.md](references/authoring-program-files.md) |
| "I have an `.originir` / `.qasm` file — submit it."   | [references/submit-and-poll.md](references/submit-and-poll.md) |
| "How do I batch many circuits in one task id?"        | [references/submit-and-poll.md](references/submit-and-poll.md) (`submit_batch` section) |
| "What does the resulting `uqt_*` id map to?"          | [references/task-ids-and-shards.md](references/task-ids-and-shards.md) |

For result inspection / plotting after `wait_for_result`, hand off to
the **`uniqc-result-analysis`** skill.

## Recommended interactive flow when the user has not given a circuit

If the user asks "submit a circuit for me" without a concrete file, **do not
guess**. Ask once:

> Which circuit do you want to submit? You can give me one of:
>
> 1. A path to an `.originir` / `.qasm` file, or
> 2. A path to a `.py` script that builds and prints a `Circuit`, or
> 3. A short description ("Bell state, 2 qubits") — I'll generate the file.
>
> Also which backend? (e.g. `dummy`, `originq:WK_C180`, `quark:Baihua`, `ibm:ibm_fez`)

Then:
1. If option 3, write the circuit to `circuit.py` + dump
   `circuit.originir` to `circuit.originir` (and `circuit.qasm` to
   `circuit.qasm` for IBM/Quafu).
2. Run `uniqc config validate` and `uniqc config list` — make sure the chosen
   platform shows `Configured`.
3. Always **dry-run before real submit**.
4. Show the user the `uqt_*` id and explain how to re-attach later.

## Practical defaults

- **Always** pass `backend=` as a single `"<platform>:<backend_name>"` string
  to `submit_task` — it works for every adapter and matches `dry_run_task`.
  Two-arg form (`backend="originq", backend_name="WK_C180"`) still works.
- For OriginQ real hardware, **compile first** and pass the compiled
  `Circuit`:
  ```python
  from uniqc import compile, find_backend, submit_task
  bi = find_backend("originq:WK_C180")
  c_native = compile(my_circuit, bi, level=2)
  uid = submit_task(c_native, backend="originq:WK_C180", shots=200)
  ```
  If you skip the compile, `local_compile=1` (default) does it for you via
  qiskit (requires `unified-quantum[qiskit]`); set `local_compile=0` to skip.
- For Quafu / Quark / IBM: same single-string `backend=` works,
  shots small (≤ 200) for the first real attempt.
- Never log full tokens. Read them from `~/.uniqc/config.yaml` via
  `uniqc.config.get_*_config(...)`, not from the user prompt.
- All submits return a single string id of the form `uqt_<32-hex>` (36 chars).
  Treat platform-native ids (OriginQ MD5, IBM `cp...`, Quafu UUID) as
  legacy — they still resolve in `query_task` but emit `DeprecationWarning`.
- `wait_for_result(uid)` returns one `UnifiedResult` for single-circuit tasks
  and `list[UnifiedResult]` for batches — branch on `isinstance(_, list)`.

## CLI cheat sheet

```bash
# 0. health
uniqc config validate
uniqc config list

# 1. authoring (Python -> file)
python build_circuit.py            # writes circuit.originir / circuit.qasm

# 2. dry-run (no quota spent)
uniqc submit circuit.originir --backend dummy:local:simulator --shots 1000 --dry-run
uniqc submit circuit.originir --backend originq:WK_C180 --shots 200 --dry-run

# 3. real submit
uid=$(uniqc submit circuit.originir --backend originq:WK_C180 --shots 200)
echo "$uid"                            # uqt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 4. inspect status / shards
uniqc task show "$uid"
uniqc task shards "$uid"               # platform task id mapping

# 5. wait & fetch
uniqc result "$uid" --wait
```

## Python cheat sheet

```python
from uniqc import (
    Circuit, compile, find_backend,
    dry_run_task, submit_task, submit_batch,
    query_task, wait_for_result, get_platform_task_ids,
)

# 1. authoring
c = Circuit(2); c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)
open("circuit.originir", "w").write(c.originir)
open("circuit.qasm", "w").write(c.qasm)

# 2. dry-run
check = dry_run_task(c, backend="originq:WK_C180", shots=100)
if not check.success:
    raise RuntimeError(check.error or check.details)

# 3. submit (compile first for chip-backed backends)
bi = find_backend("originq:WK_C180")
c_native = compile(c, bi, level=2)
uid = submit_task(c_native, backend="originq:WK_C180", shots=200)
print(uid)                              # uqt_xxxx...

# 4. inspect
info = query_task(uid)
shards = get_platform_task_ids(uid)     # list[TaskShard]

# 5. wait & fetch
result = wait_for_result(uid, timeout=300)   # -> UnifiedResult
print(result.counts, result.shots, result.platform)
```

## Failure-mode quick reference

| Symptom                                                         | Likely cause / fix                                                                                                  |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `ConfigValidationError: Missing token`                          | `uniqc config set <platform>.token <KEY>` (Quark uses `quark.QUARK_API_KEY`, not `token`).                          |
| `Package 'pyqpanda3' is required for this feature`              | `pip install unified-quantum[originq]`. For IBM and chip-backed dummy: `[qiskit]`. For Quark: `[quark]` (Py ≥ 3.12). |
| `CompilationFailedError` on `dummy:originq:<chip>` / IBM        | `pip install unified-quantum[qiskit]`.                                                                              |
| `ValueError: Backend 'originq:wk_c180' not found`               | OriginQ chip names are case-sensitive on real submit; use `WK_C180`. Lowercase only works on the `dummy:originq:…` path. |
| `UnsupportedGateError`                                          | Wrong IR for that platform (OriginQ wants OriginIR; Quafu/IBM want OpenQASM 2.0). uniqc auto-converts at submit; check that your file actually parses. |
| `DeprecationWarning` from `query_task` with platform id         | You passed the legacy platform id; use the `uqt_*` returned by `submit_task`/`submit_batch` going forward.          |
| `wait_for_result` returns `None`                                | Job failed on the platform side — inspect `query_task(uid).status` and `query_task(uid).error`. For batches the failed shard is reported per-element. |

## Names to remember

- CLI: `uniqc config validate`, `uniqc submit`, `uniqc task show / shards`,
  `uniqc result <uid> --wait`, `uniqc backend list / show / chip-display`.
- Python: `dry_run_task`, `submit_task`, `submit_batch`, `query_task`,
  `wait_for_result`, `get_platform_task_ids` (all top-level `uniqc.*`).
- Config helpers: `uniqc.config.get_originq_config()`,
  `get_quafu_config()`, `get_quark_config()`, `get_ibm_config()`,
  `has_platform_credentials("originq")`.
- Caches: `~/.uniqc/config.yaml`, `~/.uniqc/cache/tasks.sqlite`,
  `~/.uniqc/cache/backends.json`, `~/.uniqc/backend-cache/*.json`.

## Response style

- Lead with the runnable command/script that gets the user from
  "I have a circuit" to "I have a `uqt_*`" in three steps.
- Always show the dry-run before the real submit.
- After `wait_for_result`, hand off to the result-analysis skill rather
  than re-explaining `UnifiedResult`.
