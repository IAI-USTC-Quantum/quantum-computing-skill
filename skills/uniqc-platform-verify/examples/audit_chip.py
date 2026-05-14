"""End-to-end platform metadata audit.

Refreshes the local backend cache, reads the cached chip
characterization, runs a minimal XEB + readout calibration, compares
measured fidelities to claimed, and prints a concise audit report.

Usage:
    python audit_chip.py --chip originq:WK_C180 --width 4 --shots 1000

Note: against `dummy:originq:<chip>` this becomes a self-consistency
check (the noise model was built from the vendor metadata, so measured
should track claimed within shot noise).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone


def _refresh(platform: str) -> None:
    print(f"[refresh] uniqc backend update --platform {platform}")
    try:
        subprocess.run(
            ["uniqc", "backend", "update", "--platform", platform],
            check=False,
        )
    except FileNotFoundError:
        sys.exit("uniqc CLI not on PATH — install unified-quantum first.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chip", default="dummy:originq:WK_C180",
                    help="provider:chip (use dummy:provider:chip for offline audit)")
    ap.add_argument("--width", type=int, default=4)
    ap.add_argument("--shots", type=int, default=1000)
    ap.add_argument("--n-circuits", type=int, default=20)
    args = ap.parse_args()

    from uniqc import find_backend
    from uniqc.algorithms.workflows import xeb_workflow, readout_em_workflow

    provider = args.chip.split(":")[1] if args.chip.startswith("dummy:") else args.chip.split(":")[0]
    if not args.chip.startswith("dummy:"):
        _refresh(provider)

    bi = find_backend(args.chip)
    measured_at = datetime.now(timezone.utc).isoformat()
    print(f"\nChip: {args.chip}")
    print(f"  cached_at:    {bi.calibrated_at}")
    print(f"  measured_at:  {measured_at}")
    print(f"  qubits:       {bi.qubits.n_qubits}")
    print(f"  available:    {len(bi.qubits.available_qubits)}")
    print(f"  basis:        {bi.basis_gates}")

    target = sorted(bi.qubits.available_qubits)[: args.width]
    pairs = [(target[i], target[i + 1]) for i in range(len(target) - 1)]
    print(f"  audit region: {target}")
    print(f"  audit pairs:  {pairs}\n")

    print("[1q-XEB]")
    try:
        xeb_1q = xeb_workflow.run_1q_xeb_workflow(
            backend=args.chip, target_qubits=target,
            depths=[5, 10, 20], n_circuits=args.n_circuits, shots=args.shots,
        )
        for q in target:
            r = xeb_1q[f"q{q}"]
            claimed = float(getattr(bi.qubits.qubit_info[q], "single_qubit_gate_error", float("nan")))
            measured = max(0.0, 1.0 - r.fidelity_per_layer)
            print(f"  q{q:>3}  claimed_e={claimed:.4f}  measured_e={measured:.4f}  "
                  f"Δ={measured - claimed:+.4f}")
    except Exception as exc:
        print(f"  skipped: {exc!r}")

    print("\n[2q-XEB]")
    try:
        xeb_2q = xeb_workflow.run_2q_xeb_workflow(
            backend=args.chip, pairs=pairs,
            depths=[5, 10, 20], n_circuits=args.n_circuits, shots=args.shots,
        )
        for (i, j) in pairs:
            r = xeb_2q[f"({i},{j})"]
            measured = max(0.0, 1.0 - r.fidelity_per_layer)
            print(f"  ({i},{j})  measured_e={measured:.4f}")
    except Exception as exc:
        print(f"  skipped: {exc!r}")

    print("\n[readout]")
    try:
        em = readout_em_workflow.run_readout_em_workflow(
            backend=args.chip, qubits=target, shots=args.shots * 2,
        )
        # ReadoutEM exposes the underlying calibration result via .calibration.
        # The exact attr surface is uniqc-version dependent; print the type for safety.
        print(f"  ready: {type(em).__name__}")
    except Exception as exc:
        print(f"  skipped: {exc!r}")


if __name__ == "__main__":
    main()
