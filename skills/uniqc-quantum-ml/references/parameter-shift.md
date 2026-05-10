# Parameter-shift rule

The parameter-shift rule lets us compute exact gradients of expectation
values through a quantum circuit, *without* the noise / step-size
trade-off of finite differences.

## Statement

For a single-parameter gate of the form

```
U(θ) = exp(-i θ G / 2)
```

with `G ∈ {X, Y, Z}` (i.e. `Rx`, `Ry`, `Rz`), and any observable `H`,

```
∂/∂θ ⟨ψ(θ)| H |ψ(θ)⟩ = ½ [⟨H⟩(θ + π/2) - ⟨H⟩(θ - π/2)]
```

— a **finite-difference at ±π/2 that is exactly the derivative**, not
an approximation. The factor `½` cancels with the derivative coefficient
of the rotation generator.

## Implication for `QuantumLayer`

`QuantumLayer.shift = π/2` (the default) makes backward pass correctness
hinge on this identity. Each gradient evaluation costs **two extra
forward passes per trainable parameter** (`+π/2` and `-π/2`). For `K`
trainable parameters and `N` samples per batch, that's `2KN` circuit
evaluations per backward pass.

## When the rule does not apply directly

- Multi-parameter single gates (`U3(θ, φ, λ)`, `R(θ_xx, θ_yy, θ_zz)`)
  — decompose into `Rx`/`Ry`/`Rz` first, then apply.
- Gates whose generator has more than two distinct eigenvalues
  (e.g. controlled rotations as a single block) — there is a
  generalised k-shift rule (Mari et al. 2021, Banchi & Crooks 2021),
  but `QuantumLayer.shift=π/2` will not be exact.
- Sampling-based expectations — the rule is unbiased but variance
  scales like `1/shots`. Use `shots ≥ 4096` for stable training.

## Verifying gradients with finite differences

```python
import math
import torch

eps = 1e-3
forward = lambda x: layer.forward_with_params(x)         # depends on internals; or wrap layer()
x = torch.zeros(len(layer.param_names))

x_plus  = x.clone(); x_plus[0]  += eps
x_minus = x.clone(); x_minus[0] -= eps

fd_grad   = (forward(x_plus) - forward(x_minus)) / (2 * eps)
ps_grad   = ...   # call layer's parameter-shift implementation
print("fd:", fd_grad, "ps:", ps_grad)
```

Run this once per architecture change; once it matches, trust the
parameter-shift gradient.

## Why not `torch.autograd` directly?

PyTorch can backprop through any `torch.Tensor` operation, but **not**
through a closed-source quantum simulator's internal state vectors. The
parameter-shift rule lets us treat the quantum circuit as a black box
that exposes only `f(θ)` evaluations, while still being exact.

For circuits implemented end-to-end inside torchquantum (the high-level
`QNNClassifier` route), torchquantum *does* hook into autograd directly
on the underlying tensor operations — no parameter-shift indirection
needed. That's why those classes are faster per step than wrapping the
same circuit in `QuantumLayer`.

## Practical cost model

For an `n_qubits = 8`, `depth = 3` circuit with ~48 trainable params
and `shots = None` (statevector):

- forward pass: ~10 ms on a laptop
- backward pass via parameter-shift: ~96 forward passes ≈ 1 s
- per epoch on 200 samples: ~3 minutes

For `shots = 4096` cloud submission per evaluation, multiply by the
backend's queue + execution time. **Always cache** intermediate
expectations during a single backward pass; many naive implementations
re-submit identical (θ ± π/2) circuits multiple times.
