"""Tests for tools/c1s1.py (C1S1): readings, W0 comparison (planted wrong reading), max-statistic and the R-b pass rule."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import c1s1 as S  # noqa: E402


def ind(n=40, seed=3):
    rng = np.random.default_rng(seed)
    i1 = {k: rng.normal(size=n) for k in ("mama", "fama", "fish", "trig", "reflex")}
    i2 = {k: rng.normal(size=n) for k in ("mesa", "sma", "roof")}
    i2["lrsi"] = rng.uniform(size=n)
    i2["sma"][:9] = np.nan
    return i1, i2


class Readings(unittest.TestCase):
    def test_known_values(self):
        i1 = dict(mama=[1.0, 1.0], fama=[0.5, 2.0], fish=[0.2, 0.1], trig=[0.1, 0.1], reflex=[-1.0, 0.0])
        i2 = dict(mesa=[0.3, 0.6], sma=[np.nan, 0.5], roof=[0.01, -0.02], lrsi=[0.5, 0.9])
        r = S.readings(i1, i2)
        self.assertEqual(list(r["MAF"]), [1, -1])
        self.assertEqual(list(r["FSH"]), [1, 0])          # Fish = Fish[1]: on the line
        self.assertEqual(list(r["RFX"]), [-1, 0])
        self.assertEqual(list(r["MSS"]), [0, 1])          # no SMA yet -> 0
        self.assertEqual(list(r["ROF"]), [1, -1])
        self.assertEqual(list(r["LRS"]), [0, 1])

    def test_w0_identical_and_planted_sign_flip(self):
        i1, i2 = ind()
        st = S.readings(i1, i2)
        res = S.w0_compare(st, st, S.margins(i1, i2), first=10)
        self.assertTrue(all(v == (0, 0) for v in res.values()))
        bad = dict(st)
        bad["FSH"] = -st["FSH"]                           # planted: FSH sign flipped
        res = S.w0_compare(st, bad, S.margins(i1, i2), first=10)
        self.assertGreater(res["FSH"][0], 0)
        self.assertTrue(all(res[k] == (0, 0) for k in S.IDS if k != "FSH"))

    def test_near_threshold_counted_not_failed(self):
        i1, i2 = ind()
        i1["reflex"][20] = 1e-12
        st = S.readings(i1, i2)
        z = dict(st)
        z["RFX"] = st["RFX"].copy()
        z["RFX"][20] = -z["RFX"][20]
        self.assertEqual(S.w0_compare(st, z, S.margins(i1, i2), first=10)["RFX"], (0, 1))


class Rule(unittest.TestCase):
    def test_max_stat_and_pass(self):
        null1 = [dict(set="O1", level="x2", offset="1", mean="-0.02"), dict(set="O2", level="x2", offset="1", mean="0.01"),
                 dict(set="O1", level="x0", offset="1", mean="9")]
        c1 = [dict(set=k, level="x2", offset="1", mean=v) for k, v in
              (("MAF", "0.03"), ("RFX", "-0.05"), ("ROF", "0.00"), ("LRS", "0.02"))]
        t = S.null_table(null1, c1)
        self.assertEqual(list(S.max_stat(t)), [0.03])
        self.assertEqual(S.passes(dict(mean=0.04, total_excl=1.0), 0.03), (True, []))
        self.assertFalse(S.passes(dict(mean=0.02, total_excl=1.0), 0.03)[0])          # below the bar
        self.assertFalse(S.passes(dict(mean=0.04, total_excl=-0.1), 0.03)[0])         # best year carries it
        self.assertFalse(S.passes(dict(mean=-0.01, total_excl=1.0), -0.02)[0])        # above a negative bar, but losing
        with self.assertRaises(SystemExit):
            S.max_stat({1: {"FSH": 0.0}})                                              # an offset lacks a candidate


if __name__ == "__main__":
    unittest.main()
