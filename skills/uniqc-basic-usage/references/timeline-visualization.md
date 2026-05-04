# Timeline Visualization Reference

UnifiedQuantum v0.0.9 provides circuit scheduling and HTML/SVG rendering for analyzing gate parallelism, timing, and resource usage. The visualization module is an optional dependency.

## Quick Path

```python
from uniqc import circuit_to_html, plot_time_line_html, schedule_circuit

# Static circuit diagram (no timing required)
html = circuit_to_html(circuit, output_path="circuit.html")

# Scheduled timeline with gate durations
html = plot_time_line_html(circuit, gate_durations={"cz": 30, "sx": 20, "rz": 0}, output_path="timeline.html")

# Programmatic access to the schedule
schedule = schedule_circuit(circuit, gate_durations={"cz": 30, "sx": 20, "rz": 0})
```

---

## schedule_circuit

Left-compacts gates onto qubit resources and returns a `TimelineSchedule` object.

```python
def schedule_circuit(
    compiled_prog,                        # Circuit, OriginIR text, JSON pulse data, or gate dict list
    *,
    backend_info=None,                    # BackendInfo for gate duration lookup
    chip_characterization=None,           # ChipCharacterization for duration lookup
    gate_durations=None,                  # Explicit overrides: {"cz": 30, "sx": 20, "rz": 0}
    compile_to_basis=True,                # Compile logical circuits before scheduling
    basis_gates=None,                     # Basis gate override for compile()
    unit="ns",                            # Display unit label
) -> TimelineSchedule
```

Gate duration resolution order:
1. Explicit `gate_durations` dict (case-insensitive keys)
2. `backend_info.extra["gate_durations"]`
3. `chip_characterization` metadata (single_qubit_gate_time, two_qubit_gate_time)
4. Generic keys `"1q"`, `"2q"`, `"measure"` in overrides

Raises `TimelineDurationError` if a non-virtual gate cannot be assigned a duration.

### Integration with compile()

Pass a compiled circuit directly — compiled circuits have concrete gate sequences that scheduling needs:

```python
from uniqc import compile, TranspilerConfig, schedule_circuit

result = compile(circuit, backend_info, config=TranspilerConfig(level=2))
schedule = schedule_circuit(result.output, backend_info=backend_info)
```

---

## TimelineSchedule and TimelineGate

```python
@dataclass(frozen=True, slots=True)
class TimelineSchedule:
    gates: list[TimelineGate]
    total_duration: float
    n_layers: int
    unit: str

    @property
    def time_points(self) -> tuple[int | float, ...]: ...

    @property
    def resources(self) -> tuple[int, ...]: ...

@dataclass(frozen=True, slots=True)
class TimelineGate:
    index: int                    # gate index in the circuit
    name: str                     # gate name (e.g. "cz", "sx", "rz", "measure")
    qubits: tuple[int, ...]      # qubit indices
    params: tuple[float, ...]    # gate parameters
    start: float                 # start time (in unit)
    duration: float              # gate duration (in unit)
    end: float                   # end time = start + duration
    layer: int                   # parallel execution layer index

    @property
    def resources(self) -> tuple[int, ...]: ...

    @property
    def is_barrier(self) -> bool: ...

    def tooltip(self, *, unit: str = "ns") -> str: ...
```

---

## HTML Rendering

### circuit_to_html — Static Diagram

Renders a circuit diagram as HTML/SVG without timing information. No gate durations required.

```python
from uniqc import circuit_to_html

html = circuit_to_html(circuit, output_path="circuit.html", title="My Circuit")
```

### plot_time_line_html — Scheduled Timeline

Renders a scheduled timeline as HTML/SVG with gate tooltips showing qubits, parameters, start time, duration, and end time.

```python
from uniqc import plot_time_line_html

html = plot_time_line_html(
    circuit,
    output_path="timeline.html",
    gate_durations={"cz": 30, "sx": 20, "rz": 0, "measure": 500},
    title="My Circuit Timeline",
    unit="ns",
)
```

### plot_time_line — Table-style PDF (requires matplotlib)

Generates table-style PDF timeline plots. Requires `matplotlib`.

```python
from uniqc import plot_time_line

plot_time_line(
    circuit,
    figure_save_path="timeline_plots/",
    gate_durations={"cz": 30, "sx": 20, "rz": 0},
)
```

---

## Gate Duration Data

Gate durations can come from multiple sources:

| Source | When to use |
|--------|-------------|
| `gate_durations` dict | Quick override, known values |
| `BackendInfo.extra["gate_durations"]` | Backend metadata from `uniqc backend show` |
| `ChipCharacterization` | Real hardware calibration data |
| Generic keys `"1q"`, `"2q"` | Fallback when specific gate names are unknown |

Example with backend metadata:

```python
from uniqc import BackendInfo, schedule_circuit

backend = BackendInfo.get("origin:wuyuan:WK_C180")
schedule = schedule_circuit(circuit, backend_info=backend)
```

---

## Notes

- The visualization module is an optional dependency. Install with `unified-quantum[visualization]` for `matplotlib` and `pandas` support; the core `circuit_to_html` and `plot_time_line_html` work without them.
- `circuit_to_html` does not require gate durations (it uses logical layer grouping, not physical timing).
- `plot_time_line_html` and `schedule_circuit` require gate durations for circuits without explicit pulse timing data.
