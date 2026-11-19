"""Permanent pre-run tests for MST (spec MESA_ArticleFidelity.toml, pre-run conditions i and ii).

  (i)  indicators/ehlers/MESAStochastic.c contains [corrected_code].lines inside MESAStochasticCore and .wrapper_lines inside
       MESAStochastic (whitespace-normalised, comments stripped); the guard is SEEN TO FIRE on temp copies / in-memory files.
  (ii) The old MESAStochastic.c (git blob a8c51bacf951cd1aa7a0d1c2f39347824ca1d6bf, read from git) -> new file differs only by
       M-1, M-2, M-6, M-9 (+ the Core / wrapper structure); the token difference is printed. MESAStochastic_Superseded.c equals
       the old blob after the renames MESAStochastic -> MESAStochastic_Superseded and mstc_ -> mstco_ (comments stripped).
Helpers (comment stripping, tokeniser, function_body, check_corrected) are those of test_ss3_corrected_code.py.
Rule (CLAUDE.md 4.4): every guard is seen to fire on a deliberately broken input. Git is read-only.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import re
import shutil
import subprocess
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
SPEC = os.path.join(HARNESS, "specs", "MESA_ArticleFidelity.toml")
REL_C = "indicators/ehlers/MESAStochastic.c"
REL_SUP = "indicators/ehlers/MESAStochastic_Superseded.c"
OLD_BLOB = "a8c51bacf951cd1aa7a0d1c2f39347824ca1d6bf"
CORE_SIG = "var MESAStochasticCore(vars Price, int StochPeriod, int HPPeriod, int SSPeriod, var* pRoof, var* pStoc)"
WRAP_SIG = "var MESAStochastic(vars Price, int StochPeriod, int HPPeriod, int SSPeriod)"


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
    return re.sub(r"\bmstc_", "mstco_", old).replace("var MESAStochastic(", "var MESAStochastic_Superseded(")


def check_superseded(sup_text, old):
    """(ok, reason): the file equals the old blob after the renames, comments stripped."""
    a, b = T3.tokens(renamed_old(old)), T3.tokens(sup_text)
    if a == b:
        return True, "token-identical to the renamed old blob"
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return False, "first token difference at %d: %r vs %r" % (k, x, y)
    return False, "length differs: %d vs %d tokens" % (len(a), len(b))


# (b) token multiset difference old -> new, measured 2026-11-19 and asserted exactly.
# REMOVED: M-1 `StochPeriod + 1` ('+'), loop bound `<=` (now '<'), M-6 fallback 50, M-2 `100.0 *`, and the old locals
# mstc_RawStoch / mstc_RS / mstc_Final (now mstc_Stoc / mstc_S / mstc_Out).
EXPECTED_REMOVED = {"+": 1, "<=": 1, "mstc_RawStoch": 3, "50": 1, "100.0": 1, "mstc_RS": 2, "mstc_Final": 2}
# statements the review found correct, carried over token-identical
CARRIED = ("int mstc_i ;",
           "var mstc_HH = mstc_Roof [ 0 ] ; var mstc_LL = mstc_Roof [ 0 ] ;",
           "if ( mstc_Roof [ mstc_i ] > mstc_HH ) mstc_HH = mstc_Roof [ mstc_i ] ; "
           "if ( mstc_Roof [ mstc_i ] < mstc_LL ) mstc_LL = mstc_Roof [ mstc_i ] ;",
           "( mstc_Roof [ 0 ] - mstc_LL ) / ( mstc_HH - mstc_LL )")


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestMSTCorrectedCode(unittest.TestCase):
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
            p = os.path.join(d, "MESAStochastic_alt.c")
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            ok, why = check_both(T3.read(p), self.lines, self.wrap)
        print("\n  [fire] %s in temp copy: ok=%s (%s)" % (label, ok, why))
        self.assertFalse(ok)

    def test_spec_names_the_right_file_and_functions(self):
        cc = self.spec["corrected_code"]
        self.assertEqual((cc["file"], cc["function"], cc["wrapper_function"]), (REL_C, CORE_SIG, WRAP_SIG))
        self.assertIn(OLD_BLOB, cc["notes"])

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
        alterations = (("series(RoofingFilter(Price, HPPeriod, SSPeriod), StochPeriod)",
                        "series(RoofingFilter(Price, HPPeriod, SSPeriod), StochPeriod + 1)"),   # M-1 window
                       ("mstc_i < StochPeriod", "mstc_i <= StochPeriod"),                         # M-1 loop
                       ("    mstc_Stoc = mstc_Stoc/2;\n", ""),                                    # M-6 fallback removed
                       ("(mstc_Roof[0] - mstc_LL)", "100.0*(mstc_Roof[0] - mstc_LL)"),            # M-2 scale
                       ("*pStoc = mstc_Stoc;", "*pStoc = mstc_Out;"),
                       ("return MESAStochasticCore(Price, StochPeriod, HPPeriod, SSPeriod, &mstc_r, &mstc_s);",
                        "return mstc_r;"),                                                        # wrapper
                       ("    var mstc_HH =", "    static var mstc_HH ="))                          # static added
        for a, b in alterations:
            self.assertIn(a, self.real)
            altered = self.real.replace(a, b, 1)
            self.assertNotEqual(altered, self.real, a)
            self.fire(altered, "%s -> %s" % (a.strip(), b.strip() or "(removed)"))

    def test_i_guard_fires_when_series_moved_inside_the_if(self):
        s = self.real
        decl = "    vars mstc_S = series(mstc_Stoc, 3);\n"
        self.assertIn(decl, s)
        s = s.replace(decl, "", 1)
        old = ("    if(mstc_HH != mstc_LL)\n"
               "        mstc_Stoc = (mstc_Roof[0] - mstc_LL)/(mstc_HH - mstc_LL);\n")
        self.assertIn(old, s)
        new = ("    if(mstc_HH != mstc_LL) {\n"
               "        mstc_Stoc = (mstc_Roof[0] - mstc_LL)/(mstc_HH - mstc_LL);\n"
               "    " + decl.strip() + "\n    }\n")
        s = s.replace(old, new, 1)
        self.assertNotEqual(s, self.real)
        ok, why = check_both(s, self.lines, self.wrap)
        print("\n  [fire] vars mstc_S = series(mstc_Stoc, 3); moved inside the if: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_guard_fires_on_wrong_function_and_comment_only_lines(self):
        self.assertFalse(T3.check_corrected(self.real, self.lines, CORE_SIG.replace("Core", "Core_Other"))[0])
        commented = "// " + self.lines.replace("\n", "\n// ") + "\n" + CORE_SIG + " { return 0; }"
        self.assertFalse(T3.check_corrected(commented, self.lines, CORE_SIG)[0])

    def test_i_real_c_has_both_series_before_any_use(self):
        body = T3.norm_ws(T3.function_body(self.real, CORE_SIG))
        decl_roof = body.index("vars mstc_Roof = series(")
        decl_s = body.index("vars mstc_S = series(mstc_Stoc, 3);")
        self.assertLess(decl_roof, body.index("mstc_Roof[0]", decl_roof + 30))
        self.assertLess(body.index("mstc_Stoc = (mstc_Roof[0]"), decl_s)
        self.assertLess(decl_s, body.index("SuperSmoother2Pole(mstc_S"))
        # no series() call inside an if() statement or a for() loop
        self.assertNotRegex(body, r"if\s*\([^)]*\)\s*\{?[^;{}]*series\(")
        self.assertNotRegex(body, r"for\s*\([^)]*\)\s*\{[^}]*series\(")

    def test_i_no_statics_no_decimal_literals_no_period(self):
        code = T3.strip_comments(self.real)
        self.assertNotRegex(code, r"\bstatic\b")
        self.assertNotRegex(code, r"\bINITRUN\b")
        self.assertNotRegex(code, r"\bPeriod\b")
        # no decimal literal at all, so no product / quotient starting with decimal literals (gotchas 9d.8)
        self.assertEqual(re.findall(r"\d+\.\d+", code), [])

    def test_i_static_and_literal_scans_fire(self):
        altered = self.real.replace("    var mstc_HH =", "    static var mstc_HH =", 1)
        self.assertRegex(T3.strip_comments(altered), r"\bstatic\b")
        altered2 = self.real.replace("(mstc_Roof[0] - mstc_LL)", "100.0*(mstc_Roof[0] - mstc_LL)", 1)
        self.assertEqual(re.findall(r"\d+\.\d+", T3.strip_comments(altered2)), ["100.0"])
        print("\n  [fire] static added / 100.0* added: the static and decimal-literal scans see them")

    # ---- (ii)
    def test_ii_blob_is_the_recorded_one(self):
        rc, out, err = git("rev-parse", "c760160:%s" % REL_C)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.strip(), OLD_BLOB)

    def test_ii_old_to_new_token_difference_is_m1_m2_m6_m9_only(self):
        a = Counter(T3.tokens(old_c()))
        b = Counter(T3.tokens(self.real[self.real.index(CORE_SIG):]))
        removed, added = a - b, b - a
        print("\n  [ii] removed tokens: %s\n       added tokens: %s" % (dict(removed), dict(added)))
        self.assertEqual(dict(removed), EXPECTED_REMOVED)
        new_t = " ".join(T3.tokens(self.real))
        for stmt in CARRIED:
            self.assertIn(stmt, new_t)

    def test_ii_guard_fires_on_any_extra_change(self):
        for a, b, stmt in (("(mstc_Roof[0] - mstc_LL)/(mstc_HH - mstc_LL)", "(mstc_Roof[0] - mstc_LL)/(mstc_HH - mstc_LL + 1)", CARRIED[3]),
                           ("if(mstc_Roof[mstc_i] > mstc_HH)", "if(mstc_Roof[mstc_i] >= mstc_HH)", CARRIED[2]),
                           ("var mstc_LL = mstc_Roof[0];", "var mstc_LL = mstc_Roof[1];", CARRIED[1])):
            altered = self.real.replace(a, b, 1)
            self.assertNotEqual(altered, self.real, a)
            self.assertNotIn(stmt, " ".join(T3.tokens(altered)))
            print("\n  [fire] (ii) %s -> %s: carried-over statement no longer matches" % (a, b))

    def test_ii_superseded_is_the_renamed_old_blob(self):
        ok, why = check_superseded(self.sup, old_c())
        print("\n  [ii] %s: %s" % (REL_SUP, why))
        self.assertTrue(ok, why)
        code = T3.strip_comments(self.sup)
        self.assertNotRegex(code, r"\bmstc_")
        self.assertIn("StochPeriod + 1", T3.norm_ws(code))
        self.assertIn("100.0", code)
        self.assertIn("mstco_RawStoch = 50", code)

    def test_ii_superseded_guard_fires(self):
        for a, b in (("mstco_RawStoch = 50;", "mstc_RawStoch = 50;"), ("100.0 *", "10.0 *"),
                     ("), StochPeriod + 1);", "), StochPeriod);"), ("mstco_i <= StochPeriod", "mstco_i < StochPeriod")):
            self.assertIn(a, self.sup)
            ok, why = check_superseded(self.sup.replace(a, b, 1), old_c())
            print("\n  [fire] (ii) superseded %s -> %s: ok=%s (%s)" % (a, b, ok, why))
            self.assertFalse(ok)

    def test_ii_comment_changes_do_not_matter(self):
        self.assertTrue(check_both(self.real + "\n// trailing\n/* b */\n", self.lines, self.wrap)[0])
        self.assertTrue(check_superseded(self.sup + "\n// trailing\n", old_c())[0])


if __name__ == "__main__":
    unittest.main()
