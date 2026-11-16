"""Permanent pre-run tests for SS3F (spec SS3_ArticleFidelity.toml, pre-run conditions i and ii).

  (i)  indicators/ehlers/SuperSmoother3Pole.c contains [corrected_code].lines verbatim (whitespace-normalised)
       inside the function named in [corrected_code].function.
  (ii) The NCH inline body equals indicators/ehlers/SuperSmoother3Pole_Hybrid_Superseded.c token by token
       (comments stripped); the only allowed difference is the function name.

Run with the rest of the suite: bash analysis/harness/run_tests.sh
Rule (CLAUDE.md section 4.4): every guard is SEEN TO FIRE on a deliberately broken input. The broken inputs are
built in memory (or in a temp file), never in the repo.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import re
import sys
import tempfile
import unittest

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
SPEC = os.path.join(HARNESS, "specs", "SS3_ArticleFidelity.toml")
GOOD_C = os.path.join(ROOT, "indicators", "ehlers", "SuperSmoother3Pole.c")
HYBRID_C = os.path.join(ROOT, "indicators", "ehlers", "SuperSmoother3Pole_Hybrid_Superseded.c")


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", " ", text)


def norm_ws(text):
    return " ".join(text.split())


def function_body(text, signature):
    """Body (between the outer braces) of the function whose header is `signature`, comments stripped.
    Returns None if the signature or a balanced body is not found."""
    clean = strip_comments(text)
    m = re.search(re.escape(norm_ws(signature)).replace(r"\ ", r"\s+"), clean)
    if m is None:
        return None
    i = clean.find("{", m.end())
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(clean)):
        if clean[j] == "{":
            depth += 1
        elif clean[j] == "}":
            depth -= 1
            if depth == 0:
                return clean[i + 1:j]
    return None


def check_corrected(c_text, lines, signature):
    """(ok, reason). Condition (i)."""
    body = function_body(c_text, signature)
    if body is None:
        return False, "function %r not found" % signature
    if norm_ws(lines) in norm_ws(body):
        return True, "verbatim"
    return False, "lines not found verbatim inside the function"


TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*|\d+\.?\d*(?:[eE][-+]?\d+)?|\+\+|--|[-+*/<>=!]=|&&|\|\||\S")


def tokens(text):
    return TOKEN.findall(strip_comments(text))


def split_function(text):
    """(name, tokens after the name) for a file/body that holds one `var NAME(...) {...}` function."""
    t = tokens(text)
    assert t[0] == "var" and t[2] == "(", "unexpected function header: %r" % t[:4]
    return t[1], t[2:]


def check_hybrid(nch_body, hybrid_text):
    """(ok, reason). Condition (ii): equal except the function name."""
    n_name, n_tok = split_function(nch_body)
    h_name, h_tok = split_function(hybrid_text)
    if n_tok == h_tok:
        return True, "equal except name (%s vs %s)" % (n_name, h_name)
    for k, (a, b) in enumerate(zip(n_tok, h_tok)):
        if a != b:
            return False, "first token difference at %d: %r vs %r" % (k, a, b)
    return False, "length differs: %d vs %d tokens" % (len(n_tok), len(h_tok))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
class TestSS3CorrectedCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SPEC, "rb") as f:
            cls.spec = tomllib.load(f)
        cc = cls.spec["corrected_code"]
        cls.lines = cc["lines"]
        cls.sig = cc["function"]
        cls.good = read(GOOD_C)

    # ---- (i)
    def test_i_corrected_c_contains_lines_verbatim(self):
        ok, why = check_corrected(self.good, self.lines, self.sig)
        self.assertTrue(ok, why)

    def test_i_guard_fires_on_altered_copy(self):
        """a1*a1 -> a1 in a temp-file copy (the real hybrid error): the guard must report FAIL."""
        altered = self.good.replace("var c1 = a1 * a1;", "var c1 = a1;")
        self.assertNotEqual(altered, self.good, "the alteration did not change the text")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "SuperSmoother3Pole_altered.c")
            with open(p, "w", encoding="utf-8") as f:
                f.write(altered)
            ok, why = check_corrected(read(p), self.lines, self.sig)
        print("\n  [fire] a1*a1 -> a1 in temp copy: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_guard_fires_when_lines_outside_function(self):
        """Lines present only in a comment / wrong function name must not count."""
        ok, why = check_corrected(self.good, self.lines, "var SuperSmoother3Pole_Other(vars Price, int Period)")
        print("\n  [fire] wrong function name: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)
        commented = "// " + self.lines.replace("\n", "\n// ") + "\nvar SuperSmoother3Pole(vars Price, int Period) { return 0; }"
        ok, why = check_corrected(commented, self.lines, self.sig)
        print("  [fire] lines only in comments: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_guard_fires_on_whitespace_only_vs_token_change(self):
        """Whitespace changes pass (normalised); a changed literal fails."""
        spaced = self.good.replace("a1 * a1", "a1   *   a1").replace("\t", "    ")
        self.assertTrue(check_corrected(spaced, self.lines, self.sig)[0])
        broken = self.good.replace("sqrt(3.0)", "1.738")
        ok, why = check_corrected(broken, self.lines, self.sig)
        print("\n  [fire] sqrt(3.0) -> 1.738: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    # ---- (ii)
    def _nch_body(self):
        v = [v for v in self.spec["variants"] if v["id"] == "NCH"]
        self.assertEqual(len(v), 1)
        return v[0]["body"]

    def test_ii_nch_body_equals_hybrid_file_except_name(self):
        ok, why = check_hybrid(self._nch_body(), read(HYBRID_C))
        print("\n  [ii] %s" % why)
        self.assertTrue(ok, why)

    def test_ii_function_names_differ_as_expected(self):
        self.assertEqual(split_function(self._nch_body())[0], "ss3f_nc_h")
        self.assertEqual(split_function(read(HYBRID_C))[0], "SuperSmoother3Pole_Hybrid_Superseded")

    def test_ii_guard_fires_on_altered_hybrid(self):
        hy = read(HYBRID_C)
        for old, new in (("var c3 = a1 * a1 * a1;", "var c3 = a1 * a1;"),
                         ("var c0 = (1.0 - c1 - c2 - c3) / 2.0;", "var c0 = (1.0 - c1 - c2 - c3);")):
            altered = hy.replace(old, new)
            self.assertNotEqual(altered, hy, "alteration %r did not apply" % old)
            ok, why = check_hybrid(self._nch_body(), altered)
            print("\n  [fire] %s -> %s: ok=%s (%s)" % (old, new, ok, why))
            self.assertFalse(ok)

    def test_ii_comment_changes_do_not_matter(self):
        hy = read(HYBRID_C) + "\n// trailing comment\n/* block */\n"
        self.assertTrue(check_hybrid(self._nch_body(), hy)[0])


if __name__ == "__main__":
    unittest.main()
