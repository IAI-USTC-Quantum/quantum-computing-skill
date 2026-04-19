#!/usr/bin/env python
"""Cloud platform submission example for UnifiedQuantum.

This example demonstrates:
- Building quantum circuits programmatically
- Submitting circuits to quantum cloud platforms
- Polling for results
- Error handling

Configuration:
    Platform credentials live in the unified config file.
    Initialize and populate it with:
        uniqc config init
        uniqc config set originq.token YOUR_TOKEN
        uniqc config set quafu.token YOUR_TOKEN
        uniqc config set ibm.token YOUR_TOKEN

Usage:
    python cloud_submission.py
"""

import os

from uniqc.circuit_builder import Circuit
from uniqc import submit_task, wait_for_result
from uniqc.config import (
    get_originq_config,
    get_quafu_config,
    get_ibm_config,
    ConfigError,
)


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
    """Submit circuit to OriginQ cloud platform."""
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
    """Submit circuit to Quafu (BAQIS) cloud platform."""
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
    """
    print("\nSubmitting to dummy adapter (local simulation)...")

    # Force dummy mode for this run
    os.environ['UNIQC_DUMMY'] = 'true'

    task_id = submit_task(
        circuit.originir,
        backend='dummy',
        shots=shots
    )
    print(f"Task ID: {task_id}")

    result = wait_for_result(task_id, backend='dummy', timeout=10)
    return result


# ============================================================================
# Configuration Helpers
# ============================================================================

def _has_token(loader):
    """Return True if the config loader yields a non-empty token."""
    try:
        cfg = loader()
    except ConfigError:
        return False
    token = cfg.get("token") if isinstance(cfg, dict) else None
    return bool(token)


# ============================================================================
# Result Processing
# ============================================================================

def print_results(result, n_qubits):
    """Pretty print measurement results."""
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
    print("UnifiedQuantum Cloud Submission Example")
    print("=" * 60)

    # Create circuits
    print("\nCreating circuits...")
    ghz_circuit = create_ghz_circuit(n_qubits=4)
    print(f"GHZ circuit: {ghz_circuit.qubit_num} qubits, depth {ghz_circuit.depth}")

    # Check configuration via `~/.uniqc/uniqc.yml`
    originq_ready = _has_token(get_originq_config)
    quafu_ready = _has_token(get_quafu_config)
    ibm_ready = _has_token(get_ibm_config)

    print("\nConfiguration status:")
    print(f"  originq.token: {'Set' if originq_ready else 'Not set'}")
    print(f"  quafu.token:   {'Set' if quafu_ready else 'Not set'}")
    print(f"  ibm.token:     {'Set' if ibm_ready else 'Not set'}")

    # 1. Always test with dummy adapter first
    print("\n" + "=" * 60)
    print("Test 1: Dummy adapter (local simulation)")
    print("=" * 60)

    result = submit_to_dummy(ghz_circuit, shots=1000)
    print_results(result, ghz_circuit.qubit_num)

    # 2. Submit to OriginQ if configured
    if originq_ready:
        print("\n" + "=" * 60)
        print("Test 2: OriginQ cloud platform")
        print("=" * 60)

        result = submit_to_originq(ghz_circuit, shots=1000, wait=True, timeout=300)
        print_results(result, ghz_circuit.qubit_num)
    else:
        print("\nOriginQ not configured. Run: uniqc config set originq.token YOUR_TOKEN")

    # 3. Submit to Quafu if configured
    if quafu_ready:
        print("\n" + "=" * 60)
        print("Test 3: Quafu cloud platform")
        print("=" * 60)

        result = submit_to_quafu(ghz_circuit, chip_id='ScQ-P10', shots=1000, wait=True)
        print_results(result, ghz_circuit.qubit_num)
    else:
        print("\nQuafu not configured. Run: uniqc config set quafu.token YOUR_TOKEN")

    print("\n" + "=" * 60)
    print("Cloud submission example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
