# KAIS v4 — timing evidence (compiled 2026-11-10, before any run finished)

## Clocks (measured 2026-11-10 about 06:23 UTC against an RFC 3161 timestamp authority and a synchronised workstation)
- r7525 (<HOST>): agrees with reference UTC to within 1 s.
- H100 (host <HOST>): 6 min 30 s BEHIND reference UTC.
- NAS file mtimes (<NAS_MOUNT>): 8 min 28 s behind the H100 clock, i.e. about 14 min 58 s behind reference UTC.
All log lines keep their native clock. Corrected values are given in brackets.

## Ordering evidence
- PROTOCOL_KAIS_V4.md: NAS mtime 2026-11-10 00:51:38.107 [about 01:06:36 UTC]; PROTOCOL_KAIS_V4.frozen_at written by
  the H100 clock reads 2026-11-10T01:00:06Z [01:06:36 UTC] with sha256 0b8ccde0ee07aac9cb2cf1f31aba00ad725a88639d221c304daa83bdb5b715b1.
  The two records agree after clock correction.
- First H100 lane START lines: 2026-11-10T01:00:21Z by the H100 clock [01:06:51 UTC], process start time of the
  lane shells (ps lstart) Tue Nov 10 01:00:21 2026, 15 s after the freeze record on the same clock.
- First r7525 lane START lines: 2026-11-10T01:14:33Z (accurate clock).
- No kais_v4 run directory existed before these starts; every run needs about 30 h or more for 150 epochs.
- Independent timestamps (freetsa.org, RFC 3161, hash only): PROTOCOL_KAIS_V4.md stamped Nov 10 06:23:33 2026 GMT;
  ANALYSIS_ADDENDUM_01.md (sha256 d2555e1014432bdc94cfcc433614378cac5a590e63ff6baddd34634d6c204481) stamped
  Nov 10 06:23:52 2026 GMT. At both times no chain log contained a DONE line (runs at epoch 19-23 of 150).

## What this does and does not show
- Shows: the protocol text with this hash existed, by an independent clock, more than a day before any run could finish;
  and, by same-clock file and process records kept by the authors, 15 s before the first training process started.
- Does not show independently: that the protocol predates the START of training (that rests on the authors' own
  server records, which are not tamper-evident), nor what anyone looked at in the per-epoch training logs.
- First unified evaluation of any kais_v4 run: not yet performed; its time is to be appended here when it happens.

## Addendum 04 filed (image-resampling description, fixed models)
- ANALYSIS_ADDENDUM_04.md sha256 b2d14d05c65dd7716e73f3be1fbde18475e2f58e54011f2907c060bd379bcc22; RFC 3161 (freetsa) Time stamp: Nov 10 13:34:43 2026 GMT; .tsq/.tsr alongside.
- At filing: 0 chain logs with DONE; no kais_v4 / kaisv4mech evaluation directory exists. One independent review before filing (verdict REVISE; all findings incorporated). A first stamp of an earlier text (sha d2e950d4...1ab3, 13:34:27 GMT) was superseded only to correct the stated filing time.
- Bootstrap index array digest 246e90b9...6e34 (seed 12922872722789885999, B=2000 x 2827). Not yet implemented; implement and verify (a)/(b) at evaluation time. No re-inference; needs predictions_coco.json + val_gt_coco.json of each endpoint evaluation.

## Analysis code record 01 filed
- ANALYSIS_CODE_RECORD_01.md sha256 b8861731af72e1e4c4b3bc1f06629543f02eef2fd062d2fbb04dbcdb435d57e4; RFC 3161 (freetsa) Time stamp: Nov 10 15:43:40 2026 GMT. Scripts in analysis/ (eval_kaisv4.py, analyze_kaisv4.py, bootstrap_a04.py, a04_contrasts.py, image_offset_bound.py); 0 DONE lines and no kaisv4 eval dir at filing. Evaluate every finished run with: envs/ccad_yolo26n/bin/python kais_v4/analysis/eval_kaisv4.py <run> --device 0 (H100 only, once).
- Manuscript v8 answers the user review of v7 (B1-B3 naming, crossed-interval wording, 0.80 px bound, Q4 = random-thinning control, class-target rows not matched, reading-rule caveat).

## First endpoint evaluations started
- 0.000000T- 2026-11-11T13:53:35Z (H100 clock, about 6.5 min behind UTC): first endpoint evaluations started. Batch 1 = C1-M_seed42, F-ShufSingle-s4..s7_seed42 (trained on H100), C0-R_seed20260703 (trained on r7525); all six have DONE rc=0. Evaluated with analysis/eval_kaisv4.py --device 0 (digests verified against ANALYSIS_CODE_RECORD_01.md immediately before). No kais_v4 endpoint had been seen before this.
- (the line "- 0.000000T" above is a failed printf of the same note; nothing else was lost)
- 2026-11-11: analysis/eval_kaisv4_best.py (sha256 284e62175be36cc60d824a543e64ab20ac4d05a1c6f0a61250aed2ef9542abc3) written for the best.pt sensitivity of Addendum 01 A5, after the six batch-1 endpoints (last.pt) were seen and before any best.pt of a new run was scored. Not timestamped externally.
- 2026-11-11T16:34:50Z (H100 clock): batch 2 evaluated once with eval_kaisv4.py: C1-M_seed20260703, CBox-M_seed20260703 (trained on r7525 GPU0).

## FINDING 2026-11-11 ~16:35Z (H100 clock): CBox-M launcher error (found at evaluation)
- CBox-M_seed20260703_kaisv4 and C1-M_seed20260703_kaisv4 have identical unified endpoints (mAP 0.3823291309794702, identical per-class AP), identical predictions.json sha256 (4673ccf9...), identical run-summary losses (mean_kd_cls 0.3196, kd_matches_cls 939746). Cause: run_v4_common.sh passes --lambda-cls 0.4613535884454487 for every arm; the schedule file defines CBox-M as full x150 (same as C1-M); the historical CBox-M runs were box-only because their launcher passed --lambda-cls 0.0 (their summaries: lambda_cls 0.0, kd_matches_cls 0). So the kais_v4 CBox-M run was trained as C1-M. It is NOT a box-only run and must not be used as CBox-M.
- Discovered only after both endpoints were seen (outcome-dependent discovery; disclose).
- Side fact: two runs with identical configuration and seed on the same card (r7525 GPU0) gave bit-identical predictions.
- Still queued inside running lane scripts with the same error: CBox-M seeds 42 and 1337 on H100 (not started). Editing run_v4_common.sh does not change loops already parsed by the running lanes.
- NO action taken yet (no kill, no relaunch); awaiting the corresponding author decision.
- Addendum 05 filed: sha256 941f865e903f867fe4a88b3326bede387597c60e6e51f623d4e88716489ce532; RFC 3161 Time stamp: Nov 11 16:52:43 2026 GMT. User decision 2026-11-11: rerun CBox-M as the protocol defines it.
- 2026-11-11T16:48:00Z (H100 clock): invalid CBox-M seed 20260703 set aside (_INVALID_clskd: model dir, log, eval dir, draws); corrected run launched on r7525 GPU0, chain tag r7525c_cbox; swap watchers armed on H100 for CBox-M seeds 42 and 1337 (tags h100_cbox42, h100_cbox1337).
- 2026-11-11T18:06:05Z (H100 clock): C1-M-randmask_seed20260703_kaisv4mech evaluated once with eval_kaisv4.py.
- 2026-11-12T12:35:16Z (H100 clock): C4-M_seed20260703_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T12:36:07Z (H100 clock): F-ShufSingle-s4_seed20260703_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T12:37:00Z (H100 clock): F-ShufSingle-s5_seed20260703_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T12:37:51Z (H100 clock): F-ShufSingle-s6_seed20260703_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T12:38:43Z (H100 clock): F-ShufSingle-s7_seed20260703_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T14:56:13Z (H100 clock): C1-M-oldmask_seed20260703_kaisv4mech evaluated once with eval_kaisv4.py.
- 2026-11-12T16:28:39Z (H100 clock): C1-M-fixall_seed20260703_kaisv4mech evaluated once with eval_kaisv4.py.
- 2026-11-12T17:15:36Z (H100 clock): CBox-M_seed20260703_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T17:16:24Z (H100 clock): corrected CBox-M_seed20260703_kaisv4 (Addendum 05 rerun) checked before evaluation: run summary lambda_cls 0.0, kd_matches_cls 0, kd_matches_box 965097, mean_kd_cls 0.0; predictions sha differs from C1-M_seed20260703 (4673ccf9...).
- 2026-11-12T20:02:02Z (H100 clock): swap watcher h100_cbox1337 fired. Lane L4 started the wrongly configured CBox-M_seed1337_kaisv4 at 19:57:06Z; the watcher stopped it (pkill), and L4 then wrote "DONE CBox-M_seed1337_kaisv4 rc=0" at 19:57:31Z although the run was killed after ~25 s (the rc=0 reflects the lane loop, not a completed run). Partial dir set aside as CBox-M_seed1337_kaisv4_ABORTED_lambdacls. Corrected run started 19:57:41Z (chain v4_chain_h100_cbox1337.log, --lambda-cls 0.0). eval_kaisv4.py --dry reports finished=false for CBox-M_seed1337_kaisv4 because the last chain line for that name is the new START.
- 2026-11-12T20:05:56Z (H100 clock): C1-M_seed1337_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T20:06:52Z (H100 clock): F-ShufSingle-s4_seed1337_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T20:07:47Z (H100 clock): F-ShufSingle-s5_seed1337_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T20:08:42Z (H100 clock): F-ShufSingle-s6_seed1337_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T20:09:37Z (H100 clock): F-ShufSingle-s7_seed1337_kaisv4 evaluated once with eval_kaisv4.py.
- 2026-11-12T20:10:13Z (H100 clock): analyze_kaisv4.py (sha 728e38dd...) run on available endpoints -> kais_v4/analysis/results_partial_20261112T201012Z.json (primary_frozen complete; other families partial).
- primary_frozen result file results_partial_20261112T201012Z.json sha256 4251170555a21e1e138ff22d4a79c2c028de9d5513a4e069c407a70d33520488; RFC 3161 (freetsa.org, hash only) Time stamp: Nov 12 20:17:00 2026 GMT. Decision as computed by the frozen rule: inconclusive.
- 2026-11-13T16:19:31Z (H100 clock): C0-R-std_seed42_kaisv4mech evaluated once with eval_kaisv4.py.
- 2026-11-13T16:39:04Z (H100 clock): server-side kais_v4/auto_eval_loop.sh started (sha256 01c13ceff9e7045b2279ab1401ee00e0bfef48c8c72b392077c534d1cf333dce); same once-per-run rule as before plus a CBox-M summary guard; replaces polling from the workstation.
- 2026-11-13T18:50:00Z (H100 clock): C1-M-std_seed1337_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop.sh).
- 2026-11-13T19:07:03Z (H100 clock): C1-M-std_seed42_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop.sh).
- 2026-11-13T23:13:48Z (H100 clock): C0-R_seed42_kaisv4 evaluated once with eval_kaisv4.py (auto_eval_loop.sh).
- 2026-11-13T23:27:50Z (H100 clock): C0-R_seed1337_kaisv4 evaluated once with eval_kaisv4.py (auto_eval_loop.sh).
- 2026-11-14T03:41:15Z (H100 clock): CBox-M_seed42_kaisv4 checked before evaluation by auto_eval_loop.sh: lambda_cls 0.0, kd_matches_cls 0.
- 2026-11-14T03:41:38Z (H100 clock): CBox-M_seed42_kaisv4 evaluated once with eval_kaisv4.py (auto_eval_loop.sh).
- 2026-11-14T03:55:34Z (H100 clock): C4-M_seed42_kaisv4 evaluated once with eval_kaisv4.py (auto_eval_loop.sh).
- 2026-11-14T03:55:34Z (H100 clock): CBox-M_seed1337_kaisv4 checked before evaluation by auto_eval_loop.sh: lambda_cls 0.0, kd_matches_cls 0.
- 2026-11-14T03:55:52Z (H100 clock): CBox-M_seed1337_kaisv4 evaluated once with eval_kaisv4.py (auto_eval_loop.sh).
- 2026-11-14T04:46:48Z (H100 clock): analyze_kaisv4.py (sha256 728e38dd...48c6, equal to ANALYSIS_CODE_RECORD_01) run on eval/factorial_v3_freeze -> kais_v4/analysis/results_partial_20261114T044603Z.json (sha256 9d3c4d32606b7016176a5bd252a9b87095c5f2c4a061baa65dbb2d60593b55ac); baseline family B1-B3 complete (C0-R, CBox-M, C1-M at three seeds); RFC 3161 token kais_v4/analysis/results_partial_20261114T044603Z.json.tsr. Observation: C4-M_seed42_kaisv4 (H100, Nov) has the same final results.csv row and the same unified endpoint (0.38261254431302316) as the reused July run F-MonoSingle_seed42_v3factorial_intpad; last.pt digests differ (ef25eb45... vs 4650efaf...).
- 2026-11-14T06:30:43Z (H100 clock): seed-42 C4-M pair compared: results.csv of F-MonoSingle_seed42_v3factorial_intpad and C4-M_seed42_kaisv4 identical in all columns except time at all 150 epochs; predictions_coco.json sha256 0a6d7f79...a3b958 and predictions.json sha256 329b2b4f...6e9142 identical for both eval dirs.
- 2026-11-14T06:39:02Z (H100 clock): auto_best_loop.sh started (sha256 4a404e5c028d06acbabd932c34e18ee2e407cbd14b96163478d093c79300546d); scores best.pt of each run that has an endpoint, once, with eval_kaisv4_best.py (sha256 284e6217...abc3, unchanged since 2026-11-11). Sensitivity only (Addendum 01 A5). Log kais_v4/logs/auto_best.log.
- 2026-11-14T06:44:28Z (H100 clock): corresponding author decision 2026-11-14: compute the protocol sensitivity record on the internal evaluation split (test.txt, 2,553 images, not blind; 2,019-image subset by the rule of rights_clean_protocol_v1.json). Script analysis/eval_kaisv4_internal.py (sha256 da48e2881d1cadcf2ffda2535f3a310165e963cb8f6ae15ac878d53223a3330a) written today, after the validation endpoints of the primary family were known; last.pt, imgsz 960, same COCO scoring functions as the endpoint. Runs: the 12 shuffled-schedule runs, C4-M_seed20260703_kaisv4, and the two reused C4-M runs. One evaluation per run. Sensitivity only.
- 2026-11-14T06:51:21Z (H100 clock): 15 internal-split evaluations done (log kais_v4/logs/internal_eval.log); order contrast on the internal split written to analysis/internal_sensitivity_20261114.json (computed inline: d_s = C4-M minus mean of s4-s7, paired t, 2 df).
- 2026-11-14T06:51:42Z (H100 clock): internal-split evaluation extended to the baseline runs (C0-R, CBox-M, C1-M at three seeds) and C4-M_seed42_kaisv4, so that all finished runs of the schedule-by-seed experiment are scored as the protocol states; same script, one evaluation per run.
- 2026-11-14T08:21:05Z (H100 clock): internal-split values of the baseline runs and descriptive B1-B3 on that split written to analysis/internal_sensitivity_20261114b.json (includes the order contrast of internal_sensitivity_20261114.json).
- 2026-11-14T08:58:30Z (H100 clock): Addendum 06 filed (same-card control runs for the mechanism experiment; decided by the corresponding author 2026-11-14 AFTER outcomes; sensitivity only). ANALYSIS_ADDENDUM_06.md sha256 1dac944d937f1017d387196c0566e4b45b5b308e49bf92563b0d783daa60cb2a, RFC 3161 (freetsa) Nov 14 09:04:17 2026 GMT; code digests in ANALYSIS_ADDENDUM_06.sha256 (RFC 3161 Nov 14 09:04:18 2026 GMT): run_mech_c80.sh 64136a58...5207, queue_c80.sh 764ceb76...d192, analysis/analyze_add06.py 6771c5ec...3da3. At filing no c80 run directory or log existed; six wave-2 lanes on r7525 device 2 and nokd seed 1337 were still training.
- same time: the review of Addendum 06 found that the DONE lines of run_mech.sh, run_v4_common.sh, run_v4_cbox.sh and the July int-pad launcher always record rc=0 (the status of date). All 32 evaluated runs were checked: 150 epochs in results.csv; the 29 new runs have "150 epochs completed" and no Traceback in the training log. auto_eval_loop.sh (pid 3398444) was stopped while idle and replaced by auto_eval_loop2.sh (sha256 8d508c455bc83182ca938692198d6cf85170a8ff9aa62ed3aebcbdfeb6c6ce2b), which requires 150 epochs and the completed line before an evaluation.
- 2026-11-14T13:28:59Z (H100 clock): C1-M-oldmask_seed1337_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-14T13:29:29Z (H100 clock): C1-M-randmask_seed42_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-14T14:05:03Z (H100 clock): C1-M-oldmask_seed42_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-14T14:05:34Z (H100 clock): C1-M-randmask_seed1337_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-14T14:40:38Z (H100 clock): C1-M-fixall_seed1337_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-14T14:41:10Z (H100 clock): C1-M-fixall_seed42_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-14T15:15:44Z (H100 clock): C0-R-std_seed1337_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-14T15:21:00Z (H100 clock): all 13 mechanism runs complete (150 epochs in results.csv and trainer line "150 epochs completed" for each; last, C0-R-std_seed1337_kaisv4mech, evaluated 15:15:44Z by auto_eval_loop2.sh). analyze_kaisv4.py (sha256 728e38dd...48c6, unchanged) run -> analysis/results_partial_20261114T152024Z.json (sha256 4aca382036fa9d031a773c80576313f232329d25d242850b88aec3c33f098407; RFC 3161 Nov 14 15:26:59 2026 GMT). Q2 and Q3 labels: inconclusive, inconclusive. Manipulation checks from admission logs: fixall 9,334 box / 9,110 class rows in each of 150 epochs at all seeds; oldmask 6,434 / 6,265; randmask 6,434 / 6,277, 6,274, 6,280 (seeds 42, 1337, 20260703); std summaries 965,097 / 965,098 / 965,096 box matches; nokd 0. Addendum 06: seven same-card runs started 2026-11-14T14:17:05Z on r7525 device 2; logs/c80_nvidia_smi.txt (14:37:05Z) shows seven process ids on the GPU with index 2 (uuid GPU-48034344...) and none of them on index 1.
- 2026-11-15T01:13:01Z (H100 clock): C4-M_seed1337_kaisv4 evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-15T01:20:27Z (H100 clock): C4-M_seed1337_kaisv4 finished 2026-11-15T01:05:37Z (150 epochs, trainer completed line), evaluated by auto_eval_loop2.sh; its results.csv equals that of the reused July run in every column except time at all 150 epochs, predictions.json sha256 equal (619d8594...), endpoint 0.37048958606878407 equal; run summary 965,098 box / 939,748 class matches. Final frozen analysis of the schedule-by-seed experiment: analysis/results_final_sbs_20261115T011951Z.json (sha256 71392f13684fab3788ffe5e1143b2cb08967eb50508e85f38e2a5031164226d0, RFC 3161 Nov 15 01:26:25 2026 GMT); A3 with concurrent replicates equals the frozen analysis exactly. a04_contrasts.py (sha256 ad358851...fda3, unchanged) -> analysis/a04_contrasts_20261115T012010Z.json (sha256 87ba03f2...c3e3, RFC 3161 Nov 15 01:26:46 2026 GMT). best.pt sensitivity computed inline -> analysis/bestpt_sensitivity_20261115T012010Z.json (sha256 4fd2d172...4607, same timestamp); for seeds 42 and 1337 the C4-M best.pt is that of the November replicate (reused run names are not accepted by eval_kaisv4_best.py).
- 2026-11-16T08:19:09Z (H100 clock): C0-R-std-c80_seed42_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-16T08:32:54Z (H100 clock): C0-R-std-c80_seed1337_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-16T08:33:09Z (H100 clock): C0-R-std-c80_seed20260703_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-16T17:30:10Z (H100 clock): C1-M-randmask-c80_seed20260703_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-16T17:46:13Z (H100 clock): C1-M-std-c80_seed20260703_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-16T17:46:32Z (H100 clock): C1-M-std-c80_seed42_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-16T18:08:39Z (H100 clock): C1-M-std-c80_seed1337_kaisv4mech evaluated once with eval_kaisv4.py (auto_eval_loop2.sh; 150 epochs and completed line checked).
- 2026-11-21T05:10Z (UTC; H100 clock about 6.5 min behind): Addendum 06 same-card runs. All seven c80 runs complete: DONE lines with real exit status rc=0 (16 Nov), 150 epochs in results.csv, trainer line "150 epochs completed", no traceback; device line CUDA:2 NVIDIA A100 80GB PCIe for each; logs/c80_nvidia_smi.txt shows the seven pids on GPU index 2 (uuid GPU-48034344...). Manipulation checks: std(c80) kd_matches_box 965,097 / 965,098 / 965,096 (= 6,434 rows x 150 epochs within the usual counter offset), nokd(c80) 0 matches, randmask(c80) admission log 6,434 box and 6,280 class rows per epoch (cumulative 965,100 / 942,000) and kept_keys set identical to C1-M-randmask_seed20260703_kaisv4mech (6,434 keys). No rerun. Evaluated by auto_eval_loop2.sh on 16 Nov (EVALDONE lines in logs/auto_eval.log). Digests re-checked equal to ANALYSIS_ADDENDUM_06.sha256 (addendum 1dac944d..cb2a, run_mech_c80.sh 64136a58..5207, queue_c80.sh 764ceb76..d192, analyze_add06.py 6771c5ec..3da3). analyze_add06.py run -> analysis/results_add06_20261121T045950Z.json (sha256 72f28254f914933d466d1ab3d1abd4811565e6a6b24c0b5c162d9d993f6b2f1d), RFC 3161 (freetsa, hash only) Nov 21 05:07:00 2026 GMT, .tsq/.tsr beside it. Result: all seven card pairs have byte-identical predictions.json (difference 0 in mAP and per class); per-epoch results.csv identical excluding time columns in the three pairs checked; last.pt files differ in bytes (checkpoint metadata). Hence Q1s, Q3s, Q4s, Q5s, Q6s equal Q1, Q3, Q4, Q5, Q6; Q3s label (sensitivity only) inconclusive, same as Q3. Reading fixed in Addendum 06 applies: the card made no difference in these runs.
