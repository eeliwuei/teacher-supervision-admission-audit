# KAIS v4 — Addendum 02: restart of the seed-20260703 block (pre-outcome)

Does NOT modify PROTOCOL_KAIS_V4.md (sha256 0b8ccde0ee07aac9cb2cf1f31aba00ad725a88639d221c304daa83bdb5b715b1).

## What was found
A comparability audit on 2026-11-10 found that the Python environment built for the r7525 machine
(envs/ccad_yolo26n_r7525) did not contain the albumentations package. Ultralytics skips its albumentations
transforms silently when the import fails. The H100 environment has albumentations 2.0.8 and applies
Blur, MedianBlur, ToGray and CLAHE, each with p=0.01; the July reference runs did the same. The eight r7525 runs
(all at seed 20260703, started 2026-11-10T01:14:33Z) were therefore training with a pipeline that differed from the
other two seed blocks. This is an environment construction error, not an outcome-dependent event.

## Status when this decision was taken
- 0 of the 22 pre-specified runs had finished; the eight r7525 runs were at about epoch 21 of 150.
- No kais_v4 run had been evaluated. No validation metric of the affected runs was consulted for this decision.
- Decision taken by the corresponding author on 2026-11-10 after being shown the audit finding and three options
  (restart now; continue and disclose; continue and add a corrected block later).

## Action
1. Stop the eight r7525 runs. Keep their directories and logs, renamed with suffix _ABORTED_noalb; they are not
   evaluated and enter no analysis.
2. Install into envs/ccad_yolo26n_r7525, with --no-deps, the versions present on H100: albumentations 2.0.8,
   albucore 0.0.24, pydantic 2.13.4, pydantic_core 2.46.4, simsimd 6.5.16, stringzilla 4.6.2, annotated-types 0.6.0,
   typing-inspection 0.4.2. No other package is changed.
3. Restart the same eight runs from scratch with the same launcher, names, seeds and GPU assignment
   (GPU2: F-ShufSingle-s4..s7 and C4-M; GPU0: C0-R, CBox-M, C1-M), chain tags r7525b_*.
4. Each restarted log must show the "albumentations:" line with the four transforms before the run counts.
The protocol's rule "rerun only on technical failure" is read here as covering an environment error found before any
outcome; this reading is disclosed in the paper as a deviation.

## Still different between machines (disclosed, not changed)
GPU models (H100 PCIe vs A100 80GB / A100 40GB within the r7525 block), drivers, and an isolated venv on r7525 versus
a venv with system site-packages on H100. Each contrast in the protocol remains within one machine and one seed.
