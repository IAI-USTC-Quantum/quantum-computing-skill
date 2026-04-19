# Cloud Platforms Reference

Complete reference for submitting quantum circuits to cloud platforms via UnifiedQuantum.

## Configuration

### Environment Variables

| Variable | Scope | Description |
|----------|-------|-------------|
| `UNIQC_PROFILE` | All | Override active config profile for a single invocation |
| `UNIQC_DUMMY` | Dummy | Set to `true`/`1`/`yes` to force local dummy simulation |

All platform credentials (OriginQ, Quafu, IBM) are resolved through the config file rather than environment variables.

### Config File

Location: `~/.uniqc/uniqc.yml`

```yaml
default:
  originq:
    token: your-originq-token
    available_qubits: []
    available_topology: []
    task_group_size: 200
  quafu:
    token: your-quafu-token
  ibm:
    token: your-ibm-token
    proxy:
      http: ""
      https: ""
```

Initialize with `uniqc config init`.

### CLI Configuration

```bash
# Initialize
uniqc config init

# Set tokens
uniqc config set originq.token YOUR_TOKEN
uniqc config set quafu.token YOUR_TOKEN
uniqc config set ibm.token YOUR_TOKEN

# Validate
uniqc config validate

# View configuration
uniqc config list
```

### Profile Management

Multiple profiles for different environments:

```bash
uniqc config profile create dev
uniqc config profile use dev
uniqc config profile list
```

Set `UNIQC_PROFILE=<name>` to override the active profile for a single command.

## Platform Adapters

### OriginQ (Origin Quantum Cloud)

```python
from uniqc.task.adapters import OriginQAdapter

adapter = OriginQAdapter()
# Circuit translation and submission handled internally
```

**Features:**
- OriginIR native support
- Multiple chip backends
- Batch submission support

**Available Chips:** Varies by account. Contact OriginQ for chip availability.

### Quafu (BAQIS)

```python
from uniqc.task.adapters import QuafuAdapter

adapter = QuafuAdapter()
```

**Features:**
- Superconducting quantum processors
- Chip selection via `chip_id`

**Available Chips:**
| Chip ID | Qubits | Description |
|---------|--------|-------------|
| `ScQ-P10` | 10 | 10-qubit processor |
| `ScQ-P18` | 18 | 18-qubit processor |
| `ScQ-P136` | 136 | 136-qubit processor |

### IBM Quantum

```python
from uniqc.task.adapters import QiskitAdapter

adapter = QiskitAdapter()
```

**Features:**
- Qiskit-based circuit translation
- Access to IBM quantum fleet
- Automatic transpilation to target chip topology

### Dummy (Local Testing)

```python
from uniqc.task.adapters import DummyAdapter

adapter = DummyAdapter()
```

**Features:**
- No credentials required
- Local statevector simulation
- Identical API to real adapters
- Useful for development and debugging

## Task Submission API

### submit_task

```python
from uniqc import submit_task

task_id = submit_task(
    circuit,           # Circuit object or OriginIR string
    backend='originq', # Platform name
    shots=1000,        # Number of shots
    metadata=None,     # Optional dict for task metadata
    dummy=None,        # Override dummy mode (True/False/None)
    **kwargs           # Platform-specific options
)
# Returns: str (task ID)
```

### submit_batch

```python
from uniqc import submit_batch

task_ids = submit_batch(
    circuits,          # List of Circuit objects or OriginIR strings
    backend='originq',
    shots=1000,
    dummy=None,
    **kwargs
)
# Returns: list[str] (task IDs)
```

### query_task

```python
from uniqc import query_task

info = query_task(
    task_id='abc-123',
    backend='originq'
)
# Returns: TaskInfo
```

### wait_for_result

```python
from uniqc import wait_for_result

result = wait_for_result(
    task_id='abc-123',
    backend='originq',
    timeout=300.0,        # Max wait time in seconds
    poll_interval=5.0,    # Time between status checks
    raise_on_failure=True # Raise exception on task failure
)
# Returns: dict | None (measurement results)
```

## TaskInfo Data Class

```python
@dataclass
class TaskInfo:
    task_id: str
    backend: str
    status: str        # 'pending', 'running', 'success', 'failed'
    result: dict | None
    shots: int
    submit_time: str
    update_time: str
    metadata: dict
```

## Task Status Values

| Status | Description |
|--------|-------------|
| `pending` | Task submitted, waiting in queue |
| `running` | Task executing on quantum hardware |
| `success` | Task completed, results available |
| `failed` | Task failed, check error details |

## Complete Submission Workflow

### Programmatic

```python
import os
from uniqc.circuit_builder import Circuit
from uniqc import submit_task, wait_for_result

# Enable dummy mode for testing
os.environ['UNIQC_DUMMY'] = 'true'

# Build circuit
c = Circuit(4)
c.h(0)
for i in range(3):
    c.cnot(i, i + 1)
c.measure(0, 1, 2, 3)

# Submit
task_id = submit_task(c.originir, backend='originq', shots=1000)
print(f"Submitted task: {task_id}")

# Wait for result
result = wait_for_result(task_id, backend='originq', timeout=300)
print(f"Result: {result}")
```

### CLI

```bash
# Submit and wait
uniqc submit circuit.oir --platform originq --shots 1000 --wait

# Check status separately
uniqc task list --platform originq
uniqc result <task-id> --platform originq --wait
```

## Error Handling

```python
from uniqc import submit_task, wait_for_result

try:
    task_id = submit_task(c.originir, backend='originq', shots=1000)
    result = wait_for_result(task_id, backend='originq', timeout=300)
except TimeoutError:
    print("Task did not complete within timeout")
except ConnectionError:
    print("Could not connect to cloud platform")
except ValueError as e:
    print(f"Invalid configuration: {e}")
```

## Best Practices

1. **Test locally first**: Use dummy mode or local simulator before submitting to real hardware
2. **Validate circuits**: Check circuit depth and gate count against target chip constraints
3. **Batch submissions**: Use `submit_batch` for multiple circuits to reduce API overhead
4. **Set timeouts**: Always specify a timeout when waiting for results on real hardware
5. **Save task IDs**: Store task IDs for later result retrieval
6. **Use profiles**: Separate development and production configurations
