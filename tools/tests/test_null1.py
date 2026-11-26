"""Tests for tools/null1.py (NULL1): V2 injection known answer, shift, costs, signal stats."""
import os
import sys
import types
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import null1 as N  # noqa: E402


def synthetic():
    """6 bars, flat price 1.0; bar k ends at OLE k + 1; its 4 records at k + 0.25, 0.5, 0.75, 1.0 (time fraction f)."""
    t = np.array([k + f for k in range(6) for f in (0.25, 0.5, 0.75, 1.0)])
    m1 = {"t": t, "o": np.ones(24), "h": np.ones(24), "l": np.ones(24), "c": np.ones(24)}
    bars = dict(o=np.ones(6), h=np.ones(6), l=np.ones(6), c=np.ones(6), day=np.arange(6),
                end_ole=np.arange(1, 7, dtype=float), i0=np.arange(0, 24, 4), i1=np.arange(3, 24, 4))
    return m1, bars


class Injection(unittest.TestCase):
    def setUp(self):
        self.old = N.FT
        N.FT = 1

    def tearDown(self):
        N.FT = self.old

    def expected(self):
        # carrier states at the close of bars 0..4: +1 +1 +1 -1 -1; step = mu x ATR = 0.1 x 0.01 = 0.001
        # bar t+1 record at fraction f: cum + s_t x 0.001 x f ; cum after bars 1..5: 0.001 0.002 0.003 0.002 0.001
        f = np.array([0.25, 0.5, 0.75, 1.0])
        e = [np.zeros(4)]                                   # bar 0 (before FT): untouched
        cum = 0.0
        for s in (1, 1, 1, -1, -1):
            e.append(cum + s * 0.001 * f)
            cum += s * 0.001
        return 1.0 + np.concatenate(e)

    def test_known_answer(self):
        m1, bars = synthetic()       # bar k spans (k, k + 1]: its records' time fraction is exactly f
        carrier = np.array([1, 1, 1, -1, -1, 0])
        out, nb = N.inject(m1, bars, carrier, np.full(6, 0.01), 0.1)
        exp = self.expected()
        self.assertLess(np.abs(out["c"] - exp).max(), 1e-12)
        self.assertLess(np.abs(out["h"] - exp).max(), 1e-12)
        self.assertAlmostEqual(nb["c"][5], 1.001, places=12)       # last bar close = cum 0.001
        self.assertAlmostEqual(nb["o"][2], 1.00125, places=12)     # bar 2 first record: 0.001 + 0.001 x 0.25

    def test_planted_one_bar_early(self):
        m1, bars = synthetic()
        early = np.array([1, 1, -1, -1, 0, 0])               # the carrier read one bar early
        out, _ = N.inject(m1, bars, early, np.full(6, 0.01), 0.1)
        self.assertGreater(np.abs(out["c"] - self.expected()).max(), 1e-4)


class ShiftCosts(unittest.TestCase):
    def test_shift(self):
        old = N.FT
        N.FT = 2
        try:
            s = N.shift([9, 9, 1, 2, 3, 4, 5], 2)
            self.assertEqual(list(s), [9, 9, 4, 5, 1, 2, 3])     # state'[t] = state[FT + ((t - FT - k) mod L)]
            self.assertEqual(list(N.shift([9, 9, 1, 2, 3], 0)), [9, 9, 1, 2, 3])
        finally:
            N.FT = old

    def test_half_r_costs(self):
        # long, entry 1.0000, exit 1.0150, ATR 0.0100, 3 days, x2: net = 0.0150 - 0.00024 + 3 x -0.8947 x 0.1 / 856.1
        hf = types.SimpleNamespace(dir=1, exit_price=1.0150, entry=1.0, atr=0.01, entry_bar=0, exit_bar=1)
        roll = 3 * -0.8947 * 1000 / 10000 / (0.08561 / 0.0001)
        self.assertAlmostEqual(N.half_r(hf, np.array([100, 103]), 2), (0.0150 - 0.00024 + roll) / 0.015, places=12)
        hs = types.SimpleNamespace(dir=-1, exit_price=0.9900, entry=1.0, atr=0.01, entry_bar=0, exit_bar=1)
        roll_s = 2 * 0.4259 * 1000 / 10000 / 856.1
        self.assertAlmostEqual(N.half_r(hs, np.array([5, 7]), 1), (0.0100 - 0.00012 + roll_s) / 0.015, places=12)


if __name__ == "__main__":
    unittest.main()
