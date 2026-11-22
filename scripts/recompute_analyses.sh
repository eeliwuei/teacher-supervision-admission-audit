#!/bin/sh
# Run the filed analysis scripts, unchanged, on the files under evidence/ and
# compare with the filed results (evidence/tools/recompute.py).
# Needs numpy and scipy. Output goes to _out/recompute/, not into evidence/,
# so that evidence/MANIFEST.sha256 stays valid.
# Usage: scripts/recompute_analyses.sh [STEP ...]
#   STEP is any of: digests order add06 a04 pairs gate counts (default: all)
# Set PYTHON to use another interpreter (default: python3).
# Exit status 0 only if every comparison matches.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}
mkdir -p "$ROOT/_out/recompute" || exit 2
exec "$PYTHON" -I "$ROOT/evidence/tools/recompute.py" --out "$ROOT/_out/recompute" "$@"
