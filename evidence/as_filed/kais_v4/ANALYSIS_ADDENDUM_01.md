# KAIS v4 — Analysis addendum 01 (post-freeze, pre-outcome)

This addendum does NOT modify PROTOCOL_KAIS_V4.md (sha256 0b8ccde0ee07aac9cb2cf1f31aba00ad725a88639d221c304daa83bdb5b715b1).
The frozen primary analysis and its decision rule stand as written. Everything below was decided after the freeze
and after training started, and must be reported as such.

## Status when this addendum was filed
- 0 of 22 runs had finished: no chain log contained a DONE line; the runs were between epoch 19 and epoch 23 of 150.
- No unified evaluation of any kais_v4 run had been performed.
- The training logs contain per-epoch validation metrics of the unfinished runs. They were visible while monitoring
  progress (speed, tracebacks); no number from them was used for any choice below.

## A1. Test used for the three Holm-adjusted secondary contrasts
The protocol fixes the family (C1-M - C0-R, C1-M - CBox-M, C4-M - C1-M) but not the test. Choice: two-sided paired t
test on the three per-seed differences (2 df); Holm adjustment over the three; raw and adjusted p reported without a
significance cut-off. Reported as not pre-specified.

## A2. Scope of the primary interval, and a crossed sensitivity analysis
The primary interval (mean over 3 seeds of d_s, where d_s averages the four new schedules) describes seed-to-seed
variation conditional on the four drawn schedules. It does not carry the uncertainty of redrawing schedules and does
not by itself support a statement about the shuffled single-tail family.
Sensitivity analysis (not pre-specified, does not change the frozen decision): with y_ks = mAP(C4-M, s) - mAP(shuf_k, s)
on the 4 x 3 grid, treat schedule draw and seed as crossed random factors. Report the grand mean with
SE^2 = (MS_schedule + MS_seed - MS_residual) / 12, Satterthwaite degrees of freedom, and the resulting 95% interval,
next to the frozen interval. If MS_schedule + MS_seed - MS_residual <= 0, report that the estimate is not available
rather than truncating silently. Note that the seed mean square of y includes the seed variation of the C4-M reference.

## A3. Concurrent replicates of the two reused C4-M reference runs
The protocol reuses F-MonoSingle_seed{42,1337}_v3factorial_intpad (trained July 2026 on H100). To test whether reuse
matters, two additional runs are added: C4-M_seed42_kaisv4 and C4-M_seed1337_kaisv4, same launcher (run_v4_common.sh),
same machine (H100, device 0), queued as lane h100_L6 to start when lane h100_L5 ends. Total new training runs: 24.
Use: sensitivity only. The primary contrast and the C4-M - C1-M contrast are recomputed with the concurrent runs in
place of the reused ones and shown next to the frozen analysis, which keeps the reused runs. The reused-vs-concurrent
difference at each seed is reported in full, whatever its size. Rerun only on technical failure (rc != 0).

## A4. Difference from the historical decision rule (to be stated in the paper)
Historical rule: per-seed differences of the same sign AND absolute mean >= the project threshold (about 0.0171).
Frozen v4 rule: advantage only if the mean of d_s exceeds +0.0171 (one direction, no same-sign condition), plus an
interval rule against +/-0.01 for "no detectable order effect", else inconclusive. Only the threshold value is shared.

## A5. Checkpoint provenance
For every analysed run record: selection metric of best.pt, selected epoch, tie-break, whether weights are EMA,
and sha256 of the scored final and validation-selected checkpoint files.
