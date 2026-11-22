#!/bin/bash
# KAIS v4 Addendum 06: same-card controls of the mechanism experiment on the A100 80GB card (device 2 of r7525).
# Copy of run_mech.sh (sha256 b42c61a4d9d73a9365b7e4802950f5772a6dc521a2042988b6e8e8e89802b45a) with five changes only:
# (1) run name carries the tag -c80; (2) chain log prefix is mech_chain_c80_; (3) exits unless the device argument is 2
# and nvidia-smi reports an 80GB A100 at index 2; (4) exits if the run directory exists; (5) the DONE line records the
# trainer's exit status (in run_mech.sh "rc=$?" inside the echo is the status of date and is always 0).
# Training arguments are unchanged.
# Usage: run_mech_c80.sh <PY> 2 <chain-tag> <mid:seed:mode> ...
# mode = std (stock script, stock mapping) | fixall | oldmask | randmask (train_mech.py). mid = C1-M (any mode) or C0-R (std only).
set -u
cd /deepet/police_ai_video
PY="$1"; DEV="$2"; TAG="$3"; shift 3
EXP=experiments/ccad_yolo26n
LOG=$EXP/kais_v4/logs; CHAIN="$LOG/mech_chain_c80_${TAG}.log"
GPUNAME=$(nvidia-smi --query-gpu=name --format=csv,noheader -i "$DEV")
if [ "$DEV" != "2" ] || [ "$GPUNAME" != "NVIDIA A100 80GB PCIe" ]; then echo "$(date -u +%FT%TZ) REFUSED dev=$DEV gpu=$GPUNAME" >> "$CHAIN"; exit 3; fi
SCHED=$EXP/configs/phase4_view_schedules_v1.yaml; SHA=090d4829048b729c0f844075c303dd4b6f65e9e9763001551454a117d97ac414
for item in "$@"; do
  IFS=: read -r mid seed mode <<< "$item"
  case "$mid:$mode" in
    C1-M:std|C0-R:std) SCRIPT=tools/ccad/train_yolo26_ccad_stockloop.py; unset CCAD_MECH_MODE;;
    C1-M:fixall|C1-M:oldmask|C1-M:randmask) SCRIPT=$EXP/kais_v4/ablation_fixmap/train_mech.py; export CCAD_MECH_MODE=$mode;;
    *) echo "bad item $item" >> "$CHAIN"; exit 2;;
  esac
  name="${mid}-${mode}-c80_seed${seed}_kaisv4mech"
  if [ -e "$EXP/models/students/$name" ]; then echo "$(date -u +%FT%TZ) REFUSED $name exists" >> "$CHAIN"; exit 4; fi
  echo "$(date -u +%FT%TZ) START $name host=$(hostname) dev=$DEV" >> "$CHAIN"
  $PY $SCRIPT \
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
  rc=$?
  echo "$(date -u +%FT%TZ) DONE $name rc=$rc" >> "$CHAIN"
done
echo "$(date -u +%FT%TZ) LANE $TAG ALL DONE" >> "$CHAIN"
