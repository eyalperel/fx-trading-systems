"""Tests for tools/c1s3.py (C1S3, P-a): pairing, pooled statistic, max-statistic null and the pass rule on hand-built input."""
import os
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import c1s3 as S  # noqa: E402


class Pairing(unittest.TestCase):
    def test_permutation_deterministic_and_complete(self):
        a, e = list(range(100, 1100)), list(range(5000, 6000))
        p1, p2 = S.make_pairing(a, e), S.make_pairing(a, e)
        self.assertEqual(p1, p2)                                       # same seed, same pairing
        self.assertEqual([x[1] for x in p1], a)                        # AUD/USD offsets in file order
        self.assertEqual(sorted(x[2] for x in p1), e)                  # every EUR/JPY offset used exactly once
        self.assertNotEqual([x[2] for x in p1], e)                     # not the sorted (identity) pairing
        self.assertNotEqual(S.make_pairing(a, e, seed=1), p1)          # another seed gives another pairing

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "pairing.csv")
            open(p, "w").write("x")
            with self.assertRaises(FileExistsError):
                with open(p, "x"):
                    pass


class Stats(unittest.TestCase):
    def test_pooled_and_best_year(self):
        trs = [(1.0, 2010), (0.5, 2010), (-0.5, 2011), (0.2, 2012)]       # years: 2010 +1.5, 2011 -0.5, 2012 +0.2
        s = S.stats(trs)
        self.assertEqual(s["signals"], 4)
        self.assertAlmostEqual(s["mean"], 0.3)
        self.assertAlmostEqual(s["total"], 1.2)
        self.assertEqual(s["best_year"], 2010)
        self.assertAlmostEqual(s["total_excl"], -0.3)
        pooled = S.stats(trs + [(-1.0, 2010)])                             # pooling: one list, best year over both pairs
        self.assertEqual(pooled["best_year"], 2010)
        self.assertAlmostEqual(pooled["total_excl"], -0.3)


def table_and_pairing():
    """2 draws. AUD/USD offsets 10, 20; EUR/JPY 30, 40; pairing draw0 (10, 40), draw1 (20, 30)."""
    t = {}
    for cid in S.IDS:
        t[(cid, "AUDUSD", 10)] = (100, -5.0)
        t[(cid, "AUDUSD", 20)] = (100, 2.0)
        t[(cid, "EURJPY", 30)] = (50, 1.0)
        t[(cid, "EURJPY", 40)] = (50, -1.0)
    t[("RFX", "AUDUSD", 20)] = (100, 8.0)
    return t, [(0, 10, 40), (1, 20, 30)]


class PooledNull(unittest.TestCase):
    def test_signal_weighted_and_max(self):
        t, pairing = table_and_pairing()
        pm, mx = S.pooled_null(t, pairing)
        self.assertAlmostEqual(pm["FSH"][0], (-5.0 - 1.0) / 150)          # total / signals over both pairs
        self.assertAlmostEqual(pm["FSH"][1], (2.0 + 1.0) / 150)
        self.assertAlmostEqual(pm["RFX"][1], (8.0 + 1.0) / 150)
        self.assertAlmostEqual(mx[0], -6.0 / 150)
        self.assertAlmostEqual(mx[1], 9.0 / 150)                          # draw maximum picks RFX
        bad = [(0, 10, 30), (1, 20, 30)]                                  # planted: the pairing reuses EUR/JPY 30
        pm2, _ = S.pooled_null(t, bad)
        self.assertNotAlmostEqual(pm2["FSH"][0], pm["FSH"][0])


class PassRule(unittest.TestCase):
    def ok(self, mean=0.08, excl=3.0, aud=0.05, jpy=0.1, bar=0.05):
        return S.passes(dict(mean=mean, total_excl=excl), {"AUDUSD": dict(mean=aud), "EURJPY": dict(mean=jpy)}, bar)

    def test_pass(self):
        self.assertEqual(self.ok(), (True, []))

    def test_each_condition_fails_alone(self):
        self.assertEqual(self.ok(mean=0.04)[1], ["not above max-null 95th"])
        self.assertEqual(self.ok(excl=-0.1)[1], ["pooled total without best year <= 0"])
        self.assertEqual(self.ok(jpy=-0.01)[1], ["EURJPY mean <= 0"])     # planted: one pair negative, pooled still passes the bar
        self.assertEqual(self.ok(aud=0.0)[1], ["AUDUSD mean <= 0"])
        self.assertIn("pooled mean <= 0", self.ok(mean=-0.01, bar=-0.02)[1])   # a negative bar does not excuse a negative mean


class NullTable(unittest.TestCase):
    def test_duplicate_refused(self):
        r = dict(set="FSH", pair="AUDUSD", level="x2", offset="10", signals="5", total="1.0")
        self.assertEqual(len(S.null_table([r])), 1)
        with self.assertRaises(SystemExit):
            S.null_table([r, dict(r)])


if __name__ == "__main__":
    unittest.main()
