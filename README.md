# quantum-computing-skill

基于 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) 的量子编程 skill 仓库。

这个仓库的重点不是重复讲一遍 UnifiedQuantum 全部内部实现，而是帮助 agent 和使用者更快找到当前可用的工作流：

- 用 `Circuit` 构建线路
- 输出 `OriginIR` 或 `OpenQASM 2.0`
- 通过 `uniqc` CLI 或 `uniqc.task_manager` 执行
- 按需启用云平台、模拟、PyTorch 等可选能力

## 当前定位

适合回答这些类型的问题：

- “怎么用 UnifiedQuantum 搭一个线路 / 导出 OriginIR / 导出 QASM？”
- “`uniqc` CLI 现在有哪些命令？怎么配 token、查任务、走 dummy 模式？”
- “怎么用 HEA / QAOA / UCCSD ansatz？”
- “PyTorch 集成现在有哪些 helper？哪些功能需要额外依赖？”

不适合把它当成：

- UnifiedQuantum 主仓源码镜像
- 全量 API 手册
- 对所有 optional features 都“默认可运行”的保证

## 安装建议

基础安装：

```bash
pip install unified-quantum
```

只想把 `uniqc` 当 CLI 工具装到独立环境里：

```bash
uv tool install unified-quantum
```

常见 extras：

| 场景 | 安装命令 |
|------|---------|
| 本地模拟 / dummy 模式 | `pip install "unified-quantum[simulation]"` |
| OriginQ 云平台 | `pip install "unified-quantum[originq]"` |
| Quafu 云平台 | `pip install "unified-quantum[quafu]"` |
| IBM Quantum | `pip install "unified-quantum[qiskit]"` |
| PyTorch helper | `pip install "unified-quantum[pytorch]"` |
| TorchQuantum 集成 | `pip install "unified-quantum[torchquantum]"` |

## 推荐工作流

当前最稳妥的路径是：

1. 用 `uniqc.circuit_builder.Circuit` 或第三方工具构建线路
2. 导出 `circuit.originir` 或 `circuit.qasm`
3. 优先把输入统一到 OriginIR，再走 `uniqc simulate` / `uniqc submit`
4. 需要云平台时先配置 `~/.uniqc/uniqc.yml`
5. 需要本地模拟、dummy 模式、PyTorch 时，再补对应 extras

## 仓库结构

```text
quantum-computing-skill/
├── SKILL.md
├── references/
│   ├── circuit-building.md
│   ├── cli-guide.md
│   ├── simulators.md
│   ├── cloud-platforms.md
│   ├── variational-algorithms.md
│   ├── pytorch-integration.md
│   ├── h2-molecular-simulation.md
│   └── version-notes.md
├── examples/
│   ├── basic_circuit.py
│   ├── cli_demo.sh
│   ├── cloud_submission.py
│   ├── h2_hea_vqe.py
│   ├── mnist_classifier.py
│   └── qaoa_maxcut.py
└── scripts/
    └── setup_uniqc.sh
```

## 示例说明

| 文件 | 说明 |
|------|------|
| `examples/basic_circuit.py` | 构建 Bell 线路，导出 OriginIR/QASM，并在依赖可用时尝试本地模拟 |
| `examples/cli_demo.sh` | 演示 `uniqc circuit`、`uniqc simulate`、`uniqc submit --platform dummy` 的当前调用方式 |
| `examples/cloud_submission.py` | 展示 `submit_task` / `query_task` / `wait_for_result`，以及 dummy / 真云端的参数差异 |
| `examples/h2_hea_vqe.py` | 用 HEA 做一个 H2 风格的最小 VQE 工作流，强调可选依赖前提 |
| `examples/qaoa_maxcut.py` | 使用 `qaoa_ansatz` 构造 MaxCut QAOA 电路并做经典优化 |
| `examples/mnist_classifier.py` | 用 `uniqc.pytorch` 的 helper 做一个轻量混合量子-经典分类示例 |

高级示例都默认是“按需安装 extras 后运行”的模式，不再假设裸环境一定具备 `qutip`、`torch`、`torchvision` 等依赖。

## 参考索引

- [SKILL.md](SKILL.md): skill 主入口
- [references/circuit-building.md](references/circuit-building.md): `Circuit`、寄存器、参数、导出格式
- [references/cli-guide.md](references/cli-guide.md): `uniqc` CLI
- [references/simulators.md](references/simulators.md): 本地模拟与依赖边界
- [references/cloud-platforms.md](references/cloud-platforms.md): config、task cache、dummy / 云平台
- [references/variational-algorithms.md](references/variational-algorithms.md): `hea`、`qaoa_ansatz`、`uccsd_ansatz`
- [references/pytorch-integration.md](references/pytorch-integration.md): `QuantumLayer`、parameter-shift、batch helpers
- [references/h2-molecular-simulation.md](references/h2-molecular-simulation.md): H2 风格任务的建模建议
- [references/version-notes.md](references/version-notes.md): 只记录会影响使用与排障的重大版本断点

## License

Apache License 2.0
