#!/usr/bin/env python3
"""Quantum Volume sweep against a UnifiedQuantum backend.

Builds qiskit `quantum_volume(n, n)` circuits, loads them into uniqc,
runs ideal statevector + hardware sampling, computes heavy-output
frequency, applies the 2/3 + 2σ pass rule, and reports QV = 2^n_max.

Usage:
    python qv_demo.py --backend dummy:local:simulator --max-n 4 --n-circuits 30
    python qv_demo.py --backend originq:WK_C180     --max-n 3 --n-circuits 100 --shots 1000

Requires:
    pip install unified-quantum
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def build_qv(n: int, *, seed: int):
    """Square QV: width n, depth n, with measurements on every qubit."""
    try:
        from qiskit.circuit import ClassicalRegister
        from qiskit.circuit.library import quantum_volume
        from qiskit.qasm2 import dumps
    except ImportError as exc:
        sys.exit(
            f"qiskit not installed ({exc}). qiskit is a core dependency of "
            "uniqc 0.0.13 — reinstall with: pip install --upgrade unified-quantum"
        )
    from uniqc import Circuit

    qc = quantum_volume(n, n, seed=seed)
    qc.add_register(ClassicalRegister(n, "c"))
    qc.measure(range(n), range(n))
    qasm = dumps(qc.decompose().decompose().decompose())
    return Circuit.from_qasm(qasm)


def heavy_set(circuit, *, n: int):
    import numpy as np
    from uniqc.simulator import Simulator

    sim = Simulator(backend_type="statevector")
    probs = np.asarray(sim.simulate_pmeasure(circuit.originir), dtype=float)
    if probs.size != 2 ** n:
        raise ValueError(f"expected 2^{n} probabilities, got {probs.size}")
    median = float(np.median(probs))
    return {int(i) for i, p in enumerate(probs) if p > median}, float(probs[probs > median].sum())


def heavy_freq(counts, heavy):
    total = sum(counts.values()) or 1
    hits = sum(c for bits, c in counts.items() if int(bits, 2) in heavy)
    return hits / total


def score(freqs):
    import numpy as np
    arr = np.asarray(freqs, dtype=float)
    K = arr.size
    mean  = float(arr.mean())
    sigma = float(arr.std(ddof=1)) if K > 1 else 0.0
    stderr = sigma / np.sqrt(K) if K > 1 else 0.0
    lcb_2sigma = mean - 2.0 * stderr if K > 1 else mean
    return {
        "K": K, "mean": mean, "sigma": sigma, "stderr": stderr,
        "lcb_2sigma": lcb_2sigma, "pass": lcb_2sigma > 2 / 3,
    }


def run_qv(backend: str, n: int, n_circuits: int, shots: int, seed_base: int = 0):
    from uniqc import submit_batch, wait_for_result

    print(f"  building {n_circuits} circuits at n={n} ...", flush=True)
    seeds = list(range(seed_base, seed_base + n_circuits))
    circuits, heavies, ideal_h = [], [], []
    for s in seeds:
        c = build_qv(n, seed=s)
        h, ih = heavy_set(c, n=n)
        circuits.append(c); heavies.append(h); ideal_h.append(ih)

    ideal_mean = sum(ideal_h) / len(ideal_h)
    print(f"  ideal mean heavy-output (asymptote (1+ln2)/2 ≈ 0.847): "
          f"{ideal_mean:.4f}", flush=True)
    print("  ↑ that is the theoretical CEILING for these specific circuits.", flush=True)
    print("    A perfect simulator should match it to within shot noise.", flush=True)

    print(f"  submitting batch to {backend!r} (shots={shots}) ...", flush=True)
    t0 = time.time()
    uid = submit_batch(circuits, backend=backend, shots=shots)
    results = wait_for_result(uid, timeout=900)
    elapsed = time.time() - t0
    print(f"  uid={uid} elapsed={elapsed:.1f}s", flush=True)

    freqs = []
    for r, h in zip(results, heavies):
        if r is None:
            print("  WARNING: a circuit failed; skipping for the score.")
            continue
        freqs.append(heavy_freq(r.counts, h))

    s = score(freqs)
    s["seeds"] = seeds
    s["freqs"] = freqs
    s["ideal_mean"] = ideal_mean
    # Hardware quality fraction: how close did we get to the ceiling?
    s["fraction_of_ideal"] = s["mean"] / ideal_mean if ideal_mean > 0 else float("nan")
    return s


def sweep(backend: str, max_n: int, n_circuits: int, shots: int, save_dir: Path | None):
    qv_n = 1
    summary = {}
    for n in range(2, max_n + 1):
        print(f"\n--- width n={n} ---")
        s = run_qv(backend, n, n_circuits, shots)
        verdict = "PASS" if s["pass"] else "FAIL"
        print(f"  n={n}: {verdict}  measured={s['mean']:.4f}  "
              f"(ideal={s['ideal_mean']:.4f}, "
              f"fraction_of_ideal={s['fraction_of_ideal']:.3f})  "
              f"LCB(2σ)={s['lcb_2sigma']:.4f}  "
              f"(threshold 0.6667)")
        summary[n] = s
        if save_dir is not None:
            save_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%dT%H%M%S")
            out = save_dir / f"qv-{backend.replace(':','_')}-n{n}-{stamp}.json"
            out.write_text(json.dumps({
                "backend": backend, "n": n, "shots": shots, **s,
            }, indent=2))
            print(f"  wrote {out}")
        if s["pass"]:
            qv_n = n
        else:
            break

    qv = 2 ** qv_n
    print("\n=== QV summary ===")
    for n, s in summary.items():
        print(f"  n={n}: pass={s['pass']}  measured={s['mean']:.4f}  "
              f"ideal={s['ideal_mean']:.4f}  "
              f"fraction_of_ideal={s['fraction_of_ideal']:.3f}  "
              f"LCB={s['lcb_2sigma']:.4f}")
    print(f"\nReported value: QV = 2^{qv_n} = {qv} on backend {backend!r}")
    print("Note: a *perfect* simulator achieves measured ≈ ideal (fraction ≈ 1.0);")
    print("the ideal value itself is bounded by Porter-Thomas at (1+ln2)/2 ≈ 0.847,")
    print("which is why 'noiseless' QV scores look like 0.85 not 1.0.")
    return qv, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Quantum Volume sweep")
    parser.add_argument("--backend", default="dummy:local:simulator",
                        help="single-string backend id (default: dummy:local:simulator)")
    parser.add_argument("--max-n", type=int, default=4,
                        help="largest width to attempt (default: 4)")
    parser.add_argument("--n-circuits", type=int, default=30,
                        help="random circuits per width (default: 30; use ≥100 for serious runs)")
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--save-dir", type=Path, default=None,
                        help="if set, write per-width JSON evidence")
    args = parser.parse_args()

    sweep(args.backend, args.max_n, args.n_circuits, args.shots, args.save_dir)


if __name__ == "__main__":
    main()
