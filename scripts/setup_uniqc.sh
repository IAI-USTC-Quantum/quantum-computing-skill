#!/bin/bash
# Installation verification script for UnifiedQuantum skill
#
# This script checks if UnifiedQuantum is properly installed and
# verifies that key components are working.
#
# Usage:
#   ./setup_uniqc.sh
#
# Exit codes:
#   0 - All checks passed
#   1 - Some checks failed

set -e

echo "============================================================"
echo "UnifiedQuantum Installation Verification"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counter
PASSED=0
FAILED=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED=$((PASSED + 1))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    FAILED=$((FAILED + 1))
}

check_warn() {
    echo -e "${YELLOW}!${NC} $1"
}

# ------------------------------------------------------------
# 1. Check Python version
# ------------------------------------------------------------
echo ""
echo "1. Python environment"
echo "------------------------------------------------------------"

PYTHON_VERSION=$(python3 --version 2>&1 || echo "not found")
echo "   Python: $PYTHON_VERSION"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    check_pass "Python >= 3.10 (compatible)"
else
    check_fail "Python >= 3.10 required (UnifiedQuantum needs 3.10+)"
fi

# ------------------------------------------------------------
# 2. Check uniqc installation
# ------------------------------------------------------------
echo ""
echo "2. UnifiedQuantum installation"
echo "------------------------------------------------------------"

if python3 -c "import uniqc" 2>/dev/null; then
    VERSION=$(python3 -c "import uniqc; print(getattr(uniqc, '__version__', 'unknown'))")
    check_pass "uniqc imported successfully (version: $VERSION)"
else
    check_fail "uniqc not found - install with: pip install unified-quantum"
fi

# ------------------------------------------------------------
# 3. Check core dependencies
# ------------------------------------------------------------
echo ""
echo "3. Core dependencies"
echo "------------------------------------------------------------"

for pkg in numpy scipy; do
    if python3 -c "import $pkg" 2>/dev/null; then
        VER=$(python3 -c "import $pkg; print($pkg.__version__)")
        check_pass "$pkg installed (version: $VER)"
    else
        check_fail "$pkg not installed"
    fi
done

# ------------------------------------------------------------
# 4. Check CLI installation
# ------------------------------------------------------------
echo ""
echo "4. CLI installation"
echo "------------------------------------------------------------"

if command -v uniqc &>/dev/null; then
    check_pass "uniqc CLI available"
    uniqc --help &>/dev/null && check_pass "CLI help works" || check_fail "CLI help failed"
elif python3 -m uniqc --help &>/dev/null; then
    check_pass "uniqc available via python -m uniqc"
else
    check_fail "CLI not available"
fi

# ------------------------------------------------------------
# 5. Check optional dependencies
# ------------------------------------------------------------
echo ""
echo "5. Optional dependencies"
echo "------------------------------------------------------------"

if python3 -c "import torch" 2>/dev/null; then
    VER=$(python3 -c "import torch; print(torch.__version__)")
    check_pass "PyTorch installed (version: $VER) - enables QML features"
else
    check_warn "PyTorch not installed - QML examples require PyTorch"
fi

if python3 -c "import matplotlib" 2>/dev/null; then
    VER=$(python3 -c "import matplotlib; print(matplotlib.__version__)")
    check_pass "matplotlib installed (version: $VER) - enables plotting"
else
    check_warn "matplotlib not installed - plotting not available"
fi

# ------------------------------------------------------------
# 6. Test circuit builder
# ------------------------------------------------------------
echo ""
echo "6. Circuit builder test"
echo "------------------------------------------------------------"

TEST_CIRCUIT=$(python3 << 'EOF'
try:
    from uniqc.circuit_builder import Circuit
    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
EOF
)

if [[ "$TEST_CIRCUIT" == "PASS" ]]; then
    check_pass "Circuit creation works"
else
    check_fail "Circuit creation failed: $TEST_CIRCUIT"
fi

# ------------------------------------------------------------
# 7. Test simulator
# ------------------------------------------------------------
echo ""
echo "7. Simulator test"
echo "------------------------------------------------------------"

TEST_SIM=$(python3 << 'EOF'
try:
    from uniqc.circuit_builder import Circuit
    from uniqc.simulator import OriginIR_Simulator

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0, 1)

    sim = OriginIR_Simulator()
    result = sim.simulate_shots(c.originir, shots=100)

    if len(result) > 0:
        print("PASS")
    else:
        print("FAIL: No results")
except Exception as e:
    print(f"FAIL: {e}")
EOF
)

if [[ "$TEST_SIM" == "PASS" ]]; then
    check_pass "Simulator works"
else
    check_fail "Simulator test failed: $TEST_SIM"
fi

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "Summary"
echo "============================================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All checks passed! UnifiedQuantum is ready to use.${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}Some checks failed. Please install missing dependencies.${NC}"
    echo ""
    echo "Installation commands:"
    echo "  pip install unified-quantum           # Core package"
    echo "  pip install unified-quantum[pytorch]  # With PyTorch support"
    exit 1
fi
