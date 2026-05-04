# CLI 使用参考

## 目录

- 基本工作流
- 线路转换与检查
- 本地模拟
- dummy 与云端提交
- 任务查询
- 配置与 backend 发现
- 适合 CLI 的场景

## 基本工作流

CLI 入口是：

```bash
uniqc
```

备选模块入口：

```bash
python -m uniqc.cli
```

不要再推荐 `python -m uniqc`；v0.0.9 中 package root 不提供该入口。

如果你要给当前环境下的 AI Agent（Codex/Claude Code）补齐基础技能，执行：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill --agent codex --skill '*'
npx skills add IAI-USTC-Quantum/quantum-computing.skill --agent claude-code --skill '*'
```

CLI 的 AI 渐进式提示入口：

```bash
uniqc config list --ai-hint
uniqc backend list --ai-hints
UNIQC_AI_HINTS=1 uniqc config validate
uniqc config always-ai-hint on
```

`--ai-hints` 和 `--ai-hint` 等价。给弱一点的 agent 配环境时，推荐先运行 `uniqc config always-ai-hint on`，这样后续命令不用每次加参数也会显示下一步提示。不要推荐 `uniqc workflow --help`，除非当前版本 help 明确列出该子命令；通常 `workflow` 是文档页，不是 CLI 命令。

推荐 shell 工作流：

```bash
uniqc circuit input.qasm --format originir -o normalized.ir
uniqc simulate normalized.ir --backend statevector --shots 1024
uniqc submit normalized.ir --platform dummy --shots 1000 --wait
```

把 QASM、OriginIR 和 Python 线路先归一化成一个文件，可以减少不同入口之间的差异。

## 线路转换与检查

```bash
uniqc circuit bell.ir --info
uniqc circuit bell.ir --format qasm -o bell.qasm
uniqc circuit bell.qasm --format originir -o bell.ir
```

当用户只是想知道线路规模、门数、深度或格式是否能解析，先用 `uniqc circuit --info`。

## 本地模拟

常用后端：

```bash
uniqc simulate bell.ir --backend statevector --shots 1024 --format json
uniqc simulate bell.ir --backend density --shots 1024 --format json
```

用法建议：

- 先用 `statevector` 做快速功能验证。
- 需要噪声、混态或密度矩阵语义时用 `density`。
- 需要给后续脚本处理时加 `--format json`。
- 如果模拟命令提示缺依赖，安装 `unified-quantum[simulation]` 或 `unified-quantum[all]`。

## dummy 与云端提交

dummy 是本地任务管理和结果查询流程的首选排练后端：

```bash
uniqc submit bell.ir --platform dummy --shots 1000 --wait --format json
uniqc submit bell.ir --platform dummy --backend virtual-line-3 --shots 1000 --wait
uniqc submit bell.ir --platform dummy --backend originq:WK_C180 --shots 1000 --wait
```

`--platform dummy` 默认对应无约束、无噪声的 `dummy`；`--backend virtual-line-N` / `virtual-grid-RxC` 用虚拟拓扑；`--backend <platform>:<backend>` 复用真实 backend 拓扑和标定数据做本地含噪执行。

真实平台提交前，先列出 backend：

```bash
uniqc backend list --platform originq
uniqc backend list --platform quafu
uniqc backend list --platform quark
uniqc backend list --platform ibm
```

OriginQ 示例：

```bash
uniqc submit bell.ir --platform originq --backend WK_C180 --shots 100 --wait
```

Quafu 示例：

```bash
uniqc submit bell.ir --platform quafu --backend ScQ-Sim10 --shots 100 --wait
```

Quark 示例（需配置 `QUARK_API_KEY`）：

```bash
uniqc submit bell.ir --platform quark --backend Baihua --shots 100 --wait
```

如果不想立即提交真实任务，先做 dry run：

```bash
uniqc submit bell.ir --platform dummy --shots 100 --dry-run
uniqc submit bell.ir --platform originq --backend WK_C180 --shots 100 --dry-run
uniqc submit bell.ir --platform quark --backend Baihua --shots 100 --dry-run
```

## 任务查询

```bash
uniqc result TASK_ID --format json
uniqc task status TASK_ID
uniqc task list
```

结果通常会进入本地任务 cache。给用户写实验记录时，保留：

- circuit 文件或生成脚本
- platform/backend
- shots
- task id
- submission time
- result counts/probabilities

## 配置与 backend 发现

配置文件默认是 `~/.uniqc/config.yaml`。

Python 侧配置模块是顶级 `uniqc.config`，因为配置已经覆盖 profile、token、proxy、AI hints 等项目级状态，不再只是 backend adapter 的内部配置。旧的 `uniqc.backend_adapter.config` 可兼容旧代码，但新示例不要优先推荐它。

```bash
uniqc config init
uniqc config set originq.token YOUR_ORIGINQ_TOKEN
uniqc config set quafu.token YOUR_QUAFU_TOKEN
uniqc config set quark.QUARK_API_KEY YOUR_QUARK_API_KEY
uniqc config set ibm.token YOUR_IBM_TOKEN
uniqc config set ibm.proxy.https http://127.0.0.1:7890
uniqc config set ibm.proxy.http http://127.0.0.1:7890
uniqc config validate
```

Backend 发现：

```bash
uniqc backend update
uniqc backend list --format table
uniqc backend list --format json
uniqc backend show originq:WK_C180
uniqc backend chip-display originq/WK_C180 --update
```

用 `uniqc backend update` 刷新 backend 列表 cache；用 `chip-display ... --update` 刷新芯片标定 cache。不用时优先复用本地 cache，避免反复打云端 API。

## 标定与 QEM

CLI 标定命令（结果自动缓存到 `~/.uniqc/calibration_cache/`）：

```bash
# XEB benchmarking（1q / 2q / parallel）
uniqc calibrate xeb --qubits 0 1 2 3 --type 1q --backend dummy --shots 1000 --depths 5 10 20 40
uniqc calibrate xeb --qubits 0 1 --type 2q --backend dummy --shots 1000

# Readout 标定（1q / 2q joint）
uniqc calibrate readout --qubits 0 1 --backend dummy --shots 1000

# Pattern 分析（DSatur 并行分组）
uniqc calibrate pattern --qubits 0 1 2 3 4 5
uniqc calibrate pattern --type circuit --circuit my_circuit.ir
```

标定后可用 Python API 做 QEM（见 [references/calibration-qem.md](calibration-qem.md)）。

## 适合 CLI 的场景

优先用 CLI：

- 格式转换
- 快速模拟
- 配置检查
- backend 列表和芯片标定查看
- 单个任务提交与结果拉取

优先用 Python API：

- 参数化线路
- 批量任务
- VQE/QAOA 优化循环
- 自动选择 qubit region
- 需要把结果接入 pandas、SciPy、PyTorch 或自定义分析代码
