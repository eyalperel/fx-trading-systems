"""Pre-run condition (iii) for RFF: reference.py reproduces the numbers pre-registered in specs/RFF_ArticleFidelity.toml.

Sections: expected tables, [floor] (+ per variant), every [variants.effect], [detect.required] (rule: kind >= 10x its
tolerance), [imp.fire_test], [known_answer_T20], the D2 windows, variant / check counts.
Tolerance: <= 1e-9 absolute, relative 1e-9 for |value| > 1 (CLAUDE.md / task rule); every number in the spec is stored at
full precision, so no digit-rounding is needed (HPF Amendment 1, A1.2). No .c file is read; Zorro is not run.
Measurements use the checker's own functions (check_rows with m_gain / m_gain_alt / m_phase / m_ramp_res / m_startup).
A number the reference does not reproduce FAILS its test (never loosened to pass).
Each section prints "(iii) <section>: largest deviation ..." for the amendment record.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rff_support as S      # noqa: E402

C, R, G = S.C, S.R, S.G
TS = (5, 10, 20, 40, 100)
REAL = {"P48S10": (48, 10), "P30S10": (30, 10), "P125S10": (125, 10), "P48S20": (48, 20)}
CONTROLS = ("NCA", "NCB", "NCU", "NCO", "NC1", "NC1s", "NC2")
TOL = 1e-9
DEV = {}


def dev(expected, actual):
    d = abs(actual - expected)
    return d / abs(expected) if abs(expected) > 1 else d


def within(expected, actual, tol=TOL):
    return dev(expected, actual) <= tol


def note(section, expected, actual, tol=TOL):
    d = dev(expected, actual)
    DEV[section] = max(DEV.get(section, 0.0), d)
    return d <= tol


def hp_printed(p):
    """The article's HP with .707 as printed (exact pi where the degrees convert)."""
    arg = 0.707 * 2 * math.pi / p
    return R._hp_filter((math.cos(arg) + math.sin(arg) - 1) / math.cos(arg))


def ss_printed(p):
    """The article's SuperSmoother with 1.414 and 3.14159 as printed (the cosine's 180 degrees is exact pi)."""
    a1 = math.exp(-1.414 * 3.14159 / p)
    b1 = 2 * a1 * math.cos(1.414 * math.pi / p)
    c3 = -a1 * a1
    c1 = 1 - b1 - c3
    return R.Filter(b=(c1 / 2, c1 / 2), a=(b1, c3))


class TestRFFSpecNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = S.spec()
        cls.cs = S.cs()
        cls.x = S.inputs()
        cls.y = S.own_model_outputs()
        cls.km = {v["id"]: S.kind_max(v["id"]) for v in cls.cs["variants"]}

    @classmethod
    def tearDownClass(cls):
        print()
        for sec in ("expected", "floor", "effects", "known_answer", "imp_fire_test"):
            if sec in DEV:
                print("(iii) %-13s largest deviation %.3e" % (sec, DEV[sec]))

    # ---- the comparison rule itself is seen to fire
    def test_rule_fires(self):
        self.assertTrue(within(0.5, 0.5 + 9e-10))
        self.assertFalse(within(0.5, 0.5 + 2e-9))
        self.assertTrue(within(4.7, 4.7 * (1 + 9e-10)))
        self.assertFalse(within(4.7, 4.7 * (1 + 2e-9)))
        print("\n  [fire] comparison rule: 2e-9 abs / 2e-9 rel rejected, 9e-10 accepted")

    # ---- structure and counts
    def test_variants_and_counts(self):
        vs = self.spec["variants"]
        self.assertEqual([v["id"] for v in vs if v["role"] == "real"], list(REAL))
        self.assertEqual([v["id"] for v in vs if v["role"] == "neg_control"], list(CONTROLS))
        self.assertEqual(len(vs), 11)
        real = [v for v in self.cs["variants"] if v["role"] == "real"]
        n = sum(C.n_checks(self.cs, v) for v in real)
        print("\n  real checks = %d (4 variants x %s)" % (n, sorted({C.n_checks(self.cs, v) for v in real})))
        self.assertEqual(n, 64)
        self.assertIn("All 64 real checks PASS", self.spec["pass_condition"]["text"])
        self.assertIn("4 real + 7 negative controls = 11 variants", self.spec["pass_condition"]["text"])
        for v in vs:
            self.assertEqual(v["params"], list(REAL.get(v["id"], {"NC1": (49, 10), "NC1s": (48, 11)}.get(v["id"], (48, 10)))))
        self.assertEqual(self.spec["inputs"]["alternating"], True)
        self.assertEqual(self.spec["checks"]["startup_inputs"], ["flat", "ramp", "s20"])

    # ---- expected tables
    def test_expected_tables(self):
        fails = []
        for name, e in self.spec["expected"].items():
            hp, ss = REAL[name]
            f = R.roof_article(hp, ss)
            self.assertEqual(e["article"], "roof_article(%d,%d)" % (hp, ss))
            for t, g in zip(TS, e["gains"]):
                if not note("expected", g, R.gain_at(f, t)):
                    fails.append((name, "gain", t))
            for t in TS:
                if not note("expected", e["phases"][str(t)], R.phase_at(f, t)):
                    fails.append((name, "phase", t))
            if not note("expected", e["gain_alt"], R.gain_at(f, 2)):
                fails.append((name, "gain_alt"))
            if not note("expected", e["resid"], R.ramp_residual(f, self.cs["level"], self.cs["slope"])):
                fails.append((name, "resid"))
            self.assertEqual((e["flat"], e["resid"]), (0.0, 0.0))
            self.assertNotIn("phase_alt", e)
            self.assertLess(e["gain_alt"], self.spec["checks"]["phase_gate"])             # the gate binds in every table
            self.assertGreaterEqual(min(e["gains"]), self.spec["checks"]["phase_gate"])    # ... and nowhere else
        print("\n  expected tables: 4 x (5 gains + 5 phases + alt gain + resid) = 48 values, fails %s" % fails)
        self.assertEqual(fails, [])

    def test_expected_table_guard_fires(self):
        f = R.roof_article(48, 10)
        g = self.spec["expected"]["P48S10"]["gains"][2]
        self.assertFalse(within(g + 1e-6, R.gain_at(f, 20)))
        self.assertFalse(within(g, R.gain_at(R.roof_article(48, 11), 20)))

    # ---- tolerance windows (D2 rule 3): floor x10 <= tolerance
    def test_windows_hold_with_the_default_tolerances(self):
        tol = self.cs
        want = dict(gain=tol["tol_gain"], phase=tol["tol_phase"], resid=tol["tol_resid"], startup=tol["tol_startup"],
                    flat=tol["tol_flat"])
        self.assertEqual(want, dict(gain=3e-5, phase=3e-5, resid=1e-9, startup=1e-6, flat=1e-9))       # D4 rule 5 defaults
        for q, t in want.items():
            self.assertLessEqual(self.spec["floor"][q] * 10, t, q)
        print("\n  windows: " + ", ".join("%s %.2e x10 <= %.0e" % (q, self.spec["floor"][q], t) for q, t in want.items()))

    def test_window_guard_fires(self):
        self.assertGreater(self.spec["floor"]["phase"] * 10 * 2, self.cs["tol_phase"])      # a halved tolerance would fail

    # ---- floor
    def test_floor(self):
        """[floor] = max over the 4 real variants of each kind, corrected code (own model) vs the article tables, measured
        with the checker's own check_rows; per variant in [floor.per_variant.*]."""
        fl, fails = self.spec["floor"], []
        for q in S.KINDS:
            want = max(self.km[v].get(q, 0.0) for v in REAL)
            print("  floor %-8s spec %.10g  measured %.10g  dev %.3e" % (q, fl[q], want, dev(fl[q], want)))
            if not note("floor", fl[q], want):
                fails.append(q)
        for v in REAL:
            pv = self.spec["floor"]["per_variant"][v]
            for q in S.KINDS:
                if not note("floor", pv[q], self.km[v].get(q, 0.0)):
                    fails.append((v, q))
            for q in S.KINDS:                                                  # the max really is the max
                self.assertLessEqual(pv[q], fl[q] + 1e-30)
        self.assertEqual(fails, [])

    def test_floor_guard_fires(self):
        want = max(self.km[v]["gain"] for v in REAL)
        self.assertTrue(within(self.spec["floor"]["gain"], want))
        self.assertFalse(within(self.spec["floor"]["gain"] + 5e-9, want))

    def test_floor_is_the_pi_gap(self):
        """The floor is analytic: roof_code (Zorro PI) vs roof_article; planning-chat bounds gain <= 5.6e-7, phase <= 1.6e-6."""
        self.assertLessEqual(self.spec["floor"]["gain"], 5.6e-7)
        self.assertLessEqual(self.spec["floor"]["phase"], 1.6e-6)

    # ---- variant effects
    def test_variant_effects(self):
        fails, n = [], 0
        for v in self.spec["variants"]:
            if v["role"] != "neg_control":
                continue
            m = self.km[v["id"]]
            for q in S.KINDS:
                n += 1
                if not note("effects", v["effect"][q], m.get(q, 0.0)):
                    fails.append((v["id"], q, v["effect"][q], m.get(q, 0.0)))
        print("\n  variant effects: 7 controls x 5 kinds = %d values, fails %s" % (n, fails))
        self.assertEqual(n, 35)
        self.assertEqual(fails, [])

    def test_variant_effect_guard_fires(self):
        eff = [v for v in self.spec["variants"] if v["id"] == "NCB"][0]["effect"]["gain"]
        self.assertTrue(within(eff, self.km["NCB"]["gain"]))
        self.assertFalse(within(eff * 1.01, self.km["NCB"]["gain"]))
        self.assertFalse(within(eff, self.km["NCA"]["gain"]))                     # a swapped control

    # ---- detect.required follows the rule exactly
    def test_detect_required_is_the_rule(self):
        """[detect.required][id] = every kind whose effect >= 10x its tolerance (not a hand pick), and every control has one."""
        tol = dict(flat=self.cs["tol_flat"], gain=self.cs["tol_gain"], phase=self.cs["tol_phase"],
                   resid=self.cs["tol_resid"], startup=self.cs["tol_startup"])
        req = self.spec["detect"]["required"]
        for v in self.spec["variants"]:
            if v["role"] != "neg_control":
                continue
            rule = [q for q in S.KINDS if self.km[v["id"]].get(q, 0.0) >= 10 * tol[q]]
            print("  %-5s required %-32s (ratios %s)" % (v["id"], rule, {q: "%.3g" % (self.km[v["id"]].get(q, 0.0) / tol[q]) for q in S.KINDS}))
            self.assertEqual(req[v["id"]], rule, v["id"])
            self.assertTrue(rule, "control %s has NO kind >= 10x" % v["id"])
        self.assertEqual(set(req), set(CONTROLS))

    def test_detect_guard_fires(self):
        """NCO's gain is 2.2x tolerance: a hand-picked 'gain' for NCO would not meet the 10x rule (and NCA startup 7.1x)."""
        self.assertLess(self.km["NCO"]["gain"], 10 * self.cs["tol_gain"])
        self.assertLess(self.km["NCA"]["startup"], 10 * self.cs["tol_startup"])
        self.assertNotIn("gain", self.spec["detect"]["required"]["NCO"])
        self.assertNotIn("startup", self.spec["detect"]["required"]["NCA"])

    # ---- known answers (planning chat; superseded 0.890038)
    def test_known_answer_T20(self):
        ka = self.spec["known_answer_T20"]
        art = R.roof_article(48, 10)
        got = dict(article_gain_T20=R.gain_at(art, 20), article_phase_T20=R.phase_at(art, 20),
                   printed_gain_T20=R.gain_at(R.cascade(hp_printed(48), ss_printed(10)), 20),
                   old_gain_T20=R.gain_at(R.cascade(R.hp_code(48, k=0.707, pi_value=math.pi),
                                                    R.ss2_code(10, pi_value=math.pi)), 20))
        for k, v in got.items():
            self.assertTrue(note("known_answer", ka[k], v), (k, ka[k], v))
        # planning-chat values (stated to ~1e-14 by an independent evaluation) agree to 1e-12
        for k, v in dict(article_gain_T20=0.8900165495219456, article_phase_T20=-0.05338683922280491,
                         printed_gain_T20=0.8900220682097724, old_gain_T20=0.8900377520202766).items():
            self.assertLess(abs(ka[k] - v), 1e-12, k)
        self.assertLess(abs(ka["old_gain_T20"] - 0.890038), 1e-6)       # PROJECT_STATE section 5 value = the OLD code

    def test_known_answer_guard_fires(self):
        ka = self.spec["known_answer_T20"]
        self.assertFalse(within(ka["article_gain_T20"], ka["old_gain_T20"]))               # the superseded value is not the article's
        self.assertAlmostEqual(R.gain_at(R.roof_article(48, 10), 2), 0.0, delta=1e-15)

    # ---- IMP fire test
    def _maxdiff(self, a, b):
        return max(float(np.max(np.abs(a[i] - b[i]))) for i in C.input_names(self.cs))

    def _sim(self, model_str, seed):
        m = R.IMP_MODELS[model_str]()
        return {i: R.simulate_any(m, self.x[i], seed=seed) for i in C.input_names(self.cs)}

    def test_imp_fire_test(self):
        ft = self.spec["imp"]["fire_test"]
        corr = self._sim("roof_code(48, 10)", "zero")
        nco = self._sim("roof_nco(48, 10)", "price")
        got = {"P48S10 vs NCO model": (ft["p48s10_vs_nco_model"], self._maxdiff(self.y["P48S10"], nco)),
               "NCO vs corrected model": (ft["nco_vs_corrected_model"], self._maxdiff(self.y["NCO"], corr))}
        for v in CONTROLS:
            # own-model replay is exactly 0 (a standalone model); the control differs from roof_code(48, 10) by `disc`
            self.assertEqual(self._maxdiff(self.y[v], self._sim(self.spec["imp"]["must_pass"][v],
                                                                [x for x in self.spec["variants"] if x["id"] == v][0]["seed"])), 0.0, v)
            got["control " + v] = (ft["discrimination"][v], self._maxdiff(self.y[v], corr))
        fails = []
        for k, (stored, actual) in got.items():
            ok = note("imp_fire_test", stored, actual)
            print("  %-24s spec %-22.15g actual %-22.15g %s" % (k, stored, actual, "ok" if ok else "FAIL"))
            self.assertGreater(actual, 1e-9, "%s would not fire / discriminate" % k)
            if not ok:
                fails.append(k)
        self.assertEqual(len(got), 2 + 7)
        self.assertEqual(fails, [])

    def test_imp_fire_test_guard_fires(self):
        """A control that equals the corrected pipeline would NOT discriminate (replay 0): NCU's output vs a copy of itself."""
        corr = self._sim("roof_code(48, 10)", "zero")
        self.assertLessEqual(self._maxdiff(self.y["P48S10"], corr), 1e-9)                   # the real variant replays clean
        self.assertGreater(self._maxdiff(self.y["P48S10"], self._sim("roof_nco(48, 10)", "price")), 1e-9)

    def test_imp_lists_and_registry(self):
        imp = self.spec["imp"]
        self.assertEqual(set(imp["must_pass"]), {v["id"] for v in self.spec["variants"]})
        self.assertEqual(imp["must_fail"], {"P48S10": "roof_nco(48, 10)", "NCO": "roof_code(48, 10)"})
        for tab in (imp["must_pass"], imp["must_fail"]):
            for vid, m in tab.items():
                self.assertIn(m, R.IMP_MODELS, m)
        self.assertEqual(len(set(imp["must_pass"].values())), 11)                          # every variant has its own model


if __name__ == "__main__":
    unittest.main()
