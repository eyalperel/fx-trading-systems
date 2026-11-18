"""Pre-run condition (iii) for USE: reference.py reproduces the numbers pre-registered in specs/USE_ArticleFidelity.toml.

Sections: expected tables, [floor] (+ per variant), every [variants.effect], [detect.required] (rule: kind >= 10x its
tolerance), [imp.fire_test], [findings], the D2 windows, variant / check counts.
Tolerance: <= 1e-9 absolute, relative 1e-9 for |value| > 1; every number in the spec is stored at full precision.
No .c file is read; Zorro is not run. Measurements use the checker's own functions (check_rows).
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
import use_support as S      # noqa: E402

C, R, G = S.C, S.R, S.G
TS = (5, 10, 20, 40, 100)
REAL = {"P10": 10, "P14": 14, "P20": 20, "P30": 30}
CONTROLS = ("NCA", "NCB", "NCS", "NCX", "NC1", "NC2")
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


class TestUSESpecNumbers(unittest.TestCase):
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
        for sec in ("expected", "floor", "effects", "findings", "imp_fire_test"):
            if sec in DEV:
                print("(iii) %-13s largest deviation %.3e" % (sec, DEV[sec]))

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
        self.assertEqual([v["id"] for v in vs if v["role"] == "info"], ["NCL"])
        self.assertEqual(len(vs), 11)
        real = [v for v in self.cs["variants"] if v["role"] == "real"]
        n = sum(C.n_checks(self.cs, v) for v in real)
        print("\n  real checks = %d (4 variants x %s)" % (n, sorted({C.n_checks(self.cs, v) for v in real})))
        self.assertEqual(n, 64)
        self.assertEqual({C.n_checks(self.cs, v) for v in real}, {16})
        self.assertIn("All 64 real checks PASS", self.spec["pass_condition"]["text"])
        self.assertIn("4 real + 6 negative controls + 1 info (NCL) = 11 variants", self.spec["pass_condition"]["text"])
        for v in vs:
            self.assertEqual(v["params"], [REAL.get(v["id"], 21 if v["id"] == "NC1" else 20)])
        self.assertEqual(self.spec["inputs"]["alternating"], True)
        self.assertEqual(self.spec["checks"]["startup_inputs"], ["flat", "ramp", "s20"])
        self.assertEqual((self.spec["checks"]["startup_seed"], self.spec["checks"]["dc_gain"]), ("pass3", 1.0))
        self.assertEqual({v["id"]: v["seed"] for v in vs if v["id"] in ("NCS", "NCX", "P20")},
                         {"NCS": "pass4", "NCX": "zero", "P20": "pass3"})

    # ---- expected tables
    def test_expected_tables(self):
        fails = []
        for name, e in self.spec["expected"].items():
            f = R.us_article(REAL[name])
            self.assertEqual(e["article"], "us_article(%d)" % REAL[name])
            for t, g in zip(TS, e["gains"]):
                if not note("expected", g, R.gain_at(f, t)):
                    fails.append((name, "gain", t))
            for t in TS:
                if not note("expected", e["phases"][str(t)], R.phase_at(f, t)):
                    fails.append((name, "phase", t))
            if not note("expected", e["gain_alt"], R.gain_at(f, 2)):
                fails.append((name, "gain_alt"))
            if not note("expected", e["lag"], R.ramp_lag(f)):
                fails.append((name, "lag"))
            self.assertEqual((e["flat"], e["lag"]), (0.0, 0.0))
            self.assertNotIn("phase_alt", e)
            self.assertNotIn("resid", e)
            self.assertLess(e["gain_alt"], self.spec["checks"]["phase_gate"])
            self.assertGreaterEqual(min(e["gains"]), self.spec["checks"]["phase_gate"])
        print("\n  expected tables: 4 x (5 gains + 5 phases + alt gain + lag) = 48 values, fails %s" % fails)
        self.assertEqual(fails, [])

    def test_expected_table_guard_fires(self):
        g = self.spec["expected"]["P20"]["gains"][2]
        self.assertFalse(within(g + 1e-6, R.gain_at(R.us_article(20), 20)))
        self.assertFalse(within(g, R.gain_at(R.us_article(21), 20)))

    # ---- tolerance windows (D2 rule 3)
    def test_windows_hold_with_the_default_tolerances(self):
        want = dict(gain=self.cs["tol_gain"], phase=self.cs["tol_phase"], lag=self.cs["tol_lag"],
                    startup=self.cs["tol_startup"], flat=self.cs["tol_flat"])
        self.assertEqual(want, dict(gain=3e-5, phase=3e-5, lag=1e-3, startup=1e-6, flat=1e-9))      # D4 rule 5 defaults
        for q, t in want.items():
            self.assertLessEqual(self.spec["floor"][q] * 10, t, q)
        print("\n  windows: " + ", ".join("%s %.2e x10 <= %.0e" % (q, self.spec["floor"][q], t) for q, t in want.items()))

    def test_window_guard_fires(self):
        self.assertGreater(self.spec["floor"]["phase"] * 10 * 4, self.cs["tol_phase"])      # a tolerance 4x tighter would fail

    # ---- floor
    def test_floor(self):
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
                self.assertLessEqual(pv[q], fl[q] + 1e-30)
        self.assertEqual(fails, [])

    def test_floor_guard_fires(self):
        want = max(self.km[v]["gain"] for v in REAL)
        self.assertTrue(within(self.spec["floor"]["gain"], want))
        self.assertFalse(within(self.spec["floor"]["gain"] + 5e-9, want))

    def test_floor_is_the_pi_gap(self):
        self.assertLessEqual(self.spec["floor"]["gain"], 6.6e-7)
        self.assertLessEqual(self.spec["floor"]["phase"], 7.7e-7)

    # ---- variant effects
    def test_variant_effects(self):
        fails, n = [], 0
        for v in self.spec["variants"]:
            if v["role"] == "real":
                continue
            m = self.km[v["id"]]
            for q in S.KINDS:
                n += 1
                if not note("effects", v["effect"][q], m.get(q, 0.0)):
                    fails.append((v["id"], q, v["effect"][q], m.get(q, 0.0)))
        print("\n  variant effects: 6 controls + NCL x 5 kinds = %d values, fails %s" % (n, fails))
        self.assertEqual(n, 35)
        self.assertEqual(fails, [])

    def test_variant_effect_guard_fires(self):
        eff = [v for v in self.spec["variants"] if v["id"] == "NCB"][0]["effect"]["gain"]
        self.assertTrue(within(eff, self.km["NCB"]["gain"]))
        self.assertFalse(within(eff * 1.01, self.km["NCB"]["gain"]))
        self.assertFalse(within(eff, self.km["NCA"]["gain"]))                     # a swapped control

    # ---- detect.required follows the rule exactly
    def test_detect_required_is_the_rule(self):
        tol = dict(flat=self.cs["tol_flat"], gain=self.cs["tol_gain"], lag=self.cs["tol_lag"], phase=self.cs["tol_phase"],
                   startup=self.cs["tol_startup"])
        req = self.spec["detect"]["required"]
        for vid in CONTROLS:
            rule = [q for q in S.KINDS if self.km[vid].get(q, 0.0) >= 10 * tol[q]]
            print("  %-4s required %-30s (ratios %s)" % (vid, rule, {q: "%.3g" % (self.km[vid].get(q, 0.0) / tol[q]) for q in S.KINDS}))
            self.assertEqual(req[vid], rule, vid)
            self.assertTrue(rule, "control %s has NO kind >= 10x" % vid)
        self.assertEqual(set(req), set(CONTROLS))
        self.assertNotIn("NCL", req)                                              # the INFO variant is not a control

    def test_detect_guard_fires(self):
        """NCS is seen by start-up only: its gain / phase effects are the Zorro-PI floor (< 1x tolerance)."""
        self.assertEqual(self.spec["detect"]["required"]["NCS"], ["startup"])
        self.assertLess(self.km["NCS"]["gain"], self.cs["tol_gain"])
        self.assertLess(self.km["NCS"]["phase"], self.cs["tol_phase"])
        self.assertGreater(self.km["NCS"]["startup"], 10 * self.cs["tol_startup"])
        for vid in CONTROLS:                                                      # the ramp-lag check is structural only
            self.assertLess(self.km[vid]["lag"], 1e-6 * self.cs["tol_lag"], vid)         # < 1e-9: ~1e-12 round-off
            self.assertNotIn("lag", self.spec["detect"]["required"][vid])

    # ---- NCL: INFO
    def test_ncl_is_info_and_reported(self):
        ncl = [v for v in self.spec["variants"] if v["id"] == "NCL"][0]
        self.assertEqual(ncl["role"], "info")
        self.assertAlmostEqual(self.km["NCL"]["gain"], 1.072e-4, delta=1e-7)
        self.assertAlmostEqual(self.km["NCL"]["phase"], 1.430e-4, delta=1e-7)
        self.assertGreater(self.km["NCL"]["gain"], self.cs["tol_gain"])           # above tolerance: reported, would FAIL if judged
        self.assertLess(self.km["NCL"]["gain"], 10 * self.cs["tol_gain"])          # ... and below 10x: it could not be a control

    # ---- findings
    def test_findings(self):
        fd, fails = self.spec["findings"], []
        am = {p: R.us_article(p) for p in (10, 14, 20, 30)}
        got = dict(dc_gain_dev_max=max(abs(R.dc_gain(f) - 1.0) for f in am.values()),
                   nyquist_gain_max=max(abs(R._hz(f, math.pi)) for f in am.values()),
                   ramp_lag_abs_max=max(abs(R.ramp_lag(f)) for f in am.values()))
        for k, v in got.items():
            self.assertLess(fd[k], 1e-12, k)
            self.assertLess(v, 1e-12, k)
        for p, f in am.items():
            Ts = np.arange(4, 400.0001, 0.01)
            g = np.array([R.gain_at(f, t) for t in Ts])
            i = int(np.argmax(g))
            for k, v in (("peak_gain_P%d" % p, float(g[i])), ("peak_T_P%d" % p, float(Ts[i])),
                         ("phase_at_T_eq_P_P%d" % p, R.phase_at(f, p))):
                if not note("findings", fd[k], v):
                    fails.append(k)
        gm = max(abs(R.gain_at(R.us_article(p), t) - R.gain_at(R.us_code(p), t)) for p in am for t in TS)
        pm = max(abs(R.phase_at(R.us_article(p), t) - R.phase_at(R.us_code(p), t)) for p in am for t in TS)
        for k, v in (("floor_gain_analytic", gm), ("floor_phase_analytic", pm)):
            if not note("findings", fd[k], v):
                fails.append(k)
        s20 = self.x["s20"]
        d = float(np.max(np.abs(R.simulate(am[20], s20, seed="pass3") - R.simulate(am[20], s20, seed="pass4"))))
        if not note("findings", fd["startup_s20_pass3_vs_pass4"], d):
            fails.append("startup_s20_pass3_vs_pass4")
        self.assertEqual(fails, [])

    def test_findings_guard_fires(self):
        fd = self.spec["findings"]
        self.assertFalse(within(fd["peak_gain_P20"], R.gain_at(R.us_article(21), 25.63)))
        self.assertFalse(within(fd["floor_gain_analytic"] * 1.01, fd["floor_gain_analytic"]))

    # ---- IMP fire test
    def _maxdiff(self, a, b):
        return max(float(np.max(np.abs(a[i] - b[i]))) for i in C.input_names(self.cs))

    def _sim(self, model_str):
        m = R.IMP_MODELS[model_str]()
        return {i: R.simulate_any(m, self.x[i]) for i in C.input_names(self.cs)}

    def test_imp_fire_test(self):
        ft = self.spec["imp"]["fire_test"]
        p20 = self._sim("us_code(20, pass3)")
        got = {"P20 vs NCX model": (ft["p20_vs_ncx_model"], self._maxdiff(self.y["P20"], self._sim("us_nx(20)"))),
               "NCS vs P20 pass3 model": (ft["ncs_vs_p20_pass3_model"], self._maxdiff(self.y["NCS"], p20))}
        for v in ("NCL",) + CONTROLS:
            self.assertEqual(self._maxdiff(self.y[v], self._sim(self.spec["imp"]["must_pass"][v])), 0.0, v)      # own-model replay is 0
            got["variant " + v] = (ft["discrimination"][v], self._maxdiff(self.y[v], p20))
        fails = []
        for k, (stored, actual) in got.items():
            ok = note("imp_fire_test", stored, actual)
            print("  %-24s spec %-22.15g actual %-22.15g %s" % (k, stored, actual, "ok" if ok else "FAIL"))
            self.assertGreater(actual, 1e-9, "%s would not fire / discriminate" % k)
            if not ok:
                fails.append(k)
        self.assertEqual(len(got), 2 + 7)
        self.assertEqual(fails, [])
        self.assertLessEqual(self._maxdiff(self.y["P20"], p20), 0.0)                  # the real variant replays clean

    def test_imp_lists_and_registry(self):
        imp = self.spec["imp"]
        self.assertEqual(set(imp["must_pass"]), {v["id"] for v in self.spec["variants"]})
        self.assertEqual(imp["must_fail"], {"P20": "us_nx(20)", "NCS": "us_code(20, pass3)"})
        for tab in (imp["must_pass"], imp["must_fail"]):
            for vid, m in tab.items():
                self.assertIn(m, R.IMP_MODELS, m)
        self.assertEqual(len(set(imp["must_pass"].values())), 11)                          # every variant has its own model
        # the NCS must_fail model is NOT NCS's own must_pass model (same filter, other seed): the pair is what makes it fire
        self.assertNotEqual(imp["must_fail"]["NCS"], imp["must_pass"]["NCS"])


if __name__ == "__main__":
    unittest.main()
