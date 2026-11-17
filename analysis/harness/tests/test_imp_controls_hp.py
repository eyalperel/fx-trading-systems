"""IMP must_pass for every HP negative control (own model). Spec: HP_ArticleFidelity.toml.
Rule (CLAUDE.md 4.4): the discrimination is seen to fire (control replayed with the corrected model FAILS).
Labels: (b) verified here."""
import copy
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)

import checker as C        # noqa: E402
import generator as G      # noqa: E402
import reference as R      # noqa: E402
import hp_fixture as FX    # noqa: E402

SPEC = os.path.join(HARNESS, "specs", "HP_ArticleFidelity.toml")
K = math.sqrt(2.0) / 2.0
NEW = {   # control -> (model string, hook-built filter factory)
    "NCA": ("hp_code(48, PI_ZORRO, SQRT_HALF, alpha_bump=1)", lambda: R.hp_code(48, k=K, alpha_bump=1)),
    "NCB": ("hp_code(48, PI_ZORRO, SQRT_HALF, in_bump=1)", lambda: R.hp_code(48, k=K, in_bump=1)),
    "NCF": ("hp_code(48, PI_ZORRO, SQRT_HALF, fb2_bump=1)", lambda: R.hp_code(48, k=K, fb2_bump=1)),
    "NCZ": ("hp_code(48, PI_ZORRO, SQRT_HALF, num=1st)", lambda: R.hp_code(48, k=K, num="1st")),
    "NC1": ("hp_code(49, PI_ZORRO, SQRT_HALF)", lambda: R.hp_code(49, k=K)),
    "NC2": ("hp_code(20, PI_ZORRO, SQRT_HALF, deg)", lambda: R.hp_code(20, k=K, deg=True)),
}


def spec_of():
    return G.load_spec(SPEC)


class TestImpControlModels(unittest.TestCase):
    def test_01_strings_resolve_and_equal_hook_built(self):
        for vid, (s, fac) in NEW.items():
            self.assertIn(s, R.IMP_MODELS, vid)
            a, b = R.IMP_MODELS[s](), fac()
            self.assertEqual((a.b, a.a), (b.b, b.a), vid)

    def test_02_unknown_variant_string_still_refused(self):
        self.assertNotIn("hp_code(48, PI_ZORRO, SQRT_HALF, alpha_bump=2)", R.IMP_MODELS)

    def test_03_spec_must_pass_lists_every_control(self):
        s = spec_of()
        ids = {v["id"] for v in s["variants"]}
        mp, mf = s["imp"]["must_pass"], s["imp"]["must_fail"]
        for k in list(mp) + list(mf):
            self.assertIn(k, ids)
        for v in s["variants"]:
            self.assertIn(v["id"], mp, "no must_pass for %s" % v["id"])
        for vid, (m, _) in NEW.items():
            self.assertEqual(mp[vid], m)
        self.assertEqual(mp["NCS"], "hp_code(48, PI_ZORRO, SQRT_HALF)")
        self.assertEqual(mp["NCH"], "hp_code(48, PI_ZORRO, F32_0707)")
        self.assertEqual(G.validate_spec(s)[0], [])


class TestImpControlsReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = G.to_checker_spec(spec_of())
        ov = {}
        for v in cls.spec["variants"]:
            vid = v["id"]
            m = cls.spec["imp"]["must_pass"][vid]
            ov[vid] = (R.IMP_MODELS[m](), v.get("seed", "price"))
        cls.cols = FX.build_cols(cls.spec, override=ov)

    def raw(self, cols):
        r = C.Raw()
        r.header = list(cols)
        r.cols = {k: np.array(v) for k, v in cols.items()}
        r.nrows = len(cols["n"])
        return r

    def test_04_own_model_replay_passes_for_every_variant(self):
        rows = [r for r in C.imp_rows(self.spec, self.raw(self.cols)) if r["check_id"].endswith("imp-pass")]
        self.assertEqual(len(rows), 12)
        for r in rows:
            self.assertEqual(r["result"], "PASS", "%s %.3e" % (r["check_id"], r["actual"]))

    def test_05_discrimination_rule_all_controls(self):
        """Uniform rule: control's own-model output vs hp_code(P_expected, PI_ZORRO, SQRT_HALF) with seed ZERO,
        P_expected = P of the control's expected table (48 for all, 20 for NC2). Must be > 1e-9 (fires: FAIL)."""
        import re
        ctrls = [v["id"] for v in self.spec["variants"] if v["id"].startswith("NC")]
        self.assertEqual(len(ctrls), 8)
        self.seen = {}
        for vid in ctrls:
            spec = copy.deepcopy(self.spec)
            v = [x for x in spec["variants"] if x["id"] == vid][0]
            pexp = int(re.fullmatch(r"hp_article\((\d+)\)", v["article"]).group(1))
            self.assertEqual(pexp, 20 if vid == "NC2" else 48, vid)
            v["seed"] = "zero"
            spec["imp"]["must_pass"][vid] = "hp_code(%d, PI_ZORRO, SQRT_HALF)" % pexp
            row = [r for r in C.imp_rows(spec, self.raw(self.cols)) if r["check_id"] == "HPF-%s-imp-pass" % vid]
            self.assertEqual(len(row), 1)
            self.assertEqual(row[0]["result"], "FAIL", "%s residual %.3e" % (vid, row[0]["actual"]))
            self.assertGreater(row[0]["actual"], 1e-9)
            self.seen[vid] = row[0]["actual"]

    def test_06_every_must_pass_and_must_fail_key_is_a_variant(self):
        ids = {v["id"] for v in self.spec["variants"]}
        for lst in ("must_pass", "must_fail"):
            for k in self.spec["imp"][lst]:
                self.assertIn(k, ids)


if __name__ == "__main__":
    unittest.main()
