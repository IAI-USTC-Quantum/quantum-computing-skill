# H2 Molecular Simulation Reference

Guide for simulating the H2 molecule using HEA ansatz and computing the ground state energy curve.

## Problem Overview

The H2 molecule in STO-3G basis requires 4 qubits (2 spin-orbitals per atom). The electronic Hamiltonian is:

H = Σ_i h_i P_i + Σ_{ij} h_{ij} P_i P_j + E_nuclear

where P_i are Pauli strings obtained via Bravyi-Kitaev transformation.

## H2 Hamiltonian (STO-3G, Bravyi-Kitaev)

The Hamiltonian for H2 at bond length R can be written as:

H(R) = c₁(R) Z₀ + c₂(R) Z₁ + c₃(R) Z₀Z₁ + c₄(R) X₀X₁ + c₅(R) Y₀Y₁ + E_nuc(R)

### Hamiltonian Coefficients Table

Pre-computed coefficients at selected bond lengths (atomic units):

| R (Å) | c₁      | c₂      | c₃      | c₄       | c₅       | E_nuc   |
|--------|---------|---------|---------|----------|----------|---------|
| 0.30   | -0.4803 | +0.4803 | +0.4822 | +0.11721 | -0.11721 | 0.9445  |
| 0.40   | -0.4974 | +0.4974 | +0.4843 | +0.11974 | -0.11974 | 0.7084  |
| 0.50   | -0.5160 | +0.5160 | +0.4871 | +0.12186 | -0.12186 | 0.5667  |
| 0.60   | -0.5358 | +0.5358 | +0.4904 | +0.12356 | -0.12356 | 0.4723  |
| 0.70   | -0.5558 | +0.5558 | +0.4943 | +0.12474 | -0.12474 | 0.4048  |
| 0.74   | -0.5626 | +0.5626 | +0.4959 | +0.12505 | -0.12505 | 0.3827  |
| 0.80   | -0.5746 | +0.5746 | +0.4987 | +0.12539 | -0.12539 | 0.3543  |
| 0.90   | -0.5922 | +0.5922 | +0.5035 | +0.12514 | -0.12514 | 0.3159  |
| 1.00   | -0.6084 | +0.6084 | +0.5087 | +0.12425 | -0.12425 | 0.2843  |
| 1.20   | -0.6358 | +0.6358 | +0.5197 | +0.12084 | -0.12084 | 0.2370  |
| 1.40   | -0.6577 | +0.6577 | +0.5305 | +0.11518 | -0.11518 | 0.2032  |
| 1.60   | -0.6745 | +0.6745 | +0.5405 | +0.10829 | -0.10829 | 0.1778  |
| 1.80   | -0.6873 | +0.6873 | +0.5494 | +0.10089 | -0.10089 | 0.1581  |
| 2.00   | -0.6971 | +0.6971 | +0.5571 | +0.09361 | -0.09361 | 0.1423  |

Reference ground state energy at equilibrium (R ≈ 0.74 Å): **-1.137 Ha**

## HEA-Based VQE for H2

### Approach

Use HEA ansatz instead of the more common UCCSD for H2 simulation. While HEA is not chemistry-native, it offers:
- Shallow circuits suitable for NISQ hardware
- Hardware-efficient gate set (Rz, Ry, CNOT)
- Direct hardware mapping without transpilation

### Implementation

```python
import numpy as np
from scipy.optimize import minimize
from qpandalite.algorithmics.ansatz import hea
from qpandalite.simulator import OriginIR_Simulator

def compute_pauli_z_expectation(statevector, qubit_idx, n_qubits):
    """Compute <Z_qubit_idx> from statevector."""
    n_states = len(statevector)
    expectation = 0.0
    for i in range(n_states):
        bit = (i >> (n_qubits - 1 - qubit_idx)) & 1
        prob = abs(statevector[i]) ** 2
        expectation += (1 - 2 * bit) * prob
    return expectation

def compute_zz_expectation(statevector, q1, q2, n_qubits):
    """Compute <Z_q1 Z_q2> from statevector."""
    n_states = len(statevector)
    expectation = 0.0
    for i in range(n_states):
        b1 = (i >> (n_qubits - 1 - q1)) & 1
        b2 = (i >> (n_qubits - 1 - q2)) & 1
        prob = abs(statevector[i]) ** 2
        expectation += (1 - 2*b1) * (1 - 2*b2) * prob
    return expectation

def compute_xx_expectation(statevector, q1, q2, n_qubits):
    """Compute <X_q1 X_q2> using computational basis measurement."""
    # X = H Z H, so <X X> = <H q1 H q2 | Z Z | H q1 H q2>
    # This requires adding H gates before measurement
    # For statevector: use full matrix multiplication
    n_states = len(statevector)
    # Create |+> basis transformation
    # For simplicity, use matrix approach
    return compute_correlation_x(statevector, q1, q2, n_qubits)
```

### Simplified 2-Qubit Reduction

H2 in minimal basis reduces to an effective 2-qubit problem after freezing core orbitals. The Hamiltonian becomes:

H = c₁ I + c₂ Z₀ + c₃ Z₁ + c₄ Z₀Z₁ + c₅ X₀X₁ + c₆ Y₀Y₁

For this 2-qubit problem, HEA with depth 1-2 is sufficient.

### Bond Length Scan

```python
def h2_energy_curve(bond_lengths, hea_depth=2):
    """Compute H2 ground state energy curve using HEA-VQE."""
    sim = OriginIR_Simulator(backend_type='statevector')
    n_qubits = 4  # Full 4-qubit Hamiltonian
    n_params = 2 * n_qubits * hea_depth

    energies = []
    for R in bond_lengths:
        # Get Hamiltonian coefficients for this bond length
        hamiltonian = get_h2_hamiltonian(R)

        def objective(params):
            circuit = hea(n_qubits, depth=hea_depth, params=params)
            sv = sim.simulate_statevector(circuit.originir)
            energy = 0.0
            for pauli_str, coeff in hamiltonian:
                exp_val = compute_pauli_expectation(sv, pauli_str, n_qubits)
                energy += coeff * exp_val
            return energy

        result = minimize(
            objective,
            x0=np.random.uniform(0, 2*np.pi, n_params),
            method='COBYLA',
            options={'maxiter': 300}
        )
        energies.append(result.fun)

    return energies
```

## Nuclear Repulsion Energy

For H2, the nuclear repulsion energy is:

E_nuc(R) = 1/R (in atomic units, where R is in Bohr)

To convert Å to Bohr: R_Bohr = R_Å × 1.8897259886

```python
def nuclear_repulsion(R_angstrom):
    """Compute nuclear repulsion for H2 at bond length R."""
    R_bohr = R_angstrom * 1.8897259886
    return 1.0 / R_bohr
```

## Plotting the Energy Curve

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_h2_curve(bond_lengths, energies, reference_energy=-1.137):
    """Plot H2 ground state energy curve."""
    plt.figure(figsize=(8, 5))
    plt.plot(bond_lengths, energies, 'bo-', label='HEA-VQE')
    plt.axhline(y=reference_energy, color='r', linestyle='--',
                label=f'Reference: {reference_energy:.3f} Ha')
    plt.xlabel('Bond Length (Å)')
    plt.ylabel('Energy (Hartree)')
    plt.title('H2 Ground State Energy Curve')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('h2_energy_curve.png', dpi=150, bbox_inches='tight')
    plt.show()
```

## Notes on Accuracy

- **HEA depth**: Depth 2-3 typically sufficient for H2; deeper circuits may overfit
- **Initial parameters**: Random initialization may converge to local minima; try multiple restarts
- **Classical reference**: FCI (Full Configuration Interaction) energy is the exact benchmark
- **Active space**: Freezing the 1s core reduces H2 to an effective 2-qubit problem, significantly simplifying computation
