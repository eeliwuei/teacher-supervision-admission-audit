#!/usr/bin/env python3
"""List KD match bookkeeping of historical (non-*_kaisv4) stock-loop run summaries. Read-only."""
import json, glob, os
root = "/deepet/police_ai_video/experiments/ccad_yolo26n/models/students"
print("run,epochs,optimizer_steps,kd_steps,kd_matches_box,kd_matches_cls,box_per_kd_epoch,summary_mtime")
for p in sorted(glob.glob(root + "/*/ccad_stockloop_run_summary.json")):
    d = os.path.basename(os.path.dirname(p))
    if d.endswith("_kaisv4"):
        continue
    try:
        s = json.load(open(p))
    except Exception as e:
        print(d, "ERR", e); continue
    vl = s.get("view_list", [])
    vc = s.get("view_counts", {})
    st = s.get("optimizer_steps")
    kd_steps = sum(v for k, v in vc.items() if k != "human_only")
    kd_ep = sum(1 for v in vl if v != "human_only")
    box = s.get("kd_matches_box")
    import datetime
    print(",".join(str(x) for x in [d, len(vl), st, kd_steps, box, s.get("kd_matches_cls"),
          round(box / kd_ep, 2) if kd_ep and box is not None else "", datetime.datetime.utcfromtimestamp(os.path.getmtime(p)).isoformat()]))
