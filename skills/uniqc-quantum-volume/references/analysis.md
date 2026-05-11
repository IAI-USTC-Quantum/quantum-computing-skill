# Scoring and reporting QV results

The output of a QV run for a given width `n` is `K` numbers
`h_1, …, h_K ∈ [0, 1]`, one per random circuit. From those:

```
h̄  = (1/K) Σ h_k
σ² = (1/(K-1)) Σ (h_k - h̄)²
LCB_2σ = h̄ − 2 · σ / √K
pass = LCB_2σ > 2/3
```

## Reference implementation

```python
import numpy as np


def heavy_freq(counts: dict, heavy: set[int]) -> float:
    """Fraction of shots that landed in the heavy set."""
    total = sum(counts.values()) or 1
    hits = sum(c for bits, c in counts.items() if int(bits, 2) in heavy)
    return hits / total


def score(freqs: list[float]) -> dict:
    arr = np.asarray(freqs, dtype=float)
    K = arr.size
    mean  = float(arr.mean())
    sigma = float(arr.std(ddof=1)) if K > 1 else 0.0
    lcb_2sigma = mean - 2.0 * sigma / np.sqrt(K) if K > 1 else mean
    return {
        "K": K,
        "mean": mean,
        "sigma": sigma,
        "stderr": sigma / np.sqrt(K) if K > 1 else 0.0,
        "lcb_2sigma": lcb_2sigma,
        "pass": lcb_2sigma > 2 / 3,
    }
```

## Bootstrap confidence interval (more robust)

Sample variance assumes near-Gaussian per-circuit `h_k`, which fails
when `K` is small (~30) or the underlying distribution is heavy-tailed.
A non-parametric percentile bootstrap is more robust:

```python
def bootstrap_lcb(freqs: list[float], *, n_boot: int = 10_000,
                  ci_lower_pct: float = 2.5, seed: int = 0) -> float:
    rng = np.random.default_rng(seed)
    arr = np.asarray(freqs, dtype=float)
    K = arr.size
    means = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = rng.integers(0, K, size=K)
        means[i] = arr[idx].mean()
    return float(np.percentile(means, ci_lower_pct))
```

`ci_lower_pct=2.5` recovers the lower edge of a 95% bootstrap CI
(roughly aligned with 2σ for Gaussian data).

## Sweeping width

```python
def sweep(backend, *, max_n: int = 8, n_circuits: int = 100, shots: int = 1000):
    qv_n = 1                                  # QV = 2^qv_n; start at "passes nothing"
    summary = {}
    for n in range(2, max_n + 1):
        s = run_qv(backend=backend, n=n, n_circuits=n_circuits, shots=shots)
        summary[n] = s
        if s["pass"]:
            qv_n = n
        else:
            print(f"n={n}: FAIL (mean={s['mean']:.4f}, LCB={s['lcb_2sigma']:.4f})")
            break
        print(f"n={n}: PASS (mean={s['mean']:.4f}, LCB={s['lcb_2sigma']:.4f})")
    return {"QV": 2 ** qv_n, "qv_n": qv_n, "per_width": summary}
```

`run_qv` is the helper in the SKILL.md cheat sheet — build circuits,
submit batch, fetch counts, compute `freqs`, call `score()`.

## Plotting heavy-output decay vs width

```python
import matplotlib.pyplot as plt


def plot_sweep(summary: dict, save_to: str | None = None) -> None:
    widths = sorted(summary)
    means  = [summary[n]["mean"]     for n in widths]
    stderr = [summary[n]["stderr"]   for n in widths]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.errorbar(widths, means, yerr=[2 * e for e in stderr],
                fmt="o-", capsize=4, label="mean ± 2σ/√K")
    ax.axhline(2 / 3, color="r", linestyle="--", label="QV pass threshold (2/3)")
    ax.axhline((1 + np.log(2)) / 2, color="g", linestyle=":",
               label="ideal asymptote (0.847)")
    ax.set_xlabel("width n")
    ax.set_ylabel("heavy-output probability")
    ax.set_title("Quantum Volume sweep")
    ax.set_ylim(0.4, 1.0)
    ax.grid(alpha=0.3)
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    if save_to:
        fig.savefig(save_to, dpi=160, bbox_inches="tight")
    return fig
```

## Reading the per-circuit distribution

A histogram of `h_k` over the `K` circuits is more diagnostic than the
mean alone. A long left tail of low-`h_k` circuits suggests sporadic
calibration drops or specific qubit pairs that fail; a tight cluster
that just happens to sit below `2/3` suggests uniformly degraded
gate fidelity.

```python
plt.hist(freqs, bins=20, edgecolor="k")
plt.axvline(2 / 3, color="r", linestyle="--")
plt.xlabel("h_k (per-circuit heavy-output frequency)")
plt.ylabel("count")
plt.title(f"per-circuit distribution at n={n} (mean={np.mean(freqs):.3f})")
```

## Saving evidence

QV is reported in papers, vendor pages, and procurement specs — keep
the raw data:

```python
import json
from pathlib import Path

p = Path("qv-runs") / f"{backend.replace(':', '_')}-n{n}-{stamp}.json"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({
    "backend": backend,
    "n": n,
    "n_circuits": K,
    "shots": shots,
    "seeds": SEEDS,
    "freqs": freqs,
    "score": score(freqs),
}, indent=2))
```

## Conventional reporting form

> **`QV = 2^n_max = …`** on `<backend>` (`<backend_name>`),
> with `K = …` circuits and `S = …` shots per circuit at width
> `n_max`, achieving mean heavy-output `h̄ = …` and a one-sided 2σ
> lower confidence bound of `…` (above the `2/3` threshold).

Cite Cross et al. 2019 (arXiv:1811.12926) when the audience expects a
formal definition.

## Troubleshooting a borderline pass

| Symptom                                  | Investigation                                                                          |
| ---------------------------------------- | -------------------------------------------------------------------------------------- |
| Mean ≈ 0.6, stderr small                 | Coherent gate error or topology-driven SWAP overhead. Try `compile(level=3)`.          |
| Mean ≈ 0.7, stderr large                 | Specific seeds tank — bad qubit pair on this run. Run XEB on involved pairs.           |
| Mean drops sharply between n and n+1     | Crosstalk or uncompiled long-range gates. Inspect compiled depth, not logical depth.   |
| Mean ≈ 0.5                               | Effectively random output (depolarised). Suspect classical resets / readout misconfig. |
| `LCB > 2/3` only after readout EM        | Readout error dominating; report both numbers and prefer the mitigated one.            |
