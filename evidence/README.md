# Evidence files (Online Resource 13)

This directory holds the evidence files that accompany the paper: the core evidence behind the two
pre-specified experiments (the schedule-by-seed order experiment and the mechanism experiment with its
same-card control) and the run-time gate measurement. Online Resource 13 of the paper is this folder. In the
repository it is the folder `evidence/`; "the bundle" below means this folder, and the commands below are run
from inside it.

Everything in `as_filed/` and `scrubbed/` was copied from the project directory on the training server on
21 Nov 2026. Nothing in the project directory was changed. `gate_rows_nocoord/` was added afterwards on the
same day; its files were derived from per-row files that are not released (see its `README.txt`). The folder
was rebuilt on 22 Nov 2026: per-row files are now given only for the rows of the sources D3 and D4.
`MANIFEST.sha256` lists the SHA-256 of every file here. The copy of this folder that is filed with the journal
(Online Resource 13 of the paper) also holds `ARTICLE.txt`, which names the article, its authors and the
corresponding address. That file is not part of this folder and is not in the manifest.

## Layout

| Folder | Content | Files |
|---|---|---|
| `as_filed/` | Byte-for-byte copies of files whose digests are filed or whose bytes are themselves evidence. Same relative paths as in the project directory. | 217 |
| `scrubbed/` | Copies of files that are needed to recompute or check results but carried absolute paths, host names or user names. Same relative paths. `scrubbed/SCRUB_TABLE.tsv` maps each original SHA-256 to the SHA-256 of the scrubbed copy. | 301 + table |
| `tools/` | `scrub.py` (made the scrubbed copies), `recompute.py` (reruns the filed analysis scripts and compares), `admission_audit.py` (stand-alone gate audit tool, unchanged copy), `make_fig_admission.py` (script of Figure 1 of the paper; see "Figure script" below), `recompute_map.py` (recomputes the endpoint values from the prediction files and the ground truth of Online Resource 10; see "Endpoint values from the prediction files" below), the two file lists, an example rules file. | 8 |
| `_test_out/` | Outputs of the test run of 21 Nov 2026 made inside this bundle, the record of the follow-up check of the same day, and `MAP_RECOMPUTE_REPORT.txt` (test of `tools/recompute_map.py`, 22 Nov 2026). | 12 |
| `gate_rows_nocoord/` | Run-time gate measurement without coordinates. Per-row files for the 3,698 rows of the sources D3 and D4 (static audit and two passes, random row numbers). For the other 5,636 rows: count cells, class-term counts, totals, three sorted value lists and one file of bin counts, all without row identifier. `runtime_gate_analyze_nocoord.py`, a copy of the summary, `README.txt`, `SHA256SUMS.txt`. | 14 |
| `EXCLUDED.md` | What is deliberately not here, and what a reader loses. | |
| `MANIFEST.sha256` | `sha256  relative/path` for every file, sorted. Check with `sha256sum -c MANIFEST.sha256`. | |

### as_filed/

- `kais_v4/PROTOCOL_KAIS_V4.md` with `.tsq`, `.tsr` and `.frozen_at`: the frozen protocol.
- `kais_v4/ANALYSIS_ADDENDUM_01.md` ... `_06.md`, `ANALYSIS_ADDENDUM_06.sha256`, `ANALYSIS_CODE_RECORD_01.md`,
  each with its RFC 3161 request (`.tsq`) and reply (`.tsr`).
- `kais_v4/analysis/`: the six analysis scripts whose digests are filed (`analyze_kaisv4.py`,
  `analyze_add06.py`, `a04_contrasts.py`, `bootstrap_a04.py`, `eval_kaisv4.py`, `image_offset_bound.py`);
  the results files (`results_final_sbs_*`, `results_add06_*`, `results_partial_*` x3, `a04_contrasts_*`,
  `bestpt_sensitivity_*`, each with tokens; `internal_sensitivity_20261114.json` and `..._20261114b.json`
  without tokens); `a04_draws/` (92 files: per-draw values and verification record of 46 models) and
  `a04_verify_july/` (2 files).
- `kais_v4/phase4_view_schedules_v4_kais_shuffled.yaml`, its `.sha256`, and `build_v4_shuffled_schedules.py`.
- Launch and queue scripts: `kais_v4/run_v4_common.sh`, `run_v4_cbox.sh`, `queue_L6.sh`, `swap_cbox_h100.sh`,
  `auto_eval_loop.sh`, `auto_eval_loop2.sh`, `auto_best_loop.sh`; `kais_v4/ablation_fixmap/run_mech.sh`,
  `queue_wave2.sh`, `run_abl.sh`, `build_old_keys.py`, `run_mech_c80.sh`, `queue_c80.sh`.
- `kais_v4/audit_out/runtime_gate/`: `runtime_gate_audit.py`, `runtime_gate_analyze.py`, `hist_summaries.py`,
  `historical_kd_match_counts.csv`.
- `eval/factorial_v3_freeze/<run>/predictions.json` for the 46 evaluation directories
  (22 pre-specified, 2 replicates, 2 reused, 13 mechanism, 7 same-card).

### scrubbed/

- `eval/factorial_v3_freeze/<run>/metrics_unified.json` (46) and `eval_env.json` (44; the two reused runs
  never had one).
- `models/students/<run>/` run summaries (two JSON files per run) and `results.csv` (46 runs).
- `kais_v4/logs/*.admission.jsonl` (10), the chain and queue logs of the three groups of runs, the smoke log
  and `c80_nvidia_smi.txt` (the card snapshot of the same-card runs; see the note on it below).
- `kais_v4/audit_out/runtime_gate/`: `runtime_gate_analysis.txt` (the summary), the three
  `runtime_gate_meta_*.json`, the two run logs, `SHA256SUMS`, `pre_train_cache.sha256`.
- `kais_v4/PROVENANCE_KAIS_V4.md` (the timing record; original SHA-256 on 21 Nov 2026
  `f774b12f5774a7b60b9303b86cd3509116b3f7f918ff040d0de85c11e74e7633`; the original was still being appended
  that day, so this digest is not final).
- `kais_v4/analysis/eval_kaisv4_best.py`, `eval_kaisv4_internal.py` (no filed digest).

How the copies were made: `tools/scrub.py` applies an ordered list of replacements to the text of each file.
The project directory became `<PROJECT_ROOT>`, the rest of the shared storage path `<NAS_ROOT>` or
`<NAS_MOUNT>`, home directories `<HOME>`, host names `<HOST>`, user names `<USER>`, e-mail-like strings
`<EMAIL>`, GPU hardware identifiers `GPU-<UUID>`, process ids `<PID>`. The site-specific rules contain the
real names and are therefore not stored here; `tools/scrub_rules.example.json` shows their form. 199 of the
301 files changed (1,808 replacements, a removed line counted as one); 102 were already clean and are
identical to the original. For every JSON and JSON-lines file the script parsed the original and the copy
and required all numeric values and the key structure to be identical (195 files, no failure); the one
exception is the `pid` field described below. For other text files it required unchanged line counts and no
change outside replaced lines.

Hardware identifiers and process ids (follow-up of 21 Nov 2026; built-in rules of `tools/scrub.py`):

- `kais_v4/logs/c80_nvidia_smi.txt`: the three GPU hardware identifiers became `GPU-<UUID>` (10 places).
  The two per-process lines of devices 0 and 1 were removed (device 1 was in use by another user); the seven
  per-process lines of device 2, the card the same-card runs used, are kept with their memory figures.
  The process id became `<PID>` in those seven lines and in the seven command lines below them (14 places).
  The per-card table (index, model, memory in use) is kept for all three cards. Because the ids are masked,
  the copy no longer shows which of the seven command lines belongs to which per-process line, and it can
  no longer be matched to the admission log of the same-card randmask run by process id. The file has two
  lines fewer than the original; the line check was made against the original without those two lines.
  `tools/scrub_rules.example.json` carries the entry that names this file and the kept device index.
- `kais_v4/logs/*.admission.jsonl` (10 files, 151 records each): the value of the `pid` field became the
  string `"<PID>"` (1,510 places). `tools/recompute.py` reads only `calls`, `has_box` and `labels` from
  these files, so no value it uses changed. Every other field (906 numeric values per file) is identical to
  the original; the `pid` field is the only one whose type changed (integer to string) and it is excluded
  from the numeric comparison by name. Each file had a single process id in all its records.
- `scrubbed/SCRUB_TABLE.tsv` has the new digests and counts for these 11 files; the `original_sha256`
  column is unchanged.

Not replaced, on purpose: the two machine labels used throughout the protocol and the timing record
(`H100`, `r7525`, also in file names and in the GPU model field). They are kept on purpose: they are
hardware labels, not network host names, and the timing record cannot be read without them. Relative paths
and internal names of the training code (for example the prefix of the run-summary file names and the
environment name) were also left; the section "Known residue in the contents of scrubbed files" lists them.

## How to recompute each main-text result

Requirements: Python 3 with numpy and scipy (tested with Python 3.10.12, numpy 2.2.6, scipy 1.13.0). CPU only.
The filed results were made with these library versions. Exact equality with the filed results was also
obtained with Python 3.9.23, numpy 2.0.2 and scipy 1.13.1 (20 `MATCH` lines, exit status 0). Under other
library versions `tools/recompute.py` prints `DIFFERS` lines for the first two scripts and ends with exit
status 1. Measured: with Python 3.11.12, numpy 2.4.6 and scipy 1.17.1, 75 and 40 differences of at most
1.3e-12; with Python 3.10.12, numpy 1.26.4 and scipy 1.10.1, 74 and 40 differences of at most 8e-12. The
differences are in interval bounds and p-values; every other value and the whole third output are
identical. Which library causes them was not isolated.
Run from the bundle directory. One command does everything:

    python3 tools/recompute.py

It writes into `_test_out/` and prints `MATCH` or the exact differences for every comparison
(`_test_out/RECOMPUTE_REPORT.txt`). The files in `_test_out/` are listed in `MANIFEST.sha256`; a new run
overwrites them (the first line of the report names the library versions), so use `--out DIR` if the manifest
is to stay valid. Single steps: `python3 tools/recompute.py order`, `add06`, `a04`, `pairs`,
`gate`, `counts`, `digests`. Add `--out DIR` to write elsewhere.

The filed scripts are not edited and not imported. Each one takes its input directory on the command line
and expects `<eval_root>/<run>/metrics_unified.json` (the sixth-addendum script also
`<eval_root>/<run>/predictions.json`). Here the endpoint files are in `scrubbed/` and the prediction files in
`as_filed/`, so `recompute.py` builds a temporary directory of links, `<out>/eval_view/<run>/`, that puts
the two side by side, and starts each filed script as its usage line says. The links are symbolic links
(`os.symlink`); on a system where the user may not create symbolic links this step fails (not tested). With `--keep-view` the directory
is kept and the scripts can be started by hand, for example:

    python3 tools/recompute.py --keep-view digests
    python3 as_filed/kais_v4/analysis/analyze_kaisv4.py _test_out/eval_view  my_results.json
    python3 as_filed/kais_v4/analysis/analyze_add06.py  _test_out/eval_view  my_add06.json
    python3 as_filed/kais_v4/analysis/a04_contrasts.py  as_filed/kais_v4/analysis/a04_draws _test_out/eval_view my_a04.json

| Result in the main text | Command | Output to read | Compare with (in `as_filed/kais_v4/analysis/`) |
|---|---|---|---|
| Order contrast table (schedule by seed): primary contrast, decision, baseline contrasts with Holm p-values, variance components of the shuffled grid, crossed interval | `python3 tools/recompute.py order` | `_test_out/results_final_sbs.recomputed.json`, keys `primary_frozen`, `baseline_contrasts`, `shuffled_grid_anova`, `crossed_A2_frozen`, and the `_A3` / `concurrent` keys | `results_final_sbs_20261115T011951Z.json` |
| Mechanism contrasts Q1-Q6 with labels and per-class values; endpoint list | same command | same file, keys `mechanism` and `endpoints` | same file |
| Image-resampling intervals of the contrasts (fourth addendum) | `python3 tools/recompute.py a04` | `_test_out/a04_contrasts.recomputed.json` | `a04_contrasts_20261115T012010Z.json` |
| Same-card comparison: contrasts Q1s, Q3s-Q6s, the seven card pairs and their summary | `python3 tools/recompute.py add06` | `_test_out/results_add06.recomputed.json`, keys `same_card_80GB`, `card_pairs`, `card_pairs_summary` | `results_add06_20261121T045950Z.json` |
| Byte identity of the seven prediction pairs | `python3 tools/recompute.py pairs` | `_test_out/card_pairs_sha256.tsv` | field `predictions_sha256_*` of `card_pairs` in `results_add06_20261121T045950Z.json`, and the table below |
| Run-time gate summary counts (6,434 admitted of 9,334 eligible rows, both passes) | `python3 tools/recompute.py gate` | `_test_out/gate_counts.tsv` | `scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt` and the two `runtime_gate_meta_pass*.json`. This step only reads the summary. Its printed note that the per-row files are not in the bundle was written before `gate_rows_nocoord/` was added; `tools/recompute.py` and `_test_out/` were not changed. |
| Run-time gate summary recomputed from the released files: the admitted count, the shares by class, source, image shape and object size, the pass comparison and the static-versus-run-time comparison | in `gate_rows_nocoord/`: `python3 -I runtime_gate_analyze_nocoord.py > out.txt` | `out.txt` (123 lines) | `cmp out.txt runtime_gate_analysis.txt`; the same bytes as `scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt`. See the limits in the next section. |
| Historical admitted-row counts | `sha256sum as_filed/kais_v4/audit_out/runtime_gate/historical_kd_match_counts.csv` | digest `4586609af83b55a8ac4a1faafdada381004190094a4f8f1caf2d1242c3318c65` | the line for this file in `scrubbed/kais_v4/audit_out/runtime_gate/SHA256SUMS`. The table is read, not recomputed; see below. `python3 tools/recompute.py counts` writes the same columns for the 46 runs of this bundle (`_test_out/current_kd_match_counts.tsv`) and prints the first and last record of each admission log. |
| Filed digests of the analysis and launch scripts | `python3 tools/recompute.py digests` | `MATCH` lines | `ANALYSIS_ADDENDUM_06.sha256`, `ANALYSIS_CODE_RECORD_01.md` |

The RFC 3161 tokens can be checked with OpenSSL, for example
`openssl ts -reply -in X.tsr -text` and `openssl ts -verify -data X -in X.tsr -CAfile <authority chain>`;
the authority certificates are not in the bundle and this was not run in the test.

### Endpoint values from the prediction files (needs Online Resource 10)

The endpoint values in `metrics_unified.json` (mAP50-95, AP50, AP75 and the per-class values) can be
recomputed from the `predictions.json` files of this bundle. The validation ground truth is not in this
bundle. It is in Online Resource 10 of the paper, without 87 boxes of two sources with restricted
annotations; a script in Online Resource 10 rebuilds these boxes from the providers' own files.

Requirements: Python 3 with numpy and pycocotools (tested with Python 3.11.12, numpy 2.4.6, pycocotools 2.0.8).

1. Extract Online Resource 10. It holds one folder, `S8_File/`, called `OR10` below. The README inside
   Online Resource 10 keeps the labels of an earlier version of the article (for example "S8 File",
   "S1 Appendix" and "Table 7").
2. Get the annotation files of the two providers at the revisions named in `OR10/README.md` (section
   "Withheld boxes"). The validation split needs 87 files: 53 XML files of one provider and 34 text files of
   the other (32,612 bytes in the test). No image is needed. These files are not in either archive.
   Keep the providers' own folder layout below each root (a clone or snapshot at the named revision has it).
   The script builds each annotation path from the image path in `OR10/gt/provider_route_images.csv`;
   the same files in one flat folder are not found.
   The 87 files lie in four folders:
   `Knife_detection/annotations/` (44 XML files),
   `Weapons and similar handled objects/Sohas_weapon-Detection/annotations/xmls/` (8 XML files),
   `Weapons and similar handled objects/Sohas_weapon-Detection/annotations_test/xmls/` (1 XML file) and
   `Handgun_vs_BagOfChips/labels/` (34 text files). All four are needed; the script stops if a file is missing.
   Commands for a full copy at the pinned revisions (images included; not run in the test, size not measured):

       git clone https://github.com/ari-dasci/OD-WeaponDetection
       git -C OD-WeaponDetection checkout 48860b990e4d4f57fe100248887fceb248475dc8
       git clone https://huggingface.co/datasets/Simuletic/Weapon_Detection_Dataset_Handgun_vs_BagOfChips
       git -C Weapon_Detection_Dataset_Handgun_vs_BagOfChips checkout 265ae3c929be2e6fc24a2612eae6ad3b0dd87381

   In the test the 87 files were fetched one by one, without images, from addresses of this form:

       https://raw.githubusercontent.com/ari-dasci/OD-WeaponDetection/48860b990e4d4f57fe100248887fceb248475dc8/<folder>/<image name without extension>.xml
       https://huggingface.co/datasets/Simuletic/Weapon_Detection_Dataset_Handgun_vs_BagOfChips/resolve/265ae3c929be2e6fc24a2612eae6ad3b0dd87381/Handgun_vs_BagOfChips/labels/<image name without extension>.txt

   The image names are in `OR10/gt/provider_route_images.csv` (column `provider_path`, rows with split `val`).
3. Rebuild the ground truth as `OR10/README.md` says:
   `python3 OR10/scripts/rebuild_provider_gt.py --split val --odw-root <first provider> --chips-root <second provider>`.
   It writes `OR10/gt/val_gt_coco_full.json` (2,827 images, 2,151 boxes).
4. From the bundle directory: `python3 tools/recompute_map.py --or10 OR10 --mode full --out my_table.tsv`.
   It prints one line per run and ends with `PASS` or `FAIL` (tolerance 1e-9). Exit status 0, 1 or 2.
   A full run finds 46 run directories and ends with `(414 values)`. If another number of directories is
   found, the tool prints a `NOTE` line and its result covers only the directories found.

Image-id mapping: each row of `predictions.json` carries `file_name`; the ground truth of Online Resource 10
gives each image an integer `id` and the same `file_name`; the tool maps each row to that `id` and stops if a
`file_name` or a `category_id` is unknown.

Evaluation settings: pycocotools `COCOeval`, `bbox`, category ids 1, 2, 3 (knife, gun, stick), all other
parameters at their defaults (IoU 0.50 to 0.95 in steps of 0.05, 101 recall thresholds, at most 100
detections per image, area range `all` for the reported values), all 2,827 images scored. These are the
settings stated in `as_filed/kais_v4/analysis/bootstrap_a04.py` (lines 6-7 and 40-52) for mAP50-95 and
the per-class AP. The project evaluator that wrote `metrics_unified.json` is not in the bundle, so the
rule for AP50, AP75 and the per-class AP50 (the same quantities at one IoU threshold) is not stated in a
filed file; the tool's rule gives the filed values. Every row of `predictions.json` is used;
the lowest score in the 46 files is 0.001 and no image has more than 16 rows.

Measured agreement (22 Nov 2026, record in `_test_out/MAP_RECOMPUTE_REPORT.txt`): for all 46 runs the nine
recomputed values per run are equal to the filed values (414 values, maximum absolute difference 0).
The 46 directories hold 37 distinct prediction files; nine files occur in two directories (the seven card
pairs below, and the two reused runs, whose files equal those of two other directories). Each directory
was compared with its own endpoint file.
With `--evaluator faster-coco-eval` (version 1.6.7) one value differed by 1.11e-16. The pycocotools
version of the filed evaluation is not recorded (`eval_env.json` has `"pycocotools": "?"`).
With `--mode public` (the 87 boxes missing) the values differ from the filed ones: mAP is lower by 0.0014
to 0.0060, and the largest difference of any of the nine values is 0.038. Public mode gives no `PASS`.

Image-resampling draws: `--draws N` recomputes N of the 2,000 draws per run with the functions of the filed
`bootstrap_a04.py` (loaded unchanged) and compares them with `a04_draws/<run>.draws.npy`. In the test, 12
draws for each of the 46 runs were equal to the filed values (maximum absolute difference 0); the other
draws were not recomputed. The filed script scores each draw with its image indices sorted in ascending
order (`np.sort` in the functions `fast` and `resampled_json`). In a separate check of six draws (two runs,
draws 7, 911 and 1733) with an independent implementation, the sorted order gave the filed values exactly,
and the same images in draw order gave values that differed by 2e-6 to 1.3e-5. The tool does not write a
bytecode file into the bundle when it loads the filed script. `--export-view DIR` writes evaluation directories in the layout that
`bootstrap_a04.py` reads, so that the filed script can be started by hand. The exported files hold
ground-truth boxes of the restricted sources; do not redistribute them.

### The seven prediction pairs (SHA-256 of `predictions.json`, 40 GB card run = 80 GB card run)

| Condition, seed | Run on the 40 GB card | Run on the 80 GB card | SHA-256 of both files |
|---|---|---|---|
| std, 42 | `C1-M-std_seed42_kaisv4mech` | `C1-M-std-c80_seed42_kaisv4mech` | `90282f869911254f2ffd866f57f4ea9bdb37d3957ab62ee501e95c57407ec459` |
| std, 1337 | `C1-M-std_seed1337_kaisv4mech` | `C1-M-std-c80_seed1337_kaisv4mech` | `7fb028c4600b11fa8a99bdb102030ab6fbdf370969d7e400fbb5fd84be5fc4a8` |
| std, 20260703 | `C1-M_seed20260703_kaisv4` | `C1-M-std-c80_seed20260703_kaisv4mech` | `4673ccf97e80a7ebe543d2ef96cff3393ceec4cf29b1b880f9edaf5de3f506aa` |
| no-KD, 42 | `C0-R-std_seed42_kaisv4mech` | `C0-R-std-c80_seed42_kaisv4mech` | `cd71252e7673eb971d30ac1df1a054e8d81833cdbc431a1031be2047ed2deaa7` |
| no-KD, 1337 | `C0-R-std_seed1337_kaisv4mech` | `C0-R-std-c80_seed1337_kaisv4mech` | `101a2c9e81ff95d3e58022c1e49110d2ab9347a0836cd64312b05e68ecb11947` |
| no-KD, 20260703 | `C0-R_seed20260703_kaisv4` | `C0-R-std-c80_seed20260703_kaisv4mech` | `f5f61633dd4a991c111ab6b9b6ad4631b847143a03d8e2be1fb9975b485abc05` |
| randmask, 20260703 | `C1-M-randmask_seed20260703_kaisv4mech` | `C1-M-randmask-c80_seed20260703_kaisv4mech` | `e14fe3734ccdbae7df69441f75fb9534931473010dda2f4a4b4e4290d968a6d5` |

In each pair the two files have the same digest, so they are byte-identical.

## Figure script

`tools/make_fig_admission.py` is the script that drew Figure 1 of the paper (rows admitted by the gate, by
class, image shape, source and object size). It is the script used for the paper. After the
figure file was written, its first comment line was reworded and the line that also wrote a PNG file was
removed; the plotting code and the counts were not changed. Its first comment line names a table of an earlier
draft; the counts are those of the figure. It
reads no file. The counts are typed in at its top; they were typed in from
`scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt` (sections "by class", "by image aspect",
"by source", "by size bin" and the line "ADMITTED"). It needs matplotlib and writes `Fig1.pdf` into its own
folder; a file written there is not listed in `MANIFEST.sha256`, so remove it before a manifest check. The
repository copy `scripts/make_fig_admission.py` differs from it only in the first comment line and in the
output path (`_out/fig_admission.pdf`).

## Cannot be recomputed from the bundle

(The run-time gate item below was corrected when `gate_rows_nocoord/` was added, and again when the folder
was rebuilt on 22 Nov 2026.)

- (Corrected on 22 Nov 2026.) The prediction files: they need the trained checkpoints, the validation
  images and the project evaluator (`eval_kaisv4.py` is here as filed but cannot run without them). The
  endpoint values (`metrics_unified.json`) cannot be recomputed from this bundle alone, because the
  validation ground truth is not in it. They can be recomputed from the prediction files together with
  Online Resource 10 and the providers' annotation files; see "Endpoint values from the prediction files".
- (Corrected on 22 Nov 2026.) The per-draw values in `a04_draws/` cannot be recomputed from this bundle
  alone: `bootstrap_a04.py` needs the validation ground truth and `predictions_coco.json`, neither of which
  is in the bundle. With the ground truth rebuilt from Online Resource 10, `tools/recompute_map.py` writes
  both inputs (`--export-view`) or recomputes chosen draws (`--draws`). 12 draws per run were recomputed
  and were equal to the filed values; all 2,000 draws were not rerun.
- The run-time gate summary from box coordinates. The filed script `runtime_gate_analyze.py` needs the
  original per-row files and the row-level padding audit, which hold coordinates and image paths and are not
  in the bundle, so it cannot run here. The command in `gate_rows_nocoord/README.txt` (also in the table
  above) recomputes the summary from the files of that folder; the output is byte-identical to the summary.
  Limits: per-row files are given only for the 3,698 rows of the sources D3 and D4. For the 5,636 rows of D2
  and of the pooled source the inputs are count cells, totals, and sorted value lists or bin counts without
  row identifier. For these rows 34 of the 123 lines rest on yes/no flags that the authors evaluated on the
  unreleased values (run-time padding parity, the geometry checks, the comparisons between the passes), and
  6 lines rest on totals supplied by the authors. A reader cannot recompute these. The admitted counts of
  these rows are supplied counts; they equal the static flag `ul_admitted_int` of Online Resource 12 in
  every cell. The gate IoU and the edge offsets are precomputed values, not computed from coordinates, and
  some are rounded. The size class and the static flags are precomputed as well. The `admitted` flag is the
  one recorded from the pipeline during the measurement; the gate itself is not rerun.
  `gate_rows_nocoord/README.txt` states what the files still disclose about images and boxes. The digest of the summary is filed in `SHA256SUMS`
  (the summary needed no scrubbing, so its digest is unchanged).
- The historical admitted-row table: `hist_summaries.py` reads the run summaries of earlier runs, which are
  not in the bundle.
- The best-checkpoint and internal-split sensitivity results (`bestpt_sensitivity_*`, `internal_sensitivity_*`):
  the evaluation scripts are in `scrubbed/kais_v4/analysis/` (`eval_kaisv4_best.py`, `eval_kaisv4_internal.py`),
  but no script that writes the two kinds of result file is in the bundle, and their evaluation directories
  are not in the bundle.
- The mask and old-gate conditions of the mechanism experiment: the mask files and the key list are not in
  the bundle; the admission logs give only counts per pass.
- That each run was trained as described: no training log, training code or checkpoint is in the bundle.
- The digests in `scrubbed/kais_v4/audit_out/runtime_gate/SHA256SUMS` for the two run logs and the three meta
  files refer to the originals; use the `original_sha256` column of `scrubbed/SCRUB_TABLE.tsv` to see that
  they agree.

## Known residue in as-filed files

These files could not be changed without breaking filed digests or byte identity.

- Absolute project path (the string that became `<PROJECT_ROOT>` or `<NAS_ROOT>` elsewhere) in 15 scripts:
  `kais_v4/ablation_fixmap/queue_c80.sh`, `queue_wave2.sh`, `run_abl.sh`, `run_mech_c80.sh`, `run_mech.sh`;
  `kais_v4/analysis/eval_kaisv4.py`; `kais_v4/audit_out/runtime_gate/hist_summaries.py`,
  `runtime_gate_audit.py`; `kais_v4/auto_best_loop.sh`, `auto_eval_loop2.sh`, `auto_eval_loop.sh`,
  `queue_L6.sh`, `run_v4_cbox.sh`, `run_v4_common.sh`, `swap_cbox_h100.sh`.
  No home directory, host name, user name or e-mail-like string was found in these 15 files.
- E-mail-like strings in all 16 `.tsr` files: contact addresses inside the certificates of the two timestamp
  authorities (binary DER data). They are not addresses of the authors.
- Machine labels (`H100`, `r7525`) in the protocol, the addenda and several script and log names. Kept on
  purpose (see above).
- The method name and the journal abbreviation occur inside the text of as-filed files (counted on
  21 Nov 2026 by a search of all 171 as-filed files other than `predictions.json`; none in the `.tsr` and
  `.tsq` files, none in the 46 `predictions.json` files):
  - The method name: 4 occurrences in 4 files. Written out in the heading of `kais_v4/PROTOCOL_KAIS_V4.md`
    (line 1) and in the docstring of `kais_v4/audit_out/runtime_gate/runtime_gate_audit.py` (line 2);
    in compact form inside the seed string of the fourth addendum, in `kais_v4/ANALYSIS_ADDENDUM_04.md`
    (line 37) and `kais_v4/analysis/bootstrap_a04.py` (line 21).
  - The journal abbreviation as a word of running text: 15 occurrences in 15 files, one each. The heading of
    `kais_v4/PROTOCOL_KAIS_V4.md`; the headings of `kais_v4/ANALYSIS_ADDENDUM_01.md` ... `_06.md` and of
    `kais_v4/ANALYSIS_CODE_RECORD_01.md`; the first comment or docstring line of
    `kais_v4/run_v4_common.sh`, `run_v4_cbox.sh`, `build_v4_shuffled_schedules.py`,
    `kais_v4/ablation_fixmap/run_abl.sh`, `run_mech.sh`, `run_mech_c80.sh` and
    `kais_v4/analysis/analyze_add06.py`.
  - The journal abbreviation inside the same seed string: 2 occurrences (`ANALYSIS_ADDENDUM_04.md`,
    `bootstrap_a04.py`). The seed string cannot be changed: the index array of the fourth addendum is
    generated from it.
  - The journal abbreviation in upper case inside the names of the protocol and timing-record files, where
    the text of other files mentions those names: 14 occurrences in 10 files (the six addenda, the code
    record, `PROTOCOL_KAIS_V4.frozen_at`, `auto_eval_loop.sh`, `auto_eval_loop2.sh`; counted together with
    the lines above that is 31 upper-case occurrences in 19 files).
  - The same abbreviation in lower case, as part of the folder name and of the run names (the suffix of the
    46 run names and the names of the analysis scripts): 458 further occurrences; in all 82 of the 171 files
    contain the abbreviation in some form.
  None of these files was edited.
- `predictions.json` (46 files) does not list all validation images. Each row is one detection and carries
  the file name of its image, so an image appears only if the model gave at least one detection for it.
  Counted on 21 Nov 2026: 2,262 distinct file names across the 46 files (1,399 to 1,535 per file) of the
  2,827 validation images; 565 validation images are named in none of them. The 2,827 is the
  `images_scored` value in all 48 verification records (`a04_draws/*.verify.json`, `a04_verify_july/`) and
  the image count fixed in `bootstrap_a04.py` and the fourth addendum; the list of validation images itself
  is not in the bundle. It is in the ground truth of Online Resource 10 (2,827 image entries). Names and model outputs only; no annotation.
  The file names begin with these source prefixes (number of distinct names):
  `hf_w_turki_ds_<n>__` with n = 1, 5 or 6 (1,015: 41, 130 and 844);
  a hexadecimal string followed by `-<number>`, no word prefix (865);
  `cocohn_` (295);
  `hf_w_chips_` (34);
  a title-like word followed by a number, no separator (53: `KnifeDefenseKrav` 16, `knifeDefenseTechnique` 12,
  `RealityKnifeAttacks` 11, `DefenseAndSurvive` 8, `online` 5, `img` 1).
  After the prefix many names keep fragments of the upstream file name. Which of these prefixes belong to
  sources with restricted annotations or images was not established in this check and is not stated here.
- The protocol and addenda say "the corresponding author" without a name. They were searched for e-mail
  addresses and organisation words; they were not read line by line.
- Directory and file names carry internal project and planning tokens (for example the name of the top folder
  under `as_filed/`). Renaming would break the relative paths the filed scripts and digest lists use.

`scrubbed/`, `tools/`, `README.md` and `EXCLUDED.md` contain none of: the project path, a home directory,
the host names, the user names, an e-mail-like string, a GPU hardware identifier (checked on 21 Nov 2026,
see below). `gate_rows_nocoord/` was added after that check and rebuilt on 22 Nov 2026. Its ten data files
(nine CSV files and one JSON file) contain no `/` and no `@` character; its `README.txt`, `SHA256SUMS.txt`
and script contain no home directory and no e-mail-like string, and the built-in rules of `tools/scrub.py`
find no match in the folder (item 14 of the test record).
A search for the host names and user names with the site rules was not repeated for this folder.

## Known residue in the contents of scrubbed files

The scrub removed absolute paths, host names, user names, e-mail-like strings, GPU hardware identifiers and
process ids. It did not remove internal names. The following are still in the text of files under
`scrubbed/` and `tools/`, not only in file names (counted on 21 Nov 2026 after the follow-up scrub):

- The project token (the lower-case token that begins the name of the run-summary files): 322 occurrences
  in 55 files. All 46 `models/students/<run>/*_run_summary.json` (in the relative paths of the schedule
  file and of the evidence bank); `kais_v4/PROVENANCE_KAIS_V4.md`; `kais_v4/analysis/eval_kaisv4_best.py`;
  `kais_v4/audit_out/runtime_gate/pre_train_cache.sha256`, `run_pass1_seed42.log`, `run_pass2_seed1337.log`;
  `kais_v4/logs/SMOKE_r7525.log`, `kais_v4/logs/c80_nvidia_smi.txt`; the path columns of
  `scrubbed/SCRUB_TABLE.tsv` and `tools/scrub.list` (the run-summary file names). In 50 of these files the
  full name of the project folder occurs (103 occurrences).
- The dataset folder name (the folder under `<NAS_ROOT>/00_data/`): 8 occurrences in 4 files,
  `kais_v4/audit_out/runtime_gate/pre_train_cache.sha256`, `run_pass1_seed42.log`, `run_pass2_seed1337.log`
  and `kais_v4/logs/SMOKE_r7525.log`.
- Training-script paths: 7 command lines in `kais_v4/logs/c80_nvidia_smi.txt` (the relative path of the
  training script six times and of the mechanism training script once, each with the start of a
  relative config path). The run summaries also keep the relative path of the schedule file (47 values in
  the 46 files and the smoke log).
- The relative path of the evidence bank, with its SHA-256: in all 46
  `models/students/<run>/*_run_summary.json` and in `kais_v4/logs/SMOKE_r7525.log` (47 files; the path 47
  times, the digest 94 times, as `evidence_sha256` and `provided_evidence_sha256`).
- The environment name (the folder under `<NAS_ROOT>/envs/`): 9 occurrences in 3 files,
  `kais_v4/logs/c80_nvidia_smi.txt` (7), `kais_v4/PROVENANCE_KAIS_V4.md` and
  `kais_v4/analysis/eval_kaisv4_best.py`.
- An image-name source prefix: 2 occurrences in `kais_v4/analysis/eval_kaisv4_internal.py` (docstring and
  the constant that selects the internal split). No other file under `scrubbed/` or `tools/` contains an
  image name or an image-name prefix; the run-time gate summary names sources only by the labels
  `D2`, `D3`, `D4` and `other`.
- The machine labels `H100` and `r7525`, kept on purpose (see "Not replaced, on purpose" above): 183
  occurrences in 59 files (the 44 `eval_env.json`, the timing record, `eval_kaisv4_best.py`, nine chain and
  queue logs, the smoke log, `c80_nvidia_smi.txt`, and the path columns of `SCRUB_TABLE.tsv` and
  `tools/scrub.list`). Also kept: the GPU model names and memory figures of all three cards in
  `kais_v4/logs/c80_nvidia_smi.txt`.

## Test record (21 Nov 2026, inside this bundle, CPU only)

1. All 217 `as_filed/` files have the same SHA-256 as the originals
   (`_test_out/as_filed_original.sha256` and `_test_out/as_filed_bundle.sha256` are identical).
2. `analyze_kaisv4.py`, `analyze_add06.py` and `a04_contrasts.py`, run unchanged on the scrubbed endpoint
   files, gave outputs equal to the filed results in every value: 471, 291 and 354 numeric values, no
   difference. The three output files are also byte-identical to the filed ones.
3. The seven prediction pairs are byte-identical and their digests equal those in the filed results.
4. A search of the whole bundle for the project path, home directories, host names, user names and
   e-mail-like strings found matches only in the as-filed files listed above.
5. The nine digests filed in `ANALYSIS_ADDENDUM_06.sha256` and `ANALYSIS_CODE_RECORD_01.md` match the bundle copies.

Follow-up check (21 Nov 2026, inside this bundle, CPU only; record in `_test_out/followup_check.txt`):

6. After the follow-up scrub of the 11 files named above, `python3 tools/recompute.py` was run again with
   all steps under Python 3.10.12, numpy 2.2.6, scipy 1.13.0. Every comparison matched; the three
   recomputed outputs are again equal in every value, and byte-identical, to the filed results. (A first
   run under numpy 1.26.4 and scipy 1.10.1 gave the small differences described under "Requirements".)
7. All 217 `as_filed/` files have the same SHA-256 as in the manifest made before the follow-up.
8. `scrubbed/`, `tools/`, `README.md` and `EXCLUDED.md` contain no GPU hardware identifier and no
   occurrence of the absolute project or storage path.
9. `tools/scrub.py`, run with the example rules on the 301 scrubbed files, reproduces each of them
   byte for byte (no further replacement).

Addition of `gate_rows_nocoord/` (21 Nov 2026, CPU only):

10. The command in `gate_rows_nocoord/README.txt` gives an output that is byte-identical to
    `gate_rows_nocoord/runtime_gate_analysis.txt` and to
    `scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt` (123 lines, SHA-256
    `754c5a1849119de4d0f58569ef7419be426960e142c19fe8d24edbe6d23744b0`). The seven digests in
    `gate_rows_nocoord/SHA256SUMS.txt` match. `tools/scrub.py --check gate_rows_nocoord` with an empty list
    of site rules (built-in rules only) reports no match.
11. Of the 538 files listed in the manifest made before this addition, 536 have the same SHA-256 as in
    that manifest. The other two are `README.md` and `EXCLUDED.md`, which were edited for this addition.
    `MANIFEST.sha256` was then regenerated; it lists 547 files.

Items 10 and 11 describe the folder as it was on 21 Nov 2026. Item 14 describes the present folder.

Addition of the figure script (21 Nov 2026):

12. `tools/make_fig_admission.py` was added and `README.md` and `EXCLUDED.md` were edited. No other file
    changed. `MANIFEST.sha256` was regenerated; it lists 548 files. The script was not rerun for this
    addition.

Addition of `tools/recompute_map.py` (22 Nov 2026, CPU only; record in `_test_out/MAP_RECOMPUTE_REPORT.txt`):

13. With the ground truth of Online Resource 10, completed by its rebuild script from the providers' files
    (2,827 images, 2,151 boxes), `tools/recompute_map.py --mode full --draws 12` gave `PASS`: the 414
    recomputed endpoint values and the 12 recomputed draws of each of the 46 runs are equal to the filed
    values. The filed `bootstrap_a04.py`, started unchanged in verify mode on two exported directories,
    passed, and its records are equal to the filed ones except for the two file digests and the numpy
    version. `README.md` and `EXCLUDED.md` were edited; no file under `as_filed/` or `scrubbed/` and no
    other tool changed. `MANIFEST.sha256` was regenerated; it lists 550 files.

Rebuild of `gate_rows_nocoord/` (22 Nov 2026, CPU only):

14. The folder was replaced. Per-row files are now given for the 3,698 rows of the sources D3 and D4 only.
    The other 5,636 rows are given as count cells, totals, sorted value lists and bin counts. The folder has
    14 files instead of 9. `python3 -I runtime_gate_analyze_nocoord.py`, run in the folder, gives an output
    that is byte-identical to `gate_rows_nocoord/runtime_gate_analysis.txt` and to
    `scrubbed/kais_v4/audit_out/runtime_gate/runtime_gate_analysis.txt` (123 lines, the SHA-256 of item 10),
    with Python 3.9.6 and with Python 3.9.23. The 13 digests in `gate_rows_nocoord/SHA256SUMS.txt` match.
    `tools/scrub.py --check gate_rows_nocoord` with an empty list of site rules reports no match.
    `README.md` and `EXCLUDED.md` were edited; no file under `as_filed/` or `scrubbed/` and no tool changed.
    `MANIFEST.sha256` was regenerated; it lists 555 files.
15. `gate_rows_nocoord/README.txt` was extended by one weighted test on the bins and rounded values of the
    admitted rows of D2, with its figures. No data file and no script of the folder changed. The digest of
    the README in `gate_rows_nocoord/SHA256SUMS.txt` and `MANIFEST.sha256` were regenerated; the manifest
    still lists 555 files. The script was not rerun for this addition.
16. One row of `EXCLUDED.md` was corrected: the 11 attempts that enter no analysis include one run that had
    been evaluated once before its configuration error was found. No other file changed except `README.md`
    and `MANIFEST.sha256`, which was regenerated; it still lists 555 files.

Not tested: the RFC 3161 tokens; anything that needs images, checkpoints or a GPU; all 2,000 draws of the
image-resampling analysis.
