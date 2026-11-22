Run-time gate measurement - released files
==========================================

What the files are
------------------
During two instrumented passes over the training data (pass 1 with seed 42, pass 2 with
seed 1337) the 0.999 IoU gate of the training pipeline was observed for each of the 9,334
box-eligible teacher-evidence rows. The original per-row files hold absolute image paths
and box coordinates of every training row and are not released.

The rows fall in two groups.
  * 3,698 rows of the sources D3 and D4. Their annotations are public. They are given
    here row by row, without coordinates, paths or file names.
  * 5,636 rows of D2 (5,470) and of the pooled source "other" (166, D5 to D7). The box
    annotations of D2 and D7 may not be redistributed, and D7 is not labelled separately.
    These rows are called restricted below. No per-row record of a restricted row is in
    this folder. They are given as count cells, as totals, and as sorted value lists or
    bin counts without row identifier.

Together the files reproduce the published summary (runtime_gate_analysis.txt: 6,434 of
9,334 rows admitted; shares by class, source, image shape and object size; pass 1 versus
pass 2; static audit versus run time).

padding_row_audit.nocoord.public.csv                  static audit, rows of D3 and D4, 3,698 rows, 16 columns
runtime_gate_rows_pass1_seed42.nocoord.public.csv     run-time rows of pass 1, D3 and D4, 3,698 rows, 24 columns
runtime_gate_rows_pass2_seed1337.nocoord.public.csv   the same for pass 2
restricted_cells.csv                                  restricted rows as count cells, 71 cells, 5,636 rows
restricted_class_term_counts.csv                      restricted rows by class, admitted and class term, 6 counts
restricted_aggregates.json                            totals for the restricted rows, supplied by the authors
restricted_gate_iou.sorted.csv                        gate IoU of the restricted rows, sorted, no row id
restricted_abs_gate_iou_minus_ul_iou_int.sorted.csv   one difference per restricted row, sorted, no row id
restricted_edge_offset_rejected.sorted.csv            edge offset of the restricted rejected rows, sorted, no row id
restricted_edge_offset_admitted_bins.csv              edge offset of the restricted admitted rows, counts per bin
runtime_gate_analyze_nocoord.py                       recomputes the summary (Python 3, standard library only)
runtime_gate_analysis.txt                             the published summary (unchanged)
SHA256SUMS.txt                                        SHA-256 of the files in this folder

A third original file (a 31-row smoke test) is not used by the analysis and has no
counterpart here.

Recompute
---------
    python3 -I runtime_gate_analyze_nocoord.py > out.txt
    cmp out.txt runtime_gate_analysis.txt

The script reads the files from its own folder (or from a folder given as argument). The
output is byte-identical to runtime_gate_analysis.txt (123 lines, SHA-256
754c5a1849119de4d0f58569ef7419be426960e142c19fe8d24edbe6d23744b0).

    python3 -I runtime_gate_analyze_nocoord.py --status

prints the same lines with a tag in front of each line. The tag says where the part of
the line that concerns the restricted rows comes from (next section).

Which lines are recomputed and which are supplied by the authors
----------------------------------------------------------------
For the rows of D3 and D4 every line is computed from the per-row files. The only
exception is the last line, which uses the released flag same_batch_in_both_passes.
For the restricted rows the line numbers below refer to runtime_gate_analysis.txt.

[C] 62 lines: 1, 5-10, 14-32, 38-42, 62-67, 71-89, 95-99, 118.
    Counts over the per-row files plus the count cells, using recorded fields: class,
    admitted, class term, and the static strata and flags. These are the admitted count,
    the shares by class, static padding parity, source, size and image shape, the
    comparison with the static flags, and "admitted differs". The static fields of the
    cells can be checked against Online Resource 12 (see "How to check the cells").
    For the restricted rows the admitted counts are counts supplied by the authors. A
    reader can check that they equal the static flag ul_admitted_int of Online Resource
    12 in every cell, and nothing more.
[F] 34 lines: 11-13, 33-37, 44-50, 68-70, 90-94, 101-107, 119-121, 123.
    As [C], but for the restricted rows the field is a yes/no flag that the authors
    evaluated on the unreleased per-row values before counting. These are the lines on
    the run-time padding parity, the seven lines of the geometry checks that compare
    sizes and paddings or count rows without a label of their class, and the between-pass
    lines "gate_iou differs", "batch box differs", "pad/resized differs" and "same batch
    index". The reader cannot recompute these flags for the restricted rows.
[T] 6 lines: 3, 4, 60, 61, 117, 122.
    The restricted part is a total supplied by the authors in restricted_aggregates.json:
    5,636 distinct rows and 5,119 images in each pass, no row of the static file missing
    from a pass and no row of a pass missing from the static file (lines 4 and 61), and
    5,119 images whose pixel sum differs between the passes. The reader cannot recompute
    these totals.
[L] 16 lines: 51-58, 108-115.
    The restricted part comes from sorted value lists or bin counts without row id.
    Some of these values are rounded (see the column descriptions). The header of the
    script says why the printed digits do not change, and the script stops if the bin
    counts do not fix the line that uses them.
[H] 5 lines: 2, 43, 59, 100, 116. Headers without data.

Columns of padding_row_audit.nocoord.public.csv (rows of D3 and D4)
-------------------------------------------------------------------
row_id             integer 1..3698 assigned in a private random order, the same row in the
                   three per-row files; the files are sorted by it. It is unrelated to
                   the row order of any other released file and to the row_id of earlier
                   versions of this folder
source             D3 or D4
size_bin           object size class in the 960 x 960 letterboxed image: small<32^2, medium, large>=96^2
aspect_bin         image shape class: square, tall, wide
pad_parity         even / odd, parity of the total padding when the image is resized with round()
ul_pad_parity      the same when the image is resized with ceil()
new_w, new_h       resized image size with round()
ul_new_w, ul_new_h resized image size with ceil()
iou_int            static IoU under integer padding (1.0 for every row by construction)
admitted_int       1 if iou_int >= 0.999 (1 for every row by construction; this column does not
                   record admission in training)
admitted_float     1 if the static IoU under float (half-pixel) padding >= 0.999
ul_admitted_int, ul_admitted_float   the same flags against the ceil-resize reference
ul_iou_int         static IoU of the integer mapping against the ceil-resize reference
                   (the same value is in Online Resource 12 for these rows)

Columns of runtime_gate_rows_*.nocoord.public.csv (rows of D3 and D4)
---------------------------------------------------------------------
row_id             as above
pass_tag, seed     pass identifier and its seed
image_idx          integer 1..3509 assigned in a private random order; rows of the same image share it
class              gun, knife, stick
ori_h, ori_w       original image size reported by the data loader
bank_h, bank_w     image size recorded in the evidence bank
resized_h, resized_w   size of the training image (960, 960)
lb_in_h, lb_in_w   image size at the input of the letterbox step
pad_left, pad_top, pad_total_x, pad_total_y   padding applied by the pipeline, pixels
admitted           1 if the row passed the 0.999 gate at run time
has_cls            1 if the admitted row also carried the class term
gate_iou           the IoU the gate compares with 0.999, as recorded (float32 printed in full)
max_abs_edge_offset_px   largest absolute offset, in pixels, between the four box edges
                   mapped by the adapter and by the batch (4 decimals, as recorded)
batch_box_digest   keyed digest (HMAC-SHA-256, first 16 hex digits, key not released) of the four
                   label-box values of the row in the batch; used only to test whether the box was
                   the same in both passes
img_sum            sum of the pixel values of the (augmented) image tensor in that pass
same_batch_in_both_passes   1 if the row was in the batch with the same index in both passes.
                   The batch index itself and the order in which the data loader delivered
                   the rows are not released.

Columns of restricted_cells.csv (rows of D2 and other)
------------------------------------------------------
One line per combination of values that occurs; n is the number of restricted rows with
that combination. The sum of n is 5,636.
class, source, size_bin, aspect_bin, pad_parity, ul_pad_parity, admitted_int,
admitted_float, ul_admitted_int, ul_admitted_float
                   as in the static file above
p1_..., p2_...     the same field for pass 1 and for pass 2:
  admitted         1 if the row passed the gate at run time
  rt_pad_parity    even / odd, parity of pad_total_x and pad_total_y observed in the pipeline
  ori_eq_bank      1 if (ori_h, ori_w) equals (bank_h, bank_w)
  resized_960      1 if (resized_h, resized_w) equals (960, 960)
  lbin_eq_ceil     1 if (lb_in_w, lb_in_h) equals (ul_new_w, ul_new_h)
  lbin_eq_round    1 if (lb_in_w, lb_in_h) equals (new_w, new_h)
  pad_rule_ok      1 if (pad_left, pad_top) equals round(total/2 - 0.1) on both axes
  pad_eq_adapter   1 if (pad_left, pad_top) equals the integer padding of the adapter
  has_gate_iou     1 if a gate IoU was recorded (a label of the same class was in the batch)
x_same_gate_iou    1 if the recorded gate_iou string is the same in both passes
x_same_box         1 if the four label-box values of the batch are the same in both passes
x_same_pad         1 if pad_left, pad_top, lb_in_h, lb_in_w, resized_h, resized_w are the same in both passes
x_same_batch       1 if the row was in the batch with the same index in both passes
n                  number of rows
The p1_, p2_ and x_ flags other than admitted were evaluated by the authors on the
unreleased per-row values, with the same expressions that the script applies to the rows
of D3 and D4.

restricted_class_term_counts.csv
--------------------------------
class, p1_admitted, p1_has_cls, p2_admitted, p2_has_cls, n. The class term is kept apart
from the cells so that no cell holds a field that Online Resource 12 does not already
determine. There is no restricted row of class stick.

restricted_aggregates.json
--------------------------
restricted_rows, restricted_unique_row_keys          5,636
restricted_images_pass1, restricted_images_pass2, restricted_images_in_both_passes   5,119
restricted_images_pixel_sum_differs_between_passes   5,119
images_with_rows_in_both_groups                      0 (no image has rows in both groups)
restricted_static_rows_not_in_pass1, restricted_static_rows_not_in_pass2   0
restricted_pass1_rows_not_in_static, restricted_pass2_rows_not_in_static   0
These totals are supplied by the authors.

Value lists and bin counts of the restricted rows
-------------------------------------------------
All four files have a column "pass" (1 or 2). Three are sorted by value inside each pass.
restricted_gate_iou.sorted.csv is sorted by value inside each pass and admitted group;
the admitted group comes first. The files carry no row id, and their order is unrelated
to any other file. The values of pass 2 are the same as those of pass 1.
restricted_gate_iou.sorted.csv              pass, admitted, value. For admitted = 0 (1,791 rows per pass)
                                            the value is gate_iou as recorded. For admitted = 1 (3,845 rows
                                            per pass) the value is gate_iou rounded upward to 4 decimals;
                                            there are 10 distinct values, each shared by at least 56 rows.
restricted_abs_gate_iou_minus_ul_iou_int.sorted.csv
                                            pass, value. |gate_iou - static ul_iou_int| of each restricted
                                            row, rounded to 8 decimals.
restricted_edge_offset_rejected.sorted.csv  pass, value. Largest absolute edge offset in pixels of each
                                            restricted rejected row, rounded to 3 decimals.
restricted_edge_offset_admitted_bins.csv    pass, lower_exclusive, upper_inclusive, n. Number of restricted
                                            admitted rows whose largest absolute edge offset lies in the
                                            bin. The first bin holds the rows with offset 0. The last bin
                                            ends at 0.69, below the largest value among the admitted rows of
                                            D3 and D4 (0.6934). No single value is released for these rows.

How the files were derived
--------------------------
row_id and image_idx of the rows of D3 and D4 are new random permutations. The tables to
the original row key and to the image path are not released. The per-row files are
written in ascending row_id.
Removed from the rows of D3 and D4, compared with the original files: image path
(im_file), original row key, batch index (batch_i), the eight box coordinate columns, the
four per-edge offsets (their largest absolute value is kept), class_id, n_labels_img,
n_same_cls_labels, n_candidates_same_cls, best_iou_any_label; from the static file:
image_id, query_id, matched_gt_id, bank_line, class, image size, ground-truth
coordinates, scale, box width, height and area, padded_axis, padding amounts, iou_float,
ul_total_pad_px, ul_iou_float.
Removed for the restricted rows: every per-row record. In particular no batch index,
image index, image size, padding, resized size, per-row gate_iou, box digest or pixel sum
of a restricted row is released.

How to check the cells against Online Resource 12
-------------------------------------------------
Online Resource 12 lists every restricted row with class, source, size_bin, aspect_bin,
pad_parity, ul_pad_parity, the four static admission flags, and the resized sizes under
both rules. Counting those rows by the ten static fields gives the same counts as
restricted_cells.csv summed over the run-time fields. The run-time fields of every cell
also agree with what the static columns predict: admitted equals ul_admitted_int,
rt_pad_parity equals ul_pad_parity, lbin_eq_round is 1 where the two resized sizes are
equal, and pad_eq_adapter is 1 where the two integer paddings are equal. With these four
rules and the value 1 for the remaining flags, the whole cell table can be rebuilt from
Online Resource 12 (tested: identical, 71 cells).

Limits of the anonymisation
---------------------------
Rows of D3 and D4. These rows are not anonymous and need not be. Their annotations are
public, and Online Resource 12 gives their coordinates. Rows of the per-row files can be
matched to their rows in Online Resource 12, for example through source, ul_iou_int,
new_w and new_h (1,382 of the 3,698 rows by these four values alone).

Restricted rows. The folder holds no record of a single restricted row. What it holds
about them, and what we measured:
  * Count cells. 6 of the 71 cells have n = 1 (4 rows of D2, 2 of other), and 23 cells
    with 54 rows have n below 5. A cell with n = 1 can be matched to one row of Online
    Resource 12. The match adds nothing to that row, because every field of the cell
    follows from the columns of Online Resource 12 (previous section).
  * Class term. Six counts by class. They say that 23 admitted gun rows and 13 admitted
    knife rows of the restricted sources carried no class term, not which rows. In the
    rows of D3 and D4, 132 of the 133 admitted rows without class term have a query_id
    other than 0. If the same holds for the restricted rows, the 36 rows are among the
    393 admitted restricted rows of Online Resource 12 with such a query_id. No single
    row is identified.
  * Gate IoU list, rejected rows, as recorded. We tested whether a value can be assigned
    to a row of Online Resource 12, using the image size of each row, whole-pixel box
    edges, and a tolerance fitted on the rows of D3 and D4 (2.74e-6). Each value is
    compatible with at least 492 restricted rows (median 1,627). Pairing each value with
    every value of the difference list did not narrow this (at least 516 rows).
  * Gate IoU list, admitted rows. Ten values, each shared by at least 56 rows.
  * Edge offsets, rejected rows, 3 decimals. Each distinct value is compatible with at
    least 382 restricted rows (median 855).
  * Edge offsets, admitted rows. Eight bin counts; the smallest count is 10. The image
    geometry allows an offset in the last bin for fewer than 40 of the restricted
    admitted rows (27 and 38 in two tests), and 10 of them lie in that bin. No value
    follows for a row.
  * Bins and rounded values of the admitted rows, weighted. A further test weighted each
    bin and each rounded gate IoU value by the number of whole-pixel edge pairs of the
    row that fall in it. It scaled the weights to the released counts. The first two
    bins were merged. One of the other six bins got a weight above 0.5 for 545 admitted
    rows of D2 that geometry and flags do not fix alone; for 402 of them it was the true
    bin. In the last bin these were 9 rows (7 correct), 2 of them above 0.8 (both
    correct). A rounded value below 1.0000 got a weight above 0.5 for 97 such rows (56
    correct). Most of the weight comes from the image geometry and the flags of the row
    in Online Resource 12. These alone fix one of the six bins for 10 rows and a value
    below 1.0000 for 5 rows. An assigned bin or value is a band. It left at least 239
    whole-pixel edge pairs for every row with a weight above 0.5.
  * All lists together. For each rejected row of D2 we counted the pairs of whole-pixel
    box edges on the padded axis that agree with the gate IoU list, the edge-offset list,
    the size class and, where it applies, the extent list of Online Resource 12. At least
    133 pairs remain for every row (median 29,360). The rejected flag alone leaves a
    median of 68,265 pairs. A test that weighted the gate IoU values by size class gave
    no row a value with a weight above 0.25.
  No test gave a box extent, a box position or a ratio of box edges for a row. The
  weighted test above assigned a bin or a rounded value, not a recorded value.
The lists do show the distribution of these quantities over the restricted rows.
Earlier versions of this folder kept the order in which the data loader delivered the
rows, a batch index and an image index for every row. That order can be replayed from the
list of training file names. The present files hold none of the three.
Not tested: a replay of the single-precision arithmetic of the pipeline to the last bit.
The tests used a model that agrees with the recorded gate IoU to about 1e-7 (median).
The rejected gate IoU values are released as recorded. Rows of the pooled source "other"
were treated as compatible with every value. The tests were run on pass 1.

SHA-256 of the original (unreleased) files, as recorded in their SHA256SUMS
---------------------------------------------------------------------------
cda26aba7a1f4521a7af21701c84b0884d1ca4f654b41fcbb27ee6dbe4649fc6  runtime_gate_rows_pass1_seed42.csv
e6292126f69b3582a7a0962b63f2be301879ef14f824b1e5af1b98324321bdb2  runtime_gate_rows_pass2_seed1337.csv
276e7f3f8286f21dbde153dc27164f42a31f85085e1a611919dfbff804f8bc60  runtime_gate_rows_smoke.csv
eb350670067d2e15a5ae339b84cc1fc8a4a786086d068c17f0c391ef5f64496e  runtime_gate_analyze.py
754c5a1849119de4d0f58569ef7419be426960e142c19fe8d24edbe6d23744b0  runtime_gate_analysis.txt
1f7a1b2253cd5749f25690c963d815116611aa9fe720ac227ac2e9dc13214f33  padding_row_audit.csv (recorded in padding_row_audit.sha256)
