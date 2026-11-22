#!/usr/bin/env python3
"""Addendum 04: image-resampling of fixed trained models (per-model draws).

Usage: bootstrap_a04.py verify|full <out_dir> <eval_dir> [<eval_dir> ...]
Each eval_dir holds predictions_coco.json, val_gt_coco.json, metrics_unified.json written by the unified
evaluation that produced the endpoint. No model is loaded. Reference library: pycocotools COCOeval, catIds
[1,2,3], default params (as phase2b_common.evaluate_coco calls it).
verify: checks (a) identity, (b) rows 0..19 against the reference on explicitly written resampled JSON, and
        the duplicate-count acceptance test. full: verify, then all 2,000 draws -> <out>/<run>.draws.npy
        (columns: mAP50-95, AP knife, AP gun, AP stick; NaN = undefined).
"""
import sys, json, hashlib, io, os, tempfile
from contextlib import redirect_stdout
from pathlib import Path
import numpy as np
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
import pycocotools

N_IMG, B = 2827, 2000
SEED = int.from_bytes(hashlib.sha256(b"LPCCAD-KAISV4-A04").digest()[:8], "big")
IDX_SHA = "246e90b9e083a0dd9f6ca230687679e26b95aeb25564337c1707aea626fa6e34"
CAT_IDS = [1, 2, 3]
TOL = 1e-9

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def index_array():
    idx = np.random.default_rng(SEED).integers(0, N_IMG, size=(B, N_IMG), dtype=np.int64)
    got = hashlib.sha256(idx.astype("<i8").tobytes()).hexdigest()
    if got != IDX_SHA:
        raise SystemExit(f"index array digest mismatch: {got}")
    return idx

def scores(ev):
    """mAP50-95 exactly as COCOeval.summarize stats[0]; per-class AP as evaluate_coco."""
    pr = ev.eval["precision"]  # T,R,K,A,M
    a = [i for i, r in enumerate(ev.params.areaRngLbl) if r == "all"][0]
    m = [i for i, d in enumerate(ev.params.maxDets) if d == 100][0]
    s = pr[:, :, :, a, m]
    out = [float(np.mean(s[s > -1])) if (s > -1).any() else float("nan")]
    for k in range(len(CAT_IDS)):
        p = pr[:, :, k, a, m]; p = p[p > -1]
        out.append(float(np.mean(p)) if p.size else float("nan"))
    if any(np.isnan(v) for v in out[1:]):
        out[0] = float("nan")  # a class without valid precision: draw undefined for mAP
    return out

def reference_eval(gt, dt_rows):
    """Full reference COCOeval on in-memory dicts (written to JSON files first)."""
    with tempfile.TemporaryDirectory() as td:
        g = Path(td) / "gt.json"; d = Path(td) / "dt.json"
        g.write_text(json.dumps(gt)); d.write_text(json.dumps(dt_rows))
        with redirect_stdout(io.StringIO()):
            cg = COCO(str(g)); cd = cg.loadRes(str(d))
            ev = COCOeval(cg, cd, "bbox"); ev.params.catIds = CAT_IDS
            ev.evaluate(); ev.accumulate(); ev.summarize()
    return ev

class Model:
    def __init__(self, eval_dir):
        self.dir = Path(eval_dir); self.name = self.dir.name
        self.gt_path = self.dir / "val_gt_coco.json"; self.dt_path = self.dir / "predictions_coco.json"
        self.gt = json.loads(self.gt_path.read_text()); self.dt = json.loads(self.dt_path.read_text())
        self.rec = json.loads((self.dir / "metrics_unified.json").read_text())
        self.img_ids = [im["id"] for im in self.gt["images"]]          # file order = index order of Addendum 04
        if len(self.img_ids) != N_IMG or len(set(self.img_ids)) != N_IMG:
            raise SystemExit(f"{self.name}: expected {N_IMG} distinct images")
        self.img_by_id = {im["id"]: im for im in self.gt["images"]}
        self.gt_by_img = {}; self.dt_by_img = {}
        for a in self.gt["annotations"]: self.gt_by_img.setdefault(a["image_id"], []).append(a)
        for r in self.dt: self.dt_by_img.setdefault(r["image_id"], []).append(r)   # keeps file order
        with redirect_stdout(io.StringIO()):
            cg = COCO(str(self.gt_path)); cd = cg.loadRes(str(self.dt_path))
            ev = COCOeval(cg, cd, "bbox"); ev.params.catIds = CAT_IDS
            ev.params.imgIds = list(self.img_ids)   # COCOeval sorts and uniques these itself
            ev.evaluate()
        self.ev = ev
        p = ev.params
        self.K, self.A, self.I = len(p.catIds), len(p.areaRng), len(p.imgIds)
        self.pos = {iid: n for n, iid in enumerate(p.imgIds)}            # position inside evalImgs
        self.base_evalImgs = ev.evalImgs
        self.base_imgIds = list(p.imgIds)

    def fast(self, row):
        """Accumulate on the resampled image list, reusing per-image matching. row: indices into gt['images']."""
        srt = np.sort(np.asarray(row))
        posn = [self.pos[self.img_ids[i]] for i in srt]
        E = self.base_evalImgs; K, A, I = self.K, self.A, self.I
        ev = self.ev
        ev.evalImgs = [E[k * A * I + a * I + q] for k in range(K) for a in range(A) for q in posn]
        ids = list(range(1, len(posn) + 1))
        ev.params.imgIds = ids; ev._paramsEval.imgIds = ids
        with redirect_stdout(io.StringIO()):
            ev.accumulate()
        out = scores(ev)
        ev.evalImgs = E; ev.params.imgIds = list(self.base_imgIds); ev._paramsEval.imgIds = list(self.base_imgIds)
        return out

    def resampled_json(self, row):
        """Explicit relabelled copy: j-th entry of the ascending-sorted draw becomes image id j (1-based)."""
        srt = np.sort(np.asarray(row))
        images, anns, dts = [], [], []; aid = 0
        for j, i in enumerate(srt, start=1):
            iid = self.img_ids[i]; im = dict(self.img_by_id[iid]); im["id"] = j; images.append(im)
            for a in self.gt_by_img.get(iid, []):
                aid += 1; b = dict(a); b["image_id"] = j; b["id"] = aid; anns.append(b)
            for r in self.dt_by_img.get(iid, []):
                b = {k: v for k, v in r.items() if k != "id"}; b["image_id"] = j; dts.append(b)
        gt = {k: v for k, v in self.gt.items() if k not in ("images", "annotations")}
        gt["images"] = images; gt["annotations"] = anns
        return gt, dts

    def verify(self, idx):
        rep = {"run": self.name, "gt_sha256": sha256_file(self.gt_path), "dt_sha256": sha256_file(self.dt_path),
               "pycocotools": getattr(pycocotools, "__version__", "?"), "numpy": np.__version__}
        want = [self.rec["mAP"]] + [self.rec["per_class"][c] for c in ("knife", "gun", "stick")]
        ident = self.fast(np.arange(N_IMG))
        da = np.abs(np.array(ident, float) - np.array(want, float))
        rep["a_identity_maxabs"] = float("inf") if np.isnan(da).any() else float(da.max())
        ref_id = scores(reference_eval(*self.resampled_json(np.arange(N_IMG))))
        dr = np.abs(np.array(ref_id, float) - np.array(want, float))
        rep["a_identity_reference_maxabs"] = float("inf") if np.isnan(dr).any() else float(dr.max())
        worst = 0.0; dup = []
        for b in range(20):
            gt, dts = self.resampled_json(idx[b])
            ev = reference_eval(gt, dts)
            ref = scores(ev); fst = self.fast(idx[b])
            if np.isnan(ref).tolist() != np.isnan(fst).tolist():
                worst = float("inf")
            else:
                worst = max(worst, float(np.nanmax(np.abs(np.array(ref) - np.array(fst)))) if not np.all(np.isnan(ref)) else 0.0)
            # duplicate-count acceptance: the reference really scores 2,827 images, repeats included
            cnt = np.bincount(idx[b], minlength=N_IMG)
            exp_gt = sum(int(c) * len(self.gt_by_img.get(self.img_ids[i], [])) for i, c in enumerate(cnt))
            exp_dt = sum(int(c) * len(self.dt_by_img.get(self.img_ids[i], [])) for i, c in enumerate(cnt))
            ok = (len(ev.params.imgIds) == N_IMG and len(gt["annotations"]) == exp_gt and len(dts) == exp_dt
                  and len(ev.cocoGt.getAnnIds()) == exp_gt and len(ev.cocoDt.getAnnIds()) == exp_dt)
            dup.append({"draw": b, "distinct_source_images": int((cnt > 0).sum()), "max_multiplicity": int(cnt.max()),
                        "images_scored": len(ev.params.imgIds), "gt_scored": len(ev.cocoGt.getAnnIds()),
                        "gt_expected_with_multiplicity": exp_gt, "dt_scored": len(ev.cocoDt.getAnnIds()),
                        "dt_expected_with_multiplicity": exp_dt, "ok": bool(ok)})
        rep["b_rows0_19_maxabs"] = worst
        rep["duplicates_counted"] = all(d["ok"] for d in dup)
        rep["duplicate_checks"] = dup
        # negative control: scoring only the distinct images of draw 0 (i.e. de-duplicating) must differ
        cnt0 = np.bincount(idx[0], minlength=N_IMG); uniq = np.nonzero(cnt0)[0]
        g2, d2 = self.resampled_json(uniq); dd = scores(reference_eval(g2, d2))
        rep["negctl_dedup_draw0_mAP"] = dd[0]; rep["draw0_mAP"] = self.fast(idx[0])[0]
        rep["negctl_differs"] = abs(dd[0] - rep["draw0_mAP"]) > TOL
        rep["pass"] = bool(rep["a_identity_maxabs"] <= TOL and worst <= TOL and rep["duplicates_counted"])
        # Addendum 04 step 4: if the fast path fails, every draw is computed with the reference library instead
        rep["reference_path_ok"] = bool(rep["a_identity_reference_maxabs"] <= TOL and rep["duplicates_counted"])
        return rep

def main():
    mode, out = sys.argv[1], Path(sys.argv[2]); dirs = sys.argv[3:]
    out.mkdir(parents=True, exist_ok=True)
    idx = index_array()
    for d in dirs:
        m = Model(d); rep = m.verify(idx)
        (out / f"{m.name}.verify.json").write_text(json.dumps(rep, indent=1))
        print(m.name, "pass" if rep["pass"] else "FAIL", "a=%.2e b=%.2e dup=%s negctl_differs=%s" % (
            rep["a_identity_maxabs"], rep["b_rows0_19_maxabs"], rep["duplicates_counted"], rep["negctl_differs"]), flush=True)
        if mode == "full":
            if rep["pass"]:
                arr = np.array([m.fast(idx[b]) for b in range(B)], dtype=np.float64); how = "fast"
            elif rep["reference_path_ok"]:
                print(m.name, "fast path failed verification: all draws with the reference library (disclose)", flush=True)
                arr = np.array([scores(reference_eval(*m.resampled_json(idx[b]))) for b in range(B)], dtype=np.float64); how = "reference"
            else:
                print(m.name, "no draws written (verification failed)"); continue
            rep["draws_computed_with"] = how
            (out / f"{m.name}.verify.json").write_text(json.dumps(rep, indent=1))
            np.save(out / f"{m.name}.draws.npy", arr)

if __name__ == "__main__":
    main()
