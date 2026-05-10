# Deutsch-Jozsa

Decides whether a Boolean oracle `f: {0,1}^n -> {0,1}` is constant or
balanced in a single quantum query.

```python
from uniqc import Circuit, deutsch_jozsa_circuit
```

## With a built-in test oracle

Without an explicit `oracle`, uniqc uses a default constant or balanced
oracle for demonstration:

```python
prog = deutsch_jozsa_circuit(qubits=[0, 1, 2])     # 3-qubit input, 1 ancilla added
```

Sample: if all measured input qubits are `0`, `f` is **constant**;
otherwise it is **balanced**.

## With a custom oracle

```python
from uniqc import Circuit, deutsch_jozsa_circuit

n = 3
oracle = Circuit(n + 1)                            # last qubit is the ancilla
# Example: balanced oracle that XORs all input bits into the ancilla
for i in range(n):
    oracle.cnot(i, n)

prog = deutsch_jozsa_circuit(
    qubits=list(range(n)),
    ancilla=n,
    oracle=oracle,
)
```

## Decoding the result

```python
from uniqc.simulator import Simulator
sim = Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(prog.originir)

n_input = 3
input_zero_prob = sum(
    float(p) for i, p in enumerate(probs)
    if (i & ((1 << n_input) - 1)) == 0          # input register all zero
)
print("P(input = 00...0) =", input_zero_prob)
print("oracle is", "constant" if input_zero_prob > 0.99 else "balanced")
```

## Practical defaults

- DJ is a textbook algorithm; on a noisy chip the contrast (`0` vs `1`)
  degrades quickly with `n`. Use `n ≤ 4` on real hardware.
- Always specify the `ancilla` index explicitly if you embed in a wider
  circuit; the default uses the qubit immediately after `qubits[-1]`.

## Bernstein-Vazirani as a variant

DJ with a balanced oracle that XORs a hidden mask `s` into the ancilla
recovers `s` in the measured input bits — that is BV. Build the same
way with a different oracle:

```python
n = 3
hidden = 0b101
oracle = Circuit(n + 1)
for i in range(n):
    if (hidden >> i) & 1:
        oracle.cnot(i, n)

prog = deutsch_jozsa_circuit(qubits=list(range(n)), ancilla=n, oracle=oracle)
# Most likely measured bitstring on input qubits = hidden (little-endian).
```
