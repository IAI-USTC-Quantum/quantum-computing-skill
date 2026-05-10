# Plotting results

uniqc ships a thin matplotlib-based visualization layer. The two main
helpers for measurement results are:

```python
from uniqc.visualization import plot_histogram, plot_distribution
```

Both accept either a `dict[str, float]` (bitstring -> value) or a
`list[float]` (index -> value). Use the dict form unless you specifically
want a probability vector indexed by integer.

## Histogram of raw counts

```python
plot_histogram(
    result.counts,
    title=f"counts  task={result.task_id[:10]}…  platform={result.platform}",
    figsize=(10, 6),
)
```

This calls `matplotlib.pyplot` under the hood — so to save instead of
showing:

```python
import matplotlib.pyplot as plt
plot_histogram(result.counts, title="raw counts")
plt.savefig(f"results/{result.task_id}_counts.png", dpi=160, bbox_inches="tight")
plt.close()
```

## Distribution (probabilities)

```python
plot_distribution(
    result.probabilities,
    title=f"probabilities  shots={result.shots}",
)
```

The "distribution" plot is what you usually want for cross-run comparisons
because it normalizes for shot count differences.

## Top-K only

```python
top_k = dict(sorted(result.counts.items(), key=lambda kv: kv[1], reverse=True)[:16])
plot_histogram(top_k, title="top-16 bitstrings")
```

For wide circuits (≥ 8 qubits), plotting all 2^n bitstrings is unreadable.
Either pick top-K or compute marginals first.

## Side-by-side comparison of two runs

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

plt.sca(axes[0])
plot_histogram(result_a.counts, title=f"A: {result_a.platform}")

plt.sca(axes[1])
plot_histogram(result_b.counts, title=f"B: {result_b.platform}")

plt.tight_layout()
plt.savefig("compare.png", dpi=160)
plt.close()
```

`plot_histogram` writes into the current axes via `plt.gca()`, so
`plt.sca(...)` is the trick to force placement.

## Saving raw data alongside the figure

Always pair a PNG with the JSON it came from:

```python
import json
from pathlib import Path

base = Path(f"results/{result.task_id}")
base.parent.mkdir(parents=True, exist_ok=True)
plot_histogram(result.counts, title="counts")
plt.savefig(base.with_suffix(".png"), dpi=160, bbox_inches="tight")
plt.close()
base.with_suffix(".json").write_text(json.dumps({
    "task_id": result.task_id,
    "platform": result.platform,
    "backend_name": result.backend_name,
    "shots": result.shots,
    "counts": result.counts,
}, indent=2))
```

## Probability vectors over the full Hilbert space

When you have a `simulate_pmeasure(...)` output (a flat array of length
2^n_qubits), the list form of `plot_distribution` is more convenient:

```python
import numpy as np
from uniqc import Circuit
from uniqc.simulator import Simulator

c = Circuit(3); c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1); c.measure(2)
sim = Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(c.originir)        # length-8 list
plot_distribution(list(probs), title="ideal probabilities")
```

For very wide systems, threshold first:

```python
probs = np.asarray(probs)
mask = probs > 1e-3
shown = {format(i, f"0{c.n_qubits}b"): float(p) for i, p in enumerate(probs) if mask[i]}
plot_distribution(shown, title="probabilities (> 1e-3)")
```

## When matplotlib is not available

`plot_histogram` / `plot_distribution` both `import matplotlib.pyplot`
on entry — they raise `ImportError` if matplotlib is missing. For a
text-only environment, fall back to:

```python
from uniqc.visualization import format_result
print(format_result(result))
```

`format_result` returns a string suitable for stdout / log files.
