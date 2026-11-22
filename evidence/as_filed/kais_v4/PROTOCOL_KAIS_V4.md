# LP-CCAD follow-up v4 (KAIS revision): protocol fixed before any v4 training run

Written 2026-11-10 (UTC), before the first v4 run was started. No v4 outcome existed when this file was written.

## Fixed inputs (unchanged from the corrected-pipeline follow-up of July 2026)
- Code: tools/ccad as on disk since 2026-07-21 (integer letterbox padding). ccad_dataset_adapter.py sha256 caea921e94f11467721e7aa223fe6760e0c9b67f2736410aadf20ac39b1ac118.
- Data ccad_v2 splits, evidence bank selected_best_stg1_v2 (sha256 eca4969b...b9cbc), protocol sha 1f4372dc...c2e1.
- Hyperparameters: yolo26n, 150 epochs, batch 16, imgsz 960, AMP, temperature 1.0, lambda_box 0.45423083821737265, lambda_cls 0.4613535884454487, save-period 5.
- Training seeds: 42, 1337, 20260703 (the three seeds of every earlier stage). No seed is added or dropped.

## Runs (22)
A. Schedule-by-seed crossing: four new shuffled-head/single-tail schedules F-ShufSingle-s4..s7 (schedule seeds 20261725..20261728, the continuation of the v3 rule; file phase4_view_schedules_v4_kais_shuffled.yaml, sha256 82769c508af610521e97ee2a26fc05a3949f8c5a4ca4f1dab710cf16cfd91a9b), each trained at all three seeds: 12 runs.
B. Concurrent baselines from phase4_view_schedules_v1.yaml (sha256 090d4829...c414), each at all three seeds: C0-R (no KD), CBox-M (box KD only), C1-M (box + class KD, full view every epoch): 9 runs.
C. Monotone reference C4-M: the existing integer-padding runs F-MonoSingle_seed{42,1337}_v3factorial_intpad are reused for seeds 42 and 1337 (their outcomes were known before this protocol). For seed 20260703 one new C4-M run is trained on the second machine: 1 run.

## Machines
Seeds 42 and 1337: H100 server (one H100), stock environment (torch 2.6.0+cu124, ultralytics 8.4.24).
Seed 20260703: server r7525 (A100), separate environment pinned to the same package versions.
Every contrast below is computed within seed, so no contrast compares runs from different machines. Machine is aliased with the seed block and is not separately identified. The existing H100 run F-MonoSingle_seed20260703 is not used in any contrast; it is reported next to the new A100 run of the same arm and seed as a descriptive cross-machine pair.

## Endpoint and checkpoint rule
Validation split (2,827 images), COCO mAP50-95, unified evaluator (factorial_freeze_eval.py, faster-coco-eval), final EMA checkpoint after epoch 150 (last.pt after the chain log records DONE rc=0). The validation-selected checkpoint is reported as a sensitivity analysis only. The internal evaluation split is not blind (its labels were consulted during development); values on it (all 2,553 images and the 2,019-image subset) are reported as non-independent sensitivity records and decide nothing.

## Primary comparison (one)
Order contrast per seed s: d_s = mAP(C4-M, s) - mean over the four new schedules k of mAP(F-ShufSingle-sk, s). Estimate: mean of d_s over the three seeds, with a descriptive paired-t 95% interval (2 df). Decision rule, unchanged from the project: the monotone schedule is credited with an advantage only if the mean exceeds the frozen threshold 0.0171; an interval inside +-0.01 is described as no detectable order effect at that margin; anything else is inconclusive.

## Secondary analyses (Holm over the three baseline contrasts)
1. KD vs none: C1-M - C0-R. 2. Class-KD increment: C1-M - CBox-M. 3. Curriculum increment: C4-M - C1-M. Each per seed, mean, descriptive interval.
4. Variance components of the 4 x 3 shuffled grid (schedule draw, seed, residual), by two-way ANOVA without replication; reported descriptively. This addresses whether seed replication can stand in for schedule replication.
5. Per-class AP for every run; admitted teacher-evidence counts are static (9,334 of 9,334 under integer padding) and are not re-estimated per run.
Exploratory, labelled as such: the three v3 schedules F-ShufSingle-s1..s3 (one seed each, outcomes already known) shown alongside the new grid.

## Stopping and exclusions
All 22 runs are reported. A run is repeated only if it stops before epoch 150 for a technical reason (rc != 0); the failed attempt is listed. No run is excluded on the basis of its metric.
