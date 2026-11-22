#!/usr/bin/env python3
"""Addendum 04 contrasts from per-model draws. Usage: a04_contrasts.py <draws_dir> <eval_root> <out_json>
Writes, per contrast: dbar on the original split, mean and SD over defined draws, 2.5/97.5 percentiles
(numpy.percentile, method 'linear'), undefined draws, and the sentence(s) fixed in the addendum.
B1..B3 are the addendum's H1..H3."""
import sys, json
from pathlib import Path
import numpy as np
S = [42, 1337, 20260703]
def k4(mid, s): return f"{mid}_seed{s}_kaisv4"
def mech(mode, s): return f"C1-M-{mode}_seed{s}_kaisv4mech"
def c4_reused(s): return f"F-MonoSingle_seed{s}_v3factorial_intpad" if s != 20260703 else k4("C4-M", s)
def c4_conc(s): return k4("C4-M", s)
def std(s): return mech("std", s) if s != 20260703 else k4("C1-M", s)
def nokd(s): return f"C0-R-std_seed{s}_kaisv4mech" if s != 20260703 else k4("C0-R", s)
SHUF = [f"F-ShufSingle-s{k}" for k in (4, 5, 6, 7)]
# contrast -> per seed list of (weight, run)
def P(c4): return [[(1.0, c4(s))] + [(-0.25, k4(m, s)) for m in SHUF] for s in S]
def D(a, b): return [[(1.0, a(s)), (-1.0, b(s))] for s in S]
CON = {
 "P": P(c4_reused), "P'": P(c4_conc),
 "B1": D(lambda s: k4("C1-M", s), lambda s: k4("C0-R", s)),
 "B2": D(lambda s: k4("C1-M", s), lambda s: k4("CBox-M", s)),
 "B3": D(c4_reused, lambda s: k4("C1-M", s)), "B3'": D(c4_conc, lambda s: k4("C1-M", s)),
 "Q1": D(lambda s: mech("fixall", s), nokd), "Q2": D(lambda s: mech("oldmask", s), lambda s: mech("fixall", s)),
 "Q3": D(lambda s: mech("oldmask", s), lambda s: mech("randmask", s)),
 "Q4": D(lambda s: mech("randmask", s), lambda s: mech("fixall", s)), "Q5": D(std, lambda s: mech("oldmask", s)),
}
COLS = ["mAP50-95", "knife", "gun", "stick"]
def sentences(lo, hi):
    out = []
    if -0.01 <= lo and hi <= 0.01:
        out.append("For these trained models, the central 95% of the mean differences obtained by resampling the validation images lay within +/-0.01.")
    if (lo > 0 and hi > 0) or (lo < 0 and hi < 0):
        out.append("For these trained models, the central 95% of the resampled mean differences excluded zero.")
    if not out:
        out.append("For these trained models, the central 95% of the resampled mean differences included zero and extended beyond +/-0.01.")
    return [s + " This interval contains no seed-to-seed variation and does not describe other training runs." for s in out]
def main():
    dd, er, outp = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    def draws(run):
        v = json.loads((dd / f"{run}.verify.json").read_text())
        if not (v["pass"] or v.get("draws_computed_with") == "reference"): raise KeyError(f"verification failed: {run}")
        a = np.load(dd / f"{run}.draws.npy")
        if a.shape != (2000, 4): raise KeyError(f"unexpected draws shape {a.shape}: {run}")
        return a
    def orig(run):
        r = json.loads((er / run / "metrics_unified.json").read_text())
        return np.array([r["mAP"]] + [r["per_class"][c] for c in COLS[1:]], dtype=float)
    res = {"contrasts": {}, "models": {}}
    runs = sorted({r for c in CON.values() for seed in c for _, r in seed})
    gts = set(); n_read = 0
    for r in runs:
        try:
            gts.add(json.loads((dd / f"{r}.verify.json").read_text())["gt_sha256"]); n_read += 1
        except Exception:
            pass
    res["n_models_expected"] = len(runs); res["n_models_with_verify"] = n_read; res["gt_sha256_distinct"] = len(gts)
    if n_read != len(runs) or len(gts) != 1:
        res["error"] = "analysis not run: all 39 models must have a verify.json and share one ground-truth sha256"
        outp.write_text(json.dumps(res, indent=1)); return
    for r in runs:
        try:
            a = draws(r); res["models"][r] = {"mAP_sd_over_draws": float(np.nanstd(a[:, 0], ddof=1))}
        except Exception as e:
            res["models"][r] = {"missing": str(e)}
    for name, con in CON.items():
        try:
            per_seed_draw = [sum(w * draws(r) for w, r in seed) for seed in con]     # 3 x (B,4)
            per_seed_orig = [sum(w * orig(r) for w, r in seed) for seed in con]
        except Exception as e:
            res["contrasts"][name] = {"not_reported": str(e)}; continue
        dbar_draw = np.mean(per_seed_draw, axis=0); dbar = np.mean(per_seed_orig, axis=0)
        ent = {}
        cols = range(4) if name.startswith("Q") else range(1)
        for c in cols:
            x = dbar_draw[:, c]; ok = ~np.isnan(x); und = int((~ok).sum())
            e = {"dbar_original": float(dbar[c]), "undefined_draws": und,
                 "per_seed_original": [float(v[c]) for v in per_seed_orig],
                 "per_seed_sd_over_draws": [float(np.nanstd(v[:, c], ddof=1)) for v in per_seed_draw]}
            if und > 0.01 * len(x):
                e["interval"] = "not established"
            else:
                lo, hi = np.percentile(x[ok], [2.5, 97.5], method="linear")
                e.update(mean_over_draws=float(x[ok].mean()), sd_over_draws=float(x[ok].std(ddof=1)), p2_5=float(lo), p97_5=float(hi))
                if c == 0: e["sentences"] = sentences(float(lo), float(hi))
            ent[COLS[c]] = e
        res["contrasts"][name] = ent
    outp.write_text(json.dumps(res, indent=1))
if __name__ == "__main__":
    main()
