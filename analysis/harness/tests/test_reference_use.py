"""USE stage 1: reference.py additions for the UltimateSmoother (V.42:04): seed mode `pass<n>`, the complement model
`one_minus`, `us_article` / `us_code` and the control models, `article_model('us_article(P)')`, `IMP_MODELS`, and the
planning-chat findings 1-7 reproduced independently (a second implementation: direct EasyLanguage-style recursion).

Rule (CLAUDE.md 4.4): every guard is SEEN TO FIRE on a deliberately broken input. No .c file is read, no Zorro run.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))
import reference as R   # noqa: E402

TS = (5, 10, 20, 40, 100)
LEVEL, AMP, SLOPE = 1.1, 0.01, 0.0001


def inputs(n=3000):
    k = np.arange(n, dtype=float)
    return {"flat": np.full(n, LEVEL), "ramp": LEVEL + SLOPE * k,
            "s20": LEVEL + AMP * np.sin(2 * math.pi * k / 20), "s5": LEVEL + AMP * np.sin(2 * math.pi * k / 5),
            "alt": LEVEL + AMP * (1.0 - 2.0 * (k % 2))}


def easylanguage_us(price, period, pi=math.pi):
    """Independent implementation: the V.42:04 sidebar, line by line (CurrentBar starts at 1, US = Price for CurrentBar < 4)."""
    a1 = math.exp(-math.sqrt(2.0) * pi / period)
    b1 = 2 * a1 * math.cos(math.sqrt(2.0) * pi / period)
    c2, c3 = b1, -a1 * a1
    c1 = (1 + c2 - c3) / 4
    us = []
    for i, p in enumerate(price):
        cur = i + 1
        if cur >= 4:
            us.append((1 - c1) * p + (2 * c1 - c2) * price[i - 1] - (c1 + c3) * price[i - 2] + c2 * us[i - 1] + c3 * us[i - 2])
        else:
            us.append(p)
    return np.array(us)


class TestPassSeed(unittest.TestCase):
    def test_01_pass_n_parsing_and_refusal(self):
        self.assertEqual((R.pass_n("pass3"), R.pass_n("pass4"), R.pass_n("zero"), R.pass_n(None), R.pass_n("pass")), (3, 4, None, None, None))
        for bad in ("pass", "pass-1", "passx", "Pass3", "three"):
            with self.assertRaises(ValueError, msg=bad):
                R.simulate(R.ema(0.5), np.ones(5), seed=bad)

    def test_02_first_n_outputs_equal_the_input_then_the_recursion_runs(self):
        x = inputs()["s5"][:40]
        y = R.simulate(R.us_article(20), x, seed="pass3")
        self.assertTrue(np.array_equal(y[:3], x[:3]))
        f = R.us_article(20)
        want = f.b[0] * x[3] + f.b[1] * x[2] + f.b[2] * x[1] + f.a[0] * y[2] + f.a[1] * y[1]          # the 4th call, by hand
        self.assertAlmostEqual(y[3], want, delta=1e-15)
        self.assertNotEqual(y[3], x[3])

    def test_03_equals_the_easylanguage_recursion(self):
        """(a) the sidebar's CurrentBar >= 4 rule, implemented independently, on every input."""
        worst = 0.0
        for k, x in inputs().items():
            for p in (10, 14, 20, 30):
                worst = max(worst, float(np.max(np.abs(R.simulate(R.us_article(p), x, seed="pass3") - easylanguage_us(x, p)))))
        print("\n  pass3 vs independent EasyLanguage recursion: max |diff| %.3e over 5 inputs x 4 periods" % worst)
        self.assertLessEqual(worst, 1e-12)

    def test_04_flat_and_ramp_are_seed_independent_s20_is_not(self):
        """Finding 7: 3-bar and 4-bar seed give IDENTICAL output on flat and ramp, up to 8.337e-4 apart on s20."""
        f, x = R.us_article(20), inputs()
        d = {k: float(np.max(np.abs(R.simulate(f, x[k], seed="pass3") - R.simulate(f, x[k], seed="pass4")))) for k in x}
        print("\n  pass3 vs pass4: " + ", ".join("%s %.3e" % kv for kv in d.items()))
        self.assertLessEqual(d["flat"], 1e-15)
        self.assertLessEqual(d["ramp"], 1e-15)
        self.assertGreater(d["s20"], 1e-4)
        self.assertAlmostEqual(d["s20"], 8.337e-4, delta=5e-7)
        self.assertGreater(d["s5"], d["s20"])                      # (b) s5 and alt see the seed more strongly
        self.assertGreater(d["alt"], d["s5"])

    def test_05_the_old_modes_are_unchanged(self):
        x = inputs()["s5"][:200]
        f = R.us_article(14)
        a = R.simulate(f, x)
        self.assertTrue(np.array_equal(a, R.simulate(f, x, seed="price")))
        self.assertFalse(np.array_equal(a, R.simulate(f, x, seed="zero")))

    def test_06_guard_fires_a_wrong_seed_is_visible(self):
        """pass3 vs zero and vs price differ on every non-flat input: the seed is not a silent default."""
        f, x = R.us_article(20), inputs()["s20"][:100]
        p3 = R.simulate(f, x, seed="pass3")
        self.assertGreater(float(np.max(np.abs(p3 - R.simulate(f, x, seed="zero")))), 1e-3)
        self.assertGreater(float(np.max(np.abs(p3 - R.simulate(f, x, seed="price")))), 1e-6)


class TestComplementModel(unittest.TestCase):
    def test_07_one_minus_as_one_filter(self):
        """num = den - f.num (b). Analytic equality of H = 1 - f(H)."""
        for p in (20, 48):
            hp = R.hp_code(p, k=math.sqrt(2.0) / 2.0)
            one = R.one_minus_filter(hp)
            d = [1.0, -hp.a[0], -hp.a[1]]
            self.assertEqual(one.b, tuple(di - bi for di, bi in zip(d, hp.b)))
            self.assertEqual(one.a, hp.a)
            for t in (5, 20, 40, 100):
                h = R._hz(hp, 2 * math.pi / t)
                self.assertAlmostEqual(abs(R._hz(one, 2 * math.pi / t) - (1 - h)), 0.0, delta=1e-14)

    def test_08_simulation_equals_x_minus_f_x_and_the_price_seeded_single_filter(self):
        hp = R.hp_code(20, k=math.sqrt(2.0) / 2.0)
        for k, x in inputs().items():
            comp = R.simulate_any(R.one_minus(hp, "zero"), x)
            self.assertTrue(np.array_equal(comp, x - R.simulate(hp, x, seed="zero")), k)
            single = R.simulate(R.one_minus_filter(hp), x, seed="price")       # y history x[0] = x[0] - 0
            self.assertLessEqual(float(np.max(np.abs(comp - single))), 1e-13, k)

    def test_09_complement_of_the_wrong_highpass_differs_from_the_article(self):
        """NCX: x - HP-A (V.32:1) is not the article's US (V.42:04 $HighPass): gain / phase differ by ~0.2 / 0.13."""
        x = R.as_filter(R.IMP_MODELS["us_nx(20)"]())
        art = R.us_article(20)
        self.assertGreater(max(abs(R.gain_at(x, t) - R.gain_at(art, t)) for t in TS), 0.2)
        self.assertGreater(max(abs(R.phase_at(x, t) - R.phase_at(art, t)) for t in TS), 0.13)
        self.assertAlmostEqual(R.dc_gain(x), 1.0, delta=1e-14)               # the complement keeps DC gain 1 and lag 0
        self.assertAlmostEqual(R.ramp_lag(x), 0.0, delta=1e-12)

    def test_10_seeded_wrapper_and_as_filter(self):
        f = R.us_code(20)
        s = R.Seeded(f, "pass4")
        x = inputs()["s20"][:300]
        self.assertTrue(np.array_equal(R.simulate_any(s, x, seed="pass3"), R.simulate(f, x, seed="pass4")))   # own seed wins
        self.assertIs(R.as_filter(s), f)
        self.assertIs(R.as_filter(f), f)
        self.assertIsNone(R.as_filter(R.Cascade(stages=())))


class TestUltimateSmootherModels(unittest.TestCase):
    def test_11_finding_1_dc_gain_is_one_for_any_c1(self):
        for p in (10, 14, 20, 30):
            self.assertAlmostEqual(R.dc_gain(R.us_article(p)), 1.0, delta=1e-15)
        for div in (3.0, 4.0, 4.01, 5.0):                                       # "any c1": other divisors keep DC gain 1
            self.assertAlmostEqual(R.dc_gain(R.us_code(20, c1_div=div)), 1.0, delta=1e-15)

    def test_12_finding_2_nyquist_zero(self):
        for p in (10, 14, 20, 30):
            self.assertLessEqual(abs(R._hz(R.us_article(p), math.pi)), 1e-16 * 1.5)
            a1 = math.exp(-math.sqrt(2.0) * math.pi / p)
            c2, c3 = 2 * a1 * math.cos(math.sqrt(2.0) * math.pi / p), -a1 * a1
            c1 = (1 + c2 - c3) / 4
            self.assertAlmostEqual(1 - 4 * c1 + c2 - c3, 0.0, delta=1e-15)      # numerator at z = -1
        self.assertGreater(abs(R._hz(R.us_code(20, c1_div=4.01), math.pi)), 1e-4)   # NCB moves it: the guard can fire

    def test_13_finding_3_ramp_lag_is_zero_for_every_control(self):
        for model in ("us_code(10, pass3)", "us_code(20, pass3, c1_div=4.01)", "us_nca(20, pass3)", "us_code(20, pass3, deg)",
                      "us_nx(20)", "us_printed(20, pass3)", "us_code(21, pass3)"):
            f = R.as_filter(R.IMP_MODELS[model]())
            self.assertAlmostEqual(R.dc_gain(f), 1.0, delta=1e-12, msg=model)
            self.assertAlmostEqual(R.ramp_lag(f), 0.0, delta=1e-10, msg=model)
        # simulation agrees (steady state of a ramp): x - y = 0
        x = inputs()["ramp"]
        y = R.simulate(R.us_article(20), x, seed="pass3")
        self.assertLessEqual(float(np.max(np.abs(x[-100:] - y[-100:]))), 1e-12)

    def test_14_finding_4_article_table_p20(self):
        chat = {5: (0.3111895913971734, -1.4085322832040272), 10: (0.7061322838536961, -1.1651717789452474),
                20: (1.2180269670507957, -0.6194039409919978), 40: (1.1873768956922401, -0.1414708831480580),
                100: (1.0383782872038971, -0.010965416173332418)}
        f = R.us_article(20)
        worst = max(max(abs(R.gain_at(f, t) - g), abs(R.phase_at(f, t) - ph)) for t, (g, ph) in chat.items())
        print("\n  P=20 table vs planning chat: max |diff| %.3e" % worst)
        self.assertLessEqual(worst, 1e-12)
        self.assertGreater(abs(R.gain_at(R.us_article(21), 20) - chat[20][0]), 1e-2)       # guard fires (NC1)

    def test_15_finding_5_passband_overshoot(self):
        for p in (10, 14, 20, 30):
            f = R.us_article(p)
            Ts = np.arange(4, 400.0001, 0.05)
            g = np.array([R.gain_at(f, t) for t in Ts])
            self.assertTrue(1.25 < g.max() < 1.28, p)
            self.assertTrue(0.61 < -R.phase_at(f, p) < 0.64, p)
        self.assertAlmostEqual(-R.phase_at(R.us_article(20), 20) * 20 / (2 * math.pi), 1.97, delta=0.01)

    def test_16_finding_6_floor_is_the_pi_gap(self):
        gm = pm = 0.0
        for p in (10, 14, 20, 30):
            for t in TS:
                gm = max(gm, abs(R.gain_at(R.us_article(p), t) - R.gain_at(R.us_code(p), t)))
                pm = max(pm, abs(R.phase_at(R.us_article(p), t) - R.phase_at(R.us_code(p), t)))
        print("\n  analytic Zorro-PI floor: gain %.3e phase %.3e" % (gm, pm))
        self.assertLessEqual(gm, 6.6e-7)
        self.assertLessEqual(pm, 7.7e-7)
        self.assertLessEqual(gm * 10, 3e-5)
        self.assertLessEqual(pm * 10, 3e-5)
        self.assertGreater(gm, 1e-7)                                             # the gap is real, not zero

    def test_17_us_code_equals_us_article_with_exact_pi(self):
        a, c = R.us_article(20), R.us_code(20, pi_value=math.pi)
        self.assertEqual(a.b, c.b)
        self.assertEqual(a.a, c.a)

    def test_18_nca_and_printed_models(self):
        art = R.us_article(20)
        self.assertGreater(max(abs(R.gain_at(R.us_nca(20), t) - R.gain_at(art, t)) for t in TS), 2e-3)
        pr = max(abs(R.gain_at(R.us_printed(20), t) - R.gain_at(art, t)) for t in TS)
        self.assertAlmostEqual(pr, 1.072e-4, delta=1e-7)                         # planning chat (Zorro PI in the cosine)
        pp = max(abs(R.phase_at(R.us_printed(20), t) - R.phase_at(art, t)) for t in TS)
        self.assertAlmostEqual(pp, 1.430e-4, delta=1e-7)


class TestRegistry(unittest.TestCase):
    def test_19_article_model(self):
        self.assertEqual(R.article_model("us_article(20)"), R.us_article(20))
        for bad in ("us_article(0)", "us_article()", "us_article(20,10)", "us_article(x)", "us_code(20)", None, 20):
            self.assertIsNone(R.article_model(bad), bad)
        self.assertEqual(R.article_model("hp_article(48)"), R.hp_article(48))                # the old forms still resolve

    def test_20_imp_models_resolve_and_carry_their_seed(self):
        names = ["us_code(%d, pass3)" % p for p in (10, 14, 20, 30)] + [
            "us_code(21, pass3)", "us_code(20, pass4)", "us_code(20, pass3, c1_div=4.01)", "us_code(20, pass3, deg)",
            "us_nca(20, pass3)", "us_printed(20, pass3)", "us_nx(20)"]
        x = inputs()["s20"][:200]
        for n in names:
            m = R.IMP_MODELS[n]()
            self.assertIsInstance(m, (R.Seeded, R.Complement), n)
            self.assertTrue(np.all(np.isfinite(R.simulate_any(m, x))), n)
        # the NCS model is the pass4 seed of the P20 filter; replaying it as pass3 must differ on s20 (must_fail fires)
        d = np.max(np.abs(R.simulate_any(R.IMP_MODELS["us_code(20, pass4)"](), x) - R.simulate_any(R.IMP_MODELS["us_code(20, pass3)"](), x)))
        self.assertGreater(float(d), 1e-4)


if __name__ == "__main__":
    unittest.main()
