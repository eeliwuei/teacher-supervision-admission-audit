# KAIS v4 — Addendum 05: launcher error in the CBox-M arm, found after outcomes; corrected reruns (deviation record)

Does NOT modify PROTOCOL_KAIS_V4.md (sha256 0b8ccde0ee07aac9cb2cf1f31aba00ad725a88639d221c304daa83bdb5b715b1) or
Addenda 01-04. It records a deviation and how it is handled. Unlike the earlier addenda, it was written AFTER
outcomes had been seen, and the error it records was discovered FROM outcomes. Decided by the corresponding
author on 2026-11-11 after being shown the finding and three options (rerun as the protocol defines the arm; drop
the contrast; wait).

## What was found
The protocol defines CBox-M as box distillation only and the contrast C1-M - CBox-M as the class-KD increment.
The launcher written for this experiment (run_v4_common.sh, sha256
395d1e32009b77dcc9dc62999e01787652b5a2dcd51d22999148d2e5c64a87d4) passes --lambda-cls 0.4613535884454487 for every
arm. In the schedule file CBox-M and C1-M are the same list (the full view at all 150 epochs); the historical
CBox-M runs were box-only because their launcher passed --lambda-cls 0.0 (their run summaries record lambda_cls 0.0
and kd_matches_cls 0). The run CBox-M_seed20260703_kaisv4 was therefore trained with class distillation on, with
the configuration of C1-M. Its run summary records lambda_cls 0.4613535884454487 and kd_matches_cls 939,746.
This is an error of the launcher, made by the analyst who wrote it, and was not caught by any check before launch.

## How and when it was found
On 2026-11-11 at about 16:30 UTC the second batch of endpoint evaluations was run (C1-M and CBox-M at seed
20260703). Both runs returned the same mAP50-95 (0.3823291309794702) and the same per-class AP, and their
prediction files have the same sha256 (4673ccf9...). The equality prompted the inspection that found the cause.
Outcomes seen at that time: the unified endpoints of C1-M, the four shuffled schedules at seed 42, of C0-R, C1-M and
the wrongly configured CBox-M at seed 20260703, and the two reused C4-M endpoints. No correctly configured CBox-M
run of this experiment existed, so no C1-M - CBox-M difference had been seen. The discovery is nevertheless
outcome-dependent and is to be reported as such.

## Handling
1. The wrongly configured run is kept and set aside: its model directory, log and evaluation directory are renamed
   with the suffix _INVALID_clskd. It is not a CBox-M run, enters no contrast as CBox-M, and is reported. Its only
   use is the observation in "Side observation" below.
2. Corrected launcher run_v4_cbox.sh: identical to run_v4_common.sh except that only CBox-M is accepted and
   --lambda-cls is 0.0 (sha256 410b7da4b0f4376319404e0ef21f7b3ccd026fe626ccb2bdcb1144d2fcef0138). All other
   arguments, the schedule file, the evidence bank, the seeds and the run names are unchanged.
3. CBox-M_seed20260703_kaisv4 is trained again from scratch with the corrected launcher on the same server and the
   same card as the invalid run and as the C1-M and C0-R runs of that seed (r7525, GPU 0, A100 40 GB).
4. The two CBox-M runs at seeds 42 and 1337 are queued inside lane scripts that are already running on H100 and
   cannot be changed in place. When a lane starts one of them, that single trainer process is stopped, its partial
   directory is renamed with the suffix _ABORTED_lambdacls and never evaluated, and the corrected run is started
   on the same card (script swap_cbox_h100.sh, sha256
   75a923e5b628d8bc8198c5886285793a95a5d577e8c65a761754a8e6300a916d).
5. Manipulation check for every corrected run, required before it counts: its run summary must record
   lambda_cls 0.0 and kd_matches_cls 0, and kd_matches_box consistent with 6,434 rows per epoch. A corrected run
   that fails this check is reported and not used.
6. The analysis is unchanged: the contrast C1-M - CBox-M and the Holm family are computed as specified, from the
   corrected runs. The paper reports this deviation, the fact that it was found after outcomes, and the endpoint of
   the invalid run.
The protocol's rule "rerun only on technical failure" is read as covering a run that did not implement its arm;
this reading is disclosed.

## Check of the other arms for the same error (done now, from run summaries and launch scripts)
C0-R: the schedule is human-only, so the trainer sets both distillation terms to zero; the finished run records
kd_matches_box 0 and kd_matches_cls 0. C1-M, C4-M and the shuffled schedules are meant to have class distillation
on. The mechanism launcher (run_mech.sh) uses C1-M and C0-R only. No other arm of either experiment is box-only.

## Side observation (not planned, descriptive)
Because the invalid run had exactly the configuration and seed of C1-M_seed20260703_kaisv4 and ran on the same
card at the same time, the two are an unplanned exact replicate. Their prediction files are identical. Training
with this code was therefore bit-reproducible in that one instance on that card. Nothing is inferred about other
cards, other seeds, or runs months apart.
