"""MST stage 1: checker tooling for MESAStochastic (D6 + its notes): three-output variants (roof / stoc / out), the trace gate on the
MODEL's range HighestC - LowestC, the two-sided ABSOLUTE bound on a named output (stoc), `startup_info` variants, the MESA IMP replay,
and the full verdict on a synthetic perfect run of specs/MESA_ArticleFidelity.toml.

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
import mst_support as S      # noqa: E402

C, R = S.C, S.R


def raw_copy():
    return S.synth_raw()


def rows_of(vid, kind=None, rows=None):
    rows = rows if rows is not None else S.evaluated()[0]
    return [r for r in rows if r["check_id"].startswith("MST-%s-" % vid) and (kind is None or C._kind(r["check_id"]) == kind)]


def row(rows, cid):
    m = [r for r in rows if r["check_id"] == cid]
    assert len(m) == 1, (cid, len(m))
    return m[0]


class TestColumnsAndCounts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def test_01_header_and_three_output_columns(self):
        h = C.header_of(self.cs)
        self.assertEqual(len(h), 308)                                                  # 2 + 18 x_ + 288 y_
        self.assertEqual(h, S.synth_raw().header)
        self.assertEqual(len(set(h)), len(h))
        n = {v["id"]: len(C.variant_columns(self.cs, v)) for v in self.cs["variants"]}
        self.assertEqual({k: n[k] for k in ("L20", "NCL", "NCZ", "NCW", "NCS")},
                         {"L20": 34, "NCL": 24, "NCZ": 24, "NCW": 24, "NCS": 8})    # 8 roof + 8 stoc + 18 out | 3 x 8 | out only
        for col in ("roof_L20_s10", "stoc_L20_ramp", "out_L20_of100", "out_NCS_alt"):
            self.assertIn(col, h)
        for col in ("roof_L20_sc5", "stoc_L20_of100", "stoc_NCS_s5", "roof_NCS_s5"):    # copies: return output only; NCS: out only
            self.assertNotIn(col, h)
        print("\n  raw columns: %d (2 + 18 x_ + 288 y_)" % len(h))

    def test_02_perfect_run_has_no_guard(self):
        self.assertEqual(C.validate(self.cs, S.synth_raw()), [])

    def test_03_three_parameter_variants_reach_the_checker(self):
        self.assertEqual({v["id"]: v["params"] for v in self.spec["variants"]},
                         {"L14": [14, 48, 10], "L20": [20, 48, 10], "L30": [30, 48, 10], "S20": [20, 48, 20], "NCL": [20, 48, 10],
                          "NCZ": [20, 48, 10], "NCW": [20, 48, 10], "NCA": [20, 48, 10], "NCP": [20, 40, 10], "NC1": [22, 48, 10],
                          "NCS": [20, 48, 10]})
        self.assertEqual(row(S.evaluated()[0], "MST-NCP-gain-T20")["params"], "NCP: HPPeriod 40 vs the (20,48,10) article")
        self.assertEqual(row(S.evaluated()[0], "MST-NCP-gain-T20")["result"], "FAIL")      # the HP period reaches the Roof checks


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
        by = {v["id"]: C.n_checks(self.cs, v) for v in self.cs["variants"]}
        self.assertEqual(by, {"L14": 21, "L20": 21, "L30": 21, "S20": 21, "NCL": 19, "NCZ": 19, "NCW": 19, "NCA": 19,
                              "NCP": 19, "NC1": 19, "NCS": 5})                           # NCS: 5 trace, no roof, no stoc
        self.assertEqual(sum(r["result"] == "SKIP" for r in self.rows), 10)              # alt phase of every roof exporter
        self.assertEqual(sum(r["role"] == "floor" for r in self.rows), 20)               # 4 real x (gain, phase, resid, trace, invariance)
        self.assertEqual(sum(r["role"] == "imp" for r in self.rows), 13)                 # 11 must_pass + 2 must_fail

    def test_02_every_control_is_detected_on_every_required_kind(self):
        self.assertEqual(sorted(self.nc), sorted(S.CONTROLS))
        for vid, d in self.nc.items():
            self.assertTrue(d["fails_as_required"], vid)
            self.assertTrue(d["margin10_met"], vid)
            for k in d["required"]:
                self.assertTrue(d["detected"][k], (vid, k))

    def test_03_check_ids_cover_the_design(self):
        ids = sorted(r["check_id"].split("-", 2)[2] for r in rows_of("L20", rows=self.rows)
                     if r["result"] != "INFO" and r["role"] == "real")
        self.assertEqual(ids, sorted(["flat", "gain-T5", "gain-T10", "gain-T20", "gain-T40", "gain-T100", "gain-alt",
                                      "phase-T5", "phase-T10", "phase-T20", "phase-T40", "phase-T100", "ramp-res",
                                      "trace-T5", "trace-T10", "trace-T20", "trace-T40", "trace-T100", "bound",
                                      "invar-sc", "invar-of"]))
        self.assertEqual(sorted(r["check_id"] for r in rows_of("NCS", rows=self.rows) if r["role"] == "neg_control"),
                         ["MST-NCS-trace-T%d" % t for t in (10, 100, 20, 40, 5)])
        self.assertEqual(rows_of("NCS", "bound", rows=self.rows), [])                   # decided 2026-11-19: trace-only detection
        self.assertEqual([r["check_id"] for r in rows_of("L20", rows=self.rows) if r["result"] == "SKIP"], ["MST-L20-phase-alt"])

    def test_04_info_rows_and_startup_info_variant(self):
        info = sorted(r["check_id"] for r in rows_of("L20", rows=self.rows) if r["result"] == "INFO")
        self.assertEqual(info, ["MST-L20-info-flat", "MST-L20-info-ramp", "MST-L20-info-startup"])
        self.assertEqual(row(self.rows, "MST-L20-info-flat")["actual"], 0.5)            # M-6 fallback on the flat input
        # NCZ (role info, startup_info = true) gets the start-up row: the source zero final seed, finding 7
        su = row(self.rows, "MST-NCZ-info-startup")
        self.assertEqual(su["result"], "INFO")
        self.assertAlmostEqual(su["actual"], 0.4367, places=3)
        self.assertLess(row(self.rows, "MST-L20-info-startup")["actual"], 1e-5)         # library seed: only the PI gap
        # NCL (role info, no startup_info): no start-up row; every non-imp row INFO or SKIP
        self.assertEqual([r for r in rows_of("NCL", rows=self.rows) if r["check_id"].endswith("info-startup")], [])
        self.assertTrue(all(r["result"] in ("INFO", "SKIP") for r in rows_of("NCL", rows=self.rows) if r["role"] != "imp"))
        self.assertTrue(all(r["result"] in ("INFO", "SKIP") for r in rows_of("NCZ", rows=self.rows) if r["role"] != "imp"))

    def test_05_start_up_rows_never_change_the_verdict(self):
        raw = raw_copy()
        raw.cols["out_L20_s10"][:50] = 0.9
        rows, nc = C.evaluate(self.cs, raw)
        self.assertTrue(C.verdict(self.cs, rows, nc, [])[0])
        self.assertGreater(row(rows, "MST-L20-info-startup")["actual"], 0.1)

    def test_06_trace_compares_with_the_expected_tables_model(self):
        """NC1 (L = 22) and NCW (window 21) are traced against the L20 article model: FAIL only at T > L (finding 8)."""
        res = {r["check_id"].rsplit("-", 1)[1]: r["result"] for r in rows_of("NC1", "trace", rows=self.rows)}
        self.assertEqual(res, {"T5": "PASS", "T10": "PASS", "T20": "PASS", "T40": "FAIL", "T100": "FAIL"})
        res = {r["check_id"].rsplit("-", 1)[1]: r["result"] for r in rows_of("NCW", "trace", rows=self.rows)}
        self.assertEqual(res, {"T5": "PASS", "T10": "PASS", "T20": "PASS", "T40": "FAIL", "T100": "FAIL"})


class TestTraceGateOnTheModelRange(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def test_01_gate_reads_the_model_range(self):
        w, n, amp = self.cs["w"], self.cs["n_bars"], self.cs["amp"]
        rng = np.full(n, 1e-3)                                  # / amp 0.01 = 0.1 >= g = 0.01
        rng[w:w + 5] = 1e-6                                     # / amp = 1e-4 < g: gated out
        mo = R.MesaOut(np.zeros(n), np.zeros(n), np.zeros(n), rng)
        self.assertIs(C.gate_q(mo), rng)
        out = np.zeros(n)
        out[w:w + 5] = 99.0                                     # big differences on the gated rows only
        self.assertEqual(C.m_trace(self.cs, out, mo, amp), (0.0, n - w - 5, 5))
        out[w + 5] = 1e-3                                       # the same on a used row
        self.assertEqual(C.m_trace(self.cs, out, mo, amp)[:2], (1e-3, n - w - 5))
        out2 = np.zeros(n)
        out2[w - 1] = 99.0                                      # rows < W are never traced
        self.assertEqual(C.m_trace(self.cs, out2, mo, amp)[0], 0.0)
        # the Reflex form is unchanged: sqrt(MS)
        ro = R.ReflexOut(np.zeros(n), np.full(n, 4.0), np.zeros(n))
        self.assertEqual(float(C.gate_q(ro)[0]), 2.0)

    def test_02_a_gated_row_in_a_real_run(self):
        """g = 0.03 sits above the tightest model margin (L14, T = 100: 0.0284, finding 4): rows are gated out, counted in the row's
        input text, and an error placed on a gated row does not reach the trace; on a used row it does."""
        cs = copy.deepcopy(self.cs)
        cs["osc"]["gate"] = 0.03
        mo = C.model_out(R.mesa_article(14, 48, 10), self.x["s100"])
        q = C.gate_q(mo)[cs["w"]:] / cs["amp"]
        gated_idx = np.nonzero(q < 0.03)[0]
        self.assertGreater(len(gated_idx), 0)
        raw = raw_copy()
        raw.cols["out_L14_s100"][cs["w"] + gated_idx[0]] += 1.0
        rows, _ = C.evaluate(cs, raw)
        t = row(rows, "MST-L14-trace-T100")
        self.assertIn("gated out %d of 2300" % len(gated_idx), t["input"])
        self.assertEqual(t["result"], "PASS")
        self.assertEqual(row(rows, "MST-L20-trace-T100")["input"].split("gated out ")[1], "0 of 2300")
        used = int(np.nonzero(q >= 0.03)[0][0])
        raw.cols["out_L14_s100"][cs["w"] + used] += 1e-3
        self.assertEqual(row(C.evaluate(cs, raw)[0], "MST-L14-trace-T100")["result"], "FAIL")
        print("\n  gate 0.03: %d rows of L14 T=100 gated out and reported" % len(gated_idx))

    def test_03_trace_fires_on_one_wrong_row(self):
        raw = raw_copy()
        raw.cols["out_L20_s40"][1500] += 1e-3                  # 20x the tolerance 5e-5
        rows, _ = C.evaluate(self.cs, raw)
        t = row(rows, "MST-L20-trace-T40")
        self.assertEqual(t["result"], "FAIL")
        self.assertGreater(t["ratio"], 19)
        self.assertEqual([row(rows, "MST-L20-trace-T%d" % k)["result"] for k in (20, 100)], ["PASS", "PASS"])
        self.assertFalse(C.verdict(self.cs, rows, C.nc_report(self.cs, rows), [])[0])
        raw = raw_copy()
        raw.cols["out_L20_s40"][1500] += 3e-5                  # below the tolerance
        self.assertEqual(row(C.evaluate(self.cs, raw)[0], "MST-L20-trace-T40")["result"], "PASS")

    def test_04_everything_gated_out_is_an_error_not_a_pass(self):
        cs = copy.deepcopy(self.cs)
        cs["osc"]["gate"] = 1e9
        t = row(C.evaluate(cs, raw_copy())[0], "MST-L20-trace-T5")
        self.assertEqual(t["result"], "ERROR")
        self.assertTrue(math.isnan(t["actual"]))


class TestTwoSidedBound(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def bound(self, mutate, vid="L20"):
        raw = raw_copy()
        mutate(raw)
        return row(C.evaluate(self.cs, raw)[0], "MST-%s-bound" % vid)

    def test_01_perfect_run_attains_both_ends(self):
        r = self.bound(lambda raw: None)
        self.assertEqual((r["result"], r["expected"], r["actual"], r["abs_diff"]), ("PASS", 1.0, 1.0, 0.0))
        self.assertIn("min 0.0, max 1.0", r["input"])
        self.assertEqual(r["tolerance"], 1e-12)

    def test_02_fires_on_a_row_of_1_0000001_and_reports_the_max(self):
        def m(raw):
            raw.cols["stoc_L20_s20"][1200] = 1.0000001
        r = self.bound(m)
        self.assertEqual(r["result"], "FAIL")
        self.assertEqual((r["expected"], r["actual"]), (1.0, 1.0000001))
        self.assertAlmostEqual(r["abs_diff"], 1e-7, delta=1e-15)
        self.assertIn("high side reported", r["input"])
        print("\n  [fire] stoc 1.0000001: %s, actual %r, ratio %.3g" % (r["result"], r["actual"], r["ratio"]))

    def test_03_fires_on_a_row_of_minus_1e9_and_reports_the_min(self):
        def m(raw):
            raw.cols["stoc_L20_s20"][1200] = -1e-9
        r = self.bound(m)
        self.assertEqual(r["result"], "FAIL")
        self.assertEqual((r["expected"], r["actual"], r["abs_diff"]), (0.0, -1e-9, 1e-9))
        self.assertIn("low side reported", r["input"])
        print("\n  [fire] stoc -1e-9: %s, actual %r, ratio %.3g" % (r["result"], r["actual"], r["ratio"]))

    def test_04_few_ulp_allowance_on_both_ends(self):
        for v, want in ((1.0 + 5e-13, "PASS"), (-5e-13, "PASS"), (1.0 + 2e-12, "FAIL"), (-2e-12, "FAIL")):
            def m(raw, v=v):
                raw.cols["stoc_L20_s20"][1200] = v
            self.assertEqual(self.bound(m)["result"], want, v)

    def test_05_every_row_of_every_base_input_counts(self):
        def m(raw):
            raw.cols["stoc_L20_ramp"][3] = 1.5                 # start-up row of the ill-conditioned ramp
        self.assertEqual(self.bound(m)["result"], "FAIL")
        def m2(raw):
            raw.cols["stoc_S20_flat"][2999] = -0.1
        self.assertEqual(self.bound(m2, "S20")["result"], "FAIL")

    def test_06_the_bound_reads_stoc_not_out(self):
        """The final output overshoots by design (finding 5): out outside [0, 1] is not a bound failure."""
        def m(raw):
            raw.cols["out_L20_s100"][100] = 1.03
        self.assertEqual(self.bound(m)["result"], "PASS")

    def test_07_nan_is_an_error(self):
        def m(raw):
            raw.cols["stoc_L20_s5"][900] = float("nan")
        self.assertEqual(self.bound(m)["result"], "ERROR")

    def test_08_m_bound_two_sided(self):
        self.assertEqual(C.m_bound_two_sided([np.array([0.0, 0.5]), np.array([1.0])], 0.0, 1.0), (1.0, 0.0, 0.0))
        self.assertEqual(C.m_bound_two_sided([np.array([-0.25, 0.5])], 0.0, 1.0), (0.5, -0.25, 0.25))
        self.assertEqual(C.m_bound_two_sided([np.array([0.5, 1.5])], 0.0, 1.0), (1.5, 0.5, 0.5))


class TestInvariance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def inv(self, mutate):
        raw = raw_copy()
        mutate(raw)
        rows, _ = C.evaluate(self.cs, raw)
        return {r["check_id"][-2:]: r for r in rows if r["check_id"].startswith("MST-L20-invar-")}

    def test_01_perfect_run_passes(self):
        r = self.inv(lambda raw: None)
        self.assertEqual({k: v["result"] for k, v in r.items()}, {"sc": "PASS", "of": "PASS"})

    def test_02_fires_on_a_shifted_copy(self):
        def m(raw):
            raw.cols["out_L20_of40"][1000:] += 1e-6
        r = self.inv(m)
        self.assertEqual((r["sc"]["result"], r["of"]["result"]), ("PASS", "FAIL"))
        def m2(raw):
            raw.cols["out_L20_sc20"][1000:] *= 1.001
        r = self.inv(m2)
        self.assertEqual((r["sc"]["result"], r["of"]["result"]), ("FAIL", "PASS"))

    def test_03_only_variants_with_invariance_get_the_check(self):
        self.assertEqual(rows_of("NCA", "invariance"), [])
        self.assertEqual(len(rows_of("S20", "invariance")), 2)


class TestImpReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def imp(self, raw, cs=None):
        return {r["check_id"]: r for r in C.imp_rows(cs or self.cs, raw, self.x)}

    def test_01_perfect_run(self):
        d = self.imp(raw_copy())
        self.assertEqual(len(d), 13)
        self.assertTrue(all(r["result"] == "PASS" for r in d.values()))
        self.assertLess(max(r["actual"] for k, r in d.items() if k.endswith("imp-pass")), 1e-12)
        self.assertGreater(d["MST-L20-imp-fail"]["actual"], 1e-4)                    # must_fail seen to fire
        self.assertGreater(d["MST-NCS-imp-fail"]["actual"], 50)

    def test_02_roof_stoc_and_out_are_replayed(self):
        for col in ("roof_L20_ramp", "roof_L20_s10", "stoc_L20_s40", "out_L20_s40", "out_L20_sc100", "out_L20_of5"):
            raw = raw_copy()
            raw.cols[col][1500] += 1e-6
            r = self.imp(raw)["MST-L20-imp-pass"]
            self.assertEqual(r["result"], "FAIL", col)
            self.assertGreater(r["actual"], 1e-9, col)

    def test_03_ill_conditioned_rows_are_not_replayed(self):
        raw = raw_copy()
        for col in ("stoc_L20_ramp", "stoc_L20_flat", "stoc_L20_alt", "out_L20_ramp", "out_L20_flat", "out_L20_alt"):
            raw.cols[col][1500] += 1.0
        self.assertEqual(self.imp(raw)["MST-L20-imp-pass"]["result"], "PASS")

    def test_04_start_up_rows_are_not_replayed(self):
        raw = raw_copy()
        raw.cols["roof_L20_s10"][:100] += 1.0
        raw.cols["out_L20_s10"][:100] += 1.0
        self.assertEqual(self.imp(raw)["MST-L20-imp-pass"]["result"], "PASS")

    def test_05_dispatch_by_model_type(self):
        """A MesaModel goes to _imp_mesa, never to the Reflex replay; an unknown model name is an ERROR."""
        self.assertIsInstance(R.IMP_MODELS["mesa_code(20,48,10)"](), R.MesaModel)
        cs = copy.deepcopy(self.cs)
        cs["imp"]["must_pass"]["L20"] = "mesa_code(99,48,10)"
        self.assertEqual(self.imp(raw_copy(), cs)["MST-L20-imp-pass"]["result"], "ERROR")

    def test_06_everything_gated_out_is_an_error(self):
        cs = copy.deepcopy(self.cs)
        cs["osc"]["gate"] = 1e9
        self.assertEqual(self.imp(raw_copy(), cs)["MST-L20-imp-pass"]["result"], "ERROR")

    def test_07_wrong_model_fails_the_replay(self):
        """L20's columns replayed with the L14 model: the stoc / out residual is O(1) (finding 8 region, T > L)."""
        cs = copy.deepcopy(self.cs)
        cs["imp"]["must_pass"]["L20"] = "mesa_code(14,48,10)"
        r = self.imp(raw_copy(), cs)["MST-L20-imp-pass"]
        self.assertEqual(r["result"], "FAIL")
        self.assertGreater(r["actual"], 0.1)


class TestFloorGuard(unittest.TestCase):
    def test_floor_rows_and_guard_fires(self):
        spec, cs, x = S.load()
        rows, _ = S.evaluated()
        fl = [r for r in rows if r["role"] == "floor"]
        self.assertEqual(sorted({r["check_id"].split("-")[-1] for r in fl}), ["gain", "invariance", "phase", "resid", "trace"])
        self.assertTrue(all(r["result"] == "PASS" for r in fl))
        self.assertLess(max(r["ratio"] for r in fl), 1.0)
        self.assertEqual(row(fl, "MST-L14-floor-trace")["tolerance"], 5e-6)
        # a trace error of 7e-6 (> tol/10 = 5e-6, < tol 5e-5) passes the check but fails the floor guard
        raw = S.synth_raw()
        raw.cols["out_L20_s10"][1500] += 7e-6
        rows2, _ = C.evaluate(cs, raw)
        self.assertEqual(row(rows2, "MST-L20-trace-T10")["result"], "PASS")
        self.assertEqual(row(rows2, "MST-L20-floor-trace")["result"], "FAIL")
        self.assertFalse(C.verdict(cs, rows2, C.nc_report(cs, rows2), [])[0])


class TestEndToEnd(unittest.TestCase):
    def test_run_check_on_a_synthetic_raw_csv(self):
        spec, cs, x = S.load()
        with tempfile.TemporaryDirectory() as td:
            raw_path = os.path.join(td, "raw.csv")
            with open(raw_path, "w", encoding="utf-8", newline="") as f:
                f.write(S.raw_csv_text())
            res = C.run_check(cs, raw_path, os.path.join(td, "out"), "20261119")
            self.assertTrue(res["ok"], res["counts"])
            self.assertEqual(res["errs"], [])
            with open(res["path"], encoding="utf-8") as f:
                text = f.read()
        self.assertIn("# batch=MST_ArticleFidelity variants_run=11 real=4 neg_control=5 info=2", text)
        self.assertIn("# real_checks=84 PASS=84 FAIL=0 ERROR=0", text)
        self.assertIn("# SKIP=10", text)
        self.assertIn("# VERDICT: PASS", text)
        for vid in S.CONTROLS:
            self.assertIn("# NC %s fails_as_required=True" % vid, text)

    def test_other_specs_have_no_mst_keys(self):
        import generator as G
        for name in ("H1_SuperSmoother2Pole", "SS2_ArticleFidelity", "SS3_ArticleFidelity", "HP_ArticleFidelity",
                     "RFF_ArticleFidelity", "USE_ArticleFidelity", "RFX_ArticleFidelity"):
            cs = G.to_checker_spec(G.load_spec(os.path.join(S.HARNESS, "specs", name + ".toml")))
            self.assertNotIn("bound_output", cs.get("osc", {}), name)
            self.assertTrue(all("startup_info" not in v for v in cs["variants"]), name)


if __name__ == "__main__":
    unittest.main()
