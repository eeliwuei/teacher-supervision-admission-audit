#!/usr/bin/env python3
"""Recompute the endpoint values of the 46 evaluation directories from the per-image predictions.

What it does
  For each run it reads as_filed/eval/factorial_v3_freeze/<run>/predictions.json (one row per detection),
  maps every row to the integer image id of the validation ground truth, scores the rows with the COCO
  evaluator, and compares mAP50-95, AP50, AP75 and the per-class values with the filed values in
  scrubbed/eval/factorial_v3_freeze/<run>/metrics_unified.json. It prints a line per run, writes a table
  (--out), and ends with the maximum absolute difference and PASS or FAIL.

Inputs
  --or10 DIR      the extracted Online Resource 10 (the folder S8_File that holds gt/ and scripts/).
  --evidence DIR  this bundle (default: the folder above tools/).
  --mode full     uses DIR/gt/val_gt_coco_full.json (2,827 images, 2,151 boxes).
  --mode public   uses DIR/gt/val_gt_coco_public.json (2,827 images, 2,064 boxes).

Ground truth
  The validation ground truth is not in this bundle. Online Resource 10 holds it without the 87 boxes that
  belong to 86 of the 87 listed images of two sources with restricted annotations (one listed image has no
  box, one has two). scripts/rebuild_provider_gt.py of Online
  Resource 10 rebuilds these boxes from the providers' own annotation files and writes
  gt/val_gt_coco_full.json; run it before --mode full. The providers' files are not included in either
  archive. In public mode the 87 boxes are missing, so the values differ from the filed ones and no
  PASS/FAIL is given.

Image-id mapping
  A prediction row carries "file_name" (for example "x.jpg") and "image_id" (the same name without the
  extension, a string). The ground truth of Online Resource 10 gives each image an integer "id" and the
  same "file_name". Each row is mapped through file_name to the integer id. A row whose file_name is not in
  the ground truth, or whose category_id is not a ground-truth category, stops the program (exit status 2).

Evaluation settings (those of the filed evaluation, as bootstrap_a04.py states them)
  COCOeval, iouType "bbox", catIds [1, 2, 3] (knife, gun, stick), all other parameters at their defaults:
  IoU thresholds 0.50:0.05:0.95, 101 recall thresholds, maxDets [1, 10, 100], area ranges all / small /
  medium / large, all 2,827 images scored (images without boxes and images without predictions included).
  mAP, mAP50, mAP75 = stats[0], stats[1], stats[2]. Per-class AP = mean of precision[:, :, k, all, 100]
  over the entries greater than -1; per-class AP50 = the same at IoU 0.50. All rows of predictions.json
  are used; no score threshold or per-image cap is applied here.

Optional: image-resampling draws (--draws N)
  Loads the filed as_filed/kais_v4/analysis/bootstrap_a04.py unchanged (as a module), gives it a temporary
  evaluation directory with the id-mapped predictions and the ground truth, recomputes N of the 2,000 draws
  with its own functions and compares them with the filed rows of a04_draws/<run>.draws.npy. Full mode only.
  The filed script sorts the image indices of a draw in ascending order before scoring. No bytecode file is
  written into the bundle while the filed script is loaded.

Optional: evaluation directories for the filed script (--export-view DIR)
  Writes DIR/<run>/predictions_coco.json (the id-mapped rows), val_gt_coco.json (a copy of the ground truth)
  and metrics_unified.json for the runs of --draw-runs, so that bootstrap_a04.py can be started as its usage
  line says, for example: python3 as_filed/kais_v4/analysis/bootstrap_a04.py verify OUT DIR/<run>.
  These files hold ground-truth boxes; do not redistribute them. Full mode only.

Number of runs
  The bundle holds 46 evaluation directories; a full run compares 414 values. If another number of
  directories is found, the tool prints a NOTE line and the result covers only the directories found.

Exit status: 0 PASS (or public mode finished), 1 FAIL (a difference above the tolerance), 2 cannot run.
Requires: Python 3, numpy, pycocotools (the evaluator of the filed evaluation). --evaluator faster-coco-eval
uses that library instead if it is installed.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import math
import os
import shutil
import sys
import tempfile

TOL = 1e-9
CAT_IDS = [1, 2, 3]
CAT_NAMES = {1: "knife", 2: "gun", 3: "stick"}
EVAL_REL = os.path.join("eval", "factorial_v3_freeze")
N_RUNS = 46
QUANTITIES = ["mAP", "mAP50", "mAP75", "AP_knife", "AP_gun", "AP_stick", "AP50_knife", "AP50_gun", "AP50_stick"]


def cannot_run(msg):
    print("ERROR: " + msg)
    sys.exit(2)


def load_evaluator(name):
    import numpy
    if name == "pycocotools":
        import pycocotools
        from pycocotools.coco import COCO
        from pycocotools.cocoeval import COCOeval as Eval
        mod, dist = pycocotools, "pycocotools"
    else:
        import faster_coco_eval
        from faster_coco_eval import COCO
        from faster_coco_eval import COCOeval_faster as Eval
        mod, dist = faster_coco_eval, "faster-coco-eval"
    ver = getattr(mod, "__version__", None)
    if not ver:
        try:
            from importlib.metadata import version
            ver = version(dist)
        except Exception:
            ver = "?"
    return COCO, Eval, "%s %s, numpy %s, Python %s" % (dist, ver, numpy.__version__, sys.version.split()[0])


def map_predictions(rows, id_by_name, cat_ids, run):
    """Rows of predictions.json -> COCO result rows with the integer image ids of the ground truth."""
    out = []
    for n, r in enumerate(rows):
        fn = r.get("file_name")
        if fn not in id_by_name:
            cannot_run("%s: row %d: file_name %r is not an image of the ground truth" % (run, n, fn))
        if r.get("category_id") not in cat_ids:
            cannot_run("%s: row %d: category_id %r is not a ground-truth category" % (run, n, r.get("category_id")))
        out.append({"image_id": id_by_name[fn], "category_id": r["category_id"],
                    "bbox": r["bbox"], "score": r["score"]})
    return out


def filed_values(rec):
    v = {"mAP": rec["mAP"], "mAP50": rec["mAP50"], "mAP75": rec["mAP75"]}
    for c in CAT_IDS:
        v["AP_" + CAT_NAMES[c]] = rec["per_class"][CAT_NAMES[c]]
        v["AP50_" + CAT_NAMES[c]] = rec["per_class_ap50"][CAT_NAMES[c]]
    return v


def evaluate(coco_gt, Eval, dt_rows):
    import numpy as np
    with contextlib.redirect_stdout(io.StringIO()):
        cd = coco_gt.loadRes(dt_rows)
        ev = Eval(coco_gt, cd, "bbox")
        ev.params.catIds = list(CAT_IDS)
        ev.evaluate()
        ev.accumulate()
        ev.summarize()
    p = ev.params
    if len(p.imgIds) != len(coco_gt.getImgIds()):
        cannot_run("the evaluator did not score all ground-truth images")
    v = {"mAP": float(ev.stats[0]), "mAP50": float(ev.stats[1]), "mAP75": float(ev.stats[2])}
    pr = ev.eval["precision"]  # IoU threshold, recall threshold, class, area range, maxDets
    a = list(p.areaRngLbl).index("all")
    m = list(p.maxDets).index(100)
    t50 = int(np.argmin(np.abs(np.asarray(p.iouThrs) - 0.5)))
    for k, c in enumerate(CAT_IDS):
        s = pr[:, :, k, a, m]
        s = s[s > -1]
        v["AP_" + CAT_NAMES[c]] = float(np.mean(s)) if s.size else float("nan")
        s = pr[t50, :, k, a, m]
        s = s[s > -1]
        v["AP50_" + CAT_NAMES[c]] = float(np.mean(s)) if s.size else float("nan")
    return v


def pick_draws(n, total):
    import numpy as np
    if n >= total:
        return list(range(total))
    return sorted(set(int(round(x)) for x in np.linspace(0, total - 1, n)))


def write_view(evidence, gt_path, mapped, run, dst):
    """One evaluation directory in the layout bootstrap_a04.py reads."""
    d = os.path.join(dst, run)
    os.makedirs(d)
    shutil.copyfile(gt_path, os.path.join(d, "val_gt_coco.json"))
    shutil.copyfile(os.path.join(evidence, "scrubbed", EVAL_REL, run, "metrics_unified.json"),
                    os.path.join(d, "metrics_unified.json"))
    with open(os.path.join(d, "predictions_coco.json"), "w") as f:
        json.dump(mapped[run], f)
    return d


def check_draws(evidence, gt_path, mapped, runs, n_draws):
    """Recompute n_draws image-resampling draws per run with the filed bootstrap_a04.py; compare with a04_draws/."""
    import numpy as np
    script = os.path.join(evidence, "as_filed", "kais_v4", "analysis", "bootstrap_a04.py")
    draws_dir = os.path.join(evidence, "as_filed", "kais_v4", "analysis", "a04_draws")
    spec = importlib.util.spec_from_file_location("bootstrap_a04_filed", script)
    B = importlib.util.module_from_spec(spec)
    old_flag = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # no __pycache__ in the bundle: the manifest check reports unlisted files
    try:
        spec.loader.exec_module(B)
    finally:
        sys.dont_write_bytecode = old_flag
    idx = B.index_array()  # the filed script checks the digest of the index array itself
    picks = pick_draws(n_draws, B.B)
    worst, lines, bad = 0.0, [], 0
    tmp = tempfile.mkdtemp(prefix="recompute_map_")
    try:
        for run in runs:
            d = write_view(evidence, gt_path, mapped, run, tmp)
            filed = np.load(os.path.join(draws_dir, run + ".draws.npy"))
            if filed.shape != (B.B, 4):
                cannot_run("%s: unexpected shape of the filed draws %s" % (run, filed.shape))
            m = B.Model(d)
            ident = np.array(m.fast(np.arange(B.N_IMG)), float)
            want = np.array([m.rec["mAP"]] + [m.rec["per_class"][c] for c in ("knife", "gun", "stick")], float)
            d_id = float(np.max(np.abs(ident - want)))
            got = np.array([m.fast(idx[b]) for b in picks], float)
            ref = filed[picks]
            same_nan = bool((np.isnan(got) == np.isnan(ref)).all())
            diff = np.abs(got - ref)
            d_dr = float(np.nanmax(diff)) if not np.isnan(diff).all() else 0.0
            ok = same_nan and d_dr <= TOL and d_id <= TOL
            bad += (not ok)
            worst = max(worst, d_dr, d_id)
            lines.append("%-44s draws %d  identity %.2e  max|recomputed - filed| %.2e  undefined entries %d%s"
                         % (run, len(picks), d_id, d_dr, int(np.isnan(ref).sum()), "" if ok else "  <- DIFFERS"))
            shutil.rmtree(d)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return picks, lines, worst, bad


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Recompute mAP of the 46 runs from predictions.json and the "
                                             "ground truth of Online Resource 10.")
    ap.add_argument("--or10", required=True, help="extracted Online Resource 10 (folder S8_File)")
    ap.add_argument("--evidence", default=os.path.dirname(here), help="this bundle (default: folder above tools/)")
    ap.add_argument("--mode", choices=["full", "public"], default="full")
    ap.add_argument("--evaluator", choices=["pycocotools", "faster-coco-eval"], default="pycocotools")
    ap.add_argument("--out", default=None, help="write the table to this file (tab-separated)")
    ap.add_argument("--draws", type=int, default=0, help="also recompute this many image-resampling draws per run")
    ap.add_argument("--draw-runs", default="all", help="comma-separated run names for --draws (default: all)")
    ap.add_argument("--export-view", default=None, metavar="DIR",
                    help="write evaluation directories for bootstrap_a04.py into DIR (runs of --draw-runs)")
    a = ap.parse_args()

    gt_path = os.path.join(a.or10, "gt", "val_gt_coco_%s.json" % a.mode)
    if not os.path.exists(gt_path):
        cannot_run("gt/val_gt_coco_%s.json not found in --or10." % a.mode + (
            " Full mode needs the rebuilt ground truth: run scripts/rebuild_provider_gt.py --split val of "
            "Online Resource 10 first." if a.mode == "full" else ""))
    pred_root = os.path.join(a.evidence, "as_filed", EVAL_REL)
    rec_root = os.path.join(a.evidence, "scrubbed", EVAL_REL)
    if not os.path.isdir(pred_root) or not os.path.isdir(rec_root):
        cannot_run("--evidence does not hold as_filed/%s and scrubbed/%s" % (EVAL_REL, EVAL_REL))
    runs = sorted(d for d in os.listdir(pred_root) if os.path.isfile(os.path.join(pred_root, d, "predictions.json")))
    if not runs:
        cannot_run("no predictions.json found")
    for r in runs:
        if not os.path.isfile(os.path.join(rec_root, r, "metrics_unified.json")):
            cannot_run("%s: metrics_unified.json missing" % r)
    try:
        COCO, Eval, versions = load_evaluator(a.evaluator)
    except ImportError as exc:
        cannot_run("evaluator %s is not installed (%s)" % (a.evaluator, exc))

    with open(gt_path) as f:
        gt = json.load(f)
    names = [im["file_name"] for im in gt["images"]]
    if len(set(names)) != len(names):
        cannot_run("file_name is not unique in the ground truth")
    id_by_name = {im["file_name"]: im["id"] for im in gt["images"]}
    gt_cats = sorted(c["id"] for c in gt["categories"])
    if gt_cats != CAT_IDS:
        cannot_run("ground-truth categories are %s, expected %s" % (gt_cats, CAT_IDS))
    with contextlib.redirect_stdout(io.StringIO()):
        cg = COCO()
        cg.dataset = gt
        cg.createIndex()

    head = ["mode %s; ground truth: %d images, %d boxes; %d runs" % (a.mode, len(gt["images"]), len(gt["annotations"]), len(runs)),
            "evaluator: " + versions,
            "settings: bbox, catIds %s, default COCOeval parameters; tolerance %.0e" % (CAT_IDS, TOL)]
    if len(runs) != N_RUNS:
        head.append("NOTE: %d run directories found, %d expected; the result covers only the %d found"
                    % (len(runs), N_RUNS, len(runs)))
    for h in head:
        print(h)
    rows, worst, mapped = [], {q: 0.0 for q in QUANTITIES}, {}
    n_bad = 0
    for run in runs:
        with open(os.path.join(pred_root, run, "predictions.json")) as f:
            dt = map_predictions(json.load(f), id_by_name, set(CAT_IDS), run)
        mapped[run] = dt
        with open(os.path.join(rec_root, run, "metrics_unified.json")) as f:
            filed = filed_values(json.load(f))
        got = evaluate(cg, Eval, dt)
        dmax = 0.0
        for q in QUANTITIES:
            d = abs(got[q] - filed[q])
            if not math.isfinite(d):
                d = float("inf")
            rows.append([run, q, repr(filed[q]), repr(got[q]), "%.3e" % d])
            worst[q] = max(worst[q], d)
            dmax = max(dmax, d)
        n_bad += dmax > TOL
        print("%-44s rows %5d  mAP filed %.6f recomputed %.6f  max|diff| over 9 values %.2e"
              % (run, len(dt), filed["mAP"], got["mAP"], dmax))
    summary = ["max |recomputed - filed| over %d runs: " % len(runs)
               + ", ".join("%s %.2e" % (q, worst[q]) for q in QUANTITIES)]
    overall = max(worst.values())
    status = 0
    if a.mode == "public":
        summary.append("public mode: 87 boxes are missing from the ground truth, so the values differ from the "
                       "filed ones (maximum %.2e); no PASS/FAIL in this mode" % overall)
    elif overall <= TOL:
        summary.append("PASS: maximum absolute difference %.2e <= %.0e (%d values)" % (overall, TOL, len(rows)))
    else:
        summary.append("FAIL: maximum absolute difference %.2e > %.0e (%d of %d runs differ)" % (overall, TOL, n_bad, len(runs)))
        status = 1

    sel = runs if a.draw_runs == "all" else [r for r in a.draw_runs.split(",") if r]
    for r in sel:
        if r not in mapped:
            cannot_run("--draw-runs: unknown run %s" % r)
    if (a.draws > 0 or a.export_view) and a.mode != "full":
        cannot_run("--draws and --export-view need --mode full")
    if a.export_view:
        for r in sel:
            if os.path.exists(os.path.join(a.export_view, r)):
                cannot_run("--export-view: %s already exists there" % r)
        os.makedirs(a.export_view, exist_ok=True)
        for r in sel:
            write_view(a.evidence, gt_path, mapped, r, a.export_view)
        summary.append("wrote %d evaluation directories for bootstrap_a04.py" % len(sel))
    if a.draws > 0:
        picks, lines, w, bad = check_draws(a.evidence, gt_path, mapped, sel, a.draws)
        summary.append("image-resampling draws (filed bootstrap_a04.py, pycocotools; draw numbers %s; columns mAP, "
                       "AP knife, AP gun, AP stick):" % ",".join(map(str, picks)))
        summary.extend(lines)
        if bad:
            summary.append("FAIL (draws): %d of %d runs differ from the filed draws by more than %.0e" % (bad, len(sel), TOL))
            status = 1
        else:
            summary.append("PASS (draws): maximum absolute difference %.2e <= %.0e (%d runs, %d draws each)"
                           % (w, TOL, len(sel), len(picks)))
    for s in summary:
        print(s)
    if a.out:
        with open(a.out, "w") as f:
            for h in head:
                f.write("# " + h + "\n")
            f.write("run\tquantity\tfiled\trecomputed\tabs_diff\n")
            for r in rows:
                f.write("\t".join(r) + "\n")
            for s in summary:
                f.write("# " + s + "\n")
    sys.exit(status)


if __name__ == "__main__":
    main()
