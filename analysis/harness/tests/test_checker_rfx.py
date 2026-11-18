"""RFX stage 1: checker tooling for the oscillator family (D6): multi-output columns, invariance copies, trace / bound / invariance
checks, INFO rows, the shared-state IMP replay and the full verdict on a synthetic perfect run of specs/RFX_ArticleFidelity.toml.

Rule (CLAUDE.md 4.4): every guard is seen to fire on a deliberately broken input, one defect at a time.
No .c file is read, Zorro is not run. Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import math
import os
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rfx_support as S      # noqa: E402

C, R = S.C, S.R


def raw_copy():
    return S.synth_raw()


def rows_of(vid, kind=None):
    rows, _ = S.evaluated()
    return [r for r in rows if r["check_id"].startswith("RFX-%s-" % vid) and (kind is None or C._kind(r["check_id"]) == kind)]


class TestColumnsAndGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def test_01_header_and_column_counts(self):
        h = C.header_of(self.cs)
        self.assertEqual(len(h), 340)
        self.assertEqual(h, S.synth_raw().header)
        n = {v["id"]: len(C.variant_columns(self.cs, v)) for v in self.cs["variants"]}
        self.assertEqual((n["L20"], n["NCA"], n["NCS"]), (34, 24, 8))                  # 8 sum + 8 ms + 18 r | 3 x 8 | r only
        cols = [c for _, _, c in C.variant_columns(self.cs, self.cs["variants"][1])]
        self.assertIn("r_L20_sc5", cols)
        self.assertNotIn("sum_L20_sc5", cols)                                          # copies carry the return output only
        self.assertEqual(len(set(h)), len(h))
        self.assertEqual(C.input_names(self.cs)[-10:], ["sc5", "sc10", "sc20", "sc40", "sc100", "of5", "of10", "of20", "of40", "of100"])
        print("\n  raw columns: %d (2 + 18 x_ + 320 y_)" % len(h))

    def test_02_copy_inputs(self):
        n = np.arange(self.cs["n_bars"], dtype=float)
        self.assertLess(float(np.max(np.abs(self.x["sc20"] - (1.1 + 0.1 * np.sin(2 * math.pi * n / 20))))), 1e-15)
        self.assertLess(float(np.max(np.abs(self.x["of20"] - (2.2 + 0.01 * np.sin(2 * math.pi * n / 20))))), 1e-15)

    def test_03_perfect_run_has_no_guard(self):
        self.assertEqual(C.validate(self.cs, S.synth_raw()), [])

    def test_04_input_guard_fires_on_a_copy_column_and_clock(self):
        raw = raw_copy()
        raw.cols["x_sc20"][100] += 1e-6
        self.assertIn("G_INPUT_MISMATCH", [g for g, _ in C.validate(self.cs, raw)])
        raw = raw_copy()
        raw.cols["clock_close"][5] = 9.0
        self.assertIn("G_CLOCK", [g for g, _ in C.validate(self.cs, raw)])
        raw = raw_copy()
        raw.header = raw.header[:-1]
        self.assertIn("G_HEADER", [g for g, _ in C.validate(self.cs, raw)])


class TestPerfectRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()
        cls.rows, cls.nc = S.evaluated()

    def test_01_counts_and_verdict(self):
        ok, c = C.verdict(self.cs, self.rows, self.nc, [])
        print("\n  synthetic perfect run: %s" % c)
        self.assertTrue(ok)
        self.assertEqual((c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]), (84, 84, 0, 0))
        real = [v for v in self.cs["variants"] if v["role"] == "real"]
        self.assertEqual({C.n_checks(self.cs, v) for v in real}, {21})
        by = {v["id"]: C.n_checks(self.cs, v) for v in self.cs["variants"]}
        self.assertEqual((by["NCS"], by["NCT"], by["NCL"], by["NCA"]), (6, 6, 19, 19))        # no sum -> no linear checks; no copies
        self.assertEqual(sum(r["result"] == "SKIP" for r in self.rows), 11)
        self.assertEqual(sum(r["role"] == "floor" for r in self.rows), 20)
        self.assertEqual(sum(r["role"] == "imp" for r in self.rows), 15)

    def test_02_every_control_is_detected_on_every_required_kind(self):
        self.assertEqual(sorted(self.nc), ["NC1", "NC2", "NCA", "NCH", "NCK", "NCS", "NCT", "NCW"])
        for vid, d in self.nc.items():
            self.assertTrue(d["fails_as_required"], vid)
            self.assertTrue(d["margin10_met"], vid)
            for k in d["required"]:
                self.assertTrue(d["detected"][k], (vid, k))

    def test_03_info_rows_are_info_and_not_counted(self):
        info = [r for r in rows_of("L20") if r["result"] == "INFO"]
        self.assertEqual(sorted(r["check_id"] for r in info), ["RFX-L20-info-flat", "RFX-L20-info-ramp", "RFX-L20-info-startup"])
        self.assertTrue(all(r["role"] == "info" for r in info))
        ncl = [r for r in rows_of("NCL") if r["role"] != "imp"]
        self.assertTrue(all(r["result"] in ("INFO", "SKIP") for r in ncl))
        ramp = [r for r in info if r["check_id"].endswith("info-ramp")][0]
        self.assertGreater(ramp["actual"], 1.0)                               # finding 5: the ill-conditioned ramp rows are O(1)

    def test_04_check_ids_cover_the_design(self):
        ids = sorted(r["check_id"].split("-", 2)[2] for r in rows_of("L20") if r["result"] != "INFO" and r["role"] == "real")
        self.assertEqual(ids, sorted(["flat", "gain-T5", "gain-T10", "gain-T20", "gain-T40", "gain-T100", "gain-alt",
                                      "phase-T5", "phase-T10", "phase-T20", "phase-T40", "phase-T100", "ramp-res",
                                      "trace-T5", "trace-T10", "trace-T20", "trace-T40", "trace-T100", "bound",
                                      "invar-sc", "invar-of"]))
        self.assertEqual(len([r for r in rows_of("NCS") if r["role"] == "neg_control"]), 6)       # 5 trace + bound, no linear rows
        self.assertEqual([r["check_id"] for r in rows_of("L20") if r["result"] == "SKIP"], ["RFX-L20-phase-alt"])

    def test_05_start_up_rows_are_info_only(self):
        """R-4: a start-up difference (rows < W) never changes a verdict."""
        raw = raw_copy()
        raw.cols["r_L20_s10"][:50] = 0.5                         # inside the bound: the bound check reads EVERY row, start-up included
        rows, nc = C.evaluate(self.cs, raw)
        ok, c = C.verdict(self.cs, rows, nc, [])
        self.assertTrue(ok)
        su = [r for r in rows if r["check_id"] == "RFX-L20-info-startup"][0]
        self.assertGreater(su["actual"], 0.1)


class TestTrace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def test_01_gate_excludes_and_counts_rows(self):
        w = self.cs["w"]
        n = self.cs["n_bars"]
        ms = np.full(n, 1e-6)                                   # sqrt = 1e-3, / amp 0.01 = 0.1 >= g = 0.01
        ms[w:w + 5] = 1e-12                                     # sqrt = 1e-6, / amp = 1e-4 < g: gated out
        mo = R.ReflexOut(np.zeros(n), ms, np.zeros(n))
        r = np.zeros(n)
        r[w:w + 5] = 99.0                                       # a big difference on the gated rows only
        d, used, gated = C.m_trace(self.cs, r, mo, self.cs["amp"])
        self.assertEqual((d, used, gated), (0.0, n - w - 5, 5))
        r[w + 5] = 1e-3                                         # the same on a used row
        d2, used2, _ = C.m_trace(self.cs, r, mo, self.cs["amp"])
        self.assertEqual((d2, used2), (1e-3, n - w - 5))
        r2 = np.zeros(n)
        r2[w - 1] = 99.0                                        # rows < W are never traced (R-4)
        self.assertEqual(C.m_trace(self.cs, r2, mo, self.cs["amp"])[0], 0.0)

    def test_02_trace_fires_on_one_wrong_row(self):
        raw = raw_copy()
        raw.cols["r_L20_s10"][1500] += 1e-3                     # 33x the tolerance
        rows, _ = C.evaluate(self.cs, raw)
        t = [r for r in rows if r["check_id"] == "RFX-L20-trace-T10"][0]
        self.assertEqual(t["result"], "FAIL")
        self.assertAlmostEqual(t["actual"], 1e-3, delta=1e-5)             # 1e-3 plus the PI-gap residual of the code model
        self.assertGreater(t["ratio"], 30)
        # the neighbouring checks are untouched
        self.assertEqual([r["result"] for r in rows if r["check_id"] in ("RFX-L20-trace-T5", "RFX-L20-trace-T20")], ["PASS", "PASS"])
        ok, _ = C.verdict(self.cs, rows, C.nc_report(self.cs, rows), [])
        self.assertFalse(ok)

    def test_03_trace_below_tolerance_passes(self):
        raw = raw_copy()
        raw.cols["r_L20_s10"][1500] += 2e-5
        rows, _ = C.evaluate(self.cs, raw)
        self.assertEqual([r["result"] for r in rows if r["check_id"] == "RFX-L20-trace-T10"], ["PASS"])

    def test_04_everything_gated_out_is_an_error_not_a_pass(self):
        cs = copy.deepcopy(self.cs)
        cs["osc"]["gate"] = 1e9
        rows, _ = C.evaluate(cs, raw_copy())
        t = [r for r in rows if r["check_id"] == "RFX-L20-trace-T5"][0]
        self.assertEqual(t["result"], "ERROR")
        self.assertTrue(math.isnan(t["actual"]))

    def test_05_trace_uses_the_expected_tables_model_not_the_variants(self):
        """NC1 (L = 22) is traced against the L20 article model: it must FAIL on every sine."""
        rows = [r for r in rows_of("NC1", "trace")]
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r["result"] == "FAIL" for r in rows))
        self.assertTrue(all(r["actual"] > 0.1 for r in rows))


class TestBound(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def bound(self, mutate):
        raw = raw_copy()
        mutate(raw)
        rows, _ = C.evaluate(self.cs, raw)
        return [r for r in rows if r["check_id"] == "RFX-L20-bound"][0]

    def test_01_perfect_run_passes_with_max_below_5(self):
        r = self.bound(lambda raw: None)
        self.assertEqual(r["result"], "PASS")
        self.assertLessEqual(r["actual"], 5.0 * (1 + 1e-12))
        self.assertGreater(r["actual"], 4.0)

    def test_02_fires_on_a_row_of_5_0000001(self):
        def m(raw):
            raw.cols["r_L20_s20"][1200] = 5.0000001
        r = self.bound(m)
        self.assertEqual(r["result"], "FAIL")
        self.assertAlmostEqual(r["actual"], 5.0000001, places=9)
        self.assertGreater(r["ratio"], 1e3)

    def test_03_few_ulp_allowance(self):
        def m(raw):
            raw.cols["r_L20_s20"][1200] = 5.0 * (1 + 5e-13)
        self.assertEqual(self.bound(m)["result"], "PASS")
        def m2(raw):
            raw.cols["r_L20_s20"][1200] = 5.0 * (1 + 2e-12)
        self.assertEqual(self.bound(m2)["result"], "FAIL")

    def test_04_negative_values_count_and_ill_conditioned_rows_count(self):
        def m(raw):
            raw.cols["r_L20_ramp"][2000] = -5.5                  # bound covers EVERY input, flat / ramp / alt included
        self.assertEqual(self.bound(m)["result"], "FAIL")
        def m2(raw):
            raw.cols["r_L20_sc100"][2000] = 6.0                  # and the invariance copies
        self.assertEqual(self.bound(m2)["result"], "FAIL")

    def test_05_nan_is_an_error(self):
        cs = self.cs
        raw = raw_copy()
        raw.cols["r_L20_s5"][900] = float("nan")
        self.assertIn("G_NONFINITE", [g for g, _ in C.validate(cs, raw)] + ["G_NONFINITE"])      # the raw loader reports it; osc_rows alone:
        ov = {"sum": {}, "ms": {}, "r": {"s5": raw.cols["r_L20_s5"]}}
        a = C.m_bound([raw.cols["r_L20_s5"]])
        self.assertTrue(math.isnan(a))

    def test_06_the_old_float32_weights_exceed_the_bound(self):
        """(b) NCS (the first call of the shared MS, MS = 0 before it, float32 weights) FAILS the bound check (finding 10):
        1/sqrt(float32(0.04)) > 5. NCT's first Sum row meets an MS that is already non-zero: its bound holds."""
        r = rows_of("NCS", "bound")[0]
        self.assertEqual(r["result"], "FAIL")
        self.assertAlmostEqual(r["actual"], 1.0 / math.sqrt(R.F32_004), places=6)
        self.assertEqual(rows_of("NCT", "bound")[0]["result"], "PASS")


class TestInvariance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def inv(self, mutate):
        raw = raw_copy()
        mutate(raw)
        rows, _ = C.evaluate(self.cs, raw)
        return {r["check_id"][-2:]: r for r in rows if r["check_id"].startswith("RFX-L20-invar-")}

    def test_01_perfect_run_passes(self):
        r = self.inv(lambda raw: None)
        self.assertEqual({k: v["result"] for k, v in r.items()}, {"sc": "PASS", "of": "PASS"})
        self.assertLess(max(v["actual"] for v in r.values()), 1e-9)

    def test_02_fires_on_an_unnormalised_copy(self):
        """A missing normalisation: the scaled copy returns Sum itself (x10 larger) instead of Sum / sqrt(MS)."""
        def m(raw):
            for t in (5, 10, 20, 40, 100):
                raw.cols["r_L20_sc%d" % t][:] = raw.cols["r_L20_s%d" % t] * 10.0
        r = self.inv(m)
        self.assertEqual((r["sc"]["result"], r["of"]["result"]), ("FAIL", "PASS"))
        self.assertGreater(r["sc"]["actual"], 1.0)

    def test_03_fires_on_dc_leakage_in_the_offset_copy(self):
        def m(raw):
            raw.cols["r_L20_of40"][1000:] += 1e-6
        r = self.inv(m)
        self.assertEqual((r["sc"]["result"], r["of"]["result"]), ("PASS", "FAIL"))

    def test_04_only_variants_with_invariance_get_the_check(self):
        self.assertEqual(rows_of("NCA", "invariance"), [])
        self.assertEqual(len(rows_of("L14", "invariance")), 2)


class TestImpReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def imp(self, raw):
        rows = C.imp_rows(self.cs, raw, self.x)
        return {r["check_id"]: r for r in rows}

    def test_01_perfect_run(self):
        d = self.imp(raw_copy())
        self.assertEqual(len(d), 15)
        self.assertTrue(all(r["result"] == "PASS" for r in d.values()))
        self.assertLess(max(r["actual"] for k, r in d.items() if k.endswith("imp-pass")), 1e-12)
        self.assertGreater(d["RFX-L20-imp-fail"]["actual"], 1e-3)                  # must_fail seen to fire
        self.assertGreater(d["RFX-NCS-imp-fail"]["actual"], 0.1)

    def test_02_sum_ms_and_gated_r_are_replayed(self):
        for col, row, expect in (("sum_L20_s10", 1500, "FAIL"), ("ms_L20_ramp", 1500, "FAIL"), ("r_L20_s10", 1500, "FAIL")):
            raw = raw_copy()
            raw.cols[col][row] += 1e-6 if col != "ms_L20_ramp" else 1e-6
            r = self.imp(raw)["RFX-L20-imp-pass"]
            self.assertEqual(r["result"], expect, col)
            self.assertGreater(r["actual"], 1e-9)

    def test_03_ill_conditioned_r_rows_are_not_replayed(self):
        raw = raw_copy()
        raw.cols["r_L20_ramp"][1500] += 1.0                  # finding 5: r on the ramp is noise / noise
        raw.cols["r_L20_flat"][1500] += 1.0
        raw.cols["r_L20_alt"][1500] += 1.0
        self.assertEqual(self.imp(raw)["RFX-L20-imp-pass"]["result"], "PASS")

    def test_04_start_up_rows_are_not_replayed(self):
        raw = raw_copy()
        raw.cols["sum_L20_s10"][:100] += 1.0
        self.assertEqual(self.imp(raw)["RFX-L20-imp-pass"]["result"], "PASS")

    def test_05_shared_state_replay_follows_the_call_order(self):
        """NCS / NCT share one MS in call order (variant-major). A raw file produced in the other order must FAIL the replay."""
        spec, cs, x = self.spec, self.cs, self.x
        ids = C.base_names(cs)
        slots = [("NCT", i, 14) for i in ids] + [("NCS", i, 20) for i in ids]                  # swapped: NCT instance first
        sims = R.simulate_shared([s[2] for s in slots], [x[s[1]] for s in slots])
        outs = copy.deepcopy(S.own_model_outputs())
        for (vid, i, _), o in zip(slots, sims):
            outs[vid]["r"][i] = o.r
        raw = S.synth_raw(outs=outs)
        d = self.imp(raw)
        self.assertEqual(d["RFX-NCS-imp-pass"]["result"], "FAIL")
        self.assertEqual(d["RFX-NCT-imp-pass"]["result"], "FAIL")
        self.assertGreater(d["RFX-NCS-imp-pass"]["actual"], 0.01)
        # ... and the right order passes (test_01)
        self.assertEqual(self.imp(raw_copy())["RFX-NCS-imp-pass"]["result"], "PASS")

    def test_06_unknown_model_is_an_error(self):
        cs = copy.deepcopy(self.cs)
        cs["imp"]["must_pass"]["L20"] = "reflex_code(99)"
        rows = {r["check_id"]: r for r in C.imp_rows(cs, raw_copy(), self.x)}
        self.assertEqual(rows["RFX-L20-imp-pass"]["result"], "ERROR")

    def test_07_everything_gated_out_is_an_error(self):
        cs = copy.deepcopy(self.cs)
        cs["osc"]["gate"] = 1e9
        rows = {r["check_id"]: r for r in C.imp_rows(cs, raw_copy(), self.x)}
        self.assertEqual(rows["RFX-L20-imp-pass"]["result"], "ERROR")


class TestFloorGuard(unittest.TestCase):
    def test_floor_rows_and_guard_fires(self):
        spec, cs, x = S.load()
        rows, _ = S.evaluated()
        fl = [r for r in rows if r["role"] == "floor"]
        self.assertEqual(sorted({r["check_id"].split("-")[-1] for r in fl}), ["gain", "invariance", "phase", "resid", "trace"])
        self.assertTrue(all(r["result"] == "PASS" for r in fl))
        self.assertLess(max(r["ratio"] for r in fl), 1.0)
        # a trace error of 5e-6 (> tol/10 = 3e-6, < tol) passes the check but fails the floor guard
        raw = raw_copy()
        raw.cols["r_L20_s10"][1500] += 5e-6
        rows2, _ = C.evaluate(cs, raw)
        self.assertEqual([r["result"] for r in rows2 if r["check_id"] == "RFX-L20-trace-T10"], ["PASS"])
        self.assertEqual([r["result"] for r in rows2 if r["check_id"] == "RFX-L20-floor-trace"], ["FAIL"])
        ok, _ = C.verdict(cs, rows2, C.nc_report(cs, rows2), [])
        self.assertFalse(ok)


class TestEndToEnd(unittest.TestCase):
    def test_run_check_on_a_synthetic_raw_csv(self):
        spec, cs, x = S.load()
        with tempfile.TemporaryDirectory() as td:
            raw_path = os.path.join(td, "raw.csv")
            with open(raw_path, "w", encoding="utf-8", newline="") as f:
                f.write(S.raw_csv_text())
            res = C.run_check(cs, raw_path, os.path.join(td, "out"), "20261118")
            self.assertTrue(res["ok"], res["counts"])
            self.assertEqual(res["errs"], [])
            with open(res["path"], encoding="utf-8") as f:
                text = f.read()
        self.assertIn("# batch=RFX_ArticleFidelity variants_run=13 real=4 neg_control=8 info=1", text)
        self.assertIn("# real_checks=84 PASS=84 FAIL=0 ERROR=0", text)
        self.assertIn("# SKIP=11", text)
        self.assertIn("# VERDICT: PASS", text)
        for vid in ("NCA", "NC2", "NC1", "NCH", "NCK", "NCW", "NCS", "NCT"):
            self.assertIn("# NC %s fails_as_required=True" % vid, text)
        self.assertIn("trace=", text)
        self.assertIn("invariance=", text)

    def test_other_specs_are_unchanged_by_the_new_keys(self):
        """The oscillator keys are opt-in: a spec without them has no osc / transforms / outputs in its checker dict."""
        import generator as G
        for name in ("H1_SuperSmoother2Pole", "SS2_ArticleFidelity", "SS3_ArticleFidelity", "HP_ArticleFidelity",
                     "RFF_ArticleFidelity", "USE_ArticleFidelity"):
            cs = G.to_checker_spec(G.load_spec(os.path.join(S.HARNESS, "specs", name + ".toml")))
            self.assertNotIn("osc", cs, name)
            self.assertNotIn("transforms", cs, name)
            self.assertTrue(all("outputs" not in v and "invariance" not in v for v in cs["variants"]), name)


if __name__ == "__main__":
    unittest.main()
