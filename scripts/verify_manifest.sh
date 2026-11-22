#!/bin/sh
# Check every file under evidence/ against evidence/MANIFEST.sha256.
# Run from anywhere; exit status 0 only if every file matches.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT/evidence" || exit 2
if command -v sha256sum >/dev/null 2>&1; then SUM="sha256sum"; else SUM="shasum -a 256"; fi
OUT=$($SUM -c MANIFEST.sha256 2>&1)
STATUS=$?
TOTAL=$(wc -l < MANIFEST.sha256 | tr -d ' ')
OK=$(printf '%s\n' "$OUT" | grep -c ': OK$')
printf '%s\n' "$OUT" | grep -v ': OK$'
echo "manifest entries: $TOTAL   files OK: $OK"
# files under evidence/ that the manifest does not list
EXTRA=$(find . -type f ! -name MANIFEST.sha256 | sed 's|^\./||' | LC_ALL=C sort | while IFS= read -r f; do
  cut -c67- MANIFEST.sha256 | grep -qxF -- "$f" || printf '%s\n' "$f"; done)
if [ -n "$EXTRA" ]; then echo "files not listed in the manifest:"; printf '%s\n' "$EXTRA"; STATUS=1; fi
if [ "$STATUS" -eq 0 ] && [ "$OK" -eq "$TOTAL" ]; then echo "verify_manifest: PASS"; exit 0; fi
echo "verify_manifest: FAIL"; exit 1
