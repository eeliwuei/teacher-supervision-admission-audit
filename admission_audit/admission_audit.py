#!/usr/bin/env python3
"""admission_audit.py - count and stratify the supervision a geometric gate admits.

When teacher outputs are stored and later re-attached to a training batch, the
same object is placed in batch coordinates by two code paths (for example the
path that produced the stored teacher boxes and the data loader of the student).
If a consistency gate compares the two placements by IoU and rejects rows below
a threshold, small differences in resize and padding arithmetic can decide how
much supervision reaches the loss. This tool measures that directly.

Input, either
  --csv FILE   one row per object, columns ax1,ay1,ax2,ay2 (box from path A) and
               bx1,by1,bx2,by2 (box from path B), in pixels of the same canvas;
               any further columns can be used as strata with --strata c1,c2
  --npy-a A.npy --npy-b B.npy   two arrays of shape (N, 4), xyxy, row-aligned

Output: rows total, admitted and share at --threshold (default 0.999); the same
per stratum; quantiles of IoU; quantiles of per-edge absolute offsets in pixels;
the share admitted at thresholds 0.5, 0.9, 0.99 and 0.999. --json FILE writes
the same content as JSON.

The helpers place_uniform_round() and place_ceil_peraxis() illustrate two resize
conventions so that box pairs can be generated for any image size without a
dataset. They are illustrations of the two conventions, not the exact code of
any library; audit your own pipeline with boxes taken from your own code paths.

Requires numpy. pandas is used for CSV reading if installed, otherwise the csv
module. No network access. Run `python3 admission_audit.py --selftest` to check.
"""
import argparse
import csv
import json
import math
import sys

import numpy as np

try:  # optional
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

BOX_A = ["ax1", "ay1", "ax2", "ay2"]
BOX_B = ["bx1", "by1", "bx2", "by2"]
SWEEP = (0.5, 0.9, 0.99, 0.999)
QUANTILES = (0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0)
EDGES = ("x1", "y1", "x2", "y2")


def pairwise_iou(a, b):
    """Row-wise IoU of two (N, 4) xyxy arrays. Degenerate pairs give 0."""
    a = np.asarray(a, dtype=np.float64).reshape(-1, 4)
    b = np.asarray(b, dtype=np.float64).reshape(-1, 4)
    iw = np.clip(np.minimum(a[:, 2], b[:, 2]) - np.maximum(a[:, 0], b[:, 0]), 0, None)
    ih = np.clip(np.minimum(a[:, 3], b[:, 3]) - np.maximum(a[:, 1], b[:, 1]), 0, None)
    inter = iw * ih
    area_a = np.clip(a[:, 2] - a[:, 0], 0, None) * np.clip(a[:, 3] - a[:, 1], 0, None)
    area_b = np.clip(b[:, 2] - b[:, 0], 0, None) * np.clip(b[:, 3] - b[:, 1], 0, None)
    union = area_a + area_b - inter
    return np.where(union > 0, inter / np.where(union > 0, union, 1.0), 0.0)


def place_uniform_round(boxes, w0, h0, S):
    """Illustration 1: uniform gain, rounded resized size, whole-pixel padding.

    One gain r = min(S/w0, S/h0) scales both axes; the resized image is
    round(w0*r) x round(h0*r); it is centred on the S x S canvas with the
    left/top padding rounded to whole pixels. Boxes use r on both axes.
    """
    b = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    r = min(S / w0, S / h0)
    new_w, new_h = int(round(w0 * r)), int(round(h0 * r))
    left = int(round((S - new_w) / 2 - 0.1))
    top = int(round((S - new_h) / 2 - 0.1))
    return b * r + np.array([left, top, left, top], dtype=np.float64)


def place_ceil_peraxis(boxes, w0, h0, S):
    """Illustration 2: ceil resized size, per-axis gain, then pad.

    The resized image is ceil(w0*r) x ceil(h0*r) with r = min(S/w0, S/h0);
    each axis then has its own gain (resized size / original size); the image
    is centred with floor-divided padding. Boxes use the per-axis gains.
    """
    b = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    r = min(S / w0, S / h0)
    new_w, new_h = int(math.ceil(w0 * r)), int(math.ceil(h0 * r))
    gx, gy = new_w / w0, new_h / h0
    left, top = (S - new_w) // 2, (S - new_h) // 2
    return b * np.array([gx, gy, gx, gy]) + np.array([left, top, left, top], dtype=np.float64)


def _q(x):
    if x.size == 0:
        return {}
    return {"q%g" % (100 * p): float(np.quantile(x, p)) for p in QUANTILES}


def _count(iou, thr):
    n = int(iou.size)
    k = int(np.count_nonzero(iou >= thr))
    return {"rows": n, "admitted": k, "share": (k / n) if n else float("nan")}


def audit(box_a, box_b, strata=None, threshold=0.999):
    """Audit a gate that admits a row when IoU(box_a, box_b) >= threshold.

    box_a, box_b: (N, 4) xyxy arrays. strata: optional dict name -> length-N
    sequence of labels. Returns a JSON-serialisable dict.
    """
    a = np.asarray(box_a, dtype=np.float64).reshape(-1, 4)
    b = np.asarray(box_b, dtype=np.float64).reshape(-1, 4)
    if a.shape != b.shape:
        raise ValueError("box arrays differ in shape: %s vs %s" % (a.shape, b.shape))
    finite = np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
    iou = pairwise_iou(a, b)
    iou[~finite] = 0.0  # a non-finite row cannot pass a gate
    off = np.abs(a - b)[finite]
    out = {
        "threshold": float(threshold),
        "non_finite_rows": int((~finite).sum()),
        "overall": _count(iou, threshold),
        "iou_quantiles": _q(iou),
        "edge_abs_offset_px": {e: _q(off[:, i]) for i, e in enumerate(EDGES)},
        "max_edge_abs_offset_px": _q(off.max(axis=1)) if off.size else {},
        "threshold_sweep": {str(t): _count(iou, t) for t in SWEEP},
        "strata": {},
    }
    for name, labels in (strata or {}).items():
        labels = np.asarray([str(v) for v in labels])
        if labels.shape[0] != iou.shape[0]:
            raise ValueError("stratum %r has %d labels for %d rows" % (name, labels.shape[0], iou.shape[0]))
        out["strata"][name] = {lv: _count(iou[labels == lv], threshold) for lv in sorted(set(labels.tolist()))}
    return out


def format_report(res):
    L = []
    o = res["overall"]
    L.append("Admission audit, gate: IoU >= %g" % res["threshold"])
    L.append("  rows %d   admitted %d   share %.4f" % (o["rows"], o["admitted"], o["share"]))
    if res["non_finite_rows"]:
        L.append("  rows with non-finite coordinates (counted as rejected): %d" % res["non_finite_rows"])
    L.append("")
    L.append("Share admitted at other thresholds")
    for t, c in res["threshold_sweep"].items():
        L.append("  IoU >= %-6s admitted %8d of %8d   share %.4f" % (t, c["admitted"], c["rows"], c["share"]))
    keys = list(res["iou_quantiles"].keys())
    if keys:
        L.append("")
        L.append("Quantiles     " + "".join("%10s" % k for k in keys))
        L.append("  IoU         " + "".join("%10.6f" % res["iou_quantiles"][k] for k in keys))
        for e in EDGES:
            d = res["edge_abs_offset_px"][e]
            if d:
                L.append("  |d%s| px    " % e + "".join("%10.4f" % d[k] for k in keys))
        d = res["max_edge_abs_offset_px"]
        if d:
            L.append("  max edge px " + "".join("%10.4f" % d[k] for k in keys))
    for name, levels in res["strata"].items():
        L.append("")
        L.append("By %s" % name)
        width = max([len(lv) for lv in levels] + [5])
        L.append("  %-*s %8s %9s %8s" % (width, "level", "rows", "admitted", "share"))
        for lv, c in levels.items():
            L.append("  %-*s %8d %9d %8.4f" % (width, lv, c["rows"], c["admitted"], c["share"]))
    return "\n".join(L)


def read_csv(path, strata_cols):
    need = BOX_A + BOX_B + list(strata_cols)
    if pd is not None:
        df = pd.read_csv(path)
        miss = [c for c in need if c not in df.columns]
        if miss:
            raise SystemExit("missing CSV columns: %s" % ", ".join(miss))
        return (df[BOX_A].to_numpy(dtype=np.float64), df[BOX_B].to_numpy(dtype=np.float64),
                {c: df[c].astype(str).tolist() for c in strata_cols})
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    miss = [c for c in need if rows and c not in rows[0]]
    if miss:
        raise SystemExit("missing CSV columns: %s" % ", ".join(miss))
    a = np.array([[float(r[c]) for c in BOX_A] for r in rows], dtype=np.float64).reshape(-1, 4)
    b = np.array([[float(r[c]) for c in BOX_B] for r in rows], dtype=np.float64).reshape(-1, 4)
    return a, b, {c: [r[c] for r in rows] for c in strata_cols}


def selftest():
    """Synthetic check on a few image sizes; prints an audit and returns 0 on success."""
    S = 960
    rng = np.random.default_rng(0)
    A, B, shape, size = [], [], [], []
    for (w0, h0) in [(1333, 800), (1280, 720), (1920, 1080), (640, 480), (500, 375), (960, 960)]:
        n = 200
        bw = rng.uniform(8, 0.6 * w0, n)
        bh = rng.uniform(8, 0.6 * h0, n)
        x1 = rng.uniform(0, w0 - bw)
        y1 = rng.uniform(0, h0 - bh)
        boxes = np.stack([x1, y1, x1 + bw, y1 + bh], axis=1)
        pa = place_uniform_round(boxes, w0, h0, S)
        pb = place_ceil_peraxis(boxes, w0, h0, S)
        assert pa.min() >= -1e-6 and pa.max() <= S + 1e-6, "path A left the canvas"
        assert pb.min() >= -1e-6 and pb.max() <= S + 1.0 + 1e-6, "path B left the canvas"
        A.append(pa)
        B.append(pb)
        shape += ["%dx%d" % (w0, h0)] * n
        side = np.sqrt((pa[:, 2] - pa[:, 0]) * (pa[:, 3] - pa[:, 1]))
        size += np.where(side < 32, "small", np.where(side < 96, "medium", "large")).tolist()
    A, B = np.concatenate(A), np.concatenate(B)
    assert np.allclose(pairwise_iou(A, A), 1.0), "IoU of identical boxes must be 1"
    same = audit(A, A)
    assert same["overall"]["share"] == 1.0, "identical placements must all be admitted"
    assert pairwise_iou([[0, 0, 10, 10]], [[20, 20, 30, 30]])[0] == 0.0
    assert abs(pairwise_iou([[0, 0, 10, 10]], [[0, 0, 10, 5]])[0] - 0.5) < 1e-12
    sq = place_uniform_round([[10, 10, 50, 50]], 960, 960, S) - place_ceil_peraxis([[10, 10, 50, 50]], 960, 960, S)
    assert np.abs(sq).max() == 0.0, "no resize: both conventions must agree"
    res = audit(A, B, strata={"image_shape": shape, "size_bucket": size}, threshold=0.999)
    sw = [res["threshold_sweep"][str(t)]["share"] for t in SWEEP]
    assert all(x >= y for x, y in zip(sw, sw[1:])), "admitted share must not rise with the threshold"
    assert sum(c["rows"] for c in res["strata"]["image_shape"].values()) == res["overall"]["rows"]
    json.dumps(res)
    print("Synthetic boxes, canvas S=%d; path A = uniform gain / rounded size / whole-pixel pad," % S)
    print("path B = ceil size / per-axis gain / pad. Illustration only, not a result of the paper.\n")
    print(format_report(res))
    print("\nselftest: PASS")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Audit how much supervision a geometric IoU gate admits.")
    p.add_argument("--csv", help="CSV with columns %s and optional strata" % ",".join(BOX_A + BOX_B))
    p.add_argument("--npy-a", help=".npy array (N,4) xyxy from code path A")
    p.add_argument("--npy-b", help=".npy array (N,4) xyxy from code path B")
    p.add_argument("--strata", default="", help="comma-separated CSV columns to stratify by")
    p.add_argument("--threshold", type=float, default=0.999, help="gate threshold on IoU (default 0.999)")
    p.add_argument("--json", help="write the audit to this JSON file")
    p.add_argument("--selftest", action="store_true", help="run a synthetic check and exit")
    args = p.parse_args(argv)
    if args.selftest:
        return selftest()
    cols = [c.strip() for c in args.strata.split(",") if c.strip()]
    if args.csv:
        a, b, strata = read_csv(args.csv, cols)
    elif args.npy_a and args.npy_b:
        if cols:
            raise SystemExit("--strata needs --csv")
        a, b, strata = np.load(args.npy_a), np.load(args.npy_b), {}
    else:
        p.error("give --csv, or --npy-a and --npy-b, or --selftest")
    res = audit(a, b, strata=strata, threshold=args.threshold)
    print(format_report(res))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(res, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
