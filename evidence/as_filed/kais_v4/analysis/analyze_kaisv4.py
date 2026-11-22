#!/usr/bin/env python3
"""Seed-based analyses of the frozen protocol, Addendum 01 and Addendum 03 (fixed before any run finished).
Usage: analyze_kaisv4.py <eval_root> <out_json>      Reads <eval_root>/<run>/metrics_unified.json only.
Protocol: primary contrast and decision; three baseline contrasts; two-way ANOVA of the shuffled grid.
Addendum 01: paired-t p-values with Holm (A1); crossed-random-factor interval (A2); concurrent replicates (A3).
Addendum 03: Q1..Q6 with the reading rule for Q2 and Q3; per-class AP for every contrast."""
import sys, json, math
from pathlib import Path
import numpy as np
from scipy import stats
S = [42, 1337, 20260703]; SH = [4, 5, 6, 7]; THR = 0.0171; BAND = 0.01
CL = ["knife", "gun", "stick"]
def k4(mid, s): return f"{mid}_seed{s}_kaisv4"
def mech(mode, s): return f"C1-M-{mode}_seed{s}_kaisv4mech"
def c4_reused(s): return f"F-MonoSingle_seed{s}_v3factorial_intpad" if s != 20260703 else k4("C4-M", s)
def std(s): return mech("std", s) if s != 20260703 else k4("C1-M", s)
def nokd(s): return f"C0-R-std_seed{s}_kaisv4mech" if s != 20260703 else k4("C0-R", s)
def main():
    root, outp = Path(sys.argv[1]), Path(sys.argv[2]); cache = {}
    def rec(run):
        if run not in cache: cache[run] = json.loads((root / run / "metrics_unified.json").read_text())
        return cache[run]
    def val(run, key="mAP"): return float(rec(run)["mAP"] if key == "mAP" else rec(run)["per_class"][key])
    def paired(d):
        d = np.asarray(d, float); n = len(d); m = d.mean(); sd = d.std(ddof=1); se = sd / math.sqrt(n)
        tq = stats.t.ppf(0.975, n - 1); t = m / se if se > 0 else (math.copysign(1e308, m) if m else 0.0)
        p = float(2 * stats.t.sf(abs(t), n - 1)) if se > 0 else (0.0 if m else 1.0)
        return {"per_seed": d.tolist(), "mean": float(m), "sd": float(sd), "ci95": [float(m - tq * se), float(m + tq * se)],
                "t": float(t), "p_two_sided": p, "same_sign": bool(np.all(d > 0) or np.all(d < 0))}
    def guard(f):
        try: return f()
        except FileNotFoundError as e: return {"not_available": str(e)}
    out = {"threshold": THR, "band": BAND}
    def primary(c4):
        d = [val(c4(s)) - np.mean([val(k4(f"F-ShufSingle-s{k}", s)) for k in SH]) for s in S]
        r = paired(d); lo, hi = r["ci95"]
        r["decision"] = ("advantage" if r["mean"] > THR else
                         "no detectable order effect at +/-0.01" if (-BAND <= lo and hi <= BAND) else "inconclusive")
        return r
    out["primary_frozen"] = guard(lambda: primary(c4_reused))
    def sens(r):
        if "decision" in r: r["rule_applied_for_sensitivity_only"] = r.pop("decision")
        return r
    out["primary_concurrent_A3"] = guard(lambda: sens(primary(lambda s: k4("C4-M", s))))
    def diff(a, b, key="mAP"): return paired([val(a(s), key) - val(b(s), key) for s in S])
    base = {"C1-M - C0-R": (lambda s: k4("C1-M", s), lambda s: k4("C0-R", s)),
            "C1-M - CBox-M": (lambda s: k4("C1-M", s), lambda s: k4("CBox-M", s)),
            "C4-M - C1-M": (c4_reused, lambda s: k4("C1-M", s))}
    def holm_family():
        r = {n: diff(a, b) for n, (a, b) in base.items()}
        order = sorted(r, key=lambda n: r[n]["p_two_sided"]); m = len(order); run = 0.0
        for i, n in enumerate(order):
            run = max(run, min(1.0, (m - i) * r[n]["p_two_sided"])); r[n]["p_holm"] = run
        return r
    out["baseline_contrasts"] = guard(holm_family)
    out["C4-M - C1-M concurrent_A3"] = guard(lambda: diff(lambda s: k4("C4-M", s), lambda s: k4("C1-M", s)))
    out["reused_minus_concurrent"] = guard(lambda: {str(s): val(c4_reused(s)) - val(k4("C4-M", s)) for s in (42, 1337)})
    def twoway(Y):   # rows = schedules (4), cols = seeds (3)
        Y = np.asarray(Y, float); a, b = Y.shape; g = Y.mean()
        ssa = b * ((Y.mean(1) - g) ** 2).sum(); ssb = a * ((Y.mean(0) - g) ** 2).sum()
        sse = ((Y - Y.mean(1, keepdims=True) - Y.mean(0, keepdims=True) + g) ** 2).sum()
        dfa, dfb, dfe = a - 1, b - 1, (a - 1) * (b - 1)
        return g, ssa / dfa, ssb / dfb, sse / dfe, dfa, dfb, dfe
    def anova():
        Y = [[val(k4(f"F-ShufSingle-s{k}", s)) for s in S] for k in SH]
        g, msa, msb, mse, dfa, dfb, dfe = twoway(Y)
        return {"grid": Y, "grand_mean": g, "MS_schedule": msa, "MS_seed": msb, "MS_residual": mse,
                "df": [dfa, dfb, dfe], "var_schedule": (msa - mse) / 3, "var_seed": (msb - mse) / 4, "var_residual": mse,
                "note": "variance components by the method of moments; negative estimates reported as computed"}
    out["shuffled_grid_anova"] = guard(anova)
    def crossed(c4):
        Y = [[val(c4(s)) - val(k4(f"F-ShufSingle-s{k}", s)) for s in S] for k in SH]
        g, msa, msb, mse, dfa, dfb, dfe = twoway(Y); num = msa + msb - mse
        if num <= 0: return {"grand_mean": g, "interval": "not available (MS_schedule + MS_seed - MS_residual <= 0)", "MS": [msa, msb, mse]}
        se = math.sqrt(num / 12); df = num ** 2 / (msa ** 2 / dfa + msb ** 2 / dfb + mse ** 2 / dfe); tq = stats.t.ppf(0.975, df)
        return {"grand_mean": g, "se": se, "df_satterthwaite": df, "ci95": [g - tq * se, g + tq * se], "MS": [msa, msb, mse]}
    out["crossed_A2_frozen"] = guard(lambda: crossed(c4_reused))
    out["crossed_A2_concurrent"] = guard(lambda: crossed(lambda s: k4("C4-M", s)))
    Q = {"Q1": (lambda s: mech("fixall", s), nokd), "Q2": (lambda s: mech("oldmask", s), lambda s: mech("fixall", s)),
         "Q3": (lambda s: mech("oldmask", s), lambda s: mech("randmask", s)),
         "Q4": (lambda s: mech("randmask", s), lambda s: mech("fixall", s)), "Q5": (std, lambda s: mech("oldmask", s)),
         "Q6": (std, lambda s: mech("fixall", s))}
    def q(name):
        a, b = Q[name]; r = diff(a, b); r["per_class"] = {c: diff(a, b, c) for c in CL}
        if name in ("Q2", "Q3"):
            lo, hi = r["ci95"]
            r["label"] = ("consistent difference" if (r["same_sign"] and abs(r["mean"]) >= BAND) else
                          "no detectable difference at this precision" if (-BAND <= lo and hi <= BAND) else "inconclusive")
            r["ci95_includes_zero"] = bool(lo <= 0 <= hi)
        return r
    out["mechanism"] = {n: guard(lambda n=n: q(n)) for n in Q}
    names = sorted({f(s) for s in S for f in [c4_reused, std, nokd, lambda s: k4("C4-M", s), lambda s: k4("C1-M", s),
             lambda s: k4("C0-R", s), lambda s: k4("CBox-M", s)] + [lambda s, m=m: mech(m, s) for m in ("fixall", "oldmask", "randmask")]
             + [lambda s, k=k: k4(f"F-ShufSingle-s{k}", s) for k in SH]})
    out["endpoints"] = {n: guard(lambda n=n: {"mAP": val(n), **{c: val(n, c) for c in CL}, "checkpoint_sha256": rec(n).get("checkpoint_sha256")}) for n in names}
    outp.write_text(json.dumps(out, indent=1, default=float))
if __name__ == "__main__":
    main()
