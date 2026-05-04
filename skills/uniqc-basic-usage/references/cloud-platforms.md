# 云平台与真机实验参考

## 目录

- 实验工作流
- 配置
- backend 发现与 cache
- Python task API
- RegionSelector 与芯片数据
- 平台建议
- 实验记录

## 实验工作流

把云端实验拆成固定步骤：

1. 构建或加载线路。
2. 本地模拟，确认概率分布符合预期。
3. dummy backend 跑通 submit/query/result。
4. 用 `uniqc backend list/show` 选择平台和 backend。
5. 需要真机时读取 chip characterization，选择 qubit region。
6. 小 shots 提交真实任务。
7. 查询结果并保存实验元数据。

这个顺序比直接提交真机更稳，也更容易定位失败发生在认证、线路、backend、任务队列还是结果解析。

## 配置

默认配置路径：

```text
~/.uniqc/config.yaml
```

CLI 配置：

```bash
uniqc config init
uniqc config set originq.token YOUR_ORIGINQ_TOKEN
uniqc config set quafu.token YOUR_QUAFU_TOKEN
uniqc config set quark.QUARK_API_KEY YOUR_QUARK_API_KEY
uniqc config set ibm.token YOUR_IBM_TOKEN
uniqc config set ibm.proxy.https http://127.0.0.1:7890
uniqc config set ibm.proxy.http http://127.0.0.1:7890
uniqc config always-ai-hint on
uniqc config validate
```

Python adapters 会读取配置。新代码优先通过顶级 `uniqc.config` 理解和操作项目级配置。IBM proxy 优先放进 `~/.uniqc/config.yaml`，这样 CLI、Python API 和测试路径能共用同一份网络配置。自动化脚本也可以显式设置环境变量，便于 CI 或临时凭证：

```bash
export ORIGINQ_API_KEY=...
export QUAFU_API_TOKEN=...
export QUARK_API_KEY=...
export IBM_TOKEN=...
```

不要把 token 写进示例代码、日志或 issue。

## backend 发现与 cache

首选 CLI：

```bash
uniqc backend list --platform originq
uniqc backend list --platform quafu
uniqc backend list --platform quark
uniqc backend list --platform ibm
uniqc backend list --format json
uniqc backend show originq:WK_C180
uniqc backend update --platform originq
uniqc backend chip-display originq/WK_C180 --update
```

Cache 位置：

- backend 列表 cache：`~/.uniqc/cache/backends.json`
- 芯片标定 cache：`~/.uniqc/backend-cache/*.json`
- 任务 cache：`~/.uniqc/cache/tasks.sqlite`

用法建议：

- 开始实验时用 `--update` 强制刷新一次。
- 后续在同一轮开发里复用 cache。
- 如果 backend 不可用、排队太长或 topology 不适合，换 backend，不要硬提交。

## Python task API

公共入口：

```python
from uniqc import dry_run_task, submit_task, submit_batch, query_task, wait_for_result
```

dummy 排练：

```python
task_id = submit_task(circuit, backend="dummy", shots=1000)
result = wait_for_result(task_id, timeout=60)
```

拓扑和芯片标定路径：

```python
line_task = submit_task(circuit, backend="dummy:virtual-line-3", shots=1000)
noisy_task = submit_task(circuit, backend="dummy:originq:WK_C180", shots=1000)
```

`dummy:originq:WK_C180` 这类写法会按真实 backend compile/transpile，再本地含噪执行；它是提交规则，不是 `backend list` 里的枚举项。

OriginQ 真机：

```python
task_id = submit_task(
    circuit,
    backend="originq",
    backend_name="WK_C180",
    shots=100,
)
info = query_task(task_id, backend="originq")
result = wait_for_result(task_id, backend="originq", timeout=300)
```

真实提交前先 dry-run：

```python
check = dry_run_task(circuit, backend="originq", shots=100, backend_name="WK_C180")
if not check.success:
    raise RuntimeError(check.error or check.details)
```

Quafu simulator 或真机：

```python
task_id = submit_task(
    circuit,
    backend="quafu",
    chip_id="ScQ-Sim10",
    shots=100,
)
result = wait_for_result(task_id, backend="quafu", timeout=300)
```

Quark 真机（需配置 `QUARK_API_KEY`，Python ≥ 3.12）：

```python
from uniqc import QuarkOptions

opts = QuarkOptions(chip_id="Baihua", compile=True)
task_id = submit_task(
    circuit,
    backend="quark",
    shots=100,
    options=opts,
)
result = wait_for_result(task_id, backend="quark", timeout=300)
```

批量任务：

```python
task_ids = submit_batch(circuits, backend="dummy", shots=1000)
results = [wait_for_result(task_id, timeout=60) for task_id in task_ids]
```

批量真机任务要更保守：先用 1 到 2 个小任务确认 backend、认证和线路都正常，再提交更大的批次。

## RegionSelector 与芯片数据

RegionSelector 用于把逻辑线路放到质量更好的物理 qubit 区域上。典型使用场景：

- 线路需要连续耦合区域。
- 目标 backend 的 qubit 质量差异明显。
- 希望避开不可用 qubit 或高错误率边。
- 需要在多个 candidate region 中做可重复选择。

推荐流程：

1. 刷新 backend/chip cache。
2. 读取目标 backend 的 topology 和 characterization。
3. 根据线路宽度、连通性和质量指标选择 region。
4. 对 circuit 做 remapping。
5. 把 remapping 信息写进实验记录。

不要把芯片表格截图当成唯一真值；在自动化流程里优先使用结构化 cache/API 数据。

## 平台建议

### OriginQ

- 常用真机 backend 名可通过 `uniqc backend list --platform originq` 获取。
- 提交时使用 `backend_name=...`。
- 云端 simulator 适合验证平台任务路径，但不一定适合作为快速 smoke test。

### Quafu

- `ScQ-Sim10` 适合做云端 simulator 级别检查。
- 真机提交时用当前 backend list 里的 chip id。
- 如果线路不满足拓扑，优先启用 mapping 或先 remap。

### Quark

- 配置 `QUARK_API_KEY`（不是 `token`）：`uniqc config set quark.QUARK_API_KEY <KEY>`。
- 安装：`unified-quantum[quark]`（Python ≥ 3.12）。
- 常用 backend：`Baihua`、`Dongling`，通过 `uniqc backend list --platform quark` 查看完整列表。
- 支持 compile、compiler selection、dynamical decoupling 和 readout correction 选项。
- 电路格式为 OpenQASM 2.0，UnifiedQuantum 自动从 OriginIR 转换。

### IBM

- 先确认本地 qiskit runtime 依赖和账号实例可用。
- 如果直连 IBM Quantum 不稳定，先配置 `ibm.proxy.https` / `ibm.proxy.http`，再跑 `uniqc backend update --platform ibm`。
- backend 可用性、region、排队状态会变化，提交前必须重新查 backend。

## 实验记录

每次真实提交都记录：

- UnifiedQuantum 版本和 Python 环境
- circuit 生成脚本或 OriginIR/QASM 文件
- platform/backend/chip id
- selected qubits / remapping
- shots
- task id
- submit/query/result 时间
- counts/probabilities
- 是否开启优化、measurement amend、auto mapping 等平台选项

如果要写论文式或报告式结果，保留原始 counts，不只保留归一化概率。
