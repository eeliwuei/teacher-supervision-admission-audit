#!/bin/sh
# Recompute the run-time gate summary from the files in
# evidence/gate_rows_nocoord/ (per-row files for the rows of D3 and D4; count
# cells, totals and sorted value lists for the other rows) and compare it,
# byte for byte, with the filed summary. Standard library only. Output goes
# to _out/gate/.
# Set PYTHON to use another interpreter (default: python3).
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}
G="$ROOT/evidence/gate_rows_nocoord"
FILED="$ROOT/evidence/scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt"
OUT="$ROOT/_out/gate"
mkdir -p "$OUT" || exit 2
NEW="$OUT/runtime_gate_analysis.recomputed.txt"
"$PYTHON" -I "$G/runtime_gate_analyze_nocoord.py" "$G" > "$NEW" || { echo "recompute_gate: the analysis script failed"; exit 1; }
grep -E '^(=+ |ADMITTED)' "$NEW"
STATUS=0
if cmp -s "$NEW" "$FILED"; then
  echo "IDENTICAL to evidence/scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt"
else
  echo "DIFFERS from evidence/scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt"; STATUS=1
fi
if cmp -s "$NEW" "$G/runtime_gate_analysis.txt"; then
  echo "IDENTICAL to evidence/gate_rows_nocoord/runtime_gate_analysis.txt"
else
  echo "DIFFERS from evidence/gate_rows_nocoord/runtime_gate_analysis.txt"; STATUS=1
fi
echo "lines: $(wc -l < "$NEW" | tr -d ' ')   output: _out/gate/runtime_gate_analysis.recomputed.txt"
if [ "$STATUS" -eq 0 ]; then echo "recompute_gate: PASS"; else echo "recompute_gate: FAIL"; fi
exit "$STATUS"
