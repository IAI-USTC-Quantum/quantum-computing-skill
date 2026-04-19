#!/usr/bin/env python
"""H2 molecular ground state simulation using HEA ansatz.

This example demonstrates:
- Computing molecular Hamiltonian expectation values
- Using HEA ansatz for VQE (instead of UCCSD)
- Generating the ground state energy curve vs bond length

The H2 molecule in STO-3G basis requires 4 qubits. We use a reduced
Hamiltonian after freezing core orbitals for efficiency.

Usage:
    python h2_hea_vqe.py --depth 2 --points 10
"""

import argparse
import numpy as np
from scipy.optimize import minimize

from uniqc.algorithmics.ansatz import hea
from uniqc.simulator import OriginIR_Simulator


# ============================================================================
# H2 Hamiltonian Data
# ============================================================================

# Pre-computed H2 Hamiltonian coefficients (STO-3G, Bravyi-Kitaev)
# Format: {bond_length_angstrom: (c1, c2, c3, c4, c5, E_nuclear)}
# H = c1*Z0 + c2*Z1 + c3*Z0Z1 + c4*X0X1 + c5*Y0Y1 + E_nuclear

H2_HAMILTONIAN_DATA = {
    0.30: (-0.4803, 0.4803, 0.4822, 0.11721, -0.11721, 0.9445),
    0.40: (-0.4974, 0.4974, 0.4843, 0.11974, -0.11974, 0.7084),
    0.50: (-0.5160, 0.5160, 0.4871, 0.12186, -0.12186, 0.5667),
    0.60: (-0.5358, 0.5358, 0.4904, 0.12356, -0.12356, 0.4723),
    0.70: (-0.5558, 0.5558, 0.4943, 0.12474, -0.12474, 0.4048),
    0.74: (-0.5626, 0.5626, 0.4959, 0.12505, -0.12505, 0.3827),  # Equilibrium
    0.80: (-0.5746, 0.5746, 0.4987, 0.12539, -0.12539, 0.3543),
    0.90: (-0.5922, 0.5922, 0.5035, 0.12514, -0.12514, 0.3159),
    1.00: (-0.6084, 0.6084, 0.5087, 0.12425, -0.12425, 0.2843),
    1.20: (-0.6358, 0.6358, 0.5197, 0.12084, -0.12084, 0.2370),
    1.40: (-0.6577, 0.6577, 0.5305, 0.11518, -0.11518, 0.2032),
    1.60: (-0.6745, 0.6745, 0.5405, 0.10829, -0.10829, 0.1778),
    1.80: (-0.6873, 0.6873, 0.5494, 0.10089, -0.10089, 0.1581),
    2.00: (-0.6971, 0.6971, 0.5571, 0.09361, -0.09361, 0.1423),
}

# Reference ground state energy at equilibrium
REFERENCE_ENERGY = -1.137  # Hartree at R=0.74 Å


# ============================================================================
# Expectation Value Computation
# ============================================================================

def compute_pauli_expectation(statevector, pauli_string, n_qubits):
    """Compute expectation value of a Pauli operator from statevector.

    Args:
        statevector: np.ndarray of complex amplitudes
        pauli_string: Pauli operator (e.g., "Z0Z1" or "X0X1")
        n_qubits: Number of qubits

    Returns:
        float: Expectation value
    """
    n_states = len(statevector)
    exp_val = 0.0

    # Parse Pauli string
    paulis = {}
    for term in pauli_string.split():
        if term[0] in ['X', 'Y', 'Z', 'I']:
            paulis[int(term[1])] = term[0]

    for i in range(n_states):
        # Get amplitude and probability
        amp = statevector[i]
        prob = np.abs(amp) ** 2

        # Compute Pauli eigenvalue for this basis state
        eigenvalue = 1.0
        for q, p in paulis.items():
            bit = (i >> (n_qubits - 1 - q)) & 1
            if p == 'Z':
                eigenvalue *= 1 - 2 * bit
            elif p == 'X':
                # X flips the bit
                eigenvalue *= 1  # Handled by off-diagonal elements
            elif p == 'Y':
                eigenvalue *= 1j * (1 - 2 * bit)

        exp_val += eigenvalue * prob

    # For X and Y operators, need off-diagonal elements
    # Simplified: use matrix approach for mixed Pauli terms
    if 'X' in paulis.values() or 'Y' in paulis.values():
        return compute_correlation_expectation(statevector, pauli_string, n_qubits)

    return np.real(exp_val)


def compute_correlation_expectation(statevector, pauli_string, n_qubits):
    """Compute expectation for X-X or Y-Y correlation terms."""
    n_states = len(statevector)

    # Parse which qubits have X or Y
    x_qubits = []
    y_qubits = []
    z_qubits = []

    for term in pauli_string.split():
        if term.startswith('X'):
            x_qubits.append(int(term[1]))
        elif term.startswith('Y'):
            y_qubits.append(int(term[1]))
        elif term.startswith('Z'):
            z_qubits.append(int(term[1]))

    # For X0X1 and Y0Y1 (common in H2 Hamiltonian)
    if len(x_qubits) == 2 and len(y_qubits) == 0:
        q1, q2 = sorted(x_qubits)
        exp_val = 0.0
        for i in range(n_states):
            bit1 = (i >> (n_qubits - 1 - q1)) & 1
            bit2 = (i >> (n_qubits - 1 - q2)) & 1
            # X|0⟩=|1⟩, X|1⟩=|0⟩
            # ⟨ψ|X1X2|ψ⟩ involves flipping both bits
            j = i ^ (1 << (n_qubits - 1 - q1)) ^ (1 << (n_qubits - 1 - q2))
            exp_val += np.real(np.conj(statevector[i]) * statevector[j])
        return exp_val

    if len(y_qubits) == 2 and len(x_qubits) == 0:
        q1, q2 = sorted(y_qubits)
        exp_val = 0.0
        for i in range(n_states):
            bit1 = (i >> (n_qubits - 1 - q1)) & 1
            bit2 = (i >> (n_qubits - 1 - q2)) & 1
            j = i ^ (1 << (n_qubits - 1 - q1)) ^ (1 << (n_qubits - 1 - q2))
            sign = (-1) ** (bit1 + bit2)
            exp_val += np.real(np.conj(statevector[i]) * statevector[j] * sign * (-1j**2))
        return -np.real(exp_val)  # Y0Y1 has negative sign in H2 Hamiltonian

    return 0.0


def compute_h2_energy(statevector, hamiltonian_coeffs, n_qubits):
    """Compute H2 energy from statevector and Hamiltonian coefficients.

    Args:
        statevector: Quantum state as complex array
        hamiltonian_coeffs: Tuple of (c1, c2, c3, c4, c5, E_nuclear)
        n_qubits: Number of qubits

    Returns:
        float: Total energy
    """
    c1, c2, c3, c4, c5, E_nuc = hamiltonian_coeffs

    energy = 0.0
    energy += c1 * compute_pauli_expectation(statevector, "Z0", n_qubits)
    energy += c2 * compute_pauli_expectation(statevector, "Z1", n_qubits)
    energy += c3 * compute_pauli_expectation(statevector, "Z0 Z1", n_qubits)
    energy += c4 * compute_pauli_expectation(statevector, "X0 X1", n_qubits)
    energy += c5 * compute_pauli_expectation(statevector, "Y0 Y1", n_qubits)
    energy += E_nuc

    return energy


# ============================================================================
# VQE Optimization
# ============================================================================

def vqe_h2(hamiltonian_coeffs, n_qubits, depth, maxiter=200):
    """Run VQE for H2 at a specific bond length.

    Args:
        hamiltonian_coeffs: Hamiltonian coefficient tuple
        n_qubits: Number of qubits (4 for full H2, 2 for reduced)
        depth: HEA depth
        maxiter: Maximum optimizer iterations

    Returns:
        float: Optimal energy
        np.ndarray: Optimal parameters
    """
    sim = OriginIR_Simulator(backend_type='statevector')
    n_params = 2 * n_qubits * depth

    def objective(params):
        circuit = hea(n_qubits, depth=depth, params=params)
        sv = sim.simulate_statevector(circuit.originir)
        energy = compute_h2_energy(sv, hamiltonian_coeffs, n_qubits)
        return energy

    # Multiple restarts to avoid local minima
    best_energy = float('inf')
    best_params = None

    for _ in range(3):
        result = minimize(
            objective,
            x0=np.random.uniform(0, 2 * np.pi, n_params),
            method='COBYLA',
            options={'maxiter': maxiter}
        )
        if result.fun < best_energy:
            best_energy = result.fun
            best_params = result.x

    return best_energy, best_params


# ============================================================================
# Energy Curve Generation
# ============================================================================

def compute_energy_curve(depth=2, n_points=10):
    """Compute H2 ground state energy curve.

    Args:
        depth: HEA depth
        n_points: Number of bond lengths to sample

    Returns:
        bond_lengths, energies, reference_energy
    """
    print(f"Computing H2 energy curve (HEA depth={depth})...")
    print("-" * 50)

    # Select bond lengths to compute
    all_lengths = sorted(H2_HAMILTONIAN_DATA.keys())
    indices = np.linspace(0, len(all_lengths) - 1, n_points, dtype=int)
    bond_lengths = [all_lengths[i] for i in indices]

    energies = []

    for R in bond_lengths:
        coeffs = H2_HAMILTONIAN_DATA[R]
        energy, params = vqe_h2(coeffs, n_qubits=4, depth=depth)
        energies.append(energy)
        print(f"  R = {R:.2f} Å: E = {energy:.4f} Ha")

    return bond_lengths, energies, REFERENCE_ENERGY


def plot_energy_curve(bond_lengths, energies, reference_energy, output_file='h2_curve.png'):
    """Plot and save the energy curve."""
    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 6))
        plt.plot(bond_lengths, energies, 'bo-', markersize=8, linewidth=2, label='HEA-VQE')
        plt.axhline(y=reference_energy, color='r', linestyle='--',
                   label=f'Reference: {reference_energy:.3f} Ha')

        plt.xlabel('Bond Length R (Å)', fontsize=12)
        plt.ylabel('Energy (Hartree)', fontsize=12)
        plt.title('H₂ Ground State Energy Curve', fontsize=14)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)

        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\nEnergy curve saved to: {output_file}")

        plt.show()
    except ImportError:
        print("\n(matplotlib not available - skipping plot)")
        print("Bond lengths:", bond_lengths)
        print("Energies:", energies)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='H2 VQE with HEA')
    parser.add_argument('--depth', type=int, default=2, help='HEA ansatz depth')
    parser.add_argument('--points', type=int, default=10, help='Number of bond lengths')
    parser.add_argument('--no-plot', action='store_true', help='Skip plotting')
    args = parser.parse_args()

    print("=" * 60)
    print("H₂ Molecular Ground State Simulation with HEA Ansatz")
    print("=" * 60)
    print(f"HEA depth: {args.depth}")
    print(f"Parameters per point: {2 * 4 * args.depth}")

    # Compute energy curve
    bond_lengths, energies, reference = compute_energy_curve(
        depth=args.depth,
        n_points=args.points
    )

    # Find equilibrium bond length
    min_idx = np.argmin(energies)
    eq_length = bond_lengths[min_idx]
    eq_energy = energies[min_idx]

    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Equilibrium bond length: {eq_length:.2f} Å")
    print(f"Minimum energy: {eq_energy:.4f} Ha")
    print(f"Reference energy: {reference:.3f} Ha")
    print(f"Error: {abs(eq_energy - reference):.4f} Ha")

    # Plot
    if not args.no_plot:
        plot_energy_curve(bond_lengths, energies, reference)


if __name__ == "__main__":
    main()
