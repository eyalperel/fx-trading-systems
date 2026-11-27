"""Tests for tools/diag1.py (DIAG1 G-a, J-a, Amendment 1): arms, cost levels, year blocks, jackknife, G0 guard."""
import math
import os
import sys
import unittest
from types import SimpleNamespace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import diag1 as G  # noqa: E402
import null1 as N  # noqa: E402


class Arms(unittest.TestCase):
    def test_configs(self):
        st = dict(c1=np.array([1, -1, 1, 0]), c2=np.array([-1, -1, -1, -1]), baseline=np.zeros(4), atr=np.ones(4))
        for arm in ("A2", "A3"):
            s, _ = G.arm_config(arm, st)
            self.assertTrue(np.array_equal(s["c2"], st["c1"]))             # C2 neutral: always agrees with C1
        for arm in ("A0", "A1"):
            s, _ = G.arm_config(arm, st)
            self.assertTrue(np.array_equal(s["c2"], st["c2"]))             # C2 untouched
        self.assertTrue(np.array_equal(st["c2"], [-1, -1, -1, -1]))        # the input dict is not modified
        self.assertTrue(G.arm_config("A0", st)[1].btf_on)
        self.assertFalse(G.arm_config("A1", st)[1].btf_on)
        self.assertTrue(G.arm_config("A2", st)[1].btf_on)
        self.assertFalse(G.arm_config("A3", st)[1].btf_on)
        self.assertEqual(G.arm_config("A4", st)[1].baseline_mode, "off")
        self.assertEqual(G.arm_config("A0", st)[1].baseline_mode, "on")


class Levels(unittest.TestCase):
    def test_x0_has_no_rollover_x0r_has(self):
        hf = SimpleNamespace(dir=1, exit_price=1.1050, entry=1.1000, atr=0.0100, entry_bar=0, exit_bar=1)
        day = np.array([0, 10])                                              # 10 days held
        x0 = G.half_r("EURUSD", hf, day, "x0")
        self.assertAlmostEqual(x0, 0.0050 / 0.0150)                          # dir x move / (1.5 ATR), nothing else
        x0r = G.half_r("EURUSD", hf, day, "x0r")
        self.assertAlmostEqual(x0r, N.half_r(hf, day, 0))                    # NULL1's x0 definition
        self.assertAlmostEqual(x0r - x0, N.roll_price(1, 10) / 0.0150)       # the difference is exactly the rollover
        self.assertLess(x0r, x0)                                             # EUR/USD long rollover is negative
        x0r_a = G.half_r("AUDUSD", hf, day, "x0r")
        self.assertNotAlmostEqual(x0r_a, x0r)                                # per-pair constants used


class Blocks(unittest.TestCase):
    def test_format_roundtrip(self):
        yr = {2011: [-1.25, 3], 2010: [2.5, 4]}
        self.assertEqual(G.parse_years(G.fmt_years(yr)), {2010: [2.5, 4], 2011: [-1.25, 3]})
        self.assertEqual(G.parse_years(""), {})

    def test_blocks_sum_offsets_and_pairs(self):
        rows = [dict(arm="A0", level="x0", pair="EURUSD", years="2010:1.0:2;2011:-1.0:2"),
                dict(arm="A0", level="x0", pair="AUDUSD", years="2010:0.5:1"),
                dict(arm="A0", level="x0r", pair="AUDUSD", years="2010:9.0:1"),     # other level: excluded
                dict(arm="A1", level="x0", pair="EURUSD", years="2010:9.0:1")]      # other arm: excluded
        self.assertEqual(G.blocks(rows, "A0", "x0"), {2010: [1.5, 3], 2011: [-1.0, 2]})
        self.assertEqual(G.blocks(rows, "A0", "x0", ("AUDUSD",)), {2010: [0.5, 1]})


class Jackknife(unittest.TestCase):
    def test_hand_calculated(self):
        # years 2010 (R 2, n 10), 2011 (-1, 10), 2012 (0, 10): mean 1/30;
        # leave-one-out means -1/20, 2/20, 1/20 -> mean 1/30; deviations -1/12, 1/15, 1/60;
        # sum of squares 0.0116667; x (J-1)/J = 2/3 -> 0.0077778; SE = 0.0881917
        b = {2010: [2.0, 10], 2011: [-1.0, 10], 2012: [0.0, 10]}
        est, se, z = G.jackknife(b)
        self.assertAlmostEqual(est, 1 / 30)
        self.assertAlmostEqual(se, math.sqrt(2 / 3 * ((1 / 12) ** 2 + (1 / 15) ** 2 + (1 / 60) ** 2)))
        self.assertAlmostEqual(se, 0.0881917, places=6)
        self.assertAlmostEqual(z, (1 / 30) / se)

    def test_contrast_removes_shared_year_noise(self):
        a = {2010: [2.0, 10], 2011: [-1.0, 10], 2012: [0.0, 10]}
        b = {y: [v[0] - 0.1 * v[1], v[1]] for y, v in a.items()}             # b = a shifted by -0.1 R per signal every year
        est, se, _ = G.jackknife(a, b)
        self.assertAlmostEqual(est, 0.1)
        self.assertAlmostEqual(se, 0.0)                                      # shared path noise cancels in the paired contrast


def g0_rows(arm_set, n=1000, mean=-0.028, total=-7.0, signals=250, halves=500, level="x0"):
    return [dict(set=arm_set, level=level, offset=str(k), signals=str(signals), halves=str(halves), mean=f"{mean:.6f}",
                 total=f"{total:.6f}") for k in range(1, n + 1)]


def diag_rows(arm, n=1000, mean=-0.028, total=-7.0, signals=250, halves=500, level="x0r"):
    return [dict(arm=arm, pair="EURUSD", level=level, offset=str(k), signals=str(signals), halves=str(halves),
                 mean=f"{mean:.9f}", total=f"{total:.9f}") for k in range(1, n + 1)]


class G0(unittest.TestCase):
    def setUp(self):
        self.ref = g0_rows("F2") + g0_rows("O2", mean=-0.010, total=-3.0) + g0_rows("F2", level="x2", mean=-0.05)

    def test_equal(self):
        got = G.g0_compare(diag_rows("A0") + diag_rows("A4", mean=-0.010, total=-3.0), self.ref)
        self.assertEqual(got, {"A0": (1000, 0), "A4": (1000, 0)})

    def test_rounding_inside_tolerance(self):
        got = G.g0_compare(diag_rows("A0", mean=-0.0280004) + diag_rows("A4", mean=-0.010, total=-3.0), self.ref)
        self.assertEqual(got["A0"], (1000, 0))

    def test_planted_changes_fail(self):
        got = G.g0_compare(diag_rows("A0", mean=-0.0250) + diag_rows("A4", mean=-0.010, total=-3.0), self.ref)
        self.assertEqual(got["A0"], (1000, 1000))                            # planted: a different arm result (e.g. btf off)
        got = G.g0_compare(diag_rows("A0", signals=251) + diag_rows("A4", mean=-0.010, total=-3.0), self.ref)
        self.assertEqual(got["A0"], (1000, 1000))                            # planted: one more signal
        got = G.g0_compare(diag_rows("A0", level="x0") + diag_rows("A4", mean=-0.010, total=-3.0), self.ref)
        self.assertEqual(got["A0"], (0, 0))                                  # true x0 rows are not G0's comparison (n != 1000 -> FAIL)

    def test_half_way_rounding_boundary(self):
        # Amendment 2: a true total at a half-way 7th digit, stored by NULL1 rounded the other way: |diff| = 5.0e-7 (+ float noise)
        ref = g0_rows("F2", total=-6.469672) + g0_rows("O2", mean=-0.010, total=-3.0)
        got = G.g0_compare(diag_rows("A0", total=-6.4696715) + diag_rows("A4", mean=-0.010, total=-3.0), ref)
        self.assertEqual(got["A0"], (1000, 0))
        got = G.g0_compare(diag_rows("A0", total=-6.4696705) + diag_rows("A4", mean=-0.010, total=-3.0), ref)
        self.assertEqual(got["A0"], (1000, 1000))                            # a whole 6th-decimal unit off still fails


if __name__ == "__main__":
    unittest.main()
