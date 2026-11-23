# What is not in this bundle, and why

Sizes are those on the server on 21 Nov 2026.

## Withheld: annotation-derived coordinates or image paths

| Item | Why | What a reader loses |
|---|---|---|
| Run-time gate per-row files: `runtime_gate_rows_pass1_seed42.csv`, `..._pass2_seed1337.csv`, `..._smoke.csv` (8.8 MB) | Absolute image path and box coordinates of every training row, including rows from the two sources whose annotations are withheld. The originals stay withheld. `gate_rows_nocoord/` holds per-row files without path or coordinate for the 3,698 rows of D3 and D4 (random row and image numbers, no batch index). For the 5,636 rows of D2 and of the pooled source it holds no per-row record; it holds count cells, totals, sorted value lists and bin counts. The 31-row smoke file has no counterpart there. | The filed `runtime_gate_analyze.py` cannot run. The summary can be recomputed from `gate_rows_nocoord/` with the command in its `README.txt`; the output is byte-identical. For the 5,636 rows, 34 of the 123 lines rest on yes/no flags evaluated by the authors and 6 lines on totals supplied by the authors. A reader cannot check these. Nothing can be checked against box coordinates. |
| `padding_row_audit.csv` (with its script, digest file and published summary; 3.0 MB) | Ground-truth box coordinates of all 9,334 rows. The original stays withheld here. For the 3,698 rows of D3 and D4 a version with 16 columns (row number, strata, resized sizes, static flags and one static IoU) is included as `gate_rows_nocoord/padding_row_audit.nocoord.public.csv`. Online Resource 12 of the paper is a copy of the file with all rows. In it ten columns are empty for the 5,636 rows of D2 and of the pooled source, and `iou_float` is empty for 1,376 of these rows. | The second input of the filed `runtime_gate_analyze.py` is missing. The static-versus-run-time comparison can be recomputed from the static flags in `gate_rows_nocoord/` (per row for D3 and D4, per count cell for the other rows); the static flags themselves cannot be recomputed from this bundle. |
| `val_gt_coco.json` in every evaluation directory (one identical file, 1.19 MB each) and `val_gt_coco.image_id_map.json` | Annotation boxes of all validation images, including the withheld sources. | Nothing can be scored from this bundle alone. With Online Resource 10 the loss is recovered: it holds the validation ground truth without 87 boxes of the two restricted sources, and its script rebuilds these boxes from the providers' files. `tools/recompute_map.py` then recomputes the endpoint values of all 46 runs from the prediction files (equal to the filed values in the test of 22 Nov 2026) and can give `bootstrap_a04.py` its inputs. The rebuilt file is not byte-identical to the withheld one (other image ids), so the filed `gt_sha256` cannot be checked. `val_gt_coco.image_id_map.json` is not needed: the tool maps images by file name. |
| `runtime_gate_mech/` (65 files, 38 MB) and `runtime_gate_fixmap/` (30 files, 6.4 MB) | Per-row files with image paths, teacher box coordinates, teacher scores; lists of image paths; mask files. | The pre-launch verification of the mechanism code and the fix-map audit cannot be checked. |
| Internal-split evaluations (25 directories, 90 MB) | Ground truth of the internal evaluation split and predictions on it. | `internal_sensitivity_*.json` can be read but not recomputed. |

## Withheld: training-side code

| Item | Why | What a reader loses |
|---|---|---|
| `mech_patch.py`, `train_mech.py`, `fixmap_patch.py`, `train_fixmap.py` | Patches of the training and distillation code, which is not released. | The definition of the fixall / oldmask / randmask conditions can be read in the third addendum but not in code. The launch scripts in the bundle call these files and cannot run. |

## Withheld: row keys of restricted subsets

| Item | Why | What a reader loses |
|---|---|---|
| Mask files of the 9 masked runs and of the same-card randmask run (`*.mask.json`, 3.5 MB) | Lists of image-row keys, including keys from the withheld sources. | Cannot check which rows each masked run admitted, or that the same-card randmask run used the same key set as its pair. Only the counts per pass in the admission logs remain. |
| `old_gate_admitted_keys.json` (0.33 MB) | The 6,434 row keys of the old-gate condition. | Cannot rebuild the oldmask mask; `build_old_keys.py` is here but has no input. |

## Left out for size or because they add nothing to the recomputation

| Item | Why | What a reader loses |
|---|---|---|
| Training logs of the 44 new runs (about 1 GB) and of the 2 reused runs (46 MB) | Size; paths on every line. | Per-epoch training record; the card each run used (the same-card claim rests on these logs and on `c80_nvidia_smi.txt`, which is in the bundle with hardware identifiers and process ids masked and the process lines of the two other cards removed). |
| Checkpoints (`weights/`) | Not released. | Predictions cannot be regenerated. The endpoint values can be recomputed from the filed predictions, not from new ones (see the row on `val_gt_coco.json`). |
| `predictions_coco.json` of the 46 evaluation directories | Left out. It is the second input of `bootstrap_a04.py`. | The filed `predictions_coco_sha256` and `dt_sha256` cannot be checked. A working equivalent is written by `tools/recompute_map.py --export-view` from `predictions.json` and the ground truth of Online Resource 10 (rows mapped to integer image ids). With it the filed script passed its verify mode for two runs, and 12 of the 2,000 draws of each of the 46 runs were recomputed and were equal to the filed values. All 2,000 draws were not rerun. |
| `yolo_val.log` of the 46 evaluation directories, evaluation driver logs (13 files) | Contain server paths; not needed for the recomputations offered here. | The once-per-run evaluation record. |
| `args.yaml` of the 46 runs and the trainer argument files of the gate measurement | Training configuration with data paths; not needed for the recomputations offered here. | The full argument list of each run. |
| `STATE_KAIS_V4.md` | Working note, not needed for any result. | Nothing needed for a result. |
| Best-checkpoint evaluations (44 directories, 169 MB) | Sensitivity analysis only; same layout as the endpoint directories, with ground truth copies. | `bestpt_sensitivity_*.json` can be read but not recomputed. |
| Checkpoint provenance audit (7 files), comparability inputs (4 files) | Not part of the three main results; server paths, one e-mail-like string. The checkpoint provenance record, with server paths replaced by placeholders, is Online Resource 11 of the paper. | The supporting record for the provenance and comparability statements. |
| Aborted and invalid runs (11 attempts that enter no analysis; logs, model and evaluation directories, two draw files) | Enter no result. Ten were never evaluated. The wrongly configured CBox-M run at seed 20260703 had been evaluated once before its configuration error was found; its values are not used. Their existence is recorded in the timing record. | Nothing that enters a result. |

## Files that do not exist or were not found

| Item | Status | What a reader loses |
|---|---|---|
| Comparability audit table | No table file exists. Only its inputs exist (a recheck script and its result, a package list, an empty label-manifest check); the audit is prose in the supplementary text. | No table exists. The audit is given as text in Online Resource 1 of the paper. |
| Fourth-addendum index array as a file | Never stored. `bootstrap_a04.py` regenerates it from a fixed seed and checks its digest at run time (2000 x 2827 integers, about 45 MB if written). | Nothing, once the script can run; the per-draw values are in the bundle. |
| Source values of the checkpoint-rule table | Not found under the experiment folder; only the provenance record is there. | That table cannot be traced to a source file from this bundle. |
| `admission_audit.py` on the server | Was only on the authors' workstation. An unchanged copy is now in `tools/` (SHA-256 `2fd1d2fca09833311637eb0c3c96c07138f97fc48e7a430c907d48a64cda56e3`). | Nothing. |
| `eval_env.json` of the two reused runs | The earlier evaluation did not write it. | The environment record for those two evaluations. |
| Script that draws the admission figure from the per-row files | Does not exist. The figure script of the paper is in `tools/make_fig_admission.py`. It reads no file: the counts are typed in, and they are the counts of `runtime_gate_analysis.txt`. | The figure cannot be regenerated from the per-row files by script. |
