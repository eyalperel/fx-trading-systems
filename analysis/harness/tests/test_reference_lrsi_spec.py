"""Pre-run condition (iii) for LRS: reference.py reproduces the numbers pre-registered in specs/LRSI_ArticleFidelity.toml.

Sections: expected tables, [floor] (+ per variant), every [variants.effect], [detect.required] (rule: exactly the kinds >= 10x their
tolerance), [imp.fire_test] (+ discrimination), every [findings] key, the D2 windows, variant / check counts, the text of the pass condition
and of the observations that quote a [findings] value.
Tolerance: <= 1e-9 absolute, relative 1e-9 for |value| > 1; every number in the spec is stored at full precision.
No .c file is read; Zorro is not run. Measurements use the checker's own functions (evaluate / _imp_lrsi / model_out).
A number the reference does not reproduce FAILS its test (never loosened to pass).
The comparison with the planning chat's numbers is in test_reference_lrsi (from the models, not from this file).
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lrs_support as S      # noqa: E402

C, R, G = S.C, S.R, S.G
TS = S.TS
TOL = 1e-9
DEV = {}
KINDS = ("gain", "phase", "lag", "flat", "trace", "invariance", "startup", "ramp_exact")


def dev(expected, actual):
    d = abs(actual - expected)
    return d / abs(expected) if abs(expected) > 1 else d


def note(section, expected, actual, tol=TOL):
    d = dev(expected, actual)
    DEV[section] = max(DEV.get(section, 0.0), d)
    return d <= tol


class TestLRSSpecNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()
        cls.rows, cls.nc = S.evaluated()
        cls.km = {v["id"]: S.kind_max(v["id"]) for v in cls.cs["variants"]}
        cls.tol = {k: cls.cs["tol_" + k] for k in KINDS + ("bound",)}
        cls.outs = S.own_model_outputs()

    @classmethod
    def tearDownClass(cls):
        print()
        for sec in ("expected", "floor", "effects", "findings", "imp_fire_test"):
            if sec in DEV:
                print("(iii) %-13s largest deviation %.3e" % (sec, DEV[sec]))

    def test_rule_fires(self):
        self.assertTrue(dev(0.5, 0.5 + 9e-10) <= TOL)
        self.assertFalse(dev(0.5, 0.5 + 2e-9) <= TOL)
        self.assertFalse(dev(31.0, 31.0 * (1 + 2e-9)) <= TOL)

    # ---- structure and counts
    def test_variants_and_counts(self):
        vs = self.spec["variants"]
        self.assertEqual([v["id"] for v in vs if v["role"] == "real"], list(S.REAL))
        self.assertEqual([v["id"] for v in vs if v["role"] == "neg_control"], list(S.CONTROLS))
        self.assertEqual([v["id"] for v in vs if v["role"] == "info"], list(S.INFO))
        for vid, p in S.REAL.items():
            self.assertEqual([v for v in vs if v["id"] == vid][0]["params"], [list(p)])
        real = [v for v in self.cs["variants"] if v["role"] == "real"]
        n = sum(C.n_checks(self.cs, v) for v in real)
        print("\n  real checks = %d (3 variants x %s)" % (n, sorted({C.n_checks(self.cs, v) for v in real})))
        self.assertEqual(n, 129)
        txt = self.spec["pass_condition"]["text"]
        for s in ("All 129 real checks PASS", "3 real + 4 negative controls + 2 info (NCH, NCT) = 9 variants",
                  "(9 variants), and the [imp].must_fail replay > 1e-9 (1 row", "no-static lint"):
            self.assertIn(s, txt)
        ch, tl = self.spec["checks"], self.spec["tolerances"]
        self.assertEqual((ch["dc_gain"], ch["trace_gate"], ch["bound"], ch["bound_output"], ch["linear_output"], ch["phase_gate"],
                          ch["ramp_exact"], ch["startup_output"], self.spec["inputs"]["warmup"]),
                         (1.0, 0.01, [0.0, 1.0], "out", ["l0", "l3"], 0.05, {"ramp": 1.0, "rampdn": 0.0}, True, 700))
        self.assertEqual({k: tl[k]["value"] for k in tl},
                         dict(flat=1e-9, gain=3e-5, phase=3e-5, lag=1e-3, trace=3e-5, startup=1e-6, ramp_exact=1e-12, bound=1e-12,
                              invariance=1e-9, x=1e-12, imp=1e-9))
        self.assertEqual(self.spec["imp"]["must_fail"], {"G05": "lrsi_article(1/2,g_l0=1/2+1/1000)"})
        self.assertEqual(self.spec["lint"]["no_static"], ["indicators/ehlers/LaguerreRSI.c"])

    # ---- expected tables
    def test_expected_tables(self):
        fails, n = [], 0
        for vid, (num, den) in S.REAL.items():
            g = num / den
            for st in (0, 3):
                e = self.spec["expected"]["%s_l%d" % (vid, st)]
                self.assertEqual(e["article"], "lrsi_article(%d/%d)" % (num, den))
                vals = [(gv, R.lrsi_gain(g, st, t)) for t, gv in zip(TS, e["gains"])] \
                    + [(e["phases"][str(t)], R.lrsi_phase(g, st, t)) for t in TS] \
                    + [(e["gain_alt"], R.lrsi_gain(g, st, 2)), (e["phase_alt"], R.lrsi_alt_phase(g, st)), (e["lag"], R.lrsi_lag(g, st))]
                for a, b in vals:
                    n += 1
                    if not note("expected", a, b):
                        fails.append((vid, st, a, b))
                self.assertEqual(e["flat"], 0.0)
                self.assertGreaterEqual(e["gain_alt"], self.spec["checks"]["phase_gate"])     # every alt phase checked (no SKIP)
        print("\n  expected tables: 6 x 13 = %d values, fails %s" % (n, fails))
        self.assertEqual(fails, [])

    def test_expected_table_guard_fires(self):
        g = self.spec["expected"]["G05_l3"]["phases"]["20"]
        self.assertFalse(note("guard", g, R.lrsi_phase(0.5, 2, 20)))
        self.assertFalse(note("guard", self.spec["expected"]["G08_l3"]["lag"], R.lrsi_lag(0.7, 3)))

    # ---- tolerance windows (D2 rule 3)
    def test_windows(self):
        fl = self.spec["floor"]
        for q in KINDS:
            self.assertLessEqual(fl[q] * 10, self.tol[q], q)
        errs, infos = G.validate_spec(self.spec)
        self.assertEqual(errs, [])
        self.assertEqual(len([i for i in infos if i.startswith("INFO D2 floor") and "window ok" in i]), 8)
        for i in infos:
            self.assertNotIn("EXCEEDS", i)
            if i.startswith("INFO D2 margin"):
                self.assertIn("10x margin met", i)

    # ---- floors
    def test_floors(self):
        fails = []
        for vid in S.REAL:
            pv = self.spec["floor"]["per_variant"][vid]
            self.assertEqual(sorted(pv), sorted(KINDS))
            for k in KINDS:
                if not note("floor", pv[k], self.km[vid][k]):
                    fails.append((vid, k, pv[k], self.km[vid][k]))
        for k in KINDS:
            self.assertTrue(note("floor", self.spec["floor"][k], max(self.spec["floor"]["per_variant"][v][k] for v in S.REAL)), k)
        self.assertEqual(fails, [])

    # ---- effects and the 10x rule
    def test_effects(self):
        fails, n = [], 0
        for v in self.spec["variants"]:
            if v["role"] == "real":
                continue
            self.assertEqual(sorted(k for k in v["effect"] if k != "source"), sorted(self.km[v["id"]]), v["id"])
            for k, val in v["effect"].items():
                if k == "source":
                    continue
                n += 1
                if not note("effects", val, self.km[v["id"]][k]):
                    fails.append((v["id"], k, val, self.km[v["id"]][k]))
        print("\n  effects: %d values over 6 variants, fails %s" % (n, fails))
        self.assertEqual(fails, [])

    def test_detect_required(self):
        req = self.spec["detect"]["required"]
        self.assertEqual(set(req), set(S.CONTROLS))
        for vid, kinds in req.items():
            eff = [v for v in self.spec["variants"] if v["id"] == vid][0]["effect"]
            ten = sorted(k for k, val in eff.items() if k != "source" and val / self.tol[k] >= 10.0)
            self.assertEqual(sorted(kinds), ten, vid)                         # exactly the kinds >= 10x (brief)
        self.assertEqual(req["NCS"], ["startup"])                             # Amendment 1 A
        ncg = [v for v in self.spec["variants"] if v["id"] == "NCG"][0]["effect"]
        print("\n  [detect.required]: tightest NCG trace %.1fx, gain %.1fx, phase %.1fx; NCG lag %.2fx (not required)"
              % (ncg["trace"] / 3e-5, ncg["gain"] / 3e-5, ncg["phase"] / 3e-5, ncg["lag"] / 1e-3))

    # ---- imp fire tests
    def test_imp_fire_test(self):
        ft = self.spec["imp"]["fire_test"]
        imp = {r["check_id"]: r for r in self.rows if r["role"] == "imp"}
        self.assertTrue(note("imp_fire_test", ft["g05_vs_ncg_model"], imp["LRS-G05-imp-fail"]["actual"]))
        disc = ft["discrimination"]
        self.assertEqual(set(disc), {v["id"] for v in self.spec["variants"]})
        base = R.lrsi_article(0.5)
        raw = S.synth_raw()
        for v in self.cs["variants"]:
            d = max(C._imp_lrsi(self.cs, raw, v, base, {}).values())
            self.assertTrue(note("imp_fire_test", disc[v["id"]], d), (v["id"], disc[v["id"]], d))
            if v["id"] in ("G05", "NCH", "NCP", "NCS", "NCT"):                 # O_IMP_ROWS: differ only in rows < W, or nowhere
                self.assertEqual(d, 0.0, v["id"])
            else:
                self.assertGreater(d, self.cs["imp"]["tol"], v["id"])
        self.assertNotIn("NCS", self.spec["imp"]["must_fail"])

    # ---- findings
    def test_findings(self):
        f, x, cs = self.spec["findings"], self.x, self.cs
        W, amp, slp = cs["w"], cs["amp"], cs["slope"]
        seen = set()

        def chk(key, value):
            seen.add(key)
            self.assertTrue(note("findings", f[key], value), (key, f[key], value))

        def mo(m, k):
            return C.model_out(m, x[k])

        for vid, (num, den) in S.REAL.items():
            g = num / den
            m = R.lrsi_article(g)
            chk("l3_minus_l0_gain_max_%s" % vid, max(abs(R.lrsi_gain(g, 3, t) - R.lrsi_gain(g, 0, t)) for t in TS + (2,)))
            chk("ramp_lag_theory_l0_%s" % vid, R.lrsi_lag(g, 0))
            chk("ramp_lag_theory_l3_%s" % vid, R.lrsi_lag(g, 3))
            a = mo(m, "ramp")
            chk("ramp_lag_measured_l0_%s" % vid, float(np.mean((x["ramp"][-100:] - a.l0[-100:]) / slp)))
            chk("ramp_lag_measured_l3_%s" % vid, float(np.mean((x["ramp"][-100:] - a.l3[-100:]) / slp)))
            sv = 0.0
            for k in C.base_names(cs):
                a = mo(m, k)
                sv = max(sv, float(np.max(np.abs(a.l0[W:] - R.simulate(R.lrsi_l0_filter(g), x[k], seed="zero")[W:]))),
                         float(np.max(np.abs(a.l3[W:] - R.simulate(R.lrsi_l3_filter(g), x[k], seed="zero")[W:]))))
            chk("stages_vs_filter_max_%s" % vid, sv)
            self.assertLessEqual(sv, 1e-12)
            chk("flat_l3_max_err_%s" % vid, float(np.max(np.abs(mo(m, "flat").l3[W:] - cs["level"]))))
            gm = []
            for t in TS:
                gm.append(float(np.min(mo(m, "s%d" % t).den[200:] / amp)))
                chk("gate_margin_%s_T%d" % (vid, t), gm[-1])
                o = mo(m, "s%d" % t).out[200:]
                chk("pinned_share_%s_T%d" % (vid, t), float(np.mean((o == 0) | (o == 1))))
            chk("gate_margin_%s_min" % vid, min(gm))
            chk("gate_margin_alt_%s" % vid, float(np.min(mo(m, "alt").den[200:] / amp)))
            mk = mf = 0.0
            for t in TS:
                b = mo(m, "s%d" % t).out
                mk = max(mk, float(np.max(np.abs(mo(m, "sc%d" % t).out[W:] - b[W:]))))
                mf = max(mf, float(np.max(np.abs(mo(m, "of%d" % t).out[W:] - b[W:]))))
            chk("invariance_scale10_%s" % vid, mk)
            chk("invariance_offset_%s" % vid, mf)
            md, lr = 0.0, -1
            for t in TS:
                d = np.abs(mo(m, "s%d" % t).out - mo(R.lrsi_article(g, seed="price"), "s%d" % t).out)
                md, lr = max(md, float(d.max())), max(lr, int(np.nonzero(d > 1e-12)[0].max()))
            chk("startup_memory_max_diff_%s" % vid, md)
            chk("startup_memory_last_row_%s" % vid, lr)
            chk("ramp_first_row_of_ones_%s" % vid, int(np.nonzero(mo(m, "ramp").out != 1.0)[0].max()) + 1)
            chk("rampdn_last_row_nonzero_%s" % vid, int(np.nonzero(mo(m, "rampdn").out != 0.0)[0].max()))
            o = mo(m, "alt").out[W:]
            chk("alt_out_min_%s" % vid, float(o.min()))
            chk("alt_out_max_%s" % vid, float(o.max()))
            chk("alt_out_distinct_%s" % vid, len(np.unique(o)))
            fl = mo(m, "flat")
            z = np.nonzero(fl.den == 0)[0]
            chk("flat_zero_den_rows_%s" % vid, len(z))
            if len(z):
                chk("flat_first_zero_den_row_%s" % vid, int(z.min()))
                chk("flat_held_value_%s" % vid, float(fl.out[z.min()]))
        allo = [mo(R.lrsi_article(n / d), k).out for (n, d) in S.REAL.values() for k in C.input_names(cs)]
        chk("out_min_all_real_all_rows", min(float(a.min()) for a in allo))
        chk("out_max_all_real_all_rows", max(float(a.max()) for a in allo))
        g05 = R.lrsi_article(0.5)
        for r_ in range(4):
            chk("startup_out_row%d_G05_T20" % r_, float(mo(g05, "s20").out[r_]))
        ctrl = {"NCG": R.lrsi_article(0.5, g_l0=0.5 + 1.0 / 1000), "NC25": R.lrsi_article(0.5, form="tasc2025"),
                "NCP": R.lrsi_article(0.5, seed="price"), "NCH": R.lrsi_article(0.5, hold0=0.5)}
        for c, m in ctrl.items():
            for t in TS:
                a, b = mo(m, "s%d" % t).out, mo(g05, "s%d" % t).out
                chk("effect_%s_trace_T%d" % (c, t), float(np.max(np.abs(a[W:] - b[W:]))))
                chk("effect_%s_startup_T%d" % (c, t), float(np.max(np.abs(a[:W] - b[:W]))))
        q = 0.5 + 1.0 / 1000
        chk("effect_NCG_gain_max_analytic", max(abs(R.lrsi_gain(q, 0, t) - R.lrsi_gain(0.5, 0, t)) for t in TS + (2,)))
        chk("effect_NCG_phase_max_analytic", max(abs(C.wrap_phase(R.lrsi_phase(q, 0, t) - R.lrsi_phase(0.5, 0, t))) for t in TS))
        chk("effect_NCG_lag_l0_analytic", R.lrsi_lag(q, 0))

        def h25(g, w):
            zi = np.exp(-1j * w)
            return (1 - g) / (1 - g * zi) * ((1 - g) * zi / (1 - g * zi)) ** 3
        chk("effect_NC25_l3_gain_max_analytic", max(abs(abs(h25(0.5, 2 * math.pi / t)) - R.lrsi_gain(0.5, 3, t)) for t in TS + (2,)))
        chk("effect_NC25_l3_phase_max_analytic",
            max(abs(C.wrap_phase(float(np.angle(h25(0.5, 2 * math.pi / t))) - R.lrsi_phase(0.5, 3, t))) for t in TS))
        chk("effect_NC25_lag_l3_analytic", 0.5 / 0.5 + 3 * (1 + 0.5 / 0.5))
        tab = {}
        for vid in ("NCS", "NCT"):                                             # the shared-statics replay in the actual call order
            v = [u for u in self.cs["variants"] if u["id"] == vid][0]
            for i in C.variant_inputs(self.cs, v):
                tab[(vid, i)] = np.abs(self.outs[vid]["out"][i] - mo(g05, i).out)
        d5 = tab[("NCS", "s5")]
        chk("ncs_startup_s5", float(d5[:W].max()))
        chk("ncs_startup_s5_last_row", int(np.nonzero(d5)[0].max()))
        chk("ncs_startup_s5_last_row_gt_1e12", int(np.nonzero(d5 > 1e-12)[0].max()))
        chk("ncs_max_diff_other_pairs", max(float(d.max()) for k, d in tab.items() if k != ("NCS", "s5")))
        chk("ncs_max_diff_rows_ge_W", max(float(d[W:].max()) for d in tab.values()))
        self.assertEqual(seen, set(f) - {"source"}, "every [findings] key is reproduced here")
        print("\n  findings: %d values reproduced" % len(seen))

    # ---- one value per quantity: the observations quote [findings]
    def test_observations_quote_the_findings(self):
        f, o = self.spec["findings"], self.spec["observations"]
        for vid in S.REAL:
            for t in TS:
                self.assertIn(repr(f["pinned_share_%s_T%d" % (vid, t)]), o["O_PIN"])
            self.assertIn(repr(f["gate_margin_%s_min" % vid]), o["O_GATE"])
            self.assertIn(repr(f["alt_out_min_%s" % vid]), o["O_ALT"])
        for k in ("ncs_startup_s5", "ncs_startup_s5_last_row_gt_1e12", "ncs_max_diff_other_pairs"):
            self.assertIn(repr(f[k]), o["O_NCS"], k)
        self.assertIn(repr(f["flat_first_zero_den_row_G05"]), o["O_HOLD"])
        for t in TS:
            self.assertIn(repr(f["effect_NCP_startup_T%d" % t]), o["O_NCP"])
        self.assertIn(repr(f["effect_NCG_gain_max_analytic"]), o["O_NCG"])
        self.assertIn(repr(f["startup_out_row1_G05_T20"]), o["O_STARTUP"])
        self.assertIn("restart zorro before any rerun", self.spec["run_notes"]["rerun"].lower())


if __name__ == "__main__":
    unittest.main()
