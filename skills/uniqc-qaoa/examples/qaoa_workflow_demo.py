#!/usr/bin/env python3
"""High-level QAOA via uniqc.algorithms.workflows.qaoa_workflow.

Usage:
    python qaoa_workflow_demo.py
    python qaoa_workflow_demo.py --p 3 --graph square
"""

from __future__ import annotations

import argparse


PRESET_GRAPHS = {
    "triangle": [(0, 1), (1, 2), (0, 2)],
    "square":   [(0, 1), (1, 2), (2, 3), (3, 0)],
    "line3":    [(0, 1), (1, 2)],
}


def maxcut_hamiltonian_compact(edges, n_nodes):
    """Compact Pauli form (length = n_nodes) — required by run_qaoa_workflow."""
    terms = []
    for i, j in edges:
        ops = ["I"] * n_nodes
        ops[i] = "Z"
        ops[j] = "Z"
        terms.append(("".join(ops), 1.0))
    return terms


def maxcut_hamiltonian_indexed(edges):
    """Indexed Pauli form — required by qaoa_ansatz."""
    return [(f"Z{i}Z{j}", 1.0) for i, j in edges]


def cut_value(bits, edges):
    return sum(1 for i, j in edges if bits[-1 - i] != bits[-1 - j])


def main() -> None:
    parser = argparse.ArgumentParser(description="QAOA MaxCut via run_qaoa_workflow")
    parser.add_argument("--graph", choices=list(PRESET_GRAPHS), default="triangle")
    parser.add_argument("--p", type=int, default=2)
    parser.add_argument("--maxiter", type=int, default=200)
    args = parser.parse_args()

    edges = PRESET_GRAPHS[args.graph]
    n_qubits = max(max(e) for e in edges) + 1
    cost_h_compact = maxcut_hamiltonian_compact(edges, n_qubits)
    cost_h_indexed = maxcut_hamiltonian_indexed(edges)

    from uniqc.algorithms.workflows.qaoa_workflow import run_qaoa_workflow

    print(f"graph={args.graph} edges={edges} n_qubits={n_qubits} p={args.p}")
    result = run_qaoa_workflow(
        cost_h_compact,
        n_qubits=n_qubits,
        p=args.p,
        method="COBYLA",
        options={"maxiter": args.maxiter},
    )

    print(f"energy: {result.energy:.6f}")
    print(f"γ:      {result.gammas}")
    print(f"β:      {result.betas}")
    print(f"iters:  {result.n_iter}  converged={result.success}  msg={result.message!r}")
    print(f"history (last 5): {result.history[-5:]}")

    # Sample to see the cut distribution
    from uniqc import qaoa_ansatz
    from uniqc.simulator import Simulator

    circuit = qaoa_ansatz(cost_h_indexed, p=args.p, gammas=result.gammas, betas=result.betas)
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
