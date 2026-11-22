"""Checker for strategies/tests/PROBE_SeriesExprLen.c (ATR stage 2, pre-run (vi)).

  python analysis/harness/tools/check_probe_series_len.py [Data/PROBE_SeriesExprLen.csv]

Expected (b, by construction; brief docs/harness/ATR_STAGE2_PROMPT.md section 2): columns bar,r14,r20; bar = 1..60 contiguous;
r14 = bar - 15 for bar > 15, r20 = 1000 + bar - 21 for bar > 21; earlier rows 0. A padding value other than 0 is INFO (a finding),
not a failure. Prints PASS / FAIL with the first mismatching row; exit code 0 = PASS, 1 = FAIL.
"""
import csv
import sys

TOL = 1e-9
NBARS = 60


def expected(bar):
    e14 = bar - 15 if bar > 15 else 0
    e20 = 1000 + bar - 21 if bar > 21 else 0
    return e14, e20


def check(rows):
    """rows: list of (bar, r14, r20) floats. Returns (result, message, infos)."""
    infos = []
    if len(rows) != NBARS:
        return "FAIL", "expected %d rows, got %d" % (NBARS, len(rows)), infos
    for k, (bar, r14, r20) in enumerate(rows):
        if bar != k + 1:
            return "FAIL", "row %d: bar %r, expected %d (not contiguous from 1)" % (k, bar, k + 1), infos
        e14, e20 = expected(k + 1)
        for name, got, want in (("r14", r14, e14), ("r20", r20, e20)):
            if not abs(got - want) <= TOL:                   # NaN fails too
                pad = (name == "r14" and bar <= 15) or (name == "r20" and bar <= 21)
                if pad:
                    infos.append("INFO padding row bar=%d %s = %r (expected 0)" % (bar, name, got))
                    continue
                return "FAIL", "first mismatch: row bar=%d %s = %r, expected %r" % (bar, name, got, want), infos
    return "PASS", "r14 = bar - 15 (bar > 15) and r20 = 1000 + bar - 21 (bar > 21) on all %d rows; separate slots per call" % NBARS, infos


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.reader(fh)
        header = next(r)
        if header != ["bar", "r14", "r20"]:
            raise ValueError("unexpected header %r" % header)
        return [(int(a), float(b), float(c)) for a, b, c in r]


def main(argv):
    path = argv[1] if len(argv) > 1 else "C:/Zorro/Data/PROBE_SeriesExprLen.csv"
    try:
        rows = read(path)
    except (OSError, ValueError) as e:
        print("FAIL: cannot read %s: %s" % (path, e))
        return 1
    res, msg, infos = check(rows)
    for i in infos:
        print(i)
    print("%s: %s" % (res, msg))
    return 0 if res == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
