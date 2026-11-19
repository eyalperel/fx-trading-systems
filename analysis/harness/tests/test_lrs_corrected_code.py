"""Permanent pre-run tests for LRSI (spec LRSI_ArticleFidelity.toml, pre-run conditions i, ii and the code side of v).

  (i)  indicators/ehlers/LaguerreRSI.c contains [corrected_code].lines inside LaguerreRSICore and .wrapper_lines inside
       LaguerreRSI (whitespace-normalised, comments stripped); the guard is SEEN TO FIRE on in-memory / temp copies.
  (ii) The old LaguerreRSI.c (git blob b05f725176eff59b4ba1b68f299395c1c774ddff, read from git) -> new file differs only by
       L-1, L-2, L-3, L-5 (+ the Core / wrapper structure); the token difference is printed and asserted exactly.
       LaguerreRSI_Superseded.c equals the old blob after the renames LaguerreRSI -> LaguerreRSI_Superseded and lr_ -> lro_.
  (v)  no `static` in LaguerreRSI.c (the generator's lint_no_static); 2 hits on the superseded file (lro_init, lro_prevRSI).
Helpers are those of test_ss3_corrected_code.py. Rule (CLAUDE.md 4.4): every guard is seen to fire. Git is read-only.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter

import test_ss3_corrected_code as T3

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
sys.path.insert(0, HARNESS)
import generator  # noqa: E402

SPEC = os.path.join(HARNESS, "specs", "LRSI_ArticleFidelity.toml")
REL_C = "indicators/ehlers/LaguerreRSI.c"
REL_SUP = "indicators/ehlers/LaguerreRSI_Superseded.c"
OLD_BLOB = "b05f725176eff59b4ba1b68f299395c1c774ddff"
CORE_SIG = "var LaguerreRSICore(vars Close, var gamma, var* pL0, var* pL3, var* pDen)"
WRAP_SIG = "var LaguerreRSI(vars Close, var gamma)"


def git(*args):
    r = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


def old_c():
    rc, out, err = git("cat-file", "-p", OLD_BLOB)
    if rc != 0:
        raise AssertionError("git cat-file -p %s failed: %s" % (OLD_BLOB, err.strip()))
    return out


def check_both(text, lines, wrap):
    a = T3.check_corrected(text, lines, CORE_SIG)
    b = T3.check_corrected(text, wrap, WRAP_SIG)
    return (a[0] and b[0]), "core: %s; wrapper: %s" % (a[1], b[1])


def renamed_old(old):
    return re.sub(r"\blr_", "lro_", old).replace("var LaguerreRSI(", "var LaguerreRSI_Superseded(")


def check_superseded(sup_text, old):
    """(ok, reason): the file equals the old blob after the renames, comments stripped."""
    a, b = T3.tokens(renamed_old(old)), T3.tokens(sup_text)
    if a == b:
        return True, "token-identical to the renamed old blob"
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return False, "first token difference at %d: %r vs %r" % (k, x, y)
    return False, "length differs: %d vs %d tokens" % (len(a), len(b))


# (b) token multiset difference old file -> new file (Core + wrapper), measured 2026-11-19 and asserted exactly. By decision:
#  L-1: `static int lr_init`, the INITRUN reset, the `!lr_init && Close[0] > 0` guard, the seed block (8 stage assignments, 4 x lr_init,
#       `return 0.5`) and `(1.0 - gamma)` (now `lr_k = 1; lr_k = lr_k - gamma;`, gotchas 9d.8).
#  L-2: `static var lr_prevRSI = 0.5`, its INITRUN reset, `if(CU + CD == 0) return lr_prevRSI;` and `lr_prevRSI = ...` (now the series lr_R).
#  L-5: the Core signature with pL0 / pL3 / pDen, three out assignments, the wrapper LaguerreRSI (lr_w0 / lr_w3 / lr_wd, `&`).
#  also (pre-registered form, same value): `CU += x` -> `CU = CU + x` (4 `+=`), and the stage lines `-g*L(k-1) + L(k-1)[1] + g*Lk[1]` ->
#  `L(k-1)[1] - g*L(k-1) + g*Lk[1]` (term order: a token-multiset no-op, so it is checked by the verbatim test (i), not here).
EXPECTED_REMOVED = {'(': 3, 'Close': 7, ')': 3, 'lr_L0': 1, '=': 2, '0': 10, ';': 4, 'lr_L1': 2, 'lr_L2': 2, 'lr_L3': 1, 'static': 2,
                    'int': 1, 'lr_init': 4, 'if': 3, 'is': 2, 'INITRUN': 2, '!': 1, '&&': 1, '[': 11, ']': 11, '>': 1, '1': 3,
                    'return': 1, '0.5': 3, '1.0': 1, '+=': 4, 'lr_prevRSI': 5, '==': 1}
EXPECTED_ADDED = {'var': 8, 'LaguerreRSICore': 2, 'vars': 2, ',': 9, 'gamma': 2, '*': 6, 'pL0': 2, 'pL3': 2, 'pDen': 2, 'series': 1,
                  '2': 1, 'lr_R': 5, 'lr_k': 4, '+': 2, 'lr_CU': 3, 'lr_CD': 3, '!=': 1, 'lr_w0': 2, 'lr_w3': 2, 'lr_wd': 2, '&': 3}


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestLRSCorrectedCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SPEC, "rb") as f:
            cls.spec = tomllib.load(f)
        cc = cls.spec["corrected_code"]
        cls.lines, cls.wrap = cc["lines"], cc["wrapper_lines"]
        cls.real = T3.read(os.path.join(ROOT, *REL_C.split("/")))
        cls.sup = T3.read(os.path.join(ROOT, *REL_SUP.split("/")))

    def fire(self, text, label):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "LaguerreRSI_alt.c")
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            ok, why = check_both(T3.read(p), self.lines, self.wrap)
        print("\n  [fire] %s in temp copy: ok=%s (%s)" % (label, ok, why))
        self.assertFalse(ok)

    def test_spec_names_the_right_file_and_functions(self):
        cc = self.spec["corrected_code"]
        self.assertEqual((cc["file"], cc["function"], cc["wrapper_function"]), (REL_C, CORE_SIG, WRAP_SIG))

    # ---- (i)
    def test_i_real_c_contains_lines_verbatim(self):
        ok, why = check_both(self.real, self.lines, self.wrap)
        print("\n  [i] %s: %s" % (REL_C, why))
        self.assertTrue(ok, why)

    def test_i_check_passes_on_in_memory_file_and_ignores_whitespace(self):
        good = "// header\n%s\n{\n%s\n}\n%s\n{\n%s\n}\n" % (CORE_SIG, self.lines, WRAP_SIG, self.wrap)
        self.assertTrue(check_both(good, self.lines, self.wrap)[0])
        spaced = good.replace("\nvar", "\n\n\tvar").replace(" = ", "   =\t")
        self.assertNotEqual(spaced, good)
        self.assertTrue(check_both(spaced, self.lines, self.wrap)[0])

    def test_i_real_c_guard_fires_on_temp_copies(self):
        alterations = (("    var lr_CU = 0;", "    static var lr_CU = 0;"),                                  # static added
                       ("vars lr_L0 = series(0, 2);", "vars lr_L0 = series(Close[0], 2);"),                # price seed (L-1)
                       ("    lr_R[0] = lr_R[1];\n", ""),                                                   # hold removed (L-2)
                       ("lr_L1[0] = lr_L0[1] - gamma*lr_L0[0] + gamma*lr_L1[1];",
                        "lr_L1[0] = lr_L0[1] - gamma*lr_L0[1] + gamma*lr_L1[1];"),                         # 2025 form
                       ("    lr_k = lr_k - gamma;\n", ""),                                                 # alpha removed
                       ("*pL3 = lr_L3[0];", "*pL3 = lr_L2[0];"),
                       ("return LaguerreRSICore(Close, gamma, &lr_w0, &lr_w3, &lr_wd);", "return lr_w0;"))  # wrapper
        for a, b in alterations:
            self.assertIn(a, self.real)
            altered = self.real.replace(a, b, 1)
            self.assertNotEqual(altered, self.real, a)
            self.fire(altered, "%s -> %s" % (a.strip(), b.strip() or "(removed)"))

    def test_i_guard_fires_when_series_moved_inside_the_if(self):
        s = self.real
        decl = "    vars lr_R  = series(0, 2);\n"
        self.assertIn(decl, s)
        s = s.replace(decl, "", 1)
        old = "    if(lr_CU + lr_CD != 0) lr_R[0] = lr_CU/(lr_CU + lr_CD);\n"
        self.assertIn(old, s)
        new = "    if(lr_CU + lr_CD != 0) {\n    " + decl.strip() + "\n        lr_R[0] = lr_CU/(lr_CU + lr_CD);\n    }\n"
        s = s.replace(old, new, 1)
        self.assertNotEqual(s, self.real)
        ok, why = check_both(s, self.lines, self.wrap)
        print("\n  [fire] vars lr_R = series(0, 2); moved inside the if: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_guard_fires_on_wrong_function_and_comment_only_lines(self):
        self.assertFalse(T3.check_corrected(self.real, self.lines, CORE_SIG.replace("Core", "Core_Other"))[0])
        commented = "// " + self.lines.replace("\n", "\n// ") + "\n" + CORE_SIG + " { return 0; }"
        self.assertFalse(T3.check_corrected(commented, self.lines, CORE_SIG)[0])

    def test_i_real_c_has_all_series_before_any_use(self):
        body = T3.norm_ws(T3.function_body(self.real, CORE_SIG))
        for name in ("lr_L0", "lr_L1", "lr_L2", "lr_L3", "lr_R"):
            self.assertIn("vars %s = series(0, 2);" % name, body)
            self.assertLess(body.index("vars %s = series(" % name), body.index("lr_k = 1;"))
        self.assertLess(body.index("vars lr_R = series(0, 2);"), body.index("lr_L0[0] ="))
        self.assertEqual(body.count("series("), 5)
        self.assertNotRegex(body, r"if\s*\([^)]*\)\s*\{?[^;{}]*series\(")
        self.assertNotRegex(body, r"for\s*\([^)]*\)\s*\{[^}]*series\(")

    def test_i_no_statics_no_decimal_literals_no_period(self):
        code = T3.strip_comments(self.real)
        self.assertEqual(generator.lint_no_static(self.real), [])
        self.assertNotRegex(code, r"\bstatic\b")
        self.assertNotRegex(code, r"\bINITRUN\b")
        self.assertNotRegex(code, r"\bPeriod\b")
        # no decimal literal at all, so no product / quotient starting with decimal literals (gotchas 9d.8)
        self.assertEqual(re.findall(r"\d+\.\d+", code), [])

    def test_i_static_and_literal_scans_fire(self):
        altered = self.real.replace("    var lr_CU = 0;", "    static var lr_CU = 0;", 1)
        self.assertRegex(T3.strip_comments(altered), r"\bstatic\b")
        hits = generator.lint_no_static(altered)
        self.assertEqual([n for _, n in hits], ["lr_CU"])
        altered2 = self.real.replace("lr_k = 1;", "lr_k = 1.0;", 1)
        self.assertEqual(re.findall(r"\d+\.\d+", T3.strip_comments(altered2)), ["1.0"])
        altered3 = self.real.replace("lr_k*Close[0]", "0.5*0.5*Close[0]", 1)
        self.assertEqual(re.findall(r"\d+\.\d+", T3.strip_comments(altered3)), ["0.5", "0.5"])
        print("\n  [fire] static added / 1.0 / 0.5*0.5* added: the static and decimal-literal scans see them")

    # ---- (ii)
    def test_ii_blob_is_the_recorded_one(self):
        rc, out, err = git("rev-parse", "824a3cc:%s" % REL_C)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.strip(), OLD_BLOB)

    def test_ii_old_to_new_token_difference_is_l1_l2_l3_l5_only(self):
        a = Counter(T3.tokens(old_c()))
        b = Counter(T3.tokens(self.real[self.real.index(CORE_SIG):]))
        removed, added = a - b, b - a
        print("\n  [ii] removed tokens: %s\n       added tokens: %s" % (dict(removed), dict(added)))
        self.assertEqual(dict(removed), EXPECTED_REMOVED)
        self.assertEqual(dict(added), EXPECTED_ADDED)

    def test_ii_old_blob_has_what_the_diff_removes(self):
        old = T3.strip_comments(old_c())
        for s in ("static int lr_init", "static var lr_prevRSI", "return 0.5;", "Close[0] > 0", "(1.0 - gamma)", "lr_CU += "):
            self.assertIn(s, old)

    def test_ii_guard_fires_on_any_extra_change(self):
        a = Counter(T3.tokens(old_c()))
        for x, y in (("lr_CU/(lr_CU + lr_CD)", "lr_CU/(lr_CU + lr_CD + gamma)"),
                     ("if(lr_L2[0] >= lr_L3[0])", "if(lr_L2[0] > lr_L3[0])")):
            self.assertIn(x, self.real)
            altered = self.real.replace(x, y, 1)
            b = Counter(T3.tokens(altered[altered.index(CORE_SIG):]))
            self.assertNotEqual((dict(a - b), dict(b - a)), (EXPECTED_REMOVED, EXPECTED_ADDED))
            print("\n  [fire] (ii) %s -> %s: the exact token difference no longer matches" % (x, y))

    def test_ii_superseded_is_the_renamed_old_blob(self):
        ok, why = check_superseded(self.sup, old_c())
        print("\n  [ii] %s: %s" % (REL_SUP, why))
        self.assertTrue(ok, why)
        code = T3.strip_comments(self.sup)
        self.assertNotRegex(code, r"\blr_")
        for s in ("static int lro_init", "static var lro_prevRSI = 0.5", "return 0.5;", "Close[0] > 0"):
            self.assertIn(s, code)

    def test_ii_superseded_guard_fires(self):
        for a, b in (("static int lro_init = 0;", "static int lr_init = 0;"), ("return 0.5;", "return 0.4;"),
                     ("Close[0] > 0", "Close[0] > 1"), ("lro_L0[0] >= lro_L1[0]", "lro_L0[0] > lro_L1[0]")):
            self.assertIn(a, self.sup)
            ok, why = check_superseded(self.sup.replace(a, b, 1), old_c())
            print("\n  [fire] (ii) superseded %s -> %s: ok=%s (%s)" % (a, b, ok, why))
            self.assertFalse(ok)

    def test_ii_comment_changes_do_not_matter(self):
        self.assertTrue(check_both(self.real + "\n// trailing\n/* b */\n", self.lines, self.wrap)[0])
        self.assertTrue(check_superseded(self.sup + "\n// trailing\n", old_c())[0])

    # ---- (v)
    def test_v_no_static_lint_on_real_files(self):
        self.assertEqual(generator.lint_no_static(self.real), [])
        hits = generator.lint_no_static(self.sup)
        print("\n  [v] LaguerreRSI.c: 0 hits; LaguerreRSI_Superseded.c: %s" % hits)
        self.assertEqual([n for _, n in hits], ["lro_init", "lro_prevRSI"])


if __name__ == "__main__":
    unittest.main()
