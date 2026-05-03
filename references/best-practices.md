# v0.0.8 最佳实践参考

UnifiedQuantum v0.0.8 文档的“最佳实践”章节是一组已执行 notebooks，用于发布前验证主路径：配置、后端缓存、裸 Circuit、Named Circuit、虚拟/本地后端、API/CLI 提交、云后端 dry-run 模板、变分线路、Torch 集成、Calibration/QEM 和 XEB workflow。

## 首选导入与模块边界

新代码优先从 `uniqc` 顶层导入常用对象：

```python
from uniqc import Circuit, compile, dry_run_task, submit_task, wait_for_result
from uniqc import BackendInfo, Platform, QubitTopology
from uniqc import calculate_expectation, hea, qaoa_ansatz, uccsd_ansatz
```

只有在需要特定子模块能力时才使用深层路径，例如 `uniqc.simulator.OriginIR_Simulator`、`uniqc.torch_adapter`、`uniqc.calibration`、`uniqc.qem`、`uniqc.algorithms.workflows`。

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

安装默认建议：

```bash
uv tool install unified-quantum
uv pip install unified-quantum
```

按功能安装 extras：

- OriginQ: `unified-quantum[originq]`
- IBM/Qiskit: `unified-quantum[qiskit]`
- 高级模拟: `unified-quantum[simulation]`
- 可视化: `unified-quantum[visualization]`
- PyTorch: `unified-quantum[pytorch]`
- 全部常规 extras: `unified-quantum[all]`

Quafu/`pyquafu` 已 deprecated，且不在 `[all]` 中；只有用户明确需要 Quafu 时才单独安装 `[quafu]`，并提示它可能引入 `numpy<2` 约束。

## 发布前/维护者路径

维护者全量开发环境使用：

```bash
uv sync --all-extras --group dev --group docs --upgrade
uv run pytest uniqc/test
uv run pytest uniqc/test --real-cloud-test
uv run python scripts/generate_best_practice_notebooks.py
```

真实云平台测试中，读取后端列表、验证 token、查询 status/API 默认应可跑；会实际提交量子线路的测试才放在 `--real-cloud-test` 下。

## Calibration、QEM、XEB

- Calibration 结果写入 `~/.uniqc/calibration_cache/`。
- `uniqc.calibration` 负责生成和保存标定数据。
- `uniqc.qem` 负责读取标定数据并执行 error mitigation，包含 TTL 新鲜度检查。
- XEB workflow 走 `from uniqc import xeb_workflow`，例如 `xeb_workflow.run_1q_xeb_workflow(...)`。

示例默认用 `backend="dummy"` 做无约束、无噪声发布检查；要验证真实芯片标定噪声路径时才改成 `backend="dummy:originq:WK_C180"`。
