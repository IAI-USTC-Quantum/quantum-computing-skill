---
name: uniqc-quantum-ml
description: "Use when the user wants to do quantum machine learning with UnifiedQuantum + PyTorch: high-level `QNNClassifier` / `QCNNClassifier` / `HybridQCLModel`, low-level `QuantumLayer` (parameter-shift autograd over a `Circuit`), and end-to-end PyTorch training loops on classical datasets (moons / MNIST / quantum-state classification). Covers torchquantum optional dependency and parameter-shift gradients."
---

# Uniqc Quantum ML Skill

This skill is the entry point for **PyTorch-based** quantum machine
learning. UnifiedQuantum exposes three layers:

| Layer | Class                                          | Use for                                              |
| ----- | ---------------------------------------------- | ---------------------------------------------------- |
| 1     | `QNNClassifier`, `QCNNClassifier`, `HybridQCLModel` | Drop-in classifiers for tabular / image / state inputs |
| 2     | `QuantumLayer(circuit, expectation_fn, ...)`   | Custom architectures around your own `Circuit`       |
| 3     | Hand-written parameter-shift gradient          | Algorithmic research                                 |

> ⚠️ Optional dependency: classes in layer 1 import **torchquantum**.
> The pip extra `unified-quantum[pytorch]` only pulls `torch`.
> torchquantum is installed manually:
>
> ```bash
> pip install "torchquantum @ git+https://github.com/Agony5757/torchquantum.git@fix/optional-qiskit-deps"
> ```
>
> If the user hits `ImportError: torchquantum`, install it before
> retrying. `QuantumLayer` (layer 2) does **not** need torchquantum — it
> uses uniqc's own simulator + parameter-shift.

## First decision

| User goal                                                      | Read first                                              |
| -------------------------------------------------------------- | ------------------------------------------------------- |
| "Train a binary classifier on a tabular dataset"               | [references/qnn-classifier.md](references/qnn-classifier.md) |
| "Train an image / state classifier (deep)"                     | [references/qcnn-and-hybrid.md](references/qcnn-and-hybrid.md) |
| "Wrap my own circuit so PyTorch sees its parameters"           | [references/quantumlayer.md](references/quantumlayer.md) |
| "Understand the parameter-shift rule / why π/2"                | [references/parameter-shift.md](references/parameter-shift.md) |
| "Run training on a real / dummy backend, not local sim"        | [references/quantumlayer.md](references/quantumlayer.md) (`expectation_fn` swap) |

## Mental model

```
classical input ─► classical encoder (optional)
                  └──► QuantumLayer / QNNClassifier
                       │  forward: prepare circuit, sample / statevector
                       │  backward: parameter-shift (Δθ = ±π/2)
                  └──► classical decoder (optional)
                       └──► loss
```

For QNNClassifier / QCNNClassifier / HybridQCLModel, all three slabs are
already wired; you only supply data + optimiser.

## Practical defaults

- **Dataset prep**: standard-scale features (mean 0 / std 1) before
  amplitude or angle encoding. Skipping this is the #1 reason a QML
  model "trains" but never improves.
- **Optimizer**: Adam(lr=0.01) for `QNNClassifier`; reduce to 0.005 if
  you see oscillation. Use AdamW if you have many trainable params.
- **Loss**: BCELoss (binary), CrossEntropyLoss (multi-class). For
  expectation-as-output regression, use MSELoss.
- **Batch size**: 8–32 for QML on a laptop; the per-iter cost is
  dominated by the circuit forward pass.
- **Epochs**: start with 50 and watch `loss.item()` plateau before
  scaling up.
- **Device**: torchquantum simulators run on CPU by default; pass
  `device='cuda'` if your build supports it.
- **Seeds**: set `torch.manual_seed`, `numpy.random.seed`, and pass
  `random_state` to scikit-learn — QML training is sensitive.

## Cheat sheet — `QNNClassifier`

```python
import torch
import torch.nn as nn
from sklearn.datasets import make_moons
from sklearn.preprocessing import StandardScaler
from uniqc import QNNClassifier

X_np, y_np = make_moons(n_samples=200, noise=0.15, random_state=42)
X_np = StandardScaler().fit_transform(X_np)
X = torch.tensor(X_np, dtype=torch.float32)
y = torch.tensor(y_np, dtype=torch.float32)

model = QNNClassifier(n_qubits=4, n_features=2, depth=2)
opt = torch.optim.Adam(model.parameters(), lr=0.01)
loss_fn = nn.BCELoss()

for epoch in range(50):
    opt.zero_grad()
    y_pred = model(X)
    loss = loss_fn(y_pred, y)
    loss.backward()
    opt.step()
    if (epoch + 1) % 10 == 0:
        acc = ((y_pred > 0.5).float() == y).float().mean()
        print(f"epoch {epoch+1:3d}  loss={loss.item():.4f}  acc={acc:.4f}")
```

## Cheat sheet — `QuantumLayer` (custom circuit)

> ⚠️ `QuantumLayer` in uniqc 0.0.13.dev0 needs a circuit built via
> `circuit_def(...).build_standalone()` — building with bare
> `Circuit()` + `Parameter("theta")` will **not** populate the
> `_parameters` dict and the backward pass crashes. If `QuantumLayer`
> misbehaves, fall back to the manual parameter-shift loop in
> `examples/quantumlayer_demo.py`. See `references/quantumlayer.md`
> for the full story.

```python
import math
import torch
from uniqc import circuit_def, QuantumLayer
from uniqc.algorithms.core.measurement import pauli_expectation

@circuit_def(name="single_rx", qregs={"q": 1}, params=["theta"])
def single_rx(circ, q, theta):
    circ.rx(q[0], theta[0])
    return circ

qc = single_rx.build_standalone()
layer = QuantumLayer(
    circuit=qc,
    expectation_fn=lambda c: pauli_expectation(c, "Z0"),
    n_outputs=1,
    init_params=torch.tensor([1.0]),
    shift=math.pi / 2,
)
print(layer())          # forward pass returns a torch tensor
```

`QuantumLayer.parameters()` returns a torch `Parameter` you can hand to
any optimiser. Parameter names live at `layer._param_names` (private —
no public accessor in this version).

## Names to remember

- High-level classifiers (need torchquantum): `QNNClassifier`,
  `QCNNClassifier`, `HybridQCLModel`.
- Low-level wrapping: `QuantumLayer(circuit, expectation_fn, n_outputs,
  init_params, shift)` from `uniqc.torch_adapter.quantum_layer`
  (re-exported as `uniqc.QuantumLayer`).
- Symbolic params on `Circuit`: `uniqc.Parameter("name")` — substitute
  via `circuit.bind({theta: value})`.
- Optional extra: `pip install unified-quantum[pytorch]` — pulls torch
  only. torchquantum is a separate manual install (link above).

## Response style

- Always do `StandardScaler` on classical features unless the user has
  a reason not to. Mention it explicitly; it is the most common silent
  bug in QML demos.
- For new architectures, prototype with `QuantumLayer` over a small
  circuit; only graduate to torchquantum when you need the high-level
  classes.
- Print loss every 10 epochs, not every step — reduces noise in the log.
- Save `model.state_dict()` after training; QML hyperparameter sweeps
  are expensive to redo.
