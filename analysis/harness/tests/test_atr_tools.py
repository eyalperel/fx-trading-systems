"""Tests of analysis/harness/tools/check_probe_series_len.py and check_xchk_atr.py (ATR stage 2).
Every guard is seen to fire on a deliberately broken file (CLAUDE.md 4.4)."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, "..", "tools"))
sys.path.insert(0, TOOLS)
import check_probe_series_len as P  # noqa: E402
import check_xchk_atr as X  # noqa: E402


def probe_rows(swap=False, pad=0.0):
    rows = []
    for b in range(1, 61):
        e14, e20 = P.expected(b)
        if b <= 15:
            e14 = pad
        if swap:
            e14, e20 = e20, e14
        rows.append((b, float(e14), float(e20)))
    return rows


def xchk_rows(n=300):
    rows = []
    for k in range(n):
        z = 0.0 if k < 14 else 0.0075 + 0.0001 * (k % 7)
        rows.append(dict(date=20100101 + k, bar=k, lookback=1 if k < 100 else 0, atrmt4=z, atrs=z, absdiff=0.0, reldiff=0.0, close=1.3))
    return rows


class TestProbeChecker(unittest.TestCase):
    def test_good(self):
        res, msg, infos = P.check(probe_rows())
        self.assertEqual((res, infos), ("PASS", []), msg)

    def test_calls_swapped_fails_at_first_mismatching_row(self):
        res, msg, _ = P.check(probe_rows(swap=True))
        print("\n  [fire] probe checker, calls swapped: %s: %s" % (res, msg))
        self.assertEqual(res, "FAIL")
        self.assertIn("bar=16 r14", msg)

    def test_one_value_off_fails(self):
        rows = probe_rows()
        rows[40] = (rows[40][0], rows[40][1] + 1.0, rows[40][2])
        res, msg, _ = P.check(rows)
        print("\n  [fire] probe checker, one value off: %s: %s" % (res, msg))
        self.assertEqual(res, "FAIL")
        self.assertIn("bar=41", msg)

    def test_nonzero_padding_is_info_not_fail(self):
        res, msg, infos = P.check(probe_rows(pad=7.0))
        self.assertEqual(res, "PASS")
        self.assertEqual(len(infos), 15)
        print("\n  [fire] probe checker, padding 7 instead of 0: PASS with %d INFO lines (first: %s)" % (len(infos), infos[0]))

    def test_nan_and_short_and_noncontiguous_fail(self):
        rows = probe_rows()
        rows[30] = (rows[30][0], float("nan"), rows[30][2])
        self.assertEqual(P.check(rows)[0], "FAIL")
        self.assertEqual(P.check(probe_rows()[:59])[0], "FAIL")
        rows = probe_rows()
        rows[5] = (99, 0.0, 0.0)
        self.assertEqual(P.check(rows)[0], "FAIL")

    def test_cli_on_files(self):
        script = os.path.join(TOOLS, "check_probe_series_len.py")
        with tempfile.TemporaryDirectory() as d:
            for name, rows, rc in (("good.csv", probe_rows(), 0), ("bad.csv", probe_rows(swap=True), 1)):
                p = os.path.join(d, name)
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write("bar,r14,r20\n")
                    for b, a, c in rows:
                        fh.write("%d,%.15e,%.15e\n" % (b, a, c))
                r = subprocess.run([sys.executable, "-I", script, p], capture_output=True, text=True)
                self.assertEqual(r.returncode, rc, r.stdout + r.stderr)
                self.assertIn("PASS" if rc == 0 else "FAIL", r.stdout)
            r = subprocess.run([sys.executable, "-I", script, os.path.join(d, "none.csv")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)


class TestXchkChecker(unittest.TestCase):
    def test_pass_and_info_count(self):
        rows = xchk_rows()
        rows[200]["atrmt4"] *= 1 + 1e-11                 # > 1e-12 relative, < 1e-9: INFO only
        res, msg, info = X.check(rows)
        self.assertEqual(res, "PASS", msg)
        self.assertEqual(info["n_gt_1e-12"], 1)
        self.assertGreater(info["max_rel"], 1e-12)

    def test_fail_by_one_row(self):
        rows = xchk_rows()
        rows[250]["atrmt4"] *= 1 + 1e-8
        res, msg, info = X.check(rows)
        print("\n  [fire] xchk checker, one row 1e-8 off: %s: %s" % (res, msg))
        self.assertEqual(res, "FAIL")
        self.assertEqual(info["max_row"]["bar"], 250)

    def test_rows_before_100_are_excluded(self):
        rows = xchk_rows()
        rows[50]["atrmt4"] *= 2
        self.assertEqual(X.check(rows)[0], "PASS")

    def test_atrs_zero_row_has_relative_zero(self):
        rows = xchk_rows()
        rows[150]["atrs"] = 0.0
        rows[150]["atrmt4"] = 0.0
        res, msg, _ = X.check(rows)
        self.assertEqual(res, "PASS", msg)
        rows[151]["atrs"] = 0.0                          # ATRS 0 but ATRMT4 not 0: relative defined as 0 (brief), no division error
        res, msg, _ = X.check(rows)
        self.assertEqual(res, "PASS", msg)

    def test_guards_fire(self):
        cases = {}
        r = xchk_rows()
        r[10]["close"] = 150.0
        cases["wrong asset close 150"] = r
        r = xchk_rows()
        r[120]["atrmt4"] = float("nan")
        cases["NaN"] = r
        r = xchk_rows()
        r[30]["bar"] = 99
        cases["bar index not contiguous"] = r
        cases["fewer than 101 rows"] = xchk_rows(100)
        for label, rows in cases.items():
            res, msg, _ = X.check(rows)
            print("\n  [fire] xchk checker, %s: %s: %s" % (label, res, msg))
            self.assertEqual(res, "FAIL", label)

    def test_cli_on_files(self):
        script = os.path.join(TOOLS, "check_xchk_atr.py")
        with tempfile.TemporaryDirectory() as d:
            for name, bump, rc in (("good.csv", 1.0, 0), ("bad.csv", 1 + 1e-8, 1)):
                rows = xchk_rows()
                rows[250]["atrmt4"] *= bump
                p = os.path.join(d, name)
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(",".join(X.HEADER) + "\n")
                    for r in rows:
                        fh.write("%d,%d,%d,%.15e,%.15e,%.15e,%.15e,%.15e\n" % (r["date"], r["bar"], r["lookback"], r["atrmt4"], r["atrs"],
                                                                           r["absdiff"], r["reldiff"], r["close"]))
                out = subprocess.run([sys.executable, "-I", script, p], capture_output=True, text=True)
                self.assertEqual(out.returncode, rc, out.stdout + out.stderr)
                self.assertIn("PASS" if rc == 0 else "FAIL", out.stdout)


if __name__ == "__main__":
    unittest.main()
