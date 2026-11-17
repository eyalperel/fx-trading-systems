"""Tests for the RFF reference additions (RFF stage 1): cascade, simulate_cascade, simulate_any, roof_article, roof_code
(+ control hooks), roof_nco, the ss2_code hooks, the article_model grammar and the IMP registry entries.

Rule (CLAUDE.md 4.4): each guard / check is seen to fire on a deliberately broken input.
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

N = 3000
LEVEL, AMP, SLOPE = 1.1, 0.01, 1e-4
TS = (5, 10, 20, 40, 100)


def make_x():
    n = np.arange(N, dtype=float)
    x = {"flat": np.full(N, LEVEL)}
    for t in TS:
        x["s%d" % t] = LEVEL + AMP * np.sin(2 * math.pi * n / t)
    x["alt"] = LEVEL + AMP * (1.0 - 2.0 * (n % 2))
    x["ramp"] = LEVEL + SLOPE * n
    return x


X = make_x()
SQ = math.sqrt(2.0) / 2.0


class TestCascade(unittest.TestCase):
    def test_01_transfer_function_is_the_product(self):
        """H_cascade(w) = H_f(w) * H_g(w): gain multiplies, phase adds, at several periods (hp_article, ss2_article)."""
        f, g = R.hp_article(48), R.ss2_article(10)
        c = R.cascade(f, g)
        for t in (2, 5, 10, 20, 40, 100):
            # (b) 1e-12, not 1e-14: the expanded polynomial product rounds differently from the product of the two
            # evaluations (measured 2.1e-14 at T = 40)
            self.assertAlmostEqual(R.gain_at(c, t), R.gain_at(f, t) * R.gain_at(g, t), delta=1e-12)
        for t in (5, 10, 20, 40, 100):
            d = R.phase_at(c, t) - R.phase_at(f, t) - R.phase_at(g, t)
            self.assertLess(abs((d + math.pi) % (2 * math.pi) - math.pi), 1e-12)

    def test_02_tap_counts_and_known_values(self):
        """3-tap numerator x 2-tap numerator = 4 taps; denominators (a1 a2) x (a1 a2) = 4 feedback taps. Known answer:
        the planning-chat gain at T = 20 for (48, 10) is 0.89001654952194 (b, reference.roof_article)."""
        c = R.roof_article(48, 10)
        self.assertEqual((len(c.b), len(c.a)), (4, 4))
        self.assertAlmostEqual(R.gain_at(c, 20), 0.8900165495219456, delta=1e-12)
        self.assertAlmostEqual(R.phase_at(c, 20), -0.05338683922280491, delta=1e-12)
        self.assertLess(R.gain_at(c, 2), 1e-15)                       # gain at Nyquist is a numerical zero

    def test_03_cascade_simulation_matches_stage_by_stage_zero_seeds(self):
        """One cascaded Filter run with seed 'zero' == the stages run one after the other, both zero-seeded (the same
        system started at rest): <= 1e-14 on every input."""
        f, g = R.hp_article(48), R.ss2_article(10)
        for i, x in X.items():
            a = R.simulate(R.cascade(f, g), x, seed="zero")
            b = R.simulate_cascade([(f, "zero"), (g, "zero")], x)
            self.assertLessEqual(float(np.max(np.abs(a - b))), 1e-14, i)

    def test_04_guard_fires_wrong_order_of_taps(self):
        """The product is not symmetric in the SIGN of a feedback tap: a cascade built with a flipped sign differs."""
        f, g = R.hp_article(48), R.ss2_article(10)
        bad = R.Filter(b=R.cascade(f, g).b, a=tuple(-v for v in R.cascade(f, g).a))
        self.assertGreater(abs(R.gain_at(bad, 20) - R.gain_at(R.cascade(f, g), 20)), 1e-3)


class TestSimulateCascade(unittest.TestCase):
    def test_05_corrected_code_equals_cascade_of_stages_all_inputs(self):
        """Decision: for the corrected code, simulate_cascade([(hp_code, zero), (ss2_code, price)]) equals
        simulate(roof_code, x, seed='zero') to <= 1e-14 on all 8 inputs, for the four real parameter pairs."""
        worst = 0.0
        for hp, ss in ((48, 10), (30, 10), (125, 10), (48, 20)):
            casc = [(R.hp_code(hp, k=SQ), "zero"), (R.ss2_code(ss), "price")]
            for i, x in X.items():
                d = float(np.max(np.abs(R.simulate_cascade(casc, x) - R.simulate(R.roof_code(hp, ss), x, seed="zero"))))
                worst = max(worst, d)
                self.assertLessEqual(d, 1e-14, "%s %s" % ((hp, ss), i))
        print("\n  [cascade] corrected code: largest |stage cascade - single filter| over 4 pairs x 8 inputs = %.3e" % worst)

    def test_06_guard_fires_price_seed_on_hp_stage(self):
        """With the HP stage price-seeded (the old HighPassFilter.c) the cascade is NOT the zero-seed single filter:
        start-up differs by ~1 (the seed transient). The equality above is therefore a real condition."""
        casc = [(R.hp_code(48, k=SQ), "price"), (R.ss2_code(10), "price")]
        d = float(np.max(np.abs(R.simulate_cascade(casc, X["flat"]) - R.simulate(R.roof_code(48, 10), X["flat"], seed="zero"))))
        print("\n  [fire] HP price seed vs zero seed, flat input: %.3e" % d)
        self.assertGreater(d, 1.0)

    def test_07_stages_use_their_own_seed(self):
        """A single stage 'price' is simulate(seed=price), 'zero' is simulate(seed=zero)."""
        f = R.ss2_code(10)
        for seed in ("price", "zero"):
            a = R.simulate_cascade([(f, seed)], X["s20"])
            b = R.simulate(f, X["s20"], seed=seed)
            self.assertTrue(np.array_equal(a, b), seed)

    def test_08_simulate_any_dispatch(self):
        f = R.roof_code(48, 10)
        self.assertTrue(np.array_equal(R.simulate_any(f, X["s20"], seed="zero"), R.simulate(f, X["s20"], seed="zero")))
        nco = R.roof_nco(48, 10)
        self.assertIsInstance(nco, R.Cascade)
        self.assertTrue(np.array_equal(R.simulate_any(nco, X["s20"], seed="zero"),     # seed argument is ignored
                                       R.simulate_cascade(nco.stages, X["s20"])))
        self.assertTrue(np.array_equal(R.simulate_any(nco, X["s20"], seed="price"),
                                       R.simulate_any(nco, X["s20"], seed="zero")))


class TestRoofModels(unittest.TestCase):
    def test_09_roof_code_vs_article_is_the_pi_gap_only(self):
        """Planning-chat finding 5: code vs article, P = (48,10),(48,20),(30,10),(125,10): gain <= 5.6e-7, phase <= 1.6e-6."""
        g = ph = 0.0
        for hp, ss in ((48, 10), (48, 20), (30, 10), (125, 10)):
            a, c = R.roof_article(hp, ss), R.roof_code(hp, ss)
            for t in TS:
                g = max(g, abs(R.gain_at(c, t) - R.gain_at(a, t)))
                ph = max(ph, abs((R.phase_at(c, t) - R.phase_at(a, t) + math.pi) % (2 * math.pi) - math.pi))
        print("\n  [floor] analytic code-vs-article: gain %.3e phase %.3e" % (g, ph))
        self.assertLessEqual(g, 5.6e-7)
        self.assertLessEqual(ph, 1.6e-6)
        self.assertGreater(g, 1e-8)           # it is not accidentally the identical filter

    def test_10_default_hooks_leave_ss2_code_unchanged(self):
        """ss2_code with the new keyword defaults equals the pre-stage-1 formula (H1 EXPECT-table model)."""
        for p in (10, 14, 20, 30):
            f = R.ss2_code(p)
            root2 = math.sqrt(2.0)
            c1 = math.exp(-root2 * R.PI_ZORRO / p)
            b1 = 2.0 * c1 * math.cos(root2 * R.PI_ZORRO / p)
            self.assertEqual(f, R.Filter(b=((1.0 - b1 + c1 * c1) / 2.0,) * 2, a=(b1, -c1 * c1)))

    def test_11_hooks_change_what_they_claim(self):
        base = R.roof_code(48, 10)
        self.assertNotEqual(R.roof_code(48, 10, ss_c1_bump=1), base)
        self.assertNotEqual(R.roof_code(48, 10, ss_in_bump=1), base)
        self.assertNotEqual(R.roof_code(48, 10, ss_deg=True), base)
        # NCU: input weight 2*c0 on hp[0] only: one numerator tap in the SS stage, DC gain still 1
        u = R.ss2_code(10, unaveraged=True)
        self.assertEqual(len(u.b), 1)
        self.assertAlmostEqual(R.dc_gain(u), 1.0, delta=1e-12)
        self.assertAlmostEqual(R.dc_gain(R.ss2_code(10, in_bump=1)), 1.0, delta=1e-12 + 0.01)   # NCB moves it a little
        self.assertGreater(abs(R.dc_gain(R.ss2_code(10, in_bump=1)) - 1.0), 1e-3)                # ... and it is visible
        # NCU Nyquist gain is far from 0 (the averaged form has an exact zero there)
        self.assertGreater(R.gain_at(u, 2), 0.05)
        self.assertLess(R.gain_at(R.ss2_code(10), 2), 1e-12)
        # NC2: the cosine argument in degrees really is the degrees value
        d = R.ss2_code(10, deg=True)
        c1 = math.exp(-math.sqrt(2.0) * R.PI_ZORRO / 10)
        self.assertAlmostEqual(d.a[0], 2.0 * c1 * math.cos(math.sqrt(2.0) * 180.0 / 10), delta=1e-15)

    def test_12_roof_nco_is_the_old_pipeline(self):
        """NCO = old HP (folded literal theta, price seed) then SS (price seed). Its steady state is the old-code gain
        (0.8900377... at T = 20 from the folded theta), its start-up differs from the corrected pipeline by the seed."""
        nco = R.roof_nco(48, 10)
        (f_hp, s_hp), (f_ss, s_ss) = nco.stages
        self.assertEqual((s_hp, s_ss), ("price", "price"))
        self.assertEqual(f_hp, R.hp_code(48, theta_const=R.ZORRO_FOLD_0707x2xPI))
        old = R.cascade(f_hp, f_ss)
        self.assertAlmostEqual(R.gain_at(old, 20), 0.8900377248747544, delta=1e-12)
        y = R.simulate_any(nco, X["flat"])
        z = R.simulate(R.roof_code(48, 10), X["flat"], seed="zero")
        self.assertGreater(float(np.max(np.abs(y[:500] - z[:500]))), 1.0)           # the seed transient
        self.assertLess(float(np.max(np.abs(y[500:] - z[500:]))), 1e-9)             # gone by n = 500 on a flat input


class TestArticleModelGrammar(unittest.TestCase):
    def test_13_roof_article_resolves(self):
        self.assertEqual(R.article_model("roof_article(48,10)"), R.roof_article(48, 10))
        self.assertEqual(R.article_model("roof_article(125, 10)"), R.roof_article(125, 10))
        self.assertEqual(R.article_model("hp_article(48)"), R.hp_article(48))          # old grammar unchanged

    def test_14_guard_fires_on_everything_else(self):
        for bad in ("roof_article(0,10)", "roof_article(48,0)", "roof_article(48)", "roof_article(48,10); x",
                    "roof_article(48,10,3)", "__import__('os')", "roof_article(48.5,10)", "roof_article(-1,10)",
                    "hp_article(0)", "", None, 7):
            self.assertIsNone(R.article_model(bad), repr(bad))


class TestImpRegistry(unittest.TestCase):
    NAMES = ("roof_code(48, 10)", "roof_code(30, 10)", "roof_code(125, 10)", "roof_code(48, 20)",
             "roof_code(48, 10, ss_c1_bump=1)", "roof_code(48, 10, ss_in_bump=1)", "roof_code(48, 10, ss_unaveraged)",
             "roof_code(48, 10, ss_deg)", "roof_code(49, 10)", "roof_code(48, 11)", "roof_nco(48, 10)")

    def test_15_entries_exist_and_build(self):
        for nme in self.NAMES:
            self.assertIn(nme, R.IMP_MODELS, nme)
            self.assertIsNotNone(R.IMP_MODELS[nme]())
        self.assertEqual(R.IMP_MODELS["roof_code(48, 10)"](), R.roof_code(48, 10))
        self.assertEqual(R.IMP_MODELS["roof_code(125, 10)"](), R.roof_code(125, 10))     # lambda default args bound right
        self.assertEqual(R.IMP_MODELS["roof_code(48, 20)"](), R.roof_code(48, 20))
        self.assertIsInstance(R.IMP_MODELS["roof_nco(48, 10)"](), R.Cascade)

    def test_16_entries_are_distinct_systems(self):
        """Fire: no two registry entries are the same filter (a copy-paste in the registry would show here)."""
        filt = [R.IMP_MODELS[nme]() for nme in self.NAMES if "nco" not in nme]
        for i in range(len(filt)):
            for j in range(i + 1, len(filt)):
                self.assertNotEqual(filt[i], filt[j], (self.NAMES[i], self.NAMES[j]))


if __name__ == "__main__":
    unittest.main()
