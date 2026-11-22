# KAIS v4 — Addendum 04: image-resampling description of the fixed trained models (post-freeze, pre-outcome)

Does NOT modify PROTOCOL_KAIS_V4.md (sha256 0b8ccde0ee07aac9cb2cf1f31aba00ad725a88639d221c304daa83bdb5b715b1) or
Addenda 01, 02, 03. No decision rule, reading rule or label of the protocol or of the mechanism experiment uses
anything defined here. Decided by the corresponding author on 2026-11-10. The procedure is adapted from one the
author used in another project; it is not part of the frozen protocol and must be reported as added after the
freeze and after training started. The draft was reviewed once, independently, before filing; the review's
findings are incorporated below.

## Status when this addendum was filed (2026-11-10, about 13:35 UTC)
- 0 of the protocol's 22 runs, 0 of the 2 concurrent C4-M replicates and 0 of the 13 mechanism runs had finished
  (no chain log contained a DONE line); no run was beyond about epoch 60 of 150.
- No unified evaluation of any kais_v4 or kaisv4mech run had been performed.
- Already known: the two reused July C4-M endpoints (seeds 42, 1337) were evaluated in July 2026; their mAP50-95,
  per-class AP and detection files exist and have been seen. They enter P and H3. No resampling of any kind had
  been run on them, or on any other detection file, when this was filed.
- Per-epoch validation metrics in the training logs were visible while monitoring; none was used here.

## Why
Every interval in the protocol and in Addenda 01 and 03 is computed from three per-seed differences (2 df). Such an
interval describes seed-to-seed variation only and is wide. It says nothing about how much a difference between
trained models depends on which validation images happen to be in the split. This addendum adds that second,
separate description. The two are not combined.

## Models and estimands
39 models: the 22 protocol runs, the 2 reused July C4-M runs, the 2 concurrent C4-M replicates, the 13 mechanism runs.
Final EMA checkpoint (last.pt), validation split (2,827 images), mAP50-95 of the unified evaluator.
For each contrast c, dbar_c is the mean over the three seeds of the per-seed difference, exactly as defined in the
protocol or addendum that introduced it. It is a property of these trained models, not of a population of runs.
 P    primary: C4-M minus the mean of the four shuffled schedules (reused July C4-M runs at seeds 42, 1337)
 P'   the same with the concurrent C4-M replicates (Addendum 01, A3)
 H1   C1-M - C0-R      H2   C1-M - CBox-M      H3   C4-M - C1-M (reused runs)      H3'  H3 with the replicates
 Q1..Q5 of Addendum 03. Q6 is omitted (descriptive only and without a label in Addendum 03).
Per-class AP50-95 (knife, gun, stick) is computed for Q1..Q5 only and tabulated without any sentence.

## Procedure
1. Index array, fixed now. seed = int.from_bytes(sha256(b"LPCCAD-KAISV4-A04").digest()[:8], "big")
   = 12922872722789885999; idx = numpy.random.default_rng(seed).integers(0, 2827, size=(2000, 2827), dtype=numpy.int64),
   one call. sha256(idx.tobytes()) = 246e90b9e083a0dd9f6ca230687679e26b95aeb25564337c1707aea626fa6e34
   (little-endian; obtained identically with numpy 2.2.6 and 2.4.6). Row b is draw b (B = 2,000). Index i is the
   i-th entry of "images" in val_gt_coco.json. The same row is used for every model. Seeds, schedules and models
   are never resampled. If the array cannot be regenerated with this digest, the analysis is not run.
2. Inputs. For each model, the detection file (predictions_coco.json) and ground-truth file (val_gt_coco.json)
   written by the single unified evaluation that produced the model's reported endpoint. No model is re-inferred
   for this analysis. The ground-truth file must have one sha256 across all 39 models; if not, the analysis is not
   run and this is disclosed. The unified evaluator does not accept the run names of the baseline and mechanism
   runs; the wrapper needed for that is part of the endpoint evaluation and is disclosed there, not here.
3. Resampled set of draw b: row b sorted ascending; its j-th entry becomes a new image with id j (1-based), carrying
   that image's ground truth and detections, so an image drawn m times appears as m distinct images. Detections
   keep their stored scores and categories; no threshold, category shift or other filter is re-applied.
   mAP50-95 and per-class AP are computed on that set as the unified evaluator computes them. Per-image scores
   are never averaged.
4. Reference library: the COCOeval implementation that the unified evaluator actually used for the reported
   endpoints (recorded at evaluation; the protocol names faster-coco-eval, while the evaluator code tries
   pycocotools first — whichever ran is the reference and the discrepancy is disclosed).
   Verification before any interval is computed, for every model: (a) the identity vector 0..2826 reproduces the
   recorded mAP50-95 and per-class AP to within 1e-9; (b) for rows 0..19, the implementation agrees to within 1e-9
   with the reference library run on explicitly written resampled JSON files. An implementation that reuses
   per-image matching across draws is allowed only if it passes (a) and (b); if it fails, every draw is computed
   with the reference library on written files instead, and the failed attempt is disclosed.
5. A draw in which a class has no ground-truth instance, or no valid precision entry, is undefined for every
   quantity using that class; it is excluded and counted. If more than 1% of draws are undefined for a quantity,
   no interval is reported for it ("not established").
6. All per-draw values are stored (draw x model), with a sha256 of each input file.

## Outputs
For each contrast: dbar_c on the original split; the mean and SD of dbar_c over defined draws; the 2.5% and 97.5%
percentiles (numpy.percentile, method "linear", over defined draws); the number of undefined draws.
For each model: the SD of its mAP50-95 over draws. For each per-seed difference: its SD over draws.
The interval is a percentile interval of the resampling distribution, not a confidence interval with verified
coverage; no other interval method is substituted afterwards. Intervals are per contrast and unadjusted; no
joint or multiplicity-adjusted statement is made. Endpoints are compared with 0 and +/-0.01 unrounded.
They are shown in a separate column next to the seed-based intervals and are never merged with them.

## Statements allowed (fixed now; mAP50-95 contrasts only)
(i)  If both endpoints lie inside [-0.01, +0.01]: "For these trained models, the central 95% of the mean
     differences obtained by resampling the validation images lay within +/-0.01."
(ii) If both endpoints are strictly of the same sign: "For these trained models, the central 95% of the resampled
     mean differences excluded zero."
Both sentences are used if both hold. If neither holds: "For these trained models, the central 95% of the
resampled mean differences included zero and extended beyond +/-0.01."
Every such sentence is followed by: "This interval contains no seed-to-seed variation and does not describe other
training runs."
Not allowed: any statement of significance; any change of a protocol decision or of a Q2/Q3 label; attaching the
protocol's phrase "no detectable order effect" to this interval for P or P'; any claim about other images, other
data or the population of training runs; any combination of this interval with a seed-based interval.

## Limits stated in advance
- Images are resampled as if exchangeable. Frames from the same source or sequence are not independent, so the
  intervals are likely too narrow as a description of image-level uncertainty. Per-image source identifiers were
  not audited; no source-level resampling is attempted.
- The validation split is the one whose per-epoch metrics appear in the training logs; the analysis describes
  that split only. The reserved public test split is not used.
- With three seeds the seed-based interval remains the only statement about run-to-run variation.
- The validation-selected checkpoints, the aborted r7525 runs (*_ABORTED_noalb) and the historical July runs
  other than the two reused C4-M endpoints do not enter this analysis.
