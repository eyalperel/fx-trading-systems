"""Pre-run condition (iii) for MST: reference.py reproduces the numbers pre-registered in specs/MESA_ArticleFidelity.toml.

Sections: expected tables, [floor] (+ per variant), every [variants.effect], [detect.required] (rule: kind >= 10x its tolerance),
[imp.fire_test] (+ discrimination), every [findings] key, the D2 windows, variant / check counts, the text of the pass condition and
of the observations that quote a [findings] value (one value per quantity).
Tolerance: <= 1e-9 absolute, relative 1e-9 for |value| > 1; every number in the spec is stored at full precision.
No .c file is read; Zorro is not run. Measurements use the checker's own functions (check_rows / evaluate / _imp_mesa).
A number the reference does not reproduce FAILS its test (never loosened to pass).
Each section prints "(iii) <section>: largest deviation ..." for the amendment record.
The comparison with the planning chat's numbers is in test_reference_mst (from the models, not from this file).
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mst_support as S      # noqa: E402

C, R, G = S.C, S.R, S.G
TS = S.TS
TOL = 1e-9
DEV = {}


def dev(expected, actual):
    d = abs(actual - expected)
    return d / abs(expected) if abs(expected) > 1 else d


def note(section, expected, actual, tol=TOL):
    d = dev(expected, actual)
    DEV[section] = max(DEV.get(section, 0.0), d)
    return d <= tol


class TestMSTSpecNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()
        cls.rows, cls.nc = S.evaluated()
        cls.km = {v["id"]: S.kind_max(v["id"]) for v in cls.cs["variants"]}
        cls.tol = {k: cls.cs["tol_" + k] for k in ("gain", "phase", "resid", "trace", "bound", "invariance", "flat")}

    @classmethod
    def tearDownClass(cls):
        print()
        for sec in ("expected", "floor", "effects", "findings", "imp_fire_test"):
            if sec in DEV:
                print("(iii) %-13s largest deviation %.3e" % (sec, DEV[sec]))

    def test_rule_fires(self):
        self.assertTrue(dev(0.5, 0.5 + 9e-10) <= TOL)
        self.assertFalse(dev(0.5, 0.5 + 2e-9) <= TOL)
        self.assertFalse(dev(101.85, 101.85 * (1 + 2e-9)) <= TOL)
        print("\n  [fire] comparison rule: 2e-9 abs / 2e-9 rel rejected, 9e-10 accepted")

    # ---- structure and counts
    def test_variants_and_counts(self):
        vs = self.spec["variants"]
        self.assertEqual([v["id"] for v in vs if v["role"] == "real"], list(S.REAL))
        self.assertEqual([v["id"] for v in vs if v["role"] == "neg_control"], list(S.CONTROLS))
        self.assertEqual([v["id"] for v in vs if v["role"] == "info"], list(S.INFO))
        for vid, p in S.REAL.items():
            self.assertEqual([v for v in vs if v["id"] == vid][0]["params"], list(p))
        real = [v for v in self.cs["variants"] if v["role"] == "real"]
        n = sum(C.n_checks(self.cs, v) for v in real)
        print("\n  real checks = %d (4 variants x %s)" % (n, sorted({C.n_checks(self.cs, v) for v in real})))
        self.assertEqual(n, 84)
        txt = self.spec["pass_condition"]["text"]
        self.assertIn("All 84 real checks PASS", txt)
        self.assertIn("4 real + 5 negative controls + 2 info (NCL, NCZ) = 11 variants", txt)
        self.assertIn("(10 rows: 4 real, 2 info, 4 controls) is SKIP", txt)
        self.assertEqual(sum(r["result"] == "SKIP" for r in self.rows), 10)
        ch, tl = self.spec["checks"], self.spec["tolerances"]
        self.assertEqual((ch["dc_gain"], ch["trace_gate"], ch["bound"], ch["bound_output"], ch["linear_output"], ch["phase_gate"],
                          self.spec["inputs"]["warmup"]), (0.0, 0.01, [0.0, 1.0], "stoc", "roof", 0.05, 700))
        self.assertEqual({k: tl[k]["value"] for k in tl},
                         dict(flat=1e-9, gain=3e-5, phase=3e-5, resid=1e-9, trace=5e-5, bound=1e-12, invariance=1e-9, x=1e-12, imp=1e-9))

    # ---- expected tables
    def test_expected_tables(self):
        fails = []
        for name, e in self.spec["expected"].items():
            hp, ss = S.REAL[name][1:]
            f = R.roof_article(hp, ss)
            self.assertEqual(e["article"], "mesa_article(%d,%d,%d)" % S.REAL[name])
            for t, g in zip(TS, e["gains"]):
                if not note("expected", g, R.gain_at(f, t)):
                    fails.append((name, "gain", t))
            for t in TS:
                if not note("expected", e["phases"][str(t)], R.phase_at(f, t)):
                    fails.append((name, "phase", t))
            if not note("expected", e["gain_alt"], R.gain_at(f, 2)):
                fails.append((name, "gain_alt"))
            self.assertEqual((e["flat"], e["resid"]), (0.0, 0.0))
            self.assertNotIn("phase_alt", e)
            self.assertLess(e["gain_alt"], self.spec["checks"]["phase_gate"])
            self.assertGreaterEqual(min(e["gains"]), self.spec["checks"]["phase_gate"])
        print("\n  expected tables: 4 x (5 gains + 5 phases + alt gain) = 44 values, fails %s" % fails)
        self.assertEqual(fails, [])

    def test_expected_table_guard_fires(self):
        g = self.spec["expected"]["L20"]["gains"][2]
        self.assertFalse(note("guard", g + 1e-6, R.gain_at(R.roof_article(48, 10), 20)))
        self.assertFalse(note("guard", g, R.gain_at(R.roof_article(48, 20), 20)))

    # ---- tolerance windows (D2 rule 3)
    def test_windows(self):
        fl = self.spec["floor"]
        for q in ("gain", "phase", "resid", "trace", "invariance", "flat"):
            self.assertLessEqual(fl[q] * 10, self.tol[q], q)
        self.assertGreater(fl["trace"] * 10, 3e-5)              # why this spec departs from the D6 default (D2 rule 1)
        errs, infos = G.validate_spec(self.spec)
        self.assertEqual(errs, [])
        self.assertEqual(len([i for i in infos if i.startswith("INFO D2 floor") and "window ok" in i]), 6)
        for i in infos:
            self.assertNotIn("EXCEEDS", i)
            if i.startswith("INFO D2 margin"):
                self.assertIn("10x margin met", i)

    # ---- floors
    def test_floors(self):
        fails = []
        kinds = ("gain", "phase", "resid", "flat", "trace", "invariance")
        for vid in S.REAL:
            pv = self.spec["floor"]["per_variant"][vid]
            for k in kinds:
                if not note("floor", pv[k], self.km[vid][k]):
                    fails.append((vid, k, pv[k], self.km[vid][k]))
        for k in kinds:
            self.assertTrue(note("floor", self.spec["floor"][k], max(self.spec["floor"]["per_variant"][v][k] for v in S.REAL)), k)
        self.assertEqual(fails, [])

    # ---- effects and the 10x rule
    def test_effects(self):
        fails, n = [], 0
        for v in self.spec["variants"]:
            if v["role"] == "real":
                continue
            for k, val in v["effect"].items():
                if k == "source":
                    continue
                n += 1
                if not note("effects", val, self.km[v["id"]].get(k, float("nan"))):
                    fails.append((v["id"], k, val, self.km[v["id"]].get(k)))
        print("\n  effects: %d values over 7 variants, fails %s" % (n, fails))
        self.assertEqual(fails, [])

    def test_detect_required(self):
        req = self.spec["detect"]["required"]
        self.assertEqual(set(req), set(S.CONTROLS))
        for vid, kinds in req.items():
            eff = [v for v in self.spec["variants"] if v["id"] == vid][0]["effect"]
            for k in kinds:
                self.assertGreaterEqual(eff[k] / self.tol[k], 10.0, (vid, k))
            for k, val in eff.items():                                   # kinds not listed are below 10x
                if k != "source" and k not in kinds:
                    self.assertLess(val / self.tol[k], 10.0, (vid, k))
        nca = [v for v in self.spec["variants"] if v["id"] == "NCA"][0]["effect"]["trace"] / self.tol["trace"]
        print("\n  [detect.required]: every listed kind >= 10x (tightest NCA trace %.1fx)" % nca)
        self.assertLess(nca, 20.0)

    # ---- imp fire tests
    def test_imp_fire_test(self):
        ft = self.spec["imp"]["fire_test"]
        imp = {r["check_id"]: r for r in self.rows if r["role"] == "imp"}
        self.assertTrue(note("imp_fire_test", ft["l20_vs_nca_model"], imp["MST-L20-imp-fail"]["actual"]))
        self.assertTrue(note("imp_fire_test", ft["ncs_vs_l20_article_model"], imp["MST-NCS-imp-fail"]["actual"]))
        disc = ft["discrimination"]
        self.assertEqual(set(disc), {v["id"] for v in self.spec["variants"]})
        base = R.mesa_code(20, 48, 10)
        raw = S.synth_raw()
        for v in self.cs["variants"]:
            d = max(C._imp_mesa(self.cs, raw, v, base).values())
            self.assertTrue(note("imp_fire_test", disc[v["id"]], d), (v["id"], disc[v["id"]], d))
            if v["id"] in ("L20", "NCZ"):                       # L20 itself; NCZ differs in rows < 60 only (O_NCZ_IMP)
                self.assertEqual(d, 0.0, v["id"])
            else:
                self.assertGreater(d, self.cs["imp"]["tol"], v["id"])
        self.assertEqual(self.spec["imp"]["must_fail"], {"L20": "mesa_code(20,48,10,da_final=1/1000)", "NCS": "mesa_article(20,48,10)"})

    # ---- findings
    def test_findings(self):
        f, x, cs = self.spec["findings"], self.x, self.cs
        W, amp = cs["w"], cs["amp"]
        seen = set()

        def chk(key, value):
            seen.add(key)
            self.assertTrue(note("findings", f[key], value), (key, f[key], value))

        def mo(m, k):
            return C.model_out(m, x[k])

        for hp, ss in ((48, 10), (48, 20)):
            a, c = R.roof_article(hp, ss), R.roof_code(hp, ss)
            chk("roof_pi_floor_gain_%d_%d" % (hp, ss), max(abs(R.gain_at(a, t) - R.gain_at(c, t)) for t in TS))
            chk("roof_pi_floor_phase_%d_%d" % (hp, ss), max(abs(R.phase_at(a, t) - R.phase_at(c, t)) for t in TS))
        chk("roof_T20_gain_minus_project_state", R.gain_at(R.roof_article(48, 10), 20) - 0.8900165495219391)
        chk("roof_dc_gain_max", max(abs(R.dc_gain(R.roof_article(48, s))) for s in (10, 20)))
        chk("roof_ramp_residual_abs_max", max(abs(R.ramp_residual(R.roof_article(48, s), cs["level"], cs["slope"])) for s in (10, 20)))
        chk("roof_nyquist_gain_max", max(R.gain_at(R.roof_article(48, s), 2) for s in (10, 20)))
        gmins, fmaxs = [], []
        for vid, p in S.REAL.items():
            fl, gm = [], []
            for t in TS:
                a, c = mo(R.mesa_article(*p), "s%d" % t), mo(R.mesa_code(*p), "s%d" % t)
                fl.append(float(np.max(np.abs(a.out[W:] - c.out[W:]))))
                gm.append(float(np.min(a.rng[W:] / amp)))
                chk("trace_floor_%s_T%d" % (vid, t), fl[-1])
                chk("gate_margin_%s_T%d" % (vid, t), gm[-1])
            chk("gate_margin_%s_min" % vid, min(gm))
            chk("trace_floor_%s_max" % vid, max(fl))
            gmins.append(min(gm))
            fmaxs.append(max(fl))
            mk = mf = 0.0
            for t in TS:
                b = mo(R.mesa_article(*p), "s%d" % t).out
                mk = max(mk, float(np.max(np.abs(mo(R.mesa_article(*p), "sc%d" % t).out[W:] - b[W:]))))
                mf = max(mf, float(np.max(np.abs(mo(R.mesa_article(*p), "of%d" % t).out[W:] - b[W:]))))
            chk("invariance_scale10_%s" % vid, mk)
            chk("invariance_offset_%s" % vid, mf)
        chk("gate_margin_min_all", min(gmins))
        chk("trace_floor_max_all", max(fmaxs))
        st = [mo(R.mesa_article(*p), k).stoc for p in S.REAL.values() for k in C.base_names(cs)]
        chk("stoc_min_all_real_all_rows", min(float(s.min()) for s in st))
        chk("stoc_max_all_real_all_rows", max(float(s.max()) for s in st))
        for t in (40, 100):
            o = mo(R.mesa_article(20, 48, 10), "s%d" % t).out[W:]
            chk("out_min_L20_T%d" % t, float(o.min()))
            chk("out_max_L20_T%d" % t, float(o.max()))
        a = mo(R.mesa_article(20, 48, 10), "s20")
        for r in range(4):
            chk("startup_out_row%d_L20_T20" % r, float(a.out[r]))
            chk("startup_stoc_row%d_L20_T20" % r, float(a.stoc[r]))
        md, lr = 0.0, -1
        for t in TS:
            d = np.abs(mo(R.mesa_article(20, 48, 10), "s%d" % t).out - mo(R.mesa_article(20, 48, 10, final_seed="zero"), "s%d" % t).out)
            md, lr = max(md, float(d.max())), max(lr, int(np.nonzero(d > 1e-12)[0].max()))
        chk("final_seed_max_diff_L20", md)
        chk("final_seed_last_row_gt_1e12", lr)
        ctrl = {"NCL": R.mesa_article(20, 48, 10, literals="printed"), "NCA": R.mesa_article(20, 48, 10, da_final=1.0 / 1000),
                "NCP": R.mesa_article(20, 40, 10), "NC1": R.mesa_article(22, 48, 10),
                "NCS": R.mesa_article(20, 48, 10, win=21, scale=100.0, fallback=50.0)}
        for t in TS:
            b = mo(R.mesa_article(20, 48, 10), "s%d" % t).out
            chk("window_ncw_article_T%d" % t, float(np.max(np.abs(mo(R.mesa_article(20, 48, 10, win=21), "s%d" % t).out[W:] - b[W:]))))
            for k, m in ctrl.items():
                chk("effect_article_%s_T%d" % (k, t), float(np.max(np.abs(mo(m, "s%d" % t).out[W:] - b[W:]))))
        chk("stoc_max_ncs_model_all_inputs", max(float(mo(R.mesa_superseded(20, 48, 10), k).stoc.max()) for k in C.base_names(cs)))
        self.assertEqual(seen, set(f) - {"source"}, "every [findings] key is reproduced here")
        print("\n  findings: %d values reproduced" % len(seen))

    # ---- one value per quantity: the observations quote [findings] (fixed 2026-11-19)
    def test_observations_quote_the_findings(self):
        f, o = self.spec["findings"], self.spec["observations"]
        for t in TS:
            self.assertIn(repr(f["window_ncw_article_T%d" % t]), o["O_WINDOW"])
        for t in (40, 100):
            for k in ("out_min_L20_T%d" % t, "out_max_L20_T%d" % t):
                self.assertIn(repr(f[k]), o["O_OUTPUT_UNBOUNDED"], k)
        ncl = [v for v in self.spec["variants"] if v["id"] == "NCL"][0]["effect"]
        for k in ("gain", "phase", "trace"):
            self.assertIn(repr(ncl[k]), o["O_NCL"], k)
        self.assertIn(repr(f["stoc_max_ncs_model_all_inputs"]), o["O_NCS_BOUND"])
        for k in ("final_seed_max_diff_L20", "startup_out_row1_L20_T20"):
            self.assertIn(repr(f[k]), o["O_STARTUP"])


if __name__ == "__main__":
    unittest.main()
