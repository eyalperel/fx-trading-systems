"""FSH pre-run item (iii): reference.py (via tests/fsh_support.numbers) reproduces every number the spec stores: [findings], [floor],
[variants.effect], [imp.fire_test] (incl. own-model and discrimination). Tolerance 1e-9 absolute, relative 1e-9 for |values| > 1 (the
spec's own rule). Also: every effect kind of [detect.required] is >= 10x its tolerance, and no kind >= 10x is missing from it.
No Zorro run, no .c file read. Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fsh_support as S      # noqa: E402

KINDS = ("trace", "bound", "invariance", "ramp_exact", "trigger", "flat_zero")


def close(a, e):
    return abs(a - e) <= (1e-9 * abs(e) if abs(e) > 1 else 1e-9)


class TestSpecNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = S.load()[0]
        cls.N = S.numbers()

    def test_01_findings(self):
        F, sf = self.N["findings"], {k: v for k, v in self.spec["findings"].items() if k != "source"}
        self.assertEqual(sorted(F), sorted(sf))
        bad = [(k, F[k], sf[k]) for k in F if not close(float(F[k]), float(sf[k]))]
        self.assertEqual(bad, [])
        print("\n  [findings]: %d values reproduced" % len(F))

    def test_02_floor(self):
        fl = self.spec["floor"]
        for k, v in self.N["floor"].items():
            self.assertTrue(close(v, fl[k]), (k, v, fl[k]))
        est = max(self.N["floor"].values())
        self.assertTrue(close(est, fl["trace"]))
        self.assertLessEqual(fl["trace"] * 10, self.spec["tolerances"]["trace"]["value"])      # brief STOP rule: floor x10 <= 1e-9

    def test_03_effects_and_detect_required(self):
        tol = {k: self.spec["tolerances"][k]["value"] for k in KINDS}
        for v in self.spec["variants"]:
            if v["role"] == "real":
                continue
            got, stored = self.N["effects"][v["id"]], {k: x for k, x in v["effect"].items() if k != "source"}
            self.assertEqual(sorted(got), sorted(stored), v["id"])
            for k in got:
                self.assertTrue(close(got[k], stored[k]), (v["id"], k, got[k], stored[k]))
            if v["role"] == "neg_control":
                want = sorted(k for k in KINDS if k in got and (got[k] >= 10 * tol[k] if tol[k] else got[k] > 0))
                self.assertEqual(sorted(self.spec["detect"]["required"][v["id"]]), want, v["id"])
                self.assertTrue(want, v["id"])                                                   # brief STOP rule: some kind >= 10x

    def test_04_imp_fire_tests(self):
        ft = self.spec["imp"]["fire_test"]
        self.assertTrue(close(self.N["fire"]["FSH-FR10-imp-fail"], ft["fr10_vs_ncw_model"]))
        self.assertTrue(close(self.N["fire"]["FSH-NCS-imp-fail"], ft["ncs_vs_fr10_model"]))
        for vid, e in ft["must_pass_own_model"].items():
            self.assertTrue(close(self.N["fire"]["FSH-%s-imp-pass" % vid], e), vid)
        for vid, e in ft["discrimination"].items():
            self.assertTrue(close(self.N["discrimination"][vid], e), vid)
            if vid != "FR10":
                self.assertGreater(e, self.spec["tolerances"]["imp"]["value"], vid)

    def test_05_ncs_differs_on_rows_ge_W_on_every_input(self):
        """Brief STOP rule: NCS must not differ from the model only on rows < W or only on flat."""
        F = self.N["findings"]
        for vid in ("ncs", "nct"):
            for i in ("flat", "s5", "s10", "s20", "s40", "s100", "ramp", "rampdn"):
                self.assertGreater(F["%s_%s_ge_W" % (vid, i)], 0.5, (vid, i))


if __name__ == "__main__":
    unittest.main()
