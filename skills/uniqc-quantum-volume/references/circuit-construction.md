# Building QV circuits

uniqc 0.0.13 does not ship a QV circuit factory, so we use
qiskit's `quantum_volume(n, depth, seed=...)` and load the result into
uniqc. As of 0.0.13, qiskit is a **core dependency** (`pip install
unified-quantum` is sufficient — no `[qiskit]` extra), and uniqc accepts
qiskit `QuantumCircuit` objects directly anywhere `AnyQuantumCircuit`
is expected.

> Requires `pip install unified-quantum`.

## The minimum recipe

```python
from qiskit.circuit import ClassicalRegister
from qiskit.circuit.library import quantum_volume
from qiskit.qasm2 import dumps

from uniqc import Circuit


def build_qv(n: int, *, seed: int) -> Circuit:
    """Square QV: width n, depth n, with measurements on every qubit."""
    qc = quantum_volume(n, n, seed=seed)             # function form (qiskit ≥ 1.0)
    qc.add_register(ClassicalRegister(n, "c"))       # uniqc rejects QASM2 with no creg
    qc.measure(range(n), range(n))
    # quantum_volume produces an UnitaryGate per pair; decompose into u + cx so
    # uniqc's parser accepts the QASM and so the OriginIR timeline is honest.
    qasm = dumps(qc.decompose().decompose().decompose())
    return Circuit.from_qasm(qasm)
```

The triple-`decompose()` is needed because `quantum_volume` builds the
2-qubit blocks as `UnitaryGate` objects (not in any standard basis).
Without decomposition, `qiskit.qasm2.dumps` raises
`Qasm2ExporterError`. The triple expansion lands on `u(θ, φ, λ)` +
`cx`, both of which `Circuit.from_qasm` accepts.

## Common pitfalls when loading

1. **Empty classical register** — `Circuit.from_qasm` raises
   `RegisterDefinitionError: Register is empty` if the QASM has no
   `creg`. The `add_register(ClassicalRegister(n, "c"))` line above
   prevents this. (Even if you do not intend to measure, add a dummy
   `creg c[1];`.)
2. **Custom gates in QASM** — anything beyond the standard `qelib1.inc`
   set must be expanded first; `decompose()` does it. If you see
   `gate def` blocks in the dumped QASM, the parse will succeed but
   the resulting OriginIR may not transpile cleanly to your target
   backend's basis.
3. **Measurement order** — uniqc reports counts in **little-endian**
   (`q0` is the rightmost character of the bitstring). When matching
   a counts key back to an integer index for the heavy-set lookup,
   use `int(bits, 2)`; the bit ordering is consistent because qiskit's
   `measure(range(n), range(n))` and uniqc's binary key both put `q0`
   in the LSB.

## Ideal heavy-set computation

```python
import numpy as np
from uniqc.simulator import Simulator


def heavy_set(circuit: Circuit, *, n: int) -> tuple[set[int], float, np.ndarray]:
    """Indices with p_ideal(x) > median, the median, and the full prob vector."""
    sim = Simulator(backend_type="statevector")
    probs = np.asarray(sim.simulate_pmeasure(circuit.originir), dtype=float)
    if probs.size != 2 ** n:
        raise ValueError(f"expected 2^{n} probabilities, got {probs.size}")
    median = float(np.median(probs))
    heavy = {int(i) for i, p in enumerate(probs) if p > median}
    return heavy, median, probs
```

The Porter-Thomas asymptote says `Σ_{x ∈ heavy} p(x) → (1 + ln 2)/2 ≈
0.847` as `n → ∞`. Empirically for `n = 3`, single random seeds give
values in 0.65 – 0.95; this is the noiseless ceiling for that
particular circuit, so even ideal hardware will average around 0.85.

## Compiling for the target backend

```python
from uniqc import compile, find_backend

bi = find_backend("originq:WK_C180")
compiled = compile(circuit, bi, level=2,
                    basis_gates=["cz", "sx", "rz"])
```

`compile()` returns a uniqc `Circuit` rewritten in the chip basis.
Submit the compiled version; the heavy-set was computed from the
*logical* (uncompiled) circuit, which is correct because compilation
preserves the unitary up to a global phase.

## Submitting a sweep

```python
from uniqc import submit_batch, wait_for_result

uid = submit_batch(circuits, backend="originq:WK_C180", shots=1000)
results = wait_for_result(uid, timeout=900)         # list[UnifiedResult]
```

`submit_batch` returns one `uqt_*` even when the batch is auto-sharded
across multiple OriginQ task groups — see the `uniqc-cloud-submit`
skill's `task-ids-and-shards.md` reference.

## Reproducibility

Always pass an explicit `seed` to `quantum_volume(n, n, seed=s)`.
Save the list of seeds you used so you can re-run the *same* circuits
on a different backend later for an apples-to-apples comparison.

```python
SEEDS = list(range(100))      # or any sequence you can persist
circuits = [build_qv(n, seed=s) for s in SEEDS]
```

## Edge cases

- **n=1**: QV is undefined for 1 qubit (no SU(4) layer). Start at n=2.
- **odd n**: A layer has `floor(n/2)` SU(4) blocks; the leftover qubit
  is idle for that layer. Counts and heavy-set arithmetic still work.
- **n very small (2–3)**: the Porter-Thomas asymptote does not hold;
  expected ideal heavy-output is closer to 0.78 than 0.85. Pass/fail
  is still based on `2/3`, so this does not affect the test.
- **n very large**: ideal simulation becomes the bottleneck. See
  `protocol.md`'s closing note.
