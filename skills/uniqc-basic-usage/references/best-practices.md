# 当前最佳实践参考

UnifiedQuantum 0.0.11.x（当前 release）文档的"最佳实践"章节是一组已执行 notebooks，用于发布前验证主路径：配置、后端缓存、裸 Circuit、Named Circuit、虚拟/本地后端、API/CLI 提交（含 Quark）、云后端 dry-run 模板、变分线路、Torch 集成、Calibration/QEM、XEB workflow 和 timeline visualization。

## 首选导入与模块边界

新代码优先从 `uniqc` 顶层导入常用对象：

```python
from uniqc import Circuit, compile, dry_run_task, submit_task, wait_for_result
from uniqc import BackendInfo, Platform, QubitTopology
from uniqc import calculate_expectation, hea, qaoa_ansatz, uccsd_ansatz
from uniqc import M3Mitigator, ReadoutEM, QuarkOptions, DummyOptions
```

只有在需要特定子模块能力时才使用深层路径，例如 `uniqc.simulator.OriginIR_Simulator`、`uniqc.config`、`uniqc.torch_adapter`、`uniqc.calibration`、`uniqc.qem`、`uniqc.algorithms.workflows`、`uniqc.visualization`。配置属于项目级能力，新代码应优先使用 `uniqc.config`；`uniqc.backend_adapter.config` 是纯 re-export shim，只作为兼容入口理解。

不要在新代码里依赖旧入口：`uniqc.transpiler`、`uniqc.task`、`uniqc.qasm`、`uniqc.originir`、`uniqc.pytorch`、`uniqc.analyzer`。

## 最稳的用户路径

1. 用 `Circuit()` 构建线路，显式测量需要的 qubit。
2. 导出 `originir`，必要时也导出 OpenQASM 2.0。
3. 本地用 `OriginIR_Simulator()` 或 `uniqc simulate` 验证概率/采样结果。
4. 用 `backend="dummy"` 跑通 API submit/wait/result，或用 `uniqc submit -p dummy --wait` 跑通 CLI。
5. 如果需要拓扑约束，改用 `dummy:virtual-line-N` 或 `dummy:virtual-grid-RxC`。
6. 如果需要真实芯片拓扑和标定噪声，改用 `dummy:<platform>:<backend>`，例如 `dummy:originq:WK_C180`。
7. 真机提交前先 `dry_run_task(...)` 或 `uniqc submit --dry-run`，再小 shots 提交。

## Dummy Backend 语义

- `dummy`: 无约束、无噪声的本地虚拟机，适合最快功能检查。
- `dummy:virtual-line-N`: N 比特线性拓扑，无噪声。
- `dummy:virtual-grid-RxC`: R*C 比特网格拓扑，无噪声。
- `dummy:<platform>:<backend>`: 规则型 backend id；提交时按真实 backend 拓扑和门集 compile/transpile，保存编译后线路，再用本地含噪 dummy 执行。

`dummy:<platform>:<backend>` 不会作为独立 backend 出现在 `uniqc backend list` 或 WebUI backend 卡片中。

## CLI 与安装

CLI 首选入口是 `uniqc`，模块入口是 `python -m uniqc.cli`。不要再推荐 `python -m uniqc`。

CLI 的渐进式提示路径是 `--ai-hints` / `--ai-hint`，也可以用 `UNIQC_AI_HINTS=1` 或 `uniqc config always-ai-hint on` 默认开启。`workflow` 是文档中的工作流说明，不要假设存在 `uniqc workflow` 子命令；需要下一步建议时让 agent 读取 command help 和 AI hints。

AI Agent 使用时建议一并安装本仓库技能：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill --agent codex --skill '*'
npx skills add IAI-USTC-Quantum/quantum-computing.skill --agent claude-code --skill '*'
```

IBM Quantum 如需代理，优先写入配置文件而不是只依赖环境变量：

```bash
uniqc config set ibm.proxy.https http://127.0.0.1:7890
uniqc config set ibm.proxy.http http://127.0.0.1:7890
uniqc config validate
```

安装默认建议：

```bash
uv tool install unified-quantum
uv pip install unified-quantum
```

按功能安装 extras：

- OriginQ: `unified-quantum[originq]`
- Quark: `unified-quantum[quark]`（Python ≥ 3.12）
- IBM/Qiskit: `unified-quantum[qiskit]`
- 高级模拟: `unified-quantum[simulation]`
- 可视化: `unified-quantum[visualization]`
- PyTorch: `unified-quantum[pytorch]`
- 全部常规 extras: `unified-quantum[all]`

Quafu/`pyquafu` 已 deprecated，且不在 `[all]` 中；只有用户明确需要 Quafu 时才单独安装 `[quafu]`，并提示它可能引入 `numpy<2` 约束。

## 发布前/维护者路径

维护者全量开发环境使用：

```bash
uv sync --extra all --group dev --group docs --upgrade
uv run pytest uniqc/test
uv run pytest uniqc/test --real-cloud-test
uv run python scripts/generate_best_practice_notebooks.py
```

不要把 `uv sync --all-extras` 当成默认维护者命令；deprecated Quafu/`pyquafu` 可能在当前 Python 上阻塞依赖解析。只有明确测试 Quafu 时才单独启用 `[quafu]`。

真实云平台测试中，读取后端列表、验证 token、查询 status/API 默认应可跑；会实际提交量子线路的测试才放在 `--real-cloud-test` 下。

## Calibration、QEM、XEB

CLI 标定命令：

```bash
uniqc calibrate xeb --qubits 0 1 2 3 --type 1q --backend dummy --shots 1000
uniqc calibrate readout --qubits 0 1 --backend dummy --shots 1000
uniqc calibrate pattern --qubits 0 1 2 3 4 5
```

Python API：

```python
from uniqc import ReadoutEM, M3Mitigator, StaleCalibrationError
from uniqc.algorithms.workflows import xeb_workflow, readout_em_workflow
```

- Calibration 结果写入 `~/.uniqc/calibration_cache/`。
- `uniqc.calibration` 负责生成和保存标定数据（`XEBResult`、`ReadoutCalibrationResult`）。
- `uniqc.qem` 负责读取标定数据并执行 error mitigation，包含 TTL 新鲜度检查（`max_age_hours`）。
- `ReadoutEM` 是统一接口，自动分派 1q/2q/多qubit 标定；`M3Mitigator` 提供混淆矩阵线性反转。
- XEB workflow 走 `from uniqc.algorithms.workflows import xeb_workflow`，例如 `xeb_workflow.run_1q_xeb_workflow(...)`。
- readout_em workflow 走 `from uniqc.algorithms.workflows import readout_em_workflow`。

示例默认用 `backend="dummy"` 做无约束、无噪声发布检查；要验证真实芯片标定噪声路径时才改成 `backend="dummy:originq:WK_C180"`。
