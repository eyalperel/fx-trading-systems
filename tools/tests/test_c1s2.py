"""Tests for tools/c1s2.py: per-pair cost arithmetic (by hand), the offsets rule, the pass rule."""
import os
import sys
import types
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import c1s2 as S  # noqa: E402


class Costs(unittest.TestCase):
    def test_eurjpy_long_earns_rollover(self):
        # long EUR/JPY, entry 160.00, exit 161.50, ATR 1.00, 4 days, x2: net = 1.50 - 0.046 + 4 x 0.2828 x 0.1 / (0.058102 / 0.01)
        hf = types.SimpleNamespace(dir=1, entry=160.0, exit_price=161.5, atr=1.0, entry_bar=0, exit_bar=1)
        roll = 4 * 0.2828 * 1000 / 10000 / (0.058102 / 0.01)
        self.assertAlmostEqual(S.half_r("EURJPY", hf, np.array([10, 14]), 2), (1.5 - 0.046 + roll) / 1.5, places=12)
        self.assertGreater(roll, 0)
        self.assertAlmostEqual(S.half_r("EURJPY", hf, np.array([10, 14]), 2, roll=False), (1.5 - 0.046) / 1.5, places=12)

    def test_audusd_short(self):
        hs = types.SimpleNamespace(dir=-1, entry=0.7000, exit_price=0.6950, atr=0.0050, entry_bar=0, exit_bar=1)
        roll = 2 * 0.0454 * 1000 / 10000 / (0.08561 / 0.0001)
        self.assertAlmostEqual(S.half_r("AUDUSD", hs, np.array([3, 5]), 1), (0.0050 - 0.00008 + roll) / 0.0075, places=12)
        self.assertAlmostEqual(S.half_r("AUDUSD", hs, np.array([3, 5]), 0, roll=False), 0.0050 / 0.0075, places=12)


class Offsets(unittest.TestCase):
    def test_rule(self):
        a = S.make_offsets(4000)
        self.assertEqual(len(a), 1000)
        self.assertEqual(len(set(a.tolist())), 1000)
        self.assertGreaterEqual(a.min(), 260)
        self.assertLessEqual(a.max(), 4000 - 260)
        self.assertTrue((S.make_offsets(4000) == a).all())           # reproducible from the seed
        # same rule as NULL1: L = 4970 reproduces NULL1_offsets.csv
        import csv
        p = os.path.join(S.ROOT, "analysis", "null_template", "NULL1_offsets.csv")
        ref = [int(r["offset"]) for r in csv.DictReader(open(p))]
        self.assertEqual(S.make_offsets(4970).tolist(), ref)


class Rule(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(S.passes(dict(mean=0.05, total_excl=1.0), 0.03), (True, []))
        self.assertFalse(S.passes(dict(mean=0.02, total_excl=1.0), 0.03)[0])
        self.assertFalse(S.passes(dict(mean=0.05, total_excl=-1.0), 0.03)[0])
        self.assertFalse(S.passes(dict(mean=-0.01, total_excl=1.0), -0.05)[0])


if __name__ == "__main__":
    unittest.main()
