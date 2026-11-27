"""Tests for tools/prem2.py (PREM2 K1, K2: loader, thirds, single-series S-2 test, L = 120 planting, bounds)."""
import io
import os
import sys
import tempfile
import unittest
import zipfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import prem1 as P1  # noqa: E402
import prem2 as P  # noqa: E402

T0 = 1502942400          # 2017-08-17 04:00 UTC (s)
H4 = 4 * 3600


def write_zip(path, rows):
    buf = io.StringIO()
    for t, c in rows:
        buf.write(f"{t},{c},{c},{c},{c},1,{t + H4 - 1},1,1,1,1,0\n")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(os.path.basename(path).replace(".zip", ".csv"), buf.getvalue())


class Loader(unittest.TestCase):
    def test_ms_us_gap_and_grid(self):
        with tempfile.TemporaryDirectory() as d:
            write_zip(os.path.join(d, "BTCUSDT-4h-2017-08.zip"), [((T0 + k * H4) * 1000, 100 + k) for k in range(3)])
            # next file: microseconds, one missing bar (gap of 8h) before its first row
            write_zip(os.path.join(d, "BTCUSDT-4h-2025-01.zip"), [((T0 + k * H4) * 1000000, 100 + k) for k in (4, 5)])
            b = P.load_bars(d)
            self.assertEqual(b["units"], (3, 2))
            self.assertEqual(list(b["t"]), [T0 + k * H4 for k in (0, 1, 2, 4, 5)])
            self.assertEqual(P.utc(b["t"][0]), "2017-08-17 04:00")
            self.assertEqual(list(P.gaps(b)), [2])                    # return 2 spans the gap: kept as one return (G-a)
            r = P.returns_from(b)
            self.assertEqual(len(r), 4)
            self.assertAlmostEqual(r[2], np.log(104 / 102))

    def test_off_grid_refused(self):
        with tempfile.TemporaryDirectory() as d:
            write_zip(os.path.join(d, "BTCUSDT-4h-2017-08.zip"), [((T0 + k * H4 + 60) * 1000, 100) for k in range(3)])
            with self.assertRaises(SystemExit):
                P.load_bars(d)

    def test_non_increasing_refused(self):
        with tempfile.TemporaryDirectory() as d:
            write_zip(os.path.join(d, "BTCUSDT-4h-2017-08.zip"), [((T0 + k * H4) * 1000, 100) for k in (0, 1, 1)])
            with self.assertRaises(SystemExit):
                P.load_bars(d)


class Thirds(unittest.TestCase):
    def test_sizes(self):
        for n, want in ((20159, [6719, 6720, 6720]), (9, [3, 3, 3]), (10, [3, 3, 4]), (11, [3, 4, 4])):
            tb = P.third_bounds(n)
            self.assertEqual([b - a for a, b in tb], want)
            self.assertEqual(tb[0][0], 0)
            self.assertEqual(tb[2][1], n)
            self.assertEqual(tb[0][1], tb[1][0])
            self.assertEqual(tb[1][1], tb[2][0])

    def test_vr_parts_rows(self):
        rng = np.random.default_rng(5)
        r = rng.normal(size=3001)
        v = P.vr_parts(r)
        self.assertEqual(v.shape, (4, len(P.QS)))
        self.assertAlmostEqual(v[0, 3], P1.vr(r, P.QS[3]))
        a, b = P.third_bounds(len(r))[1]
        self.assertAlmostEqual(v[2, 0], P1.vr(r[a:b], P.QS[0]))


class SingleSeriesTest(unittest.TestCase):
    def setUp(self):
        nq = len(P.QS)
        self.m, self.s, self.bar = np.ones(nq), np.full(nq, 0.1), 2.5

    def table(self, j, full, thirds):
        v = np.ones((4, len(P.QS)))
        v[0, j] = full
        v[1:, j] = thirds
        return v

    def test_all_thirds_agree_flagged(self):
        z, fl, ep = P.flags(self.table(3, 1.5, (1.4, 1.6, 1.2)), self.m, self.s, self.bar)
        self.assertEqual((fl, ep), ([3], []))
        self.assertAlmostEqual(z[3], 5.0)

    def test_two_of_three_enough(self):
        _, fl, _ = P.flags(self.table(3, 1.5, (1.4, 0.9, 1.2)), self.m, self.s, self.bar)
        self.assertEqual(fl, [3])

    def test_one_third_spike_blocked(self):
        _, fl, ep = P.flags(self.table(7, 1.5, (2.5, 0.9, 0.95)), self.m, self.s, self.bar)
        self.assertEqual((fl, ep), ([], [7]))                          # episode-driven, not flagged

    def test_reversal_two_sided(self):
        _, fl, _ = P.flags(self.table(1, 0.6, (0.7, 0.5, 0.8)), self.m, self.s, self.bar)
        self.assertEqual(fl, [1])

    def test_wrong_planted_sign_not_counted(self):
        _, fl, ep = P.flags(self.table(1, 0.6, (0.7, 0.5, 0.8)), self.m, self.s, self.bar, want_sign=1)
        self.assertEqual((fl, ep), ([], []))

    def test_below_bar_not_flagged(self):
        _, fl, ep = P.flags(self.table(0, 1.2, (1.2, 1.2, 1.2)), self.m, self.s, self.bar)   # z = 2.0
        self.assertEqual((fl, ep), ([], []))

    def test_null_bar(self):
        rng = np.random.default_rng(6)
        nv = 1 + 0.05 * rng.normal(size=(4000, 4, len(P.QS)))
        m, s, M, bar = P.null_stats(nv)
        self.assertAlmostEqual(np.mean(M > bar), 0.05, delta=0.002)
        self.assertGreater(bar, 2.6)                                    # 9 independent two-sided: about 2.77
        self.assertLess(bar, 2.95)


class Planting(unittest.TestCase):
    def test_mom120_startup_and_recursion(self):
        rng = np.random.default_rng(7)
        rs = rng.normal(size=400)
        x = P.plant("mom120", rs, 0.4)
        np.testing.assert_array_equal(x[:120], rs[:120])
        self.assertAlmostEqual(x[120], rs[120] + 0.4 * rs[:120].mean())
        self.assertAlmostEqual(x[300], rs[300] + 0.4 * x[180:300].mean())

    def test_vectorised_equals_rowwise(self):
        rng = np.random.default_rng(8)
        rs = rng.normal(size=(3, 500))
        for kind in ("ar1", "mom20", "mom120"):
            xa = P.plant(kind, rs, 0.3)
            for i in range(3):
                np.testing.assert_allclose(xa[i], P.plant(kind, rs[i], 0.3), rtol=0, atol=1e-12)

    def test_mom120_raises_vr240(self):
        rng = np.random.default_rng(9)
        x = P.plant("mom120", rng.normal(size=200000), 0.4)
        self.assertGreater(P1.vr(x, 240), 1.3)                          # about 1 + 1.5 kappa = 1.6

    def test_sign_surrogate_keeps_sizes_on_long_series(self):
        rng = np.random.default_rng(10)
        r = rng.standard_t(3, size=20159) * 0.01
        rs = P1.sign_surrogate(r, rng)
        np.testing.assert_allclose(np.abs(rs), np.abs(r - r.mean()), rtol=0, atol=0)


class K3Check(unittest.TestCase):
    def good(self):
        return dict(bars=P.K3_BARS, first=P.K3_FIRST, last=P.K3_LAST, units=P.K3_UNITS, gaps=P.K3_GAPS,
                    gap_hours=P.K3_GAP_HOURS, missing=P.K3_MISSING)

    def test_record_passes(self):
        self.assertTrue(P.k3_check(self.good()))
        self.assertEqual(sum(h // 4 - 1 for h in P.K3_GAP_HOURS), P.K3_MISSING)     # record is self-consistent

    def test_each_item_fires(self):
        bad = {"bars": 20159, "first": "2017-08-17 08:00", "last": "2026-10-31 16:00", "units": (16145, 4015),
               "gaps": P.K3_GAPS[:-1], "gap_hours": (8, 28, 12, 8, 8, 8, 12, 8, 8), "missing": 16}
        for k, v in bad.items():
            sm = self.good()
            sm[k] = v
            self.assertFalse(P.k3_check(sm), k)


class Bounds(unittest.TestCase):
    def test_bound_per_kind(self):
        rates = {("mom120", 0.4): 0.95, ("mom120", -0.4): 0.85, ("mom120", 0.6): 0.99, ("mom120", -0.6): 0.93,
                 ("ar1", 0.05): 0.91, ("ar1", -0.05): 0.90}
        self.assertEqual(P.bound(rates, "mom120"), 0.6)
        self.assertEqual(P.bound(rates, "mom120", signs=(1,)), 0.4)
        self.assertEqual(P.bound(rates, "ar1"), 0.05)
        self.assertIsNone(P.bound({("mom20", 0.4): 0.5, ("mom20", -0.4): 0.95}, "mom20"))


if __name__ == "__main__":
    unittest.main()
