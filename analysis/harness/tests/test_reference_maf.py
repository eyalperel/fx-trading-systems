"""MAF stage 1: the D7 reference models (reference.mama_article / mama_superseded / frama_article / frama_superseded, the conditioning
classifier) against (1) the planning chat's independent review model docs/harness/MAMA_FRAMA_REVIEW_MODEL.py and (2) the brief's numbers,
items 1-7 (docs/harness/MAF_STAGE1_PROMPT.md, the source of every number below; the planning chat's script MAMA_FRAMA_STAGE1_NUMBERS.py).
Brief rule: the models mirror the CORRECTED code's operation order (deg = 180/pi, then atan(.)*deg) while the planning chat used
atan(.)*180/pi, so a difference counts only if it exceeds max(10 x that column's conditioning value, 1e-12); effects within 1% relative.
Rule (CLAUDE.md 4.4): each model hook is seen to change the output. No .c file is read, Zorro is not run.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import importlib.util
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import maf_support as S     # noqa: E402

R, C = S.R, S.C
MA05, MA03 = R.mama_article((1, 2), (1, 20)), R.mama_article((3, 10), (1, 10))
FR16, FR32 = R.frama_article(16), R.frama_article(32)
H0 = 2 / 1000


def review():
    spec = importlib.util.spec_from_file_location("maf_review_model", S.REVIEW_MODEL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V = review()
X = V.inputs()
mx = S.mx


class TestModelsVsReviewModel(unittest.TestCase):
    """(b) The models reproduce the planning chat's review model: FRAMA bit for bit (same operation order), MAMA within the
    operation-order difference (atan*deg vs atan*180/pi), the old files bit for bit."""

    def test_01_mama_article_vs_mama_src(self):
        worst = 0.0
        for m, (FL, SL) in ((MA05, (0.5, 0.05)), (MA03, (0.3, 0.1))):
            for k, x in X.items():
                a, b = R.simulate_mama(m, x), V.mama_src(x, FL, SL)
                for c in R.MAMA_COLUMNS:
                    worst = max(worst, mx(getattr(a, c), b[c]))
        print("\n  mama_article vs mama_src, all inputs and columns: %.3e" % worst)
        self.assertLess(worst, 1e-12)          # (b) 8.3e-14 (phase, s40)
        self.assertGreater(worst, 0.0)         # the operation order differs: not bit-identical

    def test_02_frama_article_bit_identical_point_and_band(self):
        for m in (FR16, FR32):
            for k, x in X.items():
                for band in (False, True):
                    H, L = (x + H0, x - H0) if band else (x, x)
                    a, b = R.simulate_frama(m, x, H, L), V.frama_src(x, m.N, H=H, Lo=L)
                    for c in R.FRAMA_COLUMNS:
                        self.assertEqual(mx(getattr(a, c), b[c]), 0.0, (m.N, k, band, c))

    def test_03_frama_old_startup_is_the_current_file_with_exact_literals(self):
        for m in (FR16, FR32):
            mo = R.frama_article(m.N, startup="old")
            for k, x in X.items():
                for band in (False, True):
                    H, L = (x + H0, x - H0) if band else (x, x)
                    o = R.simulate_frama(mo, x, H, L).out
                    c = V.frama_code(x, m.N // 2, k46=4.6, k01=0.01, H=H, Lo=L)["out"]
                    self.assertEqual(mx(o, c), 0.0, (m.N, k, band))

    def test_04_mama_superseded_one_slot_is_the_current_file(self):
        """A slot preceded by 4 (or >= 5) other superseded calls on bar 0 is mama_code with counter_offset 4 (or 5): bit-identical."""
        F32 = {k: V.f32(float(k)) for k in ("0.0962", "0.5769", "0.075", "0.54", "0.2", "0.8", "0.33", "0.67")}
        for FL, SL in ((0.5, 0.05), (0.3, 0.1)):
            for k in ("flat", "s5", "s20", "s100", "ramp"):
                x = X[k]
                for off in (0, 4, 5, 9):
                    sh = R.simulate_mama_shared([(FL, SL)] * (off + 1), [x] * (off + 1))[off]
                    ref = V.mama_code(x, FL, SL, lit=F32, pi=V.f32(3.14159), counter_offset=min(off, 5))
                    for c in R.MAMA_COLUMNS:
                        self.assertEqual(mx(getattr(sh, c), ref[c]), 0.0, (FL, k, off, c))

    def test_05_frama_superseded_one_slot_is_the_current_file(self):
        for T in (8, 16):
            for k, x in X.items():
                for band in (False, True):
                    H, L = (x + H0, x - H0) if band else (x, x)
                    o = R.simulate_frama_shared([T], [x], [H], [L])[0].out
                    self.assertEqual(mx(o, V.frama_code(x, T, H=H, Lo=L)["out"]), 0.0, (T, k, band))


class TestSharedState(unittest.TestCase):
    """D7 rule 7: the shared statics of the old files, replayed over several slots, change the outputs (seen to fire)."""

    def test_01_mama_shared_barcount_shifts_the_startup_only(self):
        x = X["s20"]
        alone = R.simulate_mama_shared([(0.5, 0.05)], [x])[0]
        two = R.simulate_mama_shared([(0.5, 0.05)] * 7, [X["flat"]] * 6 + [x])[6]     # 6 earlier calls: barCount > 5 from bar 0
        d = np.abs(two.mama - alone.mama)
        self.assertGreater(float(d.max()), 1e-3)                  # start-up differs
        self.assertEqual(float(d[1000:].max()), 0.0)              # s20: not permanent (only barCount is shared)

    def test_02_frama_shared_prev_is_permanent(self):
        x, y = X["s40"], X["s100"]
        a = R.simulate_frama_shared([8, 8], [x, y], [x, y], [x, y])
        alone = R.simulate_frama_shared([8], [x], [x], [x])[0]
        self.assertGreater(float(np.max(np.abs(a[0].out[1000:] - alone.out[1000:]))), 1e-3)

    def test_03_frama_shared_point_ramp_is_immune(self):
        """(b) On the point ramp alpha = 1 (D < 1), so every call overwrites the shared state with its own x: no effect."""
        r = X["ramp"]
        a = R.simulate_frama_shared([8, 8], [X["s20"], r], [X["s20"], r], [X["s20"], r])
        self.assertEqual(mx(a[1].out, r), 0.0)

    def test_04_old_frama_dim_alpha_are_nan_on_early_returns(self):
        f = R.simulate_frama_shared([8], [X["flat"]], [X["flat"]], [X["flat"]])[0]
        self.assertTrue(np.all(np.isnan(f.dim)) and np.all(f.out == X["flat"][0]))


class TestHooksFire(unittest.TestCase):
    """Every model hook changes the output (CLAUDE.md 4.4)."""

    def test_01_mama_hooks(self):
        x = X["s40"]
        base = R.simulate_mama(MA05, x)
        for kw, col in ((dict(w1=(963, 10000)), "phase"), (dict(w2=(5770, 10000)), "phase"), (dict(ka=(76, 1000)), "period"),
                        (dict(kb=(55, 100)), "period"), (dict(a2=(21, 100)), "period"), (dict(a8=(81, 100)), "period"),
                        (dict(fama_k=(51, 100)), "fama"), (dict(pi="zorro"), "phase"), (dict(literals="float32"), "period")):
            o = R.simulate_mama(R.mama_article((1, 2), (1, 20), **kw), x)
            self.assertGreater(mx(getattr(o, col), getattr(base, col)), 1e-9, kw)
        o = R.simulate_mama(R.mama_article((1, 2), (1, 20), up=(14, 10)), X["ramp"])          # 1.5x bound: binds on the ramp
        self.assertGreater(mx(o.period, R.simulate_mama(MA05, X["ramp"]).period), 1e-6)
        o = R.simulate_mama(R.mama_article((1, 2), (1, 20), c33=(34, 100), c67=(66, 100)), x)  # SmoothPeriod is not exported (MA-6)
        self.assertEqual(max(mx(getattr(o, c), getattr(base, c)) for c in R.MAMA_COLUMNS), 0.0)

    def test_02_frama_hooks(self):
        x = X["s20"]
        base = R.simulate_frama(FR16, x)
        for kw in (dict(k=(461, 100)), dict(literals="float32"), dict(startup="old")):
            o = R.simulate_frama(R.frama_article(16, **kw), x)
            self.assertGreater(mx(o.alpha, base.alpha) + mx(o.out, base.out), 1e-9, kw)
        o = R.simulate_frama(R.frama_article(16, lo=(2, 100)), x)       # the floor binds only if raised above exp(-4.6)
        self.assertGreater(mx(o.alpha, base.alpha), 1e-3)

    def test_03_refusals(self):
        for bad in (lambda: R.mama_article((1, 2), (1, 20), pi="pi"), lambda: R.mama_article((1, 2), (1, 20), literals="x"),
                    lambda: R.mama_article((1, 2), (0, 20)), lambda: R.mama_article(0.5, (1, 20)),
                    lambda: R.frama_article(15), lambda: R.frama_article(16, startup="new"), lambda: R.frama_article(16, k=4.6)):
            with self.assertRaises(ValueError):
                bad()
        self.assertIsNone(R.adaptive_article_model("mama_article(1/20,1/2)"))       # SL > FL refused
        self.assertIsNone(R.adaptive_article_model("frama_article(15)"))
        self.assertIsNone(R.adaptive_article_model("eval(1)"))
        self.assertEqual(R.adaptive_article_model("mama_article(1/2,1/20)"), MA05)
        self.assertEqual(R.adaptive_article_model("frama_article(32)"), FR32)


class TestBriefItems(unittest.TestCase):
    """The brief's items 1-7 (planning-chat numbers), reproduced with the models (tolerance rule in the module docstring)."""

    def test_item1_conditioning_table(self):
        """Classification (CHECKED / INFO) and the largest checked values, both specs, the spec's seed and draw order."""
        for path, tabs in ((S.MAMA_SPEC, ("MA05", "MA03")), (S.FRAMA_SPEC, ("FR16", "FR32"))):
            _, cs, _, _ = S.load(path)
            vals, info = C.conditioning_table(cs)
            if path == S.MAMA_SPEC:
                for t in tabs:
                    self.assertEqual(info[t], {"flat": list(R.MAMA_COLUMNS), "ramp": list(R.MAMA_COLUMNS), "s5": ["mama", "fama", "alpha", "phase"]})
                want = {("MA05", "s100", "phase"): 1.453e-10, ("MA05", "s100", "alpha"): 2.318e-11, ("MA05", "s100", "fama"): 2.351e-13,
                        ("MA03", "s100", "phase"): 1.538e-10, ("MA03", "s100", "alpha"): 1.624e-11, ("MA03", "s100", "fama"): 6.678e-13,
                        ("MA05", "ramp", "alpha"): 4.5e-01, ("MA05", "ramp", "fama"): 2.788e-04, ("MA05", "flat", "fama"): 3.244e-02,
                        ("MA05", "s5", "fama"): 1.686e-02}
                for (t, i, c), w in want.items():
                    self.assertTrue(math.isclose(vals[t][i][c], w, rel_tol=6e-3), (t, i, c, vals[t][i][c], w))
                for t in tabs:                     # the largest CHECKED values are those of s100
                    chk = [(vals[t][i][c], c) for i in ("s10", "s20", "s40", "s100") for c in R.MAMA_COLUMNS]
                    self.assertEqual(max(v for v, c in chk if c == "phase"), vals[t]["s100"]["phase"])
            else:
                for t in tabs:
                    self.assertEqual(info[t], {"flat": ["dim", "alpha"]})
                ch = [vals[t][i][c] for t in tabs for i in cs["adaptive"]["conditioning"]["order"] for c in R.FRAMA_COLUMNS
                      if not (i == "flat" and c != "out")]
                self.assertEqual("%.3e" % max(vals[t][i]["out"] for t in tabs for i in vals[t] if i in cs["adaptive"]["conditioning"]["order"]),
                                 "5.773e-15")
                self.assertEqual("%.3e" % vals["FR16"]["s100"]["dim"], "5.178e-13")
                self.assertEqual("%.3e" % vals["FR16"]["s100"]["alpha"], "1.285e-12")
                self.assertEqual(max(ch), vals["FR16"]["s100"]["alpha"])
                self.assertTrue(math.isclose(vals["FR16"]["flat"]["dim"], 2.0, rel_tol=1e-3))

    def test_item2_mama_facts(self):
        brief = {"s10": (10.046866000871653, 10.138692660663777), "s20": (19.955554535888744, 20.051537545020732),
                 "s40": (39.807136333604554, 40.18200281308779), "s100": (50.0, 50.0)}
        for m in (MA05, MA03):
            for i, (lo, hi) in brief.items():
                o = R.simulate_mama(m, X[i])
                self.assertTrue(np.all((o.alpha[5:] >= m.SL) & (o.alpha[5:] <= m.FL)))
                self.assertEqual(float(np.max(np.abs(o.alpha[:5]))), 0.0)
                self.assertLessEqual(float(np.max(o.period)), 50.0)
                self.assertLess(abs(float(np.min(o.period[1000:])) - lo), 1e-12)
                self.assertLess(abs(float(np.max(o.period[1000:])) - hi), 1e-12)
        self.assertEqual(float(np.max(R.simulate_mama(MA05, X["s100"]).period[1000:])), 50.0)        # exactly
        for i, (lo, hi) in (("s20", (1.099446341089458, 1.1005536589105402)), ("s100", (1.0920658491664514, 1.1079341508335487))):
            f = R.simulate_mama(MA05, X[i]).fama[1000:]
            self.assertLess(abs(float(f.min()) - lo), 1e-12)
            self.assertLess(abs(float(f.max()) - hi), 1e-12)

    def test_item3_mama_equivariance(self):
        last = 0
        for m in (MA05, MA03):
            for i in ("s20", "s40"):
                a = R.simulate_mama(m, X[i])
                for k, c0 in ((10.0, -99 / 10), (1.0, 11 / 10)):
                    b = R.simulate_mama(m, k * X[i] + c0)
                    for c in R.MAMA_COLUMNS:
                        ref = k * getattr(a, c) + c0 if c in ("mama", "fama") else getattr(a, c)
                        d = np.abs(getattr(b, c) - ref)
                        nz = np.nonzero(d > (1e-8 if c == "phase" else 1e-9))[0]
                        last = max(last, int(nz[-1]) if len(nz) else 0)
                        lim = {"mama": 1.6e-14, "fama": 1.6e-14, "alpha": 3.7e-13, "period": 6.2e-12, "phase": 5.3e-11}[c]
                        self.assertLess(float(d[1000:].max()), max(10 * lim, 1e-12) if c in ("mama", "fama") else lim * 1.01, (i, c))
        self.assertEqual(last, 516)                     # brief: <= 516 on s20 / s40, both variants

    def test_item4_imp_estimate(self):
        o = R.simulate_mama(MA05, X["s100"])
        p = R.simulate_mama(MA05, S.round15(X["s100"]))
        for c, w in (("phase", 1.124e-10), ("alpha", 1.737e-11), ("fama", 2.596e-13)):
            self.assertTrue(math.isclose(mx(getattr(p, c), getattr(o, c)), w, rel_tol=2e-3), c)
        o = R.simulate_frama(FR16, X["s100"])
        p = R.simulate_frama(FR16, S.round15(X["s100"]))
        self.assertEqual("%.3e" % mx(p.alpha, o.alpha), "1.933e-12")
        self.assertLessEqual(mx(p.out, o.out), 5.1e-15)

    def test_item5_frama_known_answers(self):
        s = 1 / 10000
        for m, D_pt, D_b, a_b, lag, conv in ((FR16, 0.9004643264490856, 1.773229138152978, 0.028528433125587088, 34.05274879969143, 854),
                                             (FR32, 0.9526942852216433, 1.6316125940199773, 0.054725914083758966, 17.27287888639891, 450)):
            N = m.N
            o = R.simulate_frama(m, X["ramp"])
            self.assertEqual(mx(o.out, X["ramp"]), 0.0)
            self.assertTrue(np.all(o.alpha == 1.0))
            self.assertEqual(math.log2(4 * (N / 2 - 1) / (N - 1)), D_pt)
            self.assertLess(abs(o.dim[500] - D_pt), 1e-13)
            r1, r3 = s * (N / 2 - 1) + 2 * H0, s * (N - 1) + 2 * H0
            self.assertEqual(math.log2(4 * r1 / r3), D_b)
            self.assertEqual(math.exp(-4.6 * (D_b - 1)), a_b)
            self.assertEqual((1 - a_b) / a_b, lag)
            b = R.simulate_frama(m, X["ramp"], X["ramp"] + H0, X["ramp"] - H0)
            meas = float(np.mean((X["ramp"][-100:] - b.out[-100:]) / s))
            self.assertLess(abs(meas - lag), 1e-10)
            nz = np.nonzero(np.abs((X["ramp"] - b.out) / s - lag) > 1e-9)[0]
            self.assertEqual(int(nz[-1]) + 1, conv)
            f = R.simulate_frama(m, X["flat"])
            self.assertEqual(mx(f.out, X["flat"]), 0.0)
            self.assertEqual(float(np.max(np.abs(f.dim))), 0.0)

    def test_item6_frama_bounds(self):
        amin, dmax = 1.0, 0.0
        for m in (FR16, FR32):
            for x in X.values():
                for H, L in ((x, x), (x + H0, x - H0)):
                    o = R.simulate_frama(m, x, H, L)
                    amin, dmax = min(amin, float(o.alpha.min())), max(dmax, float(o.dim.max()))
                    self.assertEqual(float(np.max(np.maximum(o.out - np.maximum.accumulate(x), np.minimum.accumulate(x) - o.out))), 0.0)
                    self.assertLessEqual(float(o.alpha.max()), 1.0)
        self.assertEqual(R.FRAMA_EXP_MIN, 0.010051835744633586)
        self.assertEqual(amin, 0.010051835744633504)
        self.assertEqual(dmax, 2.0000000000000018)
        self.assertLess((R.FRAMA_EXP_MIN - amin) / R.FRAMA_EXP_MIN, 1e-12)
        self.assertLess((dmax - 2) / 2, 1e-12)

    def test_item7_frama_equivariance(self):
        x = X["s40"]
        worst = {}
        for m in (FR16, FR32):
            a = R.simulate_frama(m, x, x + H0, x - H0)
            for tid, k, c0 in (("sc", 10.0, -99 / 10), ("of", 1.0, 11 / 10)):
                b = R.simulate_frama(m, k * x + c0, k * (x + H0) + c0, k * (x - H0) + c0)
                for c in R.FRAMA_COLUMNS:
                    ref = k * getattr(a, c) + c0 if c == "out" else getattr(a, c)
                    worst[(tid, c)] = max(worst.get((tid, c), 0.0), mx(getattr(b, c), ref))
        brief = {("sc", "out"): 7.994e-15, ("sc", "dim"): 1.532e-14, ("sc", "alpha"): 2.787e-14,
                 ("of", "out"): 1.776e-15, ("of", "dim"): 5.773e-14, ("of", "alpha"): 6.384e-14}
        for kk, w in brief.items():
            self.assertEqual("%.3e" % worst[kk], "%.3e" % w, kk)


if __name__ == "__main__":
    unittest.main()
