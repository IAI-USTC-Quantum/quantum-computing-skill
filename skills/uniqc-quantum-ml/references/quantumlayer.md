# `QuantumLayer` — wrap your own circuit for PyTorch

`QuantumLayer` is uniqc's `torch.nn.Module` wrapper around a parametric
circuit. The forward pass evaluates an `expectation_fn` on the bound
circuit; the backward pass uses the **parameter-shift rule**.

> ⚠️ **Brittleness in uniqc 0.0.13.dev0**: `QuantumLayer` reads parameter
> names from `circuit._parameters`, which is only populated when you
> build the circuit through `circuit_def(name=..., qregs=..., params=...)`
> followed by `.build_standalone()`. Constructing a `Circuit()` directly
> and inserting `Parameter("theta")` does **not** populate
> `_parameters`, and the backward pass then fails with
> `ValueError: zip() argument 2 is longer than argument 1`.
>
> If `QuantumLayer.forward()` raises that error, fall back to the
> manual parameter-shift loop shown at the bottom of this page (also in
> `examples/quantumlayer_demo.py`). It is what the upstream uniqc
> torchquantum example uses, and it sidesteps the wrapper entirely.

`QuantumLayer` does **not** need torchquantum — it uses uniqc's own
simulator path. Optional dependency: `torch` only
(`pip install unified-quantum[pytorch]`).

## Signature

```python
QuantumLayer(
    circuit:        Circuit,
    expectation_fn: Callable[[Circuit], float],
    n_outputs:      int = 1,
    init_params:    torch.Tensor | None = None,
    shift:          float = math.pi / 2,
)
```

- `circuit` — built via `circuit_def(...).build_standalone()`. Inspect
  via `layer._param_names` (private — uniqc 0.0.13.dev0 does not expose
  a public `param_names` attribute despite the upstream basic-usage
  reference suggesting it does).
- `expectation_fn(circuit) -> float` — given a circuit with all
  parameters bound, returns a scalar. Typically wraps `pauli_expectation`.
- `n_outputs` — when > 1, `expectation_fn` returns a 1-D iterable.
- `init_params` — initial trainable values; defaults to
  `randn(n_params) * 0.1` if None.
- `shift` — finite-difference step; π/2 implements parameter-shift for
  `Rx / Ry / Rz`.

## Recommended construction (when QuantumLayer works)

```python
import math
import torch

from uniqc import circuit_def, QuantumLayer
from uniqc.algorithms.core.measurement import pauli_expectation


@circuit_def(name="single_rx", qregs={"q": 1}, params=["theta"])
def single_rx(circ, q, theta):
    circ.rx(q[0], theta[0])
    return circ


qc = single_rx.build_standalone()           # populates _parameters

def expect(c):
    return pauli_expectation(c, "Z0")

layer = QuantumLayer(
    circuit=qc, expectation_fn=expect,
    n_outputs=1, init_params=torch.tensor([1.0]), shift=math.pi / 2,
)
```

If `layer()` raises `ValueError: zip() argument 2 is longer than
argument 1`, the wrapper failed to extract parameter names — fall
back to the manual parameter-shift loop below.

## Manual parameter-shift fallback (recommended baseline)

This is the upstream uniqc torchquantum-training pattern — clear,
runnable, and not dependent on `QuantumLayer` internals:

```python
import math
import torch
from uniqc import Circuit
from uniqc.simulator import Simulator

sim = Simulator(backend_type="statevector")

def z_expectation(theta_value: float) -> float:
    c = Circuit(1)
    c.rx(0, float(theta_value))
    c.measure(0)
    counts = sim.simulate_shots(c.originir, shots=4096)
    total = sum(counts.values()) or 1
    return (counts.get("0", 0) - counts.get("1", 0)) / total

torch.manual_seed(0)
theta = torch.nn.Parameter(torch.tensor(1.0))
opt   = torch.optim.SGD([theta], lr=0.3)

for step in range(40):
    opt.zero_grad()
    val = z_expectation(theta.item())
    grad = 0.5 * (
        z_expectation(theta.item() + math.pi / 2)
        - z_expectation(theta.item() - math.pi / 2)
    )
    # Maximise <Z>: loss = -<Z>, ∂loss/∂θ = -grad
    theta.grad = torch.tensor(-grad, dtype=theta.dtype)
    opt.step()
```

See `examples/quantumlayer_demo.py` for a runnable version.

## Multi-parameter / multi-output (with `circuit_def`)

```python
@circuit_def(name="two_param", qregs={"q": 2}, params=["gamma", "beta"])
def two_param(circ, q, gamma, beta):
    circ.h(q[0]); circ.h(q[1])
    circ.cnot(q[0], q[1]); circ.rz(q[1], gamma[0]); circ.cnot(q[0], q[1])
    circ.rx(q[0], beta[0]); circ.rx(q[1], beta[0])
    return circ

qc = two_param.build_standalone()

def expvals(c):
    return [pauli_expectation(c, "Z0Z1"), pauli_expectation(c, "X0X1")]

layer = QuantumLayer(circuit=qc, expectation_fn=expvals, n_outputs=2,
                     init_params=torch.tensor([0.5, 0.7]))
```

## Plugging into a training loop

```python
import torch.nn as nn

classical_head = nn.Linear(2, 1)
opt = torch.optim.Adam(
    list(layer.parameters()) + list(classical_head.parameters()),
    lr=0.01,
)

target = torch.tensor([0.0])
for epoch in range(100):
    opt.zero_grad()
    qz = layer().unsqueeze(0)
    pred = torch.sigmoid(classical_head(qz)).squeeze()
    loss = (pred - target) ** 2
    loss.backward()
    opt.step()
```

(Same caveat — if the layer's backward fails, replace `layer()` with a
manual parameter-shift wrapper of your circuit.)

## Backend selection

`expectation_fn` controls where the circuit runs. Default
`pauli_expectation` uses the local OriginIR statevector simulator. To
sample on a backend:

```python
def expectation_on_backend(circuit, *, backend="dummy:local:simulator", shots=4096):
    return pauli_expectation(circuit, "Z0", shots=shots)
```

For a true cloud loop, wrap a `submit_task` + `wait_for_result` call
inside `expectation_fn`. **Do not do this naively in a training loop**
— each forward pass costs one cloud submission, plus 2 more per
parameter for the shift. Cache aggressively.

## Why `shift = π/2`

For a single-parameter rotation gate
`R(θ) = exp(-i θ P / 2)` with Pauli `P`, the gradient of
`⟨ψ(θ)| H |ψ(θ)⟩` is exactly:

```
df/dθ = (f(θ + π/2) - f(θ - π/2)) / 2
```

— finite-difference at `±π/2`, **not** an approximation. This is why
`shift=π/2` is the default and why this only works cleanly for
`Rx / Ry / Rz`. For arbitrary `U` gates, use the generalised k-shift
rule or fall back to small-step finite differences.

## Common mistakes

- Building a circuit with `Circuit()` + `Parameter("theta")` directly
  and handing it to `QuantumLayer`. The wrapper looks for
  `circuit._parameters` (a dict), which is only populated through
  `circuit_def`. Use the decorator path or fall back to manual
  parameter-shift.
- Forgetting to pass `init_params` — defaults to `randn * 0.1`; many
  circuits have a saddle near θ=0 and never train.
- Passing `n_outputs > 1` but having `expectation_fn` return a scalar.
  Crashes with shape mismatch in the autograd backward.
- Using a non-rotation gate (`U`, `R3`, `Rxx`) and assuming
  `shift=π/2` is exact. Validate gradients with finite differences
  before believing the loss curve.
