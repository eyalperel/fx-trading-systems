"""Checker for strategies/tests/XCHK_ATRMT4_vs_ATRS.c (ATR stage 2, S8 / AT-5).

  python analysis/harness/tools/check_xchk_atr.py [Data/XCHK_ATR_raw.csv]

Criterion (spec [cross_check], (c)): on rows with bar index >= 100, max relative |ATRMT4 - ATRS| <= 1e-9. Relative = |diff| / ATRS, recomputed here
from the two exported values (0 when ATRS = 0); the exported reldiff column is cross-read. Prints PASS / FAIL, the max row, and
the number of rows > 1e-12 relative (INFO). Also FAIL: header mismatch, bar index not contiguous from 0, fewer than 101 rows, a
NaN / infinite value, a close outside 0.8 .. 1.7 (wrong-asset guard, (b) h1_check CLOCK_LO / CLOCK_HI). Exit code 0 = PASS, 1 = FAIL.
"""
import csv
import math
import sys

HEADER = ["date", "bar", "lookback", "atrmt4", "atrs", "absdiff", "reldiff", "close"]
FROM_ROW = 100
LIMIT = 1e-9
INFO_LIMIT = 1e-12
CLOCK_LO, CLOCK_HI = 0.8, 1.7


def check(rows):
    """rows: list of dicts (date, bar int; the rest float). Returns (result, message, info)."""
    info = {}
    if len(rows) <= FROM_ROW:
        return "FAIL", "only %d rows; need more than %d" % (len(rows), FROM_ROW), info
    for k, r in enumerate(rows):
        if r["bar"] != k:
            return "FAIL", "row %d: bar index %r, expected %d" % (k, r["bar"], k), info
        for key in ("atrmt4", "atrs", "absdiff", "reldiff", "close"):
            if not math.isfinite(r[key]):
                return "FAIL", "row %d: %s is not finite (%r)" % (k, key, r[key]), info
        if not (CLOCK_LO <= r["close"] <= CLOCK_HI):
            return "FAIL", "row %d (date %d): close %r outside %s .. %s (wrong asset?)" % (k, r["date"], r["close"], CLOCK_LO, CLOCK_HI), info
    worst, worst_row, n_info = -1.0, None, 0
    for r in rows[FROM_ROW:]:
        rel = 0.0 if r["atrs"] == 0 else abs(r["atrmt4"] - r["atrs"]) / abs(r["atrs"])
        if rel > INFO_LIMIT:
            n_info += 1
        if rel > worst:
            worst, worst_row = rel, r
    info = {"max_rel": worst, "max_row": worst_row, "n_gt_1e-12": n_info, "n_rows_checked": len(rows) - FROM_ROW}
    if worst <= LIMIT:
        return "PASS", "max relative |diff| %.3e <= %.0e on %d rows (bar >= %d)" % (worst, LIMIT, len(rows) - FROM_ROW, FROM_ROW), info
    return "FAIL", "max relative |diff| %.3e > %.0e at bar %d (date %d)" % (worst, LIMIT, worst_row["bar"], worst_row["date"]), info


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.reader(fh)
        header = next(r)
        if header != HEADER:
            raise ValueError("unexpected header %r" % header)
        out = []
        for a in r:
            out.append(dict(date=int(a[0]), bar=int(a[1]), lookback=int(a[2]), atrmt4=float(a[3]), atrs=float(a[4]),
                            absdiff=float(a[5]), reldiff=float(a[6]), close=float(a[7])))
        return out


def main(argv):
    path = argv[1] if len(argv) > 1 else "C:/Zorro/Data/XCHK_ATR_raw.csv"
    try:
        rows = read(path)
    except (OSError, ValueError) as e:
        print("FAIL: cannot read %s: %s" % (path, e))
        return 1
    res, msg, info = check(rows)
    if info:
        w = info["max_row"]
        print("INFO max row: bar %d date %d atrmt4 %r atrs %r" % (w["bar"], w["date"], w["atrmt4"], w["atrs"]))
        print("INFO rows with relative |diff| > 1e-12: %d of %d" % (info["n_gt_1e-12"], info["n_rows_checked"]))
    print("%s: %s" % (res, msg))
    return 0 if res == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
