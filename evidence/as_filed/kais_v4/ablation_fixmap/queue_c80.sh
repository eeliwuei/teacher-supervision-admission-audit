#!/bin/bash
# Addendum 06: start the seven same-card control runs on device 2 (A100 80GB) of r7525 when the six wave-2
# mechanism lanes on that device (fixall, oldmask, randmask at seeds 42 and 1337) have all written ALL DONE.
# One lane per run, as in wave 2. Runs on r7525 as the experiment's user; starts only its own processes.
cd /deepet/police_ai_video/experiments/ccad_yolo26n/kais_v4 || exit 1
mkdir logs/.queue_c80.lock 2>/dev/null || { echo "$(date -u +%FT%TZ) queue already started; exit" >> logs/mech_queue_c80.log; exit 1; }
P=/deepet/police_ai_video/envs/ccad_yolo26n_r7525/bin/python; R=ablation_fixmap/run_mech_c80.sh
[ -x "$P" ] && [ -f "$R" ] || { echo "$(date -u +%FT%TZ) missing python or launcher; exit" >> logs/mech_queue_c80.log; exit 1; }
done6() { grep -l "ALL DONE" logs/mech_chain_mech_w2_fixall_42.log logs/mech_chain_mech_w2_fixall_1337.log logs/mech_chain_mech_w2_oldmask_42.log logs/mech_chain_mech_w2_oldmask_1337.log logs/mech_chain_mech_w2_rand_42.log logs/mech_chain_mech_w2_rand_1337.log 2>/dev/null | wc -l; }
echo "$(date -u +%FT%TZ) queue armed; lanes finished now: $(done6)" >> logs/mech_queue_c80.log
while [ "$(done6)" -lt 6 ]; do sleep 180; done
echo "$(date -u +%FT%TZ) addendum 06 start" >> logs/mech_queue_c80.log
for s in 42 1337 20260703; do
  nohup setsid bash $R $P 2 std_$s  C1-M:$s:std > /dev/null 2>> logs/mech_queue_c80.log < /dev/null &
  nohup setsid bash $R $P 2 nokd_$s C0-R:$s:std > /dev/null 2>> logs/mech_queue_c80.log < /dev/null &
done
nohup setsid bash $R $P 2 rand_20260703 C1-M:20260703:randmask > /dev/null 2>> logs/mech_queue_c80.log < /dev/null &
# card check (read-only): which GPU holds which process, 20 minutes after the start
sleep 1200
{ date -u +%FT%TZ; nvidia-smi --query-gpu=index,uuid,name,memory.used --format=csv; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv; pgrep -af "c80_seed" | cut -c1-160; } > logs/c80_nvidia_smi.txt 2>&1
