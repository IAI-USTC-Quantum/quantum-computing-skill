# CLI Guide Reference

Complete reference for the UnifiedQuantum command-line interface.

## Overview

The CLI is built with Typer and accessible via:
```bash
uniqc <command> [options]
python -m uniqc <command> [options]
```

Available commands: `circuit`, `simulate`, `submit`, `result`, `task`, `config`

## circuit - Format Conversion

Convert between OriginIR and OpenQASM 2.0 formats, display circuit statistics.

```bash
uniqc circuit <input_file> [options]
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
uniqc circuit bell_state.oir --format qasm -o bell_state.qasm

# Show circuit info
uniqc circuit bell_state.oir --info

# Convert QASM to OriginIR
uniqc circuit bell_state.qasm --format originir
```

## simulate - Local Simulation

Simulate quantum circuits locally using statevector or density matrix backends.

```bash
uniqc simulate <input_file> [options]
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
uniqc simulate circuit.oir

# With specific shot count
uniqc simulate circuit.oir --shots 4096

# Density matrix backend with JSON output
uniqc simulate circuit.oir --backend density --format json

# Save results to file
uniqc simulate circuit.oir --shots 1024 -o results.json
```

## submit - Cloud Submission

Submit circuit files to quantum cloud platforms.

```bash
uniqc submit <input_files...> [options]
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
- Requires token in config (`uniqc config set originq.token YOUR_TOKEN`)
- Available chips: varies by account

**Quafu (`quafu`)**:
- Requires token in config (`uniqc config set quafu.token YOUR_TOKEN`)
- Chips: `ScQ-P10`, `ScQ-P18`, `ScQ-P136`, etc.
- Specify chip with `--chip-id`

**IBM Quantum (`ibm`)**:
- Requires token in config (`uniqc config set ibm.token YOUR_TOKEN`)
- Uses Qiskit adapter internally

**Dummy (`dummy`)**:
- No credentials required
- Local simulation for testing
- Enable globally: `export UNIQC_DUMMY=true`

### Examples

```bash
# Submit to OriginQ
uniqc submit circuit.oir --platform originq --shots 1000

# Submit to Quafu with specific chip
uniqc submit circuit.oir --platform quafu --chip-id ScQ-P10 --shots 2000

# Submit and wait for result
uniqc submit circuit.oir --platform originq --wait --timeout 600

# Submit multiple circuits
uniqc submit circuit1.oir circuit2.oir --platform originq --name "batch-experiment"

# Test with dummy platform
uniqc submit circuit.oir --platform dummy --shots 100
```

## result - Query Results

Query task results from quantum cloud platforms.

```bash
uniqc result <task_id> [options]
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
uniqc result abc-123-def --platform originq

# Wait for running task
uniqc result abc-123-def --platform originq --wait --timeout 600
```

## task - Task Management

Manage submitted quantum computing tasks.

```bash
uniqc task <subcommand> [options]
```

### Subcommands

#### list - List Tasks

```bash
uniqc task list [options]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--status` | | None | Filter: `pending`, `running`, `success`, `failed` |
| `--platform` | `-p` | None | Filter by platform |
| `--limit` | `-l` | 20 | Maximum tasks to display |
| `--format` | `-f` | `table` | Output format: `table` or `json` |

#### show - Show Task Details

```bash
uniqc task show <task_id>
```

#### clear - Clear Task History

```bash
uniqc task clear
```

## config - Configuration

Manage API keys, tokens, and configuration profiles.

```bash
uniqc config <subcommand> [options]
```

### Subcommands

#### init - Initialize Configuration

```bash
uniqc config init
```

Creates `~/.uniqc/uniqc.yml` with default structure.

#### set - Set Configuration Value

```bash
uniqc config set <key> <value>
```

Common keys:
```bash
uniqc config set originq.token YOUR_TOKEN
uniqc config set quafu.token YOUR_TOKEN
uniqc config set ibm.token YOUR_TOKEN
```

#### get - Get Configuration Value

```bash
uniqc config get <key>
```

#### list - List All Configuration

```bash
uniqc config list
```

#### validate - Validate Configuration

```bash
uniqc config validate
```

Checks that all required tokens are set for configured platforms.

#### profile - Manage Profiles

```bash
uniqc config profile list              # List profiles
uniqc config profile create <name>      # Create new profile
uniqc config profile use <name>         # Switch active profile
```

Alternatively, set `UNIQC_PROFILE=<name>` to override the active profile for a single invocation.

## Complete CLI Session Example

```bash
# 1. Initialize configuration
uniqc config init

# 2. Set up API tokens
uniqc config set originq.token YOUR_TOKEN

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
uniqc circuit bell_state.oir --info

# 5. Convert to QASM
uniqc circuit bell_state.oir --format qasm -o bell_state.qasm

# 6. Simulate locally
uniqc simulate bell_state.oir --shots 4096 --format json

# 7. Submit to cloud
uniqc submit bell_state.oir --platform originq --shots 1000 --name "bell-test"

# 8. Check task status
uniqc task list --platform originq

# 9. Get result (when ready)
uniqc result <task-id> --platform originq

# 10. Test with dummy platform
uniqc submit bell_state.oir --platform dummy --shots 100
```
