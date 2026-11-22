# Reproducing the reported results

All commands are run from the repository root. Outputs of the wrappers go to `_out/`, which is not tracked. Nothing is written into `evidence/`.

The outputs shown here were obtained on 21 Nov 2026 on a macOS machine, CPU only, with the scripts started as `python3 -I`. The interpreter that the wrappers found as `python3` was Python 3.9.23 with numpy 2.0.2 and scipy 1.13.1. A second interpreter (Python 3.11.12, numpy 2.4.6, scipy 1.17.1) was used where stated. Long outputs are trimmed; trimmed places are marked with `...`.

The wrappers use `python3`. Set the environment variable `PYTHON` to use another interpreter, for example `PYTHON=python3.10 sh scripts/recompute_analyses.sh`.

## 0. Integrity of the evidence files

What: every file under `evidence/` has the SHA-256 listed in `evidence/MANIFEST.sha256`, and no file is unlisted.

    sh scripts/verify_manifest.sh

Output:

    manifest entries: 555   files OK: 555
    verify_manifest: PASS

The same check without the wrapper: `cd evidence && sha256sum -c MANIFEST.sha256` (on macOS `shasum -a 256 -c MANIFEST.sha256`).

## 1. Run-time gate: admitted count and strata

What: during two instrumented passes over the training data the 0.999 IoU gate was observed for each of the 9,334 box-eligible teacher-evidence rows. The filed summary reports 6,434 admitted rows in both passes and the shares by class, source, image shape, object size and padding parity, the comparison of the two passes and the comparison of the static audit with run time.

Files: `evidence/gate_rows_nocoord/`. It holds three per-row CSV files for the 3,698 rows of the sources D3 and D4. For the other 5,636 rows it holds `restricted_cells.csv`, `restricted_class_term_counts.csv`, `restricted_aggregates.json`, three sorted value lists and one file of bin counts. The script is `runtime_gate_analyze_nocoord.py`; `README.txt` describes every file. Filed summary: `evidence/scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt`.

    sh scripts/recompute_gate.sh

Output:

    ==================== runtime_gate_rows_pass1_seed42.csv
    ADMITTED 6434  REJECTED 2900  of 9334  rate 0.6893
    ==================== runtime_gate_rows_pass2_seed1337.csv
    ADMITTED 6434  REJECTED 2900  of 9334  rate 0.6893
    ==================== pass comparison
    IDENTICAL to evidence/scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt
    IDENTICAL to evidence/gate_rows_nocoord/runtime_gate_analysis.txt
    lines: 123   output: _out/gate/runtime_gate_analysis.recomputed.txt
    recompute_gate: PASS

The full recomputed summary is `_out/gate/runtime_gate_analysis.recomputed.txt`. Its strata for pass 1 read:

    -- by class
       gun                          n= 5371 admitted= 3576 rejected= 1795 rate=0.6658
       knife                        n= 3457 admitted= 2615 rejected=  842 rate=0.7564
       stick                        n=  506 admitted=  243 rejected=  263 rate=0.4802
    ...
    -- by source
       D2                           n= 5470 admitted= 3839 rejected= 1631 rate=0.7018
       D3                           n= 2134 admitted= 1894 rejected=  240 rate=0.8875
       D4                           n= 1564 admitted=  695 rejected=  869 rate=0.4444
       other                        n=  166 admitted=    6 rejected=  160 rate=0.0361
    -- by size bin
       large>=96^2                  n= 7075 admitted= 4653 rejected= 2422 rate=0.6577
       medium                       n= 2037 admitted= 1580 rejected=  457 rate=0.7757
       small<32^2                   n=  222 admitted=  201 rejected=   21 rate=0.9054
    -- by image aspect
       square                       n= 1743 admitted= 1743 rejected=    0 rate=1.0000
       tall                         n=  930 admitted=  307 rejected=  623 rate=0.3301
       wide                         n= 6661 admitted= 4384 rejected= 2277 rate=0.6582

The same result was obtained with both interpreters. The script uses the standard library only.

Limits:

- The original per-row files hold image paths and box coordinates and are withheld. The filed script `runtime_gate_analyze.py` (in `evidence/as_filed/`) cannot run. The script used here is an adaptation of it; `evidence/gate_rows_nocoord/runtime_gate_analyze_nocoord.py` lists the differences in its first lines.
- For the 3,698 rows of D3 and D4 the summary is computed from per-row files. For the 5,636 rows of D2 and of the pooled sources no per-row record is released. Their part comes from count cells, from totals, and from sorted value lists or bin counts without row identifier.
- For these 5,636 rows, 34 of the 123 lines rest on yes/no flags that the authors evaluated on the unreleased values, and 6 lines rest on totals supplied by the authors. A reader cannot recompute these flags and totals. `python3 -I evidence/gate_rows_nocoord/runtime_gate_analyze_nocoord.py --status` prints a tag in front of every line.
- For these rows the admitted counts are supplied counts. They equal the static flag `ul_admitted_int` of Online Resource 12 in every cell; a reader can check this and nothing more.
- Some released values are rounded (gate IoU of admitted rows, edge offsets, one difference). The header of the script says why the printed digits do not change.
- The gate IoU and the edge offset of a row are precomputed values, not computed from coordinates.
- The object-size class and the static flags are precomputed columns.
- The `admitted` flag is the value recorded from the pipeline during the measurement. The gate itself is not rerun, and the training pipeline is not included.

## 2. Figure: admission by stratum

What: `assets/fig_admission.png`, the bar chart of admitted rows by class, image shape, source and object size.

    python3 scripts/make_fig_admission.py

It needs matplotlib and writes `_out/fig_admission.pdf`. The script used for the paper is `evidence/tools/make_fig_admission.py`; the two differ only in the first comment line and in the output path. The script reads no file. The counts are typed in at its top. They equal the counts of the filed summary (section 1); compare lines 5-8 of the script with the strata above. `assets/fig_admission.png` was rendered from the figure file of the paper with `pdftoppm -png -singlefile -scale-to-x 1600 -scale-to-y -1`. The script was run once (matplotlib 3.9.2) and wrote a PDF; the PDF was not compared pixel by pixel with the figure of the paper.

## 3. The two pre-specified experiments

What: the filed analysis scripts are run unchanged on the endpoint and prediction files under `evidence/`, and each output is compared with the filed result in every value. `evidence/README.md` (section "How to recompute each main-text result") maps each result of the main text to a step, an output file and the keys to read.

Needs numpy and scipy.

    sh scripts/recompute_analyses.sh

Single steps: `sh scripts/recompute_analyses.sh order` (order contrast table and mechanism contrasts Q1-Q6), `a04` (image-resampling intervals), `add06` (same-card comparison), `pairs` (byte identity of the seven prediction pairs), `digests` (filed digests of the scripts), `gate` (reads the gate counts from the summary and the meta files), `counts` (admitted-row bookkeeping of the 46 runs). Outputs are in `_out/recompute/`; the report is `_out/recompute/RECOMPUTE_REPORT.txt`. The exit status is 0 only if every comparison matches.

Output with Python 3.9.23, numpy 2.0.2, scipy 1.13.1 (exit status 0):

    python 3.9.23  numpy 2.0.2  scipy 1.13.1
    eval view: 46 runs (metrics_unified.json from scrubbed/, predictions.json from as_filed/)
    MATCH    filed digest of kais_v4/ANALYSIS_ADDENDUM_06.md
    ...
    MATCH    filed digest of kais_v4/analysis/image_offset_bound.py
    MATCH    analyze_kaisv4.py -> results_final_sbs.recomputed.json vs filed results_final_sbs_20261115T011951Z.json  (471 numeric values, all identical)
    MATCH    analyze_add06.py -> results_add06.recomputed.json vs filed results_add06_20261121T045950Z.json  (291 numeric values, all identical)
    MATCH    a04_contrasts.py -> a04_contrasts.recomputed.json vs filed a04_contrasts_20261115T012010Z.json  (354 numeric values, all identical)
    MATCH    prediction pair std seed 42: bytes identical and digests as filed  90282f869911254f2ffd866f57f4ea9bdb37d3957ab62ee501e95c57407ec459
    ...
    MATCH    prediction pair randmask seed 20260703: bytes identical and digests as filed  e14fe3734ccdbae7df69441f75fb9534931473010dda2f4a4b4e4290d968a6d5
        identical prediction pairs: 7 of 7
    MATCH    run-time gate: summary and meta files give one admitted/eligible count for both passes  admitted 6434 of 9334
        (read from the summary; the per-row files that produce it are not in the bundle)
    WROTE    current_kd_match_counts.tsv (46 runs; same columns as the filed historical table, which itself covers earlier runs whose summaries are not in the bundle)
    ...
    comparisons that differ: 0

In this run all 20 comparisons matched (9 digests, 3 analysis outputs, 7 prediction pairs, 1 gate count), and the three recomputed JSON files were byte-identical to the filed ones.

The note "the per-row files that produce it are not in the bundle" is printed by `evidence/tools/recompute.py`, which was written before `evidence/gate_rows_nocoord/` was added and was not changed. Use section 1 for the recomputation from the released files.

Output with Python 3.11.12, numpy 2.4.6, scipy 1.17.1 (exit status 1):

    python 3.11.12  numpy 2.4.6  scipy 1.17.1
    ...
    DIFFERS  analyze_kaisv4.py -> results_final_sbs.recomputed.json vs filed results_final_sbs_20261115T011951Z.json  75 differences
        $.C4-M - C1-M concurrent_A3.ci95[0]: -0.03024186825648305 -> -0.030241868256878936  (difference -3.959e-13)
        ...
    DIFFERS  analyze_add06.py -> results_add06.recomputed.json vs filed results_add06_20261121T045950Z.json  40 differences
        ...
    MATCH    a04_contrasts.py -> a04_contrasts.recomputed.json vs filed a04_contrasts_20261115T012010Z.json  (354 numeric values, all identical)
    ...
    comparisons that differ: 2

In this run 18 of the 20 comparisons matched. The 115 differences are in interval bounds (`ci95`) and p-values of the first two scripts. The largest absolute difference is 1.213e-12. Every other value and the whole third output are identical to the filed results. The comparison is exact, so any difference in the last digits is reported as `DIFFERS`.

What this means:

- The filed results were made with Python 3.10.12, numpy 2.2.6 and scipy 1.13.0 (`evidence/README.md`, "Requirements"; `evidence/_test_out/RECOMPUTE_REPORT.txt`, line 1). `requirements.txt` pins these two library versions. That environment was not available on the machine used for this document and was not rerun here. The record of the run in that environment is `evidence/_test_out/RECOMPUTE_REPORT.txt`.
- `evidence/README.md` reports differences of at most 8e-12 in 74 and 40 places with numpy 1.26.4 and scipy 1.10.1. The run above with numpy 2.4.6 and scipy 1.17.1 gave 75 and 40 places and at most 1.213e-12.
- Which library versions give exact equality was not studied beyond these runs.

## 3a. Endpoint values from the prediction files

What: mAP50-95, AP50, AP75 and the per-class values of the 46 runs are recomputed from `evidence/as_filed/eval/factorial_v3_freeze/<run>/predictions.json` and compared with `evidence/scrubbed/eval/factorial_v3_freeze/<run>/metrics_unified.json`.

Needs numpy and pycocotools, and files that are not in this repository: Online Resource 10 of the paper (validation ground truth without 87 boxes of two sources with restricted annotations) and the annotation files of these two providers (87 files for the validation split, no image).

1. Extract Online Resource 10; it holds the folder `S8_File/`.
2. Get the two providers' annotation files at the revisions named in `S8_File/README.md`, section "Withheld boxes". Keep the providers' own folder layout below each root; the rebuild script builds each annotation path from the image path in `S8_File/gt/provider_route_images.csv`. `evidence/README.md` ("Endpoint values from the prediction files", step 2) gives the download commands, the four annotation folders and the number of files in each.
3. Run `python3 S8_File/scripts/rebuild_provider_gt.py --split val --odw-root <first provider> --chips-root <second provider>`. It writes `S8_File/gt/val_gt_coco_full.json` (2,827 images, 2,151 boxes).
4. Run `python3 evidence/tools/recompute_map.py --or10 S8_File --mode full`.

Output on 22 Nov 2026 (Python 3.11.12, numpy 2.4.6, pycocotools 2.0.8; exit status 0):

    mode full; ground truth: 2827 images, 2151 boxes; 46 runs
    evaluator: pycocotools 2.0.8, numpy 2.4.6, Python 3.11.12
    settings: bbox, catIds [1, 2, 3], default COCOeval parameters; tolerance 1e-09
    C0-R-std-c80_seed1337_kaisv4mech             rows  2127  mAP filed 0.358926 recomputed 0.358926  max|diff| over 9 values 0.00e+00
    ...
    PASS: maximum absolute difference 0.00e+00 <= 1e-09 (414 values)

The tool maps each prediction row to the integer image id of the ground truth through `file_name` and stops if a file name or a category is unknown. The settings and the full record are in `evidence/README.md` ("Endpoint values from the prediction files") and `evidence/_test_out/MAP_RECOMPUTE_REPORT.txt`.

With `--draws 12` the tool also recomputed 12 of the 2,000 image-resampling draws of each run with the functions of the filed `bootstrap_a04.py`; they were equal to the filed values. All 2,000 draws were not rerun.

With `--mode public` (no rebuild; 87 boxes missing) the values differ from the filed ones: mAP is lower by 0.0014 to 0.0060. This mode gives no `PASS`.

Limits: the predictions themselves are not regenerated. The pycocotools version of the filed evaluation is not recorded. The rebuilt ground truth is not byte-identical to the file the filed evaluation read, so its filed digest cannot be checked.

## 4. Historical admitted-row counts

What: the table of admitted-row counts of earlier runs is read, not recomputed. Its digest can be checked.

    shasum -a 256 evidence/as_filed/kais_v4/audit_out/runtime_gate/historical_kd_match_counts.csv

Output: `4586609af83b55a8ac4a1faafdada381004190094a4f8f1caf2d1242c3318c65`, the value on the line for this file in `evidence/scrubbed/kais_v4/audit_out/runtime_gate/SHA256SUMS`.

## 5. The audit script

    python3 admission_audit/admission_audit.py --csv admission_audit/example_boxes.csv --strata image_shape

Output (first lines and the stratum table; the full output is in `admission_audit/README.md`):

    Admission audit, gate: IoU >= 0.999
      rows 16   admitted 12   share 0.7500
    ...
    By image_shape
      level        rows  admitted    share
      1280x720        4         4   1.0000
      1333x800        4         0   0.0000
      640x480         4         4   1.0000
      960x960         4         4   1.0000

The example uses synthetic boxes. It shows the interface. It does not reproduce a number of the paper.

## What cannot be reproduced, and why

From `evidence/README.md` ("Cannot be recomputed from the bundle") and `evidence/EXCLUDED.md`:

- The prediction files. They need the trained checkpoints, the validation images and the project evaluator. None of these is included. The endpoint values (`metrics_unified.json`) cannot be recomputed from this repository alone; with Online Resource 10 they can (section 3a).
- The per-draw values of the image-resampling analysis (`a04_draws/`) cannot be recomputed from this repository alone. With the ground truth of section 3a, 12 draws per run were recomputed and matched; all 2,000 draws were not rerun.
- The run-time gate summary from box coordinates. See the limits in section 1.
- The static padding audit itself. Its flags are included as precomputed columns; the coordinates they were computed from are not in this repository.
- The historical admitted-row table. The run summaries of the earlier runs are not included.
- The best-checkpoint and internal-split sensitivity results. No script file exists for them and their evaluation directories are not included.
- The mask and old-gate conditions of the mechanism experiment. The mask files and the key list are withheld; the admission logs give only counts per pass.
- That each run was trained as described. No training log, training code or checkpoint is included.
- The RFC 3161 timestamp tokens were not verified. The authority certificates are not included.
