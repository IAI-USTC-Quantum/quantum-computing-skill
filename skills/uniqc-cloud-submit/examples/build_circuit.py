#!/usr/bin/env python3
"""Build a small Circuit and persist as both .originir and .qasm.

Usage:
    python build_circuit.py [--out-dir ./.uniqc-circuits]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from uniqc import Circuit


def bell_circuit() -> Circuit:
    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)
    return c


def main() -> None:
    parser = argparse.ArgumentParser(description="Author and persist a quantum-program file")
    parser.add_argument("--out-dir", type=Path, default=Path("./.uniqc-circuits"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    c = bell_circuit()

    originir_path = args.out_dir / "bell.originir"
    qasm_path = args.out_dir / "bell.qasm"
    originir_path.write_text(c.originir)
    qasm_path.write_text(c.qasm)

    print(f"OriginIR -> {originir_path}")
    print(f"OpenQASM -> {qasm_path}")
    print("\nNext step:")
    print(f"  uniqc submit {originir_path} --backend dummy:local:simulator --shots 1000 --dry-run")


if __name__ == "__main__":
    main()
