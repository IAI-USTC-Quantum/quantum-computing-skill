# Grover and amplitude estimation

## Grover

Amplifies the amplitude of a marked bitstring in the uniform
superposition. uniqc exposes the two building blocks:

```python
from uniqc import Circuit, grover_oracle, grover_diffusion
```

### Marked-bitstring oracle (built-in)

```python
import math
n = 3
marked = 5                             # binary: 101

oracle = grover_oracle(marked_state=marked, n_qubits=n)
diff   = grover_diffusion(n_qubits=n)

prog = Circuit(n)
for q in range(n):
    prog.h(q)
iters = round(math.pi / 4 * math.sqrt(2 ** n))
for _ in range(iters):
    prog.add_circuit(oracle)
    prog.add_circuit(diff)
for q in range(n):
    prog.measure(q)
```

After `iters` rounds the marked bitstring dominates the distribution.
Sample to confirm:

```python
from uniqc.simulator import Simulator
sim = Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(prog.originir)
print({format(i, f"0{n}b"): float(p) for i, p in enumerate(probs) if p > 1e-3})
```

### Custom oracle (your own predicate)

If you need to mark a *set* of states or use an arithmetic predicate:

```python
oracle = Circuit(n + 1)                  # n + 1 ancilla
# ... apply your predicate on qubits 0..n-1, with the result in qubit n.
# Typical pattern: phase-kickback via H + X on the ancilla, then your
# arithmetic, then uncompute.
prog = Circuit(n + 1)
prog.x(n); prog.h(n)                     # |-> on ancilla
for q in range(n):
    prog.h(q)
iters = round(math.pi / 4 * math.sqrt(2 ** n))
for _ in range(iters):
    prog.add_circuit(oracle)
    prog.add_circuit(grover_diffusion(n_qubits=n))
for q in range(n):
    prog.measure(q)
```

`grover_oracle` and `grover_diffusion` accept `qubits=...` and
`ancilla=...` for explicit qubit assignment when embedding into a
larger circuit.

### Iteration count

For `K` marked items in `N = 2^n`, the optimal iteration count is
`round(π/4 * sqrt(N/K))`. Over- or under-rotation degrades amplitude;
err on the side of slightly fewer iterations.

## Amplitude estimation

`amplitude_estimation_circuit` builds a QPE-on-Grover circuit that
estimates the marked-state probability `a` to precision
`O(1/2^eval_qubits)`.

```python
from uniqc import Circuit, amplitude_estimation_circuit, grover_oracle

n = 3
marked = 5
oracle = grover_oracle(marked_state=marked, n_qubits=n)

prog = amplitude_estimation_circuit(
    oracle=oracle,
    qubits=list(range(n)),
    eval_qubits=[n + i for i in range(4)],     # 4 precision bits
    state_prep=None,                          # default: H on each system qubit
)
```

The decoded integer `m` from the precision register gives
`a ≈ sin²(π * m / 2^len(eval_qubits))`.

```python
import math
from uniqc.simulator import Simulator
sim = Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(prog.originir)

n_eval = 4
top_index = max(range(len(probs)), key=lambda i: probs[i])
m = top_index >> n                       # extract the precision bits
a_hat = math.sin(math.pi * m / (2 ** n_eval)) ** 2
print(f"estimated marked probability a ≈ {a_hat}")
```

## Practical defaults

- Use Grover for "I know the marked predicate, I want a hit". Use AE for
  "how many hits are there?" / "what's the success probability?".
- AE precision doubles per `eval_qubit`; 4 bits is a reasonable default
  for toy demos. Real applications often need 6–8.
- For both, validate on `dummy:local:simulator` before submitting to
  hardware — Grover iteration counts are very sensitive to gate noise.

## Common mistakes

- Passing `n_qubits` as a positional argument to `grover_oracle` /
  `grover_diffusion` — the signature uses `*args` then keyword-only
  arguments; pass `n_qubits=n` explicitly.
- Forgetting to apply `H` to every system qubit before iterating —
  Grover starts from the uniform superposition, not from `|0…0⟩`.
- Mis-indexing `eval_qubits`. They must not overlap with `qubits`; the
  helper returns a `Circuit` wide enough to hold the union.
