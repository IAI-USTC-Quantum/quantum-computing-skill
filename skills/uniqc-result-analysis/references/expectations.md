# Computing expectation values from results

After you have a `UnifiedResult` (or just a `counts` dict), you usually
care about an observable rather than the raw bitstring distribution. The
canonical helper is:

```python
from uniqc.algorithms.core.measurement import pauli_expectation
# or top-level: from uniqc import PauliExpectation
```

`pauli_expectation` accepts three Pauli-string forms (uniqc ≥ 0.0.11.dev30):

1. **Compact / positional** — length must equal `n_qubits`:
   ```python
   pauli_expectation(circuit, "ZIZ")     # Z⊗I⊗Z, q2 q1 q0 (left-to-right)
   ```
2. **Indexed** — only the non-`I` qubits, in any order:
   ```python
   pauli_expectation(circuit, "Z0Z2")
   ```
3. **Tuple list** — explicit `[(op, qubit), ...]`:
   ```python
   pauli_expectation(circuit, [("Z", 0), ("Z", 2)])
   ```

Pick one form and stay consistent across a script — mixing them is a
common source of off-by-one bugs.

## Hand-rolled from a counts dict

When you already have `counts` and you want `<Z_i Z_j>` or `<Z_i>`,
nothing fancy is needed:

```python
def expectation_zi(counts: dict[str, int], i: int) -> float:
    total = sum(counts.values())
    val = 0
    for bits, n in counts.items():
        bit = bits[-1 - i]                 # little-endian: q0 is rightmost
        val += n * (1 if bit == "0" else -1)
    return val / total

def expectation_zizj(counts: dict[str, int], i: int, j: int) -> float:
    total = sum(counts.values())
    val = 0
    for bits, n in counts.items():
        bi = bits[-1 - i]
        bj = bits[-1 - j]
        val += n * (1 if bi == bj else -1)
    return val / total
```

Use `pauli_expectation` for X / Y observables — it inserts the right
basis-rotation gates before measurement.

## Evaluating a Hamiltonian as a sum of Pauli terms

```python
def hamiltonian_expectation(circuit, terms, *, shots=None):
    """terms: list[tuple[pauli_string, coeff]]"""
    return sum(coeff * pauli_expectation(circuit, p, shots=shots) for p, coeff in terms)

H = [("ZZ", 1.0), ("XI", 0.5), ("IX", 0.5)]
print(hamiltonian_expectation(my_circuit, H, shots=4096))
```

For larger Hamiltonians where you want grouped diagonalization, use the
class form:

```python
from uniqc import PauliExpectation
pe = PauliExpectation(my_circuit, [("ZZ", 1.0), ("XI", 0.5)])
circuits = pe.get_readout_circuits()           # circuits per measurement basis
result   = pe.execute(backend="dummy:local:simulator")          # dispatch + aggregate
print(result)
```

## State tomography

```python
from uniqc.algorithms.core.measurement import state_tomography, tomography_summary

rho = state_tomography(my_circuit, backend="dummy:local:simulator", shots=4096)
summary = tomography_summary(rho, print_summary=True)   # eigenvalues / purity / fidelity
```

`tomography_summary` is pure NumPy/SciPy (no qutip) and returns a dict.

## Classical shadow (low-shot expectation values)

```python
from uniqc import classical_shadow, shadow_expectation

snapshots = classical_shadow(my_circuit, backend="dummy:local:simulator", shots=512)
val = shadow_expectation(snapshots, "ZZ")
```

This is much cheaper than full tomography when you only need a handful
of expectation values; see `uniqc-algorithm-cases` for a worked example.

## Real-hardware caveats

- For `pauli_expectation` on a noisy backend, apply a readout error
  mitigator first (see `uniqc-xeb-qem`) — ~1% readout error per qubit
  swings expectations significantly.
- Pin shot count: `<P>_estimated` has standard error
  `~ sqrt((1 - <P>^2) / shots)` for a single Pauli observable. For 1%
  precision near `<P>=0`, you need ~10000 shots.
- For batched submissions, `pauli_expectation` accepts a backend string;
  uniqc submits, waits, and aggregates — so a single call may take a long
  time on the real cloud. Cache intermediate counts to disk.
