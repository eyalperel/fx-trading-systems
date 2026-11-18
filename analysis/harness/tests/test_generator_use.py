"""USE stage 1: generator tooling. Seed values `pass<n>` (variant seed and [checks].startup_seed), the variant role `info`,
the lint of the USE spec, the generated script's structure, and byte-identical regeneration of ALL FIVE existing specs
(H1, SS2F, SS3F, HPF, RFF) against the committed generated scripts.

Rule (CLAUDE.md 4.4): each refusal is seen to fire on a deliberately broken spec, one defect at a time.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
sys.path.insert(0, HARNESS)

import generator as G    # noqa: E402

SPECS = os.path.join(HARNESS, "specs")
USE = os.path.join(SPECS, "USE_ArticleFidelity.toml")
EXISTING = (("H1_SuperSmoother2Pole.toml", "GEN_H1_SuperSmoother2Pole.c"),
            ("SS2_ArticleFidelity.toml", "GEN_SS2F_SuperSmoother2Pole.c"),
            ("SS3_ArticleFidelity.toml", "GEN_SS3F_SuperSmoother3Pole.c"),
            ("HP_ArticleFidelity.toml", "GEN_HPF_HighPassFilter.c"),
            ("RFF_ArticleFidelity.toml", "GEN_RFF_RoofingFilter.c"))


def codes(spec):
    errs, _ = G.validate_spec(spec)
    return [c for c, _ in errs]


def use():
    return copy.deepcopy(G.load_spec(USE))


def committed(name):
    """The committed generated script (Windows working copy CRLF, repo LF: compare LF)."""
    with open(os.path.join(ROOT, "strategies", "tests", name), "rb") as f:
        return f.read().replace(b"\r\n", b"\n").decode("utf-8")


class TestByteIdenticalRegeneration(unittest.TestCase):
    def test_01_five_existing_specs_regenerate_the_committed_scripts(self):
        for spec_name, gen_name in EXISTING:
            text, _ = G.build_script(G.load_spec(os.path.join(SPECS, spec_name)))
            self.assertEqual(text, committed(gen_name), spec_name)
            self.assertNotIn("[info]", text, spec_name)
        print("\n  [regen] H1, SS2F, SS3F, HPF, RFF: build_script == committed GEN_*.c (LF-normalised), 5 of 5")

    def test_02_the_comparison_fires(self):
        s = G.load_spec(os.path.join(SPECS, "RFF_ArticleFidelity.toml"))
        s["variants"][0]["role"] = "info"                          # the new role changes the script header: not byte-identical
        self.assertNotEqual(G.build_script(s)[0], committed("GEN_RFF_RoofingFilter.c"))
        s = G.load_spec(os.path.join(SPECS, "SS3_ArticleFidelity.toml"))
        s["variants"][0]["param"] += 1
        self.assertNotEqual(G.build_script(s)[0], committed("GEN_SS3F_SuperSmoother3Pole.c"))

    def test_03_old_checker_dicts_carry_no_new_keys(self):
        for spec_name, _ in EXISTING:
            cs = G.to_checker_spec(G.load_spec(os.path.join(SPECS, spec_name)))
            self.assertNotIn("startup_seed", cs, spec_name)
            self.assertNotIn("info", [v["role"] for v in cs["variants"]], spec_name)


class TestSeedValues(unittest.TestCase):
    def test_04_pass_n_accepted(self):
        s = use()
        for seed in ("pass1", "pass3", "pass4", "pass12", "zero", "price"):
            s["variants"][0]["seed"] = seed
            self.assertNotIn("SEED_BAD", codes(s), seed)

    def test_05_bad_seeds_refused(self):
        for seed in ("pass0", "pass", "passx", "pass-3", "Pass3", "three", "pass3.5", 3):
            s = use()
            s["variants"][0]["seed"] = seed
            self.assertIn("SEED_BAD", codes(s), repr(seed))

    def test_06_startup_seed(self):
        s = use()
        for seed in ("pass3", "zero", "price"):
            s["checks"]["startup_seed"] = seed
            self.assertNotIn("STARTUP_BAD", codes(s), seed)
            self.assertEqual(G.to_checker_spec(s)["startup_seed"], seed)
        for seed in ("pass0", "passx", "", 3):
            s["checks"]["startup_seed"] = seed
            self.assertIn("STARTUP_BAD", codes(s), repr(seed))
        del s["checks"]["startup_seed"]
        self.assertNotIn("startup_seed", G.to_checker_spec(s))


class TestInfoRole(unittest.TestCase):
    def test_07_role_values(self):
        s = use()
        self.assertEqual(codes(s), [])
        s["variants"][4]["role"] = "bogus"
        self.assertIn("STRUCT", codes(s))

    def test_08_info_is_not_a_control(self):
        """[detect.required] may not list an info variant (DETECT_UNKNOWN_ID), and an info variant needs no entry."""
        s = use()
        self.assertNotIn("NCL", s["detect"]["required"])
        self.assertEqual(codes(s), [])
        s["detect"]["required"]["NCL"] = ["gain"]
        self.assertIn("DETECT_UNKNOWN_ID", codes(s))
        s = use()
        s["variants"][4]["role"] = "neg_control"                    # NCL as a control without a detect entry: refused
        self.assertIn("DETECT_MISSING", codes(s))

    def test_09_info_line_and_script_label(self):
        errs, infos = G.validate_spec(use())
        self.assertEqual(errs, [])
        line = [i for i in infos if "variant NCL" in i]
        self.assertEqual(len(line), 1)
        self.assertIn("never PASS/FAIL", line[0])
        text, _ = G.build_script(use())
        self.assertIn("NCL [info]", text)
        self.assertEqual(len(re.findall(r"\[control\]", text[:2000])), 6)


class TestUseSpecScript(unittest.TestCase):
    def test_10_lint_only_cli(self):
        r = subprocess.run([sys.executable, os.path.join(HARNESS, "generator.py"), USE, "--lint-only"],
                           capture_output=True, text=True, cwd=ROOT)
        print("\n" + r.stdout.strip().splitlines()[-1])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("lint clean; nothing written", r.stdout)
        self.assertIn("window ok", r.stdout)
        self.assertNotIn("FLOOR x10 EXCEEDS", r.stdout)
        self.assertNotIn("10x margin NOT met", r.stdout)
        self.assertEqual(r.stdout.count("10x margin met"), 6)

    def test_11_script_structure(self):
        s = use()
        text, bodies = G.build_script(s)
        self.assertEqual(G.lint_script(text, bodies), [])
        incs = re.findall(r'#include "([^"]+)"', text)
        self.assertEqual(incs, ["../../indicators/ehlers/HighPassFilter.c", "../../indicators/ehlers/UltimateSmootherE.c"])
        self.assertEqual(len(re.findall(r"^\tY\[\d+\] = ", text, re.M)), 11 * 8)             # 88 unconditional calls
        for p in (10, 14, 20, 30):
            self.assertIn("UltimateSmootherE(S0, %d);" % p, text)
        self.assertIn("UltimateSmootherE(S0, 21);", text)
        for fn in ("use_ncl", "use_nca", "use_ncb", "use_ncs", "use_ncx", "use_nc2"):
            self.assertEqual(len(re.findall(r"^var %s\(" % fn, text, re.M)), 1, fn)
        self.assertNotRegex(text, r"\bPeriod\b.*\bint\b.*\bUSP\b")
        self.assertEqual(len(bodies), 6)
        self.assertEqual(text, G.build_script(use())[0])                                     # deterministic

    def test_12_bodies_follow_gotcha_9d8(self):
        """No product / quotient of two decimal literals starts an expression; every decimal literal is float32-exact; the
        wrong constant (4.01, 0.001, 1.414, 3.14159) never appears as a literal: built from integers at run time."""
        text, bodies = G.build_script(use())
        for b in bodies:
            for lit in ("4.01", "0.001", "1.414", "3.14159", "1.0 / 1000"):
                self.assertNotIn(lit, b, lit)
            self.assertNotRegex(b, r"[=(]\s*-?\d+\.\d+\s*[*/]\s*\d")                          # literal op literal at expression start
        self.assertEqual(G.lint_script(text, bodies), [])

    def test_13_lint_fires_on_a_float32_literal_in_a_body(self):
        s = use()
        for v in s["variants"]:
            if v["id"] == "NCB":
                v["body"] = v["body"].replace("ncb_d = ncb_d / 100;", "ncb_d = 4.01;")
        text, bodies = G.build_script(s)
        issues = G.lint_script(text, bodies)
        print("\n  [fire] lint on 4.01 in a body: %s" % issues)
        self.assertTrue(any(r == "L_FLOAT32" for r, _ in issues))

    def test_14_script_has_no_pi_in_the_plumbing_and_no_alt_literals(self):
        text, bodies = G.build_script(use())
        plumbing = text
        for b in bodies:
            plumbing = plumbing.replace(b, " ")
        self.assertNotRegex(re.sub(r"//[^\n]*", "", plumbing), r"\bPI\b")
        self.assertIn("use_sgn", text)
        self.assertIn("X[6] = lvl + amp * use_sgn;", text)


if __name__ == "__main__":
    unittest.main()
