"""Permanent pre-run tests for HPF (spec HP_ArticleFidelity.toml, pre-run conditions i and ii).

  (i)  indicators/ehlers/HighPassFilter.c contains [corrected_code].lines verbatim (whitespace-normalised, comments
       stripped) inside the function named in [corrected_code].function.
  (ii) The NCH inline body equals `git show 14395a0:indicators/ehlers/HighPassFilter.c` token by token (comments
       stripped); the only allowed difference is the function name.

Helpers (comment stripping, function_body, tokeniser) are the ones of test_ss3_corrected_code.py, imported, not copied.
Run with the rest of the suite: bash analysis/harness/run_tests.sh
Rule (CLAUDE.md section 4.4): every guard is SEEN TO FIRE on a deliberately broken input. The broken inputs are built
in memory or in a temp file, never in the repo. Git is used read-only (git show / git rev-parse).
Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import re
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
SPEC = os.path.join(HARNESS, "specs", "HP_ArticleFidelity.toml")
REL_C = "indicators/ehlers/HighPassFilter.c"
GOOD_C = os.path.join(ROOT, *REL_C.split("/"))
OLD_COMMIT = "14395a0"          # the .c as it was before the corrections (= NCH), spec [corrected_code].notes


def git(*args):
    r = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


def old_c():
    """The pre-correction file, read-only from git history. Fails (never skips) if the commit is unreadable."""
    rc, out, err = git("show", "%s:%s" % (OLD_COMMIT, REL_C))
    if rc != 0:
        raise AssertionError("git show %s:%s failed: %s" % (OLD_COMMIT, REL_C, err.strip()))
    return out


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestHPCorrectedCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SPEC, "rb") as f:
            cls.spec = tomllib.load(f)
        cc = cls.spec["corrected_code"]
        cls.lines = cc["lines"]
        cls.sig = cc["function"]
        cls.good = T3.read(GOOD_C)

    # ---- (i)
    def test_i_spec_names_the_right_file_and_function(self):
        cc = self.spec["corrected_code"]
        self.assertEqual(cc["file"], REL_C)
        self.assertEqual(cc["function"], "var HighPassFilter(vars Price, int HPPeriod)")

    def test_i_corrected_c_contains_lines_verbatim(self):
        ok, why = T3.check_corrected(self.good, self.lines, self.sig)
        print("\n  [i] %s" % why)
        self.assertTrue(ok, why)

    def _temp_copy_check(self, altered, name):
        self.assertNotEqual(altered, self.good, "the alteration did not change the text")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write(altered)
            return T3.check_corrected(T3.read(p), self.lines, self.sig)

    def test_i_guard_fires_on_float32_literal(self):
        """D-1 reintroduced in a temp-file copy: sqrt(2.0) / 2.0 -> 0.707."""
        ok, why = self._temp_copy_check(self.good.replace("sqrt(2.0) / 2.0", "0.707"), "HighPassFilter_d1.c")
        print("\n  [fire] sqrt(2.0)/2.0 -> 0.707 in temp copy: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_guard_fires_on_price_seed(self):
        """D-2 reintroduced in a temp-file copy: series(0, 3) -> series(Price[0], 3)."""
        ok, why = self._temp_copy_check(self.good.replace("series(0, 3)", "series(Price[0], 3)"),
                                        "HighPassFilter_d2.c")
        print("\n  [fire] series(0, 3) -> series(Price[0], 3) in temp copy: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_guard_fires_when_lines_outside_function(self):
        """Wrong function name, and lines present only in comments, must not count."""
        ok, why = T3.check_corrected(self.good, self.lines, "var HighPassFilter_Other(vars Price, int HPPeriod)")
        print("\n  [fire] wrong function name: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)
        commented = ("// " + self.lines.replace("\n", "\n// ")
                     + "\nvar HighPassFilter(vars Price, int HPPeriod) { return 0; }")
        ok, why = T3.check_corrected(commented, self.lines, self.sig)
        print("  [fire] lines only in comments: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_whitespace_passes_token_change_fails(self):
        # whitespace-only change: runs of blanks / tabs / newlines differ, no space is added or removed between tokens
        spaced = self.good.replace(" = ", "   =\t").replace("    ", "\t").replace(" * (", "  *   (")
        self.assertTrue(T3.check_corrected(spaced, self.lines, self.sig)[0])
        ok, why = self._temp_copy_check(self.good.replace("2.0*(1.0 - alpha1) * HP[1]", "2.0*(1.0 - alpha1) * HP[2]"),
                                        "HighPassFilter_tok.c")
        print("\n  [fire] HP[1] -> HP[2] in the feedback term: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    # ---- (ii)
    def _nch_body(self):
        v = [v for v in self.spec["variants"] if v["id"] == "NCH"]
        self.assertEqual(len(v), 1)
        return v[0]["body"]

    def test_ii_nch_body_equals_old_file_except_name(self):
        ok, why = T3.check_hybrid(self._nch_body(), old_c())
        print("\n  [ii] NCH body vs git show %s:%s: %s" % (OLD_COMMIT, REL_C, why))
        self.assertTrue(ok, why)

    def test_ii_function_names_differ_as_expected(self):
        self.assertEqual(T3.split_function(self._nch_body())[0], "hpf_nch")
        self.assertEqual(T3.split_function(old_c())[0], "HighPassFilter")

    def test_ii_old_file_is_the_uncorrected_one(self):
        """Sanity: the 14395a0 text has the two deviations, so NCH really is the pre-correction file."""
        t = " ".join(T3.strip_comments(old_c()).split())
        self.assertIn("0.707*2.0*PI", t)
        self.assertIn("series(Price[0], 3)", t)

    def test_ii_guard_fires_on_one_changed_token(self):
        old = old_c()
        start = old.index("var HighPassFilter(")          # alter CODE only: the header comments also quote 0.707
        for a, b in (("0.707", "0.708"), ("Price[2]", "Price[1]"), ("- (1.0 - alpha1) *", "+ (1.0 - alpha1) *")):
            altered = old[:start] + old[start:].replace(a, b, 1)
            self.assertNotEqual(altered, old, "alteration %r did not apply" % a)
            ok, why = T3.check_hybrid(self._nch_body(), altered)
            print("\n  [fire] %s -> %s in a copy: ok=%s (%s)" % (a, b, ok, why))
            self.assertFalse(ok)

    def test_ii_guard_fires_when_nch_body_is_changed(self):
        body = self._nch_body().replace("0.707", "0.708", 1)
        ok, why = T3.check_hybrid(body, old_c())
        print("\n  [fire] NCH body 0.707 -> 0.708: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_ii_comment_changes_do_not_matter(self):
        self.assertTrue(T3.check_hybrid(self._nch_body(), old_c() + "\n// trailing comment\n/* block */\n")[0])
        # a comment-only edit of the old file (0.707 -> 0.708 in the header comments) is NOT a code change
        header_only = old_c().replace("0.707", "0.708", 1)
        self.assertNotEqual(header_only, old_c())
        self.assertTrue(T3.check_hybrid(self._nch_body(), header_only)[0])

    # ---- blob hashes (recorded in Amendment 1)
    def test_blob_hashes_resolve(self):
        for commit in (OLD_COMMIT, "d22ef57"):
            rc, out, err = git("rev-parse", "%s:%s" % (commit, REL_C))
            print("\n  blob %s:%s = %s" % (commit, REL_C, out.strip()))
            self.assertEqual(rc, 0, err)
            self.assertRegex(out.strip(), r"^[0-9a-f]{40}$")
        rc, out, _ = git("rev-parse", "%s:%s" % (OLD_COMMIT, REL_C))
        rc2, out2, _ = git("rev-parse", "d22ef57:%s" % REL_C)
        self.assertNotEqual(out.strip(), out2.strip(), "the correction must have changed the blob")

    def test_blob_guard_fires_on_missing_path(self):
        rc, _, _ = git("rev-parse", "%s:%s" % (OLD_COMMIT, "indicators/ehlers/NoSuchFile.c"))
        print("\n  [fire] rev-parse of a missing path: rc=%d" % rc)
        self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
