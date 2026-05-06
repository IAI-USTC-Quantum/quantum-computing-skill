#!/usr/bin/env bash
# Demo of the current uniqc CLI workflow.

set -euo pipefail

DEMO_DIR="${UNIQC_DEMO_DIR:-./.uniqc-demo}"
mkdir -p "$DEMO_DIR"
TMP_DIR="$DEMO_DIR"

run_uniqc() {
  if command -v uniqc >/dev/null 2>&1; then
    uniqc "$@"
  else
    python3 -m uniqc.cli "$@"
  fi
}

cat >"$TMP_DIR/build_bell.py" <<'PY'
from uniqc import Circuit

c = Circuit(2)
c.h(0)
c.cnot(0, 1)
c.measure(0, 1)

with open("bell.ir", "w", encoding="utf-8") as f:
    f.write(c.originir)
PY

echo "[1/7] Build a Bell circuit as OriginIR"
(cd "$TMP_DIR" && python3 build_bell.py)

echo
echo "[2/7] Show circuit info"
run_uniqc circuit "$TMP_DIR/bell.ir" --info

echo
echo "[3/7] Convert to OpenQASM 2.0"
run_uniqc circuit "$TMP_DIR/bell.ir" --format qasm -o "$TMP_DIR/bell.qasm"
sed -n '1,40p' "$TMP_DIR/bell.qasm"

echo
echo "[4/7] Try local simulation and dummy submission"
echo "These steps usually require unified-quantum[simulation]."

if run_uniqc simulate "$TMP_DIR/bell.ir" --shots 1024 --format json; then
  echo
  echo "Dummy submission exercises the same submit/result flow before using a real backend."
  run_uniqc submit "$TMP_DIR/bell.ir" --platform dummy --wait --format json
else
  echo "Simulation failed. Install unified-quantum[simulation] and retry."
fi

echo
echo "[5/7] Run readout calibration on dummy backend"
echo "Results are cached to ~/.uniqc/calibration_cache/."
if run_uniqc calibrate readout --qubits 0 1 --backend dummy --shots 1000; then
  echo "Readout calibration complete."
else
  echo "Readout calibration failed (requires simulation extras). Skipping."
fi

echo
echo "[6/7] Run XEB benchmarking on dummy backend"
if run_uniqc calibrate xeb --qubits 0 1 --type 1q --backend dummy --shots 500 --depths 5 10 --n-circuits 10; then
  echo "XEB benchmarking complete."
else
  echo "XEB benchmarking failed (requires simulation extras). Skipping."
fi

echo
echo "[7/7] Show backend list (first 5 lines)"
run_uniqc backend list --format table 2>/dev/null | head -5 || true

echo
echo "Demo artefacts kept in: $DEMO_DIR"
echo "(override with UNIQC_DEMO_DIR=/path/to/dir before re-running)"
