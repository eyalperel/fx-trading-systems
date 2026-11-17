"""Tests for the high-pass reference models (HARNESS_DESIGN D4; HP-A = TASC V.32:1 2014 / V.33:09 2015).

Run with the rest of the suite: bash analysis/harness/run_tests.sh
Known answers below are (b) values computed in the planning chat 2026-11-16 and re-derived here; every
check has a numeric tolerance. Fire tests (CLAUDE.md 4.4) perturb only the thing they target.
Labels: (a) source states, (b) measured / computed, (c) inference.
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))

import reference as R   # noqa: E402

F32_0707 = float(np.float32(0.707))
SQRT_HALF = math.sqrt(2.0) / 2.0
PERIODS = (2, 3, 4, 5, 7, 10, 14, 20, 30, 40, 50, 60, 75, 100)


def alpha_of(f):
    """alpha1 recovered from the filter: feedback tap a1 = 2(1 - alpha1)."""
    return 1.0 - f.a[0] / 2.0


def fit(f, t, seed=None, n_bars=3000, w=500):
    """Independent lstsq fit y = a sin + b cos + c on a simulated sine (own code, not checker)."""
    n = np.arange(n_bars, dtype=float)
    x = 1.1 + 0.01 * np.sin(2 * math.pi * n / t)
    y = R.simulate(f, x, seed=seed)[w:]
    ww = 2 * math.pi * n[w:] / t
    A = np.column_stack([np.sin(ww), np.cos(ww), np.ones_like(ww)])
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    return math.hypot(c[0], c[1]) / 0.01, math.atan2(c[1], c[0])


class TestKnownAnswers(unittest.TestCase):
    def test_01_first_difference(self):
        f = R.Filter(b=(1.0, -1.0), a=())
        self.assertAlmostEqual(R.gain_at(f, 4), math.sqrt(2.0), places=12)
        self.assertAlmostEqual(R.phase_at(f, 4), math.pi / 4, places=12)
        self.assertAlmostEqual(R.ramp_residual(f, 1.1, 1e-4), 1e-4, places=15)
        self.assertLess(R.dc_gain(f), 1e-15)
        g, ph = fit(f, 4)        # simulation agrees with the analytic phase sign convention
        self.assertAlmostEqual(g, math.sqrt(2.0), places=9)
        self.assertAlmostEqual(ph, math.pi / 4, places=9)

    def test_02_hp_article_48(self):
        f = R.hp_article(48)
        self.assertAlmostEqual(alpha_of(f), 0.08852627461, places=10)
        self.assertAlmostEqual(1.0 - alpha_of(f), 0.91147372539, places=10)       # double pole radius
        for t, g, ph in ((20, 0.921232, 0.568957), (100, 0.315277, 1.949209), (2, 1.0, 0.0)):
            self.assertLess(abs(R.gain_at(f, t) - g), 1e-6, "gain T=%d" % t)
            self.assertLess(abs(R.phase_at(f, t) - ph), 1e-6, "phase T=%d" % t)

    def test_03_phase_sign_matches_checker_fit(self):
        """phase_at must equal atan2(b, a) of the lstsq fit (the checker's convention) and NOT its negative."""
        f = R.hp_article(48)
        for t in (5, 20, 100):
            g, ph = fit(f, t, seed="zero")
            self.assertLess(abs(R.phase_at(f, t) - ph), 1e-6, "T=%d" % t)
            self.assertGreater(abs(-R.phase_at(f, t) - ph), 0.1, "fire: sign flip is visible, T=%d" % t)

    def test_04_dc_gain_zero(self):
        for f in (R.hp_article(48), R.hp_code(48), R.hp_code(20, num="1st")):
            self.assertLess(R.dc_gain(f), 1e-15)

    def test_05_code_vs_article_floor(self):
        """hp_code(k = float32(0.707)) vs hp_article: max gain / phase gap over PERIODS."""
        want = {20: 7.59e-5, 48: 7.49e-5, 125: 5.55e-5}
        worst_ph = 0.0
        for p, wg in want.items():
            fa, fc = R.hp_article(p), R.hp_code(p)
            gg = max(abs(R.gain_at(fc, t) - R.gain_at(fa, t)) for t in PERIODS)
            ph = max(abs(R.phase_at(fc, t) - R.phase_at(fa, t)) for t in PERIODS)
            worst_ph = max(worst_ph, ph)
            self.assertLess(abs(gg - wg) / wg, 0.01, "P=%d gain gap %.3e vs %.3e" % (p, gg, wg))
        self.assertGreater(worst_ph, 1.3e-4)
        self.assertLess(worst_ph, 1.7e-4)

    def test_06_corrected_code_is_article_up_to_pi(self):
        """k = sqrt(2)/2 with exact pi reproduces the article coefficients to rounding (fire: PI_ZORRO does not)."""
        fa = R.hp_article(48)
        fx = R.hp_code(48, k=SQRT_HALF, pi_value=math.pi)
        self.assertLess(max(abs(np.array(fx.b) - np.array(fa.b))), 1e-15)
        self.assertLess(max(abs(np.array(fx.a) - np.array(fa.a))), 1e-15)
        fz = R.hp_code(48, k=SQRT_HALF)               # Zorro PI: small but visible
        self.assertGreater(max(abs(np.array(fz.a) - np.array(fa.a))), 1e-8)

    def test_07_price_seeded_transient(self):
        f = R.hp_code(48)                              # current .c: k = float32(0.707)
        x = np.full(400, 1.1)
        y = R.simulate(f, x, seed="price")
        # (b) values at raw-file index n (n = 0 is the first bar), computed here 2026-11-16
        for n, want in ((50, 5.372e-2), (100, 9.409e-4), (200, 1.679e-7), (300, 2.332e-11)):
            self.assertLess(abs(abs(y[n]) - want) / want, 0.01, "n=%d |y|=%.3e want %.3e" % (n, abs(y[n]), want))
        # The planning-chat numbers (6.3e-2 @50, 1.1e-3 @100, 2.0e-7 @200, 2.8e-11 @300) match this simulation
        # at index n-2 within 6%: a 2-bar labelling offset, not a model difference (c: likely 1-based counting
        # from the third bar). Recorded in the STOP-stage report.
        for n, want in ((50, 6.3e-2), (100, 1.1e-3), (200, 2.0e-7), (300, 2.8e-11)):
            self.assertLess(abs(abs(y[n - 2]) - want) / want, 0.06, "n-2=%d" % (n - 2))
            self.assertGreater(abs(abs(y[n]) - want) / want, 0.1, "fire: unshifted index does NOT match")

    def test_08_seed_zero_flat_is_exactly_zero(self):
        f = R.hp_article(48)
        x = np.full(300, 1.1)
        self.assertEqual(float(np.max(np.abs(R.simulate(f, x, seed="zero")))), 0.0)
        self.assertGreater(abs(R.simulate(f, x, seed="price")[0]), 0.05)         # fire: price seed is not zero

    def test_09_default_simulate_unchanged(self):
        """seed=None == seed='price' == the pre-HP behaviour (SS2/SS3 byte-identical): own re-implementation."""
        f = R.ss3_code(20)
        x = 1.1 + 1e-4 * np.arange(200) + 0.01 * np.sin(np.arange(200) / 3.0)
        old = np.empty(len(x))
        for n in range(len(x)):
            acc = 0.0
            for k in range(len(f.b)):
                acc += f.b[k] * (x[n - k] if n - k >= 0 else x[0])
            for k in range(len(f.a)):
                acc += f.a[k] * (old[n - k - 1] if n - k - 1 >= 0 else x[0])
            old[n] = acc
        self.assertTrue(np.array_equal(R.simulate(f, x), old))
        self.assertTrue(np.array_equal(R.simulate(f, x, seed="price"), old))
        self.assertFalse(np.array_equal(R.simulate(f, x, seed="zero"), old))     # fire
        with self.assertRaises(ValueError):
            R.simulate(f, x, seed="bogus")


class TestRampResidual(unittest.TestCase):
    L, S = 1.1, 1e-4

    def sim_resid(self, f, seed="zero"):
        n = np.arange(3000, dtype=float)
        x = self.L + self.S * n
        y = R.simulate(f, x, seed=seed)
        return y[-100:], x[-100:], n[-100:]

    def test_10_hp_article_residual_is_zero(self):
        for p in (20, 30, 48, 125):
            f = R.hp_article(p)
            self.assertEqual(R.ramp_residual(f, self.L, self.S), 0.0)
            y, *_ = self.sim_resid(f)
            self.assertLess(float(np.max(np.abs(y))), 1e-12, "P=%d" % p)

    def test_11_first_numerator_residual(self):
        """num='1st': constant S*c/alpha^2 (derivation in the module docstring); simulation agrees."""
        f = R.hp_code(48, k=SQRT_HALF, pi_value=math.pi, num="1st")
        r = R.ramp_residual(f, self.L, self.S)
        al = alpha_of(f)
        self.assertAlmostEqual(r, self.S * (1 - al / 2) ** 2 / al ** 2, places=12)
        y, *_ = self.sim_resid(f)
        self.assertLess(float(np.max(np.abs(y - r))), 1e-10)
        self.assertGreater(abs(r), 1e-3)                                       # fire: visibly non-zero

    def test_12_general_dc_gain_one(self):
        """DC gain 1: y_ss(n) = x[n] - S*ramp_lag  (cross-check against ramp_lag)."""
        f = R.ema(0.1)
        n = 2999
        r = R.ramp_residual(f, self.L, self.S, n=n)
        self.assertAlmostEqual(r, self.L + self.S * n - self.S * R.ramp_lag(f), places=12)
        y, x, nn = self.sim_resid(f, seed="price")
        self.assertLess(abs(y[-1] - r), 1e-10)

    def test_13_perturbed_models_residual_vs_sim(self):
        for kw in (dict(alpha_bump=1), dict(in_bump=1), dict(fb2_bump=1)):
            f = R.hp_code(48, k=SQRT_HALF, pi_value=math.pi, **kw)
            r = R.ramp_residual(f, self.L, self.S)
            y, *_ = self.sim_resid(f)
            self.assertLess(float(np.max(np.abs(y - r))), 1e-10, str(kw))


class TestHpCodeHooks(unittest.TestCase):
    def base(self, **kw):
        return R.hp_code(48, k=SQRT_HALF, pi_value=math.pi, **kw)

    def test_14_default_k_is_float32_0707(self):
        self.assertAlmostEqual(F32_0707, 0.7070000171661377, places=15)
        a = R.hp_code(48)
        b = R.hp_code(48, k=F32_0707, pi_value=R.PI_ZORRO)
        self.assertEqual(a, b)
        self.assertNotEqual(R.hp_code(48, k=SQRT_HALF), a)

    def test_15_alpha_bump_before_coefficients(self):
        f0, f1 = self.base(), self.base(alpha_bump=1)
        al0 = alpha_of(f0)
        al1 = R.bump3(al0, 1)
        self.assertAlmostEqual(alpha_of(f1), al1, places=14)
        self.assertAlmostEqual(f1.b[0], (1 - al1 / 2) ** 2, places=14)
        self.assertAlmostEqual(f1.a[1], -(1 - al1) ** 2, places=14)

    def test_16_in_bump_only_input_taps(self):
        f0, f1 = self.base(), self.base(in_bump=1)
        self.assertEqual(f1.a, f0.a)
        self.assertAlmostEqual(f1.b[0], R.bump3(f0.b[0], 1), places=14)
        self.assertAlmostEqual(f1.b[1], -2 * f1.b[0], places=14)
        self.assertAlmostEqual(f1.b[2], f1.b[0], places=14)

    def test_17_fb2_bump_only_second_feedback(self):
        f0, f1 = self.base(), self.base(fb2_bump=1)
        self.assertEqual(f1.b, f0.b)
        self.assertEqual(f1.a[0], f0.a[0])
        self.assertAlmostEqual(f1.a[1], -R.bump3((1 - alpha_of(f0)) ** 2, 1), places=14)

    def test_18_num_first_and_deg(self):
        f0, f1 = self.base(), self.base(num="1st")
        self.assertEqual(len(f1.b), 2)
        self.assertEqual(f1.a, f0.a)
        self.assertAlmostEqual(f1.b[0], f0.b[0], places=14)
        self.assertAlmostEqual(f1.b[1], -f0.b[0], places=14)
        fd = R.hp_code(48, k=SQRT_HALF, deg=True)
        arg = SQRT_HALF * 360.0 / 48
        self.assertAlmostEqual(1 - alpha_of(fd), 1 - (math.cos(arg) + math.sin(arg) - 1) / math.cos(arg), places=12)
        with self.assertRaises(ValueError):
            R.hp_code(48, num="3rd")

    def test_19_article_model_registry(self):
        """article_model: restricted names, no eval. Unknown -> None."""
        self.assertEqual(R.article_model("hp_article(48)"), R.hp_article(48))
        self.assertIsNone(R.article_model("hp_article(48); import os"))
        self.assertIsNone(R.article_model("ss2_article(48)"))
        self.assertIsNone(R.article_model("os.system('x')"))


if __name__ == "__main__":
    unittest.main()
