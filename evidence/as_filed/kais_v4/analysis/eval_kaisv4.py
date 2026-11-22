#!/usr/bin/env python3
"""Endpoint evaluation wrapper for kais_v4 / kaisv4mech runs (fixed before any of them finished).

The unified evaluator factorial_v3/factorial_freeze_eval.py rejects run names outside F-Mono*/F-Shuf*.
This wrapper changes only the name parsing and records the evaluation environment; scoring is the
evaluator's own code path (last.pt, val, imgsz 960, save_json, unified_for_pred). One evaluation per run:
--force is not passed, an existing metrics_unified.json is never overwritten.
All runs, from both training machines, are evaluated on H100 in envs/ccad_yolo26n.
Usage: eval_kaisv4.py <run_name> [--device N] [--dry]
"""
import sys, json, hashlib, platform, socket, datetime, re
from pathlib import Path
ROOT = Path("/deepet/police_ai_video"); EXP = ROOT / "experiments/ccad_yolo26n"
sys.path.insert(0, str(EXP / "factorial_v3"))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def parse_run(name):
    m = re.fullmatch(r"(.+)_seed(\d+)_(kaisv4|kaisv4mech)", name)
    if not m:
        raise SystemExit(f"not a kais_v4 run name: {name}")
    return m.group(1), int(m.group(2))

def finished(name):
    """True only if the LAST START/DONE line for exactly this name, over all chain logs, is 'DONE <name> rc=0'."""
    pat = re.compile(r"^(\S+) (START|DONE) " + re.escape(name) + r"(?: |$)(.*)$")
    ev = []
    for p in (EXP / "kais_v4/logs").glob("*chain*.log"):
        for line in p.read_text(errors="ignore").splitlines():
            m = pat.match(line.strip())
            if m: ev.append((m.group(1), m.group(2), m.group(3)))
    if not ev: return False
    ts, kind, rest = sorted(ev)[-1]
    return kind == "DONE" and re.search(r"(^| )rc=0\b", rest) is not None

def main():
    args = [a for a in sys.argv[1:] if a != "--dry"]; dry = "--dry" in sys.argv
    name = args[0]; rest = args[1:]
    if not (rest == [] or (len(rest) == 2 and rest[0] == "--device")):
        raise SystemExit("only --device N is allowed (imgsz 960 and no --force are fixed)")
    if "ABORTED" in name:
        raise SystemExit("aborted runs are never evaluated")
    cell, seed = parse_run(name)
    out = EXP / "eval/factorial_v3_freeze" / name
    if dry:
        print(json.dumps({"run": name, "cell": cell, "seed": seed, "finished": finished(name), "out": str(out),
                          "already_evaluated": (out / "metrics_unified.json").exists()})); return
    if not finished(name):
        raise SystemExit(f"no 'DONE {name} rc=0' line in the chain logs")
    if (out / "metrics_unified.json").exists():
        raise SystemExit(f"already evaluated, not repeated: {out}")
    import os
    out.mkdir(parents=True, exist_ok=True)
    try:
        os.close(os.open(out / ".eval_lock", os.O_CREAT | os.O_EXCL))
    except FileExistsError:
        raise SystemExit(f"an evaluation of this run was already started: {out}/.eval_lock")
    import factorial_freeze_eval as F
    F.parse_run = parse_run
    cap = {}
    orig = F.base.unified_for_pred
    def wrapped(*a, **k):
        u = orig(*a, **k); cap["method"] = (u.get("coco") or {}).get("method"); return u
    F.base.unified_for_pred = wrapped
    sys.argv = [sys.argv[0]] + args
    F.main()
    import torch, ultralytics, numpy, pycocotools
    env = {"run": name, "utc": datetime.datetime.utcnow().isoformat() + "Z", "host": socket.gethostname(),
           "python": platform.python_version(), "torch": torch.__version__, "ultralytics": ultralytics.__version__,
           "numpy": numpy.__version__, "pycocotools": getattr(pycocotools, "__version__", "?"),
           "coco_method": cap.get("method"), "argv": args,
           "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "wrapper_sha256": sha(__file__), "evaluator_sha256": sha(EXP / "factorial_v3/factorial_freeze_eval.py"),
           "phase2b_common_sha256": sha(ROOT / "tools/ccad/phase2b_common.py"),
           "phase4c_sha256": sha(ROOT / "tools/ccad/phase4c_select_and_freeze_c0r.py"),
           "gt_sha256": sha(out / "val_gt_coco.json"), "predictions_coco_sha256": sha(out / "predictions_coco.json")}
    (out / "eval_env.json").write_text(json.dumps(env, indent=1))

if __name__ == "__main__":
    main()
