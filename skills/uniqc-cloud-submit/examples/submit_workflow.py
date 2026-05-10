#!/usr/bin/env python3
"""End-to-end submit + poll demo, defaults to dummy backend so it always runs.

Usage:
    python submit_workflow.py
    python submit_workflow.py --backend originq:WK_C180 --shots 200
    python submit_workflow.py --file path/to/circuit.originir --backend dummy:local:simulator

Workflow demonstrated:
    1. uniqc.config sanity check (programmatic equivalent of `uniqc config validate`).
    2. Build / load a Circuit, persist to .originir + .qasm.
    3. dry_run_task -> submit_task -> query_task -> wait_for_result.
    4. Print the resulting UnifiedResult counts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def healthcheck(backend: str) -> None:
    """Programmatic equivalent of `uniqc config validate` for the chosen platform."""
    from uniqc import config as cfg

    platform = backend.split(":", 1)[0]
    if platform == "dummy":
        return                                          # no auth needed
    if platform not in cfg.SUPPORTED_PLATFORMS:
        sys.exit(f"Unknown platform '{platform}' (parsed from --backend {backend!r}).")
    if not cfg.has_platform_credentials(platform):
        sys.exit(
            f"No credentials for platform '{platform}'.\n"
            f"  uniqc config set {platform}.token <YOUR_TOKEN>\n"
            "  (Quark uses 'quark.QUARK_API_KEY' instead of 'token'.)"
        )


def load_or_build_circuit(file: Path | None):
    from uniqc import Circuit

    if file is None:
        c = Circuit(2)
        c.h(0)
        c.cnot(0, 1)
        c.measure(0)
        c.measure(1)
        return c
    text = file.read_text()
    if file.suffix == ".originir":
        return Circuit.from_originir(text)
    if file.suffix == ".qasm":
        return Circuit.from_qasm(text)
    sys.exit(f"Unsupported file extension: {file.suffix}")


def persist_program_files(circuit, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "circuit.originir").write_text(circuit.originir)
    (out_dir / "circuit.qasm").write_text(circuit.qasm)
    print(f"  wrote {out_dir/'circuit.originir'}")
    print(f"  wrote {out_dir/'circuit.qasm'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="UnifiedQuantum submit + poll demo")
    parser.add_argument("--backend", default="dummy:local:simulator",
                        help="single-string backend id, e.g. dummy:local:simulator / dummy:local:virtual-line-3 / originq:WK_C180")
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--file", type=Path, default=None,
                        help="optional .originir / .qasm to submit instead of the built-in Bell state")
    parser.add_argument("--out", type=Path, default=Path("./.uniqc-submit-demo"),
                        help="where to write the generated circuit files")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    print("[1/5] healthcheck")
    healthcheck(args.backend)
    print("       OK")

    print("[2/5] build / load circuit")
    circuit = load_or_build_circuit(args.file)
    persist_program_files(circuit, args.out)

    from uniqc import dry_run_task, submit_task, query_task, wait_for_result

    print(f"[3/5] dry_run_task(backend={args.backend!r}, shots={args.shots})")
    check = dry_run_task(circuit, backend=args.backend, shots=args.shots)
    if not check.success:
        sys.exit(f"dry-run failed: {check.error or check.details}")
    print("       OK")

    print(f"[4/5] submit_task(backend={args.backend!r}, shots={args.shots})")
    uid = submit_task(circuit, backend=args.backend, shots=args.shots)
    print(f"       uniqc task id: {uid}")

    info = query_task(uid)
    print(f"       initial status: {getattr(info, 'status', info)}")

    print(f"[5/5] wait_for_result(timeout={args.timeout}s)")
    result = wait_for_result(uid, timeout=args.timeout, poll_interval=2)
    if result is None:
        sys.exit("       FAILED — task did not return a result.")
    if isinstance(result, list):
        for i, r in enumerate(result):
            print(f"       circuit {i}: {dict(r)}")
    else:
        print(f"       counts: {dict(result)}")
        print(f"       shots:  {result.shots}")
        print(f"       platform: {result.platform}")


if __name__ == "__main__":
    main()
