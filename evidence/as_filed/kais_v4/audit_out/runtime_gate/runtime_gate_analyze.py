#!/usr/bin/env python3
"""Summarise runtime_gate_rows_*.csv against the static padding_row_audit.csv. Stdlib only.
usage: runtime_gate_analyze.py STATIC.csv PASS1.csv [PASS2.csv]"""
import csv, sys, statistics, json
from collections import Counter

def load(p):
    return list(csv.DictReader(open(p, newline="", encoding="utf-8")))

static = {r["row_id"]: r for r in load(sys.argv[1])}
p1 = load(sys.argv[2])
print("static rows:", len(static))

def summarise(rows, name):
    print("=" * 20, name)
    ids = [r["row_id"] for r in rows]
    print("row records:", len(rows), "| unique row_id:", len(set(ids)), "| images:", len({r["im_file"] for r in rows}))
    print("static rows never seen in this pass:", len(set(static) - set(ids)), "| seen rows missing from static:", len(set(ids) - set(static)))
    adm = sum(int(r["admitted"]) for r in rows)
    print("ADMITTED %d  REJECTED %d  of %d  rate %.4f" % (adm, len(rows) - adm, len(rows), adm / len(rows)))
    print("admitted with has_cls:", sum(int(r["has_cls"]) for r in rows))
    def br(keyf, title):
        c = Counter(); a = Counter()
        for r in rows:
            k = keyf(r); c[k] += 1; a[k] += int(r["admitted"])
        print("--", title)
        for k in sorted(c, key=str):
            print("   %-28s n=%5d admitted=%5d rejected=%5d rate=%.4f" % (k, c[k], a[k], c[k] - a[k], a[k] / c[k]))
    br(lambda r: r["class"], "by class")
    def rt_par(r):
        tx, ty = int(r["pad_total_x"]), int(r["pad_total_y"])
        return "odd" if (tx % 2 or ty % 2) else "even"
    br(rt_par, "by RUN-TIME padding parity (960 - LetterBox input size, as observed in the pipeline)")
    br(lambda r: static[r["row_id"]]["pad_parity"], "by static pad_parity (round model, published)")
    br(lambda r: static[r["row_id"]]["ul_pad_parity"], "by static ul_pad_parity (ceil model)")
    br(lambda r: static[r["row_id"]]["source"], "by source")
    br(lambda r: static[r["row_id"]]["size_bin"], "by size bin")
    br(lambda r: static[r["row_id"]]["aspect_bin"], "by image aspect")
    br(lambda r: "%s|rt_%s" % (static[r["row_id"]]["pad_parity"], rt_par(r)), "static round parity | run-time parity")
    print("-- confusion run-time admitted vs static columns (rows=static value, cols=run-time 0/1)")
    for col in ("admitted_int", "admitted_float", "ul_admitted_int", "ul_admitted_float"):
        c = Counter((static[r["row_id"]][col], r["admitted"]) for r in rows)
        agree = c[("0", "0")] + c[("1", "1")]
        print("   %-18s s0r0=%5d s0r1=%5d s1r0=%5d s1r1=%5d agree=%d/%d" % (col, c[("0", "0")], c[("0", "1")], c[("1", "0")], c[("1", "1")], agree, len(rows)))
    print("-- geometry checks")
    print("   ori (h,w) != bank (h,w):", sum(1 for r in rows if (int(r["ori_h"]), int(r["ori_w"])) != (int(float(r["bank_h"])), int(float(r["bank_w"])))))
    print("   resized_shape != (960,960):", sum(1 for r in rows if (r["resized_h"], r["resized_w"]) != ("960", "960")))
    print("   LetterBox input (w,h) != static ul_new (ceil):", sum(1 for r in rows if (r["lb_in_w"], r["lb_in_h"]) != (static[r["row_id"]]["ul_new_w"], static[r["row_id"]]["ul_new_h"])))
    print("   LetterBox input (w,h) != static new (round):", sum(1 for r in rows if (r["lb_in_w"], r["lb_in_h"]) != (static[r["row_id"]]["new_w"], static[r["row_id"]]["new_h"])))
    def rt_pad_ok(r):
        tx, ty = int(r["pad_total_x"]), int(r["pad_total_y"])
        return (int(r["pad_left"]), int(r["pad_top"])) == (round(tx / 2 - 0.1), round(ty / 2 - 0.1))
    print("   observed (left,top) != round(total/2-0.1):", sum(1 for r in rows if not rt_pad_ok(r)))
    def adapter_pad(r):
        s = static[r["row_id"]]; tx, ty = 960 - int(s["new_w"]), 960 - int(s["new_h"])
        return (int(round(tx / 2 - 0.1)), int(round(ty / 2 - 0.1)))
    c = Counter(((int(r["pad_left"]), int(r["pad_top"])) == adapter_pad(r), r["admitted"]) for r in rows)
    print("   observed pipeline pad == adapter int pad, by admitted:", dict(c))
    no_lab = [r for r in rows if r["gate_iou"] == ""]
    print("   rows with no same-class label in batch:", len(no_lab))
    g = [(float(r["gate_iou"]), r) for r in rows if r["gate_iou"] != ""]
    print("   admitted but gate_iou<0.999:", sum(1 for v, r in g if r["admitted"] == "1" and v < 0.999),
          "| rejected but gate_iou>=0.999 (greedy/other):", sum(1 for v, r in g if r["admitted"] == "0" and v >= 0.999))
    d = [abs(v - float(static[r["row_id"]]["ul_iou_int"])) for v, r in g]
    print("   |gate_iou - static ul_iou_int|: max %.6f median %.2e" % (max(d), statistics.median(d)))
    d2 = [abs(v - float(static[r["row_id"]]["iou_int"])) for v, r in g]
    print("   |gate_iou - static iou_int(=1)|: max %.6f" % max(d2))
    ra = sorted(v for v, r in g if r["admitted"] == "1"); rr = sorted(v for v, r in g if r["admitted"] == "0")
    print("   gate_iou admitted: n=%d min=%.6f median=%.6f" % (len(ra), ra[0], statistics.median(ra)))
    if rr:
        q = lambda p: rr[min(len(rr) - 1, int(p * len(rr)))]
        print("   gate_iou rejected: n=%d min=%.5f p05=%.5f median=%.5f p95=%.5f max=%.6f" % (len(rr), rr[0], q(.05), statistics.median(rr), q(.95), rr[-1]))
        print("   rejected with gate_iou in [0.99,0.999): %d ; [0.95,0.99): %d ; <0.95: %d" % (
            sum(1 for v in rr if v >= 0.99), sum(1 for v in rr if 0.95 <= v < 0.99), sum(1 for v in rr if v < 0.95)))
        mx = [max(abs(float(r[k])) for k in ("d_x1_px", "d_y1_px", "d_x2_px", "d_y2_px")) for v, r in g if r["admitted"] == "0"]
        print("   rejected rows max |edge offset adapter-batch| px: median %.3f p95 %.3f max %.3f" % (statistics.median(mx), sorted(mx)[int(.95 * len(mx))], max(mx)))
    mxa = [max(abs(float(r[k])) for k in ("d_x1_px", "d_y1_px", "d_x2_px", "d_y2_px")) for v, r in g if r["admitted"] == "1"]
    print("   admitted rows max |edge offset| px: median %.4f max %.4f" % (statistics.median(mxa), max(mxa)))
    return {r["row_id"]: r for r in rows}

d1 = summarise(p1, sys.argv[2])
if len(sys.argv) > 3:
    p2 = load(sys.argv[3])
    d2 = summarise(p2, sys.argv[3])
    common = sorted(set(d1) & set(d2))
    print("=" * 20, "pass comparison")
    print("rows in both passes:", len(common), "| images:", len({d1[k]["im_file"] for k in common}))
    print("admitted differs:", sum(1 for k in common if d1[k]["admitted"] != d2[k]["admitted"]))
    print("gate_iou differs (string):", sum(1 for k in common if d1[k]["gate_iou"] != d2[k]["gate_iou"]))
    print("batch box differs:", sum(1 for k in common if any(d1[k][c] != d2[k][c] for c in ("batch_cx", "batch_cy", "batch_w", "batch_h"))))
    print("pad/resized differs:", sum(1 for k in common if any(d1[k][c] != d2[k][c] for c in ("pad_left", "pad_top", "lb_in_h", "lb_in_w", "resized_h", "resized_w"))))
    ims = {}
    for k in common:
        ims[d1[k]["im_file"]] = (d1[k]["img_sum"], d2[k]["img_sum"])
    print("images whose pixel sum differs between passes (augmentation differed):", sum(1 for a, b in ims.values() if a != b), "of", len(ims))
    print("same batch index for image in both passes:", sum(1 for k in common if d1[k]["batch_i"] == d2[k]["batch_i"]), "of", len(common))
