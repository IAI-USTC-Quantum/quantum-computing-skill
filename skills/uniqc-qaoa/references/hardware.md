# QAOA on real hardware

Once the noiseless QAOA loop converges to the right answer, moving to
real hardware is mostly a matter of compile + submit + decode. Do not
run the optimiser inside-the-loop on real hardware unless you have
already verified shot-noise convergence on `dummy:originq:<chip>`.

## Recommended sequence

1. Tune `(γ*, β*)` end-to-end on `Simulator` (statevector,
   `shots=None`). Save the parameters.
2. Re-validate on `dummy:originq:<chip>` with realistic shot noise to
   estimate the convergence margin.
3. Submit the **final iterate** (or a small parameter neighborhood)
   to real hardware as a single batch.
4. Decode bitstrings; report top-K + cut value.

## Step 1 — converge offline

```python
from uniqc.algorithms.workflows.qaoa_workflow import run_qaoa_workflow

result = run_qaoa_workflow(cost_h, n_qubits=4, p=2, method="COBYLA")
gammas_star, betas_star = result.gammas, result.betas
```

## Step 2 — validate on chip-noise dummy

```python
from uniqc import qaoa_ansatz, submit_task, wait_for_result

circuit = qaoa_ansatz(cost_h, p=2, gammas=gammas_star, betas=betas_star)
for q in range(4):
    circuit.measure(q)

uid = submit_task(circuit, backend="dummy:originq:WK_C180", shots=4000)
result = wait_for_result(uid, timeout=60)
print(result.counts)
```

> ℹ️ The chip-backed compile pass uses qiskit, which is a **core dependency** in uniqc 0.0.13 (no `[qiskit]` extra needed).

## Step 3 — compile and submit to real hardware

```python
from uniqc import compile, find_backend, submit_batch, wait_for_result

bi = find_backend("originq:WK_C180")
circuits = []
for shift in [-0.05, 0.0, +0.05]:
    g = gammas_star + shift
    b = betas_star  + shift
    c = qaoa_ansatz(cost_h, p=2, gammas=g, betas=b)
    for q in range(4):
        c.measure(q)
    circuits.append(compile(c, bi, level=2))

uid = submit_batch(circuits, backend="originq:WK_C180", shots=2000)
results = wait_for_result(uid, timeout=900)
```

Submitting a small parameter neighborhood is cheap (one task id, one
queue wait) and gives you the local sensitivity for free.

## Step 4 — decode the bitstrings

```python
def cut_value(bits: str, edges) -> int:
    return sum(1 for i, j in edges if bits[-1 - i] != bits[-1 - j])

for shift, r in zip([-0.05, 0.0, +0.05], results):
    if r is None:
        print(shift, "FAILED"); continue
    ranked = sorted(r.counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
    for bits, n in ranked:
        print(f"  shift={shift:+.2f}  {bits}  count={n}  cut={cut_value(bits, edges)}")
```

## Mitigated hardware loop

For a 1-shot mitigation pass (see `uniqc-xeb-qem`):

```python
from uniqc.algorithms.workflows import readout_em_workflow
from uniqc.qem import M3Mitigator

cal = readout_em_workflow.run_readout_em_workflow(
    backend="originq:WK_C180", qubits=[0, 1, 2, 3], shots=1000)
mitigator = M3Mitigator(calibration_result=cal)
mitigated = [mitigator.apply(r) for r in results if r is not None]
```

Always print raw and mitigated counts side-by-side — readout mitigation
swings probabilities significantly on near-uniform distributions.

## Region selection on bigger chips

If you intend to embed your `n_qubits` problem on a 100+-qubit chip,
`RegionSelector` gives a topology-aware best-region pick:

```python
from uniqc.cli.chip_info import ChipCharacterization
from uniqc import RegionSelector, find_backend

bi = find_backend("originq:WK_C180")
chip = ChipCharacterization.from_backend_info(bi)
selector = RegionSelector(chip)

chain = selector.find_best_2D_from_circuit(circuit, min_qubits=4, max_search_seconds=10.0)
print("chosen physical qubits:", chain.qubits)
```

After remapping the circuit onto `chain.qubits`, compile and submit as
above. Record `chain.qubits` in your experiment log — different days
will produce different regions as the calibration drifts.

## Common mistakes

- Running the optimiser against real hardware on every step — wastes
  cloud quota; converge offline first.
- Not measuring before sampling — `pauli_expectation` adds basis rotations
  but for a custom decode you must `circuit.measure(q)` explicitly.
- Forgetting that `submit_batch` returns a single `uqt_*` for the whole
  parameter sweep; iterate over `results` (a list) after `wait_for_result`.
- Mixing `betas` and `gammas` order — uniqc convention in the workflow is
  `x = [γ_1..γ_p, β_1..β_p]` (gammas first, betas second).
