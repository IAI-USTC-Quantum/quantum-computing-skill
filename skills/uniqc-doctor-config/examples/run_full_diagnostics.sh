#!/usr/bin/env bash
# uniqc-doctor-config: end-to-end health check.
# Run this in any uniqc-installed environment; output is safe to share
# with maintainers (tokens are masked by `uniqc doctor`).

set -euo pipefail

echo "=== 1. uniqc doctor (environment + deps + tokens + cache + connectivity)"
uniqc doctor || true                # don't abort on partial failures

echo
echo "=== 2. uniqc config validate (deeper config-only check)"
uniqc config validate || true

echo
echo "=== 3. uniqc config list"
uniqc config list || true

echo
echo "=== 4. uniqc backend list (refresh per-platform cache first)"
for plat in originq ibm quark; do
  echo "  - refreshing $plat ..."
  uniqc backend update --platform "$plat" 2>&1 | sed 's/^/      /' || true
done
uniqc backend list || true

echo
echo "=== 5. dummy local smoke test (no quota, no auth)"
TMP=$(mktemp /tmp/uniqc_smoke.XXXXXX.originir)
cat > "$TMP" <<'IR'
QINIT 2
H q[0]
CNOT q[0],q[1]
MEASURE q[0],c[0]
MEASURE q[1],c[1]
IR
uniqc submit "$TMP" --backend dummy:local:simulator --shots 200 --wait
rm -f "$TMP"
