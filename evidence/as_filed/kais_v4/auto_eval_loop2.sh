#!/bin/bash
# Server-side loop: evaluates each finished run once (same rule as /tmp/eval_new2.sh), then bootstrap draws.
# Extra guard: a CBox-M run is evaluated only if its run summary shows lambda_cls 0.0 and kd_matches_cls 0.
# v2 (2026-11-14): adds the completeness guard. Stop: touch kais_v4/auto_eval.STOP
cd /deepet/police_ai_video/experiments/ccad_yolo26n
PY=/deepet/police_ai_video/envs/ccad_yolo26n/bin/python
while [ ! -e kais_v4/auto_eval.STOP ]; do
  new=""
  for n in $(grep -h " DONE " kais_v4/logs/*chain*.log | grep "rc=0" | awk "{print \$3}" | sort -u); do
    [ -f eval/factorial_v3_freeze/$n/metrics_unified.json ] && continue
    [ -e eval/factorial_v3_freeze/$n/.eval_lock ] && continue
    [ "$($PY kais_v4/analysis/eval_kaisv4.py $n --dry | grep -c "\"finished\": true")" = "1" ] || continue
    # completeness guard (Addendum 06): the rc in old chain logs is always 0, so require 150 epochs and the trainer line
    ep=$(($(wc -l < models/students/$n/results.csv)-1)); fin=$(grep -c "150 epochs completed" kais_v4/logs/$n.log 2>/dev/null)
    { [ "$ep" = "150" ] && [ "$fin" -ge 1 ]; } || { echo "$(date -u +%FT%TZ) HOLD $n (incomplete: epochs=$ep completed_line=$fin)"; continue; }
    case $n in CBox-M_*)
      ok=$(python3 -c "import json;s=json.load(open(\"models/students/$n/ccad_stockloop_run_summary.json\"));print(int(s[\"lambda_cls\"]==0 and s[\"kd_matches_cls\"]==0))" 2>/dev/null)
      [ "$ok" = "1" ] || { echo "$(date -u +%FT%TZ) HOLD $n (CBox-M summary check failed)"; continue; }
      echo "- $(date -u +%FT%TZ) (H100 clock): $n checked before evaluation by auto_eval_loop.sh: lambda_cls 0.0, kd_matches_cls 0." >> kais_v4/PROVENANCE_KAIS_V4.md;;
    esac
    echo "$(date -u +%FT%TZ) EVAL $n"
    $PY kais_v4/analysis/eval_kaisv4.py $n --device 0 2>&1 | tail -1 | cut -c1-260
    echo "$(date -u +%FT%TZ) EVALDONE $n"
    [ -f eval/factorial_v3_freeze/$n/metrics_unified.json ] && new="$new eval/factorial_v3_freeze/$n" && echo "- $(date -u +%FT%TZ) (H100 clock): $n evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked)." >> kais_v4/PROVENANCE_KAIS_V4.md
  done
  [ -n "$new" ] && $PY kais_v4/analysis/bootstrap_a04.py full kais_v4/analysis/a04_draws $new
  sleep 600
done
