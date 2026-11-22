#!/usr/bin/env python3
"""KAIS follow-up (v4): four NEW independent shuffled-head / single-tail schedule
draws, built with the unchanged v3 generator (build_arm). Seeds continue the v3
rule for the (shuf,single) cell: schedule_seed = 20260721 + 1000 + k, k = 4..7.
Fixed before any v4 training run."""
import sys, hashlib, json
from collections import Counter
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "factorial_v3"))
import build_v3_factorial_schedules as b
schedules, meta, led = {}, {}, {}
for k in (4, 5, 6, 7):
    seed = 20260721 + 1000 + k
    name = f"F-ShufSingle-s{k}"
    seq = b.build_arm("shuf", "single", seed)
    assert Counter(seq) == b.M_COUNTS and seq[b.HEAD_LEN:] == b.TAIL_BASE
    schedules[name] = seq; meta[name] = {"order": "shuf", "tail": "single", "schedule_seed": seed}; led[name] = b.ledger(seq)
payload = {"schedule_version": "phase4_view_schedules_v4_kais_shuffled", "epochs": b.EPOCHS,
           "head_len": b.HEAD_LEN, "tail_len": b.TAIL_LEN, "global_multiset_counts": dict(b.M_COUNTS),
           "schedule_meta": meta, "schedules": schedules, "ledger": led}
out = Path(__file__).resolve().parent / "phase4_view_schedules_v4_kais_shuffled.yaml"
out.write_text(yaml.safe_dump(payload, sort_keys=False))
sha = hashlib.sha256(out.read_bytes()).hexdigest()
Path(str(out) + ".sha256").write_text(f"{sha}  {out.name}\n")
old = yaml.safe_load((Path(__file__).resolve().parent.parent / "factorial_v3/phase4_view_schedules_v3_factorial.yaml").read_text())["schedules"]
c4 = yaml.safe_load((Path(__file__).resolve().parent.parent / "configs/phase4_view_schedules_v1.yaml").read_text())["schedules"]["C4-M"]
allh = {n: tuple(s[:110]) for n, s in schedules.items()}
allh.update({n: tuple(old[n][:110]) for n in ("F-ShufSingle-s1","F-ShufSingle-s2","F-ShufSingle-s3")})
print(json.dumps({"sha256": sha, "distinct_heads": len(set(allh.values())), "n": len(allh),
  "tail_equals_C4M_tail": all(list(s[110:]) == list(c4[110:]) for s in schedules.values()),
  "C4M_multiset_equal": Counter(c4) == b.M_COUNTS,
  "v3_s1_regenerates": b.build_arm("shuf","single",20261722) == old["F-ShufSingle-s1"]}))
