# Inspecting `UnifiedResult`

`UnifiedResult` is what `wait_for_result` returns for a single circuit. It
is a dataclass that **also** behaves like a `dict[str, int]` over
`self.counts`, so legacy code that did `result["00"]` keeps working.

## Quick anatomy

```python
result = wait_for_result(uid, timeout=300)

# dict-like
result["00"]          # int
list(result)          # list of bitstrings
sum(result.values())  # == result.shots
len(result)           # number of distinct bitstrings observed

# explicit attributes
result.counts          # dict[str, int]
result.probabilities   # dict[str, float]
result.shots           # int
result.platform        # str
result.task_id         # str (uqt_*)
result.backend_name    # str | None
result.execution_time  # float | None  (seconds, where reported)
result.raw_result      # platform-native payload
result.error_message   # str | None
```

## Pretty-print a counts table

```python
def print_counts(result, top: int | None = 10) -> None:
    items = sorted(result.counts.items(), key=lambda kv: kv[1], reverse=True)
    if top is not None:
        items = items[:top]
    width = max(len(k) for k, _ in items)
    print(f"task={result.task_id} shots={result.shots} platform={result.platform}")
    print(f"{'bitstring':<{width}}  count   probability")
    for k, n in items:
        print(f"{k:<{width}}  {n:>5}   {n / result.shots:.4f}")
```

`uniqc.visualization.format_result` does something similar with a more
elaborate template — handy when you want output that matches the CLI.

## Convert to a `pandas.DataFrame`

```python
import pandas as pd

df = (
    pd.DataFrame({"bitstring": list(result.counts), "count": list(result.counts.values())})
      .assign(probability=lambda d: d["count"] / result.shots)
      .sort_values("count", ascending=False)
)
print(df.head())
```

## Marginals (drop / sum out qubits)

```python
def marginal(counts: dict[str, int], keep_qubits: list[int]) -> dict[str, int]:
    """Return marginal distribution over the `keep_qubits` (qubit 0 = rightmost)."""
    out: dict[str, int] = {}
    for bits, n in counts.items():
        # bits is little-endian: bits[-1] is qubit 0
        kept = "".join(bits[-1 - q] for q in keep_qubits)
        out[kept] = out.get(kept, 0) + n
    return out

m = marginal(result.counts, [0, 2])           # qubits 0 and 2 only
```

## Endianness

uniqc reports counts in **little-endian** (qubit 0 is the rightmost
character). If you want big-endian to match a paper or another framework,
flip the keys:

```python
big = {k[::-1]: v for k, v in result.counts.items()}
```

## Working with batch results

```python
results = wait_for_result(uid, timeout=600)   # uid was from submit_batch
for i, r in enumerate(results):
    if r is None:
        print(i, "FAILED")
        continue
    print(i, max(r.counts, key=r.counts.get), r.shots)
```

## Recovering the underlying platform record

`result.raw_result` is the platform's exact payload. Use it for debug or
when you need a platform-specific field that uniqc does not normalize:

```python
import json
print(json.dumps(result.raw_result, indent=2))
```

If the field you need shows up only after a platform-specific conversion,
import a `normalize_*` helper:

```python
from uniqc.backend_adapter.adapters.originq import normalize_originq_result
norm = normalize_originq_result(result.raw_result)   # same path wait_for_result took
```

## When `result is None`

`wait_for_result` returns `None` for a hard failure. Always:

```python
if result is None:
    info = query_task(uid)
    raise RuntimeError(f"task {uid} failed: status={info.status} error={getattr(info, 'error', None)}")
```

For batches, the iteration handles per-element `None` similarly.
