#!/bin/bash
# CLI demonstration script for QPanda-lite
#
# This script demonstrates the main CLI commands:
# - circuit: format conversion and circuit info
# - simulate: local simulation
# - submit: cloud submission (commented out)
# - config: configuration management

set -e

echo "============================================================"
echo "QPanda-lite CLI Demonstration"
echo "============================================================"

# Create a temporary directory for demo files
DEMO_DIR=$(mktemp -d)
cd "$DEMO_DIR"

# ------------------------------------------------------------
# 1. Create a circuit file (Bell state in OriginIR format)
# ------------------------------------------------------------
echo ""
echo "1. Creating Bell state circuit file..."
cat > bell_state.oir << 'EOF'
QINIT 2
CREG 2
H q[0]
CNOT q[0],q[1]
MEASURE q[0],c[0]
MEASURE q[1],c[1]
EOF
echo "   Created: bell_state.oir"

# ------------------------------------------------------------
# 2. Circuit info and format conversion
# ------------------------------------------------------------
echo ""
echo "2. Circuit info:"
echo "------------------------------------------------------------"
qpandalite circuit bell_state.oir --info

echo ""
echo "3. Convert to QASM format:"
echo "------------------------------------------------------------"
qpandalite circuit bell_state.oir --format qasm -o bell_state.qasm
cat bell_state.qasm

echo ""
echo "4. Convert QASM back to OriginIR:"
echo "------------------------------------------------------------"
qpandalite circuit bell_state.qasm --format originir

# ------------------------------------------------------------
# 3. Local simulation
# ------------------------------------------------------------
echo ""
echo "5. Simulate with statevector backend:"
echo "------------------------------------------------------------"
qpandalite simulate bell_state.oir --backend statevector --shots 1024 --format table

echo ""
echo "6. Simulate with JSON output:"
echo "------------------------------------------------------------"
qpandalite simulate bell_state.oir --shots 4096 --format json | head -20

# ------------------------------------------------------------
# 4. Configuration (show current config)
# ------------------------------------------------------------
echo ""
echo "7. Current configuration:"
echo "------------------------------------------------------------"
qpandalite config list 2>/dev/null || echo "   (No configuration file found - run 'qpandalite config init' to create)"

# ------------------------------------------------------------
# 5. Cloud submission (commented out - requires API tokens)
# ------------------------------------------------------------
echo ""
echo "8. Cloud submission examples (commented out):"
echo "------------------------------------------------------------"
cat << 'EXAMPLES'
# Submit to OriginQ (requires qpandalite config set originq.token YOUR_TOKEN)
# qpandalite submit bell_state.oir --platform originq --shots 1000 --name "bell-test"

# Submit to Quafu (requires qpandalite config set quafu.token YOUR_TOKEN)
# qpandalite submit bell_state.oir --platform quafu --chip-id ScQ-P10 --shots 1000

# Submit and wait for result
# qpandalite submit bell_state.oir --platform originq --shots 1000 --wait --timeout 300

# Test with dummy platform (no tokens required)
qpandalite submit bell_state.oir --platform dummy --shots 100
EXAMPLES

# Run dummy platform test
echo ""
echo "   Testing with dummy platform:"
qpandalite submit bell_state.oir --platform dummy --shots 100

# ------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------
cd - > /dev/null
rm -rf "$DEMO_DIR"

echo ""
echo "============================================================"
echo "CLI demonstration complete!"
echo "============================================================"
