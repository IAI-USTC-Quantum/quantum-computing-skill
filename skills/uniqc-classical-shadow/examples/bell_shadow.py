"""Classical-shadow demo: collect once, estimate many observables.

Compares against the analytic Bell-state values and the same observables
estimated via `pauli_expectation` (one basis-rotation circuit per Pauli).
"""

from __future__ import annotations

from uniqc import Circuit, pauli_expectation
from uniqc.algorithms.workflows import classical_shadow_workflow as csw


def main() -> None:
    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)

    paulis = ["ZZ", "XX", "YY", "ZI", "IZ"]

    # Shadow estimation
    res = csw.run_classical_shadow_workflow(c, paulis, shots=4000)
    print(f"snapshots = {res.n_snapshots}")
    print("Pauli   shadow      pauli_exp   analytic")
    print("-----   --------    ---------   --------")

    expected = {"ZZ": +1.0, "XX": +1.0, "YY": -1.0, "ZI": 0.0, "IZ": 0.0}

    for p in paulis:
        # Per-Pauli estimation via dedicated basis rotation
        try:
            pe = float(pauli_expectation(c, p))
        except Exception as exc:                       # noqa: BLE001
            pe = float("nan")
            print(f"  pauli_expectation({p}) failed: {exc}")
        sh = res.expectations[p]
        print(f"  {p}    {sh:+.4f}     {pe:+.4f}     {expected[p]:+.4f}")


if __name__ == "__main__":
    main()
