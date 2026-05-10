#!/usr/bin/env python3
"""End-to-end XEB + Readout calibration + mitigation demo.

Runs entirely against `dummy:local:virtual-line-3` so it is fully reproducible.

Usage:
    python xeb_qem_demo.py
    python xeb_qem_demo.py --backend dummy:originq:WK_C180 --qubits 0 1
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="XEB + Readout EM demo")
    parser.add_argument("--backend", default="dummy:local:virtual-line-3")
    parser.add_argument("--qubits", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--depths", type=int, nargs="+", default=[5, 10, 20])
    args = parser.parse_args()

    from uniqc.algorithms.workflows import xeb_workflow, readout_em_workflow

    print(f"[1/4] readout calibration on {args.backend} qubits={args.qubits}")
    cal = readout_em_workflow.run_readout_em_workflow(
        backend=args.backend, qubits=args.qubits, shots=args.shots)
    print(f"      cached at: {getattr(cal, 'calibrated_at', '<unknown>')}")

    print(f"[2/4] 1q XEB on {args.backend} qubits={args.qubits}")
    results_1q = xeb_workflow.run_1q_xeb_workflow(
        backend=args.backend,
        qubits=args.qubits,
        depths=args.depths,
        n_circuits=30,
        shots=args.shots,
        use_readout_em=True,
    )
    for q, r in results_1q.items():
        print(f"      q{q}: F_per_layer = {r.fidelity_per_layer:.4f} ± {r.fidelity_std_error:.4f}")

    if len(args.qubits) >= 2:
        pairs = [(args.qubits[i], args.qubits[i + 1]) for i in range(len(args.qubits) - 1)]
        print(f"[3/4] 2q XEB on pairs {pairs}")
        results_2q = xeb_workflow.run_2q_xeb_workflow(
            backend=args.backend,
            pairs=pairs,
            depths=args.depths,
            n_circuits=20,
            shots=args.shots,
            use_readout_em=True,
        )
        for pair, r in results_2q.items():
            print(f"      {pair}: F_per_layer = {r.fidelity_per_layer:.4f}")
    else:
        print("[3/4] skipped 2q XEB (need ≥ 2 qubits)")

    print("[4/4] mitigate a noisy circuit")
    from uniqc import Circuit, submit_task, wait_for_result

    n = max(args.qubits) + 1
    c = Circuit(n)
    for q in args.qubits:
        c.h(q)
    for q in args.qubits:
        c.measure(q)

    uid = submit_task(c, backend=args.backend, shots=2000)
    raw = wait_for_result(uid, timeout=60)
    if raw is None:
        raise SystemExit("noisy run failed")

    # `run_readout_em_workflow` returned a ready-to-use `ReadoutEM` instance.
    # Apply it directly via the .apply() pipeline.
    clean = cal.apply(raw)

    raw_top = sorted(raw.counts.items(), key=lambda kv: kv[1], reverse=True)[:6]
    cln_top = sorted(clean.counts.items(), key=lambda kv: kv[1], reverse=True)[:6]
    print("      raw      top:", raw_top)
    print("      mitigated top:", cln_top)


if __name__ == "__main__":
    main()
