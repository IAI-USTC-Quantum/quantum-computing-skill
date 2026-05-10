# `QCNNClassifier` and `HybridQCLModel`

These two cover the cases `QNNClassifier` does not:

- **`QCNNClassifier`** — input is already a (real-valued) quantum state
  amplitude vector; convolution + pooling layers gradually reduce the
  qubit count and produce a classifier head. Useful for "is this
  prepared state in class A or B?".
- **`HybridQCLModel`** — classical encoder → fixed-width quantum core →
  classical decoder. Useful when the raw input is high-dimensional
  (images, text embeddings) and angle-encoding directly would burn too
  many qubits.

Both need torchquantum (see `qnn-classifier.md` for the install line).

## `QCNNClassifier` — state classification

```python
import torch
from uniqc import Circuit, QCNNClassifier
from uniqc.simulator import Simulator


def make_dataset(n_qubits: int, n_samples: int):
    sim = Simulator(backend_type="statevector")
    X, y = [], []
    for i in range(n_samples):
        if i % 2 == 0:
            c = Circuit(n_qubits)                         # |0...0>
            label = 0.0
        else:
            c = Circuit(n_qubits); c.h(0)
            for q in range(1, n_qubits):
                c.cx(0, q)                                # GHZ
            label = 1.0
        sv = sim.simulate_statevector(c.originir)
        X.append(torch.tensor(sv, dtype=torch.float32))
        y.append(label)
    return X, torch.tensor(y, dtype=torch.float32)


def main():
    n_qubits = 4
    X, y = make_dataset(n_qubits, n_samples=20)

    model = QCNNClassifier(n_qubits=n_qubits, n_classes=2)
    opt   = torch.optim.Adam(model.parameters(), lr=0.01)

    for epoch in range(50):
        total = 0.0
        correct = 0
        for sv, label in zip(X, y):
            opt.zero_grad()
            pred = model()                                # QCNN reads from the prepared state
            loss = (pred - label) ** 2
            loss.mean().backward()
            opt.step()
            total += loss.item()
            correct += int((pred.item() > 0.5) == label.item())
        if (epoch + 1) % 10 == 0:
            print(f"epoch {epoch+1:3d} loss={total/len(X):.4f} acc={correct/len(X):.4f}")
```

> The current `QCNNClassifier` API treats the prepared state as a
> module-level fixture rather than a per-sample input. For most research
> uses you want to wrap a custom data-loading scheme — the above is a
> working illustration but not the only valid pattern.

## `HybridQCLModel` — image / tabular pipelines

```python
import torch
import torch.nn as nn
from sklearn.datasets import make_moons
from sklearn.preprocessing import StandardScaler
from uniqc import HybridQCLModel


def main():
    torch.manual_seed(0)
    X_np, y_np = make_moons(n_samples=400, noise=0.15, random_state=42)
    X_np = StandardScaler().fit_transform(X_np)
    X = torch.tensor(X_np, dtype=torch.float32)
    y = torch.tensor(y_np, dtype=torch.float32).unsqueeze(1)

    model = HybridQCLModel(
        n_features=2,
        n_qubits=4,
        quantum_depth=2,
        classical_hidden=16,
    )
    opt   = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.BCELoss()

    for epoch in range(50):
        opt.zero_grad()
        y_pred = model(X)
        loss = loss_fn(y_pred, y)
        loss.backward()
        opt.step()
        if (epoch + 1) % 10 == 0:
            acc = ((y_pred > 0.5).float() == y).float().mean()
            print(f"epoch {epoch+1:3d} loss={loss.item():.4f} acc={acc:.4f}")
```

`HybridQCLModel` is the right choice when:

- Input dimension is much larger than `n_qubits` you can afford.
- You want a learnable feature map before angle encoding.
- You want a richer classifier head than the model's built-in sigmoid.

Inspect partition counts:

```python
print("encoder:", sum(p.numel() for p in model.encoder.parameters()))
print("quantum:", model.quantum_params.numel())
print("decoder:", sum(p.numel() for p in model.decoder.parameters()))
```

## Picking between the three

| Situation                                         | Pick                |
| ------------------------------------------------- | ------------------- |
| 2-10 numeric features, binary labels              | `QNNClassifier`     |
| Already-prepared quantum states, ≥ 4 qubits       | `QCNNClassifier`    |
| High-dim classical input, want classical pre/post | `HybridQCLModel`    |
| Custom architecture (e.g. encoder-decoder, vae)   | `QuantumLayer` from scratch |

## Common mistakes

- Running these classes without torchquantum installed: the import fails
  with `ImportError: torchquantum`. Install per the QNN reference.
- Passing un-scaled features — same as for any neural net, you'll see
  trivial loss curves.
- Using `QCNNClassifier` with a feature vector instead of a real
  amplitude vector — it expects a normalised state. Always call
  `Simulator.simulate_statevector` first.
- Comparing wall-clock training speed against a classical NN — quantum
  forward passes (statevector or torchquantum) are much slower per step;
  don't expect it to win on toy datasets.
