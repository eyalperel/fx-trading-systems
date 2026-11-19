"""Permanent pre-run tests for RFX (spec RFX_ArticleFidelity.toml, pre-run conditions i and ii).

  (i)  indicators/ehlers/Reflex.c contains [corrected_code].lines inside ReflexCore and .wrapper_lines inside Reflex
       (whitespace-normalised, comments stripped); the guard is SEEN TO FIRE on temp copies / in-memory files.
  (ii) The old Reflex.c (git blob 7c6b235c00f053faef6f70dff71d9e09b99c440d, read from git) -> new Reflex.c differs only by
       R-1, R-2, R-3 (+ the ReflexCore / wrapper structure); the token difference is printed. Reflex_Superseded.c equals the old
       blob after the renames Reflex -> Reflex_Superseded and rx_ -> rxo_ (comments stripped).
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
SPEC = os.path.join(HARNESS, "specs", "RFX_ArticleFidelity.toml")
REL_C = "indicators/ehlers/Reflex.c"
REL_SUP = "indicators/ehlers/Reflex_Superseded.c"
OLD_BLOB = "7c6b235c00f053faef6f70dff71d9e09b99c440d"
CORE_SIG = "var ReflexCore(vars Price, int Length, var* pSum, var* pMS)"
WRAP_SIG = "var Reflex(vars Price, int Length)"


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
    return re.sub(r"\brx_", "rxo_", old).replace("var Reflex(", "var Reflex_Superseded(")


def check_superseded(sup_text, old):
    """(ok, reason): the file equals the old blob after the renames, comments stripped."""
    a, b = T3.tokens(renamed_old(old)), T3.tokens(sup_text)
    if a == b:
        return True, "token-identical to the renamed old blob"
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return False, "first token difference at %d: %r vs %r" % (k, x, y)
    return False, "length differs: %d vs %d tokens" % (len(a), len(b))


# tokens that disappear from the old function (multiset): R-1 (static MS, INITRUN reset), R-2 (int half length, the SS2 call),
# R-3 (float32 weights); rx_Reflex is the old local result variable (now rx_R).
CARRIED = ("var rx_Slope = ( rx_Filt [ Length ] - rx_Filt [ 0 ] ) / Length ;",
           "var rx_Sum = 0 ; int rx_i ; for ( rx_i = 1 ; rx_i <= Length ; rx_i ++ ) "
           "rx_Sum += ( rx_Filt [ 0 ] + rx_i * rx_Slope ) - rx_Filt [ rx_i ] ; rx_Sum = rx_Sum / Length ;")
EXPECTED_REMOVED = {"rx_HalfLength": 2, "SuperSmoother2Pole": 1, "static": 1, "if": 1, "is": 1, "INITRUN": 1, "0.04": 1,
                    "0.96": 1, "rx_Reflex": 3}


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestRFXCorrectedCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SPEC, "rb") as f:
            cls.spec = tomllib.load(f)
        cc = cls.spec["corrected_code"]
        cls.lines, cls.wrap = cc["lines"], cc["wrapper_lines"]
        cls.real = T3.read(os.path.join(ROOT, *REL_C.split("/")))
        cls.sup = T3.read(os.path.join(ROOT, *REL_SUP.split("/")))

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
        alterations = (("rx_w1 = rx_w1/100;", "rx_w1 = rx_w1/1000;"),
                       ("    rx_half = rx_half/2;\n", ""),
                       ("vars rx_MS = series(0, 2);", "static var rx_MS;"),
                       ("rx_MS[0] = rx_w1", "rx_MS = rx_w1"),
                       ("sqrt(2.0)", "sqrt(2.1)"),
                       ("return ReflexCore(Price, Length, &rx_s, &rx_m);", "return rx_s;"))
        for a, b in alterations:
            self.assertIn(a, self.real)
            altered = self.real.replace(a, b, 1)
            self.assertNotEqual(altered, self.real, a)
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "Reflex_alt.c")
                with open(p, "w", encoding="utf-8") as f:
                    f.write(altered)
                ok, why = check_both(T3.read(p), self.lines, self.wrap)
            print("\n  [fire] %s -> %s in temp copy: ok=%s (%s)" % (a, b or "(removed)", ok, why))
            self.assertFalse(ok)

    def test_i_guard_fires_when_series_moved_after_the_ms_line(self):
        s = self.real
        decl = "    vars rx_MS = series(0, 2);\n"
        self.assertIn(decl, s)
        s = s.replace(decl, "", 1)
        s = s.replace("    rx_MS[0] = rx_w1", decl + "    rx_MS[0] = rx_w1", 1)
        self.assertNotEqual(s, self.real)
        ok, why = check_both(s, self.lines, self.wrap)
        print("\n  [fire] series(0, 2) moved after the first use of rx_MS: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_guard_fires_on_wrong_function_and_comment_only_lines(self):
        self.assertFalse(T3.check_corrected(self.real, self.lines, "var ReflexCore_Other(vars Price, int Length, var* pSum, var* pMS)")[0])
        commented = "// " + self.lines.replace("\n", "\n// ") + "\n" + CORE_SIG + " { return 0; }"
        self.assertFalse(T3.check_corrected(commented, self.lines, CORE_SIG)[0])

    def test_i_real_c_has_both_series_before_any_use(self):
        body = T3.norm_ws(T3.function_body(self.real, CORE_SIG))
        first_use = min(body.index("rx_Filt[0] ="), body.index("rx_MS[0] ="))
        self.assertLess(body.index("vars rx_Filt = series("), first_use)
        self.assertLess(body.index("vars rx_MS = series(0, 2);"), first_use)
        self.assertNotIn("static", T3.strip_comments(self.real))
        self.assertNotIn("INITRUN", T3.strip_comments(self.real))

    def test_i_no_decimal_literal_products_and_no_period_identifier(self):
        code = T3.strip_comments(self.real)
        self.assertNotRegex(code, r"\bPeriod\b")
        self.assertNotRegex(code, r"\d\.\d+\s*\*\s*\d")                      # no literal * literal (gotchas 9d.8)
        for tok in re.findall(r"\d+\.\d+", code):
            self.assertIn(tok, ("2.0", "1.0"), tok)                           # only float32-exact literals

    # ---- (ii)
    def test_ii_blob_is_the_recorded_one(self):
        rc, out, err = git("rev-parse", "fd3d8eb:%s" % REL_C)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.strip(), OLD_BLOB)

    def test_ii_old_to_new_token_difference_is_r1_r2_r3_only(self):
        a = Counter(T3.tokens(old_c()))
        b = Counter(T3.tokens(self.real[self.real.index(CORE_SIG):]))
        removed, added = a - b, b - a
        print("\n  [ii] removed tokens: %s\n       added tokens: %s" % (dict(removed), dict(added)))
        self.assertEqual(dict(removed), EXPECTED_REMOVED)
        # the statements the review found correct are carried over unchanged (token-identical inside the new file)
        new_t = " ".join(T3.tokens(self.real))
        for stmt in CARRIED:
            self.assertIn(stmt, new_t)

    def test_ii_guard_fires_on_any_extra_change(self):
        for a, b, stmt in (("(rx_Filt[0] + rx_i*rx_Slope)", "(rx_Filt[0] + rx_Slope)", CARRIED[1]),
                           ("rx_Sum = rx_Sum/Length;", "rx_Sum = rx_Sum/(Length - 1);", CARRIED[1]),
                           ("(rx_Filt[Length] - rx_Filt[0])/Length", "(rx_Filt[Length] - rx_Filt[0])/2", CARRIED[0])):
            altered = self.real.replace(a, b, 1)
            self.assertNotEqual(altered, self.real, a)
            self.assertNotIn(stmt, " ".join(T3.tokens(altered)))
            print("\n  [fire] (ii) %s -> %s: carried-over statement no longer matches" % (a, b))

    def test_ii_superseded_is_the_renamed_old_blob(self):
        ok, why = check_superseded(self.sup, old_c())
        print("\n  [ii] %s: %s" % (REL_SUP, why))
        self.assertTrue(ok, why)
        code = T3.strip_comments(self.sup)
        self.assertNotRegex(code, r"\brx_")
        self.assertIn("static var rxo_MS", code)
        self.assertIn("0.04", code)
        self.assertIn("SuperSmoother2Pole", code)

    def test_ii_superseded_guard_fires(self):
        for a, b in (("rxo_Sum = rxo_Sum / Length;", "rx_Sum = rxo_Sum / Length;"), ("0.96 * rxo_MS", "0.97 * rxo_MS"),
                     ("static var rxo_MS = 0;", "var rxo_MS = 0;"), ("Length / 2", "Length / 3")):
            self.assertIn(a, self.sup)
            ok, why = check_superseded(self.sup.replace(a, b, 1), old_c())
            print("\n  [fire] (ii) superseded %s -> %s: ok=%s (%s)" % (a, b, ok, why))
            self.assertFalse(ok)

    def test_ii_comment_changes_do_not_matter(self):
        self.assertTrue(check_both(self.real + "\n// trailing\n/* b */\n", self.lines, self.wrap)[0])
        self.assertTrue(check_superseded(self.sup + "\n// trailing\n", old_c())[0])


if __name__ == "__main__":
    unittest.main()
