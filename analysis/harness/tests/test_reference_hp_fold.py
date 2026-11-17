"""Reference model for the OLD HighPassFilter.c (the NCH control) after the compile-time literal fold (Amendment 2).

Measured by strategies/tests/PROBE_LiteralEval_20261117.c (commit ba54022, results/PROBE_LiteralEval_20261117.csv):
Zorro 3.11 folds the all-literal product 0.707*2.0*PI at compile time to the float32 value 4.44221019744873047 (L04 =
L17); trig, division and recursion are plain double. reference.ZORRO_FOLD_0707x2xPI is that constant and
hp_code(P, theta_const=...) the model with theta = constant / P. Probe values below are copied from the results file
(%.17e); the test reads the file too when it is present (it is committed) and checks the copies are the file's values.

Labels: (b) measured by the probe, (c) the rule that produces the folded value is unknown.
Run with the rest of the suite: bash analysis/harness/run_tests.sh
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)

import reference as R   # noqa: E402

PROBE_CSV = os.path.join(HARNESS, "results", "PROBE_LiteralEval_20261117.csv")
# (b) probe values, %.17e
L04 = 4.44221019744873047e+00          # 0.707*2.0*PI folded at compile time (all-literal)
L05 = 9.25460457801818848e-02          # theta = literal product / 48
L10 = 8.85134449164305115e-02          # alpha, the old NCH function at P = 48
L13 = 9.25460111518153355e-02          # theta, runtime var path (var k = 0.707)
L14 = 8.85134132174892896e-02          # alpha, runtime var path
L15 = 8.85262062408208455e-02          # alpha, corrected function

# pre-change outputs of the existing models (recorded 2026-11-17 before this edit; the edit must not move them)
OLD48 = dict(b=(0.9134452428623631, -1.8268904857247261, 0.9134452428623631), a=(1.8229731735650214, -0.8308077978844314))
SQ48 = dict(b=(0.9134330160570273, -1.8268660321140546, 0.9134330160570273), a=(1.8229475875183583, -0.8307844767097506))
OLD20 = dict(b=(0.8094128568850664, -1.6188257137701327, 0.8094128568850664), a=(1.598695000991479, -0.6389564265487864))
NEW_KEY = "hp_code(48, ZORRO_FOLD_0707x2xPI)"
OLD_KEY = "hp_code(48, PI_ZORRO, F32_0707)"


class TestZorroFoldModel(unittest.TestCase):
    def test_constant_is_the_probe_value_and_a_float32(self):
        c = R.ZORRO_FOLD_0707x2xPI
        self.assertEqual(c, L04)
        self.assertEqual(float(np.float32(c)), c, "the folded value is a float32 (L04 is a float32 print)")

    def test_probe_copies_match_the_committed_probe_file(self):
        if not os.path.isfile(PROBE_CSV):
            self.skipTest("probe results file absent: %s" % PROBE_CSV)
        vals = {}
        for ln in open(PROBE_CSV, encoding="utf-8"):
            k, v = ln.strip().split(",")
            vals[k.split("_")[0]] = float(v)
        for name, mine in (("L04", L04), ("L05", L05), ("L10", L10), ("L13", L13), ("L14", L14), ("L15", L15)):
            self.assertEqual(vals[name], mine, name)

    def test_theta_equals_probe_L05(self):
        theta = R.hp_theta(48, theta_const=R.ZORRO_FOLD_0707x2xPI)
        print("\n  theta(P=48) %.17e  L05 %.17e  |diff| %.2e" % (theta, L05, abs(theta - L05)))
        self.assertLessEqual(abs(theta - L05), 1e-16)

    def test_alpha_equals_probe_L10(self):
        a = R.hp_alpha(48, theta_const=R.ZORRO_FOLD_0707x2xPI)
        print("  alpha(P=48) %.17e  L10 %.17e  |diff| %.2e" % (a, L10, abs(a - L10)))
        self.assertLessEqual(abs(a - L10), 1e-16)

    def test_filter_uses_that_alpha(self):
        f = R.hp_code(48, theta_const=R.ZORRO_FOLD_0707x2xPI)
        a = R.hp_alpha(48, theta_const=R.ZORRO_FOLD_0707x2xPI)
        self.assertEqual(f.a[0], 2.0 * (1.0 - a))
        self.assertEqual(f.a[1], -(1.0 - a) * (1.0 - a))
        self.assertEqual(f.b[0], (1.0 - a / 2.0) * (1.0 - a / 2.0))

    def test_old_float32_model_equals_runtime_var_path(self):
        """The existing F32_0707 model is the runtime var path (probe L13 / L14): kept, and still what P48 must_fail uses."""
        self.assertLessEqual(abs(R.hp_theta(48) - L13), 1e-16)
        self.assertLessEqual(abs(R.hp_alpha(48) - L14), 1e-16)

    def test_guard_fires_old_model_is_not_the_probe_alpha(self):
        """The F32_0707 model's alpha differs from the Zorro literal alpha (L10) by 3.2e-8 abs / 3.6e-7 rel: the run-1 cause."""
        d = abs(R.hp_alpha(48) - L10)
        print("\n  [fire] F32_0707 alpha vs L10: |diff| %.3e (rel %.2e) > 1e-16" % (d, d / L10))
        self.assertGreater(d, 1e-8)
        self.assertGreater(abs(R.hp_alpha(48, k=math.sqrt(2.0) / 2.0) - L10), 1e-8)   # corrected-model alpha is not it
        self.assertLessEqual(abs(R.hp_alpha(48, k=math.sqrt(2.0) / 2.0) - L15), 1e-16)   # but it is L15

    def test_existing_models_unchanged_by_the_edit(self):
        for f, ref in ((R.hp_code(48), OLD48), (R.hp_code(48, k=math.sqrt(2.0) / 2.0), SQ48), (R.hp_code(20), OLD20)):
            self.assertEqual(tuple(f.b), ref["b"])
            self.assertEqual(tuple(f.a), ref["a"])

    def test_registry(self):
        self.assertIn(NEW_KEY, R.IMP_MODELS)
        self.assertEqual(R.IMP_MODELS[NEW_KEY](), R.hp_code(48, theta_const=R.ZORRO_FOLD_0707x2xPI))
        self.assertIn(OLD_KEY, R.IMP_MODELS)                                   # kept: P48 must_fail uses it
        self.assertEqual(R.IMP_MODELS[OLD_KEY](), R.hp_code(48))
        self.assertNotEqual(R.IMP_MODELS[NEW_KEY](), R.IMP_MODELS[OLD_KEY]())

    def test_theta_const_other_period_scales(self):
        """theta = constant / P, so P = 20 gives constant / 20 (the model is not hard-wired to 48)."""
        self.assertEqual(R.hp_theta(20, theta_const=R.ZORRO_FOLD_0707x2xPI), R.ZORRO_FOLD_0707x2xPI / 20)


class TestSpecAmendment2(unittest.TestCase):
    """The committed HP spec carries Amendment 2: [imp_corrections.NCH] replaces the NCH must_pass model only."""

    @classmethod
    def setUpClass(cls):
        import generator as G
        cls.G = G
        cls.path = os.path.join(HARNESS, "specs", "HP_ArticleFidelity.toml")
        cls.spec = G.load_spec(cls.path)

    def test_correction_fields_exactly_as_decided(self):
        c = self.spec["imp_corrections"]
        self.assertEqual(list(c), ["NCH"])
        self.assertEqual({k: c["NCH"][k] for k in ("list", "replaces", "model", "amendment")},
                         dict(list="must_pass", replaces=OLD_KEY, model=NEW_KEY, amendment="2"))
        self.assertTrue(c["NCH"]["source"].lstrip().startswith("(b)"))

    def test_record_in_imp_unchanged_and_amendment_header(self):
        imp = self.spec["imp"]
        self.assertEqual(imp["must_pass"]["NCH"], OLD_KEY)                    # the pre-registered record
        self.assertEqual(imp["must_fail"]["P48"], "hp_code(48, PI_ZORRO, F32_0707)")
        self.assertEqual(imp["must_fail"]["NCH"], "hp_code(48, PI_ZORRO, SQRT_HALF)")
        a = self.spec["amendment_2"]
        self.assertEqual((a["date"], a["after_run"], a["base_commit"]), ("2026-11-17", True, "ba54022"))

    def test_applied_to_checker_spec_nothing_else_moves(self):
        G = self.G
        errs, infos = G.validate_spec(self.spec)
        self.assertEqual(errs, [])
        self.assertIn("INFO IMP correction applied: NCH must_pass: %s -> %s (Amendment 2)" % (OLD_KEY, NEW_KEY), infos)
        d = G.to_checker_spec(self.spec)["imp"]
        self.assertEqual(d["must_pass"]["NCH"], NEW_KEY)
        self.assertEqual({k: v for k, v in d["must_pass"].items() if k != "NCH"},
                         {k: v for k, v in self.spec["imp"]["must_pass"].items() if k != "NCH"})
        self.assertEqual(d["must_fail"], self.spec["imp"]["must_fail"])
        self.assertEqual(d["tol"], 1e-9)

    def test_offline_replay_of_run1_nch_columns(self):
        """(c) evidence, not a run: run 1's raw NCH columns replayed (n >= 0, price seed). New model ~1e-15; the old
        model reproduces the run-1 residual 2.244e-7 (so the replay can fail)."""
        import checker as C
        raw_path = os.path.join(HARNESS, "results", "HP_ArticleFidelity_20261117_raw_run1.csv")
        if not os.path.isfile(raw_path):
            self.skipTest("run 1 raw copy absent (gitignored): %s" % raw_path)
        with open(raw_path, encoding="utf-8") as fh:
            raw = C.load_raw(fh)
        names = ["flat"] + ["s%d" % t for t in (5, 10, 20, 40, 100)] + ["ramp"]

        def resid(f):
            return max(float(np.max(np.abs(np.array(raw.cols["y_NCH_%s" % i])
                                           - R.simulate(f, np.array(raw.cols["x_%s" % i]), seed="price"))))
                       for i in names)
        new, old = resid(R.IMP_MODELS[NEW_KEY]()), resid(R.IMP_MODELS[OLD_KEY]())
        print("\n  run-1 NCH raw replay: new model %.3e, old model %.3e" % (new, old))
        self.assertLessEqual(new, 1e-9)
        self.assertGreater(old, 2.2e-7)
        self.assertLess(old, 2.3e-7)


if __name__ == "__main__":
    unittest.main()
