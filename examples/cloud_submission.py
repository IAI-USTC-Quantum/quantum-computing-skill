#!/usr/bin/env python
"""Cloud platform submission example for QPanda-lite.

This example demonstrates:
- Building quantum circuits programmatically
- Submitting circuits to quantum cloud platforms
- Polling for results
- Error handling

Configuration:
    Set environment variables or use config file:
    - QPANDA_API_KEY (OriginQ)
    - QUAFU_API_TOKEN (Quafu)
    - IBM_TOKEN (IBM Quantum)

    Or run: qpandalite config init
            qpandalite config set originq.token YOUR_TOKEN

Usage:
    python cloud_submission.py
"""

import os
import time

from qpandalite.circuit_builder import Circuit
from qpandalite import submit_task, query_task, wait_for_result


# ============================================================================
# Circuit Preparation
# ============================================================================

def create_ghz_circuit(n_qubits=4):
    """Create an n-qubit GHZ state circuit.

    GHZ state: (|000...0⟩ + |111...1⟩) / √2

    Args:
        n_qubits: Number of qubits

    Returns:
        Circuit: GHZ state circuit
    """
    c = Circuit(n_qubits)

    # Create superposition
    c.h(0)

    # Entangle all qubits
    for i in range(n_qubits - 1):
        c.cnot(i, i + 1)

    # Measure all qubits
    c.measure(*range(n_qubits))

    return c


def create_random_circuit(n_qubits=4, depth=3):
    """Create a random parameterized circuit.

    Args:
        n_qubits: Number of qubits
        depth: Circuit depth

    Returns:
        Circuit: Random circuit
    """
    import numpy as np

    c = Circuit(n_qubits)

    for d in range(depth):
        # Single-qubit rotations
        for q in range(n_qubits):
            theta = np.random.uniform(0, 2 * np.pi)
            c.ry(q, theta)

        # Entangling layer
        for q in range(n_qubits - 1):
            c.cnot(q, q + 1)

    c.measure(*range(n_qubits))
    return c


# ============================================================================
# Submission Functions
# ============================================================================

def submit_to_originq(circuit, shots=1000, wait=True, timeout=300):
    """Submit circuit to OriginQ cloud platform.

    Args:
        circuit: Circuit object
        shots: Number of measurement shots
        wait: Whether to wait for result
        timeout: Maximum wait time in seconds

    Returns:
        dict or str: Result dict or task ID
    """
    print("\nSubmitting to OriginQ...")

    try:
        task_id = submit_task(
            circuit.originir,
            backend='originq',
            shots=shots
        )
        print(f"Task ID: {task_id}")

        if wait:
            print(f"Waiting for result (timeout: {timeout}s)...")
            result = wait_for_result(task_id, backend='originq', timeout=timeout)
            return result
        return task_id

    except Exception as e:
        print(f"OriginQ submission failed: {e}")
        return None


def submit_to_quafu(circuit, chip_id='ScQ-P10', shots=1000, wait=True, timeout=300):
    """Submit circuit to Quafu (BAQIS) cloud platform.

    Args:
        circuit: Circuit object
        chip_id: Target chip (e.g., 'ScQ-P10', 'ScQ-P18')
        shots: Number of measurement shots
        wait: Whether to wait for result
        timeout: Maximum wait time in seconds

    Returns:
        dict or str: Result dict or task ID
    """
    print(f"\nSubmitting to Quafu (chip: {chip_id})...")

    try:
        task_id = submit_task(
            circuit.originir,
            backend='quafu',
            shots=shots,
            chip_id=chip_id
        )
        print(f"Task ID: {task_id}")

        if wait:
            print(f"Waiting for result (timeout: {timeout}s)...")
            result = wait_for_result(task_id, backend='quafu', timeout=timeout)
            return result
        return task_id

    except Exception as e:
        print(f"Quafu submission failed: {e}")
        return None


def submit_to_dummy(circuit, shots=1000):
    """Submit circuit using dummy adapter (local simulation).

    This is useful for testing without cloud credentials.

    Args:
        circuit: Circuit object
        shots: Number of measurement shots

    Returns:
        dict: Simulated measurement results
    """
    print("\nSubmitting to dummy adapter (local simulation)...")

    # Set dummy mode
    os.environ['QPANDALITE_DUMMY'] = 'true'

    task_id = submit_task(
        circuit.originir,
        backend='dummy',
        shots=shots
    )
    print(f"Task ID: {task_id}")

    result = wait_for_result(task_id, backend='dummy', timeout=10)
    return result


# ============================================================================
# Result Processing
# ============================================================================

def print_results(result, n_qubits):
    """Pretty print measurement results.

    Args:
        result: Result dict from cloud
        n_qubits: Number of qubits for bit string formatting
    """
    if result is None:
        print("No results available")
        return

    print("\nMeasurement Results:")
    print("-" * 40)

    if 'counts' in result or 'result' in result:
        counts = result.get('counts', result.get('result', {}))

        # Sort by count descending
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        total = sum(counts.values()) if counts else 1

        for state, count in sorted_counts[:10]:  # Top 10 states
            if isinstance(state, int):
                binary = format(state, f'0{n_qubits}b')
            else:
                binary = str(state)
            prob = count / total if total > 0 else 0
            bar = '█' * int(prob * 30)
            print(f"  |{binary}⟩: {count:5d} ({prob:.1%}) {bar}")

        if len(sorted_counts) > 10:
            print(f"  ... and {len(sorted_counts) - 10} more states")
    else:
        print(f"Result: {result}")


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 60)
    print("QPanda-lite Cloud Submission Example")
    print("=" * 60)

    # Create circuits
    print("\nCreating circuits...")
    ghz_circuit = create_ghz_circuit(n_qubits=4)
    print(f"GHZ circuit: {ghz_circuit.qubit_num} qubits, depth {ghz_circuit.depth}")

    # Check configuration
    print("\nConfiguration status:")
    print(f"  QPANDA_API_KEY: {'Set' if os.environ.get('QPANDA_API_KEY') else 'Not set'}")
    print(f"  QUAFU_API_TOKEN: {'Set' if os.environ.get('QUAFU_API_TOKEN') else 'Not set'}")
    print(f"  IBM_TOKEN: {'Set' if os.environ.get('IBM_TOKEN') else 'Not set'}")

    # 1. Always test with dummy adapter first
    print("\n" + "=" * 60)
    print("Test 1: Dummy adapter (local simulation)")
    print("=" * 60)

    result = submit_to_dummy(ghz_circuit, shots=1000)
    print_results(result, ghz_circuit.qubit_num)

    # 2. Submit to OriginQ if configured
    if os.environ.get('QPANDA_API_KEY'):
        print("\n" + "=" * 60)
        print("Test 2: OriginQ cloud platform")
        print("=" * 60)

        result = submit_to_originq(ghz_circuit, shots=1000, wait=True, timeout=300)
        print_results(result, ghz_circuit.qubit_num)
    else:
        print("\nOriginQ not configured. Set QPANDA_API_KEY to test.")

    # 3. Submit to Quafu if configured
    if os.environ.get('QUAFU_API_TOKEN'):
        print("\n" + "=" * 60)
        print("Test 3: Quafu cloud platform")
        print("=" * 60)

        result = submit_to_quafu(ghz_circuit, chip_id='ScQ-P10', shots=1000, wait=True)
        print_results(result, ghz_circuit.qubit_num)
    else:
        print("\nQuafu not configured. Set QUAFU_API_TOKEN to test.")

    print("\n" + "=" * 60)
    print("Cloud submission example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
