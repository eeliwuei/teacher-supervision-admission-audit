#!/usr/bin/env python3
"""KAIS v4 Addendum 06: same-card sensitivity analysis of the mechanism experiment and descriptive card pairs.
Written before any Addendum-06 run had started. Does not replace analyze_kaisv4.py (Addendum 03 analysis unchanged).
Usage: analyze_add06.py <eval_root (eval/factorial_v3_freeze)> <out.json>
Card of each run (from the training logs): 80GB = fixall, oldmask at all seeds, randmask at seeds 42 and 1337, and all
'-c80' runs; 40GB = std and nokd of Addendum 03 at all seeds, randmask at seed 20260703."""
import sys, json, math, hashlib
from pathlib import Path
import numpy as np
from scipy import stats
S = [42, 1337, 20260703]; CL = ["knife", "gun", "stick"]; BAND = 0.01
def mech(mode, s): return f"C1-M-{mode}_seed{s}_kaisv4mech"
def std40(s): return mech("std", s) if s != 20260703 else f"C1-M_seed{s}_kaisv4"
def nokd40(s): return f"C0-R-std_seed{s}_kaisv4mech" if s != 20260703 else f"C0-R_seed{s}_kaisv4"
def std80(s): return f"C1-M-std-c80_seed{s}_kaisv4mech"
def nokd80(s): return f"C0-R-std-c80_seed{s}_kaisv4mech"
def rand80(s): return mech("randmask", s) if s != 20260703 else "C1-M-randmask-c80_seed20260703_kaisv4mech"
def fixall(s): return mech("fixall", s)
def oldmask(s): return mech("oldmask", s)
def main():
    root, outp = Path(sys.argv[1]), Path(sys.argv[2]); cache = {}
    def rec(run):
        if run not in cache: cache[run] = json.loads((root / run / "metrics_unified.json").read_text())
        return cache[run]
    def val(run, key="mAP"): return float(rec(run)["mAP"] if key == "mAP" else rec(run)["per_class"][key])
    def paired(d):
        d = np.asarray(d, float); n = len(d); m = d.mean(); sd = d.std(ddof=1); se = sd / math.sqrt(n)
        tq = stats.t.ppf(0.975, n - 1)
        return {"per_seed": d.tolist(), "mean": float(m), "sd": float(sd), "ci95": [float(m - tq * se), float(m + tq * se)],
                "same_sign": bool(np.all(d > 0) or np.all(d < 0))}
    def guard(f):
        try: return f()
        except FileNotFoundError as e: return {"not_available": str(e)}
    def diff(a, b, key="mAP", seeds=S): return paired([val(a(s), key) - val(b(s), key) for s in seeds])
    def label(r):
        lo, hi = r["ci95"]
        return ("consistent difference" if (r["same_sign"] and abs(r["mean"]) >= BAND) else
                "no detectable difference at this precision" if (-BAND <= lo and hi <= BAND) else "inconclusive")
    # same-card contrasts: every run on the 80GB card
    QS = {"Q1s": (fixall, nokd80), "Q3s": (oldmask, rand80), "Q4s": (rand80, fixall), "Q5s": (std80, oldmask), "Q6s": (std80, fixall)}
    def qs(name):
        a, b = QS[name]; r = diff(a, b); r["per_class"] = {c: diff(a, b, c) for c in CL}
        if name == "Q3s": r["label_rule_applied_for_sensitivity_only"] = label(r)
        return r
    out = {"band": BAND, "same_card_80GB": {n: guard(lambda n=n: qs(n)) for n in QS}}
    # two-seed same-card subsets of the Addendum-03 runs (no new run involved): seeds 42 and 1337
    out["two_seed_subset_seeds_42_1337"] = {
        "Q3": guard(lambda: {str(s): val(oldmask(s)) - val(mech("randmask", s)) for s in (42, 1337)}),
        "Q4": guard(lambda: {str(s): val(mech("randmask", s)) - val(fixall(s)) for s in (42, 1337)})}
    # card pairs: same configuration and seed, endpoint on the 40GB card minus endpoint on the 80GB card
    pairs = [("std", s, std40(s), std80(s)) for s in S] + [("nokd", s, nokd40(s), nokd80(s)) for s in S] + \
            [("randmask", 20260703, mech("randmask", 20260703), rand80(20260703))]
    def pair(c, s, a, b):
        def psha(run):
            p = root / run / "predictions.json"
            return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        ha, hb = psha(a), psha(b)
        return {"condition": c, "seed": s, "run_40GB": a, "run_80GB": b, "mAP_40GB": val(a), "mAP_80GB": val(b),
                "diff_40_minus_80": val(a) - val(b), "per_class_diff": {k: val(a, k) - val(b, k) for k in CL},
                "predictions_sha256_40GB": ha, "predictions_sha256_80GB": hb,
                "predictions_identical": None if None in (ha, hb) else ha == hb,
                "launcher_differs": bool(s == 20260703 and c in ("std", "nokd"))}
    P = [guard(lambda t=t: pair(*t)) for t in pairs]
    out["card_pairs"] = P
    ok = [p["diff_40_minus_80"] for p in P if "diff_40_minus_80" in p]
    if len(ok) == len(pairs):
        d = np.asarray(ok); out["card_pairs_summary"] = {"n": len(ok), "mean": float(d.mean()), "sd": float(d.std(ddof=1)),
            "min": float(d.min()), "max": float(d.max()), "max_abs": float(np.abs(d).max()),
            "mean_abs": float(np.abs(d).mean()), "n_identical_predictions": int(sum(p["predictions_identical"] is True for p in P)),
            "n_predictions_not_available": int(sum(p["predictions_identical"] is None for p in P))}
    runs = sorted({f(s) for s in S for f in (std40, nokd40, std80, nokd80, rand80, fixall, oldmask, lambda s: mech("randmask", s))})
    out["endpoints"] = {r: guard(lambda r=r: {"mAP": val(r), **{c: val(r, c) for c in CL}}) for r in runs}
    outp.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
if __name__ == "__main__":
    main()
