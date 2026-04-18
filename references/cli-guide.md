# CLI Guide Reference

Complete reference for the QPanda-lite command-line interface.

## Overview

The CLI is built with Typer and accessible via:
```bash
qpandalite <command> [options]
python -m qpandalite <command> [options]
```

Available commands: `circuit`, `simulate`, `submit`, `result`, `task`, `config`

## circuit - Format Conversion

Convert between OriginIR and OpenQASM 2.0 formats, display circuit statistics.

```bash
qpandalite circuit <input_file> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `input_file` | Yes | Input circuit file (OriginIR or QASM) |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--format` | `-f` | None | Output format: `originir` or `qasm` |
| `--output` | `-o` | None | Output file path (default: stdout) |
| `--info` | | False | Show circuit statistics |

### Examples

```bash
# Convert OriginIR to QASM
qpandalite circuit bell_state.oir --format qasm -o bell_state.qasm

# Show circuit info
qpandalite circuit bell_state.oir --info

# Convert QASM to OriginIR
qpandalite circuit bell_state.qasm --format originir
```

## simulate - Local Simulation

Simulate quantum circuits locally using statevector or density matrix backends.

```bash
qpandalite simulate <input_file> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `input_file` | Yes | Circuit file (OriginIR or QASM) |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--backend` | `-b` | `statevector` | Backend type: `statevector` or `density` |
| `--shots` | `-s` | 1024 | Number of measurement shots |
| `--format` | `-f` | `table` | Output format: `table` or `json` |
| `--output` | `-o` | None | Output file path |

### Examples

```bash
# Basic statevector simulation
qpandalite simulate circuit.oir

# With specific shot count
qpandalite simulate circuit.oir --shots 4096

# Density matrix backend with JSON output
qpandalite simulate circuit.oir --backend density --format json

# Save results to file
qpandalite simulate circuit.oir --shots 1024 -o results.json
```

## submit - Cloud Submission

Submit circuit files to quantum cloud platforms.

```bash
qpandalite submit <input_files...> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `input_files` | Yes | One or more circuit files to submit |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--platform` | `-p` | Required | Platform: `originq`, `quafu`, `ibm`, `dummy` |
| `--chip-id` | | None | Target chip ID for the platform |
| `--shots` | `-s` | 1000 | Number of measurement shots |
| `--name` | | None | Task name |
| `--wait` | `-w` | False | Wait for result after submission |
| `--timeout` | | 300.0 | Timeout in seconds when waiting |
| `--format` | `-f` | `table` | Output format: `table` or `json` |

### Platform Details

**OriginQ (`originq`)**:
- Requires `QPANDA_API_KEY` environment variable or config entry
- Available chips: varies by account

**Quafu (`quafu`)**:
- Requires `QUAFU_API_TOKEN` environment variable or config entry
- Chips: `ScQ-P10`, `ScQ-P18`, `ScQ-P136`, etc.
- Specify chip with `--chip-id`

**IBM Quantum (`ibm`)**:
- Requires `IBM_TOKEN` environment variable or config entry
- Uses Qiskit adapter internally

**Dummy (`dummy`)**:
- No credentials required
- Local simulation for testing
- Enable globally: `export QPANDALITE_DUMMY=true`

### Examples

```bash
# Submit to OriginQ
qpandalite submit circuit.oir --platform originq --shots 1000

# Submit to Quafu with specific chip
qpandalite submit circuit.oir --platform quafu --chip-id ScQ-P10 --shots 2000

# Submit and wait for result
qpandalite submit circuit.oir --platform originq --wait --timeout 600

# Submit multiple circuits
qpandalite submit circuit1.oir circuit2.oir --platform originq --name "batch-experiment"

# Test with dummy platform
qpandalite submit circuit.oir --platform dummy --shots 100
```

## result - Query Results

Query task results from quantum cloud platforms.

```bash
qpandalite result <task_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID returned by submit |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--platform` | `-p` | None | Platform name |
| `--wait` | `-w` | False | Wait for result if still running |
| `--timeout` | | 300.0 | Timeout in seconds when waiting |
| `--format` | `-f` | `table` | Output format: `table` or `json` |

### Examples

```bash
# Get result
qpandalite result abc-123-def --platform originq

# Wait for running task
qpandalite result abc-123-def --platform originq --wait --timeout 600
```

## task - Task Management

Manage submitted quantum computing tasks.

```bash
qpandalite task <subcommand> [options]
```

### Subcommands

#### list - List Tasks

```bash
qpandalite task list [options]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--status` | | None | Filter: `pending`, `running`, `success`, `failed` |
| `--platform` | `-p` | None | Filter by platform |
| `--limit` | `-l` | 20 | Maximum tasks to display |
| `--format` | `-f` | `table` | Output format: `table` or `json` |

#### show - Show Task Details

```bash
qpandalite task show <task_id>
```

#### clear - Clear Task History

```bash
qpandalite task clear
```

## config - Configuration

Manage API keys, tokens, and configuration profiles.

```bash
qpandalite config <subcommand> [options]
```

### Subcommands

#### init - Initialize Configuration

```bash
qpandalite config init
```

Creates `~/.qpandalite/qpandalite.yml` with default structure.

#### set - Set Configuration Value

```bash
qpandalite config set <key> <value>
```

Common keys:
```bash
qpandalite config set originq.token YOUR_TOKEN
qpandalite config set originq.submit_url https://...
qpandalite config set originq.query_url https://...
qpandalite config set quafu.token YOUR_TOKEN
qpandalite config set ibm.token YOUR_TOKEN
```

#### get - Get Configuration Value

```bash
qpandalite config get <key>
```

#### list - List All Configuration

```bash
qpandalite config list
```

#### validate - Validate Configuration

```bash
qpandalite config validate
```

Checks that all required tokens and URLs are set for configured platforms.

#### profile - Manage Profiles

```bash
qpandalite config profile list              # List profiles
qpandalite config profile create <name>      # Create new profile
qpandalite config profile use <name>         # Switch active profile
```

## Complete CLI Session Example

```bash
# 1. Initialize configuration
qpandalite config init

# 2. Set up API tokens
qpandalite config set originq.token YOUR_TOKEN

# 3. Create a circuit file
cat > bell_state.oir << 'EOF'
QINIT 2
CREG 2
H q[0]
CNOT q[0],q[1]
MEASURE q[0],c[0]
MEASURE q[1],c[1]
EOF

# 4. Check circuit info
qpandalite circuit bell_state.oir --info

# 5. Convert to QASM
qpandalite circuit bell_state.oir --format qasm -o bell_state.qasm

# 6. Simulate locally
qpandalite simulate bell_state.oir --shots 4096 --format json

# 7. Submit to cloud
qpandalite submit bell_state.oir --platform originq --shots 1000 --name "bell-test"

# 8. Check task status
qpandalite task list --platform originq

# 9. Get result (when ready)
qpandalite result <task-id> --platform originq

# 10. Test with dummy platform
qpandalite submit bell_state.oir --platform dummy --shots 100
```
