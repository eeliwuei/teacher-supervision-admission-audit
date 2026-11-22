# KAIS v4 — Analysis code record 01 (code fixed before any run finished or was evaluated)

Does NOT modify PROTOCOL_KAIS_V4.md (sha256 0b8ccde0ee07aac9cb2cf1f31aba00ad725a88639d221c304daa83bdb5b715b1) or
Addenda 01-04. It records the code that will produce the endpoints and analyses, and the remaining practical
choices, so that none of them is made after outcomes are seen. Written 2026-11-10 after an external review of
draft v7 asked for the evaluator, checkpoint rule, hardware and admission logs to be fixed and versioned.
Status: 0 chain logs contain a DONE line; no kais_v4 / kaisv4mech run has been evaluated.

## Files (kais_v4/analysis/), sha256
86791a5fb7225c4b2c27887eef0437e848b0bb7fb365160d4aa28e1a213ab9cd  bootstrap_a04.py
66cf85882c5782007e28eea8381783027b9b370532f619aea7b3ae9828e3603b  eval_kaisv4.py
ad358851722c3f7d8537ad639fbcaf11bab7a86ea6e689506f145a98b169fda3  a04_contrasts.py
728e38dda819ea4c0a91d5fc280bcf9f2b235e298f649fd8cb581d3cfaae48c6  analyze_kaisv4.py
08976b27136e220e40a0cc21394ac4e8282a4e1ef92c8545301e7d996072db7b  image_offset_bound.py

## Fixed choices
- Endpoint evaluation: eval_kaisv4.py <run>. It calls the unchanged unified evaluator (factorial_v3/
  factorial_freeze_eval.py: last.pt, validation split, imgsz 960, save_json, unified_for_pred) and changes only the
  parsing of the run name, which the evaluator restricts to F-Mono*/F-Shuf*. It refuses a run without
  the last START/DONE line for exactly that name being "DONE <name> rc=0", refuses names containing ABORTED,
  accepts no option except --device (so imgsz 960 and no --force are enforced), and takes a lock file so that a
  run is evaluated once.
- Checkpoint: weights/last.pt (final EMA) for every endpoint. best.pt enters only the sensitivity analysis of Addendum 01.
- Where: every new run, from both training machines, is evaluated on H100 in envs/ccad_yolo26n, device 0.
  eval_env.json per run records host, GPU, package versions, the COCO library actually used, and file digests.
- Seed-based analyses: analyze_kaisv4.py (protocol primary contrast and decision with threshold 0.0171 and band
  0.01; baseline contrasts with paired t and Holm; two-way ANOVA of the shuffled grid; Addendum 01 A2 and A3;
  Addendum 03 Q1-Q6 with the reading rule and per-class AP).
- Image resampling (Addendum 04): bootstrap_a04.py then a04_contrasts.py. The addendum's H1-H3 are named B1-B3
  in the code output and the manuscript, to avoid confusion with the historical contrasts H1-H6b.
- Manipulation checks: logs/<run>.admission.jsonl (mechanism runs: rows admitted per 938 dataloader calls) and the
  kd_matches_box / kd_matches_cls counters of each run summary. These record counts, not row identity.

## Checks already run (no new outcome involved)
- bootstrap_a04.py verify on the two reused July C4-M evaluations (seeds 42, 1337): (a) identity reproduces the
  recorded mAP50-95 and per-class AP with difference 0.0; (b) rows 0-19 agree with pycocotools COCOeval on
  explicitly written resampled JSON with difference 0.0; duplicate acceptance: in every one of the 20 draws the
  reference scored 2,827 images and exactly the ground-truth and detection counts expected with multiplicity;
  negative control: scoring only the distinct images of draw 0 gives a different mAP. Output: analysis/a04_verify_july/.
  This means resampled scores of the two already-known July models (20 draws each) exist; no interval was computed.
- analyze_kaisv4.py and a04_contrasts.py were run on synthetic random numbers only (39 fake models).
- Speed of the image resampling: about 0.17 s per draw per model.

## Review before filing
One independent review of the four scripts (200 synthetic datasets checked against scipy and a hand-written Holm and
ANOVA: contrasts, intervals, p-values, variance components, A2 interval and labels agreed to 4e-16). Its findings
were applied before filing: the wrapper's option whitelist, last-line completion test and lock; enforcement of
"39 models, one ground-truth digest" in a04_contrasts.py; NaN-safe comparison and the reference-library fallback
of Addendum 04 step 4 in bootstrap_a04.py; the decision field of the concurrent-replicate analysis renamed
"rule_applied_for_sensitivity_only". The July verification was repeated with the final files (same result;
reference path also reproduces the recorded endpoints with difference 0.0).
Not in the code: the descriptive H100 F-MonoSingle seed-20260703 run and the exploratory schedules s1-s3 of the
protocol are tabulated by hand from their existing metrics files; the best.pt sensitivity analysis of Addendum 01
A5 has no script yet and will be written before best.pt of any new run is scored.

## Corrections of wording in filed documents (the documents themselves are not edited)
- Addendum 04, section "Why": "Every interval in the protocol and in Addenda 01 and 03 is computed from three
  per-seed differences" overlooks the crossed-random-factor interval of Addendum 01 A2, which also carries
  schedule-draw variation. The procedure of Addendum 04 does not depend on that sentence.
- Addendum 03: "always the same rows" rests on two measured dataloader passes with identical admission (9,334 of
  9,334 row keys agree) and on per-epoch counts; row identity in every epoch of every run was not observed.
- Addendum 03: random masks match the old mask in the number of box rows (6,434), not in the number of rows with
  a class target (6,265 against 6,277 / 6,274 / 6,280). Q4 ("amount alone") changes both how many rows and which
  rows are supervised and is reported as a random-thinning control.
- Addendum 03: the 0.69 px figure is the largest offset of the matched box. image_offset_bound.py bounds the
  offset of any coordinate in the images of the 6,434 admitted rows: at most 0.80 px (344 rows above 0.25 px,
  34 above 0.5 px). Computed from image sizes only.
- Addendum 03 reading rule: "consistent difference" (same sign at three seeds and |mean| >= 0.01) does not imply
  that the 95% interval excludes zero; it is reported with the interval and never called confirmed.
