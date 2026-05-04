# 通用排错参考

## 目录

- 排错顺序
- 环境快照
- 安装与 extra
- CLI 与 Python 不一致
- 云端任务失败
- 结果看起来不对
- 何时上报 issue

## 排错顺序

先解决用户正在做的具体工作流，不要一开始就展开版本历史。

1. 回到对应 feature reference：CLI、simulator、cloud、variational、PyTorch。
2. 拍环境快照，确认当前解释器和 `uniqc` 是同一套环境。
3. 用最小线路复现。
4. 区分解析错误、依赖错误、认证错误、backend 错误、平台队列/任务状态错误。
5. 如果最小复现仍像库问题，再查当前文档、GitHub issue 和源码。

## 环境快照

```bash
which python3
python3 --version
python3 -c "import uniqc, sys; print('uniqc', getattr(uniqc, '__version__', 'unknown')); print(uniqc.__file__); print(sys.executable)"
which uniqc || true
uniqc --help | head -40
```

如果 `python -m uniqc.cli` 和 `uniqc` 行为不同，优先处理 PATH/venv 问题。不要使用 `python -m uniqc` 作为 v0.0.9 的排错入口。

## 安装与 extra

完整量子算法和云端开发环境：

```bash
uv pip install "unified-quantum[all]"
```

按功能拆分时：

- 本地模拟 / dummy：`unified-quantum[simulation]`
- OriginQ：`unified-quantum[originq]`
- Quark：`unified-quantum[quark]`（Python ≥ 3.12）
- Quafu：`unified-quantum[quafu]`，该平台已 deprecated，且不包含在 `[all]` 中
- IBM：`unified-quantum[qiskit]`
- PyTorch：`unified-quantum[pytorch]`

缺 `qutip`、`torch`、`qiskit`、`quafu`、`pyqpanda3` 时，先判断是不是缺 extra，不要立刻当作核心库损坏。

## CLI 与 Python 不一致

常见原因：

- shell 里的 `uniqc` 来自另一个 Python 环境。
- Jupyter kernel 和终端不是同一个 venv。
- 用户改了 `~/.uniqc/config.yaml`，但进程环境里还有旧 token。
- 本地 backend/cache 过期。

处理：

```bash
python -m uniqc.cli --help
uniqc config validate
uniqc backend list --format json
uniqc backend chip-display originq/WK_C180 --update
```

必要时清楚地告诉用户当前命令实际用的是哪个解释器，不要含糊说“环境有问题”。

## 云端任务失败

按层定位：

1. 配置：`uniqc config validate`
2. backend：`uniqc backend list --platform ...`
3. 线路：先 `uniqc simulate` 或 dummy submit
4. 平台参数：OriginQ 用 `backend_name`，Quafu 用 `chip_id`
5. 任务状态：`query_task` / `uniqc task status`
6. 结果：`wait_for_result` timeout 不等价于提交失败，继续查 task status

如果 timeout，先返回 task id 和查询命令，让用户能继续追踪。

## 结果看起来不对

先区分结果类型：

- statevector/probability：理想模拟
- local shots counts：本地采样
- dummy counts：任务流程排练结果
- hardware counts：真实设备实验结果

检查项：

- measurement 是否覆盖了需要的 qubit
- bitstring 顺序是否符合用户后处理假设
- shots 是否太少
- 是否对线路做了 remapping
- 真机是否开启平台级 mapping、optimization、measurement amend
- 是否混用了概率和 counts

## 何时上报 issue

只有在满足这些条件后再建议上报：

- 当前环境和版本已经明确。
- 最小线路能复现。
- 不是缺 extra、token、PATH、cache 或 backend 当前不可用。
- 行为与当前 README/API 文档明显冲突。

Issue 内容应包含：

- 安装方式和版本
- Python 版本与 OS
- 最小代码或最小 CLI 命令
- 完整 traceback 或任务状态
- 期望行为与实际行为
- 是否涉及真实云端 task id，注意不要泄露 token

## 标定与 QEM 排错

| 症状 | 原因 | 处理 |
|------|------|------|
| `StaleCalibrationError` | 标定数据超过 `max_age_hours` TTL | 重新执行 `uniqc calibrate readout` 或 `uniqc calibrate xeb`，或在 Python API 中增大 `max_age_hours` |
| `FileNotFoundError` in `M3Mitigator` | 标定 cache 文件不存在 | 先执行 `uniqc calibrate readout` |
| 在 dummy backend 上做 QEM 结果全零 | DummyAdapter 返回的 counts 默认是无噪声的 | QEM 在 dummy 上无实际意义；用含噪 dummy（`dummy:originq:WK_C180`）或真机才有校准效果 |
| `TimelineDurationError` | 逻辑线路没有门时长数据 | 传入 `gate_durations` dict，或使用 `backend_info` 带时长信息的 backend |
