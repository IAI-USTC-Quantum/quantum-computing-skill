"""Demonstrate every supported circuit-format round-trip in uniqc 0.0.13."""

from __future__ import annotations

from uniqc import Circuit, normalize_to_circuit
from uniqc.simulator import Simulator


def build_bell() -> Circuit:
    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)
    return c


def main() -> None:
    c = build_bell()
    sim = Simulator(backend_type="statevector")

    # Reference: probabilities from the uniqc Circuit
    probs_ref = sim.simulate_pmeasure(c)
    print("ref probs (uniqc Circuit):", probs_ref)

    # 1. Circuit -> OriginIR str -> Circuit (round-trip)
    ir = c.originir
    nc = normalize_to_circuit(ir)
    print(f"\n[OriginIR] type={nc.type}")
    print(sim.simulate_pmeasure(ir))

    # 2. Circuit -> QASM2 str -> Circuit
    qasm = c.qasm
    print(f"\n[QASM2] type={normalize_to_circuit(qasm).type}")
    print(sim.simulate_pmeasure(qasm))

    # 3. Circuit -> qiskit.QuantumCircuit -> Circuit
    qc = c.to_qiskit_circuit()
    print(f"\n[qiskit] {type(qc).__name__}, type tag={normalize_to_circuit(qc).type}")
    print(sim.simulate_pmeasure(qc))

    # 4. Circuit -> pyqpanda3 (requires unified-quantum[originq])
    try:
        qpc = c.to_pyqpanda3_circuit()
        print(f"\n[pyqpanda3] {type(qpc).__name__}, type tag={normalize_to_circuit(qpc).type}")
        print(sim.simulate_pmeasure(qpc))
    except ImportError as exc:
        print(f"\n[pyqpanda3] skipped (install unified-quantum[originq]): {exc}")


if __name__ == "__main__":
    main()
