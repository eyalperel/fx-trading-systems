"""MAF stage 1: the checker's D7 path on the two specs, with synthetic raw files (a perfect run = every variant's own [imp].must_pass model,
tests/maf_support.synth_raw). Every new check is seen to fire on a deliberately broken input and to stay quiet where it must (CLAUDE.md
4.4): bars inputs and their guard, trace from row 1 with the per-(input, column) INFO classification, the conditioning classifier (fixed
seed, reproduces the spec's lists; a changed list is reported), equivariance (fires on a 1e-8 affine error, respects W_eq), hull (fires on
one row out by 1e-12), per-column bounds with a first row and a relative allowance, the FRAMA known answers (ramp_exact, lag, flat), the
D7 IMP (INFO pairs reported but never deciding; per-column tolerance), the floor guard per column group, and the verdict.
No .c file is read, Zorro is not run. Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import maf_support as S      # noqa: E402

C, R = S.C, S.R
MAMA, FRAMA = S.MAMA_SPEC, S.FRAMA_SPEC


def run(path, edit=None, raw_edit=None):
    """(rows by check id, nc, verdict ok, counts) of the checker on the own-model raw file, after `edit(outs)` on a deep copy of the
    own-model outputs and `raw_edit(raw)` on the Raw object."""
    _, cs, _, _ = S.load(path)
    outs = copy.deepcopy(S.own_model_outputs(path))
    if edit:
        edit(outs)
    raw = S.synth_raw(path, outs)
    if raw_edit:
        raw_edit(raw)
    errs = C.validate(cs, raw)
    if errs:
        return None, None, False, errs
    rows, nc = C.evaluate(cs, raw)
    ok, c = C.verdict(cs, rows, nc, [])
    return {r["check_id"]: r for r in rows}, nc, ok, c


def bump(vid, col, inp, n, d):
    def f(outs):
        outs[vid][col][inp][n] += d
    return f


class TestPerfectRun(unittest.TestCase):
    def test_01_mama_verdict_and_counts(self):
        rows, nc, ok, c = run(MAMA)
        self.assertTrue(ok)
        self.assertEqual(c, dict(n_real=66, n_pass=66, n_fail=0, n_err=0))
        real = [r for r in rows.values() if r["role"] == "real"]
        for vid in ("MA05", "MA03"):
            k = [C._kind(r["check_id"]) for r in real if r["check_id"].startswith("MAM-%s-" % vid)]
            self.assertEqual({q: k.count(q) for q in set(k)}, {"trace": 21, "bound": 2, "equivariance": 10})
            info = [r for r in rows.values() if r["check_id"].startswith("MAM-%s-info-" % vid)]
            self.assertEqual(len(info), 15)                                       # 14 INFO trace pairs + info-flat
            self.assertTrue(all(r["result"] == "INFO" for r in info))
        self.assertIn("MAM-MA05-trace-period-s5", rows)                          # s5 period is CHECKED (pass condition item 1)
        self.assertIn("MAM-MA05-info-trace-phase-s5", rows)
        self.assertNotIn("MAM-NCH-info-trace-phase-s5", rows)                    # controls get no INFO rows
        self.assertTrue(all(d["fails_as_required"] for d in nc.values()))
        self.assertEqual(sorted(nc), sorted(["NCB", "NCH", "NCF", "NC32", "NCP", "NCS", "NCS2"]))
        self.assertEqual(nc["NCB"]["required"], ["trace"])                       # NCB is a control (stage 1 review)
        ncb_fail = [k for k, r in rows.items() if k.startswith("MAM-NCB-trace-") and r["result"] == "FAIL"]
        self.assertEqual(ncb_fail, ["MAM-NCB-trace-period-s5"])                  # seen only on the checked pair s5 period

    def test_02_frama_verdict_and_counts(self):
        rows, nc, ok, c = run(FRAMA)
        self.assertTrue(ok)
        self.assertEqual(c, dict(n_real=98, n_pass=98, n_fail=0, n_err=0))
        for vid in ("FR16", "FR32"):
            k = [C._kind(r["check_id"]) for r in rows.values() if r["role"] == "real" and r["check_id"].startswith("FRA-%s-" % vid)]
            self.assertEqual({q: k.count(q) for q in set(k)},
                             {"trace": 37, "bound": 2, "hull": 1, "ramp_exact": 1, "lag": 1, "flat": 1, "equivariance": 6})
            self.assertEqual(sorted(r["check_id"] for r in rows.values() if r["check_id"].startswith("FRA-%s-info-" % vid)),
                             ["FRA-%s-info-trace-alpha-flat" % vid, "FRA-%s-info-trace-dim-flat" % vid])
        self.assertTrue(all(d["fails_as_required"] for d in nc.values()))


class TestBarsAndGuards(unittest.TestCase):
    def test_01_point_band_and_copies(self):
        _, cs, x, bars = S.load(FRAMA)
        h = 2 / 1000
        for i in ("flat", "s20", "ramp"):
            self.assertIs(bars[i][0], x[i])
            self.assertIs(bars[i][1], x[i])
        np.testing.assert_array_equal(bars["s40B"][0], x["s40B"] + h)
        np.testing.assert_array_equal(bars["s40B"][1], x["s40B"] - h)
        np.testing.assert_array_equal(x["s40B"], x["s40"])
        np.testing.assert_array_equal(x["sc40B"], 10.0 * x["s40B"] + (-99 / 10))
        np.testing.assert_array_equal(bars["sc40B"][0], 10.0 * (x["s40B"] + h) + (-99 / 10))      # High mapped, not x' + 10h
        np.testing.assert_array_equal(bars["of40B"][1], 1.0 * (x["s40B"] - h) + 11 / 10)
        self.assertEqual([c for c in C.header_of(cs) if c.startswith("xh_")],
                         ["xh_" + i for i in ("rampB", "s5B", "s10B", "s20B", "s40B", "s100B", "sc40B", "of40B")])
        _, cm, xm, _ = S.load(MAMA)
        self.assertFalse([c for c in C.header_of(cm) if c.startswith(("xh_", "xl_"))])
        np.testing.assert_array_equal(xm["sc40"], 10.0 * xm["s40"] - 9.9)

    def test_02_guard_fires_on_x_high_low(self):
        for path, col in ((FRAMA, "xh_s20B"), (FRAMA, "xl_sc40B"), (FRAMA, "x_rampB"), (MAMA, "x_of40")):
            def e(raw, col=col):
                raw.cols[col] = raw.cols[col].copy()
                raw.cols[col][100] += 1e-11
            _, _, ok, errs = run(path, raw_edit=e)
            self.assertFalse(ok)
            self.assertEqual([g for g, m in errs], ["G_INPUT_MISMATCH"], col)
            self.assertIn(col, errs[0][1])


class TestTraceAndConditioning(unittest.TestCase):
    def test_01_trace_from_row_one(self):
        rows, _, ok, _ = run(MAMA, bump("MA05", "alpha", "s20", 0, 2e-9))          # row n = 0 counts (no W cut)
        self.assertFalse(ok)
        self.assertEqual(rows["MAM-MA05-trace-alpha-s20"]["result"], "FAIL")
        rows, _, ok, _ = run(MAMA, bump("MA05", "phase", "s20", 0, 5e-9))         # phase has its own tolerance 1e-8
        self.assertEqual(rows["MAM-MA05-trace-phase-s20"]["result"], "PASS")
        self.assertEqual(rows["MAM-MA05-trace-phase-s20"]["tolerance"], 1e-8)
        rows, _, ok, _ = run(FRAMA, bump("FR32", "dim", "s5B", 0, 2e-10))
        self.assertEqual(rows["FRA-FR32-trace-dim-s5B"]["result"], "FAIL")

    def test_02_info_pairs_never_decide(self):
        rows, _, ok, c = run(MAMA, bump("MA05", "phase", "flat", 2000, 90.0))
        self.assertEqual(rows["MAM-MA05-info-trace-phase-flat"]["result"], "INFO")
        self.assertEqual(rows["MAM-MA05-info-trace-phase-flat"]["abs_diff"], 90.0)
        self.assertNotIn("MAM-MA05-trace-phase-flat", rows)
        rows, _, ok2, _ = run(FRAMA, bump("FR16", "dim", "flat", 5, 1.0))
        self.assertEqual(rows["FRA-FR16-info-trace-dim-flat"]["result"], "INFO")
        rows, _, ok3, _ = run(FRAMA, bump("FR16", "out", "flat", 5, 1e-9))       # out on point flat is CHECKED
        self.assertEqual(rows["FRA-FR16-trace-out-flat"]["result"], "FAIL")
        self.assertFalse(ok3)

    def test_03_classifier_reproduces_the_spec_and_fires(self):
        for path in (MAMA, FRAMA):
            _, cs, _, _ = S.load(path)
            rec = C.conditioning_table(cs)
            self.assertEqual(C.conditioning_mismatches(cs, rec), [])
            again = C.conditioning_table(cs)                                       # deterministic
            self.assertEqual(again[0], rec[0])
            for t, vals in rec[0].items():                                          # spec values reproduced
                for i, cv in vals.items():
                    for col, v in cv.items():
                        self.assertEqual(v, cs["adaptive"]["tables"][t]["values"][i][col], (t, i, col))
            bad = copy.deepcopy(cs)
            t0 = cs["adaptive"]["real_tables"][0]
            bad["adaptive"]["tables"][t0]["info"] = {i: l for i, l in bad["adaptive"]["tables"][t0]["info"].items() if i != "flat"}
            self.assertEqual(len(C.conditioning_mismatches(bad, rec)), 1)
            moved = copy.deepcopy(cs)
            moved["adaptive"]["conditioning"]["seed"] += 1                          # another draw: values change
            self.assertNotEqual(C.conditioning_table(moved)[0][t0]["s100"], rec[0][t0]["s100"])


class TestEquivariance(unittest.TestCase):
    def test_01_fires_on_a_1e8_affine_error(self):
        rows, _, ok, _ = run(MAMA, bump("MA05", "fama", "sc40", 1500, 1e-8))
        self.assertFalse(ok)
        r = rows["MAM-MA05-equiv-sc-fama"]
        self.assertEqual(r["result"], "FAIL")
        self.assertGreaterEqual(r["ratio"], 9.9)
        rows, _, ok, _ = run(MAMA, bump("MA03", "alpha", "of40", 1200, 1e-8))      # adaptation column: copy = base
        self.assertEqual(rows["MAM-MA03-equiv-of-alpha"]["result"], "FAIL")
        rows, _, ok, _ = run(FRAMA, bump("FR16", "out", "sc40B", 0, 1e-8))         # FRAMA: from row 1 (n = 0)
        self.assertEqual(rows["FRA-FR16-equiv-sc-out"]["result"], "FAIL")
        rows, _, ok, _ = run(FRAMA, bump("FR32", "dim", "of40B", 7, 1e-8))
        self.assertEqual(rows["FRA-FR32-equiv-of-dim"]["result"], "FAIL")

    def test_02_respects_w_eq(self):
        rows, _, ok, _ = run(MAMA, bump("MA05", "fama", "sc40", 999, 1e-3))       # row 999 < W_eq = 1000: not compared
        self.assertEqual(rows["MAM-MA05-equiv-sc-fama"]["result"], "PASS")
        self.assertEqual(rows["MAM-MA05-imp-pass"]["result"], "FAIL")               # but IMP replays the copies on every row
        self.assertIn("sc40:fama", rows["MAM-MA05-imp-pass"]["input"])
        self.assertFalse(ok)
        rows, _, _, _ = run(MAMA, bump("MA05", "fama", "sc40", 1000, 1e-3))
        self.assertEqual(rows["MAM-MA05-equiv-sc-fama"]["result"], "FAIL")

    def test_03_level_column_uses_k_and_c(self):
        _, cs, _, _ = S.load(MAMA)
        own = S.own_model_outputs(MAMA)
        b, y = own["MA05"]["mama"]["s40"][1000:], own["MA05"]["mama"]["sc40"][1000:]
        self.assertLess(float(np.max(np.abs(y - (10 * b - 9.9)))), 1e-12)
        self.assertGreater(float(np.max(np.abs(y - b))), 1e-2)                      # a plain comparison is off by the amplitude
        #                                                                             change (sc keeps the level 1.1: 10 x 1.1 - 9.9)


class TestBoundsAndHull(unittest.TestCase):
    def test_01_alpha_bound_has_a_first_row(self):
        rows, _, ok, _ = run(MAMA, bump("MA05", "alpha", "s20", 4, 0.9))           # n = 4 < from_n = 5: not a bound row
        self.assertEqual(rows["MAM-MA05-bound-alpha"]["result"], "PASS")
        rows, _, ok, _ = run(MAMA, bump("MA05", "alpha", "ramp", 5, 0.9))          # n = 5: alpha 0.5 -> 1.4 > FL
        self.assertEqual(rows["MAM-MA05-bound-alpha"]["result"], "FAIL")
        self.assertIn("high side", rows["MAM-MA05-bound-alpha"]["input"])

    def test_02_relative_allowance_both_sides(self):
        def setv(vid, col, inp, n, v):
            def f(outs):
                outs[vid][col][inp][n] = v
            return f
        rows, _, _, _ = run(MAMA, setv("MA05", "period", "s100", 2000, 50 * (1 + 0.5e-12)))
        self.assertEqual(rows["MAM-MA05-bound-period"]["result"], "PASS")
        rows, _, _, _ = run(MAMA, setv("MA05", "period", "of40", 2000, 50 * (1 + 2e-12)))         # copies are bounded too
        self.assertEqual(rows["MAM-MA05-bound-period"]["result"], "FAIL")
        lo = R.FRAMA_EXP_MIN
        rows, _, _, _ = run(FRAMA, setv("FR16", "alpha", "s5B", 2000, lo * (1 - 0.5e-12)))
        self.assertEqual(rows["FRA-FR16-bound-alpha"]["result"], "PASS")
        rows, _, _, _ = run(FRAMA, setv("FR16", "alpha", "s5B", 2000, lo * (1 - 2e-12)))
        self.assertEqual(rows["FRA-FR16-bound-alpha"]["result"], "FAIL")
        self.assertIn("low side", rows["FRA-FR16-bound-alpha"]["input"])
        rows, _, _, _ = run(FRAMA, setv("FR32", "dim", "sc40B", 0, 2 * (1 + 2e-12)))
        self.assertEqual(rows["FRA-FR32-bound-dim"]["result"], "FAIL")

    def test_03_hull_fires_on_one_row_out_by_1e12(self):
        _, _, x, _ = S.load(FRAMA)

        def above(n, d, inp="s20"):
            def f(outs):
                outs["FR16"]["out"][inp][n] = float(np.maximum.accumulate(x[inp])[n]) + d
            return f
        rows, _, ok, _ = run(FRAMA, above(1500, 1e-12))
        self.assertEqual(rows["FRA-FR16-hull"]["result"], "FAIL")
        self.assertFalse(ok)
        rows, _, ok, _ = run(FRAMA, above(1500, 0.0))                               # on the hull: allowed
        self.assertEqual(rows["FRA-FR16-hull"]["result"], "PASS")
        rows, _, _, _ = run(FRAMA, above(0, 1e-12, "of40B"))                        # row 0 and the copies count
        self.assertEqual(rows["FRA-FR16-hull"]["result"], "FAIL")


class TestFramaKnownAnswers(unittest.TestCase):
    def test_01_ramp_exact_lag_flat_fire(self):
        rows, _, _, _ = run(FRAMA, bump("FR16", "out", "ramp", 3, 2e-12))
        self.assertEqual(rows["FRA-FR16-exact-out-ramp"]["result"], "FAIL")
        def lagshift(outs):
            outs["FR32"]["out"]["rampB"] = outs["FR32"]["out"]["rampB"] - 1e-4 * 2e-6     # 2e-6 bars
        rows, _, _, _ = run(FRAMA, lagshift)
        self.assertEqual(rows["FRA-FR32-ramp-lag-rampB"]["result"], "FAIL")
        rows, _, _, _ = run(FRAMA)
        self.assertLess(rows["FRA-FR32-ramp-lag-rampB"]["abs_diff"], 1e-10)
        self.assertEqual(rows["FRA-FR16-ramp-lag-rampB"]["expected"], 34.05274879969143)
        rows, _, _, _ = run(FRAMA, bump("FR16", "out", "flat", 2999, 2e-12))
        self.assertEqual(rows["FRA-FR16-flat-out"]["result"], "FAIL")


class TestImpAndFloor(unittest.TestCase):
    def test_01_imp_per_column_tolerance_and_info_pairs(self):
        rows, _, ok, _ = run(MAMA, bump("MA05", "phase", "s5", 100, 50.0))         # INFO pair: reported, IMP still PASS
        self.assertEqual(rows["MAM-MA05-imp-pass"]["result"], "PASS")
        rows, _, _, _ = run(MAMA, bump("MA05", "phase", "s40", 100, 5e-9))         # phase 1e-8: PASS
        self.assertEqual(rows["MAM-MA05-imp-pass"]["result"], "PASS")
        rows, _, _, _ = run(MAMA, bump("MA05", "fama", "of40", 100, 5e-9))         # fama 1e-9: FAIL (copies are IMP inputs)
        r = rows["MAM-MA05-imp-pass"]
        self.assertEqual(r["result"], "FAIL")
        self.assertIn("of40:fama", r["input"])
        self.assertTrue(math.isclose(r["actual"], 5e-9, rel_tol=1e-6))
        rows, _, _, _ = run(FRAMA)
        self.assertEqual(rows["FRA-FR16-imp-fail"]["result"], "PASS")
        self.assertEqual(rows["FRA-NCS-imp-fail"]["result"], "PASS")
        self.assertGreater(len(rows["FRA-FR16-imp-pass"]["detail"]), 0)
        self.assertEqual(sorted(rows["FRA-FR16-imp-pass"]["info_detail"]), ["flat:alpha", "flat:dim"])

    def test_02_must_fail_fires_only_when_the_model_differs(self):
        _, cs, _, _ = S.load(FRAMA)
        raw = S.synth_raw(FRAMA)
        sub = copy.deepcopy(cs)
        sub["imp"]["must_fail"] = {"FR16": "frama_article(16)"}                     # the own model: must_fail must FAIL
        r = [x for x in C.imp_rows(sub, raw) if x["check_id"] == "FRA-FR16-imp-fail"][0]
        self.assertEqual(r["result"], "FAIL")

    def test_03_floor_guard_per_column_group(self):
        rows, _, ok, _ = run(MAMA, bump("MA05", "alpha", "s20", 2000, 5e-10))      # trace PASS (1e-9), floor FAIL (1e-10)
        self.assertEqual(rows["MAM-MA05-trace-alpha-s20"]["result"], "PASS")
        self.assertEqual(rows["MAM-MA05-floor-trace"]["result"], "FAIL")
        self.assertEqual(rows["MAM-MA05-floor-trace-phase"]["result"], "PASS")
        self.assertFalse(ok)
        rows, _, ok, _ = run(MAMA, bump("MA05", "phase", "s20", 2000, 5e-9))       # phase: trace PASS (1e-8), floor FAIL (1e-9)
        self.assertEqual(rows["MAM-MA05-floor-trace-phase"]["result"], "FAIL")
        self.assertEqual(rows["MAM-MA05-floor-trace"]["result"], "PASS")
        rows, _, ok, _ = run(FRAMA, bump("FR16", "out", "s20", 2000, 5e-11))
        self.assertEqual(rows["FRA-FR16-floor-trace"]["result"], "FAIL")
        _, cs, _, _ = S.load(FRAMA)
        self.assertEqual([k for k, _ in C.floor_quantities(cs)], ["trace", "equivariance", "ramp_exact", "lag", "flat"])
        _, cm, _, _ = S.load(MAMA)
        self.assertEqual(C.floor_quantities(cm), [("trace", 1e-10), ("trace:phase", 1e-09), ("equivariance", 1e-10),
                                                  ("equivariance:phase", 1e-09)])


class TestControlsFail(unittest.TestCase):
    def test_01_a_control_that_passes_fails_the_run(self):
        """Replace NC32's output (MAMA) with MA05's: the control no longer differs, so it is NOT detected and the verdict is FAIL."""
        def same(outs):
            for c in outs["NC32"]:
                for i in outs["NC32"][c]:
                    outs["NC32"][c][i] = outs["MA05"][c][i].copy()
        rows, nc, ok, _ = run(MAMA, same)
        self.assertFalse(nc["NC32"]["fails_as_required"])
        self.assertFalse(ok)

    def test_02_required_kind_must_be_detected(self):
        """NCE (FRAMA) without its bound effect (alpha forced into range): trace and lag alone are not enough, the verdict is FAIL."""
        def inrange(outs):
            for i in outs["NCE"]["alpha"]:
                a = outs["NCE"]["alpha"][i]
                outs["NCE"]["alpha"][i] = np.where(a < R.FRAMA_EXP_MIN, R.FRAMA_EXP_MIN, a)
        rows, nc, ok, _ = run(FRAMA, inrange)
        self.assertTrue(nc["NCE"]["detected"]["trace"] and nc["NCE"]["detected"]["lag"])
        self.assertFalse(nc["NCE"]["detected"]["bound"])
        self.assertFalse(ok)

    def test_03_nct_bound_is_info_only(self):
        """NCT's bound row fires (its alpha held at the initial 0) but is not required (review 2026-11-20): without it NCT still counts
        as detected (trace alone). The clipped columns then differ from NCT's own model, so only NCT's IMP must_pass row fails."""
        rows, nc, ok, _ = run(FRAMA)
        self.assertEqual(rows["FRA-NCT-bound-alpha"]["result"], "FAIL")
        self.assertEqual(nc["NCT"]["required"], ["trace"])
        def inrange(outs):
            for i in outs["NCT"]["alpha"]:
                a = outs["NCT"]["alpha"][i]
                outs["NCT"]["alpha"][i] = np.where(a < R.FRAMA_EXP_MIN, R.FRAMA_EXP_MIN, a)
        rows, nc, ok, _ = run(FRAMA, inrange)
        self.assertFalse(nc["NCT"]["detected"]["bound"])
        self.assertTrue(nc["NCT"]["fails_as_required"])
        self.assertTrue(all(d["fails_as_required"] for d in nc.values()))
        self.assertEqual([k for k, r in rows.items() if r["role"] in ("real", "imp", "floor") and r["result"] != "PASS"], ["FRA-NCT-imp-pass"])


if __name__ == "__main__":
    unittest.main()
