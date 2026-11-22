#!/bin/bash
# best.pt sensitivity (Addendum 01 A5): for every run that already has an endpoint evaluation, score best.pt once
# with analysis/eval_kaisv4_best.py (sha256 284e6217...abc3). Sensitivity only. Stop with: touch kais_v4/auto_best.STOP
cd /deepet/police_ai_video/experiments/ccad_yolo26n
PY=/deepet/police_ai_video/envs/ccad_yolo26n/bin/python
while [ ! -e kais_v4/auto_best.STOP ]; do
  for d in eval/factorial_v3_freeze/*_kaisv4 eval/factorial_v3_freeze/*_kaisv4mech; do
    n=$(basename $d); [ -f $d/metrics_unified.json ] || continue
    [ -e eval/kaisv4_bestpt/$n/.eval_lock ] && continue
    echo "$(date -u +%FT%TZ) BEST $n"; $PY kais_v4/analysis/eval_kaisv4_best.py $n --device 0 2>&1 | tail -1 | cut -c1-600
  done
  sleep 600
done
