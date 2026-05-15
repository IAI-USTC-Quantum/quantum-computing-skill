---
name: uniqc-circuit-interop
description: "Use when the user wants to convert quantum circuits across UnifiedQuantum's supported in-process types (uniqc 0.0.13): Circuit ↔ OriginIR string ↔ OpenQASM 2.0 string ↔ qiskit `QuantumCircuit` ↔ pyqpanda3 circuit. Covers `AnyQuantumCircuit` as the universal input type for compile/simulate/submit, `normalize_to_circuit()` / `NormalizedCircuit`, `Circuit.to_qiskit_circuit()` / `Circuit.to_pyqpanda3_circuit()`, `Circuit.from_qasm()` / `OriginIR_BaseParser` / `OpenQASM2_BaseParser`, round-trip pitfalls, and which platform expects which IR (OriginQ wants OriginIR; Quafu/IBM want OpenQASM 2.0; uniqc auto-converts at submit)."
---

# Uniqc Circuit Interop Skill

uniqc 0.0.13 unified the public-API circuit input type as
**`AnyQuantumCircuit`**: every compile / simulate / submit entry
point accepts any of:

- `uniqc.Circuit` (uniqc-native object)
- OriginIR `str`
- OpenQASM 2.0 `str`
- `qiskit.QuantumCircuit`
- pyqpanda3 circuit

…and normalizes internally via `normalize_to_circuit()`. This skill
helps users:

1. Pick the right type for their context (algorithm authoring, file
   storage, qiskit interop, OriginQ submission).
2. Round-trip safely without losing measurements / register names.
3. Avoid the small set of edge cases that don't round-trip cleanly.

## Decision tree

| User goal                                                       | Read first                                                  |
| --------------------------------------------------------------- | ----------------------------------------------------------- |
| "Build a circuit in uniqc, save as OriginIR / QASM2"            | [references/authoring-and-export.md](references/authoring-and-export.md) |
| "Convert qiskit `QuantumCircuit` ↔ uniqc `Circuit`"             | [references/qiskit-interop.md](references/qiskit-interop.md) |
| "Convert pyqpanda3 ↔ uniqc"                                     | [references/pyqpanda3-interop.md](references/pyqpanda3-interop.md) |
| "Parse an OriginIR / QASM2 file into a `Circuit`"               | [references/parsing.md](references/parsing.md)              |
| "What does each platform's submit pipeline want?"               | [references/per-platform-ir.md](references/per-platform-ir.md) |

## Mental model

```
                                ┌──────────────────────────────┐
   uniqc.Circuit ───────────────┤                              │
   OriginIR str  ───────────────┤  normalize_to_circuit(...)   ├──► uniqc.Circuit
   OpenQASM2 str ───────────────┤  → NormalizedCircuit          │
   qiskit.QuantumCircuit ───────┤    .circuit  (Circuit)        │
   pyqpanda3 circuit ───────────┤    .type     ('originir',     │
                                │              'qasm', 'qiskit',│
                                │              'pyqpanda3',     │
                                │              'circuit')       │
                                │    .original_input            │
                                └──────────────────────────────┘

   Circuit.originir              ──► OriginIR str (canonical)
   Circuit.qasm                  ──► OpenQASM 2.0 str
   Circuit.to_qiskit_circuit()   ──► qiskit.QuantumCircuit
   Circuit.to_pyqpanda3_circuit()──► pyqpanda3 circuit
   Circuit.from_qasm(qasm_str)   ──► Circuit  (parses OpenQASM 2.0)
```

## Cheat sheet

```python
from uniqc import (
    Circuit, AnyQuantumCircuit, normalize_to_circuit,
)
from uniqc.compile.originir import OriginIR_BaseParser
from uniqc.compile.qasm import OpenQASM2_BaseParser

# Build
c = Circuit(2)
c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)

# Export
ir   = c.originir            # str (OriginIR)
qasm = c.qasm                # str (OpenQASM 2.0)
qc   = c.to_qiskit_circuit() # qiskit.QuantumCircuit (qiskit is core in 0.0.13)
qpc  = c.to_pyqpanda3_circuit()    # needs `pip install unified-quantum[originq]`

# Parse the other way
back_ir   = OriginIR_BaseParser(); back_ir.parse(ir);   c1 = back_ir.to_circuit()
back_qasm = OpenQASM2_BaseParser(); back_qasm.parse(qasm); c2 = back_qasm.to_circuit()
c3 = Circuit.from_qasm(qasm)              # convenience wrapper

# Universal normalize (any input → Circuit + a tag)
nc = normalize_to_circuit(qc)             # qc is qiskit.QuantumCircuit
print(nc.type, type(nc.circuit))          # 'qiskit', uniqc.Circuit
```

## Practical defaults

- **Source of truth in your project: uniqc `Circuit`.** Build
  there; export to whichever IR you need at the boundary. This avoids
  parsing-format quirks from accumulating.
- **For storage on disk: OriginIR.** It round-trips cleanly through
  uniqc, is human-readable, and is the OriginQ canonical IR.
- **For qiskit cross-pollination**: prefer
  `Circuit.to_qiskit_circuit()` over hand-written QASM2 export — it
  preserves register names and gate parameters more faithfully.
- **For pyqpanda3**: `Circuit.to_pyqpanda3_circuit()` is available
  but requires `unified-quantum[originq]` (pyqpanda3 is the OriginQ
  SDK). If pyqpanda3 isn't installed, the method raises `ImportError`
  with the install hint.
- **At submit / simulate boundary**: don't pre-convert. uniqc 0.0.13
  accepts any `AnyQuantumCircuit` directly into `submit_task` /
  `Simulator(...).simulate_*` / `compile()`. Pre-converting is just
  extra work and an extra failure mode.
- **`NormalizedCircuit.type`** values are: `"circuit"`, `"originir"`,
  `"qasm"`, `"qiskit"`, `"pyqpanda3"`. The 0.0.12 attribute name
  `original_format` was renamed to `type` in 0.0.13 — old code that
  read `.original_format` must update.
- **Per-platform IR at submit**: OriginQ wants OriginIR; Quafu and
  IBM want OpenQASM 2.0; Quark wants OpenQASM 2.0. uniqc auto-converts
  at submit, but pre-validate with `dry_run_task(...)`.

## Round-trip pitfalls

| From → To              | Watch out for                                              |
| ---------------------- | ---------------------------------------------------------- |
| Circuit → QASM2        | Multi-qubit `measure(q1, q2)` becomes per-qubit `measure` lines (uniqc convention). |
| QASM2 → Circuit        | `Circuit.from_qasm` rejects QASM with no `creg` (`RegisterDefinitionError`). Always declare measurements. |
| Circuit → qiskit       | `Parameter` symbolic params are preserved as qiskit `Parameter`. Numerical params round-trip cleanly. |
| qiskit → Circuit       | `UnitaryGate` (used by `qiskit.circuit.library.quantum_volume`) does **not** round-trip via QASM2. `Circuit.to_qiskit_circuit()` round-trips the other way; for QV-style use, decompose the qiskit circuit first (`qc.decompose().decompose().decompose()` typically lands on `u + cx`). |
| OriginIR → QASM2       | OriginIR-specific gates (`RPhi`, `Phase2Q`, `XX(θ)`, `YY(θ)`, `ZZ(θ)`, `XY(θ)`) round-trip via auto-generated `gate def` blocks (uniqc 0.0.11.dev30+). |
| pyqpanda3 → Circuit    | Goes through OriginIR internally; supported gates match the OriginIR table. Custom pyqpanda3 macros that don't have an OriginIR mapping will raise. |

## Names to remember

- Top-level (uniqc): `Circuit`, `AnyQuantumCircuit`,
  `normalize_to_circuit`.
- Class on `Circuit`: `.originir`, `.qasm`, `.to_qiskit_circuit()`,
  `.to_pyqpanda3_circuit()`, `Circuit.from_qasm(qasm)`.
- Parsers: `uniqc.compile.originir.OriginIR_BaseParser`,
  `uniqc.compile.qasm.OpenQASM2_BaseParser`.
- Normalize result: `uniqc.circuit_builder.normalize.NormalizedCircuit`
  with fields `.circuit`, `.type`, `.original_input`.
- Submit / compile / simulate accept `AnyQuantumCircuit` inputs
  directly — pre-converting is unnecessary in 0.0.13.

## Response style

- Lead with the **shortest path**: if the user has a `Circuit` and
  wants to give it to a `submit_task`, just pass the `Circuit` —
  don't write a 10-line conversion utility.
- For "I have a qiskit circuit, give me an OriginIR file" requests,
  show the **single-call** path (`normalize_to_circuit(qc).circuit.originir`)
  before mentioning parsers / converters.
- For UnitaryGate / SX-token / cross-format edge cases, acknowledge
  the failure mode explicitly and provide the decomposition workaround.
