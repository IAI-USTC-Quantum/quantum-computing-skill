#!/usr/bin/env python3
"""Catalog runner: pick a named algorithm, build the circuit, simulate locally,
and print top bitstrings.

Usage:
    python run_algorithm.py --name ghz --n 3
    python run_algorithm.py --name grover --n 3 --marked 5
    python run_algorithm.py --name qpe --phi 0.375 --precision 4
    python run_algorithm.py --name dj --n 3
    python run_algorithm.py --name vqe
"""

from __future__ import annotations

import argparse
import math


def build(name: str, args: argparse.Namespace):
    from uniqc import Circuit, ghz_state, w_state, qft_circuit
    from uniqc import grover_oracle, grover_diffusion
    from uniqc import deutsch_jozsa_circuit
    from uniqc.algorithms.core.circuits import qpe_circuit

    if name == "ghz":
        prog = Circuit(args.n)
        prog.add_circuit(ghz_state(qubits=list(range(args.n))))
        for q in range(args.n):
            prog.measure(q)
        return prog, args.n

    if name == "w":
        prog = Circuit(args.n)
        prog.add_circuit(w_state(qubits=list(range(args.n))))
        for q in range(args.n):
            prog.measure(q)
        return prog, args.n

    if name == "qft":
        prog = Circuit(args.n)
        prog.x(0)        # any non-trivial input
        prog.add_circuit(qft_circuit(qubits=list(range(args.n)), swaps=True))
        for q in range(args.n):
            prog.measure(q)
        return prog, args.n

    if name == "grover":
        n = args.n
        oracle = grover_oracle(marked_state=args.marked, n_qubits=n)
        diff   = grover_diffusion(n_qubits=n)
        prog = Circuit(n)
        for q in range(n):
            prog.h(q)
        iters = round(math.pi / 4 * math.sqrt(2 ** n))
        for _ in range(iters):
            prog.add_circuit(oracle)
            prog.add_circuit(diff)
        for q in range(n):
            prog.measure(q)
        return prog, n

    if name == "qpe":
        U = Circuit(1)
        U.rz(0, 2 * math.pi * args.phi)
        prep = Circuit(1); prep.x(0)
        prog = qpe_circuit(n_precision=args.precision, unitary_circuit=U,
                            state_prep=prep, measure=True)
        return prog, args.precision      # only the precision register is measured

    if name == "dj":
        # default oracle = balanced (XOR of all input bits into ancilla)
        n = args.n
        oracle = Circuit(n + 1)
        for i in range(n):
            oracle.cnot(i, n)
        prog = deutsch_jozsa_circuit(qubits=list(range(n)), ancilla=n, oracle=oracle)
        return prog, n + 1

    if name == "vqe":
        # delegate to the workflow
        from uniqc.algorithms.workflows.vqe_workflow import run_vqe_workflow
        H = [("XX", 1.0), ("YY", 1.0), ("ZZ", 1.0)]
        result = run_vqe_workflow(H, n_qubits=2, depth=3,
                                   method="COBYLA", options={"maxiter": 200})
        print("VQE energy:", result.energy)
        print("VQE params:", result.params)
        return None, 0

    raise SystemExit(f"unknown algorithm name: {name!r}")


def simulate(prog, n_meas: int) -> None:
    from uniqc.simulator import Simulator

    sim = Simulator(backend_type="statevector")
    probs = sim.simulate_pmeasure(prog.originir)
    items = [
        (format(i, f"0{n_meas}b"), float(p))
        for i, p in enumerate(probs) if float(p) > 1e-3
    ]
    items.sort(key=lambda kv: kv[1], reverse=True)
    for bits, p in items[:8]:
        print(f"  {bits}  prob={p:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a canonical quantum algorithm")
    parser.add_argument("--name", required=True,
                        choices=["ghz", "w", "qft", "grover", "qpe", "dj", "vqe"])
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--marked", type=int, default=5, help="for grover")
    parser.add_argument("--phi", type=float, default=0.375, help="for qpe")
    parser.add_argument("--precision", type=int, default=4, help="for qpe")
    args = parser.parse_args()

    prog, n_meas = build(args.name, args)
    if prog is None:
        return
    print(f"running '{args.name}' on {n_meas} measured qubit(s)")
    simulate(prog, n_meas)


if __name__ == "__main__":
    main()
