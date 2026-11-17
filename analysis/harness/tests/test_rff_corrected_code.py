"""Permanent pre-run tests for RFF (spec RFF_ArticleFidelity.toml, pre-run conditions i and ii).

  (ii) The CURRENT indicators/ehlers/RoofingFilter.c (blob bb717f103fc1521c2ffc6046dfbaa0011a84ca3f, read from git, so
       the test keeps working after the file is rewritten) is token-identical to [corrected_code] apart from the two
       renames hp -> rf_hp and roofed -> rf_out (comments stripped).
  (i)  The checker for "the corrected .c contains [corrected_code].lines verbatim inside the function" is exercised on
       in-memory files built from the spec's own lines, and seen to fire on broken ones. The assertion on the REAL
       RoofingFilter.c is NOT here: the .c is written after the spec is committed (stage 2), which then adds that test.

Helpers (comment stripping, tokeniser, function_body) are the ones of test_ss3_corrected_code.py, imported, not copied.
Rule (CLAUDE.md 4.4): every guard is SEEN TO FIRE on a deliberately broken input; broken inputs are in memory. Git is
read-only (git cat-file / rev-parse).
Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import re
import shutil
import subprocess
import unittest

import test_ss3_corrected_code as T3

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
SPEC = os.path.join(HARNESS, "specs", "RFF_ArticleFidelity.toml")
REL_C = "indicators/ehlers/RoofingFilter.c"
OLD_BLOB = "bb717f103fc1521c2ffc6046dfbaa0011a84ca3f"     # the .c at 9b117fc (spec [corrected_code].notes)
RENAMES = {"hp": "rf_hp", "roofed": "rf_out"}


def git(*args):
    r = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


def old_c():
    """The pre-correction file by blob hash (read-only). Fails (never skips) if the blob is unreadable."""
    rc, out, err = git("cat-file", "-p", OLD_BLOB)
    if rc != 0:
        raise AssertionError("git cat-file -p %s failed: %s" % (OLD_BLOB, err.strip()))
    return out


def renamed(tokens):
    return [RENAMES.get(t, t) for t in tokens]


def wrapped(signature, lines):
    """The function the spec pre-registers, as source text."""
    return "%s\n{\n%s\n}\n" % (signature, lines)


def check_renamed(old_text, signature, lines):
    """(ok, reason): old file tokens with the two renames applied == tokens of the pre-registered function."""
    a = renamed(T3.tokens(old_text))
    b = T3.tokens(wrapped(signature, lines))
    # the old file's function header: `var RoofingFilter ( ... ) {`; compare from the name on
    if a == b:
        return True, "token-identical apart from the renames %s" % RENAMES
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return False, "first token difference at %d: %r vs %r" % (k, x, y)
    return False, "length differs: %d vs %d tokens" % (len(a), len(b))


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestRFFCorrectedCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SPEC, "rb") as f:
            cls.spec = tomllib.load(f)
        cc = cls.spec["corrected_code"]
        cls.lines, cls.sig = cc["lines"], cc["function"]

    def test_spec_names_the_right_file_function_and_lines(self):
        cc = self.spec["corrected_code"]
        self.assertEqual(cc["file"], REL_C)
        self.assertEqual(cc["function"], "var RoofingFilter(vars Price, int HPPeriod, int SSPeriod)")
        self.assertEqual(T3.norm_ws(cc["lines"]),
                         "var* rf_hp = series(HighPassFilter(Price, HPPeriod), 3); "
                         "var rf_out = SuperSmoother2Pole(rf_hp, SSPeriod); return rf_out;")
        self.assertIn(OLD_BLOB, cc["notes"])

    # ---- (ii)
    def test_ii_old_file_equals_corrected_lines_except_the_two_renames(self):
        ok, why = check_renamed(old_c(), self.sig, self.lines)
        print("\n  [ii] git blob %s vs [corrected_code] with renames hp->rf_hp, roofed->rf_out: %s" % (OLD_BLOB[:10], why))
        self.assertTrue(ok, why)

    def test_ii_the_renames_are_real_differences(self):
        """Fire: without applying the renames the two are NOT equal (so the rename step is doing something)."""
        a = T3.tokens(old_c())
        b = T3.tokens(wrapped(self.sig, self.lines))
        self.assertNotEqual(a, b)
        self.assertEqual(sorted(set(x for x in a if x not in b)), ["hp", "roofed"])
        self.assertEqual(sorted(set(x for x in b if x not in a)), ["rf_hp", "rf_out"])

    def test_ii_old_file_is_the_uncorrected_one(self):
        """Sanity: the blob is the current RoofingFilter (HP then SuperSmoother, both called through their functions)."""
        t = T3.norm_ws(T3.strip_comments(old_c()))
        self.assertIn("var* hp = series(HighPassFilter(Price, HPPeriod), 3);", t)
        self.assertIn("var roofed = SuperSmoother2Pole(hp, SSPeriod);", t)

    def test_ii_guard_fires_on_one_changed_token(self):
        old = old_c()
        start = old.index("var RoofingFilter(")             # alter CODE only: the header comments also mention names
        for a, b in (("HPPeriod), 3)", "SSPeriod), 3)"), ("SuperSmoother2Pole(hp, SSPeriod)", "SuperSmoother2Pole(hp, HPPeriod)"),
                     ("series(HighPassFilter", "series(SuperSmoother2Pole"), (", 3);", ", 2);"), ("return roofed", "return hp")):
            altered = old[:start] + old[start:].replace(a, b, 1)
            self.assertNotEqual(altered, old, "alteration %r did not apply" % a)
            ok, why = check_renamed(altered, self.sig, self.lines)
            print("\n  [fire] %s -> %s in a copy: ok=%s (%s)" % (a, b, ok, why))
            self.assertFalse(ok)

    def test_ii_guard_fires_when_the_registered_lines_change(self):
        for a, b in (("series(HighPassFilter(Price, HPPeriod), 3)", "series(HighPassFilter(Price, HPPeriod), 4)"),
                     ("SuperSmoother2Pole(rf_hp, SSPeriod)", "SuperSmoother2Pole(rf_hp, HPPeriod)")):
            ok, why = check_renamed(old_c(), self.sig, self.lines.replace(a, b))
            print("\n  [fire] registered lines %s -> %s: ok=%s (%s)" % (a, b, ok, why))
            self.assertFalse(ok)

    def test_ii_comment_changes_do_not_matter(self):
        self.assertTrue(check_renamed(old_c() + "\n// trailing comment\n/* block */\n", self.sig, self.lines)[0])
        edited = old_c().replace("Validated: EUR/USD D1, BTC/USD H4", "Validated: nowhere")
        self.assertNotEqual(edited, old_c())
        self.assertTrue(check_renamed(edited, self.sig, self.lines)[0])

    # ---- (i): the check itself, on in-memory files
    def good_file(self):
        return "// header comment\n" + wrapped(self.sig, self.lines)

    def test_i_check_passes_on_a_file_built_from_the_spec(self):
        ok, why = T3.check_corrected(self.good_file(), self.lines, self.sig)
        print("\n  [i] in-memory file built from the registered lines: %s" % why)
        self.assertTrue(ok, why)
        # whitespace-only reformat (runs of blanks / tabs / newlines changed, no space added or removed between tokens)
        spaced = self.good_file().replace(" = ", "   =\t").replace("\nvar", "\n\n\tvar").replace(", ", ",   ")
        self.assertNotEqual(spaced, self.good_file())
        self.assertTrue(T3.check_corrected(spaced, self.lines, self.sig)[0])

    def test_i_check_fires_on_broken_files(self):
        good = self.good_file()
        broken = {
            "swapped period args": good.replace("SuperSmoother2Pole(rf_hp, SSPeriod)", "SuperSmoother2Pole(rf_hp, HPPeriod)"),
            "old local names": good.replace("rf_hp", "hp").replace("rf_out", "roofed"),
            "series length": good.replace("HPPeriod), 3)", "HPPeriod), 2)"),
            "stage order": good.replace("series(HighPassFilter(Price, HPPeriod), 3)", "series(SuperSmoother2Pole(Price, SSPeriod), 3)"),
        }
        for what, text in broken.items():
            self.assertNotEqual(text, good, what)
            ok, why = T3.check_corrected(text, self.lines, self.sig)
            print("\n  [fire] %s: ok=%s (%s)" % (what, ok, why))
            self.assertFalse(ok, what)
        ok, why = T3.check_corrected(good, self.lines, "var RoofingFilter_Other(vars Price, int HPPeriod, int SSPeriod)")
        self.assertFalse(ok)                                           # wrong function name
        commented = "// " + self.lines.replace("\n", "\n// ") + "\n" + self.sig + " { return 0; }"
        self.assertFalse(T3.check_corrected(commented, self.lines, self.sig)[0])        # lines only in comments

    # ---- blob hash recorded in the spec
    def test_blob_hash_resolves_and_matches_9b117fc(self):
        rc, out, err = git("cat-file", "-e", OLD_BLOB)
        self.assertEqual(rc, 0, err)
        rc, out, err = git("rev-parse", "9b117fc:%s" % REL_C)
        print("\n  blob 9b117fc:%s = %s" % (REL_C, out.strip()))
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.strip(), OLD_BLOB)

    def test_blob_guard_fires_on_missing_object_and_path(self):
        rc, _, _ = git("cat-file", "-e", "0" * 40)
        self.assertNotEqual(rc, 0)
        rc, _, _ = git("rev-parse", "9b117fc:indicators/ehlers/NoSuchFile.c")
        self.assertNotEqual(rc, 0)
        self.assertTrue(re.fullmatch(r"[0-9a-f]{40}", OLD_BLOB))


if __name__ == "__main__":
    unittest.main()
