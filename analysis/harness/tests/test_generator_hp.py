"""Tests for the HP generator schema + lint (HARNESS_DESIGN D4): [checks] dc_gain / phase_gate / startup_inputs,
[tolerances.phase|resid|startup], expected.<P>.phases / .resid / .article, variant seed, new detect kinds,
INFO lines for the new kinds. SS2 / SS3 specs must lint exactly as before.

Rule (CLAUDE.md 4.4): each refusal is seen to fire on a deliberately broken spec, one defect at a time.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)

import generator as G      # noqa: E402
import hp_fixture as FX    # noqa: E402

SS2 = os.path.join(HARNESS, "specs", "SS2_ArticleFidelity.toml")
SS3 = os.path.join(HARNESS, "specs", "SS3_ArticleFidelity.toml")
H1 = os.path.join(HARNESS, "specs", "H1_SuperSmoother2Pole.toml")


def codes(spec):
    errs, infos = G.validate_spec(spec)
    return [c for c, _ in errs], infos


class TestHpSchema(unittest.TestCase):
    def test_01_fixture_is_clean(self):
        errs, infos = G.validate_spec(FX.toml_spec())
        self.assertEqual(errs, [])
        txt = "\n".join(infos)
        for q in ("phase", "resid", "startup"):
            self.assertIn("INFO D2 floor %s:" % q, txt)
        self.assertNotIn("INFO D2 floor lag", txt)                  # no lag at dc_gain 0
        for vid in FX.CONTROLS:
            self.assertIn("INFO D2 margin %s:" % vid, txt)

    def test_02_checker_dict_keys(self):
        cs = G.to_checker_spec(FX.toml_spec())
        self.assertEqual(cs["dc_gain"], 0.0)
        self.assertEqual((cs["tol_phase"], cs["tol_resid"], cs["tol_startup"]),
                         (FX.TOL["phase"], FX.TOL["resid"], FX.TOL["startup"]))
        self.assertEqual(cs["startup"], ["flat", "ramp"])
        v = [v for v in cs["variants"] if v["id"] == "P48"][0]
        self.assertEqual((v["seed"], v["article"], v["resid"]), ("zero", "hp_article(48)", 0.0))
        self.assertTrue(all(isinstance(k, int) for k in v["phases"]))
        self.assertIsNone(v["expected"][2])                          # no ramp-lag value at dc_gain 0
        self.assertEqual(sorted(v["phases"]), [t for t in FX.TS if t in v["phases"]])

    def test_03_old_specs_unchanged_dict(self):
        for path in (SS2, SS3):
            cs = G.to_checker_spec(G.load_spec(path))
            for k in ("dc_gain", "tol_phase", "tol_resid", "tol_startup", "startup"):
                self.assertNotIn(k, cs, "%s must not appear for %s" % (k, os.path.basename(path)))
            for v in cs["variants"]:
                for k in ("phases", "resid", "article", "seed"):
                    self.assertNotIn(k, v)
                self.assertIsNotNone(v["expected"][2])

    def test_04_old_specs_lint_output_identical(self):
        """Compare against the stored HEAD output (scratch baseline), when it is there; always check structure."""
        for path in (H1, SS2, SS3):
            r = subprocess.run([sys.executable, os.path.join(HARNESS, "generator.py"), path, "--lint-only"],
                               capture_output=True, text=True, cwd=HARNESS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("lint clean", r.stdout)
            self.assertNotIn("phase", r.stdout)
            self.assertNotIn("startup", r.stdout)
            base = os.environ.get("HARNESS_LINT_BASELINE")
            if base:
                bp = os.path.join(base, "lint_%s.txt" % os.path.splitext(os.path.basename(path))[0])
                if os.path.isfile(bp):
                    self.assertEqual(r.stdout.replace("\r\n", "\n"), open(bp, encoding="utf-8").read().replace("\r\n", "\n"))


class TestHpRefusals(unittest.TestCase):
    def broken(self, fn):
        s = FX.toml_spec()
        fn(s)
        return codes(s)[0]

    def test_05_phase_gate_lint(self):
        """A listed phase period whose reference gain is below the gate is refused. P20 gain at T=5 is ~1:
        raise the gate above every gain at P125/T=100 and list it."""
        def f(s):
            s["expected"]["P125"]["phases"][100] = 0.5          # P125 gain at T=100 is below the 0.1 gate? check below
            s["expected"]["P125"]["gains"][-1] = 0.05
        self.assertIn("PHASE_GATE", self.broken(f))
        # control: the same spec with the gain above the gate is clean
        def g(s):
            s["expected"]["P125"]["phases"][100] = 0.5
            s["expected"]["P125"]["gains"][-1] = 0.5
        self.assertNotIn("PHASE_GATE", self.broken(g))

    def test_06_phase_gate_missing(self):
        def f(s):
            del s["checks"]["phase_gate"]
        self.assertIn("PHASE_GATE_MISSING", self.broken(f))

    def test_07_phase_period_not_a_sine_period(self):
        def f(s):
            s["expected"]["P48"]["phases"][7] = 0.1
        self.assertIn("PHASE_BAD", self.broken(f))

    def test_08_phase_value_out_of_range_or_not_number(self):
        def f(s):
            s["expected"]["P48"]["phases"][20] = 4.0             # outside (-pi, pi]
        self.assertIn("PHASE_BAD", self.broken(f))
        def g(s):
            s["expected"]["P48"]["phases"][20] = "0.5"
        self.assertIn("PHASE_BAD", self.broken(g))

    def test_09_tolerances_required(self):
        for q in ("phase", "resid", "startup"):
            def f(s, q=q):
                del s["tolerances"][q]
            self.assertIn("STRUCT", self.broken(f), q)
        def g(s):
            s["tolerances"]["phase"]["source"] = "no label"
        self.assertIn("SOURCE_MISSING", self.broken(g))

    def test_10_resid_required_at_dc_gain_zero(self):
        def f(s):
            del s["expected"]["P48"]["resid"]
        self.assertIn("STRUCT", self.broken(f))

    def test_11_lag_refused_at_dc_gain_zero(self):
        def f(s):
            s["expected"]["P48"]["lag"] = 1.0
        self.assertIn("LAG_NOT_APPLICABLE", self.broken(f))

    def test_12_lag_still_required_at_dc_gain_one(self):
        """Fire on the old behaviour: a spec with dc_gain 1 (or no [checks]) still needs a lag value."""
        s = G.load_spec(SS3)
        del s["expected"]["P10"]["lag"]
        self.assertIn("STRUCT", codes(s)[0])
        s2 = FX.toml_spec()
        s2["checks"]["dc_gain"] = 1.0
        self.assertIn("STRUCT", codes(s2)[0])                    # fixture tables carry no lag

    def test_13_startup_inputs(self):
        def f(s):
            s["checks"]["startup_inputs"] = ["flat", "s7"]
        self.assertIn("STARTUP_BAD", self.broken(f))
        def g(s):
            s["checks"]["startup_inputs"] = []
        self.assertIn("STARTUP_BAD", self.broken(g))

    def test_14_article_model_required_and_resolvable(self):
        def f(s):
            del s["expected"]["P48"]["article"]
        self.assertIn("ARTICLE_MODEL", self.broken(f))
        def g(s):
            s["expected"]["P48"]["article"] = "hp_article(48); x"
        self.assertIn("ARTICLE_MODEL", self.broken(g))

    def test_15_seed(self):
        def f(s):
            s["variants"][0]["seed"] = "ones"
        self.assertIn("SEED_BAD", self.broken(f))
        def g(s):
            del s["variants"][0]["seed"]
        self.assertNotIn("SEED_BAD", self.broken(g))             # optional, default price

    def test_16_dc_gain_value(self):
        def f(s):
            s["checks"]["dc_gain"] = "zero"
        self.assertIn("CHECKS_BAD", self.broken(f))

    def test_17_new_detect_kinds_accepted_and_unknown_refused(self):
        s = FX.toml_spec()
        s["detect"]["required"]["NCS"] = ["startup"]
        self.assertEqual(codes(s)[0], [])
        s["detect"]["required"]["NCS"] = ["startup", "bogus"]
        self.assertIn("DETECT_BAD_KIND", codes(s)[0])
        s = FX.toml_spec()
        s["effect_corrections"] = {"NCS": dict(startup=1.0, source="(b) x")}
        self.assertEqual(codes(s)[0], [])

    def test_18_info_floor_window_fires(self):
        s = FX.toml_spec()
        s["floor"]["phase"] = FX.TOL["phase"] / 2             # x10 exceeds tolerance
        errs, infos = G.validate_spec(s)
        self.assertEqual(errs, [])
        self.assertTrue(any("floor phase" in l and "FLOOR x10 EXCEEDS TOLERANCE" in l for l in infos), infos)
        self.assertTrue(any("floor gain" in l and "window ok" in l for l in infos))      # others unaffected

    def test_19_info_per_control_margin_new_kinds(self):
        errs, infos = G.validate_spec(FX.toml_spec())
        line = {l.split(":")[0]: l for l in infos}
        self.assertIn("startup", line["INFO D2 margin NCS"])
        self.assertIn("10x margin met", line["INFO D2 margin NCS"])
        self.assertIn("resid", line["INFO D2 margin NCZ"])
        s = FX.toml_spec()
        [v for v in s["variants"] if v["id"] == "NCS"][0]["effect"]["startup"] = FX.TOL["startup"] * 2
        errs, infos = G.validate_spec(s)
        self.assertTrue(any("margin NCS" in l and "10x margin NOT met" in l for l in infos), infos)

    def test_20_build_script_still_works_for_hp_spec(self):
        text, bodies = G.build_script(FX.toml_spec())
        self.assertIn("GEN_HPF_fixture", text)
        self.assertIn("LookBack  = 0;", text)                    # rows from n = 0 are exported (start-up check)
        self.assertEqual(len(bodies), 7)                          # inline controls (all but NC1)


if __name__ == "__main__":
    unittest.main()
