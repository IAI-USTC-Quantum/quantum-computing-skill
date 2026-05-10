# Rendering circuits and timelines

uniqc ships a few helpers for visualizing the program itself, which is
useful when you want to put the result next to the circuit that produced it.

## ASCII / matplotlib drawing

```python
from uniqc.visualization import draw, draw_html
draw(circuit)                       # matplotlib figure (interactive)
print(circuit.draw())               # ASCII-art string (also: circuit.draw())
```

`draw_html(circuit, output_path="circuit.html")` writes a self-contained
HTML page — handy when you want to share with someone who does not have
uniqc installed.

## Self-contained HTML

```python
from uniqc.visualization import circuit_to_html
circuit_to_html(circuit, output_path="circuit.html",
                title="QAOA p=2 ansatz on 4 qubits")
```

Open `circuit.html` in any browser. Nothing on the page links back to a
local Python kernel.

## Timelines (scheduled circuit)

A "timeline" is the compiled circuit with explicit per-gate durations,
useful for understanding what actually runs on hardware.

```python
from uniqc import compile, find_backend
from uniqc.visualization import schedule_circuit, plot_time_line_html

bi      = find_backend("originq:WK_C180")
compiled = compile(my_circuit, bi, level=2)
schedule = schedule_circuit(compiled, backend_info=bi)   # TimelineSchedule
print(schedule.total_duration, schedule.unit)
print(schedule.gate_durations)

plot_time_line_html(compiled, output_path="timeline.html",
                    backend_info=bi, title="QAOA-p2 timeline")
```

`TimelineSchedule` exposes `gates`, `qubits`, `total_duration`, `unit`,
`gate_durations`, plus a `time_points` property. (No `n_layers` /
`resources` — read `max(g.layer for g in gates) + 1` if you need layer
count.)

> ⚠️ `schedule_circuit` and `plot_time_line_html` need
> `unified-quantum[qiskit]` whenever the input is a logical (un-scheduled)
> `Circuit` — the scheduling pass goes through qiskit. Already-compiled,
> backend-aware programs work without it.

## Result + circuit on one HTML page

A common workflow is to ship "circuit.html + counts.png + counts.json" as
a per-task evidence bundle:

```python
from pathlib import Path
import json
import matplotlib.pyplot as plt

from uniqc.visualization import circuit_to_html, plot_histogram

base = Path(f"reports/{result.task_id}")
base.mkdir(parents=True, exist_ok=True)

circuit_to_html(circuit, output_path=base / "circuit.html",
                title=f"task {result.task_id[:10]}…")
plot_histogram(result.counts, title="counts")
plt.savefig(base / "counts.png", dpi=160, bbox_inches="tight")
plt.close()

(base / "counts.json").write_text(json.dumps({
    "shots": result.shots,
    "platform": result.platform,
    "backend_name": result.backend_name,
    "counts": result.counts,
}, indent=2))
```

## When the user just wants to see the diagram

If they are in Jupyter:

```python
draw(circuit)
```

If they are in a terminal:

```python
print(circuit.draw())
```

If you are running headless / inside CI:

```python
draw_html(circuit, output_path="circuit.html")
print("Open circuit.html in a browser.")
```
