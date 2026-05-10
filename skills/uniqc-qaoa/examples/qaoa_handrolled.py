#!/usr/bin/env python3
"""Hand-rolled QAOA loop: qaoa_ansatz + pauli_expectation + scipy.minimize.

Use this when you want to swap in a custom optimiser or measurement
strategy. For the canonical 5-line workflow, see qaoa_workflow_demo.py.
"""

from __future__ import annotations

import argparse
import numpy as np
from scipy.optimize import minimize


PRESET_GRAPHS = {
    "triangle": [(0, 1), (1, 2), (0, 2)],
    "square":   [(0, 1), (1, 2), (2, 3), (3, 0)],
    "line3":    [(0, 1), (1, 2)],
}


def maxcut_hamiltonian(edges):
    return [(f"Z{i}Z{j}", 1.0) for i, j in edges]


def cut_value(bits, edges):
    return sum(1 for i, j in edges if bits[-1 - i] != bits[-1 - j])


def main() -> None:
    parser = argparse.ArgumentParser(description="Hand-rolled QAOA MaxCut")
    parser.add_argument("--graph", choices=list(PRESET_GRAPHS), default="triangle")
    parser.add_argument("--p", type=int, default=2)
    parser.add_argument("--maxiter", type=int, default=300)
    parser.add_argument("--shots", type=int, default=None,
                        help="None = exact statevector loss; pass an int for sampling")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    from uniqc import qaoa_ansatz
    from uniqc.algorithms.core.measurement import pauli_expectation
    from uniqc.simulator import Simulator

    edges = PRESET_GRAPHS[args.graph]
    n_qubits = max(max(e) for e in edges) + 1
    cost_h = maxcut_hamiltonian(edges)
    rng = np.random.default_rng(args.seed)

    history: list[float] = []

    def objective(x: np.ndarray) -> float:
        gammas = x[:args.p]
        betas  = x[args.p:]
        circuit = qaoa_ansatz(cost_h, p=args.p, betas=betas, gammas=gammas)
        return sum(c * pauli_expectation(circuit, ps, shots=args.shots) for ps, c in cost_h)

    def callback(xk):
        history.append(objective(xk))

    x0 = rng.uniform(0, np.pi, size=2 * args.p)
    out = minimize(objective, x0, method="COBYLA",
                   options={"maxiter": args.maxiter}, callback=callback)

    best_gammas = out.x[:args.p]
    best_betas  = out.x[args.p:]
    print(f"graph={args.graph}  p={args.p}  shots={args.shots}")
    print(f"min energy: {out.fun:.6f}  iters={out.nfev}  success={out.success}")

    circuit = qaoa_ansatz(cost_h, p=args.p, gammas=best_gammas, betas=best_betas)
    for q in range(n_qubits):
        circuit.measure(q)

    sim = Simulator(backend_type="statevector")
    probs = sim.simulate_pmeasure(circuit.originir)
    ranked = sorted(
        ((format(i, f"0{n_qubits}b"), float(p)) for i, p in enumerate(probs) if p > 1e-3),
        key=lambda kv: kv[1], reverse=True,
    )
    print("\ntop bitstrings:")
    for bits, p in ranked[:8]:
        print(f"  {bits}  prob={p:.4f}  cut={cut_value(bits, edges)}")


if __name__ == "__main__":
    main()
