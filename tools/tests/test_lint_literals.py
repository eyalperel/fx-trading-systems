"""Tests for tools/lint_literals.py (decision T11: no magic numbers).

Rules under test
  Logic files (template code): the only numeric literals allowed are 0 and 1. Any other
  number fails unless the line carries `// lint:allow <reason>` with a non-empty reason;
  every exemption is listed in the report. Numbers inside comments and strings are ignored.
  Config files (*_Config.h): every line holding a number must carry a source label in its
  comment: (a), (b), (c), a decision id (T1..T99, M-D1..), or a key in [..]. Decimal
  literals are forbidden there (float32, gotchas 9d.1): build them from integers.
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

import lint_literals as L  # noqa: E402


def lint_logic(src):
    return L.lint_text(src, mode="logic")


def lint_config(src):
    return L.lint_text(src, mode="config")


class LogicMode(unittest.TestCase):
    def test_clean_code_passes(self):
        r = lint_logic("var x = nx_StopAtr * nx_Atr;\nif(a > 0) b = c[1];\n")
        self.assertEqual(r.violations, [])

    def test_planted_integer_fails_with_line(self):
        r = lint_logic("var a = 1;\nvar b = 15;\n")
        self.assertEqual(len(r.violations), 1)
        self.assertEqual(r.violations[0].line, 2)
        self.assertEqual(r.violations[0].token, "15")

    def test_decimal_fails(self):
        r = lint_logic("var s = 1.5 * atr;\n")
        self.assertEqual([v.token for v in r.violations], ["1.5"])

    def test_zero_point_zero_fails(self):
        # only the integer spellings 0 and 1 are allowed
        r = lint_logic("var s = 0.0;\nvar t = 1.;\n")
        self.assertEqual(len(r.violations), 2)

    def test_negative_number_fails(self):
        r = lint_logic("var d = -2;\n")
        self.assertEqual([v.token for v in r.violations], ["2"])

    def test_hex_and_exponent_fail(self):
        r = lint_logic("int m = 0x10;\nvar e = 1e-6;\n")
        self.assertEqual(len(r.violations), 2)

    def test_identifiers_with_digits_not_flagged(self):
        r = lint_logic("var nx_Atr14 = series2(x);\nint c1State = C2_on;\n")
        self.assertEqual(r.violations, [])

    def test_comments_ignored(self):
        r = lint_logic("var a = b; // stop 1.5 x ATR [V25]\n/* 7 candles\n 14 */ var c = d;\n")
        self.assertEqual(r.violations, [])

    def test_strings_ignored(self):
        r = lint_logic('printf("%.15f %d", x, 7);\n'.replace(", 7", ", n"))
        self.assertEqual(r.violations, [])
        r2 = lint_logic('char* f = "Data/TPL_2026.csv";\n')
        self.assertEqual(r2.violations, [])

    def test_exemption_with_reason_passes_and_is_listed(self):
        r = lint_logic("var p = 4; // lint:allow exact pi = 4*atan(1), D3 S1\n")
        self.assertEqual(r.violations, [])
        self.assertEqual(len(r.exemptions), 1)
        self.assertEqual(r.exemptions[0].line, 1)
        self.assertIn("exact pi", r.exemptions[0].reason)

    def test_exemption_without_reason_fails(self):
        r = lint_logic("var p = 4; // lint:allow\n")
        self.assertEqual(len(r.violations), 1)

    def test_exemption_covers_only_its_own_line(self):
        r = lint_logic("var p = 4; // lint:allow reason\nvar q = 5;\n")
        self.assertEqual([v.line for v in r.violations], [2])


class ConfigMode(unittest.TestCase):
    def test_labelled_integer_passes(self):
        r = lint_config("nx_AtrLen = 14; // (a) [V03, V16]\n")
        self.assertEqual(r.violations, [])

    def test_decision_label_passes(self):
        r = lint_config("nx_FillMode = 3; // T4\nnx_Slip = 0; // M-D2\n")
        self.assertEqual(r.violations, [])

    def test_unlabelled_number_fails(self):
        r = lint_config("nx_AtrLen = 14;\n")
        self.assertEqual(len(r.violations), 1)
        self.assertIn("label", r.violations[0].reason)

    def test_comment_without_label_fails(self):
        r = lint_config("nx_AtrLen = 14; // the ATR length\n")
        self.assertEqual(len(r.violations), 1)

    def test_decimal_fails_even_with_label(self):
        r = lint_config("nx_StopAtr = 1.5; // (a) [V25]\n")
        self.assertEqual(len(r.violations), 1)
        self.assertIn("decimal", r.violations[0].reason)

    def test_integer_ratio_passes(self):
        r = lint_config("nx_StopAtr = 3; nx_StopAtr /= 2; // 1.5 (a) [V25, M3]\n")
        self.assertEqual(r.violations, [])

    def test_lines_without_numbers_need_no_label(self):
        r = lint_config("var nx_StopAtr;\nvoid nx_config_init() {\n}\n")
        self.assertEqual(r.violations, [])


class Cli(unittest.TestCase):
    def _run(self, name, text):
        d = tempfile.mkdtemp()
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return subprocess.run([sys.executable, os.path.join(TOOLS, "lint_literals.py"), p],
                              capture_output=True, text=True)

    def test_exit_zero_on_clean(self):
        r = self._run("NNFX_Template.c", "var x = a * b;\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_exit_nonzero_on_planted_literal(self):
        r = self._run("NNFX_Template.c", "var x = a * 7;\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("NNFX_Template.c:1", r.stdout)

    def test_config_mode_chosen_by_filename(self):
        r = self._run("NNFX_Config.h", "nx_AtrLen = 14; // (a) [V03]\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_report_lists_exemptions(self):
        r = self._run("NNFX_Template.c", "var p = 4; // lint:allow exact pi\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn("EXEMPT", r.stdout)


if __name__ == "__main__":
    unittest.main()
