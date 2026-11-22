#!/bin/bash
# Addendum 03 wave 2: start the remaining ten mechanism runs when all eight r7525b protocol lanes report ALL DONE.
cd /deepet/police_ai_video/experiments/ccad_yolo26n/kais_v4
P=envs/ccad_yolo26n_r7525/bin/python; R=ablation_fixmap/run_mech.sh
while [ "$(cat logs/v4_chain_r7525b_*.log | grep -c "ALL DONE")" -lt 8 ]; do sleep 180; done
echo "$(date -u +%FT%TZ) wave 2 start" >> logs/mech_queue_wave2.log
for s in 42 1337; do
  nohup setsid $R $P 2 mech_w2_fixall_$s  C1-M:$s:fixall   > /dev/null 2>&1 < /dev/null &
  nohup setsid $R $P 2 mech_w2_oldmask_$s C1-M:$s:oldmask  > /dev/null 2>&1 < /dev/null &
  nohup setsid $R $P 2 mech_w2_rand_$s    C1-M:$s:randmask > /dev/null 2>&1 < /dev/null &
  nohup setsid $R $P 0 mech_w2_std_$s     C1-M:$s:std      > /dev/null 2>&1 < /dev/null &
done
nohup setsid $R $P 0 mech_w2_nokd C0-R:42:std C0-R:1337:std > /dev/null 2>&1 < /dev/null &
