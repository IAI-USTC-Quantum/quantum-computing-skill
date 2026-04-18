#!/usr/bin/env python
"""Basic circuit demonstration - Bell state creation and simulation.

This example demonstrates:
- Creating a quantum circuit using the Circuit class
- Applying Hadamard and CNOT gates
- Generating OriginIR and QASM output
- Simulating the circuit locally
"""

from qpandalite.circuit_builder import Circuit
from qpandalite.simulator import OriginIR_Simulator


def main():
    print("=" * 60)
    print("QPanda-lite Basic Circuit Example: Bell State")
    print("=" * 60)

    # Create a 2-qubit circuit
    c = Circuit(2)

    # Build Bell state: |Φ+⟩ = (|00⟩ + |11⟩) / √2
    c.h(0)           # Hadamard on qubit 0
    c.cnot(0, 1)     # CNOT with control=0, target=1
    c.measure(0, 1)  # Measure both qubits

    # Output in OriginIR format
    print("\nOriginIR format:")
    print("-" * 40)
    print(c.originir)

    # Output in QASM format
    print("\nQASM format:")
    print("-" * 40)
    print(c.qasm)

    # Circuit properties
    print(f"\nCircuit properties:")
    print(f"  Qubits: {c.qubit_num}")
    print(f"  Classical bits: {c.cbit_num}")
    print(f"  Depth: {c.depth}")

    # Local simulation
    print("\nSimulating with 1000 shots...")
    sim = OriginIR_Simulator(backend_type='statevector')
    result = sim.simulate_shots(c.originir, shots=1000)

    print("\nMeasurement results:")
    print("-" * 40)
    for state, count in sorted(result.items()):
        binary = format(state, f'0{c.qubit_num}b')
        prob = count / 1000
        bar = '█' * int(prob * 40)
        print(f"  |{binary}⟩: {count:4d} ({prob:.2%}) {bar}")

    # Expected: ~50% |00⟩ and ~50% |11⟩ for Bell state
    print("\n✓ Expected ~50% |00⟩ and ~50% |11⟩ for Bell state")


if __name__ == "__main__":
    main()
