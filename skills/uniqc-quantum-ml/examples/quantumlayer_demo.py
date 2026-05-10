#!/usr/bin/env python3
"""Manual parameter-shift demo: minimise -<Z> over a single Rx(θ).

Mirrors uniqc's upstream `examples/3_best_practices/08_torch_quantum_training.py`
pattern: hold θ as a `torch.nn.Parameter`, evaluate <Z> via a uniqc Circuit +
Simulator, and write the parameter-shift gradient back into `theta.grad`.

This avoids the high-level `QuantumLayer` wrapper, which on uniqc 0.0.13.dev0
needs a `NamedCircuit`-style `circuit_def` and is brittle in non-trivial cases.
For most research uses, the manual loop below is shorter and easier to debug.

Usage:
    python quantumlayer_demo.py
"""

from __future__ import annotations

import math


def main() -> None:
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
        # simulate_shots returns dict[int, int]: 0 -> count of |0>, 1 -> count of |1>.
        plus  = counts.get(0, 0)
        minus = counts.get(1, 0)
        return (plus - minus) / total

    torch.manual_seed(0)
    theta = torch.nn.Parameter(torch.tensor(1.0))
    opt   = torch.optim.SGD([theta], lr=0.3)

    for step in range(40):
        opt.zero_grad()
        value = z_expectation(theta.item())
        # Parameter-shift rule for Rx: ∂<Z>/∂θ = ½ [<Z>(θ+π/2) − <Z>(θ−π/2)]
        grad = 0.5 * (
            z_expectation(theta.item() + math.pi / 2)
            - z_expectation(theta.item() - math.pi / 2)
        )
        # We want to MAXIMISE <Z>, i.e. minimise -<Z>.
        # Loss is -<Z>, so gradient w.r.t. θ is -grad.
        theta.grad = torch.tensor(-grad, dtype=theta.dtype)
        opt.step()
        if (step + 1) % 5 == 0:
            print(f"step {step+1:3d}  <Z>={value:+.4f}  θ={theta.item():+.4f}")

    print(f"\nfinal <Z>: {z_expectation(theta.item()):+.4f}")
    print(f"final θ:    {theta.item():+.4f}  (target: 0 for max <Z>)")


if __name__ == "__main__":
    main()
