"""MAF stage 1, pre-run item (iii) of both specs: reference.py and the checker reproduce every (b) number the specs store (conditioning
values and classification, floors, control effects, [detect.required] = every kind >= 10x, [findings], IMP fire tests) to <= 1e-9
relative (absolute 1e-15 below 1e-6). As for LRSI / FSH the specs were generated from this code, so 0 is self-consistency; the
comparison with the planning chat's independent numbers is test_reference_maf (brief items 1-7).
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import maf_support as S      # noqa: E402

G, C = S.G, S.C
_N = {}


def nb(path):
    if path not in _N:
        _N[path] = S.numbers(path)
    return _N[path]


def close(a, b):
    a, b = float(a), float(b)
    if math.isnan(a) or math.isnan(b):
        return math.isnan(a) and math.isnan(b)
    return abs(a - b) <= max(1e-9 * max(abs(a), abs(b)), 1e-15 if max(abs(a), abs(b)) < 1e-6 else 0.0)


class _Spec:
    PATH = None

    @classmethod
    def setUpClass(cls):
        cls.spec = G.load_spec(cls.PATH)
        cls.n = nb(cls.PATH)

    def worst(self, pairs):
        bad = [(k, a, b) for k, a, b in pairs if not close(a, b)]
        self.assertEqual(bad, [])
        return max((abs(float(a) - float(b)) for _, a, b in pairs), default=0.0)

    def test_01_conditioning(self):
        pairs = []
        for t, vals in self.n["conditioning"].items():
            cc = self.spec["expected"][t]["conditioning"]
            self.assertEqual({i: sorted(l) for i, l in cc["info"].items()}, {i: sorted(l) for i, l in self.n["info"][t].items()})
            self.assertEqual(sorted(cc["values"]), sorted(vals))
            pairs += [("%s/%s/%s" % (t, i, c), cc["values"][i][c], v) for i, cv in vals.items() for c, v in cv.items()]
        print("\n  %s conditioning: %d values, worst |diff| %.3e" % (self.spec["batch"]["id_prefix"], len(pairs), self.worst(pairs)))

    def test_02_floor(self):
        fl = self.spec["floor"]
        pairs = [(k, fl[k], v) for k, v in self.n["floor"].items()]
        self.assertTrue(all(k in fl for k in self.n["floor"]))
        self.worst(pairs)

    def test_03_effects_and_detect(self):
        pairs = []
        for v in self.spec["variants"]:
            if v["role"] in ("neg_control", "info"):
                eff = {k: x for k, x in v["effect"].items() if k != "source"}
                self.assertEqual(sorted(eff), sorted(self.n["effects"][v["id"]]), v["id"])
                pairs += [("%s/%s" % (v["id"], k), eff[k], self.n["effects"][v["id"]][k]) for k in eff]
            if v["role"] == "neg_control":
                io = self.spec["detect"].get("info_only", {}).get(v["id"], [])          # kinds >= 10x kept INFO by review decision
                self.assertTrue(all(self.n["ratios"][v["id"]][k] >= 10 for k in io), v["id"])
                want = sorted(k for k, r in self.n["ratios"][v["id"]].items() if r >= 10 and k not in io)
                self.assertEqual(sorted(self.spec["detect"]["required"][v["id"]]), want, v["id"])
        self.worst(pairs)

    def test_04_findings(self):
        F = {k: v for k, v in self.spec["findings"].items() if k != "source"}
        self.assertEqual(sorted(F), sorted(self.n["findings"]))
        print("\n  %s findings: %d values, worst |diff| %.3e" % (self.spec["batch"]["id_prefix"], len(F),
                                                               self.worst([(k, F[k], self.n["findings"][k]) for k in F])))

    def test_05_imp_fire_test(self):
        ft = self.spec["imp"]["fire_test"]
        p = self.spec["batch"]["id_prefix"]
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
            self.assertLess(val, self.spec["tolerances"]["imp"]["value"] * 10)        # well inside even at the phase tolerance
        for vid, val in ft["exported_x_15f_info_max"].items():
            pairs.append((vid + "/info", val, self.n["imp15"]["%s-%s-imp-pass" % (p, vid)]["info_max"]))
        self.worst(pairs)
        self.assertTrue(all(self.n["fire"][k]["result"] == "PASS" for k in self.n["fire"]))


class TestMamaSpecNumbers(_Spec, unittest.TestCase):
    PATH = S.MAMA_SPEC


class TestFramaSpecNumbers(_Spec, unittest.TestCase):
    PATH = S.FRAMA_SPEC


if __name__ == "__main__":
    unittest.main()
