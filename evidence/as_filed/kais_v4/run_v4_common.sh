#!/bin/bash
# KAIS v4 runs. Usage: run_v4_common.sh <PY> <device> <chain-tag> <mid:seed> [<mid:seed> ...]  (one serial lane)
set -u
cd /deepet/police_ai_video
PY="$1"; DEV="$2"; TAG="$3"; shift 3
EXP=experiments/ccad_yolo26n
LOG=$EXP/kais_v4/logs; CHAIN="$LOG/v4_chain_${TAG}.log"
for item in "$@"; do
  mid="${item%%:*}"; seed="${item##*:}"
  case "$mid" in
    F-ShufSingle-s[4-7]) SCHED=$EXP/kais_v4/phase4_view_schedules_v4_kais_shuffled.yaml; SHA=82769c508af610521e97ee2a26fc05a3949f8c5a4ca4f1dab710cf16cfd91a9b;;
    C0-R|CBox-M|C1-M|C4-M) SCHED=$EXP/configs/phase4_view_schedules_v1.yaml; SHA=090d4829048b729c0f844075c303dd4b6f65e9e9763001551454a117d97ac414;;
    *) echo "bad mid $mid" >> "$CHAIN"; exit 2;;
  esac
  name="${mid}_seed${seed}_kaisv4"
  echo "$(date -u +%FT%TZ) START $name host=$(hostname) dev=$DEV" >> "$CHAIN"
  $PY tools/ccad/train_yolo26_ccad_stockloop.py \
    --config $EXP/configs/ccad_project.yaml \
    --name "$name" --model-id "$mid" \
    --schedule-file "$SCHED" --expected-schedule-sha256 "$SHA" \
    --protocol-sha256 1f4372dc3c78555c1dca228f489def2a5a71a93d04736a698ca5abc3e7bac2e1 \
    --evidence-bank $EXP/label_banks/evidence/selected_best_stg1_v2/evidence_bank.jsonl \
    --evidence-sha256 eca4969b5586a41feae1c79ac6cda1efe29d9b5929b2f309b1d4f155434b9cbc \
    --epochs 150 --batch 16 --imgsz 960 --seed "$seed" --device "$DEV" \
    --temperature 1.0 --lambda-box 0.45423083821737265 --lambda-cls 0.4613535884454487 \
    --save-period 5 --val --amp --allow-full-training \
    >> "$LOG/${name}.log" 2>&1
  echo "$(date -u +%FT%TZ) DONE $name rc=$?" >> "$CHAIN"
done
echo "$(date -u +%FT%TZ) LANE $TAG ALL DONE" >> "$CHAIN"
