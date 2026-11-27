"""Tests for tools/prem1.py (PREM1 K1, K2; S-a pooled test; PC-a planting; bounds)."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import prem1 as P  # noqa: E402


def rho1(x):
    x = np.asarray(x) - np.mean(x)
    return float((x[1:] * x[:-1]).sum() / (x * x).sum())


class K2Estimator(unittest.TestCase):
    def test_hand_calculated(self):
        # runs: mu 0; sa2 = 8/7; 2-day sums 2,2,2,0,-2,-2,-2 -> 24; m = 2*7*(1-2/8) = 10.5; sc2 = 24/10.5; VR = 2.0
        self.assertAlmostEqual(P.vr([1, 1, 1, 1, -1, -1, -1, -1], 2), 2.0)
        # alternating: every 2-day sum is 0 -> VR(2) = 0
        self.assertAlmostEqual(P.vr([1, -1] * 4, 2), 0.0)

    def test_ar1_long_series(self):
        rng = np.random.default_rng(1)
        x = P.plant_ar1(rng.normal(size=200000), 0.2)
        self.assertLess(abs(P.vr(x, 2) - 1.2), 0.02)               # VR(2) = 1 + rho_1 = 1.2

    def test_iid_near_one_and_offset_invariant(self):
        rng = np.random.default_rng(2)
        r = rng.normal(size=100000)
        for q in P.QS:
            self.assertLess(abs(P.vr(r, q) - 1), 0.05)
        self.assertAlmostEqual(P.vr(r + 5.0, 10), P.vr(r, 10))     # de-meaned: a drift does not change VR


class K1Generator(unittest.TestCase):
    def test_sizes_kept_signs_random(self):
        rng = np.random.default_rng(3)
        r = rng.normal(size=5000) * np.exp(np.sin(np.arange(5000) / 50))     # clustered sizes
        s = P.sign_surrogate(r, np.random.default_rng(4))
        self.assertEqual(int((np.abs(s) != np.abs(r - r.mean())).sum()), 0)  # |r| kept exactly, in order
        signs = np.sign(s) * np.sign(r - r.mean())
        self.assertLess(abs(signs.mean()), 4 / np.sqrt(5000))              # balanced flips (binomial, 4 sd)
        allpos = P.sign_surrogate(np.abs(r), np.random.default_rng(5))
        self.assertLess(abs(np.mean(allpos > 0) - 0.5), 0.05)               # an all-positive input does not stay positive

    def test_planted_memory_removed(self):
        rng = np.random.default_rng(6)
        x = P.plant_ar1(rng.normal(size=50000), 0.3)
        self.assertGreater(rho1(x), 0.28)
        self.assertLess(abs(rho1(P.sign_surrogate(x, rng))), 0.02)

    def test_matrix_version_keeps_sizes(self):
        r = np.random.default_rng(7).normal(size=300)
        m = P.sign_surrogates(r, np.random.default_rng(8), 5)
        self.assertEqual(m.shape, (5, 300))
        self.assertTrue(np.allclose(np.abs(m), np.abs(r - r.mean())))


class Planting(unittest.TestCase):
    def test_mom_startup_and_recursion(self):
        rs = np.arange(1, 31, dtype=float)
        x = P.plant_mom(rs, 0.5, L=20)
        self.assertTrue(np.array_equal(x[:20], rs[:20]))                    # unchanged before L
        self.assertAlmostEqual(x[20], rs[20] + 0.5 * rs[:20].mean())
        self.assertAlmostEqual(x[21], rs[21] + 0.5 * x[1:21].mean())         # uses planted values (recursive)

    def test_vectorised_equals_rowwise(self):
        rng = np.random.default_rng(9)
        M = rng.normal(size=(3, 400))
        for f, par in ((P.plant_ar1, 0.07), (P.plant_mom, -0.1)):
            A = f(M, par)
            for i in range(3):
                self.assertTrue(np.allclose(A[i], f(M[i], par)))

    def test_mom_raises_long_vr(self):
        rng = np.random.default_rng(10)
        x = P.plant_mom(rng.normal(size=100000), 0.2)
        self.assertGreater(P.vr(x, 40), 1.2)                                 # ~1 + 1.48 kappa (criteria back-of-envelope)


class PooledTest(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(11)
        self.null = 1 + rng.normal(0, 0.01, size=(1000, 3, 6))
        self.m, self.s, self.M, self.bar = P.null_stats(self.null)

    def test_null_bar(self):
        self.assertGreater(self.bar, 2.0)
        self.assertLess(self.bar, 3.2)                                       # 6 independent two-sided horizons: ~2.6
        self.assertAlmostEqual(np.mean(self.M > self.bar), 0.05, delta=0.01)

    def test_flag_and_sign_rule(self):
        base = np.ones((3, 6))
        big = base.copy()
        big[:, 3] += 0.05                                                    # all three pairs up at q = 20
        z, fl = P.flags(big, self.m, self.s, self.bar)
        self.assertEqual(fl, [3])
        one = base.copy()
        one[0, 3] += 0.15                                                    # pooled up, but only 1 of 3 pairs above 1
        one[1, 3] -= 0.001
        one[2, 3] -= 0.001
        z, fl = P.flags(one, self.m, self.s, self.bar)
        self.assertGreater(abs(z[3]), self.bar)
        self.assertEqual(fl, [])                                             # the 2-of-3 rule blocks it
        down = base.copy()
        down[:, 1] -= 0.05
        self.assertEqual(P.flags(down, self.m, self.s, self.bar)[1], [1])   # two-sided: reversal flagged
        self.assertEqual(P.flags(down, self.m, self.s, self.bar, want_sign=1)[1], [])   # wrong planted sign not counted
        self.assertEqual(P.flags(base, self.m, self.s, self.bar)[1], [])


class Bounds(unittest.TestCase):
    def test_bound(self):
        rows = []
        for lv, rp, rn in ((0.01, 0.2, 0.2), (0.02, 0.8, 0.95), (0.03, 0.92, 0.9), (0.05, 1.0, 1.0)):
            for sign, rate in ((1, rp), (-1, rn)):
                k = int(rate * 100)
                rows += [dict(kind="ar1", level=f"{sign * lv:+.2f}", flagged=str(int(i < k))) for i in range(100)]
        rates = P.detection_table(rows)
        self.assertAlmostEqual(rates[("ar1", 0.02)], 0.8)
        self.assertEqual(P.bound(rates, "ar1"), 0.03)                        # 0.02 fails on the + side
        self.assertIsNone(P.bound({}, "mom"))                                # ladder missed -> None (amendment)
        ext = dict(rates)
        ext.update({("mom", 0.2): 0.96, ("mom", -0.2): 0.72, ("mom", 0.3): 0.99, ("mom", -0.3): 0.91})
        self.assertEqual(P.bound(ext, "mom"), 0.3)                           # extension levels are read from the rates
        self.assertEqual(P.bound(ext, "mom", signs=(1,)), 0.2)               # trend side only (information row)
        self.assertEqual(P.bound(ext, "mom", signs=(-1,)), 0.3)


if __name__ == "__main__":
    unittest.main()
