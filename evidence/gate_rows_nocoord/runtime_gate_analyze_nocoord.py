#!/usr/bin/env python3
"""Recompute the summary of the run-time gate measurement (runtime_gate_analysis.txt).
Python 3, standard library only.

usage: runtime_gate_analyze_nocoord.py [--status] [DIR]

DIR is the folder that holds the released files (default: the folder of this script).
The output is byte-identical to runtime_gate_analysis.txt. With --status every line is
prefixed with a tag that says where the part of the line that concerns the rows of D2 and
of the pooled source "other" (5,636 rows, called restricted below) comes from:

  [H]  header line, no data
  [C]  count over the per-row files of D3 and D4 plus the count cells of the restricted
       rows, using recorded fields (class, admitted, class term, static strata and flags)
  [F]  as [C], but the field used for the restricted rows is a yes/no flag that the
       authors evaluated on the unreleased per-row values (run-time padding parity, the
       geometry comparisons, the comparisons between the two passes)
  [T]  the restricted part is a total supplied by the authors (restricted_aggregates.json)
  [L]  the restricted part comes from sorted value lists or bin counts without row id

For the rows of D3 and D4 every line is computed from the per-row files, with one
exception: the last line (same batch index in both passes) uses the released flag
same_batch_in_both_passes, because the batch index itself is not released.

Inputs that are approximations of the recorded values, and why the printed digits do not
change (the script checks the two cases it can check and stops if a check fails):
  * gate_iou of restricted admitted rows is rounded upward to 4 decimals. The lines that
    use it print a count of values below 0.999, the minimum (a row of D3 or D4) and the
    median to 6 decimals. The count stays 0: rounding is upward, and the smallest released
    value is 0.9991, so no recorded value of these rows lies below 0.999. The script stops
    if a released value of an admitted restricted row is below 0.9991.
  * |gate_iou - static ul_iou_int| of restricted rows is rounded to 8 decimals; the line
    prints the maximum to 6 decimals and the median to 3 significant digits.
  * the edge offset of restricted rejected rows is rounded to 3 decimals; the line prints
    3 decimals.
  * the edge offset of restricted admitted rows is given as bin counts. The script
    computes the line twice, with every such row at the lower and at the upper edge of
    its bin, and requires the two printed lines to be equal.
"""
import csv, json, os, statistics, sys
from collections import Counter

args = [a for a in sys.argv[1:] if a != "--status"]
STATUS = "--status" in sys.argv[1:]
D = args[0] if args else os.path.dirname(os.path.abspath(__file__))
PASSES = [(1, "pass1_seed42"), (2, "pass2_seed1337")]
STATIC_COLS = ["source", "size_bin", "aspect_bin", "pad_parity", "ul_pad_parity",
               "admitted_int", "admitted_float", "ul_admitted_int", "ul_admitted_float"]


def load(name):
    return list(csv.DictReader(open(os.path.join(D, name), newline="", encoding="utf-8")))


def out(tag, text):
    print(("[%s] " % tag if STATUS else "") + text)


static = {r["row_id"]: r for r in load("padding_row_audit.nocoord.public.csv")}
CELLS = load("restricted_cells.csv")
CLS_TERM = load("restricted_class_term_counts.csv")
AGG = json.load(open(os.path.join(D, "restricted_aggregates.json"), encoding="utf-8"))
R_GATE = load("restricted_gate_iou.sorted.csv")
R_DIFF = load("restricted_abs_gate_iou_minus_ul_iou_int.sorted.csv")
R_EDGE_REJ = load("restricted_edge_offset_rejected.sorted.csv")
R_EDGE_ADM = load("restricted_edge_offset_admitted_bins.csv")
nR = sum(int(c["n"]) for c in CELLS)
assert nR == AGG["restricted_rows"] == AGG["restricted_unique_row_keys"]
assert sum(int(c["n"]) for c in CLS_TERM) == nR
out("C", "static rows: %d" % (len(static) + nR))


def public_records(rows):
    """One record per row of D3 and D4; every comparison is evaluated here from the row values."""
    recs = []
    for r in rows:
        s = static[r["row_id"]]
        tx, ty = int(r["pad_total_x"]), int(r["pad_total_y"])
        ax, ay = 960 - int(s["new_w"]), 960 - int(s["new_h"])
        e = {c: s[c] for c in STATIC_COLS}
        e.update(
            n=1, cls=r["class"], admitted=r["admitted"],
            rt="odd" if (tx % 2 or ty % 2) else "even",
            ori_eq_bank=(int(r["ori_h"]), int(r["ori_w"])) == (int(float(r["bank_h"])), int(float(r["bank_w"]))),
            resized_960=(r["resized_h"], r["resized_w"]) == ("960", "960"),
            lbin_eq_ceil=(r["lb_in_w"], r["lb_in_h"]) == (s["ul_new_w"], s["ul_new_h"]),
            lbin_eq_round=(r["lb_in_w"], r["lb_in_h"]) == (s["new_w"], s["new_h"]),
            pad_rule_ok=(int(r["pad_left"]), int(r["pad_top"])) == (round(tx / 2 - 0.1), round(ty / 2 - 0.1)),
            pad_eq_adapter=(int(r["pad_left"]), int(r["pad_top"])) == (int(round(ax / 2 - 0.1)), int(round(ay / 2 - 0.1))),
            has_gate=r["gate_iou"] != "")
        recs.append(e)
    return recs


def restricted_records(p):
    """One record per count cell of the restricted rows; the comparisons are released flags."""
    recs = []
    for c in CELLS:
        g = lambda name: c["p%d_%s" % (p, name)]
        e = {k: c[k] for k in STATIC_COLS}
        e.update(
            n=int(c["n"]), cls=c["class"], admitted=g("admitted"), rt=g("rt_pad_parity"),
            ori_eq_bank=g("ori_eq_bank") == "1", resized_960=g("resized_960") == "1",
            lbin_eq_ceil=g("lbin_eq_ceil") == "1", lbin_eq_round=g("lbin_eq_round") == "1",
            pad_rule_ok=g("pad_rule_ok") == "1", pad_eq_adapter=g("pad_eq_adapter") == "1",
            has_gate=g("has_gate_iou") == "1")
        recs.append(e)
    return recs


def summarise(p, tag):
    rows = load("runtime_gate_rows_%s.nocoord.public.csv" % tag)
    E = public_records(rows) + restricted_records(p)
    N = sum(e["n"] for e in E)
    cnt = lambda f: sum(e["n"] for e in E if f(e))
    out("H", "%s runtime_gate_rows_%s.csv" % ("=" * 20, tag))
    ids = [r["row_id"] for r in rows]
    out("T", "row records: %d | unique row_id: %d | images: %d" % (
        N, len(set(ids)) + AGG["restricted_unique_row_keys"],
        len({r["image_idx"] for r in rows}) + AGG["restricted_images_pass%d" % p]))
    out("T", "static rows never seen in this pass: %d | seen rows missing from static: %d" % (
        len(set(static) - set(ids)) + AGG["restricted_static_rows_not_in_pass%d" % p],
        len(set(ids) - set(static)) + AGG["restricted_pass%d_rows_not_in_static" % p]))
    adm = cnt(lambda e: e["admitted"] == "1")
    out("C", "ADMITTED %d  REJECTED %d  of %d  rate %.4f" % (adm, N - adm, N, adm / N))
    # the class term: per row for D3 and D4, per (class, admitted, has_cls) count for the restricted rows
    for c in CLS_TERM:
        assert not (c["p%d_has_cls" % p] == "1" and c["p%d_admitted" % p] != "1")
    for cls in sorted({e["cls"] for e in E}):
        assert sum(int(c["n"]) for c in CLS_TERM if c["class"] == cls and c["p%d_admitted" % p] == "1") == \
            sum(int(c["n"]) for c in CELLS if c["class"] == cls and c["p%d_admitted" % p] == "1")
    out("C", "admitted with has_cls: %d" % (
        sum(int(r["has_cls"]) for r in rows) + sum(int(c["n"]) * int(c["p%d_has_cls" % p]) for c in CLS_TERM)))

    def br(keyf, title, t):
        c = Counter(); a = Counter()
        for e in E:
            k = keyf(e); c[k] += e["n"]; a[k] += e["n"] * int(e["admitted"])
        out(t, "-- " + title)
        for k in sorted(c, key=str):
            out(t, "   %-28s n=%5d admitted=%5d rejected=%5d rate=%.4f" % (k, c[k], a[k], c[k] - a[k], a[k] / c[k]))
    br(lambda e: e["cls"], "by class", "C")
    br(lambda e: e["rt"], "by RUN-TIME padding parity (960 - LetterBox input size, as observed in the pipeline)", "F")
    br(lambda e: e["pad_parity"], "by static pad_parity (round model, published)", "C")
    br(lambda e: e["ul_pad_parity"], "by static ul_pad_parity (ceil model)", "C")
    br(lambda e: e["source"], "by source", "C")
    br(lambda e: e["size_bin"], "by size bin", "C")
    br(lambda e: e["aspect_bin"], "by image aspect", "C")
    br(lambda e: "%s|rt_%s" % (e["pad_parity"], e["rt"]), "static round parity | run-time parity", "F")
    out("C", "-- confusion run-time admitted vs static columns (rows=static value, cols=run-time 0/1)")
    for col in ("admitted_int", "admitted_float", "ul_admitted_int", "ul_admitted_float"):
        c = Counter()
        for e in E:
            c[(e[col], e["admitted"])] += e["n"]
        agree = c[("0", "0")] + c[("1", "1")]
        out("C", "   %-18s s0r0=%5d s0r1=%5d s1r0=%5d s1r1=%5d agree=%d/%d" % (
            col, c[("0", "0")], c[("0", "1")], c[("1", "0")], c[("1", "1")], agree, N))
    out("H", "-- geometry checks")
    out("F", "   ori (h,w) != bank (h,w): %d" % cnt(lambda e: not e["ori_eq_bank"]))
    out("F", "   resized_shape != (960,960): %d" % cnt(lambda e: not e["resized_960"]))
    out("F", "   LetterBox input (w,h) != static ul_new (ceil): %d" % cnt(lambda e: not e["lbin_eq_ceil"]))
    out("F", "   LetterBox input (w,h) != static new (round): %d" % cnt(lambda e: not e["lbin_eq_round"]))
    out("F", "   observed (left,top) != round(total/2-0.1): %d" % cnt(lambda e: not e["pad_rule_ok"]))
    c = Counter()
    for e in E:
        c[(e["pad_eq_adapter"], e["admitted"])] += e["n"]
    # keys in descending order; this is the order of first occurrence in the original per-row file
    out("F", "   observed pipeline pad == adapter int pad, by admitted: %s" % {k: c[k] for k in sorted(c, reverse=True)})
    out("F", "   rows with no same-class label in batch: %d" % cnt(lambda e: not e["has_gate"]))

    # gate_iou: per row for D3 and D4; sorted list with the admitted flag for the restricted rows
    g = [(float(r["gate_iou"]), r["admitted"]) for r in rows if r["gate_iou"] != ""]
    d2 = [abs(float(r["gate_iou"]) - float(static[r["row_id"]]["iou_int"])) for r in rows if r["gate_iou"] != ""]
    d = [abs(float(r["gate_iou"]) - float(static[r["row_id"]]["ul_iou_int"])) for r in rows if r["gate_iou"] != ""]
    rg = [(float(x["value"]), x["admitted"]) for x in R_GATE if x["pass"] == str(p)]
    assert all(c["admitted_int"] == "1" for c in CELLS)      # static iou_int is 1 for every restricted row
    if any(a == "1" and v < 0.9991 for v, a in rg):
        sys.exit("a released gate_iou of an admitted restricted row is below 0.9991; the count of values below 0.999 is not fixed")
    g += rg
    d2 += [abs(v - 1.0) for v, a in rg]
    d += [float(x["value"]) for x in R_DIFF if x["pass"] == str(p)]
    assert len(g) == len(d) == cnt(lambda e: e["has_gate"])
    for a in ("0", "1"):
        assert sum(1 for v, x in rg if x == a) == sum(int(c["n"]) for c in CELLS if c["p%d_admitted" % p] == a and c["p%d_has_gate_iou" % p] == "1")
    out("L", "   admitted but gate_iou<0.999: %d | rejected but gate_iou>=0.999 (greedy/other): %d" % (
        sum(1 for v, a in g if a == "1" and v < 0.999), sum(1 for v, a in g if a == "0" and v >= 0.999)))
    out("L", "   |gate_iou - static ul_iou_int|: max %.6f median %.2e" % (max(d), statistics.median(d)))
    out("L", "   |gate_iou - static iou_int(=1)|: max %.6f" % max(d2))
    ra = sorted(v for v, a in g if a == "1"); rr = sorted(v for v, a in g if a == "0")
    out("L", "   gate_iou admitted: n=%d min=%.6f median=%.6f" % (len(ra), ra[0], statistics.median(ra)))
    q = lambda f: rr[min(len(rr) - 1, int(f * len(rr)))]
    out("L", "   gate_iou rejected: n=%d min=%.5f p05=%.5f median=%.5f p95=%.5f max=%.6f" % (
        len(rr), rr[0], q(.05), statistics.median(rr), q(.95), rr[-1]))
    out("L", "   rejected with gate_iou in [0.99,0.999): %d ; [0.95,0.99): %d ; <0.95: %d" % (
        sum(1 for v in rr if v >= 0.99), sum(1 for v in rr if 0.95 <= v < 0.99), sum(1 for v in rr if v < 0.95)))
    mx = [float(r["max_abs_edge_offset_px"]) for r in rows if r["admitted"] == "0"]
    mx += [float(x["value"]) for x in R_EDGE_REJ if x["pass"] == str(p)]
    assert len(mx) == len(rr)
    out("L", "   rejected rows max |edge offset adapter-batch| px: median %.3f p95 %.3f max %.3f" % (
        statistics.median(mx), sorted(mx)[int(.95 * len(mx))], max(mx)))
    pub_a = [float(r["max_abs_edge_offset_px"]) for r in rows if r["admitted"] == "1"]
    lines = []
    for edge in ("lower_exclusive", "upper_inclusive"):
        mxa = list(pub_a)
        for x in R_EDGE_ADM:
            if x["pass"] == str(p):
                mxa += [float(x[edge])] * int(x["n"])
        assert len(mxa) == len(ra)
        lines.append("   admitted rows max |edge offset| px: median %.4f max %.4f" % (statistics.median(mxa), max(mxa)))
    if lines[0] != lines[1]:
        sys.exit("the bin counts do not fix the admitted edge-offset line: %r / %r" % tuple(lines))
    out("L", lines[1])
    return {r["row_id"]: r for r in rows}


d1 = summarise(*PASSES[0])
d2 = summarise(*PASSES[1])
common = sorted(set(d1) & set(d2))
cR = lambda f: sum(int(c["n"]) for c in CELLS if f(c))
out("H", "%s pass comparison" % ("=" * 20))
out("T", "rows in both passes: %d | images: %d" % (
    len(common) + nR, len({d1[k]["image_idx"] for k in common}) + AGG["restricted_images_in_both_passes"]))
out("C", "admitted differs: %d" % (
    sum(1 for k in common if d1[k]["admitted"] != d2[k]["admitted"]) + cR(lambda c: c["p1_admitted"] != c["p2_admitted"])))
out("F", "gate_iou differs (string): %d" % (
    sum(1 for k in common if d1[k]["gate_iou"] != d2[k]["gate_iou"]) + cR(lambda c: c["x_same_gate_iou"] != "1")))
out("F", "batch box differs: %d" % (
    sum(1 for k in common if d1[k]["batch_box_digest"] != d2[k]["batch_box_digest"]) + cR(lambda c: c["x_same_box"] != "1")))
out("F", "pad/resized differs: %d" % (
    sum(1 for k in common if any(d1[k][c] != d2[k][c] for c in ("pad_left", "pad_top", "lb_in_h", "lb_in_w", "resized_h", "resized_w")))
    + cR(lambda c: c["x_same_pad"] != "1")))
ims = {}
for k in common:
    ims[d1[k]["image_idx"]] = (d1[k]["img_sum"], d2[k]["img_sum"])
out("T", "images whose pixel sum differs between passes (augmentation differed): %d of %d" % (
    sum(1 for a, b in ims.values() if a != b) + AGG["restricted_images_pixel_sum_differs_between_passes"],
    len(ims) + AGG["restricted_images_in_both_passes"]))
assert all(d1[k]["same_batch_in_both_passes"] == d2[k]["same_batch_in_both_passes"] for k in common)
out("F", "same batch index for image in both passes: %d of %d" % (
    sum(1 for k in common if d1[k]["same_batch_in_both_passes"] == "1") + cR(lambda c: c["x_same_batch"] == "1"), len(common) + nR))
