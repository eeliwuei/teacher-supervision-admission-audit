#!/usr/bin/env python3
"""Run-time audit of the LP-CCAD label-space admission gate (CPU only, read-only).

Builds the real training dataloader through the project's own trainer class
(CCADDetectionTrainer.get_dataloader -> build_dataset -> build_yolo_dataset ->
build_dataloader, the path BaseTrainer._setup_train uses), iterates batches,
passes every batch through the trainer's own preprocess_batch (which calls
ccad_dataset_adapter.build_batch_teacher_targets, i.e. the gate), and writes one
CSV row per eligible evidence row whose image appeared.

Nothing of the gate is reimplemented: admitted/not comes from
build_batch_teacher_targets(...)["has_box"/"gt_uid"]; the IoU column is computed
with the adapter's own xyxy_to_xywh_norm and xywh_iou on the batch tensors.

The only instrumentation is a pass-through wrapper around
LetterBox._update_labels that copies (left, top) and the pre-letterbox image
shape into two extra label keys; it does not change any value the pipeline
computes. save_dataset_cache_file is replaced by a function that raises, so this
process can never rewrite the dataset label cache.

No model is built, no GPU is used, trainer.train() is never called.
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
import argparse, csv, hashlib, json, sys, time
from pathlib import Path

ROOT = "/deepet/police_ai_video"
E = ROOT + "/experiments/ccad_yolo26n"
OUTDIR = E + "/kais_v4/audit_out/runtime_gate"
BANK = E + "/label_banks/evidence/selected_best_stg1_v2/evidence_bank.jsonl"
BANK_SHA256 = "eca4969b5586a41feae1c79ac6cda1efe29d9b5929b2f309b1d4f155434b9cbc"
DATA = ROOT + "/00_data/weapon_detection_ccad_v2/dataset.yaml"

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--max-batches", type=int, default=0)
ap.add_argument("--workers", type=int, default=0)
ap.add_argument("--tag", required=True)
a = ap.parse_args()

os.chdir(ROOT)
sys.path.insert(0, ROOT + "/tools/ccad")
import torch
torch.set_num_threads(4)
assert not torch.cuda.is_available()

import ultralytics
import ultralytics.data.dataset as uds
from ultralytics.data.augment import LetterBox


def _no_cache_write(*args, **kw):
    raise RuntimeError("audit: refusing to write dataset label cache")
uds.save_dataset_cache_file = _no_cache_write

_orig_update = LetterBox._update_labels
def _update_labels(labels, ratio, padw, padh):
    out = _orig_update(labels, ratio, padw, padh)
    out["audit_pad_lt"] = (int(padw), int(padh))
    out["audit_lb_in_hw"] = tuple(int(v) for v in labels["img"].shape[:2])
    out["audit_lb_ratio"] = (float(ratio[0]), float(ratio[1]))
    return out
LetterBox._update_labels = staticmethod(_update_labels)

import ccad_dataset_adapter as ada
from ccad_detection_trainer import CCADDetectionTrainer


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

assert sha256_file(BANK) == BANK_SHA256, "bank sha mismatch"

# row ids exactly as padding_row_audit.py (same filter as CCADEvidenceIndex)
rowid = {}
n_elig = 0
with open(BANK, encoding="utf-8") as f:
    for ln, line in enumerate(f, 1):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("evidence_type") != "E1_matched_refinement":
            continue
        if not r.get("box_kd_allowed", r.get("e1_box_eligible", False)):
            continue
        n_elig += 1
        k = (str(r["image_id"]), int(r["query_id"]), int(r["matched_gt_id"]))
        assert k not in rowid, k
        rowid[k] = "L%06d:%s:q%d:g%d" % (ln, r["image_id"], int(r["query_id"]), int(r["matched_gt_id"]))

# same overrides as tools/ccad/train_yolo26_ccad_stockloop.py::run, except
# device (cpu), project/name (audit dir), amp (no model here).
overrides = {
    "model": "yolo26n.pt", "data": DATA, "epochs": 150, "imgsz": 960, "batch": 16,
    "device": "cpu", "workers": a.workers,
    "project": OUTDIR, "name": "trainer_scratch_" + a.tag, "exist_ok": True,
    "amp": False, "seed": a.seed, "deterministic": True,
    "mosaic": 0, "close_mosaic": 0, "mixup": 0, "copy_paste": 0, "cutmix": 0,
    "degrees": 0, "translate": 0, "scale": 0, "shear": 0, "perspective": 0,
    "fliplr": 0, "flipud": 0, "erasing": 0, "multi_scale": 0,
    "save": True, "save_period": 5, "val": True, "plots": False, "verbose": False,
    "fraction": 1.0,
}
trainer = CCADDetectionTrainer(overrides=overrides, evidence_bank=BANK, schedule="full",
                               lambda_box=0.05, lambda_cls=0.05, ccad_enabled=True)
assert trainer.device.type == "cpu"
assert trainer.evidence.e1_box == n_elig, (trainer.evidence.e1_box, n_elig)
# build_dataset only reads model.stride.max() (-> gs=32; YOLO26n strides are 8/16/32).
# No model is loaded here; a stub Module carrying the stride stands in for it.
class _StrideStub(torch.nn.Module):
    stride = torch.tensor([8.0, 16.0, 32.0])
trainer.model = _StrideStub()
loader = trainer.get_dataloader(trainer.data["train"], batch_size=trainer.batch_size, rank=-1, mode="train")
ds = loader.dataset
meta = {
    "tag": a.tag, "seed": a.seed, "workers_requested": a.workers, "workers_effective": loader.num_workers,
    "ultralytics": ultralytics.__version__, "torch": torch.__version__,
    "n_images": len(ds), "n_batches": len(loader), "batch_size": trainer.batch_size,
    "eligible_rows_in_bank": n_elig, "dataset_transforms": repr(ds.transforms)[:4000],
    "augment": bool(ds.augment), "rect": bool(ds.rect), "imgsz": ds.imgsz,
    "adapter_sha256": sha256_file(ROOT + "/tools/ccad/ccad_dataset_adapter.py"),
    "trainer_sha256": sha256_file(ROOT + "/tools/ccad/ccad_detection_trainer.py"),
    "iou_match_thr_default": ada.build_batch_teacher_targets.__defaults__,
    "batch_keys": None,
}

FIELDS = ["row_id", "pass_tag", "seed", "batch_i", "im_file", "class", "class_id",
          "ori_h", "ori_w", "bank_h", "bank_w", "resized_h", "resized_w",
          "lb_in_h", "lb_in_w", "pad_left", "pad_top", "pad_total_x", "pad_total_y",
          "n_labels_img", "n_same_cls_labels", "n_candidates_same_cls",
          "admitted", "has_cls", "gate_iou", "best_iou_any_label",
          "batch_cx", "batch_cy", "batch_w", "batch_h",
          "adapter_cx", "adapter_cy", "adapter_w", "adapter_h",
          "d_x1_px", "d_y1_px", "d_x2_px", "d_y2_px", "img_sum"]
out_csv = "%s/runtime_gate_rows_%s.csv" % (OUTDIR, a.tag)
t0 = time.time()
n_img = n_lab = 0
tot_has_box = tot_has_cls = 0
uid_kinds = {"no_teacher": 0, "unmatched": 0, "matched": 0}
with open(out_csv, "w", newline="", encoding="utf-8") as g:
    wr = csv.DictWriter(g, fieldnames=FIELDS, lineterminator="\n")
    wr.writeheader()
    for bi_, batch in enumerate(loader):
        if a.max_batches and bi_ >= a.max_batches:
            break
        if meta["batch_keys"] is None:
            meta["batch_keys"] = sorted(batch.keys())
            meta["has_ratio_pad_key"] = "ratio_pad" in batch
        batch = trainer.preprocess_batch(batch)   # real gate call happens here
        tt = batch["ccad_teacher_targets"]
        nb = int(batch["img"].shape[0])
        n_img += nb
        bidx = batch["batch_idx"].long().tolist()
        cls = batch["cls"].view(-1).long().tolist()
        bboxes = batch["bboxes"].float()
        n_lab += len(cls)
        tot_has_box += int(tt["has_box"].sum()); tot_has_cls += int(tt["has_cls"].sum())
        assert tuple(batch["img"].shape[-2:]) == (960, 960), batch["img"].shape
        # gate outcome per label
        admitted = {}   # (im index, matched_gt_id, query_id) -> label_i
        for li, uid in enumerate(tt["gt_uid"]):
            stem, x, y = uid.rsplit(":", 2)
            if y in ("no_teacher", "unmatched"):
                uid_kinds[y] += 1
                continue
            uid_kinds["matched"] += 1
            assert bool(tt["has_box"][li])
            admitted[(bidx[li], int(x), int(y))] = li
        used = set()
        for im_i in range(nb):
            im_file = batch["im_file"][im_i]
            ori = batch["ori_shape"][im_i]; rs = batch["resized_shape"][im_i]
            pl, pt = batch["audit_pad_lt"][im_i]; lh, lw = batch["audit_lb_in_hw"][im_i]
            labs = [li for li in range(len(cls)) if bidx[li] == im_i]
            img_sum = float(batch["img"][im_i].double().sum())
            rows = trainer.evidence.for_image(im_file)
            for r in rows:
                k = (str(r["image_id"]), int(r["query_id"]), int(r["matched_gt_id"]))
                c = int(r.get("matched_gt_class_id", -1))
                tg = torch.tensor(ada.xyxy_to_xywh_norm(r["matched_gt_bbox"], ori, rs), dtype=torch.float32).unsqueeze(0)
                same = [li for li in labs if cls[li] == c]
                ious = {li: float(ada.xywh_iou(bboxes[li].unsqueeze(0), tg)[0]) for li in labs}
                akey = (im_i, int(r["matched_gt_id"]), int(r["query_id"]))
                li_adm = admitted.get(akey)
                if li_adm is not None:
                    used.add(akey)
                    li_ref = li_adm
                else:
                    li_ref = max(same, key=lambda li: ious[li]) if same else None
                rec = {"row_id": rowid[k], "pass_tag": a.tag, "seed": a.seed, "batch_i": bi_, "im_file": im_file,
                       "class": r.get("matched_gt_class"), "class_id": c,
                       "ori_h": int(ori[0]), "ori_w": int(ori[1]),
                       "bank_h": r.get("image_height"), "bank_w": r.get("image_width"),
                       "resized_h": int(rs[0]), "resized_w": int(rs[1]),
                       "lb_in_h": lh, "lb_in_w": lw, "pad_left": pl, "pad_top": pt,
                       "pad_total_x": int(rs[1]) - lw, "pad_total_y": int(rs[0]) - lh,
                       "n_labels_img": len(labs), "n_same_cls_labels": len(same),
                       "n_candidates_same_cls": sum(1 for q in rows if int(q.get("matched_gt_class_id", -1)) == c),
                       "admitted": int(li_adm is not None),
                       "has_cls": int(bool(tt["has_cls"][li_adm])) if li_adm is not None else 0,
                       "gate_iou": repr(ious[li_ref]) if li_ref is not None else "",
                       "best_iou_any_label": repr(max(ious.values())) if ious else "",
                       "img_sum": repr(img_sum)}
                if li_ref is not None:
                    b = bboxes[li_ref].tolist(); t = tg[0].tolist()
                    rec.update(batch_cx=repr(b[0]), batch_cy=repr(b[1]), batch_w=repr(b[2]), batch_h=repr(b[3]),
                               adapter_cx=repr(t[0]), adapter_cy=repr(t[1]), adapter_w=repr(t[2]), adapter_h=repr(t[3]))
                    W, H = float(rs[1]), float(rs[0])
                    rec.update(d_x1_px="%.4f" % (((t[0] - t[2] / 2) - (b[0] - b[2] / 2)) * W),
                               d_y1_px="%.4f" % (((t[1] - t[3] / 2) - (b[1] - b[3] / 2)) * H),
                               d_x2_px="%.4f" % (((t[0] + t[2] / 2) - (b[0] + b[2] / 2)) * W),
                               d_y2_px="%.4f" % (((t[1] + t[3] / 2) - (b[1] + b[3] / 2)) * H))
                wr.writerow(rec)
        assert used == set(admitted), "admitted label not attributed to an evidence row"
        if bi_ % 50 == 0:
            g.flush()
            print("batch %d/%d images %d labels %d has_box %d elapsed %.0fs" % (bi_, len(loader), n_img, n_lab, tot_has_box, time.time() - t0), flush=True)
meta.update(images_iterated=n_img, labels_iterated=n_lab, sum_has_box=tot_has_box, sum_has_cls=tot_has_cls,
            gt_uid_kinds=uid_kinds, elapsed_s=round(time.time() - t0, 1), out_csv=out_csv)
with open("%s/runtime_gate_meta_%s.json" % (OUTDIR, a.tag), "w") as f:
    json.dump(meta, f, indent=2, default=str)
print(json.dumps(meta, indent=2, default=str))
print("DONE")
