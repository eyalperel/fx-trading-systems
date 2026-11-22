"""ATR stage 1, pre-run item (iii) of the spec: reference.py and the checker reproduce every (b) number specs/ATR_MT4Fidelity.toml stores
(conditioning values and classification, floors, control effects, [detect.required] = every kind >= 10x, [findings], IMP fire tests) to <= 1e-9
relative (absolute 1e-15 below 1e-6). As for MAF / LRSI / FSH the spec was generated from this code, so 0 is self-consistency; the comparison with
the planning chat's independent numbers is test_reference_atr (brief items 1-6). Also: the planning output's classification equals the spec's.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import atr_support as A      # noqa: E402

G, C = A.G, A.C


def close(a, b):
    a, b = float(a), float(b)
    if math.isnan(a) or math.isnan(b):
        return math.isnan(a) and math.isnan(b)
    return abs(a - b) <= max(1e-9 * max(abs(a), abs(b)), 1e-15 if max(abs(a), abs(b)) < 1e-6 else 0.0)


def flat(d, pre=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flat(v, "%s%s/" % (pre, k)))
        elif not isinstance(v, str):
            out[pre + k] = v
    return out


class TestAtrSpecNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = G.load_spec(A.SPEC)
        cls.n = A.numbers(A.SPEC)

    def worst(self, pairs):
        bad = [(k, a, b) for k, a, b in pairs if not close(a, b)]
        self.assertEqual(bad, [])
        return max((abs(float(a) - float(b)) for _, a, b in pairs), default=0.0)

    def test_01_conditioning(self):
        pairs = []
        for t, vals in self.n["conditioning"].items():
            cc = self.spec["expected"][t]["conditioning"]
            self.assertEqual(cc["info"], {})
            self.assertEqual(self.n["info"][t], {})
            self.assertEqual(sorted(cc["values"]), sorted(vals))
            self.assertEqual(len(vals), 18)                                         # 16 inputs + 2 copies
            pairs += [("%s/%s/%s" % (t, i, c), cc["values"][i][c], v) for i, cv in vals.items() for c, v in cv.items()]
        self.assertEqual(len(pairs), 72)
        print("\n  ATR conditioning: %d values, worst |diff| %.3e" % (len(pairs), self.worst(pairs)))

    def test_01b_pre_run_vii_classification_matches(self):
        cs = G.to_checker_spec(self.spec)
        self.assertEqual(C.conditioning_mismatches(cs), [])
        # guard seen to fire: an INFO entry the recomputation does not produce is a mismatch
        cs2 = G.to_checker_spec(self.spec)
        cs2["adaptive"]["tables"]["AT14"]["info"] = {"s5": ["atr"]}
        self.assertEqual(len(C.conditioning_mismatches(cs2)), 1)

    def test_02_floor(self):
        fl = self.spec["floor"]
        pairs = [(k, fl[k], v) for k, v in self.n["floor"].items()]
        self.assertTrue(all(k in fl for k in self.n["floor"]))
        self.assertEqual(fl["imp_estimate"], fl["trace"])
        self.worst(pairs)
        for q, tol in (("trace", 1e-12), ("equivariance", 1e-12), ("known_value", 1e-12)):
            self.assertLessEqual(fl[q] * 10, tol, q)                                # D2 rule 3: floor x 10 <= tolerance

    def test_03_effects_and_detect(self):
        pairs = []
        for v in self.spec["variants"]:
            if v["role"] != "neg_control":
                continue
            eff = {k: x for k, x in v["effect"].items() if k != "source"}
            self.assertEqual(sorted(eff), sorted(self.n["effects"][v["id"]]), v["id"])
            pairs += [("%s/%s" % (v["id"], k), eff[k], self.n["effects"][v["id"]][k]) for k in eff]
            want = sorted(k for k, r in self.n["ratios"][v["id"]].items() if r >= 10)
            self.assertEqual(sorted(self.spec["detect"]["required"][v["id"]]), want, v["id"])
            self.assertTrue(want, v["id"])                                          # a control with no kind >= 10x would be a STOP
        self.worst(pairs)

    def test_04_findings(self):
        F = flat({k: v for k, v in self.spec["findings"].items()})
        N = flat(self.n["findings"])
        self.assertEqual(sorted(F), sorted(N))
        print("\n  ATR findings: %d values, worst |diff| %.3e" % (len(F), self.worst([(k, F[k], N[k]) for k in F])))

    def test_05_imp_fire_test(self):
        ft = self.spec["imp"]["fire_test"]
        p = "ATR"
        pairs = []
        for key, val in ft.items():
            if isinstance(val, float):
                vid = key.split("_vs_")[0].upper()
                pairs.append((key, val, self.n["fire"]["%s-%s-imp-fail" % (p, vid)]["actual"]))
                pairs.append((key + "/ratio", ft["must_fail_ratio"][key], self.n["fire"]["%s-%s-imp-fail" % (p, vid)]["ratio"]))
        for vid, val in ft["must_pass_own_model"].items():
            pairs.append((vid, val, self.n["fire"]["%s-%s-imp-pass" % (p, vid)]["actual"]))
            self.assertEqual(val, 0.0)
        for vid, val in ft["discrimination"].items():
            pairs.append((vid, val, self.n["discrimination"][vid]["actual"]))
        for vid, val in ft["exported_x_15f"].items():
            pairs.append((vid, val, self.n["imp15"]["%s-%s-imp-pass" % (p, vid)]["actual"]))
            self.assertLess(val * 10, self.spec["tolerances"]["imp"]["value"])      # floor x 10 inside the 1e-12 tolerance
        self.worst(pairs)
        self.assertTrue(all(self.n["fire"][k]["result"] == "PASS" for k in self.n["fire"]))
        self.assertEqual(len(ft["exported_x_15f"]), 9)

    def test_06_planning_chat_classification_equals_the_spec(self):
        """The planning chat's printed 'checked' / 'INFO' column (ATR_STAGE1_NUMBERS_output.txt) is the spec's (none INFO)."""
        with open(A.NUMBERS_OUT, encoding="utf-8") as f:
            txt = f.read()
        self.assertEqual(txt.count("-> checked"), 32)
        self.assertEqual(txt.count("-> INFO"), 0)

    def test_07_spec_includes_the_cross_check_preregistration(self):
        cc = self.spec["cross_check"]
        self.assertEqual(cc["script"], "strategies/tests/XCHK_ATRMT4_vs_ATRS.c")
        self.assertIn("1e-9", cc["criterion"])
        self.assertIn(">= 100", cc["criterion"])
        self.assertEqual(cc["variants"], 1)


if __name__ == "__main__":
    unittest.main()
