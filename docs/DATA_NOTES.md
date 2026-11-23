# Data notes

This page says what was withheld from the repository and why. The full list, with the reason and with what a reader loses for each item, is [evidence/EXCLUDED.md](../evidence/EXCLUDED.md). The limits of what can be recomputed are in [evidence/README.md](../evidence/README.md), section "Cannot be recomputed from the bundle".

## What the repository contains

- Filed documents and scripts of the two pre-specified experiments, as byte-for-byte copies (`evidence/as_filed/`).
- Model outputs on the validation images (`predictions.json`, 46 files). Each row is one detection with the file name of its image. No annotation is in these files.
- Endpoint files, run summaries and logs with server paths, host names, user names, e-mail-like strings, GPU hardware identifiers and process ids replaced (`evidence/scrubbed/`). `evidence/scrubbed/SCRUB_TABLE.tsv` maps the digest of each original to the digest of its copy.
- Files of the run-time gate measurement without coordinates (`evidence/gate_rows_nocoord/`): per-row files for the rows of the sources D3 and D4, and count cells, totals and sorted value lists for the other rows.

## What was withheld

Annotation-derived coordinates and image paths:

- The original per-row files of the run-time gate measurement. They hold the absolute image path and the box coordinates of every training row, including rows from sources whose annotations are withheld.
- The row-level static padding audit with ground-truth box coordinates.
- The ground-truth files of the validation images. Online Resource 10 of the paper holds the validation ground truth without 87 boxes of two restricted sources, and a script that rebuilds them (docs/REPRODUCE.md, section 3a).
- The per-row files, path lists and mask files of the pre-launch verification of the mechanism code and of the fix-map audit.
- The ground truth and predictions of the internal evaluation split.

Training-side code:

- The patches of the training and distillation code that define the conditions of the mechanism experiment. The training code is not released.

Row keys of restricted subsets:

- The mask files of the masked runs and the list of the 6,434 row keys of the old-gate condition.

Left out for size or because they add nothing to the recomputation:

- Training logs, checkpoints, evaluation logs, argument files, the evaluation directories of the sensitivity analyses, and the 11 attempts that entered no analysis. Ten of them were never evaluated; the wrongly configured CBox-M run at seed 20260703 had been evaluated once before its configuration error was found, and its values are not used.

No image is included anywhere in the repository.

## The files of the gate measurement

`evidence/gate_rows_nocoord/README.txt` describes every file and column, how the files were derived and what was removed. In short:

- The 9,334 rows fall in two groups. 3,698 rows come from the sources D3 and D4, whose annotations are public. 5,636 rows come from D2 and from the pooled source `other`; box annotations of these sources may not all be redistributed.
- For the rows of D3 and D4 there are three per-row files. They contain no coordinate, no path and no file name. Row numbers and image numbers are random, and the tables that map them to the original keys are not released. The batch index and the order in which the data loader delivered the rows are not released.
- In these files the box of a row in the batch is replaced by a keyed digest. The key is not released.
- The rows of D3 and D4 are not anonymous. Their annotations are public, and rows can be matched to the row-level static audit file of Online Resource 12 by value (1,382 of the 3,698 rows by four columns).
- For the other 5,636 rows the folder holds no per-row record. It holds 71 count cells, six counts for the class term, totals, three sorted value lists without row identifier, and one file of bin counts. The README of the folder reports the tests that were made: no test assigned a list value to a single row.
- An earlier version of the folder held per-row files of all 9,334 rows in the order of the data loader. In a test that order was replayed from the list of training file names in Online Resource 9, and all rows were linked to their images. The present folder replaces that version.

## Known residue

Some as-filed files could not be edited without breaking filed digests. They still contain the absolute project path (15 scripts), internal project tokens in file and folder names, and contact addresses of the timestamp authorities inside the timestamp replies. `evidence/README.md` lists these in the sections "Known residue in as-filed files" and "Known residue in the contents of scrubbed files".

## Sources

The summary of the run-time gate names the data sources only by the labels `D2`, `D3`, `D4` and `other` (`other` pools D5 to D7, as `evidence/gate_rows_nocoord/README.txt` states). This repository does not state which data set each label stands for. The prediction files do carry the file names of validation images, and these names begin with source prefixes; `evidence/README.md`, section "Known residue in as-filed files", lists them.
