# KAIS v4 — Addendum 06: same-card control runs for the mechanism experiment (added AFTER outcomes; sensitivity only)

Does NOT modify PROTOCOL_KAIS_V4.md (sha256 0b8ccde0ee07aac9cb2cf1f31aba00ad725a88639d221c304daa83bdb5b715b1) or
Addenda 01-05. It adds seven training runs and one sensitivity analysis to the mechanism experiment of Addendum 03.
The analysis of Addendum 03 (Q1-Q6, reading rule for Q2 and Q3, analyze_kaisv4.py) is unchanged and remains the
analysis of that experiment. Decided by the corresponding author on 2026-11-14.

## Why, and what was known when this was decided (outcome-dependent; disclose)
The 13 runs of Addendum 03 and the two protocol runs it reuses were placed on two different GPU models of the same
server (r7525): device 2, an NVIDIA A100 80GB PCIe, and device 0, an NVIDIA A100-PCIE-40GB. The placement was written
into the launch commands on 2026-11-10 (wave 1: device recorded in logs/mech_chain_mech_w1a/b/c.log; wave 2:
queue_wave2.sh) and is confirmed by the device line of each
training log:
- 80GB card: fixall and oldmask at seeds 42, 1337, 20260703; randmask at seeds 42 and 1337.
- 40GB card: std and nokd at seeds 42, 1337, 20260703 (at 20260703 the protocol runs C1-M and C0-R); randmask at
  seed 20260703.
Hence Q2 (oldmask - fixall) is within one card at every seed; Q3 and Q4 are within one card at seeds 42 and 1337 and
across cards at seed 20260703; Q1, Q5 and Q6 are across cards at every seed. No configuration was trained on both
cards, so a card effect can be neither estimated nor excluded from the Addendum-03 runs.
Addendum 03 states that every contrast is within one machine and one seed. That remains true for the server;
Addendum 03 did not record or consider that the server's two usable cards are of different models.
This addendum was prompted by a reader's comment on the manuscript draft that pointed out this confound, and it was
decided AFTER the following outcomes had been seen (unified validation endpoints):
- mechanism experiment: fixall, oldmask, randmask at seed 20260703; std at seeds 42 and 1337; nokd at seed 42; the
  two protocol runs C1-M and C0-R at seed 20260703. Single-seed values of Q1-Q6 at seed 20260703 were therefore known
  (Q1 +0.0210, Q2 -0.0118, Q3 +0.0046, Q4 -0.0164, Q5 +0.0151, Q6 +0.0033).
- schedule-by-seed experiment: every endpoint except the seed-1337 C4-M replicate.
- It had also been seen that the same C1-M configuration gave different endpoints on different servers at the same
  seed (H100 protocol run against the 40GB-card std run: 0.371088 against 0.386354 at seed 42; 0.383342 against
  0.370328 at seed 1337), and that two runs of one configuration and seed on one card gave identical predictions in the
  two instances observed (Addendum 05; the seed-42 C4-M replicate).
Not yet known at filing: the endpoints of fixall, oldmask and randmask at seeds 42 and 1337 and of nokd at seed 1337
(these seven runs were still training, at epochs 108 to 135 of 150). Their per-epoch in-training validation values
(the trainer's own validator, not the unified endpoint) are written to results.csv and the training logs. The analyst
who prepared this addendum read from these files only the number of completed epochs and the device line, and did not
read or tabulate the validation values; whether anyone else looked at them is not recorded. At these epochs such
values approximate the endpoints, so a reader should treat Q1-Q6 at seeds 42 and 1337 as knowable, though not known to
the analyst, when this was decided. Of the seven card pairs defined below, the 40GB-card member was already known
for six (all except nokd at seed 1337).
Because it was decided after outcomes, nothing in this addendum is confirmatory, and it must not be presented as
pre-specified relative to the Addendum-03 outcomes listed above.

## Runs: seven new, all on device 2 of r7525 (NVIDIA A100 80GB PCIe), env envs/ccad_yolo26n_r7525
- std at seeds 42, 1337, 20260703:      C1-M-std-c80_seed<seed>_kaisv4mech   (stock script, stock mapping)
- nokd at seeds 42, 1337, 20260703:     C0-R-std-c80_seed<seed>_kaisv4mech   (stock script, no distillation)
- randmask at seed 20260703:            C1-M-randmask-c80_seed20260703_kaisv4mech (train_mech.py, same random mask as
  the 40GB-card run: the mask is a function of the training seed only)
Launcher: ablation_fixmap/run_mech_c80.sh, a copy of run_mech.sh (sha256
b42c61a4d9d73a9365b7e4802950f5772a6dc521a2042988b6e8e8e89802b45a) with five changes only: (1) the run name carries the
tag "-c80"; (2) the chain log is logs/mech_chain_c80_<tag>.log; (3) the script exits before any run unless the device
argument is 2 and nvidia-smi reports "NVIDIA A100 80GB PCIe" for index 2; (4) it exits if the run directory already
exists; (5) the DONE line records the trainer's exit status (see "Defect found in the existing launchers"). Training
arguments, training code (train_mech.py, mech_patch.py, fixmap_patch.py, stock trainer), evidence bank, schedule
file and environment are those of Addendum 03. The seven runs start together, one lane each, when the six wave-2
lanes on device 2 have all finished (ablation_fixmap/queue_c80.sh); they share the card with each other, as the runs
of wave 2 did. Device 1 of that server belongs to another user and is not used.
Difference to note: at seed 20260703 the 40GB-card std and nokd runs are protocol runs started with
run_v4_common.sh (same trainer script and arm, different launcher and schedule file name); at seeds 42 and 1337 the
40GB-card std and nokd runs were started with run_mech.sh, whose arguments run_mech_c80.sh repeats exactly.
After these runs every condition of the mechanism experiment exists on the 80GB card at every seed.

## Endpoint
As in Addendum 03: validation mAP50-95, final EMA checkpoint (last.pt after "DONE <name> rc=0"), unified evaluator
through analysis/eval_kaisv4.py on H100, one evaluation per run. Per-class AP is reported.

## Analysis (analysis/analyze_add06.py, written before any of the seven runs started)
1. Same-card versions of the cross-card contrasts, all runs on the 80GB card, each as three per-seed differences,
   their mean and a paired-t 95% interval (2 df), with per-class values:
     Q1s = fixall - nokd(c80);  Q3s = oldmask - randmask (c80 run at seed 20260703);
     Q4s = randmask (c80 run at seed 20260703) - fixall;  Q5s = std(c80) - oldmask;  Q6s = std(c80) - fixall.
   Q2 needs no same-card version. At seeds 42 and 1337, Q3s and Q4s equal Q3 and Q4.
   Same card does not mean same occasion: the c80 runs train later than their comparators and with seven jobs on
   the card instead of six (wave 2) or fewer (wave 1). Per seed, Q5 - Q5s and Q6 - Q6s equal the std card-pair
   difference of item 3, and Q1s - Q1 equals the nokd card-pair difference; items 1 and 3 are two views of the same
   seven runs, not independent evidence.
   The reading rule of Addendum 03 is applied to Q3s for sensitivity only; the label of the experiment for Q3 remains
   the one from the Addendum-03 runs. Q3 and Q3s differ only at seed 20260703, by the randmask card-pair difference.
   If the two labels differ, both are reported side by side, and any statement that Addendum 03 ties to the Q3 label
   is accompanied in the same sentence by the statement that it does not hold in the same-card runs (or holds only
   there). The manuscript then says that the label differs between the Addendum-03 runs and the same-card runs; it
   does not attribute the difference to the card.
2. Two-seed subset without any new run: Q3 and Q4 at seeds 42 and 1337 only (both within the 80GB card), reported as
   two values each, without interval or label.
3. Card pairs, descriptive: for each of the seven configurations trained on both cards (std x 3 seeds, nokd x 3
   seeds, randmask at seed 20260703), the endpoint on the 40GB card minus the endpoint on the 80GB card, per-class
   differences, and whether the two prediction files are identical, defined as equal sha256 of
   eval/factorial_v3_freeze/<run>/predictions.json (byte identity, the criterion used in Addendum 05). A missing
   prediction file is reported as "not available", not as a difference. Files that differ in bytes count as not
   identical even if the metrics agree. Summary: mean, SD, range, mean and maximum
   absolute difference over the seven pairs. No test and no label.
   Reading fixed now: if all seven pairs have identical prediction files, the manuscript states that the card made no
   difference in these runs. Otherwise it reports the seven differences and states that the cross-card contrasts of
   Addendum 03 (Q1, Q5, Q6 at every seed; Q3, Q4 at seed 20260703) include a card-and-occasion component of the
   observed size. A card pair differs in card only as far as is known; it also differs in the other jobs sharing the card and in
   time, and at seed 20260703 for std and nokd in launcher. It is therefore a card-and-occasion difference, and is
   not called a pure hardware effect. Seven pairs do not support a general statement about GPU models.
4. Consequence for the paper, fixed now: statements tied to the Q2 and Q3 labels follow Addendum 03 unchanged. The
   same-card results are reported beside the Addendum-03 results in the main text. Q1, Q4, Q5 and Q6 carry no label
   in either version. Wherever the manuscript quotes a value of Q1, Q3, Q4, Q5 or Q6 (text, table or abstract), the
   Addendum-03 value and the same-card value are given together; neither is quoted alone.

## Manipulation checks, reruns, reporting
std(c80): run-summary counters consistent with 6,434 box rows per epoch (about 965,100 over 150 epochs), as in the
other stock-gate runs. nokd(c80): no distillation matches. randmask(c80): admission log 6,434 box rows and 6,280
class rows per epoch and a kept-key set identical to that of C1-M-randmask_seed20260703_kaisv4mech. A run whose
log shows that its condition was not in effect is reported as a failed manipulation and rerun, with disclosure;
otherwise a run is repeated only on technical failure (non-zero exit status, or fewer than 150 epochs in
results.csv). Card check for every c80 run: the device line of the training log names CUDA:2 and an 80GB A100, and an
nvidia-smi listing taken 20 minutes after the start (logs/c80_nvidia_smi.txt, written by queue_c80.sh) shows the
seven process ids on GPU index 2. A run found on another card is a failed manipulation and is rerun, with disclosure.
A rerun keeps the run name; the failed run directory and its training log are first renamed with the suffix
.failed1 and kept, and the failure is disclosed with its cause. A rerun may share the card with fewer jobs than the
first attempt; this is disclosed per run. At most two attempts per run. If a run still has no valid endpoint, the
contrasts and pairs that need it are reported as incomplete, with the available per-seed differences only and
without mean, interval or label, and the summary of item 3 is given over the available pairs with n stated. No run
is replaced by a run on another card or with another seed. All seven runs are reported, whatever they show.

## Defect found in the existing launchers during the review of this addendum (disclose)
In run_mech.sh, run_v4_common.sh, run_v4_cbox.sh and the July launcher of the reused C4-M runs, the completion line
is written as echo "$(date ...) DONE <name> rc=$?". The command substitution runs first, so $? is the exit status of
date and the line always reads rc=0, whatever the trainer returned. The completion gate "DONE <name> rc=0" used by
eval_kaisv4.py therefore shows only that the trainer process ended, not that it succeeded. Checked on 2026-11-14 for
every run that has been evaluated (23 kais_v4 runs, 6 kaisv4mech runs, 3 reused or existing C4-M runs): results.csv
has 150 epochs; the 29 new runs have the trainer's line "150 epochs completed" and no traceback in the training log
(the July logs were not searched); every run with distillation records 140,699 optimizer steps in its summary. No
evaluated run was incomplete. From now on a run of either experiment is evaluated only if, in addition to the DONE
line, results.csv has 150 epochs and the training log has the completed line; for the eight runs still training
under the old launchers this is checked by hand and recorded in PROVENANCE_KAIS_V4.md. The old launchers are not
edited (running lanes have already parsed them); run_mech_c80.sh records the real exit status.

## Code, sha256 (computed at filing; listed in PROVENANCE_KAIS_V4.md with this addendum's digest)
ablation_fixmap/run_mech_c80.sh, ablation_fixmap/queue_c80.sh, analysis/analyze_add06.py: digests are written to
kais_v4/ANALYSIS_ADDENDUM_06.sha256 at filing, and that file is timestamped together with this addendum.
One independent review before filing (three reviewers: scripts, analysis code, text; verdicts REVISE, FILE, REVISE);
all findings were applied, including the exit-status defect above, which the review found.

## Not covered
No 40GB-card versions of fixall or oldmask (Q2 is already within one card); no additional seeds; the
schedule-by-seed experiment, where server and GPU model are aliased with the seed block, is not addressed by these
runs. Dose of concurrent jobs on the card is not controlled.
