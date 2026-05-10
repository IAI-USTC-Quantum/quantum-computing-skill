# QFT and QPE

## QFT

```python
from uniqc import Circuit, qft_circuit

frag = qft_circuit(qubits=[0, 1, 2, 3], swaps=True)
```

`swaps=True` (the default) appends the bit-reversal swaps so the output
indices match standard QFT convention. Set `swaps=False` if you intend
to absorb the reversal into a downstream operation (e.g. QPE).

```python
prog = Circuit(4)
prog.add_circuit(frag)
for q in range(4):
    prog.measure(q)
```

To sanity-check on a known input (e.g. computational basis `|0…01⟩`):

```python
from uniqc import Circuit, qft_circuit
from uniqc.simulator import Simulator

p = Circuit(4)
p.x(0)                            # prepare |0001>
p.add_circuit(qft_circuit(qubits=[0, 1, 2, 3], swaps=True))
sim = Simulator(backend_type="statevector")
sv = sim.simulate_statevector(p.originir)
# All 16 amplitudes should have magnitude 1/4.
```

## QPE — Quantum Phase Estimation

QPE estimates the eigenphase `φ` of a unitary `U` on a known eigenstate
`|u⟩`, with `n_precision` ancilla qubits (precision = `1/2^n_precision`).

```python
import math
from uniqc import Circuit
from uniqc.algorithms.core.circuits import qpe_circuit

# 1. Build U with known eigenphase
phi = 0.375                          # = 0.011 in binary, exact at n_precision=3
U = Circuit(1)
U.rz(0, 2 * math.pi * phi)

# 2. State prep: |1> is the +φ eigenstate of R_Z(.)
prep = Circuit(1); prep.x(0)

# 3. Build QPE
n_precision = 4
prog = qpe_circuit(
    n_precision=n_precision,
    unitary_circuit=U,
    state_prep=prep,
    measure=True,                    # measures the precision register
)
```

Decoded integer `m` from measured cbits gives `φ ≈ m / 2^n_precision`.

```python
from uniqc.simulator import Simulator

sim = Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(prog.originir)
top_index = max(range(len(probs)), key=lambda i: probs[i])
phi_est = top_index / (2 ** n_precision)
print(f"estimated φ ≈ {phi_est}  vs  true {phi}")
```

## QPE arguments

```python
qpe_circuit(
    n_precision: int,
    unitary_circuit: Circuit,
    *,
    state_prep:        Circuit | None = None,
    controlled_power:  Callable[[Circuit, Circuit, int, int], None] | None = None,
    measure:           bool = True,
) -> Circuit
```

- `n_precision` — number of ancilla bits; precision `2^-n_precision`.
- `unitary_circuit` — `Circuit` implementing `U`. Width is your `n_system`.
- `state_prep` — prepares `|u⟩` on the system register. If omitted, system
  starts in `|0…0⟩`.
- `controlled_power(prog, U, system_offset, k)` — custom builder for
  controlled-`U^{2^k}` if you have a more efficient one than the naive
  `2^k`-times repetition.
- `measure=True` — appends measurements on the precision register.

The returned `Circuit` has `n_system + n_precision` qubits in total;
ancilla qubits are placed *after* the system qubits.

## Practical defaults

- Choose `n_precision` so that the expected error is small enough:
  `2^-n_precision` is the resolution. For `φ = 0.375`, `n_precision=3` is
  exact; `4` already adds 1 bit of slack.
- For non-eigenstates of `U`, the output distribution is a superposition
  of binary expansions of every eigenphase, weighted by overlap of
  `|u⟩` with each eigenvector.
- For research, call `qpe_circuit(..., measure=False)` and post-process
  the joint statevector — much easier to debug than peering at sampled
  bitstrings.

## Common mistakes

- Reading the bitstring with the wrong endianness. uniqc reports
  measurements in little-endian (precision bit `k=0` is the rightmost
  character of the result string).
- Building a controlled-`U^{2^k}` by literally calling `add_circuit(U)`
  `2^k` times for large `k` — exponential. Pass a `controlled_power`
  function that builds it analytically when `U` has special structure.
- Passing `unitary_circuit` with measurements still attached — strip
  them; QPE wants a coherent unitary.
