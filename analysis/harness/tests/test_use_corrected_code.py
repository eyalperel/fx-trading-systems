"""Permanent pre-run tests for USE (spec USE_ArticleFidelity.toml, pre-run conditions i and ii).

  (i)  The real indicators/ehlers/UltimateSmootherE.c contains [corrected_code].lines verbatim (whitespace-normalised,
       comments stripped) inside the declared function; the guard is SEEN TO FIRE on temp copies and in-memory files.
  (ii) The old file (git blob c545c201140e2927e9a5c1ec7664440ded1b3350, ddbf9fa; read from git, so the test keeps
       working after the rewrite) differs from the new function body only by D-1 (`1.414 * PI` -> `us_k*PI` plus the us_k
       line) and D-2 (`Bar < 4` -> the us_n counter, 2 lines). The token diff is printed.

Helpers (comment stripping, tokeniser, function_body, check_corrected) are those of test_ss3_corrected_code.py, imported.
Rule (CLAUDE.md 4.4): every guard is seen to fire on a deliberately broken input. Git is read-only.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import difflib
import os
import shutil
import subprocess
import tempfile
import unittest

import test_ss3_corrected_code as T3

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
SPEC = os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml")
REL_C = "indicators/ehlers/UltimateSmootherE.c"
OLD_BLOB = "c545c201140e2927e9a5c1ec7664440ded1b3350"     # the .c at ddbf9fa (spec [corrected_code].notes)
SIG = "var UltimateSmootherE(vars Price, int Period)"


def git(*args):
    r = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


def old_c():
    rc, out, err = git("cat-file", "-p", OLD_BLOB)
    if rc != 0:
        raise AssertionError("git cat-file -p %s failed: %s" % (OLD_BLOB, err.strip()))
    return out


def wrapped(lines):
    return "%s\n{\n%s\n}\n" % (SIG, lines)


def fn_tokens(text):
    """Tokens of the function, from its name on (comments stripped)."""
    t = T3.tokens(text)
    return t[t.index("UltimateSmootherE"):]


def diff_ops(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return [(tag, " ".join(a[i1:i2]), " ".join(b[j1:j2])) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]


def apply_d1_d2(old_body):
    """The old function text with exactly D-1 and D-2 applied (string level)."""
    s = old_body
    assert s.count("1.414 * PI") == 2
    s = s.replace("1.414 * PI", "us_k*PI")
    s = s.replace("    var us_a1 =", "    var us_k = sqrt(2.0);\n    var us_a1 =", 1)
    s = s.replace("    vars us_US =", "    vars us_n = series(0, 2);\n    us_n[0] = us_n[1] + 1;\n    vars us_US =", 1)
    assert s.count("Bar < 4") == 1
    return s.replace("Bar < 4", "us_n[0] < 4")


def check_d1_d2(old_text, new_text):
    """(ok, reason): old with D-1 and D-2 applied is token-identical to new, from the function name on."""
    a = fn_tokens(apply_d1_d2(old_text[old_text.index("var UltimateSmootherE("):]))
    b = fn_tokens(new_text)
    if a == b:
        return True, "token-identical after D-1 and D-2"
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return False, "first token difference at %d: %r vs %r" % (k, x, y)
    return False, "length differs: %d vs %d tokens" % (len(a), len(b))


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestUSECorrectedCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SPEC, "rb") as f:
            cls.spec = tomllib.load(f)
        cc = cls.spec["corrected_code"]
        cls.lines, cls.sig = cc["lines"], cc["function"]
        cls.real = T3.read(os.path.join(ROOT, *REL_C.split("/")))

    def test_spec_names_the_right_file_and_function(self):
        cc = self.spec["corrected_code"]
        self.assertEqual(cc["file"], REL_C)
        self.assertEqual(cc["function"], SIG)
        self.assertIn(OLD_BLOB, cc["notes"])

    # ---- (i)
    def test_i_real_c_contains_lines_verbatim(self):
        ok, why = T3.check_corrected(self.real, self.lines, self.sig)
        print("\n  [i] %s: %s" % (REL_C, why))
        self.assertTrue(ok, why)

    def test_i_check_passes_on_in_memory_file_and_ignores_whitespace(self):
        good = "// header\n" + wrapped(self.lines)
        self.assertTrue(T3.check_corrected(good, self.lines, self.sig)[0])
        spaced = good.replace("\nvar", "\n\n\tvar").replace(" = ", "   =\t")
        self.assertNotEqual(spaced, good)
        self.assertTrue(T3.check_corrected(spaced, self.lines, self.sig)[0])

    def test_i_real_c_guard_fires_on_temp_copies(self):
        alterations = (("us_n[0] < 4", "us_n[0] < 5"),
                       ("us_k*PI", "1.414*PI"),
                       ("/4.0", "/4.01"),
                       ("us_n = series(0, 2);", "us_n = series(0, 3);"))
        for a, b in alterations:
            self.assertIn(a, self.real)
            altered = self.real.replace(a, b, 1)
            self.assertNotEqual(altered, self.real, a)
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "UltimateSmootherE_alt.c")
                with open(p, "w", encoding="utf-8") as f:
                    f.write(altered)
                ok, why = T3.check_corrected(T3.read(p), self.lines, self.sig)
            print("\n  [fire] %s -> %s in temp copy: ok=%s (%s)" % (a, b, ok, why))
            self.assertFalse(ok)

    def test_i_guard_fires_when_series_moved_after_early_return(self):
        """series(0, 2) (us_n) moved after the early return: the lines are no longer verbatim."""
        s = self.real
        decl = "    vars us_n = series(0, 2);\n    us_n[0] = us_n[1] + 1;\n"
        self.assertIn(decl, s)
        s = s.replace(decl, "", 1)
        s = s.replace("    us_US[0] = (1.0 - us_c1)", decl + "    us_US[0] = (1.0 - us_c1)", 1)
        self.assertNotEqual(s, self.real)
        ok, why = T3.check_corrected(s, self.lines, self.sig)
        print("\n  [fire] series(0, 2) moved after the early return: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_guard_fires_on_wrong_function_and_comment_only_lines(self):
        self.assertFalse(T3.check_corrected(self.real, self.lines, "var UltimateSmootherE_Other(vars Price, int Period)")[0])
        commented = "// " + self.lines.replace("\n", "\n// ") + "\n" + self.sig + " { return 0; }"
        self.assertFalse(T3.check_corrected(commented, self.lines, self.sig)[0])

    def test_i_real_c_has_both_series_before_the_early_return(self):
        body = T3.norm_ws(T3.function_body(self.real, self.sig))
        ret = body.index("return us_US[0];")
        self.assertLess(body.index("series(0, 2)"), ret)
        self.assertLess(body.index("series(Price[0], 3)"), ret)

    def test_i_real_c_has_no_removed_claims(self):
        for gone in ("Week 5 validation", "article seeds with the raw price for 4 bars", "1.414 * PI"):
            self.assertNotIn(gone, self.real)

    # ---- (ii)
    def test_ii_blob_is_the_ddbf9fa_file(self):
        rc, out, err = git("rev-parse", "ddbf9fa:%s" % REL_C)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.strip(), OLD_BLOB)

    def test_ii_old_file_differs_only_by_d1_and_d2(self):
        ok, why = check_d1_d2(old_c(), self.real)
        print("\n  [ii] blob %s -> %s: %s" % (OLD_BLOB[:10], REL_C, why))
        for op in diff_ops(fn_tokens(old_c()), fn_tokens(self.real)):
            print("       token diff: %s | old: %r | new: %r" % op)
        self.assertTrue(ok, why)

    def test_ii_token_multiset_difference_is_exactly_d1_d2(self):
        """Alignment-independent: tokens removed / added between old and new function (multiset difference)."""
        from collections import Counter
        a, b = Counter(fn_tokens(old_c())), Counter(fn_tokens(self.real))
        removed, added = a - b, b - a
        print("\n  [ii] removed tokens: %s\n       added tokens: %s" % (dict(removed), dict(added)))
        self.assertEqual(dict(removed), {"1.414": 2, "Bar": 1})
        exp_added = (Counter(fn_tokens("var UltimateSmootherE(){ var us_k = sqrt(2.0); us_k us_k "
                                       "vars us_n = series(0, 2); us_n[0] = us_n[1] + 1; us_n[0] }"))
                     - Counter(fn_tokens("var UltimateSmootherE(){ }")))
        self.assertEqual(added, exp_added)

    def test_ii_guard_fires_on_any_extra_change(self):
        for a, b in (("us_n[0] < 4", "us_n[0] < 5"), ("/4.0", "/4.01"), ("us_k*PI", "1.414*PI"),
                     ("sqrt(2.0)", "sqrt(2.1)"), ("- (us_c1 + us_c3)", "+ (us_c1 + us_c3)")):
            altered = self.real.replace(a, b, 1)
            self.assertNotEqual(altered, self.real, a)
            ok, why = check_d1_d2(old_c(), altered)
            print("\n  [fire] (ii) %s -> %s: ok=%s (%s)" % (a, b, ok, why))
            self.assertFalse(ok)

    def test_ii_comment_changes_do_not_matter(self):
        self.assertTrue(check_d1_d2(old_c(), self.real + "\n// trailing\n/* b */\n")[0])


if __name__ == "__main__":
    unittest.main()
