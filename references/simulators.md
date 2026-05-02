# 模拟器与 dummy 参考

## 目录

- 选择哪种执行方式
- 本地模拟器
- shots 与 counts
- dummy backend
- 拓扑与 qubit remapping
- 从模拟走向真机

## 选择哪种执行方式

- **本地模拟器**：用于算法开发、概率分布、statevector/density matrix、优化循环。
- **dummy backend**：用于 task-manager、CLI submit/result、任务缓存和云端流程排练。
- **云平台 simulator**：用于检查平台 adapter、排队/任务查询接口和云端执行路径。
- **真机 backend**：用于最终硬件实验，提交前要检查 topology、qubit 质量、shots 和任务成本。

## 本地模拟器

安装：

```bash
pip install "unified-quantum[simulation]"
```

Python 用法：

```python
from uniqc.circuit_builder import Circuit
from uniqc.simulator import OriginIR_Simulator

circuit = Circuit(2)
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure(0, 1)

sim = OriginIR_Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(circuit.originir)
state = sim.simulate_statevector(circuit.originir)
counts = sim.simulate_shots(circuit.originir, shots=1000)
```

密度矩阵：

```python
sim = OriginIR_Simulator(backend_type="densitymatrix")
rho = sim.simulate_density_matrix(circuit.originir)
```

CLI 用法：

```bash
uniqc simulate bell.ir --backend statevector --shots 1024 --format json
uniqc simulate bell.ir --backend density --shots 1024 --format json
```

## shots 与 counts

算法调试时优先看精确概率或 statevector；准备上云前再看有限 shots 的 counts。

```python
probabilities = sim.simulate_pmeasure(circuit.originir)
counts = sim.simulate_shots(circuit.originir, shots=4096)
```

解释结果时说明它们代表不同对象：

- probability/statevector：理想模拟分布
- counts：有限采样结果
- hardware counts：带有设备噪声、排队状态和平台后处理的真实实验结果

## dummy backend

dummy backend 不是物理模拟器；它用于验证 task API、缓存和结果查询流程。

```python
from uniqc import submit_task, submit_batch, wait_for_result

task_id = submit_task(circuit, backend="dummy", shots=1000)
result = wait_for_result(task_id, timeout=60)

task_ids = submit_batch([circuit, circuit], backend="dummy", shots=1000)
results = [wait_for_result(task_id, timeout=60) for task_id in task_ids]
```

CLI：

```bash
uniqc submit bell.ir --platform dummy --shots 1000 --wait --format json
```

使用建议：

- 写 cloud workflow 示例时，先给 dummy，再给 OriginQ/Quafu/IBM。
- dummy 通过后，再替换 platform/backend 和认证配置。
- 不要把 dummy counts 当成硬件噪声模型结论。

## 拓扑与 qubit remapping

从本地模拟走向真实芯片时，要考虑可用 qubit 和耦合关系。优先使用 backend/chip characterization 或 RegionSelector，而不是手写固定 qubit 编号。

常见流程：

1. `uniqc backend list --platform originq`
2. `uniqc backend show originq:WK_C180`
3. `uniqc backend chip-display originq:WK_C180 --update`
4. 在 Python 中基于 topology/characterization 选择 region
5. 对线路做 qubit remapping，再提交

如果只是把逻辑线路重映射到一组可用 qubit，可查 `least_qubit_remapping`：

```python
from uniqc.remapper import least_qubit_remapping
```

## 从模拟走向真机

推荐检查清单：

1. 本地模拟给出合理概率分布。
2. dummy submit/result 跑通。
3. backend list/show 确认目标设备可用。
4. 根据 topology 和 qubit 质量选择 region。
5. 小 shots 真机试跑。
6. 保存 task id、backend、shots、线路源码和结果。
