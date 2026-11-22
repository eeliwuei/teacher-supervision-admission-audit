# admission_audit.py

`admission_audit.py` counts and stratifies the supervision that a geometric IoU gate admits. It compares two placements of the same objects, row by row.

The file in this folder is a byte-identical copy of `evidence/tools/admission_audit.py` (SHA-256 `2fd1d2fca09833311637eb0c3c96c07138f97fc48e7a430c907d48a64cda56e3`). Check with:

    cmp admission_audit/admission_audit.py evidence/tools/admission_audit.py

Requirements: Python 3 and numpy. pandas is used for CSV reading if it is installed; otherwise the `csv` module is used. No network access.

## Input

Boxes are `x1, y1, x2, y2` in pixels of the same canvas. Row `i` of path A and row `i` of path B must be the same object.

- `--csv FILE`: one row per object, columns `ax1,ay1,ax2,ay2` (path A) and `bx1,by1,bx2,by2` (path B). Further columns can be used as strata with `--strata c1,c2`.
- `--npy-a A.npy --npy-b B.npy`: two arrays of shape (N, 4). Strata are not available in this form.

Other options: `--threshold T` (default 0.999), `--json FILE`, `--selftest`.

A row is admitted when IoU(A, B) >= threshold. A row with a non-finite coordinate is counted as rejected.

## Example 1: two small arrays

This makes two arrays of four boxes. The second box of path B is shifted down by half a pixel and the third box is shifted right by one pixel. The numbers are made up for the example. Run from the repository root.

    mkdir -p _out/example
    python3 -c '
    import numpy as np
    a = np.array([[100, 80, 300, 260], [400, 150, 520, 400], [50, 300, 90, 340], [600, 100, 900, 500]], dtype=float)
    b = a.copy()
    b[1] += [0, 0.5, 0, 0.5]   # second box: shifted down by half a pixel
    b[2] += [1, 0, 1, 0]       # third box: shifted right by one pixel
    np.save("_out/example/a.npy", a)
    np.save("_out/example/b.npy", b)
    '
    python3 admission_audit/admission_audit.py --npy-a _out/example/a.npy --npy-b _out/example/b.npy

Output (as obtained on 21 Nov 2026):

    Admission audit, gate: IoU >= 0.999
      rows 4   admitted 2   share 0.5000

    Share admitted at other thresholds
      IoU >= 0.5    admitted        4 of        4   share 1.0000
      IoU >= 0.9    admitted        4 of        4   share 1.0000
      IoU >= 0.99   admitted        3 of        4   share 0.7500
      IoU >= 0.999  admitted        2 of        4   share 0.5000

    Quantiles             q0        q1        q5       q25       q50       q75       q95       q99      q100
      IoU           0.951220  0.952563  0.957938  0.984811  0.998004  1.000000  1.000000  1.000000  1.000000
      |dx1| px        0.0000    0.0000    0.0000    0.0000    0.0000    0.2500    0.8500    0.9700    1.0000
      |dy1| px        0.0000    0.0000    0.0000    0.0000    0.0000    0.1250    0.4250    0.4850    0.5000
      |dx2| px        0.0000    0.0000    0.0000    0.0000    0.0000    0.2500    0.8500    0.9700    1.0000
      |dy2| px        0.0000    0.0000    0.0000    0.0000    0.0000    0.1250    0.4250    0.4850    0.5000
      max edge px     0.0000    0.0000    0.0000    0.0000    0.2500    0.6250    0.9250    0.9850    1.0000

The two shifted boxes fall below IoU 0.999. The box shifted by half a pixel still passes at 0.99.

## Example 2: a CSV with a stratum

`example_boxes.csv` holds 16 synthetic box pairs: four boxes on each of four image sizes, placed on a 960 x 960 canvas by the two illustration helpers of the script (`place_uniform_round` as path A, `place_ceil_peraxis` as path B) and written with four decimals. The column `image_shape` is the original image size. The file is an illustration, not data of the paper.

    python3 admission_audit/admission_audit.py --csv admission_audit/example_boxes.csv --strata image_shape

Output (as obtained on 21 Nov 2026):

    Admission audit, gate: IoU >= 0.999
      rows 16   admitted 12   share 0.7500

    Share admitted at other thresholds
      IoU >= 0.5    admitted       16 of       16   share 1.0000
      IoU >= 0.9    admitted       16 of       16   share 1.0000
      IoU >= 0.99   admitted       13 of       16   share 0.8125
      IoU >= 0.999  admitted       12 of       16   share 0.7500

    Quantiles             q0        q1        q5       q25       q50       q75       q95       q99      q100
      IoU           0.942224  0.948554  0.973875  0.998480  1.000000  1.000000  1.000000  1.000000  1.000000
      |dx1| px        0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000
      |dy1| px        0.0000    0.0000    0.0000    0.0000    0.0000    0.1831    0.9153    0.9260    0.9287
      |dx2| px        0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000
      |dy2| px        0.0000    0.0000    0.0000    0.0000    0.0000    0.1385    0.7146    0.7575    0.7682
      max edge px     0.0000    0.0000    0.0000    0.0000    0.0000    0.1831    0.9153    0.9260    0.9287

    By image_shape
      level        rows  admitted    share
      1280x720        4         4   1.0000
      1333x800        4         0   0.0000
      640x480         4         4   1.0000
      960x960         4         4   1.0000

In this synthetic example the two conventions agree for three image sizes and disagree for 1333 x 800, where the resized height differs by one pixel between rounding and ceiling.

## Self-test

    python3 admission_audit/admission_audit.py --selftest

It builds 1,200 synthetic box pairs on six image sizes, runs internal checks and ends with `selftest: PASS`.

## Use on your own pipeline

1. In the code path that produces the stored teacher boxes, write out each box in the coordinates of the training canvas.
2. In the data loader of the student, write out the box of the same object in the same canvas coordinates.
3. Align the two lists row by row and run the script with the threshold of your gate.

The helpers `place_uniform_round()` and `place_ceil_peraxis()` illustrate two resize conventions. They are not the code of any library. Audit your own pipeline with boxes taken from your own code paths.

## Tested with

Python 3.9.23 with numpy 2.0.2 (no pandas) and Python 3.11.12 with numpy 2.4.6 and pandas 2.2.3. The output of example 2 was the same in both.
