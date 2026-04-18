# Circuit Building Reference

Complete API reference for the QPanda-lite `Circuit` class and related types.

## Circuit Class

### Initialization

```python
from qpandalite.circuit_builder import Circuit

# Empty circuit (qubits auto-detected from gate usage)
c = Circuit()

# Fixed qubit count
c = Circuit(4)

# Named registers
c = Circuit(qregs={"data": 4, "ancilla": 2})
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `originir` | `str` | Circuit in OriginIR format |
| `qasm` | `str` | Circuit in OpenQASM 2.0 format |
| `circuit` | `str` | Alias for `originir` |
| `qubit_num` | `int` | Total number of qubits |
| `cbit_num` | `int` | Total number of classical bits |
| `depth` | `int` | Circuit depth (computed) |
| `max_qubit` | `int` | Highest qubit index used |
| `used_qubit_list` | `list[int]` | Qubits referenced in circuit |
| `measure_list` | `list[int]` | Qubits scheduled for measurement |
| `opcode_list` | `list[OpCode]` | Internal gate opcodes |
| `qregs` | `dict[str, QReg]` | Named quantum registers |

### Named Registers

```python
c = Circuit(qregs={"data": 4, "ancilla": 2})

# Access register
data_reg = c.get_qreg("data")
# data_reg.qubits -> [Qubit("data", 0, 0), Qubit("data", 1, 1), ...]

# Use register in gates
c.h(data_reg[0])    # Hadamard on data[0]
c.x(data_reg[1:3])  # X on data[1], data[2]
```

## Single-Qubit Gates (No Parameters)

| Method | Gate | Description |
|--------|------|-------------|
| `c.h(qn)` | Hadamard | Equal superposition |
| `c.x(qn)` | Pauli-X | Bit flip |
| `c.y(qn)` | Pauli-Y | Bit+phase flip |
| `c.z(qn)` | Pauli-Z | Phase flip |
| `c.s(qn)` | S gate | Phase π/2 |
| `c.sdg(qn)` | S-dagger | Phase -π/2 |
| `c.t(qn)` | T gate | Phase π/4 |
| `c.tdg(qn)` | T-dagger | Phase -π/4 |
| `c.sx(qn)` | √X | Square-root of X |
| `c.sxdg(qn)` | √X-dagger | Adjoint of √X |
| `c.identity(qn)` | I | Identity (no-op) |

All accept `QubitInput`: `int`, `Qubit`, or `QRegSlice`.

## Parametric Single-Qubit Gates

| Method | Parameters | Description |
|--------|-----------|-------------|
| `c.rx(qn, theta)` | `theta: float` | X-axis rotation |
| `c.ry(qn, theta)` | `theta: float` | Y-axis rotation |
| `c.rz(qn, theta)` | `theta: float` | Z-axis rotation |
| `c.rphi(qn, theta, phi)` | `theta, phi: float` | Arbitrary axis rotation |
| `c.u1(qn, lam)` | `lam: float` | U1 gate (phase) |
| `c.u2(qn, phi, lam)` | `phi, lam: float` | U2 gate |
| `c.u3(qn, theta, phi, lam)` | `theta, phi, lam: float` | U3 gate (general) |

## Two-Qubit Gates

| Method | Description |
|--------|-------------|
| `c.cnot(ctrl, tgt)` | CNOT (controlled-X) |
| `c.cx(ctrl, tgt)` | Alias for CNOT |
| `c.cz(q1, q2)` | Controlled-Z |
| `c.swap(q1, q2)` | SWAP |
| `c.iswap(q1, q2)` | iSWAP |
| `c.xx(q1, q2, theta)` | XX Ising interaction |
| `c.yy(q1, q2, theta)` | YY Ising interaction |
| `c.zz(q1, q2, theta)` | ZZ Ising interaction |
| `c.phase2q(q1, q2, t1, t2, tzz)` | Two-qubit phase |
| `c.uu15(q1, q2, params)` | General 2-qubit (15 params) |

## Three-Qubit Gates

| Method | Description |
|--------|-------------|
| `c.toffoli(q1, q2, q3)` | Toffoli (CCNOT) |
| `c.cswap(q1, q2, q3)` | Fredkin (controlled SWAP) |

## Measurement

```python
c.measure(0)           # Measure single qubit
c.measure(0, 1, 2)     # Measure multiple qubits
```

- Multiple calls accumulate measurements
- Classical bit indices assigned in order
- Cannot be called inside `control()` or `dagger()` contexts

## Context Managers

### Controlled Operations

```python
with c.control(0):       # Single control qubit
    c.x(1)               # -> CNOT(0, 1)
    c.z(2)               # -> CZ(0, 2)

with c.control(0, 1):   # Multiple control qubits
    c.x(2)               # -> Toffoli(0, 1, 2)
```

Low-level API:
```python
c.set_control(0)
c.x(1)
c.unset_control()
```

### Dagger (Adjoint) Operations

```python
with c.dagger():
    c.h(0)
    c.rx(1, 0.5)
```

Low-level API:
```python
c.set_dagger()
c.h(0)
c.unset_dagger()
```

## Remapping

Remap qubit indices for hardware topology compatibility:

```python
# Remap logical qubits to physical qubits
mapped = c.remapping({0: 3, 1: 5, 2: 1, 3: 4})
```

- Returns a new `Circuit` (original unchanged)
- All keys and values must be non-negative integers
- Each physical qubit can only be assigned once
- All used qubits must appear in the mapping

## Circuit Composition

```python
# Copy a circuit
c2 = c.copy()

# Add gates from another circuit
c.add_circuit(other_circuit)
```

## Barrier

```python
c.barrier(0, 1, 2)  # Insert barrier on specified qubits
```

## Qubit Types

### Qubit

```python
from qpandalite.circuit_builder import Qubit

q = Qubit(name="data", index=0, base_index=0)
# int(q) -> 0
```

### QReg

```python
from qpandalite.circuit_builder import QReg

qr = QReg(name="data", size=4, base_index=0)
# qr.qubits -> list of Qubit objects
# qr[0] -> Qubit("data", 0, 0)
# qr[1:3] -> QRegSlice
```

### Parameters

```python
from qpandalite.circuit_builder import Parameter, Parameters

# Named parameter
p = Parameter("theta")
p.bind(1.57)           # Bind a value
p.evaluate()           # Returns 1.57
p.is_bound             # True

# Parameter array
ps = Parameters("weights", size=8)
ps.bind([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
ps[0].evaluate()       # 0.1
len(ps)                # 8
```
