"""LRSI stage 1: checker tooling for the Laguerre RSI: four-column variants (l0 / l3 / den / out), the v1 checks on TWO linear outputs
(own tables, ids -l0 / -l3), the new kinds ramp_exact (out = 1 / 0 on the ramps, rows >= W) and startup on the normalised output (rows < W
vs the model), the trace gate on the MODEL's CU + CD, skipped (variant, input) pairs, the LRS IMP replay (incl. the superseded file's shared
statics in the actual call order), the results header (SKIPPED_INPUTS, L_NO_STATIC) and the full verdict on a synthetic perfect run of
specs/LRSI_ArticleFidelity.toml.

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
import lrs_support as S      # noqa: E402

C, R, G = S.C, S.R, S.G
W = 700


def rows_of(vid, kind=None, rows=None):
    rows = rows if rows is not None else S.evaluated()[0]
    return [r for r in rows if r["check_id"].startswith("LRS-%s-" % vid) and (kind is None or C._kind(r["check_id"]) == kind)]


def row(rows, cid):
    m = [r for r in rows if r["check_id"] == cid]
    assert len(m) == 1, (cid, len(m))
    return m[0]


def broken(mutate):
    """Evaluate a copy of the perfect raw file after `mutate(raw)`; returns (rows, nc, ok)."""
    spec, cs, x = S.load()
    raw = S.synth_raw()
    raw.cols = {k: np.array(v, copy=True) for k, v in raw.cols.items()}
    mutate(raw)
    rows, nc = C.evaluate(cs, raw)
    return rows, nc, C.verdict(cs, rows, nc, [])[0]


class TestColumnsAndCounts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def test_01_header_and_four_output_columns(self):
        h = C.header_of(self.cs)
        self.assertEqual(len(h), 319)                                                 # 2 + 19 x_ + 298 outputs
        self.assertEqual(h, S.synth_raw().header)
        self.assertEqual(len(set(h)), len(h))
        n = {v["id"]: len(C.variant_columns(self.cs, v)) for v in self.cs["variants"]}
        self.assertEqual(n, {"G05": 46, "G07": 46, "G08": 46, "NCH": 36, "NCG": 36, "NC25": 36, "NCP": 36, "NCS": 8, "NCT": 8})
        for col in ("l0_G05_s10", "l3_G05_rampdn", "den_G05_flat", "out_G05_of100", "out_NCS_s5", "out_NCT_rampdn"):
            self.assertIn(col, h)
        for col in ("l0_G05_sc5", "den_G05_of100", "l0_NCS_s5", "out_NCS_flat", "out_NCT_flat"):
            self.assertNotIn(col, h)
        print("\n  raw columns: %d (2 + 19 x_ + 298 outputs)" % len(h))

    def test_02_perfect_run_has_no_guard_and_a_stray_column_fires(self):
        self.assertEqual(C.validate(self.cs, S.synth_raw()), [])
        raw = S.synth_raw()
        raw.header = raw.header + ["out_NCS_flat"]                                    # a skipped pair that was called after all
        raw.cols["out_NCS_flat"] = np.zeros(3000)
        self.assertEqual([g for g, _ in C.validate(self.cs, raw)], ["G_HEADER"])

    def test_03_rampdn_input_guard(self):
        raw = S.synth_raw()
        raw.cols = dict(raw.cols)
        raw.cols["x_rampdn"] = raw.cols["x_rampdn"] + 1e-11
        self.assertIn("G_INPUT_MISMATCH", [g for g, _ in C.validate(self.cs, raw)])


class TestPerfectRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()
        cls.rows, cls.nc = S.evaluated()

    def test_01_counts_and_verdict(self):
        ok, c = C.verdict(self.cs, self.rows, self.nc, [])
        print("\n  synthetic perfect run: %s" % c)
        self.assertTrue(ok)
        self.assertEqual((c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]), (129, 129, 0, 0))
        by = {v["id"]: C.n_checks(self.cs, v) for v in self.cs["variants"]}
        self.assertEqual(by, {"G05": 43, "G07": 43, "G08": 43, "NCH": 41, "NCG": 41, "NC25": 41, "NCP": 41, "NCS": 13, "NCT": 13})
        self.assertEqual(sum(r["result"] == "SKIP" for r in self.rows), 0)
        self.assertEqual(sum(r["role"] == "floor" for r in self.rows), 21)              # 3 real x 7 kinds
        self.assertEqual(sum(r["role"] == "imp" for r in self.rows), 10)                # 9 must_pass + 1 must_fail
        self.assertTrue(all(r["result"] == "PASS" for r in self.rows if r["role"] in ("imp", "floor")))

    def test_02_every_control_is_detected_on_every_required_kind(self):
        self.assertEqual(sorted(self.nc), sorted(S.CONTROLS))
        for vid, d in self.nc.items():
            self.assertTrue(d["fails_as_required"], vid)
            for k in d["required"]:
                self.assertTrue(d["detected"][k], (vid, k))
        fails = [r["check_id"] for r in rows_of("NCS", rows=self.rows) if r["result"] == "FAIL"]
        self.assertEqual(fails, ["LRS-NCS-startup-s5"])                               # Amendment 1 A: only the seeded s5 call differs
        self.assertEqual(row(self.rows, "LRS-NCS-startup-s5")["actual"], 0.5979633949986088)
        fails = [r["check_id"] for r in rows_of("NCP", rows=self.rows) if r["result"] == "FAIL"]
        self.assertEqual(fails, ["LRS-NCP-startup-s%d" % t for t in S.TS])

    def test_03_check_ids_cover_the_design(self):
        lin = ["flat", "gain-T5", "gain-T10", "gain-T20", "gain-T40", "gain-T100", "gain-alt", "ramp-lag",
               "phase-T5", "phase-T10", "phase-T20", "phase-T40", "phase-T100", "phase-alt"]
        out = ["trace-T%d" % t for t in S.TS] + ["bound", "invar-sc", "invar-of", "exact-ramp", "exact-rampdn"] \
            + ["startup-s%d" % t for t in S.TS]
        ids = sorted(r["check_id"].split("-", 2)[2] for r in rows_of("G05", rows=self.rows) if r["role"] == "real")
        self.assertEqual(ids, sorted([c + "-l0" for c in lin] + [c + "-l3" for c in lin] + out))
        self.assertEqual(sorted(r["check_id"].split("-", 2)[2] for r in rows_of("NCS", rows=self.rows) if r["role"] == "neg_control"),
                         sorted(["trace-T%d" % t for t in S.TS] + ["bound", "exact-ramp", "exact-rampdn"] + ["startup-s%d" % t for t in S.TS]))

    def test_04_kinds_of_the_new_ids(self):
        for tail, k in (("flat-l3", "flat"), ("ramp-lag-l0", "lag"), ("phase-alt-l3", "phase"), ("gain-alt-l0", "gain"),
                        ("exact-ramp", "ramp_exact"), ("exact-rampdn", "ramp_exact"), ("startup-s5", "startup")):
            self.assertEqual(C._kind("LRS-G05-" + tail), k, tail)

    def test_05_info_rows_and_info_variants(self):
        info = sorted(r["check_id"] for r in rows_of("G05", rows=self.rows) if r["result"] == "INFO")
        self.assertEqual(info, ["LRS-G05-info-flat", "LRS-G05-info-ramp"])           # startup is a check here, not INFO
        self.assertEqual(row(self.rows, "LRS-G05-info-flat")["actual"], 1.0)          # G05 flat holds 1.0 (finding 10)
        for vid in S.INFO:
            rs = [r for r in rows_of(vid, rows=self.rows) if r["role"] != "imp"]
            self.assertTrue(rs and all(r["result"] == "INFO" for r in rs), vid)

    def test_06_linear_rows_read_their_own_tables(self):
        e = self.spec["expected"]
        self.assertEqual(row(self.rows, "LRS-G05-ramp-lag-l3")["expected"], e["G05_l3"]["lag"])
        self.assertEqual(row(self.rows, "LRS-G05-ramp-lag-l0")["expected"], e["G05_l0"]["lag"])
        self.assertEqual(row(self.rows, "LRS-G08-phase-T40-l3")["expected"], e["G08_l3"]["phases"]["40"])
        self.assertEqual(row(self.rows, "LRS-G07-phase-alt-l3")["expected"], math.pi)
        self.assertEqual(row(self.rows, "LRS-G07-phase-alt-l3")["actual"], math.pi)
        self.assertTrue(row(self.rows, "LRS-G05-gain-T5-l3")["input"].startswith("l3: "))
        self.assertEqual(row(self.rows, "LRS-NC25-ramp-lag-l3")["result"], "FAIL")    # NC25 changes L3 only
        self.assertEqual(row(self.rows, "LRS-NC25-ramp-lag-l0")["result"], "PASS")


class TestTwoLinearOutputs(unittest.TestCase):
    def test_01_swapped_outputs_fail(self):
        def mut(raw):
            for i in C.base_names(S.load()[1]):
                raw.cols["l3_G05_%s" % i] = raw.cols["l0_G05_%s" % i].copy()
        rows, nc, ok = broken(mut)
        self.assertFalse(ok)
        self.assertEqual(row(rows, "LRS-G05-ramp-lag-l3")["result"], "FAIL")
        self.assertEqual(row(rows, "LRS-G05-phase-T10-l3")["result"], "FAIL")
        self.assertEqual(row(rows, "LRS-G05-phase-alt-l3")["result"], "FAIL")
        self.assertEqual(row(rows, "LRS-G05-gain-T10-l3")["result"], "PASS")          # |L3| = |L0|: gain cannot see it
        self.assertTrue(all(r["result"] == "PASS" for r in rows_of("G05", rows=rows) if r["check_id"].endswith("-l0")))


class TestRampExact(unittest.TestCase):
    def test_01_fires_on_a_0_9999999_row(self):
        rows, nc, ok = broken(lambda raw: raw.cols["out_G05_ramp"].__setitem__(1500, 0.9999999))
        r = row(rows, "LRS-G05-exact-ramp")
        self.assertEqual((r["result"], r["actual"], r["expected"]), ("FAIL", 0.9999999, 1.0))
        self.assertAlmostEqual(r["abs_diff"], 1e-7, delta=1e-15)
        self.assertIn("n=1500", r["input"])
        self.assertFalse(ok)
        print("\n  [fire] ramp_exact on out = 0.9999999 at n = 1500: %s (|diff| %.3e)" % (r["result"], r["abs_diff"]))

    def test_02_falling_ramp_and_tolerance_edge(self):
        rows, _, ok = broken(lambda raw: raw.cols["out_G07_rampdn"].__setitem__(2999, 1e-7))
        self.assertEqual(row(rows, "LRS-G07-exact-rampdn")["result"], "FAIL")
        rows, _, ok = broken(lambda raw: raw.cols["out_G07_rampdn"].__setitem__(2999, 5e-13))
        self.assertEqual(row(rows, "LRS-G07-exact-rampdn")["result"], "PASS")       # within tol_abs 1e-12 ...
        self.assertEqual(row(rows, "LRS-G07-floor-ramp_exact")["result"], "FAIL")   # ... but above the floor guard tol/10 = 1e-13 (item 7)
        self.assertFalse(ok)
        rows, _, ok = broken(lambda raw: raw.cols["out_G07_rampdn"].__setitem__(2999, 5e-14))
        self.assertEqual(row(rows, "LRS-G07-floor-ramp_exact")["result"], "PASS")
        self.assertTrue(ok)

    def test_03_rows_below_W_are_not_read_and_nan_is_an_error(self):
        rows, _, ok = broken(lambda raw: raw.cols["out_G05_ramp"].__setitem__(10, 0.5))
        self.assertEqual(row(rows, "LRS-G05-exact-ramp")["result"], "PASS")
        rows, _, ok = broken(lambda raw: raw.cols["out_G05_ramp"].__setitem__(900, float("nan")))
        self.assertEqual(row(rows, "LRS-G05-exact-ramp")["result"], "ERROR")
        self.assertFalse(ok)


class TestStartupOnTheNormalisedOutput(unittest.TestCase):
    def test_01_fires_on_a_seeded_variant(self):
        """G05's s20 column replaced by the price-seeded model (the old start-up, L-1): its startup row FAILs, nothing else."""
        x = S.load()[2]
        seeded = R.simulate_lrsi(R.lrsi_article(0.5, seed="price"), x["s20"]).out
        rows, nc, ok = broken(lambda raw: raw.cols.__setitem__("out_G05_s20", seeded.copy()))
        r = row(rows, "LRS-G05-startup-s20")
        self.assertEqual(r["result"], "FAIL")
        self.assertAlmostEqual(r["actual"], 0.9233174011464185, delta=1e-12)       # NCP, T = 20 (brief)
        self.assertFalse(ok)
        self.assertEqual(sorted(x_["check_id"] for x_ in rows if x_["role"] == "real" and x_["result"] != "PASS"),
                         ["LRS-G05-startup-s20"])
        print("\n  [fire] startup on a price-seeded G05 s20 column: FAIL, %.6f" % r["actual"])

    def test_02_tolerance_edge(self):
        rows, _, ok = broken(lambda raw: raw.cols["out_G08_s5"].__setitem__(3, raw.cols["out_G08_s5"][3] + 9e-7))
        self.assertEqual(row(rows, "LRS-G08-startup-s5")["result"], "PASS")
        rows, _, ok = broken(lambda raw: raw.cols["out_G08_s5"].__setitem__(3, raw.cols["out_G08_s5"][3] + 2e-6))
        self.assertEqual(row(rows, "LRS-G08-startup-s5")["result"], "FAIL")


class TestGateOnTheModelDenominator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def test_01_gate_reads_the_model_den(self):
        n, amp = self.cs["n_bars"], self.cs["amp"]
        den = np.full(n, 1e-3)
        den[W:W + 5] = 1e-6                                                          # / amp = 1e-4 < g = 0.01: gated
        z = np.zeros(n)
        mo = R.LrsiOut(z, z, z, z, den, z)
        self.assertIs(C.gate_q(mo), den)
        out = np.zeros(n)
        out[W:W + 5] = 99.0
        self.assertEqual(C.m_trace(self.cs, out, mo, amp), (0.0, n - W - 5, 5))
        out[W + 10] = 1e-3
        self.assertEqual(C.m_trace(self.cs, out, mo, amp)[0], 1e-3)

    def test_02_gated_rows_are_counted_and_all_gated_is_an_error(self):
        cs = copy.deepcopy(self.cs)
        cs["osc"]["gate"] = 1.3                                                      # above the G05 T = 20 margin 1.2522
        rows, nc = C.evaluate(cs, S.synth_raw())
        r = row(rows, "LRS-G05-trace-T20")
        self.assertEqual(r["result"], "PASS")
        gated = int(r["input"].split("gated out ")[1].split(" of")[0])
        self.assertGreater(gated, 0)
        print("\n  [fire] gate 1.3 on G05 T=20: %s" % r["input"])
        cs["osc"]["gate"] = 100.0
        rows, nc = C.evaluate(cs, S.synth_raw())
        self.assertEqual(row(rows, "LRS-G05-trace-T20")["result"], "ERROR")
        self.assertFalse(C.verdict(cs, rows, nc, [])[0])

    def test_03_the_gate_uses_the_model_not_the_run(self):
        """A run whose out is wildly wrong cannot gate its own rows away: the gate reads the MODEL's CU + CD."""
        rows, _, ok = broken(lambda raw: raw.cols["out_G05_s100"].__setitem__(slice(W, None), 0.5))
        r = row(rows, "LRS-G05-trace-T100")
        self.assertEqual(r["result"], "FAIL")
        self.assertIn("gated out 0 of 2300", r["input"])


class TestImpReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()

    def imp(self, rows, vid, kind="pass"):
        return row(rows, "LRS-%s-imp-%s" % (vid, kind))

    def test_01_replay_covers_l0_l3_den_and_gated_out(self):
        for col, val in (("l3_G05_alt", 1e-8), ("den_G05_ramp", 1e-8), ("l0_G05_flat", 1e-8), ("out_G05_sc40", 1e-8)):
            rows, _, ok = broken(lambda raw, c=col, v=val: raw.cols[c].__setitem__(1000, raw.cols[c][1000] + v))
            self.assertEqual(self.imp(rows, "G05")["result"], "FAIL", col)
        rows, _, ok = broken(lambda raw: raw.cols["out_G05_flat"].__setitem__(1000, 0.3))     # flat out: INFO, not replayed
        self.assertEqual(self.imp(rows, "G05")["result"], "PASS")
        rows, _, ok = broken(lambda raw: raw.cols["l0_G05_s5"].__setitem__(10, 9.0))         # rows < W not replayed
        self.assertEqual(self.imp(rows, "G05")["result"], "PASS")

    def test_02_must_fail_fires(self):
        rows, _ = S.evaluated()
        r = self.imp(rows, "G05", "fail")
        self.assertEqual(r["result"], "PASS")
        self.assertGreater(r["actual"], 1e-9)
        self.assertEqual(r["actual"], self.spec["imp"]["fire_test"]["g05_vs_ncg_model"])

    def test_03_superseded_replay_follows_the_call_order(self):
        model = R.IMP_MODELS["lrsi_superseded(1/2,1/2)[0]"]()
        slots = C.lrsi_shared_slots(self.cs, model)
        self.assertEqual(slots[0], ("NCS", "s5", 0.5))
        self.assertEqual(len(slots), 16)
        rows, _ = S.evaluated()
        for vid in ("NCS", "NCT"):
            self.assertEqual(self.imp(rows, vid)["result"], "PASS")
            self.assertEqual(self.imp(rows, vid)["actual"], 0.0)
        # a run in which NCT (not NCS) had taken the seed: NCS's s5 start-up would then be the source's -> its startup check would PASS
        x = self.x
        rows, nc, ok = broken(lambda raw: raw.cols.__setitem__("out_NCS_s5", R.simulate_lrsi(R.lrsi_article(0.5), x["s5"]).out))
        self.assertFalse(nc["NCS"]["fails_as_required"])                              # not detected -> run FAIL (rerun rule)
        self.assertFalse(ok)


class TestResultsFile(unittest.TestCase):
    def test_01_header_lines(self):
        spec, cs, x = S.load()
        rows, nc = S.evaluated()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.csv")
            ok, c = C.write_results(p, cs, rows, nc, [], "raw.csv", "0" * 64)
            with open(p, encoding="utf-8") as f:
                txt = f.read()
        self.assertTrue(ok)
        self.assertIn("# batch=LRS_ArticleFidelity variants_run=9 real=3 neg_control=4 info=2\n", txt)
        self.assertIn("# real_checks=129 PASS=129 FAIL=0 ERROR=0\n", txt)
        self.assertIn("# SKIPPED_INPUTS=2 (variant:input; no call, no raw column, no check; spec skip_inputs): NCS:flat,NCT:flat\n", txt)
        self.assertIn("# INFO L_NO_STATIC indicators/ehlers/LaguerreRSI.c:", txt)
        self.assertIn(" ramp_exact=", txt)
        self.assertNotIn("SKIPPED_INPUTS", self._mst_header())

    def _mst_header(self):
        import mst_support as M
        spec, cs, x = M.load()
        rows, nc = M.evaluated()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.csv")
            C.write_results(p, cs, rows, nc, [], "raw.csv", "0" * 64)
            with open(p, encoding="utf-8") as f:
                return f.read()


if __name__ == "__main__":
    unittest.main()
