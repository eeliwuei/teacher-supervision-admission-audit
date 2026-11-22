#!/bin/bash
# Addendum 05: when a running lane starts a queued (wrongly configured) CBox-M run on H100, stop that one trainer
# process, set its partial directory aside, and start the corrected run. Usage: swap_cbox_h100.sh <seed> <tag>
seed="$1"; tag="$2"; cd /deepet/police_ai_video/experiments/ccad_yolo26n/kais_v4
name="CBox-M_seed${seed}_kaisv4"; L=logs/swap_cbox_${seed}.log
while ! cat logs/v4_chain_h100_L*.log | grep -q "START $name "; do sleep 5; done
sleep 20
pkill -u "$(id -un)" -f -- "--name $name " ; echo "$(date -u +%FT%TZ) stopped wrongly configured $name (pkill rc=$?)" >> $L
for i in $(seq 1 60); do pgrep -u "$(id -un)" -f -- "--name $name " >/dev/null || break; sleep 5; done
sleep 10
[ -d ../models/students/$name ] && mv ../models/students/$name ../models/students/${name}_ABORTED_lambdacls && echo "$(date -u +%FT%TZ) partial dir set aside" >> $L
[ -f logs/$name.log ] && mv logs/$name.log logs/${name}_ABORTED_lambdacls.log
nohup setsid ./run_v4_cbox.sh envs/ccad_yolo26n/bin/python 0 "$tag" "CBox-M:$seed" > /dev/null 2>&1 < /dev/null &
echo "$(date -u +%FT%TZ) corrected run launched, chain tag $tag" >> $L
