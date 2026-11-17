"""Tests for the scoped float32-literal exemption (variant fields lint_allow_float32 / lint_allow_reason).
Rule (CLAUDE.md 4.4): each refusal is seen to fire on a deliberately broken spec, one defect at a time.
Labels: (a) source states, (b) verified here, (c) inference."""
import copy
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)

import generator as G      # noqa: E402
import hp_fixture as FX    # noqa: E402

REASON = "reproduces the current file verbatim; float32 0.707 is the deviation itself (gotchas 9d.1)"


def variant(s, vid):
    return [v for v in s["variants"] if v["id"] == vid][0]


def set_body(s, vid, lit):
    v = variant(s, vid)
    v["body"] = "var %s(vars Price, int P)\n{\n\treturn Price[0] * %s;\n}" % (v["function"], lit)


def exempt_spec(lit="0.707"):
    s = FX.toml_spec()
    set_body(s, "NCH", lit)
    v = variant(s, "NCH")
    v["lint_allow_float32"] = [lit]
    v["lint_allow_reason"] = REASON
    return s


def lint(s):
    text, bodies = G.build_script(s)
    return G.lint_script(text, bodies, allow=G.lint_allowances(s)), text


def codes(s):
    return [c for c, _ in G.validate_spec(s)[0]]


class TestLintAllow(unittest.TestCase):
    def test_01_exempt_literal_passes_and_is_reported(self):
        s = exempt_spec()
        self.assertEqual(codes(s), [])
        issues, _ = lint(s)
        self.assertEqual(issues, [])
        infos = G.lint_infos(G.lint_allowances(s))
        self.assertEqual(len(infos), 1)
        for w in ("NCH", "0.707", REASON, "INFO"):
            self.assertIn(w, infos[0])

    def test_02_control_without_exemption_is_refused(self):
        s = exempt_spec()
        del variant(s, "NCH")["lint_allow_float32"], variant(s, "NCH")["lint_allow_reason"]
        issues, _ = lint(s)
        self.assertEqual([r for r, _ in issues], ["L_FLOAT32"])

    def test_03_same_literal_in_other_variant_still_refused(self):
        s = exempt_spec()
        set_body(s, "NCA", "0.707")
        issues, _ = lint(s)
        self.assertEqual([r for r, _ in issues], ["L_FLOAT32"])
        self.assertIn("0.707", issues[0][1])

    def test_04_different_inexact_literal_in_exempt_body_refused(self):
        s = exempt_spec()
        v = variant(s, "NCH")
        v["body"] = "var %s(vars Price, int P)\n{\n\treturn Price[0] * 0.707 + 0.3;\n}" % v["function"]
        issues, _ = lint(s)
        self.assertEqual([r for r, _ in issues], ["L_FLOAT32"])
        self.assertIn("0.3", issues[0][1])

    def test_05_exemption_never_applies_to_main_script_text(self):
        s = exempt_spec()
        text, bodies = G.build_script(s)
        bad = text + "\nvar zz_main = 0.707;\n"
        issues = G.lint_script(bad, bodies, allow=G.lint_allowances(s))
        self.assertEqual([r for r, _ in issues], ["L_FLOAT32"])
        # and the comment of the exempt variant is not a loophole either: plumbing literal on the line after the body
        self.assertIn("line", issues[0][1])

    def test_06_list_without_reason_refused(self):
        s = exempt_spec()
        del variant(s, "NCH")["lint_allow_reason"]
        self.assertIn("LINT_ALLOW", codes(s))

    def test_07_empty_reason_refused(self):
        s = exempt_spec()
        variant(s, "NCH")["lint_allow_reason"] = "  "
        self.assertIn("LINT_ALLOW", codes(s))

    def test_08_reason_without_list_refused(self):
        s = exempt_spec()
        del variant(s, "NCH")["lint_allow_float32"]
        self.assertIn("LINT_ALLOW", codes(s))

    def test_09_stale_literal_refused(self):
        s = exempt_spec()
        variant(s, "NCH")["lint_allow_float32"] = ["0.707", "0.5"]     # 0.5 does not occur in the body
        errs = G.validate_spec(s)[0]
        self.assertTrue(any(c == "LINT_ALLOW" and "0.5" in m for c, m in errs), errs)

    def test_10_field_on_non_inline_variant_refused(self):
        s = exempt_spec()
        v = variant(s, "P48")
        v["lint_allow_float32"] = ["0.707"]
        v["lint_allow_reason"] = REASON
        self.assertIn("LINT_ALLOW", codes(s))

    def test_11_bad_types_refused(self):
        for bad in ("0.707", [0.707], []):
            s = exempt_spec()
            variant(s, "NCH")["lint_allow_float32"] = bad
            self.assertIn("LINT_ALLOW", codes(s), bad)

    def test_12_literal_only_in_a_comment_counts_as_stale(self):
        s = exempt_spec()
        v = variant(s, "NCH")
        v["body"] = "var %s(vars Price, int P)\n{\n\treturn Price[0]; // 0.707\n}" % v["function"]
        self.assertIn("LINT_ALLOW", codes(s))

    def test_13_write_script_uses_exemption(self):
        import tempfile
        s = exempt_spec()
        with tempfile.TemporaryDirectory() as td:
            p = G.write_script(s, td)
            self.assertTrue(os.path.isfile(p))
            s2 = copy.deepcopy(s)
            set_body(s2, "NCA", "0.707")
            s2["batch"]["script_name"] = "other_name"
            with self.assertRaises(G.LintError):
                G.write_script(s2, td)


if __name__ == "__main__":
    unittest.main()
