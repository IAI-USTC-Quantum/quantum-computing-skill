# 云平台与真机实验参考

> ⚠️ 平台 extras 速查：所有 `originq` 提交路径（云端模拟器和真机）都需要 `pip install unified-quantum[originq]`（拉 `pyqpanda3`）；同理 `[quafu]`（Quafu）、`[quark]`（Quark）、`[qiskit]`（IBM **以及** chip-backed dummy backend `dummy:originq:<chip>` / `dummy:quark:<chip>` 的拓扑感知 compile 通道）。
>
> 没装对应 extra 时，`submit_task(...)` 会抛 `CompilationFailedError` 或 `Package '...' is required for this feature` 错误。

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

Python adapters 会读取配置。新代码优先通过顶级 `uniqc.config` 理解和操作项目级配置。IBM proxy 优先放进 `~/.uniqc/config.yaml`，这样 CLI、Python API 和测试路径能共用同一份网络配置。

> ⚠️ **环境变量真相**（破除常见误解）：uniqc 自己**只**读 `UNIQC_PROFILE` 以及 `HTTP(S)_PROXY`。它**不会**自动读取 `ORIGINQ_API_KEY` / `QUAFU_API_TOKEN` / `QUARK_API_KEY` / `IBM_TOKEN`。这些 token 必须写进 `~/.uniqc/config.yaml`：
>
> ```bash
> uniqc config set originq.token <TOKEN>
> uniqc config set quafu.token <TOKEN>
> uniqc config set quark.QUARK_API_KEY <TOKEN>
> uniqc config set ibm.token <TOKEN>
> ```
>
> 如果一定要用环境变量传 token，需要在自己的脚本里手动把 env → config 同步（参见 `examples/cloud_submission.py` 里的 `_sync_env_to_config` 辅助函数，那是脚本自己的便利封装，不是 uniqc 的内置行为）。
>
> 另外：旧版 `UNIQC_DUMMY` / `UNIQC_SKIP_VALIDATION` 环境变量在 0.0.11.dev10 起**已移除**。改用：
>   - **dummy 模式**：传 `backend="dummy"` / `backend="dummy:virtual-line-N"` / `backend="dummy:originq:WK_C180"` 等到 `submit_task` 即可激活，无需任何环境变量。
>   - **跳过提交前校验**：在 `submit_task(..., skip_validation=True)` 单次调用上传 kwarg。

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

> ⚠️ **当前已知问题（uniqc 0.0.11.dev22）**：`dummy:originq:<chip>` 形式当前因 uniqc compiler `_route_with_fidelity` 的 `KeyError` 在多数线路上会崩。在补丁落地前，请改用：
> - `backend="dummy"` / `backend="dummy:virtual-line-N"` / `backend="dummy:virtual-grid-RxC"` / `backend="dummy:mps:linear-N"`，或
> - `backend="originq", backend_name="WK_C180", skip_validation=True` 直接走真机。

`dummy:originq:WK_C180` 这类写法的设计初衷是按真实 backend compile/transpile，再本地含噪执行；它是**提交规则**（`submit_task(backend=...)` 专用），不是 `backend list` / `find_backend(...)` 里的枚举项。`find_backend('dummy:originq:WK_C180')` 直接抛 `ValueError: Backend ... not found`；`list_backends()` 只返回显式注册的后端（`dummy`、`dummy:virtual-line-N`、`dummy:virtual-grid-RxC`、`dummy:mps:linear-N`，加全部真实云后端）。它还需要 `unified-quantum[qiskit]`，否则 `submit_task` 会抛 `CompilationFailedError`。

> ⚠️ **OriginQ backend ID 大小写规则（务必严格遵守）**：
> - **真机 / `find_backend` / `submit_task` / `dry_run_task`**：必须使用大写 chip 名加 `originq:` 前缀，**不接受**小写或 `origin:` 前缀。例如 `originq:WK_C180` 可用，`originq:wk_c180` / `origin:WK_C180` / `origin:wk_c180` 全部抛 `ValueError`。
> - **`dummy:originq:<chip>` 路径**额外接受小写 alias（即 `dummy:originq:wk_c180` 也能解析为 `WK_C180`），但仅限 dummy 链路；不要把这个习惯带到真机入口。
> - 推荐做法：所有源码里写 chip 名一律大写，调用前用 `find_backend('originq:WK_C180')` 验证一次。

OriginQ 真机：

```python
from uniqc import Circuit, compile, find_backend, submit_task, wait_for_result

c = Circuit(2); c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)

backend_info = find_backend('originq:WK_C180')
c_native = compile(c, backend_info, level=2)         # H/CNOT → CZ/SX/RZ
task_id = submit_task(c_native, backend='originq', backend_name='WK_C180', shots=200)
result = wait_for_result(task_id, timeout=300)       # → UnifiedResult (dict-like over counts)
```

> 默认 `auto_compile=True`（uniqc ≥ 0.0.11.dev10）：当线路不满足芯片 basis/topology 时，`submit_task` 会先调用 `compile_for_backend` 自动编译再提交；若仍不能落到 basis/topology 则抛 `UnsupportedGateError`。需要手动绕过校验时传 `submit_task(..., skip_validation=True)`。要完全跳过自动编译可传 `auto_compile=False`。

真实提交前先 dry-run：

```python
check = dry_run_task(circuit, backend="originq", shots=100, backend_name="WK_C180")
if not check.success:
    raise RuntimeError(check.error or check.details)
```

> Gotcha: `dry_run_task` 与 `submit_task` 的 backend 写法**不完全等价**。`dry_run_task` 仅接受 `backend="<platform>"` + `backend_name="<chip>"` 这种二元形式；写成 `backend="originq:WK_C180"` 会得到 `Unknown backend` 误导。`submit_task` 两种写法都能工作（`backend="originq:WK_C180"` 自动解析），但为了和 `dry_run_task` 保持一致，统一推荐二元写法。

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

### `wait_for_result` 的返回结构

`wait_for_result(task_id, ...)` 返回一个 **`UnifiedResult`** dataclass（uniqc ≥ 0.0.11.dev10）。它**同时**实现了 dict-like 协议（`result["00"]`、`for k in result`、`result.get(...)`、`len(result)`、`result.values()`），所以旧的"当 counts dict 用"的代码继续可用——counts 通过 dict 接口暴露：

```python
result = wait_for_result(task_id, timeout=300)
result["00"]            # 直接当 counts dict 索引（推荐）
sum(result.values())    # 总 shots
result.counts           # 显式拿 counts dict
result.probabilities    # 显式拿概率（同样 dict）
result.shots            # int
result.platform         # 'originq' / 'quafu' / 'quark' / 'ibm' / 'dummy'
result.task_id          # str
result.backend_name     # str | None
result.raw()            # 拿到平台原始 payload（用于 debug 或访问平台特有字段）
```

`result == {"00": 512, "11": 488}` 这样的等值比较（与普通 dict 比较 counts）也保持向后兼容。failure 路径返回 `None`，所以仍要做 `if result is None: ...` 判断。

如果只想要平台原始格式（不经 normalize），用 `result.raw()`。`normalize_*` 系列辅助函数（如 `normalize_originq_result`）依然存在，行为等价于 `wait_for_result` 内部逻辑。

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

最小代码示例：

```python
from uniqc.cli.chip_info import ChipCharacterization
from uniqc import RegionSelector, find_backend

backend = find_backend('originq:PQPUMESH8')                  # 小型 3-qubit 芯片
chip = ChipCharacterization.from_backend_info(backend)       # 或 from_dict(json) 加载缓存
sel = RegionSelector(chip)
chain = sel.find_best_1D_chain(length=3)
```

> 性能提示：`find_best_1D_chain` 现在**支持** `max_search_seconds` 参数（uniqc ≥ 0.0.11.dev10）。在 `originq:WK_C180`（169 qubit）这种大芯片上，建议传 `max_search_seconds=10.0` 限制搜索时间；超时会回退到当前最优解。`find_best_2D_from_circuit(circuit, min_qubits=N, max_search_seconds=10.0)` 也同样支持。

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

## 审计已配置后端（fetch_all_backends_with_status）

`audit_backends(...)` 与 `fetch_all_backends()` 不会告诉你哪个 platform 在 fetch 时失败（缺 SDK / token 错误等都被吞掉，得到空列表）。需要可见的失败信息时改用：

```python
from uniqc.backend_adapter.backend_registry import fetch_all_backends_with_status
from uniqc.backend_adapter.backend_info import Platform

result = fetch_all_backends_with_status()
print(result.backends.keys())     # 成功 fetch 的 platform → list[BackendInfo]
print(result.fetch_failures)      # 失败 platform → 异常信息
```

当前局限（uniqc 0.0.11.dev22）：

- `fetch_all_backends_with_status` 暂未在 `uniqc.*` 顶层导出，必须从 `uniqc.backend_adapter.backend_registry` 导入。
- 对 `Platform.QUARK / Platform.QUAFU` 的聚合分支当前可能直接跳过（即便 SDK 已装），因此 `fetch_all_backends_with_status()` 看不到这两个 platform。需要单独枚举时用 `fetch_platform_backends(Platform.QUARK)` / `fetch_platform_backends(Platform.QUAFU)` 直接拿。
