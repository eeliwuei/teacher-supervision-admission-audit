#!/usr/bin/env python3
"""Addendum 01 A5 sensitivity: score the trainer's best.pt of a finished kais_v4 / kaisv4mech run with the same
unified scoring as the endpoint (val, imgsz 960, save_json, unified_for_pred). Sensitivity only; never an endpoint.
Writes eval/kaisv4_bestpt/<run>/metrics_unified_best.json with checkpoint provenance (epoch inferred from results.csv under two
candidate fitness definitions; sha256 of best.pt and last.pt).
Requires the endpoint evaluation of the run to exist already. One evaluation per run. H100, envs/ccad_yolo26n.
Usage: eval_kaisv4_best.py <run_name> [--device N] [--dry]"""
import sys, json, csv, os
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_kaisv4 as W
EXP = W.EXP
def best_epoch(run_dir):
    rows = list(csv.DictReader(open(run_dir / "results.csv")))
    k = {c.strip(): c for c in rows[0]}
    m50 = [float(r[k["metrics/mAP50(B)"]]) for r in rows]; m95 = [float(r[k["metrics/mAP50-95(B)"]]) for r in rows]
    def arg(f): return int(float(rows[max(range(len(f)), key=lambda j: (f[j], -j))][k["epoch"]]))
    return {"n_epochs": len(rows), "epoch_argmax_0.1mAP50+0.9mAP50-95": arg([0.1 * x + 0.9 * y for x, y in zip(m50, m95)]),
            "epoch_argmax_mAP50-95": arg(m95),
            "note": "inferred from results.csv (first maximum); the stripped best.pt does not store its epoch, and the "
                    "trainer's fitness definition was not verified in the library source"}
def main():
    args = [a for a in sys.argv[1:] if a != "--dry"]; dry = "--dry" in sys.argv
    name = args[0]; rest = args[1:]
    if not (rest == [] or (len(rest) == 2 and rest[0] == "--device")): raise SystemExit("only --device N is allowed")
    device = rest[1] if rest else "0"
    if "ABORTED" in name: raise SystemExit("aborted runs are never evaluated")
    W.parse_run(name)
    run_dir = EXP / "models/students" / name; ckpt = run_dir / "weights/best.pt"
    endpoint = EXP / "eval/factorial_v3_freeze" / name / "metrics_unified.json"
    out = EXP / "eval/kaisv4_bestpt" / name
    info = {"run": name, "finished": W.finished(name), "endpoint_exists": endpoint.exists(), "best_exists": ckpt.exists(),
            "already": (out / "metrics_unified_best.json").exists(), "selection": best_epoch(run_dir) if (run_dir / "results.csv").exists() else None}
    if dry: print(json.dumps(info)); return
    if not (info["finished"] and info["endpoint_exists"] and info["best_exists"]) or info["already"]:
        raise SystemExit(f"refused: {info}")
    out.mkdir(parents=True, exist_ok=True)
    try: os.close(os.open(out / ".eval_lock", os.O_CREAT | os.O_EXCL))
    except FileExistsError: raise SystemExit("already started")
    import factorial_freeze_eval as F
    cfg = F.load_config(F.CFG)
    gt_path = out / "val_gt_coco.json"; gt_summary = F.write_split_gt_coco(cfg, "val", gt_path, category_base=1)
    data_yaml = Path(cfg["data"]["source_dataset_root"]) / "dataset.yaml"
    with (out / "yolo_val.log").open("w") as log, redirect_stdout(log), redirect_stderr(log):
        from ultralytics import YOLO
        YOLO(str(ckpt)).val(data=str(data_yaml), split="val", imgsz=960, project=str(out.parent), name=out.name,
                            exist_ok=True, plots=False, save_json=True, device=device, verbose=False)
    pred = out / "predictions.json"
    if not pred.exists(): raise SystemExit("no predictions")
    coco = F.base.unified_for_pred(cfg, pred, gt_path, gt_summary, "auto")["coco"]
    CAT = {1: "knife", 2: "gun", 3: "stick"}
    rec = {"run": name, "checkpoint_rule": "trainer best.pt (sensitivity only)", "mAP": coco.get("mAP50-95"),
           "per_class": {CAT[int(r["category_id"])]: r.get("AP50-95") for r in coco.get("per_class") or []},
           "coco_method": coco.get("method"), "selection": info["selection"],
           "best_sha256": W.sha(ckpt), "last_sha256": W.sha(run_dir / "weights/last.pt"),
           "endpoint_mAP_last": json.loads(endpoint.read_text())["mAP"], "gt_sha256": W.sha(gt_path)}
    (out / "metrics_unified_best.json").write_text(json.dumps(rec, indent=1)); print(json.dumps(rec))
if __name__ == "__main__":
    main()
