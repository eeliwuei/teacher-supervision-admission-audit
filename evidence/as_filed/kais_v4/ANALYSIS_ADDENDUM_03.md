# KAIS v4 — Addendum 03: mechanism experiment on the admission gate (separate; specified before any of its runs)

Does NOT modify PROTOCOL_KAIS_V4.md (sha256 0b8ccde0ee07aac9cb2cf1f31aba00ad725a88639d221c304daa83bdb5b715b1) and
changes no run or analysis of the frozen protocol. It is an additional experiment decided by the corresponding
author on 2026-11-10, after the run-time gate audit and before any kais_v4 run had finished or been evaluated.
Its question arose from that audit; it was not a question of the original protocol and must not be presented as one.

## Question
The stock admission gate (IoU >= 0.999 between a mapped evidence box and the batch box) admits 6,434 of 9,334 eligible
teacher-evidence rows per epoch, always the same rows, unevenly by class, image shape and source
(audit_out/runtime_gate/). Rejected rows receive neither box nor class distillation.
(a) Does restoring the rejected rows change the endpoint? (b) Is the effect of the gate's selection different from
removing the same number of rows at random?

## Conditions (full-view distillation only, arm C1-M; no curriculum factor)
- std: stock script and stock mapping (the gate admits 6,434 rows).
- fixall: corrected mapping (per-axis scale with ceil, then integer padding, following the training library), all
  eligible rows available.
- oldmask: corrected mapping; only the 6,434 rows the stock gate admitted are available.
- randmask: corrected mapping; a random 6,434-row subset, drawn once per run with random.Random(training seed) from
  the sorted eligible keys, fixed for all epochs. No matching on class, source or shape.
- nokd: arm C0-R, stock script (no distillation).
A masked row is removed from the evidence index, so its label receives the human loss only, as after a gate rejection.
oldmask and randmask use the same corrected teacher targets as fixall; they differ from it only in which rows take part.
std and oldmask use the same rows; their teacher-box targets differ by the misregistration of the stock mapping
(largest edge offset between the stock-mapped matched box and the batch box, from the run-time audit CSV: of the 6,434 rows,
1,018 exceed 0.01 px and 237 exceed 0.25 px; maximum 0.69 px); class targets are identical.
Caveat: the distillation weights (lambda_box, lambda_cls) are the project's existing values, set while the stock gate was in
use; they are not re-tuned for conditions with more admitted rows.
Code (in memory patches; stock files not edited), kais_v4/ablation_fixmap/, sha256:
fixmap_patch.py c441d54fb0ad908a04843c69bee6a4234b51a3fef84688f330173f021a37d9d3
mech_patch.py 12942481045077459d36a5bc3375dc0a5b334bdf0bfd2e1fe427a309a80eebaa
train_mech.py c82a5a0c8309f9d54242d88ed1a0c959555c9d3233198a6830d467ea13a557cc
run_mech.sh b42c61a4d9d73a9365b7e4802950f5772a6dc521a2042988b6e8e8e89802b45a
old_gate_admitted_keys.json 09fe892008316799ee4c7ad88d07fde62ce633a269c294086c85546f23d7bbef
Verification before launch: two independent reviews with full passes of the real training dataloader on CPU
(audit_out/runtime_gate_fixmap/, audit_out/runtime_gate_mech/). Rows admitted per pass (with a class target):
std 6,434 (6,265); fixall 9,334 (9,110), minimum gate IoU 0.999992, mapped box within 0.0005 px of the batch box;
oldmask 6,434 (6,265), the same rows as std row for row; randmask 6,434 at each seed (6,277 / 6,274 / 6,280 for seeds
42 / 1337 / 20260703), overlapping the oldmask set in 4,447 / 4,406 / 4,414 rows. Masking never changed which row
matches which label. After the reviews two guards were added to mech_patch.py and train_mech.py (single-device
assertion, pinned key-file digest, process id and code digests in the logs); the kept-row sets were recomputed
afterwards and are identical (digests 615df2e6, 660f24e5, 9c87698f for the three random masks).
Not exercised before launch: GPU with mixed precision, validation, epochs beyond the first batches, resume.
The mask seed equals the training seed, so mask and initialisation vary together across seeds. The random masks
are unstratified and therefore differ from the old mask in composition, e.g. stick rows kept 357 / 344 / 353 against
243, square-image rows 1,207 / 1,189 / 1,188 against 1,743; this difference is the object of Q3.

## Runs: 13 new, all on r7525 (env envs/ccad_yolo26n_r7525 with albumentations 2.0.8), seeds 42, 1337, 20260703
- fixall, oldmask, randmask at all three seeds (9 runs): C1-M-<mode>_seed<seed>_kaisv4mech
- std at seeds 42 and 1337 (2 runs): C1-M-std_seed<seed>_kaisv4mech
- nokd at seeds 42 and 1337 (2 runs): C0-R-std_seed<seed>_kaisv4mech
- std and nokd at seed 20260703: the protocol's own r7525 runs C1-M_seed20260703_kaisv4 and C0-R_seed20260703_kaisv4.
Every contrast below is within one machine and one seed. Same training arguments as the protocol.
Launch: the three seed-20260703 runs first; the other ten when the protocol's r7525 block has finished.

## Endpoint and analysis
Endpoint: validation mAP50-95, final EMA checkpoint, unified evaluator, as in the protocol. Per-class AP (knife, gun,
stick) is reported for every contrast because stock admission is uneven by class (stick 243 of 506).
Contrasts, each as three per-seed differences, their mean and a paired-t 95% interval (2 df):
 Q1 distillation with complete supervision: fixall - nokd
 Q2 effect of the stock gate's selection:    oldmask - fixall
 Q3 structured versus random selection:       oldmask - randmask
 Q4 amount alone:                             randmask - fixall
 Q5 registration of the targets alone:        std - oldmask (same rows, same class targets; box targets differ by at most 0.69 px)
 Q6 the stock pipeline as a whole:            std - fixall (descriptive only; no label; per seed it equals Q2 + Q5)
Reading rule, fixed now, applied to Q2 and Q3 separately (descriptive labels, not confirmatory tests):
 - "consistent difference": all three per-seed differences have the same sign and |mean| >= 0.01;
 - "no detectable difference at this precision": the 95% interval lies inside [-0.01, +0.01];
 - otherwise "inconclusive".
With three seeds, "inconclusive" is the expected label for small effects; it is not evidence of absence.
Consequence for the paper, fixed now: the run-time admission finding is reported whatever the labels. A statement
that the gate's selection affects detector quality is made only under "consistent difference" for Q2; a statement that
the selection differs from random thinning only under "consistent difference" for Q3. No direction is presupposed;
the one historical float-versus-integer comparison did not favour the integer pipeline and proves nothing either way.
Manipulation checks from the admission logs and run summaries: fixall 9,334 rows admitted per epoch, oldmask and
randmask 6,434, std 6,434. A run whose log shows the condition was not in effect is reported as a failed manipulation
and rerun, with disclosure. Otherwise rerun only on technical failure (rc != 0). All 13 runs are reported.

## Not covered
Curriculum arms (whether the gate changes monotone-minus-shuffled is left for a later, separately specified step),
box-only distillation, masks matched on class or source, other thresholds than 0.999, other detectors or datasets,
the float-padding pipeline, the public test split. Seed is confounded with nothing here except run-to-run noise, but
the three seeds are few; generality beyond this pipeline is not claimed.
