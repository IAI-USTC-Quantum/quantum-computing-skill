---
name: quantum-computing-skill
description: "Use when the user asks about UnifiedQuantum, uniqc, OriginIR, OpenQASM, circuit building, local simulation, cloud submission, dummy mode, VQE, QAOA, UCCSD, quantum ML, or PyTorch integration with UnifiedQuantum. Focus on the current public workflow: build circuits, export IR/QASM, run with uniqc CLI or task_manager, and add extras only when needed."
version: 1.1.0
---

# UnifiedQuantum Skill

当用户在使用当前 UnifiedQuantum 的公开 API、CLI 或示例时，使用这个 skill。

## 默认处理思路

优先采用当前的高层工作流：

1. 用 `uniqc.circuit_builder.Circuit` 构建线路
2. 导出 `circuit.originir` 或 `circuit.qasm`
3. 用 `uniqc` CLI 或 `uniqc.task_manager` 执行
4. 只为确实需要的功能安装额外 extras

当用户给的是一段 QASM 线路时，更稳妥的处理路径通常是：

1. 先用 `uniqc circuit` 转成 OriginIR
2. 再对这份归一化后的 OriginIR 做模拟或提交

这样可以减少不同输入路径带来的行为差异。

## 环境与安装处理

- 不要默认用户已经先决定好如何安装 `unified-quantum`，也不要默认用户已经选好了 CLI 入口。
- 先检查用户环境里已经有什么：解释器、已安装包、模块路径、CLI 是否可用，以及相关 extras 是否存在。
- 默认根据环境自动选择一个合理的安装路径，并先尝试那条路径。
- 如果需要修改环境，但这条路径有风险、存在歧义，或者已经失败，再和用户确认下一步。
- 决定安装方式前，先识别用户当前是在 `venv`、Conda、Pixi 还是系统 Python 中工作。
- 如果有 `uv`，优先尝试基于 `uv` 的隔离安装路径。
- 对偏 CLI 的工作流，优先考虑 `uv tool install`；它隔离性较好，也更方便在当前仓库外直接使用命令。
- 对 Python API 场景，优先安装到用户实际正在使用的解释器或环境里；如果还没有合适环境，优先考虑由 `uv` 管理的虚拟环境。
- 如果用户已经在 Pixi 生态里工作，`pixi global` 也是可接受的选择。它同样有隔离性，也能全局暴露命令，但对这个 skill 来说通常比 `uv` 更重。
- 如果当前环境是已激活的 Conda 环境，默认不要直接改它。先问用户是否要装进这个环境；如果用户同意，优先在该环境里用 `pip`，避免改动 root 环境。
- 如果唯一可写目标是系统 Python，安装前先和用户确认。
- 普通 `venv` 也可以作为兜底方案。它并不局限于仓库内使用，但跨目录使用 CLI 往往依赖激活或显式路径，因此通常没有 `uv tool install` 或 `pixi global` 那么顺手。
- 如果 `uv` 不可用或不合适，再退回 `pip`。

## 几个容易混淆但要记清的点

- 包名：`unified-quantum`
- CLI 名：`uniqc`
- 主 Python 包名：`uniqc`
- 配置文件：`~/.uniqc/uniqc.yml`
- 本地任务缓存：`~/.uniqc/cache/tasks.sqlite`
- 如果主题 reference 仍然解释不了问题，再回到 [references/troubleshooting.md](references/troubleshooting.md) 做通用诊断。

## 依赖边界

不要默认基础安装就包含所有功能。

- 核心包：`pip install unified-quantum`
- 本地模拟 / dummy 模式常见需要：`pip install "unified-quantum[simulation]"`
- OriginQ 适配器：`pip install "unified-quantum[originq]"`
- Quafu 适配器：`pip install "unified-quantum[quafu]"`
- IBM 适配器：`pip install "unified-quantum[qiskit]"`
- PyTorch 辅助工具：`pip install "unified-quantum[pytorch]"`
- TorchQuantum 集成：`pip install "unified-quantum[torchquantum]"`

如果用户提到 `qutip`、`torch`、`qiskit`、`quafu` 或 `pyqpanda3` 相关导入失败，先把它当成缺少可选依赖，而不是先判断核心包坏了。

## CLI 指引

当前 CLI 主要分组有：

- `uniqc circuit`
- `uniqc simulate`
- `uniqc submit`
- `uniqc result`
- `uniqc task`
- `uniqc config`

当用户要在 shell 里做格式转换、本地执行或云任务管理时，优先用 `uniqc`，不要先写临时辅助脚本。

当前有几个细节要特别注意：

- `uniqc submit` 使用 `--platform`，并可选搭配 `--backend`
- 对 OriginQ，当前 CLI 选项是 `--backend`，不是旧的 `--chip-id`
- 对 Quafu，`chip_id` 在 Python API 中仍然相关，但当前 CLI 没有单独暴露 `--chip-id`
- `simulate` 最稳妥的输入仍是 OriginIR；如果手里是 QASM，先做归一化

## Python API 指引

如果是编程式的任务工作流，优先使用：

```python
from uniqc import submit_task, submit_batch, query_task, wait_for_result
```

构造 ansatz 时，优先使用当前公开导出：

```python
from uniqc.algorithmics.ansatz import hea, qaoa_ansatz, uccsd_ansatz
```

不要再使用像 `uccsd` 这样的旧名字。

PyTorch 集成优先使用：

```python
from uniqc.pytorch import (
    QuantumLayer,
    batch_execute,
    batch_execute_with_params,
    parameter_shift_gradient,
    compute_all_gradients,
)
```

## 接下来读什么

- 线路构建与导出：[references/circuit-building.md](references/circuit-building.md)
- CLI 用法：[references/cli-guide.md](references/cli-guide.md)
- 本地模拟与 dummy 模式：[references/simulators.md](references/simulators.md)
- 配置、云端后端与任务缓存：[references/cloud-platforms.md](references/cloud-platforms.md)
- ansatz 与变分工作流：[references/variational-algorithms.md](references/variational-algorithms.md)
- PyTorch 辅助接口：[references/pytorch-integration.md](references/pytorch-integration.md)
- H2 风格的 VQE 任务：[references/h2-molecular-simulation.md](references/h2-molecular-simulation.md)
- 主题检查之后仍然不清楚的通用排障：[references/troubleshooting.md](references/troubleshooting.md)

## 回答启发式

- 如果用户想要一个快速起步，先从 `Circuit -> originir -> uniqc` 开始。
- 如果用户卡在云端执行，先检查配置和后端特有 kwargs；如果仍然不清楚，再回到 [references/troubleshooting.md](references/troubleshooting.md)。
- 如果用户问的是本地模拟失败，先检查 `simulation` 相关依赖；必要时再回到 [references/troubleshooting.md](references/troubleshooting.md)。
- 如果用户提到缺命令、缺导入、缺 extra、缺配置路径，或者文档与本地行为不一致，先拍安装快照，再判断是不是版本漂移导致，然后查同类 issue，最后再进入 [references/troubleshooting.md](references/troubleshooting.md) 的完整通用排障流程。
- 如果需要安装，先根据环境尝试一个合理默认方案；只有当路径不清楚、有风险或已经失败时，再问用户。
- 如果用户想看现代的变分示例，优先从 `hea`、`qaoa_ansatz` 或 `uccsd_ansatz` 开始，不要从旧 helper 名称起步。
- 如果用户想走 shell 工作流，优先给 `uniqc` CLI 方案，而不是自定义 wrapper。
