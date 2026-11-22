#!/usr/bin/env python3
"""recompute.py - run the filed analysis scripts, unchanged, on the files of this bundle and compare with the filed results.

Usage (from anywhere):   python3 tools/recompute.py [--out DIR] [--keep-view] [STEP ...]
STEP is any of: digests order add06 a04 pairs gate counts   (default: all). Needs numpy and scipy. CPU only.

The filed scripts take their input directory on the command line and expect <eval_root>/<run>/metrics_unified.json
(and, for the sixth-addendum script, <eval_root>/<run>/predictions.json). In this bundle the endpoint files are in
scrubbed/ and the prediction files in as_filed/, so this wrapper builds a temporary directory of links
(<out>/eval_view/<run>/...) that puts the two side by side, and passes it to the scripts. No filed script is edited
or imported; each is started as a separate process exactly as its usage line says.

Outputs in DIR (default: _test_out/ in the bundle):
  results_final_sbs.recomputed.json   from as_filed/kais_v4/analysis/analyze_kaisv4.py
  results_add06.recomputed.json       from as_filed/kais_v4/analysis/analyze_add06.py
  a04_contrasts.recomputed.json       from as_filed/kais_v4/analysis/a04_contrasts.py
  card_pairs_sha256.tsv               SHA-256 of the seven pairs of prediction files
  gate_counts.tsv                     run-time gate counts read from the scrubbed summary and meta files
  current_kd_match_counts.tsv         admitted-row bookkeeping of the runs in this bundle (from their run summaries)
  RECOMPUTE_REPORT.txt                one line per comparison: MATCH or the exact differences
Exit status 0 only if every comparison matches.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
AF = os.path.join(BUNDLE, "as_filed")
SC = os.path.join(BUNDLE, "scrubbed")
AN = os.path.join(AF, "kais_v4", "analysis")
EV = os.path.join("eval", "factorial_v3_freeze")
FILED = {
    "order": ("analyze_kaisv4.py", "results_final_sbs_20261115T011951Z.json", "results_final_sbs.recomputed.json"),
    "add06": ("analyze_add06.py", "results_add06_20261121T045950Z.json", "results_add06.recomputed.json"),
    "a04": ("a04_contrasts.py", "a04_contrasts_20261115T012010Z.json", "a04_contrasts.recomputed.json"),
}
S = [42, 1337, 20260703]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def build_view(view):
    if os.path.isdir(view):
        shutil.rmtree(view)
    runs = sorted(os.listdir(os.path.join(SC, EV)))
    for r in runs:
        os.makedirs(os.path.join(view, r))
        for name, top in (("metrics_unified.json", SC), ("predictions.json", AF)):
            src = os.path.join(top, EV, r, name)
            dst = os.path.join(view, r, name)
            if not os.path.exists(src):
                continue
            try:
                os.symlink(os.path.relpath(src, os.path.dirname(dst)), dst)
            except OSError:
                shutil.copyfile(src, dst)
    return runs


def diff_json(a, b, path="$"):
    """Exact comparison. Returns a list of 'path: filed -> recomputed' strings."""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(f"{path}.{k}: missing in filed")
            elif k not in b:
                out.append(f"{path}.{k}: missing in recomputed")
            else:
                out += diff_json(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: list length {len(a)} -> {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff_json(x, y, f"{path}[{i}]")
    else:
        same = (a == b) and (type(a) is type(b) or not isinstance(a, bool) and not isinstance(b, bool))
        if isinstance(a, float) and isinstance(b, float) and a != a and b != b:
            same = True   # NaN on both sides
        if not same:
            extra = ""
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
                extra = f"  (difference {b - a:.3e})"
            out.append(f"{path}: {a!r} -> {b!r}{extra}")
    return out


def count_numbers(o):
    if isinstance(o, dict):
        return sum(count_numbers(v) for v in o.values())
    if isinstance(o, list):
        return sum(count_numbers(v) for v in o)
    return int(isinstance(o, (int, float)) and not isinstance(o, bool))


class Report:
    def __init__(self, path):
        self.path, self.lines, self.bad = path, [], 0

    def add(self, name, ok, detail=""):
        self.bad += (not ok)
        line = f"{'MATCH   ' if ok else 'DIFFERS '} {name}" + (f"  {detail}" if detail else "")
        self.lines.append(line)
        print(line)

    def note(self, text):
        self.lines.append(text)
        print(text)

    def write(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self.lines) + "\n")


def step_digests(rep, out):
    """Digests of the analysis scripts against the two filed digest lists."""
    want = {}
    for line in open(os.path.join(AF, "kais_v4", "ANALYSIS_ADDENDUM_06.sha256"), encoding="utf-8"):
        p = line.split()
        if len(p) == 2:
            want[os.path.join("kais_v4", p[1])] = p[0]
    for line in open(os.path.join(AF, "kais_v4", "ANALYSIS_CODE_RECORD_01.md"), encoding="utf-8"):
        m = re.match(r"\s*([0-9a-f]{64})\s+(\S+\.py)\s*$", line)
        if m:
            want[os.path.join("kais_v4", "analysis", m.group(2))] = m.group(1)
    for rel in sorted(want):
        p = os.path.join(AF, rel)
        got = sha(p) if os.path.exists(p) else "absent"
        rep.add(f"filed digest of {rel}", got == want[rel], "" if got == want[rel] else f"filed {want[rel]} bundle {got}")


def run_filed(rep, out, key, args):
    script, filed, new = FILED[key]
    newp = os.path.join(out, new)
    r = subprocess.run([sys.executable, os.path.join(AN, script)] + args + [newp],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        rep.add(f"{script} ran", False, r.stderr.strip()[-400:])
        return
    a = json.load(open(os.path.join(AN, filed)))
    b = json.load(open(newp))
    d = diff_json(a, b)
    rep.add(f"{script} -> {new} vs filed {filed}", not d,
            f"({count_numbers(a)} numeric values, all identical)" if not d else f"{len(d)} differences")
    for x in d:
        rep.note("    " + x)
    return b


def step_pairs(rep, out):
    def mech(mode, s): return f"C1-M-{mode}_seed{s}_kaisv4mech"
    pairs = [("std", s, mech("std", s) if s != 20260703 else f"C1-M_seed{s}_kaisv4", f"C1-M-std-c80_seed{s}_kaisv4mech") for s in S]
    pairs += [("nokd", s, f"C0-R-std_seed{s}_kaisv4mech" if s != 20260703 else f"C0-R_seed{s}_kaisv4", f"C0-R-std-c80_seed{s}_kaisv4mech") for s in S]
    pairs += [("randmask", 20260703, mech("randmask", 20260703), "C1-M-randmask-c80_seed20260703_kaisv4mech")]
    filed = json.load(open(os.path.join(AN, FILED["add06"][1])))["card_pairs"]
    rows, n_same = [], 0
    for (c, s, a, b), f in zip(pairs, filed):
        ha, hb = (sha(os.path.join(AF, EV, r, "predictions.json")) for r in (a, b))
        n_same += (ha == hb)
        agree = (f["run_40GB"], f["run_80GB"], f["predictions_sha256_40GB"], f["predictions_sha256_80GB"]) == (a, b, ha, hb)
        rows.append((c, s, a, b, ha, hb, "identical" if ha == hb else "DIFFERENT", "as filed" if agree else "NOT as filed"))
        rep.add(f"prediction pair {c} seed {s}: bytes identical and digests as filed", ha == hb and agree, ha)
    with open(os.path.join(out, "card_pairs_sha256.tsv"), "w", encoding="utf-8") as fh:
        fh.write("condition\tseed\trun_40GB\trun_80GB\tsha256_40GB\tsha256_80GB\tbytes\tvs_filed_results_add06\n")
        for r in rows:
            fh.write("\t".join(map(str, r)) + "\n")
    rep.note(f"    identical prediction pairs: {n_same} of {len(pairs)}")


def step_gate(rep, out):
    g = os.path.join(SC, "kais_v4", "audit_out", "runtime_gate")
    rows = []
    for tag in ("pass1_seed42", "pass2_seed1337"):
        m = json.load(open(os.path.join(g, f"runtime_gate_meta_{tag}.json")))
        rows.append((f"meta {tag}", m["sum_has_box"], m["eligible_rows_in_bank"], m["sum_has_cls"], m["labels_iterated"]))
    txt = open(os.path.join(g, "runtime_gate_analysis.txt"), encoding="utf-8").read()
    for i, m in enumerate(re.finditer(r"ADMITTED\s+(\d+)\s+REJECTED\s+(\d+)\s+of\s+(\d+)", txt), 1):
        rows.append((f"summary pass {i}", int(m.group(1)), int(m.group(3)), "", ""))
    with open(os.path.join(out, "gate_counts.tsv"), "w", encoding="utf-8") as fh:
        fh.write("source\tadmitted\teligible_rows\tadmitted_with_class_term\tlabels_iterated\n")
        for r in rows:
            fh.write("\t".join(map(str, r)) + "\n")
    ok = len(rows) == 4 and len({(r[1], r[2]) for r in rows}) == 1
    rep.add("run-time gate: summary and meta files give one admitted/eligible count for both passes", ok,
            f"admitted {rows[0][1]} of {rows[0][2]}" if ok else str(rows))
    rep.note("    (read from the summary; the per-row files that produce it are not in the bundle)")


def step_counts(rep, out):
    root = os.path.join(SC, "models", "students")
    rows = []
    for r in sorted(os.listdir(root)):
        p = [f for f in os.listdir(os.path.join(root, r)) if f.endswith("_run_summary.json")]
        if not p:
            continue
        s = json.load(open(os.path.join(root, r, p[0])))
        vl = s.get("view_list", [])
        kd_ep = sum(1 for v in vl if v != "human_only")
        box = s.get("kd_matches_box")
        rows.append((r, len(vl), s.get("optimizer_steps"), box, s.get("kd_matches_cls"),
                     round(box / kd_ep, 2) if kd_ep and box is not None else ""))
    with open(os.path.join(out, "current_kd_match_counts.tsv"), "w", encoding="utf-8") as fh:
        fh.write("run\tepochs\toptimizer_steps\tkd_matches_box\tkd_matches_cls\tbox_per_kd_epoch\n")
        for r in rows:
            fh.write("\t".join(map(str, r)) + "\n")
    rep.note(f"WROTE    current_kd_match_counts.tsv ({len(rows)} runs; same columns as the filed historical table, "
             "which itself covers earlier runs whose summaries are not in the bundle)")
    # admission logs of the masked runs: admitted rows per pass over the training set
    logs = os.path.join(SC, "kais_v4", "logs")
    for f in sorted(x for x in os.listdir(logs) if x.endswith(".admission.jsonl")):
        recs = [json.loads(x) for x in open(os.path.join(logs, f), encoding="utf-8") if x.strip()]
        first = recs[0]
        rep.note(f"    {f}: first record calls={first['calls']} has_box={first['has_box']} labels={first['labels']}; "
                 f"last calls={recs[-1]['calls']} has_box={recs[-1]['has_box']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(BUNDLE, "_test_out"))
    ap.add_argument("--keep-view", action="store_true")
    ap.add_argument("steps", nargs="*")
    args = ap.parse_args()
    steps = args.steps or ["digests", "order", "add06", "a04", "pairs", "gate", "counts"]
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    rep = Report(os.path.join(out, "RECOMPUTE_REPORT.txt"))
    import numpy, scipy
    rep.note(f"python {sys.version.split()[0]}  numpy {numpy.__version__}  scipy {scipy.__version__}")
    view = os.path.join(out, "eval_view")
    runs = build_view(view)
    rep.note(f"eval view: {len(runs)} runs (metrics_unified.json from scrubbed/, predictions.json from as_filed/)")
    try:
        if "digests" in steps: step_digests(rep, out)
        if "order" in steps: run_filed(rep, out, "order", [view])
        if "add06" in steps: run_filed(rep, out, "add06", [view])
        if "a04" in steps: run_filed(rep, out, "a04", [os.path.join(AN, "a04_draws"), view])
        if "pairs" in steps: step_pairs(rep, out)
        if "gate" in steps: step_gate(rep, out)
        if "counts" in steps: step_counts(rep, out)
    finally:
        if not args.keep_view:
            shutil.rmtree(view, ignore_errors=True)
    rep.note(f"comparisons that differ: {rep.bad}")
    rep.write()
    sys.exit(1 if rep.bad else 0)


if __name__ == "__main__":
    main()
