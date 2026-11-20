"""FSH stage 1: checker tooling for the Fisher Transform on a synthetic raw file (every variant = its own model, a perfect run):
five columns per call, trace on several outputs with per-output gates on the MODEL (range; range + clamp distance, with a gated row),
bounds on raw / v1 / out, ramp_exact per output, the new kinds trigger (fires on a one-row shift) and flat_zero (fires on 1e-9), IMP
(own-model, must_fail, shared-statics call order), per-control detection, and the results file.

Rule (CLAUDE.md 4.4): every check is seen to fire on a deliberately broken input, one defect at a time.
No Zorro run, no .c file read. Labels: (a) source states, (b) verified here, (c) inference.
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
import fsh_support as S      # noqa: E402

C, R = S.C, S.R
W = 700


def outs():
    return copy.deepcopy(S.own_model_outputs())


def run(o=None, cs=None):
    spec, cs0, _ = S.load()
    cs = cs or cs0
    raw = S.synth_raw(o)
    rows, nc = C.evaluate(cs, raw)
    return {r["check_id"]: r for r in rows}, nc, rows


def res(rows, cid):
    return rows["FSH-" + cid]["result"]


class TestPerfectRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.cs, cls.x = S.load()
        cls.rows, cls.nc = S.evaluated()
        cls.by = {r["check_id"]: r for r in cls.rows}

    def test_01_verdict_and_counts(self):
        ok, c = C.verdict(self.cs, self.rows, self.nc, [])
        self.assertTrue(ok)
        self.assertEqual(c, dict(n_real=56, n_pass=56, n_fail=0, n_err=0))
        per = {}
        for r in self.rows:
            if r["role"] == "real":
                per.setdefault(r["check_id"].split("-")[1], {}).setdefault(C._kind(r["check_id"]), 0)
                per[r["check_id"].split("-")[1]][C._kind(r["check_id"])] += 1
        want = dict(trace=15, bound=3, invariance=2, ramp_exact=6, trigger=1, flat_zero=1)
        self.assertEqual(per, {"FR10": want, "FR20": want})
        self.assertEqual({v["id"]: C.n_checks(self.cs, v) for v in self.cs["variants"]},
                         dict(FR10=28, FR20=28, NCB=26, NCW=26, NCC=26, NCK=26, NCL=26, NC32=26, NCS=9, NCT=9))
        print("\n  perfect run: 56 / 56 real checks PASS, per real variant %s" % want)

    def test_02_no_gated_row_on_a_correct_variant(self):
        for r in self.rows:
            if r["role"] == "real" and "-trace-" in r["check_id"]:
                self.assertIn("gated out 0 of 2300", r["input"], r["check_id"])

    def test_03_every_control_detected_on_its_required_kinds(self):
        self.assertEqual(set(self.nc), set(S.CONTROLS))
        for vid, d in self.nc.items():
            self.assertTrue(d["fails_as_required"], (vid, d["detected"], d["required"]))
        self.assertEqual(sorted(self.spec["detect"]["required"]), sorted(S.CONTROLS))
        ncb = [r for r in self.rows if r["check_id"].startswith("FSH-NCB-") and r["role"] != "imp"]   # its IMP row is PASS/FAIL
        self.assertTrue(ncb and all(r["result"] in ("INFO", "SKIP") for r in ncb))           # info variant: never PASS/FAIL

    def test_04_imp_and_floor_rows(self):
        imp = {r["check_id"]: r for r in self.rows if r["role"] == "imp"}
        self.assertEqual(len(imp), 12)
        self.assertTrue(all(r["result"] == "PASS" for r in imp.values()))
        self.assertGreater(imp["FSH-FR10-imp-fail"]["actual"], 1e-9)
        self.assertGreater(imp["FSH-NCS-imp-fail"]["actual"], 1e-9)
        fl = [r for r in self.rows if r["role"] == "floor"]
        self.assertEqual(sorted({r["check_id"].split("-", 2)[2] for r in fl}),
                         ["floor-flat_zero", "floor-invariance", "floor-ramp_exact", "floor-trace", "floor-trigger"])
        self.assertTrue(all(r["result"] == "PASS" for r in fl))

    def test_05_results_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.csv")
            ok, _ = C.write_results(p, self.cs, self.rows, self.nc, [], "raw.csv", "0" * 64)
            with open(p, encoding="utf-8") as f:
                txt = f.read()
        self.assertTrue(ok)
        self.assertIn("# batch=FSH_ArticleFidelity variants_run=10 real=2 neg_control=7 info=1", txt)
        self.assertIn("# real_checks=56 PASS=56 FAIL=0 ERROR=0", txt)
        self.assertIn("INFO L_NO_STATIC indicators/ehlers/FisherTransform.c", txt)
        self.assertIn("# O_IMP_RESIDUAL FR10 imp=0.000e+00 zorro_vs_book_trace=", txt)
        self.assertNotIn("O_PEAK", txt)
        self.assertIn("# VERDICT: PASS", txt)


class TestChecksFire(unittest.TestCase):
    def test_01_trace_per_output(self):
        for o_name, cid in (("raw", "FR10-trace-raw-T20"), ("v1", "FR10-trace-v1-T20"), ("out", "FR10-trace-out-T20")):
            o = outs()
            o["FR10"][o_name]["s20"][1500] += 2e-9
            by, _, _ = run(o)
            self.assertEqual(res(by, cid), "FAIL", cid)
            others = [k for k, r in by.items() if r["role"] == "real" and "-trace-" in k and r["result"] != "PASS"]
            self.assertEqual(others, ["FSH-" + cid])
        o = outs()
        o["FR10"]["v1"]["s20"][1500] += 5e-10
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-trace-v1-T20"), "PASS")                       # below the 1e-9 tolerance

    def test_02_clamp_gate_with_a_gated_row(self):
        """Raise g2 just above the model's smallest clamp distance (FR10 T100: 0.0011989375189954687): rows gated on v1 / out only."""
        spec, cs, x = S.load()
        cs2 = copy.deepcopy(cs)
        cs2["osc"]["clamp_gate"] = 0.0012
        mo = C.model_out(R.fisher_article(10), x["s100"])
        gated = np.nonzero(mo.cdist[W:] < 0.0012)[0] + W
        self.assertGreater(len(gated), 0)
        o = outs()
        o["FR10"]["v1"]["s100"][gated[0]] += 1.0                                       # a defect ON a gated row: not seen
        by, _, _ = run(o, cs2)
        self.assertEqual(res(by, "FR10-trace-v1-T100"), "PASS")
        self.assertIn("gated out %d of 2300" % len(gated), by["FSH-FR10-trace-v1-T100"]["input"])
        self.assertIn("gated out %d of 2300" % len(gated), by["FSH-FR10-trace-out-T100"]["input"])
        self.assertIn("gated out 0 of 2300", by["FSH-FR10-trace-raw-T100"]["input"])  # raw: range gate only
        by0, _, _ = run(o, cs)                                                         # the same defect with the spec's g2: seen
        self.assertEqual(res(by0, "FR10-trace-v1-T100"), "FAIL")
        print("\n  clamp gate 0.0012: %d gated row(s) on FR10 v1 / out T100; a defect on a gated row is not seen, with g2 = 1e-6 it is"
              % len(gated))
        cs3 = copy.deepcopy(cs)
        cs3["osc"]["clamp_gate"] = 10.0                                                # every row gated: ERROR, never PASS
        by3, _, _ = run(None, cs3)
        self.assertEqual(res(by3, "FR10-trace-v1-T5"), "ERROR")
        self.assertEqual(res(by3, "FR10-trace-raw-T5"), "PASS")

    def test_03_gates_read_the_model_not_the_run(self):
        """A broken run cannot gate its own rows away: v1 pushed near .99 in the RUN does not change the gate."""
        o = outs()
        o["FR10"]["v1"]["s40"][W:] = 0.99
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-trace-v1-T40"), "FAIL")
        self.assertIn("gated out 0 of 2300", by["FSH-FR10-trace-v1-T40"]["input"])

    def test_04_bounds(self):
        cases = (("raw", "ramp", 1.0 + 2e-12, "FAIL"), ("raw", "ramp", 1.0 + 5e-13, "PASS"), ("v1", "rampdn", -0.999 - 2e-12, "FAIL"),
                 ("out", "sc100", R.FISHER_LN1999 * (1 + 2e-12), "FAIL"), ("out", "ramp", R.FISHER_LN1999 * (1 + 5e-13), "PASS"))
        for o_name, i, val, want in cases:
            o = outs()
            o["FR10"][o_name][i][2000] = val
            by, _, _ = run(o)
            self.assertEqual(res(by, "FR10-bound-%s" % o_name), want, (o_name, i, val))
        o = outs()
        o["FR10"]["v1"]["rampdn"][2000] = -0.999 - 2e-12
        by, _, _ = run(o)
        self.assertIn("low side reported", by["FSH-FR10-bound-v1"]["input"])
        o = outs()
        o["FR10"]["raw"]["s5"][3] = float("nan")
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-bound-raw"), "ERROR")

    def test_05_trigger_fires_on_a_one_row_shift(self):
        o = outs()
        o["FR10"]["trig"]["s20"] = o["FR10"]["out"]["s20"].copy()                     # trig = out (no delay)
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-trigger"), "FAIL")
        o = outs()
        o["FR10"]["trig"]["ramp"] = np.concatenate([[0.0, 0.0], o["FR10"]["out"]["ramp"][:-2]])   # delayed by two rows
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-trigger"), "FAIL")
        o = outs()
        o["FR10"]["trig"]["s5"][900] = np.nextafter(o["FR10"]["trig"]["s5"][900], 10.0)   # one ulp
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-trigger"), "FAIL")
        self.assertEqual(by["FSH-FR10-trigger"]["tolerance"], 0.0)

    def test_06_flat_zero(self):
        for o_name in ("raw", "v1", "out"):
            o = outs()
            o["FR20"][o_name]["flat"][5] = 1e-9
            by, _, _ = run(o)
            self.assertEqual(res(by, "FR20-flatzero"), "FAIL", o_name)
        o = outs()
        o["FR20"]["out"]["flat"][5] = 5e-13
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR20-flatzero"), "PASS")
        o = outs()
        o["FR20"]["out"]["flat"][2] = 1e-9                                             # rows < W count too (every row)
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR20-flatzero"), "FAIL")

    def test_07_ramp_exact_per_output(self):
        for o_name, i, k, d in (("raw", "ramp", 1000, 1e-11), ("v1", "ramp", 1000, 1e-11), ("v1", "rampdn", 2999, -1e-11),
                                ("out", "rampdn", 800, 1e-11)):
            o = outs()
            o["FR10"][o_name][i][k] += d
            by, _, _ = run(o)
            self.assertEqual(res(by, "FR10-exact-%s-%s" % (o_name, i)), "FAIL", (o_name, i))
            self.assertIn("n=%d" % k, by["FSH-FR10-exact-%s-%s" % (o_name, i)]["input"])
        o = outs()
        o["FR10"]["v1"]["ramp"][300] += 1.0                                            # rows < W are not read
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-exact-v1-ramp"), "PASS")

    def test_08_invariance(self):
        o = outs()
        o["FR20"]["out"]["of40"][2500] += 2e-9
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR20-invar-of"), "FAIL")
        self.assertEqual(res(by, "FR20-invar-sc"), "PASS")

    def test_09_imp_fires(self):
        o = outs()
        o["FR10"]["out"]["s10"][1200] += 2e-9
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-imp-pass"), "FAIL")
        o = outs()
        o["FR10"]["rng"]["ramp"][1200] += 2e-9                                         # rng is replayed too (absolute)
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-imp-pass"), "FAIL")
        o = outs()
        o["NCS"], o["NCT"] = o["NCT"], o["NCS"]                                        # the instances swapped: call order matters
        by, _, _ = run(o)
        self.assertEqual(res(by, "NCS-imp-pass"), "FAIL")
        self.assertEqual(res(by, "NCT-imp-pass"), "FAIL")

    def test_10_a_control_that_passes_is_not_detected(self):
        o = outs()
        for q in S.OUTS + ("rng", "trig"):
            o["NCW"][q] = copy.deepcopy(o["FR10"][q])
            for i in list(o["NCW"][q]):
                if i not in C.base_names(S.load()[1]):
                    del o["NCW"][q][i]
        by, nc, rows = run(o)
        self.assertFalse(nc["NCW"]["fails_as_required"])
        ok, _ = C.verdict(S.load()[1], rows, nc, [])
        self.assertFalse(ok)

    def test_11_nan_is_an_error_not_a_pass(self):
        o = outs()
        o["FR10"]["trig"]["s40"][1000] = float("nan")
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-trigger"), "ERROR")
        o = outs()
        o["FR10"]["out"]["s40"][1000] = float("nan")
        by, _, _ = run(o)
        self.assertEqual(res(by, "FR10-trace-out-T40"), "ERROR")
        self.assertTrue(math.isnan(by["FSH-FR10-trace-out-T40"]["abs_diff"]))


if __name__ == "__main__":
    unittest.main()
