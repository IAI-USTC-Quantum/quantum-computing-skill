# Changelog

All notable changes to the `quantum-computing.skill` package (currently
`uniqc-basic-usage`) are documented here.

## [Unreleased]

## [0.0.12] - 2026-05-07 — UnifiedQuantum 0.0.12 alignment

UnifiedQuantum 0.0.12 引入了**uniqc 自管理的任务 ID 间接层**（breaking）以及**原生批量提交**。Skill 已对齐：

### `SKILL.md`

- 顶部版本字符串改为 0.0.12。
- 新增 cloud-task 顶层注意事项条目，说明 `submit_task` / `submit_batch` 现在统一返回 `uqt_<32-hex>` 的 uniqc 任务 ID，以及 `get_platform_task_ids` / `uniqc task shards` / `GET /api/tasks/{uid}/shards` 三种查 shard 路径，以及 `submit_batch(..., return_platform_ids=True)` 兜底。

### `references/cloud-platforms.md`

- 新增 “uniqc 任务 ID（`uqt_*`）⚠ 0.0.12 起的改动” 章节，覆盖：
  - 为什么这么改（统一平台 ID 格式 + auto-sharding）
  - `get_platform_task_ids` Python API、`uniqc task shards` CLI、`GET /api/tasks/{uid}/shards` REST
  - 兼容性 / 迁移（旧本地缓存自动迁移、`query_task(<平台 ID>)` 仍可用但 `DeprecationWarning`、`return_platform_ids=True` 兜底）
- 批量任务示例改为 `uid = submit_batch(...)` + `wait_for_result(uid)` → `list[UnifiedResult]` 模式。

### `README.md`

- follow-up 版本说明从 0.0.11 升级到 0.0.12，并列出新引入的 IDL / 原生 batch 特性。

## [0.0.11] - 2026-05-07 — UnifiedQuantum 0.0.11 alignment

This release aligns the skill with the four-round audit fixes that landed in
UnifiedQuantum 0.0.11. Every reference page was reviewed against the live API.

### `SKILL.md`

- Added `qpe_circuit` to the algorithm fragments list.
- Documented `pauli_expectation` accepting three input forms (compact `'ZIZ'`,
  indexed `'Z0Z1'`, tuple list `[('Z',0),('Z',1)]`).
- Noted that `basis_rotation_measurement` raises `ValueError` when the input
  circuit is missing `MEASURE`.

### `references/circuit-building.md`

- Removed the stale `iswap` / `rphi` / `phase2q` / `xy` / `uu15`
  `NotImplementedError` warning — these gates now round-trip through QASM2
  via auto-generated `gate def` blocks.

### `references/simulators.md`

- Corrected `get_simulator` signature to `(backend_type, program_type)` to
  match `create_simulator`.
- Documented `dummy:mps:linear-N` MPS dummy backend.

### `references/cloud-platforms.md`

- `dry_run_task` example now uses single-string form `"originq:WK_C180"` and
  notes that the two-arg `(platform, backend)` form still works.
- Removed the deprecated `backend=` kwarg from `wait_for_result` examples.
- Added a note that `OriginQAdapter.translate_circuit` transparently rewrites
  `SX` / `SX.dagger` to `RX(±π/2)` so circuits in the SX basis are accepted
  by the OriginQ remote parser.
- Updated the OriginQ default backend everywhere from `origin:wuyuan:d5` to
  `originq:WK_C180`.
- Replaced `auto_compile` references with the `local_compile` /
  `cloud_compile` integer model and linked to `docs/guide/compile_levels.md`.

### `references/variational-algorithms.md`

- Added `qpe_circuit` to the fragment list.
- Documented `pauli_expectation` 3 input forms.
- Updated `vqd_circuit` references to `vqd_ansatz` (legacy alias still works).
- Added `vqe`, `qaoa`, and `classical_shadow` workflow drivers.

### `references/calibration-qem.md`

- `ReadoutCalibrator` example shows new `timeout=900.0` and
  `poll_interval=10.0` kwargs.
- Documented that `calibrate_1q` / `calibrate_2q` return
  `ReadoutCalibrationResult` dataclasses (with backward-compat dict access).
- Replaced `mitigate_counts` / `mitigate_probabilities` with the new
  `M3Mitigator.apply(UnifiedResult)` / `ReadoutEM.apply(UnifiedResult)`
  pipeline API.
- Noted that ZNE currently raises `NotImplementedError` (placeholder).

### `references/troubleshooting.md`

- Updated dummy / skip-validation guidance: env vars `UNIQC_DUMMY` and
  `UNIQC_SKIP_VALIDATION` are gone — use the `dummy:` backend prefix and the
  `skip_validation=True` kwarg.
- Updated exception names: `CompilationFailedException` →
  `CompilationFailedError`, `IRConversionFailedException` →
  `CircuitTranslationError`.

### Mirror

- `.agents/skills/uniqc-basic-usage/` mirror is kept in sync via rsync.

## [legacy 1.2.009] — UnifiedQuantum 0.0.9
- Initial coverage for `Circuit.get_matrix()`, calibration module, MPS
  simulator preview.

## [legacy 1.2.0] — UnifiedQuantum 0.0.8
- Refocus skill on UnifiedQuantum workflows.
