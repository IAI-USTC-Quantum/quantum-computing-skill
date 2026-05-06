# 变分算法参考

## 目录

- 当前公开 ansatz
- HEA
- QAOA ansatz
- UCCSD ansatz
- 一个典型 VQE 结构
- 一个典型 QAOA 结构
- 使用这些 ansatz 时记住

当前 UnifiedQuantum 对变分算法更适合从“ansatz 构造器 + 自己的目标函数 / 优化器”来理解，而不是依赖一套过度封装的旧接口。

## 当前公开 ansatz

```python
from uniqc import hea, qaoa_ansatz, uccsd_ansatz
```

注意：

- 把这些函数当作线路生成器；优化器、目标函数和测量策略由任务决定。
- 参数维度要和 ansatz 层数、qubit 数、Hamiltonian 结构匹配。
- 生成线路后先本地模拟，再考虑 dummy 或真机任务。

## HEA

```python
from uniqc import hea

circuit = hea(
    n_qubits=4,
    depth=2,
    params=params,  # 长度应为 2 * n_qubits * depth
)
```

特点：

- 结构轻
- NISQ 友好
- 常用于最小 VQE / VQC 示例

## QAOA ansatz

```python
from uniqc import qaoa_ansatz

cost_hamiltonian = [
    ("Z0Z1", 1.0),
    ("Z1Z2", 1.0),
]

circuit = qaoa_ansatz(
    cost_hamiltonian,
    p=2,
    betas=betas,
    gammas=gammas,
)
```

要点：

- `cost_hamiltonian` 形如 `[(pauli_string, coefficient), ...]`
- `betas`、`gammas` 长度都应等于 `p`
- 如果不给，构造器会随机初始化

## UCCSD ansatz

```python
from uniqc import uccsd_ansatz

circuit = uccsd_ansatz(
    n_qubits=4,
    n_electrons=2,
    params=params,
)
```

要点：

- 适合量子化学风格任务
- 默认先准备 Hartree-Fock 初态
- 参数长度取决于单激发 / 双激发计数

## 一个典型 VQE 结构

推荐这样组织 VQE：

1. 选 ansatz
2. 写一个目标函数
3. 在目标函数里调用模拟器得到概率或态矢
4. 用 `scipy.optimize.minimize` 或你自己的优化器迭代

示意：

```python
import numpy as np
from scipy.optimize import minimize
from uniqc import calculate_expectation, hea
from uniqc.simulator import OriginIR_Simulator

sim = OriginIR_Simulator(backend_type="statevector")

def objective(params):
    circuit = hea(n_qubits=2, depth=1, params=params)
    probs = sim.simulate_pmeasure(circuit.originir)
    return calculate_expectation(probs, "ZZ")

result = minimize(objective, x0=np.zeros(4), method="COBYLA")
```

### `calculate_expectation` 的 Hamiltonian 格式

`calculate_expectation(measured_result, hamiltonian)` 接受**位置式 `Z`/`I` 字符串**，长度必须等于 `n_qubit`，例如 `"ZZII"`（对前两个 qubit 取 ⟨Z⊗Z⟩，后两个忽略）。

它**不接受** `qaoa_ansatz.cost_hamiltonian` / `pauli_expectation` 那种带索引的 Pauli-string 写法（例如 `"Z0 Z1"`、`"Z0Z1"`）。如果你已经在用索引格式，需要先转成位置式字符串再传入。

### `calculate_multi_basis_expectation` 的语义陷阱

`calculate_multi_basis_expectation(measured_result, basis_label)` 只看 `basis_label` 的**第一个字符**，并在 **qubit 0** 上计算单比特期望：传 `"XX"` 等价于 `⟨X⟩` on qubit 0，**不是** `⟨X⊗X⟩`。要算多比特 Pauli 期望请改用 `pauli_expectation(...)`。

## 一个典型 QAOA 结构

1. 从图构造 cost Hamiltonian
2. 用 `qaoa_ansatz()` 生成电路
3. 用概率分布评估 cut value
4. 优化 `betas` / `gammas`

## 使用这些 ansatz 时记住

- 把 ansatz 当作“线路生成器”来解释
- 把优化器和目标函数当作用户可替换部分
- 不要把示例当成“唯一正确范式”
- 如果示例依赖本地模拟，明确标出 `simulation` extra
