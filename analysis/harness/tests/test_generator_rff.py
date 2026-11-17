"""Tests for the RFF generator tooling (stage 1): `params = [..]` (decision 1A), `[zorro].include` as a list (1A),
`[inputs].alternating` (2A) and its expected-table keys gain_alt / phase_alt, and byte-identical regeneration of the four
existing specs (H1, SS2F, SS3F, HPF).

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
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)

import generator as G    # noqa: E402

SPECS = os.path.join(HARNESS, "specs")
RFF = os.path.join(SPECS, "RFF_ArticleFidelity.toml")
# the four existing specs and the committed generated scripts they must reproduce byte for byte
EXISTING = (("H1_SuperSmoother2Pole.toml", "GEN_H1_SuperSmoother2Pole.c"),
            ("SS2_ArticleFidelity.toml", "GEN_SS2F_SuperSmoother2Pole.c"),
            ("SS3_ArticleFidelity.toml", "GEN_SS3F_SuperSmoother3Pole.c"),
            ("HP_ArticleFidelity.toml", "GEN_HPF_HighPassFilter.c"))


def codes(spec):
    errs, infos = G.validate_spec(spec)
    return [c for c, _ in errs]


def rff():
    return copy.deepcopy(G.load_spec(RFF))


def committed(name):
    """The committed generated script. The Windows working copy is CRLF (autocrlf), the repo LF: compare LF."""
    with open(os.path.join(ROOT, "strategies", "tests", name), "rb") as f:
        return f.read().replace(b"\r\n", b"\n").decode("utf-8")


class TestByteIdenticalRegeneration(unittest.TestCase):
    def test_01_four_existing_specs_regenerate_the_committed_scripts(self):
        for spec_name, gen_name in EXISTING:
            text, _ = G.build_script(G.load_spec(os.path.join(SPECS, spec_name)))
            self.assertEqual(text, committed(gen_name), spec_name)
        print("\n  [regen] H1, SS2F, SS3F, HPF: build_script == committed GEN_*.c (LF-normalised), 4 of 4")

    def test_02_the_comparison_fires(self):
        """Fire: an altered spec (SS3F, one parameter) no longer matches the committed script, and neither does an
        existing spec given the alternating flag (the flag changes the script)."""
        s = G.load_spec(os.path.join(SPECS, "SS3_ArticleFidelity.toml"))
        s["variants"][0]["param"] = s["variants"][0]["param"] + 1
        self.assertNotEqual(G.build_script(s)[0], committed("GEN_SS3F_SuperSmoother3Pole.c"))
        h = G.load_spec(os.path.join(SPECS, "HP_ArticleFidelity.toml"))
        h["inputs"]["alternating"] = True
        for t in h["expected"].values():
            t["gain_alt"] = 0.0
        self.assertNotEqual(G.build_script(h)[0], committed("GEN_HPF_HighPassFilter.c"))

    def test_03_param_equals_one_element_params(self):
        for spec_name, _ in EXISTING:
            a = G.load_spec(os.path.join(SPECS, spec_name))
            b = copy.deepcopy(a)
            for v in b["variants"]:
                v["params"] = [v.pop("param")]
            self.assertEqual(G.build_script(a)[0], G.build_script(b)[0], spec_name)
            self.assertEqual(G.to_checker_spec(a), G.to_checker_spec(b), spec_name)

    def test_04_include_string_equals_one_element_list(self):
        for spec_name, _ in EXISTING:
            a = G.load_spec(os.path.join(SPECS, spec_name))
            b = copy.deepcopy(a)
            b["zorro"]["include"] = [a["zorro"]["include"]]
            self.assertEqual(G.build_script(a)[0], G.build_script(b)[0], spec_name)


class TestParamsAndInclude(unittest.TestCase):
    def test_05_two_integer_params_in_the_call(self):
        text, _ = G.build_script(rff())
        self.assertIn("Y[0] = RoofingFilter(S0, 48, 10);\t// P48S10 flat", text)
        self.assertIn("Y[8] = RoofingFilter(S0, 30, 10);\t// P30S10 flat", text)
        self.assertIn("Y[16] = RoofingFilter(S0, 125, 10);\t// P125S10 flat", text)
        self.assertIn("Y[24] = RoofingFilter(S0, 48, 20);\t// P48S20 flat", text)
        self.assertIn("rff_nca(S0, 48, 10);", text)
        self.assertIn("RoofingFilter(S0, 49, 10);\t// NC1 flat", text)
        self.assertIn("RoofingFilter(S0, 48, 11);\t// NC1s flat", text)

    def test_06_three_params_and_one_param(self):
        s = rff()
        s["variants"][0]["params"] = [1, 2, 3]
        self.assertIn("RoofingFilter(S0, 1, 2, 3);", G.build_script(s)[0])
        s["variants"][0]["params"] = [7]
        self.assertIn("RoofingFilter(S0, 7);", G.build_script(s)[0])

    def test_07_include_list_in_dependency_order(self):
        text, _ = G.build_script(rff())
        lines = [l for l in text.split("\n") if l.startswith("#include")]
        self.assertEqual(lines, ['#include <default.c>',
                                 '#include "../../indicators/ehlers/HighPassFilter.c"',
                                 '#include "../../indicators/ehlers/SuperSmoother2Pole.c"',
                                 '#include "../../indicators/ehlers/RoofingFilter.c"'])

    def test_08_refusals_params(self):
        bad = {"empty": [], "float": [48.0, 10], "string": ["48", 10], "bool": [True, 10], "not a list": 48,
               "nested": [[48, 10]], "None-like": "none"}
        for what, val in bad.items():
            s = rff()
            s["variants"][0]["params"] = val
            self.assertIn("PARAMS_BAD", codes(s), what)
        s = rff()
        s["variants"][0]["param"] = 48                        # both given
        self.assertIn("PARAMS_BAD", codes(s))
        s = rff()
        del s["variants"][0]["params"]                         # neither given
        self.assertIn("STRUCT", codes(s))
        s = rff()
        s["variants"][0]["params"] = [48, 10]                   # control: clean
        self.assertEqual(codes(s), [])

    def test_09_refusals_include(self):
        for what, val in {"empty list": [], "empty string": "", "non-string element": ["a.c", 3], "empty element": ["a.c", ""],
                          "number": 5}.items():
            s = rff()
            s["zorro"]["include"] = val
            self.assertIn("INCLUDE_BAD", codes(s), what)

    def test_10_lint_checks_every_listed_include(self):
        """L_INCLUDE (gotchas 9d.3) applies to each element: a missing second include in the list is caught."""
        s = rff()
        s["zorro"]["include"][1] = "../../indicators/ehlers/NoSuchIndicator.c"
        text, bodies = G.build_script(s)
        issues = G.lint_script(text, bodies, allow=G.lint_allowances(s))
        self.assertTrue(any(r == "L_INCLUDE" and "NoSuchIndicator" in m for r, m in issues), issues)
        text, bodies = G.build_script(rff())
        self.assertEqual(G.lint_script(text, bodies, allow=G.lint_allowances(rff())), [])


class TestAlternating(unittest.TestCase):
    def test_11_input_ids_and_slots(self):
        s = rff()
        self.assertEqual(G.input_ids(s), ["flat", "s5", "s10", "s20", "s40", "s100", "alt", "ramp"])
        s["inputs"]["alternating"] = False
        for t in s["expected"].values():
            del t["gain_alt"]
        self.assertEqual(G.input_ids(s), ["flat", "s5", "s10", "s20", "s40", "s100", "ramp"])
        h = G.load_spec(os.path.join(SPECS, "HP_ArticleFidelity.toml"))
        self.assertEqual(G.input_ids(h), ["flat", "s5", "s10", "s20", "s40", "s100", "ramp"])      # no key: unchanged

    def test_12_script_has_the_alt_input_without_decimal_literals(self):
        text, _ = G.build_script(rff())
        self.assertIn("static int rff_sgn = 1;", text)
        self.assertIn("rff_sgn = 1;\t// declared initialisers", text)                 # reset at INITRUN (gotchas 6)
        self.assertIn("X[6] = lvl + amp * rff_sgn;", text)                           # after the sines (X[1..5]), before ramp
        self.assertIn("X[7] = lvl + slp * n;", text)
        self.assertIn("rff_sgn = -rff_sgn;", text)
        self.assertIn("var X[8];", text)
        self.assertIn("var Y[88];", text)
        self.assertEqual(text.count("x_alt"), 1)                                      # header column
        self.assertIn(",x_s100,x_alt,x_ramp", text)
        # the sign flips in the same branch as the bar counter, after the row is written (not on the last row)
        i = text.index("rff_n += 1;")
        self.assertLess(i, text.index("rff_sgn = -rff_sgn;"))
        self.assertLess(text.index("rff_sgn = -rff_sgn;"), text.index("}", i))

    def test_13_script_without_the_flag_has_no_alt_code(self):
        text, _ = G.build_script(G.load_spec(os.path.join(SPECS, "HP_ArticleFidelity.toml")))
        for tok in ("_sgn", "x_alt", "alternating"):
            self.assertNotIn(tok, text)

    def test_14_lint_clean_and_checker_dict(self):
        s = rff()
        text, bodies = G.build_script(s)
        self.assertEqual(G.lint_script(text, bodies, allow=G.lint_allowances(s)), [])
        cs = G.to_checker_spec(s)
        self.assertTrue(cs["alt"])
        self.assertEqual(cs["phase_gate"], 0.05)
        for v in cs["variants"]:
            self.assertIn("gain_alt", v)
            self.assertNotIn("phase_alt", v)                                          # gain_alt << gate in every table
        h = G.to_checker_spec(G.load_spec(os.path.join(SPECS, "HP_ArticleFidelity.toml")))
        self.assertNotIn("alt", h)
        self.assertNotIn("phase_gate", h)
        self.assertTrue(all("gain_alt" not in v for v in h["variants"]))

    def test_15_startup_inputs_may_name_alt_and_a_sine(self):
        s = rff()
        s["checks"]["startup_inputs"] = ["flat", "alt", "s20", "s5"]
        self.assertEqual(codes(s), [])
        self.assertEqual(G.to_checker_spec(s)["startup"], ["flat", "alt", "s20", "s5"])
        for bad in (["alt", "s7"], ["nope"], []):
            s["checks"]["startup_inputs"] = bad
            self.assertIn("STARTUP_BAD", codes(s), bad)
        # fire: without the flag, 'alt' is not an input
        h = G.load_spec(os.path.join(SPECS, "HP_ArticleFidelity.toml"))
        h["checks"]["startup_inputs"] = ["flat", "alt"]
        self.assertIn("STARTUP_BAD", codes(h))

    def test_16_alt_flag_must_be_boolean(self):
        for bad in ("true", 1, [True]):
            s = rff()
            s["inputs"]["alternating"] = bad
            self.assertIn("ALT_BAD", codes(s), repr(bad))

    def test_17_gain_alt_required_with_the_flag(self):
        s = rff()
        del s["expected"]["P48S10"]["gain_alt"]
        self.assertIn("STRUCT", codes(s))
        s = rff()
        s["expected"]["P48S10"]["gain_alt"] = "0"
        self.assertIn("STRUCT", codes(s))

    def test_18_alt_keys_refused_without_the_flag(self):
        h = G.load_spec(os.path.join(SPECS, "HP_ArticleFidelity.toml"))
        h["expected"]["P48"]["gain_alt"] = 0.0
        self.assertIn("ALT_NOT_ENABLED", codes(h))
        h = G.load_spec(os.path.join(SPECS, "HP_ArticleFidelity.toml"))
        h["expected"]["P48"]["phase_alt"] = 0.0
        self.assertIn("ALT_NOT_ENABLED", codes(h))

    def test_19_phase_alt_follows_the_gate(self):
        """gain_alt >= gate needs phase_alt; gain_alt < gate must not list one (it would be SKIPped); both sides fire."""
        s = rff()
        s["expected"]["P48S10"]["gain_alt"] = 0.2                                  # >= gate 0.05, no phase_alt
        self.assertIn("ALT_PHASE_MISSING", codes(s))
        s["expected"]["P48S10"]["phase_alt"] = math_pi()                           # now listed: clean
        self.assertEqual(codes(s), [])
        s["expected"]["P48S10"]["gain_alt"] = 0.01                                 # < gate but phase_alt listed
        self.assertIn("PHASE_GATE", codes(s))
        s = rff()
        s["expected"]["P48S10"]["gain_alt"] = 0.2
        s["expected"]["P48S10"]["phase_alt"] = 4.0                                 # outside (-pi, pi]
        self.assertIn("PHASE_BAD", codes(s))

    def test_20_gate_required_with_the_flag(self):
        s = rff()
        del s["checks"]["phase_gate"]
        self.assertIn("PHASE_GATE_MISSING", codes(s))

    def test_21_phase_tolerance_required_when_only_alt_exists(self):
        s = rff()
        del s["tolerances"]["phase"]
        self.assertIn("STRUCT", codes(s))

    def test_22_rff_spec_cli_lint(self):
        r = subprocess.run([sys.executable, os.path.join(HARNESS, "generator.py"), RFF, "--lint-only"],
                           capture_output=True, text=True, cwd=HARNESS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("lint clean", r.stdout)
        self.assertEqual(r.stdout.count("INFO D2 margin"), 7)
        self.assertNotIn("NOT met", r.stdout)
        self.assertNotIn("EXCEEDS", r.stdout)
        print("\n  [lint] RFF spec: " + r.stdout.strip().splitlines()[-1] + " (7 D2 margin lines, all met, 5 floor windows ok)")


def math_pi():
    import math
    return math.pi


if __name__ == "__main__":
    unittest.main()
