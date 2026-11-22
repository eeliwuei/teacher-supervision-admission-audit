#!/usr/bin/env python3
"""scrub.py - write copies of text files with server paths, host names, user names, e-mail-like strings,
GPU hardware identifiers and process ids replaced.

Usage:
  scrub.py --src-root SRC --dst-root DST --list FILES.txt --rules RULES.json --table TABLE.tsv
  scrub.py --check DIR [DIR ...] --rules RULES.json      (report any remaining match; exit 1 if found)

FILES.txt  one path per line, relative to SRC; the copy is written to DST/<same relative path>.
RULES.json site-specific rules. Either a JSON list of [regular expression, replacement], or a JSON object
             {"replacements": [[regular expression, replacement], ...],
              "nvidia_smi_keep_index": {"<path as in FILES.txt>": <index of the card to keep>, ...}}
           The replacements are applied in order BEFORE the built-in rules. "-" reads the rules from standard
           input. The replacements that were used to build this bundle contain the real path prefix, host names
           and user names and are therefore NOT stored in the bundle; scrub_rules.example.json shows the form
           (its "nvidia_smi_keep_index" entry is the one that was used).
TABLE.tsv  one line per file: original_sha256, scrubbed_sha256, replacements, numeric check, relative path.
           A removed line counts as one replacement.

Built-in rules (always applied after the site rules):
  GPU process lists                  for each file named in "nvidia_smi_keep_index" (output of
                                     nvidia-smi --query-gpu=index,uuid,... followed by
                                     --query-compute-apps=gpu_uuid,pid,... and optional "<pid> <command>" lines):
                                     the per-process lines of every card except the kept one are removed, as are
                                     command lines of the removed processes; the process id of every kept
                                     per-process line and command line -> <PID>
  GPU hardware identifiers           GPU-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx -> GPU-<UUID>
  "pid": <integer> in JSON text      -> "pid": "<PID>"
  e-mail-like strings                -> <EMAIL>
  name@name (no dot)                 -> <USER>@<HOST>
  home directories                   -> <HOME>

Numeric check: for every .json file (and every line of a .jsonl file) the original and the scrubbed text are parsed
and the list of (path, value) of all numeric leaves must be identical, as must the key structure. The only
exception is a leaf whose key is "pid": it must be present on both sides and its value is not compared (the
replacement turns the integer into the string "<PID>"). For other files the line count must be unchanged and
every line without a replacement must be unchanged; where GPU process lines were removed, the comparison is made
against the original without those lines. Any failure makes the exit status 1.
"""
import argparse
import hashlib
import json
import os
import re
import sys

UUID = r"GPU-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
MASKED_KEYS = ("pid",)
BUILTIN = [
    (UUID, "GPU-<UUID>"),
    (r'("pid"\s*:\s*)\d+', r'\1"<PID>"'),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", "<EMAIL>"),
    (r"\b[A-Za-z0-9_-]+@[A-Za-z0-9_-]+(?=[:\s])", "<USER>@<HOST>"),
    (r"/(?:home|Users)/[A-Za-z0-9._-]+", "<HOME>"),
]
NUM = re.compile(r"(?<![A-Za-z0-9_.])[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?(?![A-Za-z0-9_])")
SMI_CARD = re.compile(r"^(\d+), (%s)," % UUID)
SMI_PROC = re.compile(r"^(%s), (\d+)," % UUID)
SMI_CMD = re.compile(r"^(\d+)(?= )")


def load_rules(arg):
    """Returns (compiled site + built-in replacements, {relative path: card index to keep})."""
    raw = sys.stdin.read() if arg == "-" else open(arg, encoding="utf-8").read()
    obj = json.loads(raw)
    keep = {}
    if isinstance(obj, dict):
        keep = {k: str(v) for k, v in obj.get("nvidia_smi_keep_index", {}).items()}
        obj = obj.get("replacements", [])
    site = [(a, b) for a, b in obj]
    return [(re.compile(a), b) for a, b in site + BUILTIN], keep


def smi_drop(text, keep_index):
    """Remove the per-process lines (and command lines) of every card except keep_index.
    Returns (text, number of removed lines, process ids of the kept card)."""
    card = {}
    for line in text.split("\n"):
        m = SMI_CARD.match(line)
        if m:
            card[m.group(2)] = m.group(1)
    kept, dropped, out, n = set(), set(), [], 0
    for line in text.split("\n"):
        m = SMI_PROC.match(line)
        if m:
            if card.get(m.group(1)) == keep_index:
                kept.add(m.group(2))
            else:
                dropped.add(m.group(2))
                n += 1
                continue
        m = SMI_CMD.match(line)
        if m and m.group(1) in dropped and m.group(1) not in kept:
            n += 1
            continue
        out.append(line)
    return "\n".join(out), n, kept


def smi_mask_pids(text, kept):
    """<PID> for the process id of the kept per-process lines and of their command lines."""
    out, n = [], 0
    for line in text.split("\n"):
        m = SMI_PROC.match(line)
        if m:
            line = line[:m.start(2)] + "<PID>" + line[m.end(2):]
            n += 1
        else:
            m = SMI_CMD.match(line)
            if m and m.group(1) in kept:
                line = "<PID>" + line[m.end(1):]
                n += 1
        out.append(line)
    return "\n".join(out), n


def apply_rules(text, rules):
    n = 0
    for rx, rep in rules:
        text, k = rx.subn(rep, text)
        n += k
    return text, n


def scrub_text(rel, text, rules, keep):
    """Returns (scrubbed text, replacements, reference text for the numeric check)."""
    ref, n = text, 0
    if rel in keep:
        ref, nd, kept = smi_drop(text, keep[rel])
        text, nm = smi_mask_pids(ref, kept)
        n = nd + nm
    out, k = apply_rules(text, rules)
    return out, n + k, ref


def sha(b):
    return hashlib.sha256(b).hexdigest()


def leaves(o, path=()):
    """(path, type, value) of every leaf; numbers keep their exact parsed value."""
    if isinstance(o, dict):
        for k in o:
            yield from leaves(o[k], path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, path + (i,))
    elif path and path[-1] in MASKED_KEYS and (isinstance(o, int) and not isinstance(o, bool) or o == "<PID>"):
        yield path, "masked", None
    elif isinstance(o, bool) or o is None:
        yield path, "const", o
    elif isinstance(o, (int, float)):
        yield path, "num", repr(o)
    else:
        yield path, "str", None


def numeric_check(rel, a, b):
    """a, b: original and scrubbed text. Returns (ok, kind, n_numeric)."""
    low = rel.lower()
    try:
        if low.endswith(".json"):
            la, lb = list(leaves(json.loads(a))), list(leaves(json.loads(b)))
            return la == lb, "json", sum(1 for x in la if x[1] == "num")
        if low.endswith(".jsonl"):
            la = [list(leaves(json.loads(x))) for x in a.splitlines() if x.strip()]
            lb = [list(leaves(json.loads(x))) for x in b.splitlines() if x.strip()]
            return la == lb, "jsonl", sum(1 for line in la for x in line if x[1] == "num")
    except ValueError:
        pass
    # text: the scrubbed text must carry the same number of lines, and every line without a replacement must be
    # unchanged
    al, bl = a.split("\n"), b.split("\n")
    if len(al) != len(bl):
        return False, "text", 0
    n = 0
    for x, y in zip(al, bl):
        if x != y and "<" not in y:
            return False, "text", 0
        if x == y:
            n += len(NUM.findall(x))
    return True, "text", n


def run_scrub(args):
    rules, keep = load_rules(args.rules)
    rows, bad = [], 0
    for rel in [x.strip() for x in open(args.list, encoding="utf-8") if x.strip()]:
        src, dst = os.path.join(args.src_root, rel), os.path.join(args.dst_root, rel)
        raw = open(src, "rb").read()
        text = raw.decode("utf-8", errors="surrogateescape")
        out, n, ref = scrub_text(rel, text, rules, keep)
        ok, kind, nnum = numeric_check(rel, ref, out)
        bad += (not ok)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        ob = out.encode("utf-8", errors="surrogateescape")
        with open(dst, "wb") as fh:
            fh.write(ob)
        st = os.stat(src)
        os.utime(dst, (st.st_atime, st.st_mtime))   # keep the original modification time
        rows.append((sha(raw), sha(ob), n, f"{kind}:{'ok' if ok else 'FAIL'}:{nnum}", rel))
    with open(args.table, "w", encoding="utf-8") as fh:
        fh.write("original_sha256\tscrubbed_sha256\treplacements\tnumeric_check(kind:result:numeric_values)\tpath\n")
        for r in rows:
            fh.write("\t".join(map(str, r)) + "\n")
    print(f"files {len(rows)}  changed {sum(1 for r in rows if r[0] != r[1])}  "
          f"replacements {sum(r[2] for r in rows)}  numeric check failures {bad}")
    return 1 if bad else 0


def run_check(args):
    rules, _ = load_rules(args.rules)
    hits = 0
    for top in args.check:
        for d, _, fs in os.walk(top):
            for f in sorted(fs):
                p = os.path.join(d, f)
                text = open(p, "rb").read().decode("utf-8", errors="surrogateescape")
                for rx, rep in rules:
                    for m in rx.finditer(text):
                        hits += 1
                        print(f"{p}\t{rep}\t{m.group(0)[:80]}")
    print(f"remaining matches: {hits}", file=sys.stderr)
    return 1 if hits else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src-root")
    ap.add_argument("--dst-root")
    ap.add_argument("--list")
    ap.add_argument("--table")
    ap.add_argument("--rules", required=True)
    ap.add_argument("--check", nargs="+")
    args = ap.parse_args()
    if args.check:
        sys.exit(run_check(args))
    if not (args.src_root and args.dst_root and args.list and args.table):
        ap.error("--src-root, --dst-root, --list and --table are required")
    sys.exit(run_scrub(args))


if __name__ == "__main__":
    main()
