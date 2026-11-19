"""MST stage 1: reference models for MESAStochastic (reference.mesa_article / mesa_code / mesa_superseded / simulate_mesa).

1. simulate_mesa equals an INDEPENDENT bar-by-bar translation of the EasyLanguage sidebar (own coefficients, own loops, the library
   conventions M-4 / M-5 / M-6), and the guard fires on broken translations.
2. The Roof stage equals the RFF model (stage-by-stage simulate_cascade, as RoofingFilter.c runs it) to <= 1e-12.
3. Findings 1-8 of docs/harness/MESA_STAGE1_PROMPT.md (the planning chat's (b) numbers) are reproduced from the MODELS (not from the
   spec file) within the brief's reporting thresholds: 1e-12 for tables, 1% relative for effects; the round-off-sized values
   (<= 1.3e-13) are checked to stay below 1e-12 and printed (accepted 2026-11-19, listed in MESA_STAGE1_REPORT.md).
4. mesa_superseded: window L + 1, scale 100, fallback 50; NCL construction (Zorro PI in the degree conversion, accepted 2026-11-19);
   grammar and IMP registry.
Source (a): Ehlers, 'Predictive And Successful Indicators', TASC V.32:1 (2014), MESA Stochastic sidebar.
No .c file is read; Zorro is not run. Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mst_support as S      # noqa: E402

C, R = S.C, S.R
TS = S.TS
N, W = 3000, 700
LEVEL, AMP = 1.1, 0.01


def sine(t, level=LEVEL, amp=AMP, n=N):
    k = np.arange(n, dtype=float)
    return level + amp * np.sin(2 * math.pi * k / t)


def independent_mesa(price, L, hp, ss, pi=math.pi, win=None, scale=1.0, fallback=0.5, final_seed="first", da_final=0.0):
    """The sidebar, line by line, in degrees converted here (Cosine(x deg) = cos(x*pi/180)), exact .707 -> sqrt(2)/2,
    1.414 -> sqrt(2), 3.14159 -> pi (D1 rule 1). `pi` replaces EVERY pi (Zorro PI for the code). Library conventions:
    Close[-k] = Close[0]; HP[-k] = 0; Filt[-k] = 0 (first Roof); window history = first Filt; HH == LL -> fallback;
    final: Stoc[-1] = Stoc[0], MESA[-k] = Stoc[0] ('first') or 0 ('zero')."""
    r2 = math.sqrt(2.0)
    deg = pi / 180.0
    arg = (r2 / 2.0) * 360.0 / hp * deg
    alpha1 = (math.cos(arg) + math.sin(arg) - 1.0) / math.cos(arg)

    def ss_coef(add=0.0):
        a1 = math.exp(-r2 * pi / ss) + add
        b1 = 2.0 * a1 * math.cos(r2 * 180.0 / ss * deg)
        c2, c3 = b1, -a1 * a1
        return 1.0 - c2 - c3, c2, c3
    c1, c2, c3 = ss_coef()
    f1, f2, f3 = ss_coef(da_final)
    win = L if win is None else win
    n = len(price)
    cl = lambda i: price[i] if i >= 0 else price[0]
    HP, Filt, Stoc, M = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    for i in range(n):
        hp1 = HP[i - 1] if i >= 1 else 0.0
        hp2 = HP[i - 2] if i >= 2 else 0.0
        HP[i] = ((1 - alpha1 / 2) * (1 - alpha1 / 2) * (cl(i) - 2 * cl(i - 1) + cl(i - 2))
                 + 2 * (1 - alpha1) * hp1 - (1 - alpha1) * (1 - alpha1) * hp2)
        hpp = HP[i - 1] if i >= 1 else HP[0]
        fl1 = Filt[i - 1] if i >= 1 else 0.0
        fl2 = Filt[i - 2] if i >= 2 else 0.0
        Filt[i] = c1 * (HP[i] + hpp) / 2 + c2 * fl1 + c3 * fl2
        hh = ll = Filt[i]
        for count in range(win):
            v = Filt[i - count] if i - count >= 0 else Filt[0]
            hh, ll = max(hh, v), min(ll, v)
        Stoc[i] = scale * (Filt[i] - ll) / (hh - ll) if hh != ll else fallback
        seed = Stoc[0] if final_seed == "first" else 0.0
        s1 = Stoc[i - 1] if i >= 1 else seed
        m1 = M[i - 1] if i >= 1 else seed
        m2 = M[i - 2] if i >= 2 else seed
        M[i] = f1 * (Stoc[i] + s1) / 2 + f2 * m1 + f3 * m2
    return Filt, Stoc, M


def maxdiff(a, b, lo=0):
    return float(np.max(np.abs(np.asarray(a)[lo:] - np.asarray(b)[lo:])))


class TestIndependentTranslation(unittest.TestCase):
    CASES = ((20, 48, 10), (14, 48, 10), (20, 48, 20))

    def test_01_article_model_equals_the_sidebar(self):
        worst = 0.0
        for L, hp, ss in self.CASES:
            for t in (10, 40, 100):
                x = sine(t, n=1200)
                mo = R.simulate_mesa(R.mesa_article(L, hp, ss), x)
                f, s, m = independent_mesa(x, L, hp, ss)
                d = max(maxdiff(mo.roof, f), maxdiff(mo.stoc, s), maxdiff(mo.out, m))
                worst = max(worst, d)
                self.assertLess(d, 1e-10, (L, hp, ss, t, d))
        print("\n  simulate_mesa vs independent sidebar translation (article, 3 params x 3 sines): max |diff| %.3e" % worst)

    def test_02_code_superseded_and_seed_variants_equal_the_sidebar(self):
        x = sine(40, n=1200)
        for model, kw in ((R.mesa_code(20, 48, 10), dict(pi=R.PI_ZORRO)),
                          (R.mesa_superseded(20, 48, 10), dict(pi=R.PI_ZORRO, win=21, scale=100.0, fallback=50.0)),
                          (R.mesa_article(20, 48, 10, final_seed="zero"), dict(final_seed="zero")),
                          (R.mesa_article(20, 48, 10, win=21), dict(win=21)),
                          (R.mesa_code(20, 48, 10, da_final=1.0 / 1000), dict(pi=R.PI_ZORRO, da_final=1.0 / 1000))):
            mo = R.simulate_mesa(model, x)
            f, s, m = independent_mesa(x, 20, 48, 10, **kw)
            sc = 100.0 if model.scale == 100.0 else 1.0
            self.assertLess(max(maxdiff(mo.roof, f), maxdiff(mo.stoc, s) / sc, maxdiff(mo.out, m) / sc), 1e-10, model)

    def test_03_guard_fires_on_broken_translations(self):
        x = sine(40, n=1200)
        mo = R.simulate_mesa(R.mesa_article(20, 48, 10), x)
        for kw in (dict(win=21), dict(pi=R.PI_ZORRO), dict(final_seed="zero"), dict(da_final=1e-3), dict(fallback=0.0)):
            f, s, m = independent_mesa(x, 20, 48, 10, **kw)
            d = max(maxdiff(mo.roof, f), maxdiff(mo.stoc, s), maxdiff(mo.out, m))
            self.assertGreater(d, 1e-10, kw)
            print("\n  [fire] sidebar translation with %s: max |diff| %.3e" % (kw, d))

    def test_04_flat_input_gives_the_fallback(self):
        mo = R.simulate_mesa(R.mesa_article(20, 48, 10), np.full(500, LEVEL))
        self.assertEqual((float(np.max(np.abs(mo.roof))), float(mo.stoc.min()), float(mo.stoc.max()), float(mo.rng.max())),
                         (0.0, 0.5, 0.5, 0.0))
        self.assertLess(maxdiff(mo.out, np.full(500, 0.5)), 1e-15)


class TestRoofIsTheRffModel(unittest.TestCase):
    def test_01_roof_equals_the_stage_by_stage_rff_model(self):
        """RoofingFilter.c runs HP (history 0) then SuperSmoother2Pole seeded with its first input: simulate_cascade stages."""
        worst = 0.0
        for hp, ss in ((48, 10), (48, 20), (40, 10)):
            for x in [sine(t) for t in TS] + [np.full(N, LEVEL), LEVEL + 1e-4 * np.arange(N, dtype=float),
                                              LEVEL + AMP * (-1.0) ** np.arange(N)]:
                code = R.simulate_cascade([(R.hp_code(hp, k=math.sqrt(2.0) / 2.0), "zero"), (R.ss2_code(ss), "price")], x)
                art = R.simulate_cascade([(R.hp_article(hp), "zero"), (R.ss2_article(ss), "price")], x)
                d = max(maxdiff(R.simulate_mesa(R.mesa_code(20, hp, ss), x).roof, code),
                        maxdiff(R.simulate_mesa(R.mesa_article(20, hp, ss), x).roof, art),
                        maxdiff(R.simulate_mesa(R.mesa_code(20, hp, ss), x).roof, R.simulate(R.roof_code(hp, ss), x, seed="zero")))
                worst = max(worst, d)
        print("\n  Roof vs RFF model (3 (hp, ss) x 8 inputs, code and article): max |diff| %.3e" % worst)
        self.assertLessEqual(worst, 1e-12)

    def test_02_guard_fires_on_a_wrong_roof(self):
        x = sine(20)
        wrong = R.simulate_cascade([(R.hp_code(48, k=math.sqrt(2.0) / 2.0), "zero"), (R.ss2_code(11), "price")], x)
        self.assertGreater(maxdiff(R.simulate_mesa(R.mesa_code(20, 48, 10), x).roof, wrong), 1e-6)
        self.assertGreater(maxdiff(R.simulate_mesa(R.mesa_code(20, 48, 10), x).roof,
                                   R.simulate_mesa(R.mesa_article(20, 48, 10), x).roof), 1e-9)      # the PI gap is visible

    def test_03_mesa_roof_filter_is_roof_article(self):
        self.assertEqual(R.mesa_roof_filter(48, 10), R.roof_article(48, 10))


BRIEF_TABLES = {
    (48, 10): ([0.2232924637311758, 0.681218960159867, 0.8900165495219456, 0.7405714692715452, 0.31520956783497034],
               [-1.7262724708581954, -1.0206179300609166, -0.05338683922280491, 0.7699840012152294, 1.8340513846256814],
               6.0342470785651366e-18),
    (48, 20): ([0.05743161850487488, 0.23365848260774144, 0.6487070206488769, 0.7198621609155487, 0.3149734799160282],
               [-2.073211124216958, -1.8117540367506384, -0.8564295844658563, 0.3805302637414841, 1.6917733148668452],
               1.5107043619184777e-18)}
BRIEF_TRACE_FLOOR = {
    "L14": (3.2793504878281254e-07, 8.784203028855408e-07, 1.0646457658802788e-06, 1.7297547684202996e-06, 3.875320166324414e-06),
    "L20": (3.279350517804147e-07, 8.784203039402527e-07, 8.397692353168118e-07, 1.4513032355889521e-06, 3.2572078335624255e-06),
    "L30": (3.2793505710948523e-07, 8.784203059386542e-07, 8.397692369821463e-07, 8.660523195258563e-07, 2.4668033711261472e-06),
    "S20": (1.0819927825922449e-07, 2.4112161933764753e-07, 1.0047369309873488e-06, 1.6674523009574393e-06, 2.3008172037042307e-06)}
BRIEF_GATE = {
    "L14": (0.41939132667745976, 1.3582805947183891, 1.3727194518603654, 0.39414032769408464, 0.028396521846796308),
    "L20": (0.4193913266775104, 1.3582805947184167, 1.7774970167172783, 0.7290686557558217, 0.057985539938341026),
    "L30": (0.419391326677519, 1.3582805947184744, 1.7774970167172863, 1.2560128828930173, 0.12688319427320272),
    "S20": (0.10731137419782429, 0.45381612166435187, 1.2926137863010458, 0.6705343068945032, 0.05928624057810884)}
BRIEF_INVARIANCE = {"L14": (2.124e-13, 3.649e-13), "L20": (1.064e-13, 2.658e-13), "L30": (5.324e-14, 1.245e-13), "S20": (5.068e-14, 1.223e-13)}
BRIEF_EFFECTS = {   # vs the L20 article, rows >= 700, T = 5, 10, 20, 40, 100 (the article-form control models)
    "NCW": (7.149836278586008e-14, 1.1213252548714081e-14, 4.218847493575595e-15, 0.062068399419046405, 0.08053344297756188),
    "NCA": (0.0003776379364223148, 0.0007941933349498442, 0.00038501894107612067, 0.00032719020964688816, 0.0003437934243362452),
    "NCP": (0.00733852860393025, 0.018739743054289437, 0.05133688574154027, 0.18557033447408722, 0.4581797762979168),
    "NC1": (1.2012613126444194e-13, 2.1760371282653068e-14, 8.104628079763643e-15, 0.12681299399496013, 0.1561225037567811),
    "NCS": (63.80040995412725, 83.74023037230494, 97.33715039633475, 101.56627378951627, 101.85048633300102),
    "NCL": (6.170885774015034e-05, 0.00016529770445106173, 0.00015804592943119422, 0.00027308494704969544, 0.0006127120163363919)}
ROUNDOFF = 1e-12        # below this, a difference from the brief is round-off (accepted 2026-11-19): both values must stay below it


def article_control(vid):
    return {"NCW": R.mesa_article(20, 48, 10, win=21), "NCA": R.mesa_article(20, 48, 10, da_final=1.0 / 1000),
            "NCP": R.mesa_article(20, 40, 10), "NC1": R.mesa_article(22, 48, 10),
            "NCS": R.mesa_article(20, 48, 10, win=21, scale=100.0, fallback=50.0),
            "NCL": R.mesa_article(20, 48, 10, literals="printed")}[vid]


class TestFindings1to8(unittest.TestCase):
    """The brief's (b) numbers from the models; thresholds as the brief states them."""

    def compare(self, label, want, got, rel=1e-2):
        if abs(want) < ROUNDOFF and abs(got) < ROUNDOFF:
            if abs(got - want) > 0.01 * abs(want):
                print("\n  round-off %s: brief %.4e, model %.4e" % (label, want, got))
            return
        self.assertLess(abs(got - want) / abs(want), rel, (label, want, got))

    def test_01_roof_tables(self):
        worst = 0.0
        for (hp, ss), (g, p, alt) in BRIEF_TABLES.items():
            f = R.roof_article(hp, ss)
            for t, gv, pv in zip(TS, g, p):
                worst = max(worst, abs(R.gain_at(f, t) - gv), abs(R.phase_at(f, t) - pv))
            worst = max(worst, abs(R.gain_at(f, 2) - alt))
            self.assertLess(abs(R.ramp_residual(f, LEVEL, 1e-4)), 1e-17)                      # double zero at DC
        self.assertLess(abs(R.gain_at(R.roof_article(48, 10), 20) - 0.8900165495219391), 1e-15)       # PROJECT_STATE section 5
        print("\n  finding 1: Roof tables vs brief max |diff| %.3e (limit 1e-12)" % worst)
        self.assertLess(worst, 1e-12)

    def test_02_roof_pi_floors(self):
        for (hp, ss), (g, p) in {(48, 10): (5.278e-07, 1.328e-06), (48, 20): (4.409e-07, 1.567e-06)}.items():
            a, c = R.roof_article(hp, ss), R.roof_code(hp, ss)
            dg = max(abs(R.gain_at(a, t) - R.gain_at(c, t)) for t in TS)
            dp = max(abs(R.phase_at(a, t) - R.phase_at(c, t)) for t in TS)
            self.assertLess(abs(dg - g) / g, 1e-3)
            self.assertLess(abs(dp - p) / p, 1e-3)
            self.assertLessEqual(10 * max(dg, dp), 3e-5)

    def test_03_trace_floors_and_gate_margins(self):
        for vid, p in S.REAL.items():
            for t, fw, gw in zip(TS, BRIEF_TRACE_FLOOR[vid], BRIEF_GATE[vid]):
                a = R.simulate_mesa(R.mesa_article(*p), sine(t))
                c = R.simulate_mesa(R.mesa_code(*p), sine(t))
                self.compare("trace floor %s T%d" % (vid, t), fw, maxdiff(a.out, c.out, W), rel=1e-3)
                self.assertLess(abs(float(np.min(a.rng[W:] / AMP)) - gw), 1e-12, (vid, t))
        top = max(max(v) for v in BRIEF_TRACE_FLOOR.values())
        self.assertLessEqual(10 * top, 5e-5)                    # the spec's trace tolerance; the D6 default 3e-5 fails
        self.assertGreater(10 * top, 3e-5)

    def test_04_bound_and_unbounded_output(self):
        lo, hi = 1.0, 0.0
        for p in S.REAL.values():
            for x in [sine(t) for t in TS] + [np.full(N, LEVEL), LEVEL + 1e-4 * np.arange(N, dtype=float),
                                              LEVEL + AMP * (-1.0) ** np.arange(N)]:
                s = R.simulate_mesa(R.mesa_article(*p), x).stoc
                lo, hi = min(lo, float(s.min())), max(hi, float(s.max()))
        self.assertEqual((lo, hi), (0.0, 1.0))
        o = R.simulate_mesa(R.mesa_article(20, 48, 10), sine(100)).out[W:]
        self.assertAlmostEqual(float(o.min()), -0.0295, places=4)
        self.assertAlmostEqual(float(o.max()), 1.0295, places=4)

    def test_05_invariance(self):
        for vid, p in S.REAL.items():
            mk = mo = 0.0
            for t in TS:
                b = R.simulate_mesa(R.mesa_article(*p), sine(t)).out
                mk = max(mk, maxdiff(R.simulate_mesa(R.mesa_article(*p), sine(t, amp=0.1)).out, b, W))
                mo = max(mo, maxdiff(R.simulate_mesa(R.mesa_article(*p), sine(t, level=2.2)).out, b, W))
            self.compare("invariance scale10 %s" % vid, BRIEF_INVARIANCE[vid][0], mk)
            self.compare("invariance offset %s" % vid, BRIEF_INVARIANCE[vid][1], mo)

    def test_06_start_up_and_final_seed(self):
        a = R.simulate_mesa(R.mesa_article(20, 48, 10), sine(20))
        for got, want in zip(a.out[:4], (0.5, 0.5632987004029524, 0.6999002012721725, 0.8320600073104027)):
            self.assertLess(abs(got - want), 1e-12)
        self.assertEqual(list(a.stoc[:4]), [0.5, 1.0, 1.0, 1.0])
        for t in (5, 10, 20, 40, 100):
            d = np.abs(R.simulate_mesa(R.mesa_article(20, 48, 10), sine(t)).out
                       - R.simulate_mesa(R.mesa_article(20, 48, 10, final_seed="zero"), sine(t)).out)
            self.assertLess(abs(float(d.max()) - 0.4367012995970475), 1e-12, t)
            self.assertEqual(int(np.nonzero(d > 1e-12)[0].max()), 59, t)

    def test_07_window_and_control_effects(self):
        for vid, want in BRIEF_EFFECTS.items():
            m = article_control(vid)
            for t, w in zip(TS, want):
                b = R.simulate_mesa(R.mesa_article(20, 48, 10), sine(t)).out
                self.compare("%s T%d" % (vid, t), w, maxdiff(R.simulate_mesa(m, sine(t)).out, b, W))

    def test_08_compare_rule_fires(self):
        with self.assertRaises(AssertionError):
            self.compare("fire", 0.1, 0.102)
        with self.assertRaises(AssertionError):
            self.compare("fire", 1e-13, 2e-12)
        self.compare("fire", 1e-13, 2e-13)                       # round-off on both sides: accepted, printed


class TestSupersededAndConstruction(unittest.TestCase):
    def test_01_superseded_is_window_21_times_100(self):
        """Scale and fallback are both x100, the smoothing is linear: superseded out = 100 x (window-21 corrected model) out."""
        for t in TS:
            x = sine(t)
            sup = R.simulate_mesa(R.mesa_superseded(20, 48, 10), x)
            ncw = R.simulate_mesa(R.mesa_code(20, 48, 10, win=21), x)
            self.assertLess(maxdiff(sup.out / 100.0, ncw.out), 1e-12, t)
            self.assertLess(maxdiff(sup.stoc / 100.0, ncw.stoc), 1e-14, t)
        m = R.mesa_superseded(20, 48, 10)
        self.assertEqual((m.win, m.scale, m.fallback, m.pi_value, m.final_seed), (21, 100.0, 50.0, R.PI_ZORRO, "first"))
        flat = R.simulate_mesa(m, np.full(300, LEVEL))
        self.assertEqual(float(flat.stoc.max()), 50.0)
        self.assertGreater(float(R.simulate_mesa(m, sine(20)).stoc.max()), 99.9)

    def test_02_ncl_construction(self):
        """Accepted 2026-11-19: k = 707/1000, f = 1414/1000, g = 314159/100000; degrees -> radians with Zorro PI:
        HP alpha arg k*2*PI/HP; SS a1 = exp(-f*g/SS); b1 cos arg f*PI/SS; same SS for both passes. The NCL body in the spec
        computes exactly these lines (asserted on its text), so IMP must_pass replays the same construction."""
        m = R.IMP_MODELS["mesa_printed(20,48,10)"]()
        hpf, ssr, ssf = R._mesa_filters(m)
        k, f, g, P = 707.0 / 1000, 1414.0 / 1000, 314159.0 / 100000, R.PI_ZORRO
        arg = k * 2.0 * P / 48
        al = (math.cos(arg) + math.sin(arg) - 1.0) / math.cos(arg)
        self.assertEqual(hpf, R.hp_code(48, k=k))
        self.assertLess(abs(hpf.a[0] - 2 * (1 - al)), 1e-15)
        a1 = math.exp(-f * g / 10)
        b1 = 2.0 * a1 * math.cos(f * P / 10)
        c1 = 1.0 - b1 + a1 * a1
        for flt in (ssr, ssf):
            self.assertLess(max(abs(flt.a[0] - b1), abs(flt.a[1] + a1 * a1), abs(flt.b[0] - c1 / 2)), 1e-15)
        spec, _, _ = S.load()
        body = [v for v in spec["variants"] if v["id"] == "NCL"][0]["body"]
        for line in ("ncl_k = ncl_k / 1000;", "ncl_f = ncl_f / 1000;", "ncl_g = ncl_g / 100000;",
                     "var ncl_arg = ncl_k * 2.0 * PI / HPPeriod;", "var ncl_a1 = exp(-ncl_f * ncl_g / SSPeriod);",
                     "var ncl_b1 = 2.0 * ncl_a1 * cos(ncl_f * PI / SSPeriod);", "vars ncl_HP = series(0, 3);"):
            self.assertIn(line, body)
        self.assertEqual(body.count("ncl_c1 * ("), 2)                       # roofing and final SS share the coefficients
        o = spec["observations"]["O_NCL"]
        for s in ("k * 2.0 * PI / HPPeriod", "exp(-f * g / SSPeriod)", "f * PI / SSPeriod", "mesa_printed(20,48,10)"):
            self.assertIn(s, o)

    def test_03_keyword_guards_fire(self):
        with self.assertRaises(ValueError):
            R.mesa_article(20, 48, 10, literals="rounded")
        with self.assertRaises(ValueError):
            R.mesa_article(20, 48, 10, final_seed="price")

    def test_04_grammar_and_registry(self):
        self.assertEqual(R.mesa_article_model("mesa_article(20,48,10)"), R.mesa_article(20, 48, 10))
        self.assertEqual(R.mesa_article_model("mesa_article(20, 48, 20)"), R.mesa_article(20, 48, 20))
        for bad in ("mesa_article(20,48)", "mesa_article(0,48,10)", "mesa_article(20,48,10) ", "mesa_code(20,48,10)",
                    "mesa_article(1e3,48,10)", None, "__import__('os')"):
            self.assertIsNone(R.mesa_article_model(bad), bad)
        self.assertIsInstance(R.osc_article_model("reflex_article(20)"), R.ReflexModel)
        self.assertIsInstance(R.osc_article_model("mesa_article(20,48,10)"), R.MesaModel)
        self.assertIsNone(R.osc_article_model("us_article(20)"))
        spec, _, _ = S.load()
        names = list(spec["imp"]["must_pass"].values()) + list(spec["imp"]["must_fail"].values())
        for nm in names:
            self.assertIsInstance(R.IMP_MODELS[nm](), R.MesaModel, nm)
        self.assertEqual(R.IMP_MODELS["mesa_code(22,48,10)"](), R.mesa_code(22, 48, 10))
        self.assertEqual(R.IMP_MODELS["mesa_code(20,40,10)"]().hp, 40)


if __name__ == "__main__":
    unittest.main()
