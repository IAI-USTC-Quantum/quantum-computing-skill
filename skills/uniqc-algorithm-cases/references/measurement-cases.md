# Measurement-heavy algorithms: tomography & shadows

For "I just want to characterise this state / circuit" rather than "I
want an answer to an optimisation problem".

## State tomography

Reconstructs the full density matrix `ρ` from a tomographically
complete set of measurements. Cost scales as `4^n` measurement
settings, so this is realistic only for small `n_qubits` (≤ 4 in
practice).

```python
from uniqc import StateTomography
from uniqc.algorithms.core.measurement import state_tomography, tomography_summary

# Class form (recommended) — exposes get_readout_circuits() / execute()
tomo = StateTomography(my_circuit, qubits=[0, 1, 2])
rho  = tomo.execute(backend="dummy:local:simulator", shots=4096)

# Function form — single call, useful for one-shot scripts
rho = state_tomography(my_circuit, backend="dummy:local:simulator", shots=4096)

summary = tomography_summary(rho, print_summary=True)
# returns: {'eigenvalues': ..., 'purity': ..., 'trace': ..., 'is_pure': ..., 'fidelity': ...}
```

`tomography_summary` is pure NumPy/SciPy (no qutip dependency). Pass
`print_summary=False` to suppress the formatted stdout output and just
get the dict.

### Comparing to a target state

```python
import numpy as np
target = np.array([1, 0, 0, 0, 0, 0, 0, 1]) / np.sqrt(2)   # GHZ on 3 qubits
target_rho = np.outer(target, target.conj())

from uniqc.algorithms.core.measurement import tomography_summary
print(tomography_summary(rho, reference=target_rho, print_summary=True))
```

(`reference` may be a target density matrix or pure-state ket; check
the local installation to confirm signature.)

## Classical shadow

Estimates many expectation values from few measurements via random
Clifford / Pauli measurements. Much cheaper than full tomography when
you need ⟨H⟩ for a specific Pauli string but not the full ρ.

```python
from uniqc.algorithms.core.measurement import classical_shadow, shadow_expectation

snapshots = classical_shadow(
    my_circuit,
    backend="dummy:local:simulator",
    shots=512,
)

# Estimate any Pauli observable from the snapshots:
val = shadow_expectation(snapshots, "Z0Z1")
val_zz = shadow_expectation(snapshots, "ZZ")
val_xy = shadow_expectation(snapshots, "X0Y1")
```

### When to use which

| Situation                                                 | Pick                |
| --------------------------------------------------------- | ------------------- |
| Need full ρ (e.g. for fidelity vs. target)                | `state_tomography`  |
| Need many ⟨P_i⟩ for fixed circuit                         | `classical_shadow`  |
| Need a single ⟨H⟩ once                                    | `pauli_expectation` |
| `n_qubits ≥ 5`                                            | `classical_shadow`  |
| `n_qubits ≤ 3` and you want certified ρ                   | `state_tomography`  |

## Pauli expectation (single observable)

```python
from uniqc.algorithms.core.measurement import pauli_expectation

val = pauli_expectation(my_circuit, "Z0Z1", shots=4096)
```

For grouped multi-basis Pauli sums, the class form auto-batches
measurement bases:

```python
from uniqc import PauliExpectation
pe = PauliExpectation(my_circuit, [("Z0Z1", 1.0), ("X0X1", 0.5)])
result = pe.execute(backend="dummy:local:simulator", shots=4096)
```

`pauli_expectation` accepts three Pauli-string forms (compact, indexed,
or tuple-list) — see the `uniqc-result-analysis` skill's
`expectations.md` reference.

## Practical defaults

- Tomography: 4096 shots per setting, 50–200 settings depending on n.
  Total wall-clock can be hours on real hardware — start on dummy.
- Shadows: `shots=512` is the lower end; bump to 4096 for tight
  estimates. Variance per observable scales as `4^locality / shots`.
- Always print `purity = Tr(ρ²)` after tomography — values much below 1
  indicate either decoherence or insufficient shots per setting.

## Common mistakes

- Forgetting that tomography measures the *output* state of the
  circuit; do **not** add `measure(...)` to the circuit yourself.
  `StateTomography` / `state_tomography` insert the right basis
  rotations + measurements.
- Calling `basis_rotation_measurement` on a circuit without explicit
  `MEASURE` instructions — uniqc ≥ 0.0.11.dev30 raises `ValueError` for
  X/Y bases (was previously a silent no-op).
- Comparing `purity` from a noisy backend to 1 and concluding "the
  state is mixed". Run a noiseless dummy first to set the baseline.
