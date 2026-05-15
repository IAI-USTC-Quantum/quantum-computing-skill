#!/usr/bin/env bash
# Installation verification script for UnifiedQuantum examples and common workflows.

set -u

PASSED=0
FAILED=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

run_py() {
  python3 "$@"
}

echo "============================================================"
echo "UnifiedQuantum Environment Check"
echo "============================================================"

echo
echo "1. Python"
echo "------------------------------------------------------------"
if command -v python3 >/dev/null 2>&1; then
  echo "   Python: $(python3 --version)"
  if python3 -c "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] < (3, 14) else 1)"; then
    check_pass "Python version is within UnifiedQuantum's supported range"
  else
    check_fail "UnifiedQuantum expects Python >= 3.10 and < 3.14"
  fi
else
  check_fail "python3 not found"
fi

echo
echo "2. Core Package"
echo "------------------------------------------------------------"
if run_py - <<'PY'
import uniqc
print(getattr(uniqc, "__version__", "unknown"))
PY
then
  check_pass "uniqc imports successfully"
else
  check_fail "uniqc import failed. Install with: pip install unified-quantum"
fi

echo
echo "3. Core Runtime Dependencies"
echo "------------------------------------------------------------"
for pkg in numpy scipy requests yaml sympy; do
  if run_py - <<PY
import ${pkg}
print(getattr(${pkg}, "__version__", "ok"))
PY
  then
    check_pass "${pkg} is importable"
  else
    check_fail "${pkg} is missing"
  fi
done

echo
echo "4. CLI"
echo "------------------------------------------------------------"
if command -v uniqc >/dev/null 2>&1; then
  if uniqc --help >/dev/null 2>&1; then
    check_pass "uniqc CLI command works"
  else
    check_fail "uniqc command exists but --help failed"
  fi
elif run_py -m uniqc.cli --help >/dev/null 2>&1; then
  check_pass "python3 -m uniqc.cli works"
else
  check_fail "No working CLI entrypoint found"
fi

if command -v uniqc >/dev/null 2>&1; then
  if uniqc backend --help >/dev/null 2>&1; then
    check_pass "uniqc backend command is available"
  else
    check_warn "uniqc backend command is unavailable; backend discovery workflows may not work"
  fi
fi

echo
echo "5. Circuit Builder Smoke Test"
echo "------------------------------------------------------------"
if run_py - <<'PY'
from uniqc import Circuit

c = Circuit(2)
c.h(0)
c.cnot(0, 1)
c.measure(0, 1)

assert "QINIT" in c.originir
assert "OPENQASM" in c.qasm
print(c.originir)
PY
then
  check_pass "Circuit export to OriginIR and QASM works"
else
  check_fail "Circuit builder smoke test failed"
fi

echo
echo "6. Optional Features"
echo "------------------------------------------------------------"
if run_py - <<'PY'
import qutip
print(qutip.__version__)
PY
then
  check_pass "qutip is available (simulation extra looks installed)"
else
  check_warn "qutip is missing; local simulation and dummy mode examples may fail"
fi

if run_py - <<'PY'
import torch
print(torch.__version__)
PY
then
  check_pass "torch is available"
else
  check_warn "torch is missing; PyTorch helper examples will be skipped"
fi

if run_py - <<'PY'
import sklearn
print(sklearn.__version__)
PY
then
  check_pass "scikit-learn is available"
else
  check_warn "scikit-learn is missing; digit-classification example will be skipped"
fi

if run_py - <<'PY'
try:
    import qiskit
    print("qiskit", qiskit.__version__)
    import qiskit_ibm_runtime
    print("qiskit_ibm_runtime", qiskit_ibm_runtime.__version__)
except Exception as exc:
    raise SystemExit(str(exc))
PY
then
  check_pass "IBM qiskit runtime packages are importable"
else
  check_warn "IBM qiskit runtime packages are not importable; IBM adapter may fail unless qiskit extra is installed"
fi

if run_py - <<'PY'
try:
    import quark
    print("quark", getattr(quark, "__version__", "ok"))
except Exception as exc:
    raise SystemExit(str(exc))
PY
then
  check_pass "quark (QuarkStudio) is importable"
else
  check_warn "quark is not importable; Quark platform adapter will not work (requires Python >= 3.12)"
fi

echo
echo "7. Local Simulation Smoke Test"
echo "------------------------------------------------------------"
if run_py - <<'PY'
from uniqc.backend_adapter.task.optional_deps import check_simulation

if not check_simulation():
    raise SystemExit(2)

from uniqc import Circuit
from uniqc.simulator import Simulator

c = Circuit(2)
c.h(0)
c.cnot(0, 1)
c.measure(0, 1)

sim = Simulator(backend_type="statevector")
probs = sim.simulate_pmeasure(c)
assert len(probs) > 0
print("nonzero entries:", sum(1 for value in probs if float(value) > 1e-12))
PY
then
  check_pass "Local simulation works"
else
  status=$?
  if [ "$status" -eq 2 ]; then
    check_warn "Simulation extra not installed; local simulation smoke test skipped"
  else
    check_fail "Local simulation smoke test failed"
  fi
fi

echo
echo "============================================================"
echo "Summary"
echo "============================================================"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"

if [ "$FAILED" -eq 0 ]; then
  echo
  echo -e "${GREEN}Environment looks good for the current UnifiedQuantum workflow.${NC}"
else
  echo
  echo -e "${YELLOW}Some checks failed. Suggested installs:${NC}"
  echo "  uv pip install unified-quantum"
  echo "  uv pip install \"unified-quantum[simulation]\""
  echo "  uv pip install \"unified-quantum[pytorch]\""
  echo "  uv pip install \"unified-quantum[quark]\"    # Python >= 3.12 only"
  exit 1
fi
