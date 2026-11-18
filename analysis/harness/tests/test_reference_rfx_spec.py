"""Pre-run condition (iii) for RFX: reference.py reproduces the numbers pre-registered in specs/RFX_ArticleFidelity.toml, and the spec
agrees with the planning chat's (b) numbers of docs/harness/RFX_STAGE1_PROMPT.md within the brief's reporting thresholds.

Sections: expected tables, [floor] (+ per variant), every [variants.effect], [detect.required] (rule: kind >= 10x its tolerance),
[imp.fire_test], [findings], the D2 windows, variant / check counts.
Tolerance: <= 1e-9 absolute, relative 1e-9 for |value| > 1; every number in the spec is stored at full precision.
No .c file is read; Zorro is not run. Measurements use the checker's own functions (check_rows / evaluate).
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
import rfx_support as S      # noqa: E402

C, R, G = S.C, S.R, S.G
TS = (5, 10, 20, 40, 100)
REAL = {"L14": 14, "L20": 20, "L21": 21, "L30": 30}
CONTROLS = ("NCA", "NC2", "NC1", "NCH", "NCK", "NCW", "NCS", "NCT")
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


class TestRFXSpecNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()
        cls.rows, cls.nc = S.evaluated()
        cls.km = {v["id"]: S.kind_max(v["id"]) for v in cls.cs["variants"]}
        cls.tol = {k: cls.cs["tol_" + k] for k in ("gain", "phase", "resid", "trace", "bound", "invariance")}
        cls.tol["flat"] = cls.cs["tol_flat"]

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
        self.assertEqual(len(vs), 13)
        real = [v for v in self.cs["variants"] if v["role"] == "real"]
        n = sum(C.n_checks(self.cs, v) for v in real)
        print("\n  real checks = %d (4 variants x %s)" % (n, sorted({C.n_checks(self.cs, v) for v in real})))
        self.assertEqual(n, 84)
        txt = self.spec["pass_condition"]["text"]
        self.assertIn("All 84 real checks PASS", txt)
        self.assertIn("4 real + 8 negative controls + 1 info (NCL) = 13 variants", txt)
        self.assertEqual({v["id"]: v["params"] for v in vs},
                         {"L14": [14], "L20": [20], "L21": [21], "L30": [30], "NCL": [20], "NCA": [20], "NC2": [20], "NC1": [22],
                          "NCH": [21], "NCK": [20], "NCW": [20], "NCS": [20], "NCT": [14]})
        self.assertEqual((self.spec["checks"]["dc_gain"], self.spec["checks"]["trace_gate"], self.spec["checks"]["bound"],
                          self.spec["inputs"]["warmup"]), (0.0, 0.01, 5.0, 700))
        self.assertEqual(self.spec["tolerances"]["trace"]["value"], 3e-5)
        self.assertEqual(self.spec["tolerances"]["bound"]["value"], 1e-12)
        self.assertEqual(self.spec["tolerances"]["invariance"]["value"], 1e-9)

    # ---- expected tables
    def test_expected_tables(self):
        fails = []
        for name, e in self.spec["expected"].items():
            L = REAL[name]
            f = R.reflex_sum_filter(L)
            self.assertEqual(e["article"], "reflex_article(%d)" % L)
            for t, g in zip(TS, e["gains"]):
                if not note("expected", g, R.gain_at(f, t)):
                    fails.append((name, "gain", t))
            for t in TS:
                if not note("expected", e["phases"][str(t)], R.phase_at(f, t)):
                    fails.append((name, "phase", t))
            if not note("expected", e["gain_alt"], R.gain_at(f, 2)):
                fails.append((name, "gain_alt"))
            self.assertEqual((e["flat"], e["resid"]), (0.0, 0.0))
            self.assertLess(abs(R.ramp_residual(f, 1.1, 1e-4)), 1e-15)
            self.assertNotIn("phase_alt", e)
            self.assertNotIn("lag", e)
            self.assertLess(e["gain_alt"], self.spec["checks"]["phase_gate"])
            self.assertGreaterEqual(min(e["gains"]), self.spec["checks"]["phase_gate"])
        print("\n  expected tables: 4 x (5 gains + 5 phases + alt gain) = 44 values, fails %s" % fails)
        self.assertEqual(fails, [])

    def test_expected_table_guard_fires(self):
        g = self.spec["expected"]["L20"]["gains"][2]
        self.assertFalse(within(g + 1e-6, R.gain_at(R.reflex_sum_filter(20), 20)))
        self.assertFalse(within(g, R.gain_at(R.reflex_sum_filter(21), 20)))

    def test_tables_agree_with_the_planning_chat_values(self):
        """The brief's (b) tables (finding 3) at 1e-13, in the spec's full-precision values."""
        import test_reference_rfx as T
        worst = 0.0
        for L, (g, p) in T.BRIEF.items():
            e = self.spec["expected"]["L%d" % L]
            for t, gv, pv in zip(TS, g, p):
                worst = max(worst, abs(e["gains"][TS.index(t)] - gv), abs(e["phases"][str(t)] - pv))
        print("\n  spec tables vs the planning chat's: max |diff| %.3e" % worst)
        self.assertLess(worst, 1e-13)

    # ---- tolerance windows (D2 rule 3)
    def test_windows_hold_with_the_default_tolerances(self):
        fl = self.spec["floor"]
        for q in ("gain", "phase", "resid", "trace", "invariance"):
            self.assertLessEqual(fl[q] * 10, self.tol[q], q)
        self.assertLessEqual(fl["flat"] * 10, self.tol["flat"])
        errs, infos = G.validate_spec(self.spec)
        self.assertEqual(errs, [])
        self.assertEqual(len([i for i in infos if i.startswith("INFO D2 floor") and "window ok" in i]), 6)
        for i in infos:
            self.assertNotIn("EXCEEDS", i)
            if i.startswith("INFO D2 margin"):
                self.assertIn("10x margin met", i)
        print("\n  floors x10 vs tolerances: gain %.3g<=3e-5, phase %.3g<=3e-5, trace %.3g<=3e-5, invariance %.3g<=1e-9"
              % (fl["gain"] * 10, fl["phase"] * 10, fl["trace"] * 10, fl["invariance"] * 10))

    # ---- floors
    def test_floors(self):
        fails = []
        for vid in REAL:
            pv = self.spec["floor"]["per_variant"][vid]
            for k in ("gain", "phase", "resid", "flat", "trace", "invariance"):
                if not note("floor", pv[k], self.km[vid][k]):
                    fails.append((vid, k))
        for k in ("gain", "phase", "resid", "flat", "trace", "invariance"):
            top = max(self.spec["floor"]["per_variant"][v][k] for v in REAL)
            self.assertTrue(note("floor", self.spec["floor"][k], top), k)
        self.assertEqual(fails, [])
        print("\n  floors: 4 variants x 6 kinds + 6 maxima")

    def test_floors_agree_with_the_planning_chat(self):
        """Finding 9 (gain / phase / trace per L, 4 digits): the brief's values."""
        brief = {"L14": (4.660e-07, 9.037e-07, 1.242e-06), "L20": (5.609e-07, 1.103e-06, 1.570e-06),
                 "L21": (5.296e-07, 1.101e-06, 1.554e-06), "L30": (5.380e-07, 1.003e-06, 1.435e-06)}
        for vid, (g, p, t) in brief.items():
            pv = self.spec["floor"]["per_variant"][vid]
            for got, want in ((pv["gain"], g), (pv["phase"], p), (pv["trace"], t)):
                self.assertLess(abs(got - want) / want, 1e-3, (vid, got, want))
            self.assertLessEqual(10 * max(pv["gain"], pv["phase"], pv["trace"]), 3e-5)

    # ---- effects and the 10x rule
    def test_effects(self):
        fails = []
        for v in self.spec["variants"]:
            if v["role"] == "real":
                continue
            eff = {k: x for k, x in v["effect"].items() if k != "source"}
            for k, val in eff.items():
                if not note("effects", val, self.km[v["id"]].get(k, float("nan"))):
                    fails.append((v["id"], k, val, self.km[v["id"]][k]))
        print("\n  effects: %d values over 9 variants, fails %s" % (sum(len(v["effect"]) - 1 for v in self.spec["variants"] if "effect" in v), fails))
        self.assertEqual(fails, [])

    def test_detect_required_kinds_have_10x_effect(self):
        for vid, kinds in self.spec["detect"]["required"].items():
            eff = [v for v in self.spec["variants"] if v["id"] == vid][0]["effect"]
            for k in kinds:
                self.assertGreaterEqual(eff[k] / self.tol[k], 10.0, (vid, k))
        # kinds NOT required are below 10x or structurally absent: NCK trace / phase, NCW gain / phase (finding NCK)
        self.assertLess(self.km["NCK"]["trace"] / self.tol["trace"], 1.0)
        self.assertLess(self.km["NCW"]["gain"] / self.tol["gain"], 1.0)
        self.assertEqual(set(self.spec["detect"]["required"]), set(CONTROLS))
        print("\n  [detect.required]: every listed kind >= 10x its tolerance (8 controls)")

    def test_effects_agree_with_the_planning_chat(self):
        """The brief's (b) effects: reporting threshold 1% relative (RFX_STAGE1_PROMPT.md, 'Planning-chat findings')."""
        brief = {"NCL": dict(gain=1.056e-04, phase=2.075e-04, trace=2.955e-04), "NCA": dict(gain=6.026e-04, phase=2.320e-03, trace=3.303e-03),
                 "NC2": dict(gain=1.710e-01, phase=1.858e-01, trace=2.647e-01), "NC1": dict(gain=2.399e-01, phase=1.323, trace=1.742),
                 "NCH": dict(gain=3.140e-02, phase=6.665e-02, trace=9.348e-02), "NCK": dict(gain=5.084820e-02), "NCW": dict(trace=5.096e-03)}
        for vid, d in brief.items():
            for k, want in d.items():
                got = self.km[vid][k]
                self.assertLess(abs(got - want) / want, 1e-2, (vid, k, got, want))
        self.assertLess(self.km["NCK"]["trace"], 1e-5)                         # normalisation cancels the scale error

    def test_ncs_effects_use_the_real_call_order(self):
        """NCS / NCT: shared MS across all 16 calls of a bar; the planning chat's pair-per-input numbers are reproduced separately."""
        self.assertAlmostEqual(self.km["NCS"]["trace"], self.spec["variants"][11]["effect"]["trace"], delta=1e-9)
        art = {L: {t: C.model_out(R.reflex_article(L), self.x["s%d" % t]) for t in TS} for L in (14, 20)}
        t20 = t14 = 0.0
        for t in TS:
            o = R.simulate_shared([20, 14], [self.x["s%d" % t], self.x["s%d" % t]])
            t20 = max(t20, float(np.max(np.abs(o[0].r[700:] - art[20][t].r[700:]))))
            t14 = max(t14, float(np.max(np.abs(o[1].r[700:] - art[14][t].r[700:]))))
        print("\n  NCS pair per input (planning chat structure): L20 %.4e L14 %.4e" % (t20, t14))
        self.assertLess(abs(t20 - 5.161e-01) / 5.161e-01, 1e-3)
        self.assertLess(abs(t14 - 1.142) / 1.142, 1e-3)
        self.assertTrue(note("effects", self.spec["findings"]["ncs_pair_per_input_trace_L20"], t20))
        self.assertGreater(self.km["NCS"]["trace"] / self.tol["trace"], 1e3)

    # ---- imp fire tests
    def test_imp_fire_test(self):
        ft = self.spec["imp"]["fire_test"]
        imp = {r["check_id"]: r for r in self.rows if r["role"] == "imp"}
        self.assertTrue(note("imp_fire_test", ft["l20_vs_ncw_model"], imp["RFX-L20-imp-fail"]["actual"]))
        self.assertTrue(note("imp_fire_test", ft["ncs_vs_l20_article_model"], imp["RFX-NCS-imp-fail"]["actual"]))
        disc = ft["discrimination"]
        base = R.reflex_code(20)
        raw = S.synth_raw()
        for v in self.cs["variants"]:
            per = C._imp_reflex(self.cs, raw, v, base, {})
            d = max(per.values())
            self.assertTrue(note("imp_fire_test", disc[v["id"]], d), v["id"])
            if v["id"] == "L20":
                self.assertEqual(d, 0.0)
            else:
                self.assertGreater(d, self.cs["imp"]["tol"], v["id"])                 # must_pass discriminates
        self.assertEqual(set(disc), {v["id"] for v in self.spec["variants"]})
        self.assertGreater(ft["l20_vs_ncw_model"], 1e-9)
        self.assertGreater(ft["ncs_vs_l20_article_model"], 1e-9)

    # ---- findings
    def test_findings(self):
        f = self.spec["findings"]
        x = self.x
        cs = self.cs
        W, amp = cs["w"], cs["amp"]
        seen = set()

        def chk(key, value):
            seen.add(key)
            self.assertTrue(note("findings", f[key], value), (key, f[key], value))

        for L in (14, 20, 21, 30):
            fl = R.reflex_sum_filter(L)
            g = p = 0.0
            for t in TS:
                o = C.model_out(R.reflex_article(L), x["s%d" % t])
                g = max(g, abs(C.m_gain(cs, o.sum, t) - R.gain_at(fl, t)))
                p = max(p, abs(C.wrap_phase(C.m_phase(cs, o.sum, t) - R.phase_at(fl, t))))
            chk("sum_vs_simulation_gain_L%d" % L, g)
            chk("sum_vs_simulation_phase_L%d" % L, p)
            chk("zerolag_phase_L%d" % L, R.phase_at(fl, L))
            chk("ss_half_phase_L%d" % L, R.phase_at(R.ss2_article(L / 2.0), L))
            chk("gate_margin_L%d" % L, float(min((np.sqrt(C.model_out(R.reflex_article(L), x["s%d" % t]).ms[W:]) / amp).min() for t in TS)))
        chk("dc_gain_dev_max", max(R.dc_gain(R.reflex_sum_filter(L)) for L in (14, 20, 21, 30)))
        chk("ramp_residual_abs_max", max(abs(R.ramp_residual(R.reflex_sum_filter(L), cs["level"], cs["slope"])) for L in (14, 20, 21, 30)))
        chk("nyquist_gain_max", max(R.gain_at(R.reflex_sum_filter(L), 2) for L in (14, 20, 21, 30)))
        chk("loop_end_terms_max", 0.0)
        dev_g = 0.0
        for L in (14, 20, 21, 30):
            z = np.exp(-1j * 2 * math.pi / L)
            dev_g = max(dev_g, float(abs((L - 1.0) / (2 * L) * (1 + z ** L) - sum(z ** k for k in range(1, L)) / L - 1)))
        chk("g_at_T_eq_L_dev", dev_g)
        o = C.model_out(R.reflex_article(20), x["ramp"])
        chk("ramp_max_abs_reflex_L20", float(np.max(np.abs(o.r[W:]))))
        chk("ramp_sum_row700_L20", float(o.sum[700]))
        chk("ramp_sqrt_ms_row700_L20", float(math.sqrt(o.ms[700])))
        chk("ramp_sqrt_ms_row1500_L20", float(math.sqrt(o.ms[1500])))
        chk("ramp_reflex_row1500_L20", float(o.r[1500]))
        chk("flat_max_abs_reflex_L20", float(np.max(np.abs(C.model_out(R.reflex_article(20), x["flat"]).r))))
        chk("bound_max_abs_all_rows", max(float(np.max(np.abs(C.model_out(R.reflex_article(L), x[k]).r)))
                                          for L in (14, 20, 21, 30) for k in C.base_names(cs)))
        chk("warmup_bars_1e12", math.log(1e-12) / math.log(0.96))
        tr = 0.0
        for t in TS:
            a = C.model_out(R.reflex_article(20), x["s%d" % t])
            b = R.simulate_reflex(R.reflex_article(20, w1=R.F32_004, w2=R.F32_096), x["s%d" % t])
            tr = max(tr, float(np.max(np.abs(a.r[W:] - b.r[W:]))))
        chk("float32_weights_trace_L20", tr)
        n = np.arange(cs["n_bars"], dtype=float)
        mk = mo = 0.0
        for t in TS:
            base_r = C.model_out(R.reflex_article(20), x["s%d" % t]).r
            xk = cs["level"] + 10 * cs["amp"] * np.sin(2 * math.pi * n / t)
            xo = 2.2 + cs["amp"] * np.sin(2 * math.pi * n / t)
            mk = max(mk, float(np.max(np.abs(R.simulate_reflex(R.reflex_article(20), xk).r[W:] - base_r[W:]))))
            mo = max(mo, float(np.max(np.abs(R.simulate_reflex(R.reflex_article(20), xo).r[W:] - base_r[W:]))))
        chk("invariance_scale10_L20", mk)
        chk("invariance_offset_L20", mo)
        bn = [r for r in self.rows if r["check_id"] == "RFX-NCS-bound"][0]
        chk("bound_ncs_max_abs_r", bn["actual"])
        chk("bound_float32_weights_analytic", 1.0 / math.sqrt(R.F32_004))
        art = {L: {t: C.model_out(R.reflex_article(L), x["s%d" % t]) for t in TS} for L in (14, 20)}
        t20 = t14 = 0.0
        for t in TS:
            o2 = R.simulate_shared([20, 14], [x["s%d" % t], x["s%d" % t]])
            t20 = max(t20, float(np.max(np.abs(o2[0].r[W:] - art[20][t].r[W:]))))
            t14 = max(t14, float(np.max(np.abs(o2[1].r[W:] - art[14][t].r[W:]))))
        chk("ncs_pair_per_input_trace_L20", t20)
        chk("ncs_pair_per_input_trace_L14", t14)
        self.assertEqual(seen, set(f) - {"source"}, "every [findings] key is reproduced here")
        print("\n  findings: %d values reproduced" % len(seen))

    def test_findings_match_the_planning_chat_thresholds(self):
        f = self.spec["findings"]
        self.assertLessEqual(f["sum_vs_simulation_gain_L20"], 1.3e-14 * 1.01)
        self.assertLessEqual(f["sum_vs_simulation_phase_L20"], 1.6e-14)
        self.assertAlmostEqual(f["ramp_max_abs_reflex_L20"], 2.857, places=3)
        self.assertAlmostEqual(f["ramp_sqrt_ms_row700_L20"], 1.3e-10, delta=0.05e-10)
        self.assertAlmostEqual(f["ramp_sqrt_ms_row1500_L20"], 1.4e-16, delta=0.1e-16)
        self.assertEqual(f["flat_max_abs_reflex_L20"], 0.0)
        self.assertAlmostEqual(f["bound_max_abs_all_rows"], 5.0, places=6)
        for L, want in ((14, 0.0370), (20, 0.0741), (21, 0.0814), (30, 0.0715)):
            self.assertAlmostEqual(f["gate_margin_L%d" % L], want, places=4)
        self.assertAlmostEqual(f["warmup_bars_1e12"], 676.87, places=2)
        self.assertAlmostEqual(f["float32_weights_trace_L20"], 4.424e-07, delta=0.001e-07)
        self.assertAlmostEqual(f["invariance_scale10_L20"], 7.040e-13, delta=0.001e-13)
        self.assertAlmostEqual(f["invariance_offset_L20"], 1.180e-12, delta=0.001e-12)
        for L, want in ((14, -0.5798402196411705), (20, -0.6223438049722935), (21, -0.6276271518404849), (30, -0.66162649242601)):
            self.assertAlmostEqual(f["zerolag_phase_L%d" % L], want, places=12)
            self.assertAlmostEqual(f["zerolag_phase_L%d" % L], f["ss_half_phase_L%d" % L], places=12)


if __name__ == "__main__":
    unittest.main()
