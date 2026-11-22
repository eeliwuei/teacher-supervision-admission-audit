#!/bin/bash
# Addendum 01 / A3: concurrent C4-M replicates at seeds 42 and 1337, started when lane h100_L5 (pid 2121120) ends.
cd /deepet/police_ai_video/experiments/ccad_yolo26n/kais_v4
while kill -0 2121120 2>/dev/null; do sleep 120; done
grep -q "LANE h100_L5 ALL DONE" logs/v4_chain_h100_L5.log || { echo "$(date -u +%FT%TZ) L5 ended without ALL DONE; L6 not started" >> logs/v4_chain_h100_L6.log; exit 1; }
exec ./run_v4_common.sh envs/ccad_yolo26n/bin/python 0 h100_L6 C4-M:42 C4-M:1337
