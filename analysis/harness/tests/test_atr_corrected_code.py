"""Permanent pre-run tests for ATR (spec ATR_MT4Fidelity.toml, pre-run conditions i, ii, v).

  (i)  indicators/nnfx/ATR.c: function ATRMT4Core's body EQUALS [corrected_code].lines and ATRMT4's body EQUALS .wrapper_lines
       (whitespace-normalised, comments stripped; equality, not containment); no static, no global var, no decimal literal, no product /
       quotient of literals, no PI, no priceHigh / priceLow / priceClose token; every series() first and unconditional with an explicit length.
       Every guard is SEEN TO FIRE on temp copies (CLAUDE.md 4.4).
  (ii) the file is new (no commit up to the spec's base commit bd62493 has it); callers of ATRMT4( are only XCHK_ATRMT4_vs_ATRS.c and the
       generated script GEN_ATR_MT4.c.
  (v)  generator.lint_no_static: 0 hits on ATR.c; seen to fire on the spec's NCS body (1 hit: ats_prev).
Helpers are those of test_ss3_corrected_code.py / test_maf_corrected_code.py. Git is read-only.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

import test_ss3_corrected_code as T3
import test_maf_corrected_code as TM

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
sys.path.insert(0, HARNESS)
import generator  # noqa: E402

SPEC = os.path.join(HARNESS, "specs", "ATR_MT4Fidelity.toml")
ATR_C = os.path.join(ROOT, "indicators", "nnfx", "ATR.c")
BASE_COMMIT = "bd62493"
ALLOWED_CALLERS = {"strategies/tests/XCHK_ATRMT4_vs_ATRS.c", "strategies/tests/GEN_ATR_MT4.c"}


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
class TestAtrCorrectedCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SPEC, "rb") as fh:
            cls.spec = tomllib.load(fh)
        cc = cls.spec["corrected_code"]
        cls.core_sig, cls.wrap_sig = cc["function"], cc["wrapper_function"]
        cls.lines, cls.wrap = T3.strip_comments(cc["lines"]), T3.strip_comments(cc["wrapper_lines"])
        cls.real = T3.read(ATR_C).replace("\r\n", "\n")

    def check(self, text):
        out = []
        for sig, want in ((self.core_sig, self.lines), (self.wrap_sig, self.wrap)):
            body = T3.function_body(text, sig)
            if body is None:
                out.append((False, "function not found"))
            elif T3.norm_ws(body) == T3.norm_ws(want):
                out.append((True, "verbatim (body == pre-registered lines)"))
            else:
                out.append((False, "body differs from the pre-registered lines"))
        return (out[0][0] and out[1][0]), "core: %s; wrapper: %s" % (out[0][1], out[1][1])

    def fire(self, text, label):
        ok, why = self.check(text)
        print("\n  [fire] ATR.c %s in temp copy: ok=%s (%s)" % (label, ok, why))
        self.assertFalse(ok)

    def alter(self, a, b, every=False):
        """The real file with `a` -> `b` (first occurrence, or every one), written to and read back from a temp file."""
        self.assertIn(a, self.real)
        altered = self.real.replace(a, b) if every else self.real.replace(a, b, 1)
        self.assertNotEqual(altered, self.real)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "ATR_alt.c")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(altered)
            return T3.read(p)

    # ---- (i)
    def test_i_spec_names_the_file_and_functions(self):
        cc = self.spec["corrected_code"]
        self.assertEqual(cc["file"], "indicators/nnfx/ATR.c")
        self.assertTrue(cc["function"].startswith("var ATRMT4Core("))
        self.assertTrue(cc["wrapper_function"].startswith("var ATRMT4("))

    def test_i_real_c_contains_lines_verbatim(self):
        ok, why = self.check(self.real)
        print("\n  [i] indicators/nnfx/ATR.c: %s" % why)
        self.assertTrue(ok, why)

    def test_i_check_ignores_whitespace_and_comments(self):
        spaced = self.real.replace(" = ", "   =\t").replace("\n    ", "\n\n\t") + "\n// trailing\n/* block */\n"
        self.assertNotEqual(spaced, self.real)
        self.assertTrue(self.check(spaced)[0])

    def test_i_no_statics_globals_decimal_literals_pi_price_calls(self):
        code = T3.strip_comments(self.real)
        self.assertEqual(generator.lint_no_static(self.real), [])
        self.assertNotRegex(code, r"\bstatic\b|\bINITRUN\b|\bPeriod\b|#include|\bPI\b")
        self.assertEqual(re.findall(r"\d+\.\d+", code), [])
        self.assertEqual(TM.LITERAL_PRODUCT.findall(code), [])
        self.assertEqual(TM.global_var_lines(code), [])
        self.assertNotRegex(code, r"\bpriceHigh\b|\bpriceLow\b|\bpriceClose\b")

    def test_i_scans_fire(self):
        code = T3.strip_comments(self.real.replace("    var ", "    static var ", 1))
        self.assertEqual(len(generator.lint_no_static(code)), 1)
        self.assertEqual(re.findall(r"\d+\.\d+", T3.strip_comments(self.real + "\nvar q = 0.5;")), ["0.5"])
        self.assertEqual(len(TM.LITERAL_PRODUCT.findall(T3.strip_comments(self.real + "\nvar q = 2*3;"))), 1)
        self.assertEqual(TM.global_var_lines(T3.strip_comments("var g_x = 0;\n" + self.real)), ["var g_x = 0;"])
        self.assertRegex(T3.strip_comments(self.real + "\nvar q = PI;"), r"\bPI\b")
        self.assertRegex(T3.strip_comments(self.real + "\nvar q = priceHigh();"), r"\bpriceHigh\b")
        print("\n  [fire] scans: static, decimal literal, literal product, global var, PI, priceHigh each reported on a broken copy")

    def test_i_series_first_unconditional_explicit_length(self):
        body = T3.norm_ws(T3.function_body(self.real, self.core_sig))
        self.assertEqual(body.count("series("), 3)
        self.assertLess(body.rindex("series("), body.index("at_n[0] = at_n[1] + 1;"))
        self.assertNotRegex(body, r"if\s*\([^)]*\)\s*\{?[^;{}]*series\(")
        self.assertEqual(TM.series_without_length(T3.strip_comments(self.real)), [])
        self.assertEqual(TM.series_without_length("vars a = series(0);"), ["series(0)"])

    def test_i_guard_fires(self):
        decl = "    vars at_A  = series(0, 2);\n"
        head = "    if(at_n[0] > 1) {"
        self.assertIn(decl, self.real)
        moved = self.real.replace(decl, "", 1)
        self.assertIn(head, moved)
        moved = moved.replace(head, head + "\n" + decl.rstrip(), 1)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "ATR_alt.c")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(moved)
            moved = T3.read(p)
        cases = (
            (self.alter("    vars at_n  = series(0, 2);", "    static vars at_n  = series(0, 2);"), "static before vars at_n"),
            (self.alter("if(at_n[0] == Length + 1)", "if(at_n[0] == Length)"), "at_n[0] == Length + 1 -> at_n[0] == Length"),
            (self.alter("Close[1]", "Close[0]", every=True), "Close[1] -> Close[0] (every occurrence)"),
            (self.alter("(at_TR[0] - at_TR[Length])", "(at_TR[0] - at_TR[Length - 1])"), "at_TR[Length] -> at_TR[Length - 1]"),
            (self.alter("vars at_TR = series(0, Length + 2);", "vars at_TR = series(0, Length);"), "series(0, Length + 2) -> series(0, Length)"),
            (self.alter("    if(at_n[0] > 1) {", "    {"), "the if(at_n[0] > 1) guard removed"),
            (moved, "vars at_A = series(0, 2) moved inside the if"),
            (self.alter("return ATRMT4Core(High, Low, Close, Length, &atw_1);", "return atw_1;"), "wrapper does not call the core"),
        )
        for text, label in cases:
            self.fire(text, label)

    # ---- (ii)
    def test_ii_file_is_new(self):
        r = subprocess.run(["git", "-C", ROOT, "log", "--oneline", BASE_COMMIT, "--", "indicators/nnfx/ATR.c"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        print("\n  [ii] git log %s -- indicators/nnfx/ATR.c: %r (no old blob)" % (BASE_COMMIT, r.stdout.strip()))
        self.assertEqual(r.stdout.strip(), "")

    @staticmethod
    def c_files():
        out = []
        for base in ("strategies", "indicators", "analysis"):
            for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
                if os.sep + "results" in dp:
                    continue
                out.extend(os.path.join(dp, f) for f in fn if f.endswith(".c"))
        return out

    @staticmethod
    def callers(text):
        return re.findall(r"\bATRMT4\s*\(", T3.strip_comments(text))

    def test_ii_no_caller_outside_xchk_and_generated_script(self):
        who = set()
        for p in self.c_files():
            rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
            if rel == "indicators/nnfx/ATR.c":
                continue                                   # the definition
            if self.callers(T3.read(p)):
                who.add(rel)
        print("\n  [ii] files calling ATRMT4(: %s" % sorted(who))
        self.assertTrue(who <= ALLOWED_CALLERS, who)

    def test_ii_caller_scan_fires(self):
        self.assertEqual(self.callers("var a = ATRMT4(h, l, c, 14);"), ["ATRMT4("])
        self.assertEqual(self.callers("// ATRMT4(h)\nvar a = ATRMT4Core(h, l, c, 14, &t);"), [])
        print("\n  [fire] caller scan reports ATRMT4( in a code line; ignores comments and ATRMT4Core(")

    # ---- (v)
    def test_v_no_static_lint_fires_on_the_ncs_body(self):
        self.assertEqual(generator.lint_no_static(self.real), [])
        ncs = next(v for v in self.spec["variants"] if v["id"] == "NCS")["body"]
        hits = generator.lint_no_static(ncs)
        print("\n  [v] ATR.c: 0 hits; spec NCS body: %s" % hits)
        self.assertEqual([n for _, n in hits], ["ats_prev"])


if __name__ == "__main__":
    unittest.main()
