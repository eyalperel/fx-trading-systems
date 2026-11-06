"""Self-test for analysis/harness/reference.py (STEP2_HANDOFF.md, Stage 1).

Run:  python -m unittest discover -s analysis/harness/tests -v
Each pre-registered check prints one line: expected, actual, |diff|, tolerance, PASS/FAIL.
Lines starting with 'INFO' are reported values, never PASS/FAIL (D1 rule 3).
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import reference as R  # noqa: E402

TS = (5, 10, 20, 40, 100)
# Copied from analysis/harness/h1_check.py EXPECT (= H1 criteria §4 table, (a)); H1 files untouched.
# P: (flat error, gains at T=5,10,20,40,100, ramp lag). Table stores 6 decimals.
EXPECT = {
    10: (0.0, [0.224200, 0.695059, 0.966116, 0.997024, 0.999785], 1.825321),
    14: (0.0, [0.116965, 0.446731, 0.894265, 0.991557, 0.999643], 2.704175),
    20: (0.0, [0.057665, 0.238406, 0.704174, 0.969143, 0.999037], 4.038666),
    30: (0.0, [0.025669, 0.108551, 0.404454, 0.870678, 0.995811], 6.277073),
}
H1_TOL_GAIN = 1e-4   # h1_check.TOL_GAIN
H1_TOL_LAG = 1e-3    # h1_check.TOL_LAG


def line(cid, exp, act, tol, ok=None):
    d = abs(act - exp)
    if ok is None:
        ok = d <= tol
    print("  %-46s exp %-14.9g act %-14.9g |diff| %.3e tol %.0e %s"
          % (cid, exp, act, d, tol, "PASS" if ok else "FAIL"))
    return ok


class TestReference(unittest.TestCase):

    # Amendment 1 (STEP2_HANDOFF.md, 2026-11-06), A1.1: the H1 EXPECT table was computed with
    # exact pi, so it is compared with ss2_code(pi_value=math.pi) and with ss2_article
    # (the same filter written independently), tol 1e-6.
    FORMS = (("code(pi)", lambda p: R.ss2_code(p, pi_value=math.pi)),
             ("article", R.ss2_article))

    def test_01_gain_vs_h1_table(self):
        """A1.1: gains vs H1 §4 table, both forms, tol 1e-6 (pre-registered, amended)."""
        fails = []
        for name, mk in self.FORMS:
            for p, (_, gains, _) in EXPECT.items():
                f = mk(p)
                for t, e in zip(TS, gains):
                    if not line("gain %s P=%d T=%d" % (name, p, t), e, R.gain_at(f, t), 1e-6):
                        fails.append((name, p, t))
        self.assertEqual(fails, [], "gain mismatches vs table at 1e-6")

    def test_02_ramp_lag_vs_h1_table(self):
        """A1.1: ramp lag vs H1 §4 table, both forms, tol 1e-6 (pre-registered, amended)."""
        fails = []
        for name, mk in self.FORMS:
            for p, (_, _, lag) in EXPECT.items():
                if not line("ramp lag %s P=%d" % (name, p), lag, R.ramp_lag(mk(p)), 1e-6):
                    fails.append((name, p))
        self.assertEqual(fails, [], "lag mismatches vs table at 1e-6")

    def test_02b_info_pi_gap(self):
        """A1.2 INFO (never PASS/FAIL): ss2_code(Zorro PI) - ss2_code(exact pi), P = 10..30.
        This is the PI floor term for D2."""
        wg = wl = 0.0
        where_g = where_l = None
        for p in range(10, 31):
            fz, fe = R.ss2_code(p), R.ss2_code(p, pi_value=math.pi)
            for t in TS:
                d = abs(R.gain_at(fz, t) - R.gain_at(fe, t))
                if d > wg:
                    wg, where_g = d, (p, t)
            dl = abs(R.ramp_lag(fz) - R.ramp_lag(fe))
            if dl > wl:
                wl, where_l = dl, p
        print("  INFO A1.2 PI gap (Zorro float32 PI minus exact pi), P=10..30, T in %s: "
              "largest gain diff %.3e (P=%d, T=%d); largest lag diff %.3e (P=%d)"
              % (TS, wg, where_g[0], where_g[1], wl, where_l))

    def test_03_ss2_code_dc_gain(self):
        """DC gain = 1 for any period, tol 1e-12 (pre-registered)."""
        for p in (3, 5, 10, 14, 20, 30, 50, 100):
            for name, f in (("code", R.ss2_code(p)), ("article", R.ss2_article(p))):
                self.assertTrue(line("DC gain %s P=%d" % (name, p), 1.0, R.dc_gain(f), 1e-12))

    def test_04_analytic_vs_simulated_P20(self):
        """Analytic vs simulated gain and lag, P=20, all T, tol 1e-6 (pre-registered)."""
        f = R.ss2_code(20)
        for t in TS:
            self.assertTrue(line("analytic vs sim gain P=20 T=%d" % t,
                                 R.gain_at(f, t), R.sim_gain(f, t), 1e-6))
        self.assertTrue(line("analytic vs sim ramp lag P=20", R.ramp_lag(f), R.sim_lag(f), 1e-6))
        self.assertTrue(line("sim DC error P=20 (flat)", 0.0, R.sim_dc_error(f), 1e-9))

    def test_05_article_vs_code(self):
        """Largest gain diff ss2_article vs ss2_code, P=10..30. Report; FAIL only if > 1e-5."""
        worst, where = 0.0, None
        worst_lag = 0.0
        for p in range(10, 31):
            fa, fc = R.ss2_article(p), R.ss2_code(p)
            for t in (5, 10, 20, 40, 100):
                d = abs(R.gain_at(fa, t) - R.gain_at(fc, t))
                if d > worst:
                    worst, where = d, (p, t)
            worst_lag = max(worst_lag, abs(R.ramp_lag(fa) - R.ramp_lag(fc)))
        print("  INFO article vs code: largest gain diff %.3e at P=%d T=%d; largest lag diff %.3e"
              % (worst, where[0], where[1], worst_lag))
        print("  INFO D1 expected ~6e-7 (b, computed 2026-11-06 vs the exact-pi/sqrt(2) .c form)")
        self.assertTrue(line("article vs code largest gain diff", 0.0, worst, 1e-5))

    def test_06_ema_ramp_lag_known_answer(self):
        """Measuring-tool check: EMA alpha=0.4 ramp lag = 1.50 bars, tol 1e-9 (pre-registered)."""
        f = R.ema(0.4)
        self.assertTrue(line("EMA(0.4) ramp lag, analytic", 1.5, R.ramp_lag(f), 1e-9))
        # simulated cross-check (EMA(0.4) transient 0.6^n is gone long before n=2900)
        self.assertTrue(line("EMA(0.4) ramp lag, simulated", 1.5, R.sim_lag(f), 1e-9))

    def test_07_negative_controls(self):
        """NC-A and NC-B must FAIL the H1 gain check (tol 1e-4) at P=20 (pre-registered, A1.4).
        Also prints error/tolerance ratios per check (gain, lag, DC) for the D2 per-control rule."""
        eg, el = EXPECT[20][1], EXPECT[20][2]
        TOL_FLAT = 1e-9      # h1_check.TOL_FLAT, applied to |y - level| on the flat input
        res = {}
        for name, kw in (("NC-A", dict(c1_bump=1)), ("NC-B", dict(in_bump=1))):
            f = R.ss2_code(20, **kw)
            gdiff = [abs(R.gain_at(f, t) - e) for t, e in zip(TS, eg)]
            ldiff = abs(R.ramp_lag(f) - el)
            dc_err = abs(R.dc_gain(f) - 1.0)
            flat_err = R.FLAT_LEVEL * dc_err      # flat-input level error as H1 measures it
            fired = max(gdiff) > H1_TOL_GAIN
            res[name] = dc_err
            print("  %s largest gain err %.3e (T=%d)  lag err %.3e  DC gain err %.3e  "
                  "H1 gain check %s" % (name, max(gdiff), TS[gdiff.index(max(gdiff))], ldiff,
                                        dc_err, "FAILS (required)" if fired else "PASSES (BROKEN)"))
            print("  INFO %s err/tol ratios: gain %.2fx (tol 1e-4)  lag %.3fx (tol 1e-3)  "
                  "DC/flat %.3gx (flat err %.3e, tol 1e-9)"
                  % (name, max(gdiff) / H1_TOL_GAIN, ldiff / H1_TOL_LAG,
                     flat_err / TOL_FLAT, flat_err))
            self.assertTrue(fired, name + " did not fail the gain check")
        self.assertAlmostEqual(res["NC-A"], 0.0, delta=1e-12)     # A keeps DC gain 1
        self.assertGreater(res["NC-B"], 1e-6)                    # B does not

    def test_08_guard_checks_can_fail(self):
        """The comparison itself must fail on a wrong answer (guards that fire)."""
        self.assertFalse(line("deliberate: EMA(0.5) vs 1.50", 1.5, R.ramp_lag(R.ema(0.5)), 1e-9))
        self.assertFalse(line("deliberate: ss2_code(21) vs P=20 gain T=20", EXPECT[20][1][2],
                              R.gain_at(R.ss2_code(21), 20), 1e-6))


if __name__ == "__main__":
    unittest.main()
