# Comparing runs

A common ask: "I ran this on the simulator, then on real hardware — how
different are they?" Or: "I ran the same circuit twice, did anything
shift?" Two complementary tools.

## Total variation distance

```python
def total_variation(p: dict[str, float], q: dict[str, float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)

tv = total_variation(result_sim.probabilities, result_hw.probabilities)
print(f"TV(sim, hw) = {tv:.4f}")
```

`tv == 0` means identical, `tv == 1` means disjoint. For NISQ-era
hardware running a small circuit, TV in the 0.05–0.20 range is typical.

## Hellinger fidelity

```python
import math

def hellinger_fidelity(p: dict[str, float], q: dict[str, float]) -> float:
    keys = set(p) | set(q)
    bc = sum(math.sqrt(p.get(k, 0.0) * q.get(k, 0.0)) for k in keys)
    return bc ** 2

print(hellinger_fidelity(result_sim.probabilities, result_hw.probabilities))
```

Hellinger fidelity is closer to "how much the distributions overlap" and
is what most NISQ benchmarking papers report.

## Per-bitstring delta table

```python
def delta_table(p: dict[str, float], q: dict[str, float], top: int = 16):
    keys = sorted(set(p) | set(q), key=lambda k: max(p.get(k, 0.0), q.get(k, 0.0)), reverse=True)
    width = max(len(k) for k in keys)
    print(f"{'bitstring':<{width}}  {'p_sim':>8}  {'p_hw':>8}  {'Δ':>8}")
    for k in keys[:top]:
        a, b = p.get(k, 0.0), q.get(k, 0.0)
        print(f"{k:<{width}}  {a:>8.4f}  {b:>8.4f}  {b - a:>+8.4f}")

delta_table(result_sim.probabilities, result_hw.probabilities)
```

## Plot two distributions overlaid

```python
import matplotlib.pyplot as plt
import numpy as np

keys = sorted(set(result_sim.probabilities) | set(result_hw.probabilities))
sim_y = [result_sim.probabilities.get(k, 0.0) for k in keys]
hw_y  = [result_hw.probabilities.get(k, 0.0) for k in keys]
x = np.arange(len(keys))

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(x - 0.18, sim_y, width=0.36, label=f"sim ({result_sim.platform})")
ax.bar(x + 0.18, hw_y,  width=0.36, label=f"hw  ({result_hw.platform})")
ax.set_xticks(x)
ax.set_xticklabels(keys, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("probability")
ax.legend()
fig.tight_layout()
fig.savefig("compare.png", dpi=160)
plt.close(fig)
```

## Cross-batch comparison

When you run the same parameter sweep on two backends as separate batches:

```python
from uniqc import wait_for_result

results_sim = wait_for_result(uid_sim, timeout=600)   # list[UnifiedResult]
results_hw  = wait_for_result(uid_hw,  timeout=900)

for i, (rs, rh) in enumerate(zip(results_sim, results_hw)):
    if rs is None or rh is None:
        print(i, "FAILED")
        continue
    tv = total_variation(rs.probabilities, rh.probabilities)
    print(f"point {i}: TV = {tv:.4f}")
```

## Mitigated vs raw

```python
from uniqc.qem import ReadoutEM

em = ReadoutEM(adapter, max_age_hours=24.0, shots=1000)
mitigated = em.apply(result_hw)

print("raw      :", dict(sorted(result_hw.counts.items())))
print("mitigated:", dict(sorted(mitigated.counts.items())))
```

`em.apply(result)` returns a new `UnifiedResult` with mitigated counts/
probabilities, so all the comparison helpers above work unchanged.
