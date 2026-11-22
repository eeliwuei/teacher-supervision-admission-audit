#!/usr/bin/env python3
"""Protocol sensitivity record on the internal evaluation split (splits/test.txt, 2,553 images; NOT blind): score
last.pt (final EMA) of a run with the unified COCO scoring (imgsz 960, save_json), on all 2,553 images and on the
2,019-image subset (rule of rights_clean_protocol_v1.json: drop basenames starting with hf_w_turki_ds_9_hardneg__).
Sensitivity only; decides nothing. Written 2026-11-14 after the validation endpoints of the primary family were known.
One evaluation per run. Usage: eval_kaisv4_internal.py <run_name> [--device N]
Allowed runs: kais_v4 / kaisv4mech names accepted by eval_kaisv4.py with an existing endpoint, and the two reused
C4-M runs F-MonoSingle_seed{42,1337}_v3factorial_intpad."""
import sys, json, os
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_kaisv4 as W
EXP = W.EXP
REUSED = {"F-MonoSingle_seed42_v3factorial_intpad", "F-MonoSingle_seed1337_v3factorial_intpad"}
PREFIX = "hf_w_turki_ds_9_hardneg__"
def main():
    name = sys.argv[1]; rest = sys.argv[2:]
    if not (rest == [] or (len(rest) == 2 and rest[0] == "--device")): raise SystemExit("only --device N is allowed")
    device = rest[1] if rest else "0"
    if "ABORTED" in name or "INVALID" in name: raise SystemExit("refused")
    if name not in REUSED:
        W.parse_run(name)
        if not W.finished(name): raise SystemExit("not finished")
    if not (EXP / "eval/factorial_v3_freeze" / name / "metrics_unified.json").exists(): raise SystemExit("no endpoint")
    ckpt = EXP / "models/students" / name / "weights/last.pt"
    out = EXP / "eval/kaisv4_internal" / name; out.mkdir(parents=True, exist_ok=True)
    try: os.close(os.open(out / ".eval_lock", os.O_CREAT | os.O_EXCL))
    except FileExistsError: raise SystemExit("already started")
    import factorial_freeze_eval as F
    B = F.base; cfg = F.load_config(F.CFG)
    from phase2b_common import normalize_prediction_rows
    gt_path = out / "test_gt_coco.json"; gs = F.write_split_gt_coco(cfg, "test", gt_path, category_base=1)
    data_yaml = Path(cfg["data"]["source_dataset_root"]) / "dataset.yaml"
    with (out / "yolo_val.log").open("w") as log, redirect_stdout(log), redirect_stderr(log):
        from ultralytics import YOLO
        YOLO(str(ckpt)).val(data=str(data_yaml), split="test", imgsz=960, project=str(out.parent), name=out.name,
                            exist_ok=True, plots=False, save_json=True, device=device, verbose=False)
    pred = out / "predictions.json"
    if not pred.exists(): raise SystemExit("no predictions")
    cat_ids = B.coco_category_ids(cfg)
    rows = normalize_prediction_rows(pred, set(cat_ids), "auto", 0.0, gs.get("image_id_map"))
    pc = out / "predictions_coco.json"; pc.write_text(json.dumps(rows))
    gt = json.loads(gt_path.read_text())
    keep = {im["id"] for im in gt["images"] if not Path(im["file_name"]).name.startswith(PREFIX)}
    if (len(gt["images"]), len(keep)) != (2553, 2019): raise SystemExit(f"count mismatch {len(gt[chr(105)+chr(109)+chr(97)+chr(103)+chr(101)+chr(115)])} {len(keep)}")
    gt2 = dict(gt); gt2["images"] = [im for im in gt["images"] if im["id"] in keep]
    gt2["annotations"] = [a for a in gt["annotations"] if a["image_id"] in keep]
    dropped_ann = len(gt["annotations"]) - len(gt2["annotations"])
    g2 = out / "test_gt_coco_2019.json"; g2.write_text(json.dumps(gt2))
    p2 = out / "predictions_coco_2019.json"; p2.write_text(json.dumps([r for r in rows if r["image_id"] in keep]))
    with (out / "coco.log").open("w") as log, redirect_stdout(log), redirect_stderr(log):
        c_all = B.evaluate_coco(gt_path, pc, cat_ids); c_sub = B.evaluate_coco(g2, p2, cat_ids)
    rec = {"run": name, "split": "internal evaluation split (test.txt), not blind", "checkpoint": "last.pt",
           "mAP_2553": c_all.get("mAP50-95"), "mAP_2019": c_sub.get("mAP50-95"), "coco_method": c_all.get("method"),
           "images": len(gt["images"]), "retained": len(keep), "dropped_annotations": dropped_ann,
           "last_sha256": W.sha(ckpt), "gt_sha256": W.sha(gt_path)}
    (out / "metrics_internal.json").write_text(json.dumps(rec, indent=1)); print(json.dumps(rec))
if __name__ == "__main__":
    main()
