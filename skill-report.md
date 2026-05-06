# quantum-computing.skill ↔ uniqc 0.0.11.dev10 不匹配报告

- 验证范围：`quantum-computing.skill/skills/uniqc-basic-usage/`（`SKILL.md` + `references/*.md` + `examples/*` + `scripts/`）
- 配套代码版本：`uniqc 0.0.11.dev10`
- 环境：`/home/agony/projects/quantum-simulator-paper-new/.venv-test`
- 本报告仅列举 skill 端的不匹配；uniqc 本体的代码/文档问题见 `uniqc-report.md`

> 注：`.agents/skills/uniqc-basic-usage/...` 是项目内同份副本，本节涉及 `references/*` 修改时需同步两侧。

---

## A 域（circuit / compile / visualization）

### A-S1 [high · 片段不可运行] `SKILL.md` 的 Compile 片段 API 已过时
- 文件：`quantum-computing.skill/skills/uniqc-basic-usage/SKILL.md:99-105`
- 现象：
  ```python
  from uniqc import compile, TranspilerConfig
  result = compile(circuit, backend_info, config=TranspilerConfig(level=2))
  compiled_circuit = result.output
  ```
  `compile()` 没有 `config=` 关键字（→ TypeError），实际返回 `Circuit | str`，没有 `.output`。
- 建议：
  ```python
  from uniqc import compile
  compiled = compile(circuit, backend_info, level=2,
                     basis_gates=['cz','sx','rz'])  # 直接是 Circuit
  ```

### A-S2 [high · 片段不可运行] `references/timeline-visualization.md` 同样的 compile 错例
- 文件：`references/timeline-visualization.md:51-56`
- 现象：
  ```python
  result = compile(circuit, backend_info, config=TranspilerConfig(level=2))
  schedule = schedule_circuit(result.output, backend_info=backend_info)
  ```
  `config=` / `.output` 均不存在。
- 建议：改成
  ```python
  compiled = compile(circuit, backend_info, level=2)
  schedule = schedule_circuit(compiled, backend_info=backend_info)
  ```

### A-S3 [medium · 片段不可运行] `BackendInfo.get(...)` 不存在
- 文件：`references/timeline-visualization.md:155-159`
- 现象：
  ```python
  from uniqc import BackendInfo
  backend = BackendInfo.get("origin:wuyuan:WK_C180")
  # AttributeError: type object 'BackendInfo' has no attribute 'get'
  ```
  `BackendInfo` 是 dataclass，没有 `get/load/find` classmethod。同时 `origin:wuyuan:WK_C180` 这个 ID 也已弃用。
- 建议：
  ```python
  from uniqc import find_backend
  backend = find_backend("originq:WK_C180")
  ```

### A-S4 [medium · 描述错误] `TimelineSchedule` 字段描述与实现不符
- 文件：`references/timeline-visualization.md:62-74`
- 现象：文档声明 `gates: list[TimelineGate]; total_duration; n_layers; unit + property time_points, resources`；实际 `gates: tuple[TimelineGate,...]; qubits: tuple[int,...]; total_duration; unit; gate_durations + property time_points (only)`。无 `n_layers`、`resources`（`resources` 仅在 `TimelineGate` 上）。
- 建议：同步字段列表；如使用方需要 `n_layers`，可用 `max(g.layer for g in sched.gates)+1` 计算并在 docs 注明。

### A-S5 [medium · 片段过时/描述不完整] `gate_durations` 单独可用的暗示
- 文件：`references/timeline-visualization.md:13-17, 116-124, 168`
- 现象：`plot_time_line_html(circuit, gate_durations={...})` / `schedule_circuit(circuit, gate_durations={...})` 对纯逻辑 `Circuit` 都因 `compile()` 进基门集而抛 `CompilationFailedException`（缺 qiskit）；第 168 行 “circuit_to_html 和 plot_time_line_html 不需 matplotlib” 也暗示无重型依赖。
- 建议：在 Quick Path 与 Notes 中明确 “调度逻辑线路需要 `unified-quantum[qiskit]`”；或先 `compile(..., basis_gates=[...])` 再传给 `schedule_circuit`。

---

## B 域（simulators）

### B-S1 [low · 内容遗漏] `references/simulators.md` MPS 段未标注 `chi_max` 默认
- 现象：skill 给的示例 `MPSConfig(chi_max=64, ...)` 与实际默认相同，但没明确说「不传时默认 64」；上游 `mps_simulator.md` 又把默认写成 256（见 `uniqc-report.md` B5）。两处叠加易让用户以为不传等价于 256。
- 建议：在 skill 里直接写 “`chi_max` 默认 64”，并提示文档存在数字偏差，避免 LLM 复述时误传 256。

### B-S2 [low · 内容遗漏] `OriginIR_Simulator` 方法名易混淆
- 文件：`references/simulators.md`
- 现象：skill 没明确列出方法。`OriginIR_Simulator` **没有** `simulate(...)` 方法，只有 `simulate_shots(ir, shots)` / `simulate_pmeasure(ir)` / `simulate_statevector(ir)` / `simulate_density_matrix(ir)`。新人按直觉写 `sim.simulate(...)` 会 AttributeError。
- 建议：列出全部方法，并给出最小可运行示例（`simulate_shots(ir, shots)`）。

---

## C 域（algorithms）

### C-S1 [low · 文档] `calculate_expectation` 仅支持 `Z`/`I` Hamiltonian
- 文件：`references/variational-algorithms.md` / `references/h2-molecular-simulation.md`
- 现象：传 `"Z0 Z1"` 这种带索引的 Pauli string 会 `ValueError: The Hamiltonian input must be a str (only containing Z or I or z or i)`。其他 uniqc API（`qaoa_ansatz` 的 `cost_hamiltonian`、`pauli_expectation`）使用的语法不一样。
- 建议：在 skill 中加一行 “`calculate_expectation` 只接受位置式 `Z/I` 串（长度 == n_qubit），不要把 `qaoa_ansatz` 的 Pauli 串直接喂进来”。

### C-S2 [low · 文档] `calculate_multi_basis_expectation` 语义易被误读
- 现象：basis label `"XX"` 被路由到 `calculate_exp_X(... qubit_index=0)`，只算 qubit 0 的 ⟨X⟩，**不是** ⟨X⊗X⟩。
- 建议：skill 若展示该 API，加一句 “basis label 仅用首字符决定 X/Y/Z，且只针对单个 qubit；要算 ⟨X⊗X⟩ 请用 `pauli_expectation`”。

### C-S3 [low · troubleshooting 增补] `Circuit.originir` 是属性，不是方法
- 现象：skill 内未发现 `to_originir()` 残留，但常见踩坑（用户把 `.originir` 写成 `.to_originir()`）值得在 troubleshooting 列一行。
- 建议：在 `references/circuit-building.md` 或 `troubleshooting.md` 加一句 “用 `c.originir`（属性）而不是 `c.to_originir()`”。

---

## D 域（backend / cloud）

### D-S1 [high · 片段不可运行] `examples/cloud_submission.py` 的 Bell 提交在 originq 真机上立刻报错
- 文件：`references/cloud-platforms.md`、`examples/cloud_submission.py`
- 现象：示例
  ```python
  task_id = submit_task(circuit, backend="originq", backend_name="WK_C180", shots=100)
  ```
  其中 `circuit` 是 `Circuit(2); h(0); cnot(0,1); measure(0,1)`。实测因 H/CNOT 不在 `[CZ,RZ,SX]` 直接 `UnsupportedGateError`。skill 没有说要先 `compile()`；且 `auto_compile` 与 `UNIQC_SKIP_VALIDATION` 现状（见 `uniqc-report.md` D2）也没说明。
- 建议：示例先做 `circuit = compile(circuit, find_backend('originq:WK_C180'))`，或换成已经是 native gate 的 Bell-equivalent 形式；`troubleshooting.md` 里说明 `auto_compile/UNIQC_SKIP_VALIDATION` 的真实行为。

### D-S2 [high · 描述错误] skill 暗示 `wait_for_result` 返回 `{counts, probabilities}`
- 文件：`examples/cloud_submission.py::print_result`
- 现象：脚本同时处理 `result["counts"]` / `result["probabilities"]`，给读者「返回 UnifiedResult-like dict」的印象；但实际 dummy 路径返回 `{bitstring: int}`，根本没有 `counts` 这个 key。
- 建议：示例 docstring 明确 “返回值是 `dict[bitstring, int]`（counts dict）”；如未来 uniqc 修成 `UnifiedResult`，同步更新 skill。

### D-S3 [medium · 缺 extras 提示] `dummy:originq:<chip>` 在 skill 中无 extras 提示
- 文件：`references/cloud-platforms.md` ~L110、`SKILL.md:47`
- 现象：
  ```python
  noisy_task = submit_task(circuit, backend="dummy:originq:WK_C180", shots=1000)
  ```
  该路径要求 `unified-quantum[qiskit]` 与芯片 cache 命中，未装 qiskit 时 `CompilationFailedException`。
- 建议：在描述里加 “需要 `unified-quantum[qiskit]` 才能启用 chip-backed dummy 路径，否则 `CompilationFailedException`”。

### D-S4 [low · 描述误导] `find_backend('dummy:originq:WK_C180')` 在 skill 中暗示可发现
- 现象：skill 行文 “real-backend mirror `dummy:originq:WK_C180`” 容易被理解为 `find_backend` 可解析；实际抛 `ValueError`，仅 `submit_task` 接受。
- 建议：明确 “这是 submit-only 模式，不出现在 `find_backend / list_backends` 结果里”。

### D-S5 [medium · 缺示例 + 性能告警] `RegionSelector` 用法 / 大芯片性能未提示
- 文件：`references/cloud-platforms.md`
- 现象：skill 提到 `RegionSelector` 但没给最小可跑示例（`ChipCharacterization` 在 `uniqc.cli.chip_info`，**不在** top-level）。`find_best_1D_chain` 在 `WK_C180` 上 30 s 不返回（`uniqc-report.md` D6）。
- 建议：补一个 ≤8 行示例（含 `from uniqc.cli.chip_info import ChipCharacterization` + `from_dict(json)`），并标注大芯片 1D 性能限制，推荐用 `find_best_2D_from_circuit(max_search_seconds=...)`。

### D-S6 [low · 内容遗漏] `BackendOptionsFactory` 暴露的方法与 skill 文风不符
- 现象：skill 列出 `BackendOptionsFactory` 但未说明 API 是 `create_default / from_kwargs / normalize_options`；且 `from_kwargs(platform, kwargs)` 不是 `**kwargs`。
- 建议：在 SKILL.md “BackendOptions” 段加 `BackendOptionsFactory().create_default('originq')` 是推荐入口。

### D-S7 [medium · 误导] skill 没区分 cloud simulator / 真机的 extras 与 token 需求
- 文件：`references/cloud-platforms.md`
- 现象：示例 `submit_task(..., backend='originq', backend_name='full_amplitude'|'WK_C180')` 都需要 `pyqpanda3`。当前环境（valid OriginQ key）依然不能提交，因为 `unified-quantum[originq]` extras 缺失。
- 建议：文档头部明确 “originq 平台所有提交路径（含 cloud sim）都需要 `pip install unified-quantum[originq]`”。

### D-S8 [low · 描述缺失] `is_dummy_mode()` 语义易误用
- 现象：用户读到 “dummy mode” 会期望运行时 `os.environ['UNIQC_DUMMY']='1'` 切换；实际不行（`uniqc-report.md` D3）。
- 建议：skill 明确 “`UNIQC_DUMMY` 必须在 import 前设置”，或等 uniqc 修复后再更新。

### D-S9 [high · 描述错误] `cloud-platforms.md` / `cloud_submission.py` 暗示 `ORIGINQ_API_KEY / QUAFU_API_TOKEN / IBM_TOKEN` 等环境变量被 uniqc 自动读取
- 文件：`references/cloud-platforms.md:49-58`、`examples/cloud_submission.py:85,168`
- 现象：源码中 `uniqc/` 不读取这些环境变量，只用到 `UNIQC_PROFILE / UNIQC_DUMMY / UNIQC_SKIP_VALIDATION / HTTP(S)_PROXY`。`cloud_submission.py` 的 `_sync_env_to_config` 只是脚本里的便利函数（把 env 回写进 `~/.uniqc/config.yaml`），不是「环境变量 → adapter」自动桥接。
- 建议：明确写 “`uniqc` 不直接读取这些环境变量；要 portable，请用 `uniqc config set originq.token <TOKEN>` 写入 `~/.uniqc/config.yaml`，或在脚本里先把 env 同步到 config”。

---

## E 域（calibration / QEM）

### E-S1 [high · API 不存在] `xeb_workflow.run_*` 签名错误
- 文件：`references/calibration-qem.md`
- 现象：skill 写 `xeb_workflow.run_1q_xeb_workflow(adapter=dummy_adapter, qubits=...)`；实际函数没有 `adapter` 参数，第一个参数是 `backend: str`（如 `"dummy"` / `"dummy:virtual-line-3"`）。`run_2q_xeb_workflow` 同理；参数名是 `pairs=`，skill 写成 `qubit_pairs=`。
- 建议：
  ```python
  result = xeb_workflow.run_1q_xeb_workflow(
      backend="dummy:virtual-line-3", qubits=[0,1,2,3],
      shots=1000, depths=[5,10,20,40], use_readout_em=True,
  )
  # 返回 dict[int, XEBResult]，不是单个 XEBResult
  ```

### E-S2 [high · API 不存在] `readout_em_workflow.apply_readout_em` 签名错误
- 现象：skill 写 `apply_readout_em(adapter, raw_counts, measured_qubits=[0,1])`；实际签名 `apply_readout_em(result, readout_em, measured_qubits)`，第 1 个参数是 task `result` 对象，第 2 个必须先有 `ReadoutEM` 实例。
- 建议：示例改为先 `em = run_readout_em_workflow(backend=..., qubits=...)`，再 `em.mitigate_counts(raw, measured_qubits=...)`；如确需 `apply_readout_em`，给出 `result` 来源。

### E-S3 [medium · 错误关键字] `find_cached_results(backend="dummy", type="readout_1q")`
- 现象：实参名是 `result_type`，不是 `type`，skill 写法直接 `TypeError`。
- 建议：更正为 `find_cached_results(backend="dummy", result_type="readout_1q")`。

### E-S4 [medium · API 不存在] `uniqc calibrate xeb --parallel`
- 现象：skill CLI 例子里有 `--parallel`。`uniqc calibrate xeb --help` 没有该选项；并行 XEB 走 `xeb_workflow.run_parallel_xeb_workflow` 或 `--type both`/具体 qubit pair。
- 建议：删除该例子，或改为 Python `run_parallel_xeb_workflow(backend=..., target_qubits=...)`。

### E-S5 [medium · 字段不全] `XEBResult` 字段描述
- 现象：skill 列出 `fidelity_per_layer/fit_a/fit_b/fit_r/depths/n_circuits/shots/backend`，但实际 dataclass 还有 `calibrated_at, type, qubit, pairs`（`type` 取值 `xeb_1q/xeb_2q/xeb_parallel`）。
- 建议：补全字段。

### E-S6 [medium · 风险] `M3Mitigator(calibration_result=readout_result)` 例子在当前实现下抛 TypeError
- 现象：触发 `uniqc-report.md` E1 的 bug。
- 建议：在源码修复前，把例子改成 `cache_path=...` 形式，或注明 “需要 dict 形式的 result，可由 `ReadoutCalibrator.calibrate_1q()` 返回”，并加 known-issue 链接。

### E-S7 [low · 措辞] CLI `--qubits 0 1 --type 2q` 行为
- 现象：skill 说 “`--type 2q` 在 pair (0,1) 上跑”，与 help 一致；但 `--qubits` 个数 >2 时实际行为（pair 切分 vs 报错）skill 没写明。
- 建议：补一句或指向 `run_2q_xeb_workflow`。

---

## F 域（CLI / config / torch）

### F-S1 [high · API 不存在] 推荐 `uniqc task status TASK_ID`
- 文件：`references/cli-guide.md:134`、`references/troubleshooting.md:84-85`
- 现象：实际 CLI 没有 `task status` 子命令；执行报 `No such command 'status'`。
- 建议：替换成 `uniqc task show TASK_ID`（缓存视图）或 `uniqc result TASK_ID --wait`（等待并取结果）。troubleshooting 第 4 步也应改为 `uniqc task show`。

### F-S2 [medium · 内容遗漏] `SKILL.md` Names To Remember 与 `cli-guide` 都没列 `uniqc gateway`
- 文件：`SKILL.md:128-146`、`references/cli-guide.md`
- 现象：CLI 已有 `uniqc gateway start/stop/restart/status`（一个网关 web UI），skill 完全没提及；新用户问 “怎么起 web UI” 会被引导成 “没有”。
- 建议：在 “Names To Remember” 加一段 `uniqc gateway`，并简短说明用途与端口默认值。

### F-S3 [low · 版本陈旧] `SKILL.md` 仍写 “uniqc v0.0.9 has six common surfaces”
- 文件：`SKILL.md:12, 21, 41-58, 126`
- 现象：skill 多处以 0.0.9 为基线（包括 `[all]` 不含 quafu、`python -m uniqc` 不可用 等表述）。0.0.11 行为基本一致，但版本号不更新会让 LLM 在排错时给出过时答复。
- 建议：把 `v0.0.9` 改为 “current 0.0.11.x” 或去掉具体版本号。

### F-S4 [low · cross-link 缺失] `uniqc config set quark.QUARK_API_KEY ...`
- 文件：`references/cli-guide.md:157`、`SKILL.md:54`
- 现象：实测 `update_platform_config` 把 `QUARK_API_KEY` 与 `token` 当作并列字段；但 `validate_config()` 中 `PLATFORM_REQUIRED_FIELDS["quark"] = ["QUARK_API_KEY"]`，只有这一种命名通过 validate。skill 内部一致，但 docs/cli/config.md 没说，cross-link 缺失。
- 建议：在 cli-guide 加一句 “Quark 必须用 `QUARK_API_KEY`，否则 `uniqc config validate` 报 missing field”。

### F-S5 [low · 措辞] `references/best-practices.md:107` 写 `from uniqc import ... StaleCalibrationError`
- 现象：能 import，但其父类是 `Exception`，不是 `UnifiedQuantumError`；troubleshooting 把它和 `UnifiedQuantumError` 一并列入「通用异常表」可能让用户误以为可以用 `except UnifiedQuantumError` 兜底。
- 建议：troubleshooting 表格里给 `StaleCalibrationError` 加注 “直接继承 `Exception`，需要显式捕获”。

### F-S6 [low · 缺签名] `references/pytorch-integration.md` 没列 `QuantumLayer` 构造参数
- 文件：`references/pytorch-integration.md:47-62`
- 现象：skill 用文字描述「两个核心输入：参数化电路模板 + expectation 函数」，没给签名；新用户照 `docs/guide/pytorch.md` 抄就会踩 F7（`circuit_template=` 不存在）。
- 建议：补最小可运行的真实签名示例：
  ```python
  layer = QuantumLayer(circuit=template, expectation_fn=ev_fn,
                       init_params=torch.zeros(n))
  ```
  并明确 “参数名称从 `circuit._parameters` 自动读取，不要再传 `param_names`”。

### F-S7 [low · 脚本健壮性] `examples/cli_demo.sh` 用 `mktemp -d` 写到 `/tmp`
- 文件：`examples/cli_demo.sh:6`
- 现象：完全在 `/tmp` 创建文件。在限制 `/tmp` 的环境（CI/sandbox）会失败；CI 里也容易因 cleanup 时序留尾巴。
- 建议：默认放到 `${UNIQC_DEMO_DIR:-./.uniqc-demo}`，并在脚本结尾打印路径以便排查。

---

## 总览

| 域 | high | medium | low |
|----|------|--------|-----|
| A circuit/compile/vis | 2 | 3 | 0 |
| B simulators | 0 | 0 | 2 |
| C algorithms | 0 | 0 | 3 |
| D backend/cloud | 3 | 3 | 3 |
| E calibration/QEM | 2 | 3 | 1 |
| F CLI/config/torch | 1 | 1 | 5 |

**优先建议**
1. **修 high 级片段不可运行**：A-S1/A-S2（compile）、D-S1（Bell 提交真机）、D-S2/D-S9（环境变量神话）、E-S1/E-S2（XEB / readout workflow 签名）、F-S1（task status 不存在）。这些用户照 skill 抄就 100% 失败。
2. **修 medium 级 extras / 行为差异**：D-S3/D-S5/D-S7、E-S3/E-S4/E-S5/E-S6 — 与运行环境/缺包路径强相关。
3. **更新版本表述与新增能力**：F-S2（gateway 子命令）、F-S3（版本基线）、A-S4（TimelineSchedule 字段）。
4. **同步 `.agents/skills/uniqc-basic-usage/...` 副本**：本仓库内有同份副本，所有 references 更改都需要 mirror。

> 与 `uniqc-report.md` 联动：A-S1/A-S2 与 uniqc 侧 A4 配套修；D-S2 与 D1 联动；E-S6 与 E1 联动；F-S1 与 F1 联动。一旦上游 API 修复，skill 仍需同步。
