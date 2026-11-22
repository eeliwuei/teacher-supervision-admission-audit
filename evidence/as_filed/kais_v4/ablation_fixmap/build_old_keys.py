"""Build old_gate_admitted_keys.json: (image_id, query_id) of rows the stock gate admitted in the run-time audit."""
import csv, json, sys
bank, rows_csv, out = sys.argv[1:4]
lines = open(bank, encoding="utf-8").read().split("\n")
keep, n = [], 0
for r in csv.DictReader(open(rows_csv)):
    n += 1
    parts = r["row_id"].split(":")
    ln, q, g = int(parts[0][1:]), int(parts[-2][1:]), int(parts[-1][1:])
    cands = [json.loads(lines[i]) for i in (ln, ln - 1) if 0 <= i < len(lines) and lines[i].strip()]
    rows = [c for c in cands if int(c.get("query_id")) == q and int(c.get("matched_gt_id", -9)) == g
            and c.get("evidence_type") == "E1_matched_refinement" and ":".join(parts[1:-2]) == str(c.get("image_id"))]
    assert len(rows) == 1, (r["row_id"], [(c.get("image_id"), c.get("query_id"), c.get("matched_gt_id")) for c in cands])
    if r["admitted"] in ("1", "True", "true"):
        keep.append([str(rows[0]["image_id"]), int(rows[0]["query_id"])])
assert len(set(map(tuple, keep))) == len(keep)
json.dump(sorted(keep), open(out, "w"))
print("rows", n, "kept", len(keep))
