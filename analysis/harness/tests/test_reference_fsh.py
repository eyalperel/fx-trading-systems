"""FSH stage 1: reference models of the Fisher Transform (reference.fisher_article / fisher_superseded) against the planning chat's
independent model (docs/harness/FISHER_REVIEW_MODEL.py) and the brief's (b) numbers (docs/harness/FISHER_STAGE1_PROMPT.md, findings 1-8
and the control effects). The brief's numbers are typed in here from the brief; every comparison has a numeric tolerance.
No Zorro run, no .c file read. Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fsh_support as S      # noqa: E402

R = S.R
N, W = 3000, 700
LEVEL, AMP, SLOPE = 11 / 10, 1 / 100, 1 / 10000
TS = (5, 10, 20, 40, 100)
n = np.arange(N, dtype=float)


def sine(t, lvl=LEVEL, amp=AMP):
    return lvl + amp * np.sin(2 * math.pi * n / t)


X = {"flat": np.full(N, LEVEL), "ramp": LEVEL + SLOPE * n, "rampdn": LEVEL - SLOPE * n}
for _t in TS:
    X["s%d" % _t] = sine(_t)
M = {L: R.fisher_article(L) for L in (10, 20)}
SIM = {(L, k): R.simulate_fisher(M[L], X[k]) for L in (10, 20) for k in X}

# the brief's (b) numbers, typed in from docs/harness/FISHER_STAGE1_PROMPT.md
BRIEF_RANGE = {10: (1.9021130325901803, 1.902113032590269, 0.9999999999998677, 0.2928932188134059, 0.048943483704833035),
               20: (1.9021130325902247, 1.9021130325902913, 2.0000000000000018, 0.9999999999999343, 0.1909830056250339)}
BRIEF_CLAMP = {10: (0.6608611703239821, 0.4309496019031033, 0.08902642427836405, 0.0016393018220295374, 0.0011989375189954687),
               20: (0.6608611703239828, 0.4309496019031033, 0.20473557299332135, 0.0017189627979685707, 0.0007121303005288571)}
BRIEF_INV = {10: (2.6565416533230746e-12, 5.31930055558405e-12), 20: (5.32018873400375e-13, 1.0578204978628492e-12)}
BRIEF_EFFECT = {   # (Fish, v1, raw) at T = 5, 10, 20, 40, 100, max |diff| rows >= W vs the FR10 model (printed with 7 significant digits)
    "NCW": ((1.147197e-03, 3.620501e-03, 2.325973e-02, 1.300183e+00, 1.304496e+00),
            (9.973904e-04, 1.694092e-03, 2.730223e-03, 1.063930e-02, 1.075769e-02), (0, 0, 0, 0, 0)),
    "NCC": ((0, 0, 0, 2.162821e+00, 2.307098e+00), (0, 0, 0, 9.0e-03, 9.0e-03), (0, 0, 0, 0, 0)),
    "NCK": ((1.764535e-01, 4.717597e-01, 1.307064e+00, 3.710631e+00, 3.800201e+00), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0)),
    "NCL": ((8.232304e-14, 5.173639e-14, 1.959533e-01, 3.303457e-01, 1.210467e+00),
            (6.700196e-14, 3.086420e-14, 1.344059e-01, 1.594356e-01, 1.663479e-01),
            (2.101652e-13, 9.348078e-14, 3.262379e-01, 3.774946e-01, 3.890338e-01)),
    "NC32": ((1.395721e-08, 5.860322e-08, 5.316101e-07, 1.242011e-05, 1.288113e-05),
             (1.253569e-08, 2.932536e-08, 6.981766e-08, 8.570537e-08, 8.566314e-08), (0, 0, 0, 0, 0)),
}
BRIEF_NCB_FISH = (7.980366e-02, 3.066436e-01, 9.611960e-01, 2.628208e+00, 2.709052e+00)
CTL = {"NCW": R.fisher_article(10, a=(331, 1000)), "NCC": R.fisher_article(10, cl=(99, 100)), "NCK": R.fisher_article(10, k=(1, 4)),
       "NCL": R.fisher_article(11), "NC32": R.fisher_article(10, literals="float32"),
       "NCB": R.fisher_article(10, a=(1, 2), b=(1, 2), thr=(9999, 10000), cl=(9999, 10000), k=(1, 4))}


def printed_close(a, e):
    """|a - e| within half a unit of the 7th significant digit of the printed value e (0 printed as 0 -> a must be 0)."""
    if e == 0:
        return a == 0.0
    return abs(a - e) <= 0.5 * 10 ** (math.floor(math.log10(abs(e))) - 6) * 1.0000001


class TestAgainstReviewModel(unittest.TestCase):
    def test_01_fisher_article_equals_the_independent_model_on_every_row(self):
        rm = S.review_model()
        worst = 0.0
        for L in (10, 20):
            for k, x in X.items():
                ref = rm.run(list(x), L, rm.SRC_A)
                o = SIM[(L, k)]
                for f, g in (("raw", "raw"), ("pre", "pre"), ("v1", "v"), ("out", "f"), ("trig", "trig"), ("rng", "rng")):
                    worst = max(worst, float(np.max(np.abs(getattr(o, f) - np.array([r[g] for r in ref])))))
        print("\n  fisher_article vs FISHER_REVIEW_MODEL, every row, 8 inputs x 2 L: max |diff| %r" % worst)
        self.assertLessEqual(worst, 1e-15)

    def test_02_float32_variant_equals_the_review_models_CODE_literals(self):
        rm = S.review_model()
        o = R.simulate_fisher(R.fisher_article(10, literals="float32"), X["s40"])
        ref = rm.run(list(X["s40"]), 10, rm.CODE)
        self.assertLessEqual(float(np.max(np.abs(o.out - np.array([r["f"] for r in ref])))), 1e-15)
        self.assertEqual(R.fisher_article(10, literals="float32")[1:5], tuple(R.f32(v) for v in (.33, .67, .99, .999)))


class TestFindings(unittest.TestCase):
    def test_1_exact_bounds(self):
        self.assertEqual(R.FISHER_LN1999, 7.6004023345004)
        for L in (10, 20):
            allo = [SIM[(L, k)] for k in X]
            self.assertEqual(min(float(np.min(o.raw)) for o in allo), -1.0)
            self.assertEqual(max(float(np.max(o.raw)) for o in allo), 1.0)
            self.assertLessEqual(max(float(np.max(np.abs(o.v1))) for o in allo), 0.999)
            self.assertEqual(sum(int(np.sum((np.abs(o.v1) > .99) & (np.abs(o.v1) < .999))) for o in allo), 0)   # no value in (.99, .999)
            self.assertLessEqual(max(float(np.max(np.abs(o.out))) for o in allo), math.log(1999))
        self.assertEqual(float(np.max(np.abs(SIM[(10, "s100")].out[W:]))), 7.6004023343329665)       # brief, FR10 T100
        self.assertEqual(float(np.max(np.abs(SIM[(20, "s100")].out[W:]))), 7.60040233312112)         # brief, FR20 T100
        self.assertEqual(math.atanh(.999) - math.atanh(.99), 1.1535487548879537)

    def test_2_gate_margins(self):
        worst = 0.0
        for L in (10, 20):
            for t, er, ec in zip(TS, BRIEF_RANGE[L], BRIEF_CLAMP[L]):
                o = SIM[(L, "s%d" % t)]
                worst = max(worst, abs(float(np.min(o.rng[W:])) / AMP - er), abs(float(np.min(o.cdist[W:])) - ec))
        print("\n  gate margins vs brief (20 values): max |diff| %r" % worst)
        self.assertLessEqual(worst, 1e-12)

    def test_3_fish_range(self):
        o = SIM
        for L, t, lo, hi in ((10, 10, -0.943519, 0.943519), (10, 20, -2.614129, 2.614129), (10, 40, -7.421263, 7.421263),
                             (10, 5, -0.333957, 0.352907)):
            self.assertAlmostEqual(float(np.min(o[(L, "s%d" % t)].out[W:])), lo, places=6)
            self.assertAlmostEqual(float(np.max(o[(L, "s%d" % t)].out[W:])), hi, places=6)

    def test_4_ramps(self):
        for L in (10, 20):
            for k, sg in (("ramp", 1.0), ("rampdn", -1.0)):
                o = SIM[(L, k)]
                self.assertEqual(o.raw[0], 0.0)                                   # row 0: rng = 0, the guard
                self.assertTrue(np.all(o.raw[1:] == sg))                          # raw = +-1 exactly from row 1
                self.assertEqual(max(i for i in range(N) if o.v1[i] != sg * .999) + 1, 12)
                self.assertEqual(max(i for i in range(N) if abs(o.out[i] - sg * math.log(1999)) > 1e-12) + 1, 53)
                self.assertEqual(float(np.max(np.abs(o.out[W:] - sg * math.log(1999)))), 0.0)    # EXACTLY ln(1999) in float64
        print("\n  ramps (L10 and L20): raw +-1 from row 1, v1 +-.999 from row 12, out within 1e-12 of +-ln(1999) from row 53, "
              "exactly +-ln(1999) on rows >= W")

    def test_5_flat(self):
        for L in (10, 20):
            o = SIM[(L, "flat")]
            self.assertEqual(int(np.sum(o.rng == 0)), N)
            self.assertTrue(np.all(o.raw == 0) and np.all(o.v1 == 0) and np.all(o.out == 0))

    def test_6_invariance(self):
        for L in (10, 20):
            for j, (lv, am) in enumerate(((11 / 10, 1 / 10), (22 / 10, 1 / 100))):
                d = max(float(np.max(np.abs(SIM[(L, "s%d" % t)].out[W:] - R.simulate_fisher(M[L], sine(t, lv, am)).out[W:]))) for t in TS)
                self.assertLessEqual(abs(d - BRIEF_INV[L][j]), 1e-12, (L, j, d))       # brief: report any difference > 1e-12

    def test_7_memory(self):
        self.assertEqual(math.ceil(math.log(1e-12) / math.log(.67)), 69)
        self.assertEqual(math.ceil(math.log(1e-12) / math.log(.5)), 40)

    def test_8_control_effects_and_ncb(self):
        bad = []
        for c, (ef, ev, er) in BRIEF_EFFECT.items():
            for t, e3 in zip(TS, zip(ef, ev, er)):
                o, r = R.simulate_fisher(CTL[c], X["s%d" % t]), SIM[(10, "s%d" % t)]
                for q, e in zip(("out", "v1", "raw"), e3):
                    a = float(np.max(np.abs(getattr(o, q)[W:] - getattr(r, q)[W:])))
                    if not printed_close(a, e):
                        bad.append((c, t, q, a, e))
        for t, e in zip(TS, BRIEF_NCB_FISH):
            a = float(np.max(np.abs(R.simulate_fisher(CTL["NCB"], X["s%d" % t]).out[W:] - SIM[(10, "s%d" % t)].out[W:])))
            if not printed_close(a, e):
                bad.append(("NCB", t, "out", a, e))
        self.assertEqual(bad, [])
        self.assertEqual(float(R.simulate_fisher(CTL["NCC"], X["ramp"]).out[-1]), 5.2933048247244905)
        self.assertEqual(float(R.simulate_fisher(CTL["NCK"], X["ramp"]).out[-1]), 3.8002011672502)
        self.assertEqual(float(R.simulate_fisher(CTL["NCC"], X["ramp"]).v1[-1]), 0.99)
        self.assertEqual(float(R.simulate_fisher(CTL["NCW"], X["ramp"]).v1[-1]), 0.999)


class TestSuperseded(unittest.TestCase):
    def test_01_one_slot_equals_the_float32_per_instance_model(self):
        for k in ("s20", "ramp", "flat"):
            a = R.simulate_fisher_shared([10], [X[k]])[0]
            b = R.simulate_fisher(R.fisher_article(10, literals="float32"), X[k])
            for f in R.FisherOut._fields:
                self.assertTrue(np.array_equal(getattr(a, f), getattr(b, f)), (k, f))

    def test_02_shared_statics_two_instances_planning_chat_values(self):
        got = []
        for t, e in ((20, 0.707983), (40, 2.692527), (100, 2.695127)):
            s = R.simulate_fisher_shared([10, 20], [X["s%d" % t]] * 2)
            own = R.simulate_fisher(R.fisher_article(10, literals="float32"), X["s%d" % t])
            got.append(float(np.max(np.abs(s[0].out[200:] - own.out[200:]))))
            self.assertAlmostEqual(got[-1], e, places=6)
        print("\n  shared statics (L10, L20 on one sine), rows >= 200: %s (brief 0.707983 / 2.692527 / 2.695127)" % got)

    def test_03_the_state_is_chained_through_every_call_in_order(self):
        xs = [X["s5"], X["s100"]]
        a = R.simulate_fisher_shared([10, 10], xs)
        b = R.simulate_fisher_shared([10, 10], xs[::-1])
        self.assertGreater(float(np.max(np.abs(a[0].out - b[1].out))), 0.1)        # call order changes the result
        for t in range(1, 50):                                                     # trig = the shared Fish left by the PREVIOUS call
            self.assertEqual(a[0].trig[t], a[1].out[t - 1])
            self.assertEqual(a[1].trig[t], a[0].out[t])
        self.assertEqual(a[0].trig[0], 0.0)

    def test_04_handles_and_registry(self):
        self.assertEqual(R.fisher_superseded((10, 10), 1), R.FisherShared((10, 10), 1))
        for name in ("fisher_article(10)", "fisher_article(20)", "fisher_article(11)", "fisher_article(10,a=331/1000)",
                     "fisher_article(10,cl=99/100)", "fisher_article(10,k=1/4)", "fisher_article(10,literals=float32)",
                     "fisher_article(10,a=1/2,b=1/2,thr=9999/10000,cl=9999/10000,k=1/4)",
                     "fisher_superseded(10,10)[0]", "fisher_superseded(10,10)[1]"):
            self.assertIn(name, R.IMP_MODELS)
            R.IMP_MODELS[name]()


class TestModelHooks(unittest.TestCase):
    def test_01_refusals(self):
        for kw in (dict(literals="f32"), dict(a=(1, 0)), dict(a=0.33), dict(k=(1.0, 2)), dict(cl=(1, 2, 3))):
            with self.assertRaises(ValueError, msg=kw):
                R.fisher_article(10, **kw)
        for L in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                R.fisher_article(L)

    def test_02_article_grammar(self):
        self.assertEqual(R.fisher_article_model("fisher_article(10)"), R.fisher_article(10))
        self.assertEqual(R.osc_article_model("fisher_article(20)"), R.fisher_article(20))
        for bad in ("fisher_article(0)", "fisher_article(10,a=1/2)", "fisher_article( 10)", "fisher_article(1234)", None):
            self.assertIsNone(R.fisher_article_model(bad), bad)

    def test_03_exact_constants(self):
        m = R.fisher_article(10)
        self.assertEqual((m.a, m.b, m.thr, m.cl, m.k), (0.33, 0.67, 0.99, 0.999, 0.5))   # n/d = the decimal's nearest double
        self.assertNotEqual(R.f32(0.999), 0.999)
        self.assertEqual(R.f32(0.999), 0.9990000128746033)

    def test_04_window_padding(self):
        hi, lo = R.fisher_window(np.array([3.0, 1.0, 2.0, 5.0]), 3)
        self.assertEqual(hi.tolist(), [3.0, 3.0, 3.0, 5.0])                              # history padded with x[0] = 3
        self.assertEqual(lo.tolist(), [3.0, 1.0, 1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
