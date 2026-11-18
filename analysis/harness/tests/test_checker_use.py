"""USE stage 1: checker tooling. `[checks].startup_seed` (the source's start-up rule as the reference), the variant role
`info` (rows written as INFO, never PASS / FAIL, not counted), and an end-to-end run of the real USE spec on a synthetic
raw file built from each variant's own model.

Rule (CLAUDE.md 4.4): every guard is SEEN TO FIRE on a deliberately broken input. No .c file is read, no Zorro run.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import os
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import use_support as S      # noqa: E402

C, R, G = S.C, S.R, S.G


def variant(cs_, vid):
    return copy.deepcopy([v for v in cs_["variants"] if v["id"] == vid][0])


class TestStartupSeed(unittest.TestCase):
    def test_01_startup_rows_follow_startup_seed(self):
        """The same pass3 output passes the start-up check with startup_seed pass3 and FAILS with zero (and with pass4 on s20)."""
        cs_, x = S.cs(), S.inputs()
        v = variant(cs_, "P20")
        yv = {i: R.simulate(R.us_code(20), x[i], seed="pass3") for i in C.input_names(cs_)}
        rows = lambda c: {r["check_id"]: r for r in C.check_rows(c, v, x, yv, xe=x) if "startup" in r["check_id"]}
        ok = rows(cs_)
        self.assertEqual({r["result"] for r in ok.values()}, {"PASS"})
        self.assertEqual(len(ok), 3)
        zero = copy.deepcopy(cs_)
        zero["startup_seed"] = "zero"
        bad = rows(zero)
        print("\n  startup_seed fire: pass3 output vs seed zero: " + ", ".join("%s %s %.2e" % (k[-4:], r["result"], r["actual"]) for k, r in bad.items()))
        self.assertEqual({r["result"] for r in bad.values()}, {"FAIL"})
        p4 = copy.deepcopy(cs_)
        p4["startup_seed"] = "pass4"
        r4 = rows(p4)
        self.assertEqual((r4["USE-P20-startup-flat"]["result"], r4["USE-P20-startup-ramp"]["result"], r4["USE-P20-startup-s20"]["result"]),
                         ("PASS", "PASS", "FAIL"))                                   # finding 7: only s20 sees pass3 vs pass4

    def test_02_default_is_zero_old_specs_unchanged(self):
        """Without the key the reference seed is zero (HP / RFF behaviour); the RFF checker dict carries no startup_seed."""
        import generator as G_
        rff = G_.to_checker_spec(G_.load_spec(os.path.join(S.HARNESS, "specs", "RFF_ArticleFidelity.toml")))
        self.assertNotIn("startup_seed", rff)
        self.assertEqual(S.cs()["startup_seed"], "pass3")


class TestInfoRole(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cs = S.cs()
        cls.header = C.header_of(cls.cs)
        cls.tmp = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_raw(self, cols, tag):
        d = os.path.join(self.tmp.name, tag)
        os.makedirs(d, exist_ok=True)
        raw = os.path.join(d, "raw.csv")
        with open(raw, "w", encoding="utf-8", newline="") as f:
            f.write(S.to_text(self.header, cols, self.cs["n_bars"]))
        res = C.run_check(self.cs, raw, d, "20261117")
        with open(res["path"], encoding="utf-8") as f:
            res["text"] = f.read()
        return res

    def test_03_header(self):
        self.assertEqual(len(self.header), 2 + 8 + 11 * 8)
        self.assertIn("x_alt", self.header)
        self.assertIn("y_NCL_alt", self.header)
        self.assertEqual([v["role"] for v in self.cs["variants"]],
                         ["real"] * 4 + ["info"] + ["neg_control"] * 6)

    def test_04_clean_run_passes_and_ncl_rows_are_info(self):
        res = self.run_raw(S.raw_cols(), "clean")
        c = res["counts"]
        print("\n  [e2e] own-model raw: ok=%s real=%d PASS=%d FAIL=%d ERROR=%d" % (res["ok"], c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]))
        self.assertEqual(res["errs"], [])
        self.assertEqual((c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]), (64, 64, 0, 0))
        self.assertTrue(res["ok"], res["text"][-800:])
        ncl = [r for r in res["rows"] if r["check_id"].startswith("USE-NCL-") and r["role"] != "imp"]
        print("  NCL rows: %d, results %s" % (len(ncl), sorted({r["result"] for r in ncl})))
        self.assertEqual(sorted({r["result"] for r in ncl}), ["INFO", "SKIP"])           # never PASS / FAIL
        self.assertEqual(sum(r["result"] == "INFO" for r in ncl), 16)                    # same 16 checks as a real variant
        self.assertTrue(all(r["role"] == "info" for r in ncl if r["result"] == "INFO"))
        self.assertEqual(sum(r["result"] == "SKIP" for r in res["rows"]), 11)             # 4 real + 1 info + 6 controls
        self.assertEqual(len(res["nc"]), 6)
        self.assertTrue(all(d["fails_as_required"] for d in res["nc"].values()))
        imp = [r for r in res["rows"] if r["role"] == "imp"]
        floor = [r for r in res["rows"] if r["role"] == "floor"]
        self.assertEqual((len(imp), len(floor)), (13, 16))                                # 11 must_pass + 2 must_fail; 4 x 4
        self.assertTrue(all(r["result"] == "PASS" for r in imp + floor))
        self.assertIn("variants_run=11 real=4 neg_control=6 info=1", res["text"])
        self.assertIn("# real_checks=64 PASS=64 FAIL=0 ERROR=0", res["text"])
        self.assertIn(",INFO,info", res["text"].replace("\r", ""))
        self.assertIn("# VERDICT: PASS", res["text"])

    def test_05_info_variant_cannot_fail_the_verdict_by_its_checks(self):
        """NCL's gain is 3.6x tolerance: as a real variant it would FAIL; as role info its rows are INFO and the verdict holds."""
        res = self.run_raw(S.raw_cols(), "infoclean")
        ncl_gain = [r for r in res["rows"] if r["check_id"].startswith("USE-NCL-gain-T")]
        self.assertTrue(any(r["ratio"] > 1 for r in ncl_gain), "NCL must exceed the tolerance somewhere (else this test proves nothing)")
        self.assertEqual({r["result"] for r in ncl_gain}, {"INFO"})
        self.assertTrue(res["ok"])
        # fire: the same variant with role real WOULD fail those rows
        cs2 = copy.deepcopy(self.cs)
        for v in cs2["variants"]:
            if v["id"] == "NCL":
                v["role"] = "real"
        v = variant(cs2, "NCL")
        rows = C.check_rows(cs2, v, S.inputs(), S.own_model_outputs()["NCL"], xe=S.inputs())
        self.assertTrue(any(r["result"] == "FAIL" for r in rows))

    def test_06_ncl_is_judged_only_by_imp(self):
        """A garbage NCL column does not fail a check, but its IMP must_pass replay fails: the run is FAIL."""
        y = S.own_model_outputs()
        bad = {i: np.asarray(y["NCL"][i]) + 1e-5 for i in y["NCL"]}
        res = self.run_raw(S.raw_cols({"NCL": bad}), "badncl")
        imp = {r["check_id"]: r for r in res["rows"] if r["role"] == "imp"}
        print("\n  NCL column + 1e-5: IMP must_pass %s %.2e; verdict ok=%s" % (imp["USE-NCL-imp-pass"]["result"], imp["USE-NCL-imp-pass"]["actual"], res["ok"]))
        self.assertEqual(imp["USE-NCL-imp-pass"]["result"], "FAIL")
        self.assertFalse(res["ok"])
        self.assertEqual(res["counts"]["n_fail"], 0)                                       # the real variants are untouched

    def test_07_ncs_output_in_the_real_slot_fails_startup_and_imp(self):
        """Guard (D-2): the 4-bar seed in P20's column fails the s20 start-up check, IMP must_pass, and ... only s20 sees it."""
        y = S.own_model_outputs()
        res = self.run_raw(S.raw_cols({"P20": y["NCS"]}), "ncsinreal")
        fails = sorted(r["check_id"] for r in res["rows"] if r["role"] == "real" and r["result"] == "FAIL")
        print("\n  NCS output in P20 slot: real FAILs %s" % fails)
        self.assertEqual(fails, ["USE-P20-startup-s20"])
        self.assertFalse(res["ok"])
        imp = {r["check_id"]: r["result"] for r in res["rows"] if r["role"] == "imp"}
        self.assertEqual(imp["USE-P20-imp-pass"], "FAIL")

    def test_08_ncx_output_in_the_real_slot_fails_and_must_fail_fires(self):
        y = S.own_model_outputs()
        res = self.run_raw(S.raw_cols({"P20": y["NCX"]}), "ncxinreal")
        fails = [r["check_id"] for r in res["rows"] if r["role"] == "real" and r["result"] == "FAIL"]
        self.assertTrue(any("gain-T" in f for f in fails) and any("phase-T" in f for f in fails))
        imp = {r["check_id"]: r["result"] for r in res["rows"] if r["role"] == "imp"}
        self.assertEqual(imp["USE-P20-imp-fail"], "FAIL")                    # must_fail row: replay vs the NCX model = 0, not > 1e-9
        self.assertFalse(res["ok"])

    def test_09_wrong_control_is_not_detected(self):
        """A control that returns the real P20 output must not be detected (NCS: startup)."""
        y = S.own_model_outputs()
        res = self.run_raw(S.raw_cols({"NCS": y["P20"]}), "ctrlpass")
        self.assertFalse(res["nc"]["NCS"]["fails_as_required"])
        self.assertFalse(res["ok"])

    def test_10_nonfinite_info_row_is_an_error_not_info(self):
        """An INFO row whose actual is not finite stays ERROR (the role rewrite only touches PASS / FAIL)."""
        cs_, x = S.cs(), S.inputs()
        cs2 = copy.deepcopy(cs_)
        for v in cs2["variants"]:
            if v["id"] == "NCL":
                v["article"] = "nonsense"                                              # start-up model missing -> ERROR rows
        y = S.own_model_outputs()["NCL"]
        v = variant(cs2, "NCL")
        rows = C.check_rows(cs2, v, x, y, xe=x)
        self.assertTrue(any(r["result"] == "ERROR" for r in rows))


if __name__ == "__main__":
    unittest.main()
