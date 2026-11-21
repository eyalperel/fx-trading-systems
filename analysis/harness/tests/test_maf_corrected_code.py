"""Permanent pre-run tests for MAF (specs MAMA_ArticleFidelity.toml and FRAMA_ArticleFidelity.toml, pre-run conditions i, ii, v and vi).

  (i)  indicators/ehlers/MAMA.c / FRAMA.c contain their spec's [corrected_code].lines inside MAMACore / FRAMACore and .wrapper_lines
       inside MAMA / FRAMA (whitespace-normalised, comments stripped on both sides); every guard is SEEN TO FIRE on temp copies.
  (ii) (A1.2) MAMA_Superseded = old blob + renames + an explicit length 7 on each of its 15 series() calls;
       old blob -> new file: the token difference is printed and asserted exactly (the review's deviations, the Core / wrapper structure
       and the renames); the superseded files equal their old blobs after the listed renames / edits (comments stripped).
  (v)  no `static` in the corrected files (generator.lint_no_static); 1 hit (mao_barCount) / 2 hits (fro_init, fro_prev) on the NEW
       superseded files.
  (vi) no caller in the repo calls FRAMA( with one argument or passes a decimal literal as a MAMA limit.
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

MAMA_LOCALS = ["barCount", "Smooth", "Detrender", "I1", "Q1", "jI", "jQ", "I2", "Q2", "Re", "Im", "Period", "SmoothPeriod", "Phase",
               "MAMAout", "FAMAout", "DeltaPhase", "alpha"]
CALLERS = ("strategies/tests/Test_FRAMA_Laguerre_DSMA.c", "strategies/tests/Test_FRAMA_vs_MAMA.c",
           "strategies/tests/Test_UltimateChannelBands.c", "strategies/tests/Test_MAMA.c")

# (b) token multiset differences old file -> new file (from the Core signature on), measured 2026-11-20 and asserted exactly.
# MAMA: MA-5 (#ifndef PI block) and S1 (PI -> ma_pi = 4*atan(1), deg = 180/pi); MA-3 (static barCount + INITRUN reset + ++ ->
# ma_n series counter); MA-1 (series(Price[0]) / series(20.0) seeds, `return Price` for 5 calls -> series(0, n), body inside
# if(ma_n[0] > 5)); MA-2 (17 holds X[0] = X[1]); MA-4 (every decimal literal -> integer ratios); MA-7 (Core signature with four
# out-parameters, the out assignments, the wrapper maw_1..maw_3 with &); renames (Smooth -> ma_S, Period -> ma_P, ...).
MAMA_REMOVED = {'#': 3, 'ifndef': 1, 'PI': 4, 'define': 1, '3.14159265358979': 1, 'endif': 1, '(': 3, 'Price': 3, '*': 12, 'outFAMA': 1,
                ')': 3, 'static': 1, 'int': 1, 'barCount': 4, 'if': 1, 'is': 1, 'INITRUN': 1, '++': 1, 'Smooth': 6, 'Detrender': 7,
                '0.0': 13, 'I1': 9, 'Q1': 8, 'jI': 3, 'jQ': 3, 'I2': 9, 'Q2': 9, 'Re': 7, 'Im': 7, 'Period': 22, '20.0': 2,
                'SmoothPeriod': 3, 'Phase': 4, 'MAMAout': 5, 'FAMAout': 4, '<=': 1, '4.0': 1, '+': 2, '3.0': 1, '2.0': 1, '10.0': 1,
                '0.0962': 8, '0.5769': 8, '0.075': 4, '0.54': 4, '0.2': 5, '0.8': 5, '360.0': 1, '180.0': 2, '1.5': 2, '0.67': 3,
                '6.0': 2, '50.0': 2, '0.33': 1, 'DeltaPhase': 4, '1.0': 4, 'alpha': 9, '0.5': 2}
MAMA_ADDED = {'var': 11, 'MAMACore': 2, 'vars': 18, ',': 29, 'FastLimit': 2, 'SlowLimit': 2, 'pFama': 2, 'pPeriod': 2, 'pAlpha': 2,
              'pPhase': 2, '{': 3, 'ma_n': 4, '=': 57, 'series': 2, '0': 54, '2': 16, ';': 59, 'ma_S': 10, '7': 4, 'ma_De': 9,
              'ma_I1': 11, 'ma_Q1': 10, 'ma_jI': 5, 'ma_jQ': 5, 'ma_I2': 11, 'ma_Q2': 11, 'ma_Re': 9, 'ma_Im': 9, 'ma_P': 22, 'ma_SP': 5,
              'ma_Ph': 9, 'ma_A': 12, 'ma_M': 7, 'ma_F': 6, '[': 42, ']': 42, '1': 16, 'ma_w1': 11, '962': 1, '/': 10, '10000': 2,
              'ma_w2': 11, '5769': 1, 'ma_ka': 4, '75': 1, '1000': 1, 'ma_kb': 4, '54': 1, '100': 4, 'ma_a2': 8, '10': 4, 'ma_a8': 8,
              '8': 1, 'ma_c33': 4, '33': 1, 'ma_c67': 4, '67': 2, 'ma_up': 5, '15': 1, 'ma_dn': 5, 'ma_pi': 4, '4': 2, 'atan': 1,
              'ma_deg': 5, '180': 1, 'ma_h': 4, 'ma_u': 3, 'ma_pf': 6, 'ma_p1': 7, 'ma_dp': 5, 'ma_ah': 4, '>': 1, '3': 1, '6': 2,
              '360': 1, '}': 3, '50': 2, 'maw_1': 2, 'maw_2': 2, 'maw_3': 2, '&': 3}
# FRAMA: FR-1 (T -> N, the full window: one loop over N, N/2 halves, /N); FR-2 (priceHigh() / priceLow() series and the mid price ->
# Price / High / Low parameters); FR-3 + FR-4 (static frama_prev / frama_init + INITRUN reset + `if(!init)` seed -> fr_n / fr_F
# series and `if(fr_n[0] < N + 1) fr_F[0] = Price[0]`); FR-5 (`if(N3 <= 0) return prev` -> `if(fr_N1 > 0 && fr_N2 > 0 && fr_N3 > 0)`,
# Dimen / alpha held in series); FR-6 (4.6, 0.01, 1.0, 2.0 -> integer-built); FR-7 (Core signature, out assignments, wrapper
# frw_1 / frw_2 with &); renames (frama_ -> fr_; Hi1..Lo3 -> fr_HH / fr_LL reused per box, as the source).
FRAMA_REMOVED = {'(': 9, 'T': 11, ')': 9, 'static': 2, 'frama_init': 4, 'if': 1, 'is': 1, 'INITRUN': 1, 'frama_High': 9, 'priceHigh': 2,
                 'frama_Low': 9, 'priceLow': 2, 'frama_price': 3, '2.0': 3, 'frama_Hi1': 5, 'frama_Lo1': 5, 'frama_i': 22, 'frama_N1': 2,
                 'frama_Hi2': 4, 'frama_Lo2': 4, 'frama_N2': 2, 'frama_Hi3': 4, 'frama_Lo3': 4, 'frama_N3': 3, 'frama_prev': 5, '!': 1,
                 '<=': 1, 'frama_D': 2, 'frama_alpha': 7, '4.6': 1, '1.0': 4, '0.01': 2, 'frama_out': 3}
FRAMA_ADDED = {'var': 1, 'FRAMACore': 2, 'vars': 8, 'Price': 5, ',': 17, 'High': 12, 'Low': 12, 'int': 1, 'N': 8, '*': 1, 'pDim': 2,
               'pAlpha': 2, '{': 1, 'fr_n': 4, '=': 16, 'series': 2, '0': 29, '2': 4, ';': 18, 'fr_F': 7, 'fr_D': 8, 'fr_A': 11,
               '[': 30, ']': 30, '1': 7, 'fr_k': 4, '46': 1, '/': 2, '10': 1, 'fr_lo': 5, '100': 1, 'fr_u': 5, 'fr_l2': 4, 'fr_h': 7,
               'fr_i': 22, 'fr_HH': 12, 'fr_LL': 12, '<': 1, '>': 3, '}': 1, 'fr_N3': 5, 'fr_N1': 5, 'fr_N2': 5, '&&': 2, 'fr_e': 4,
               'frw_1': 2, 'frw_2': 2, '&': 2}

FILES = {
    "MAMA": dict(spec="MAMA_ArticleFidelity.toml", c="indicators/ehlers/MAMA.c", sup="indicators/ehlers/MAMA_Superseded.c",
                 blob="bab4cbbb5961be5720bce82fc6e487e283f7f00e", core="MAMACore", wrap="MAMA", removed=MAMA_REMOVED, added=MAMA_ADDED,
                 static_hits=["mao_barCount"], prefix="mao_"),
    "FRAMA": dict(spec="FRAMA_ArticleFidelity.toml", c="indicators/ehlers/FRAMA.c", sup="indicators/ehlers/FRAMA_Superseded.c",
                  blob="3352fbe04ed691e479564bc63d46ae181334f9bb", core="FRAMACore", wrap="FRAMA", removed=FRAMA_REMOVED,
                  added=FRAMA_ADDED, static_hits=["fro_init", "fro_prev"], prefix="fro_"),
}
BASE_COMMIT = "b7bdd69"


def git(*args):
    r = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


def old_c(blob):
    rc, out, err = git("cat-file", "-p", blob)
    if rc != 0:
        raise AssertionError("git cat-file -p %s failed: %s" % (blob, err.strip()))
    return out


def rename_code_only(text, pat, repl):
    out = []
    for line in text.split("\n"):
        i = line.find("//")
        code, com = (line, "") if i < 0 else (line[:i], line[i:])
        out.append(re.sub(pat, repl, code) + com)
    return "\n".join(out)


def renamed_old(name, old):
    """The old blob after exactly the renames / edits the brief lists (section 3)."""
    if name == "MAMA":
        s = rename_code_only(old, r"\b(%s)\b" % "|".join(MAMA_LOCALS), r"mao_\1")
        s = rename_code_only(s, r"\bMAMA\(", "MAMA_Superseded(")
        # A1.2: an explicit length 7 on every length-less series() call (generated scripts set LookBack = 0)
        return rename_code_only(s, r"(= series\((?:Price\[0\]|0\.0|20\.0))\);", r"\1, 7);")
    s = re.sub(r"\bframa_", "fro_", old)
    s = s.replace("var FRAMA(int T) {", "var FRAMA_Superseded(vars Price, vars High, vars Low, int T) {")
    s = s.replace("vars fro_High = series(priceHigh());", "vars fro_High = High;")
    s = s.replace("vars fro_Low  = series(priceLow());", "vars fro_Low  = Low;")
    return s.replace("var fro_price = (priceHigh() + priceLow()) / 2.0;", "var fro_price = Price[0];")


def series_without_length(code):
    """Every series( call whose argument list has no top-level comma (= no explicit length)."""
    bad = []
    for m in re.finditer(r"\bseries\(", code):
        depth, i, comma = 1, m.end(), False
        while i < len(code) and depth:
            c = code[i]
            depth += (c == "(") - (c == ")")
            if c == "," and depth == 1:
                comma = True
            i += 1
        if not comma:
            bad.append(code[m.start():i])
    return bad


def check_superseded(name, sup_text, old):
    a, b = T3.tokens(renamed_old(name, old)), T3.tokens(sup_text)
    if a == b:
        return True, "token-identical to the renamed old blob"
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return False, "first token difference at %d: %r vs %r" % (k, x, y)
    return False, "length differs: %d vs %d tokens" % (len(a), len(b))


LITERAL_PRODUCT = re.compile(r"(?:^|[=(,;{]|\breturn)\s*\d+(?:\.\d+)?\s*[*/]\s*\d")


def global_var_lines(code):
    depth, top = 0, []
    for line in code.split("\n"):
        if depth == 0 and re.match(r"\s*vars?\b", line) and "(" not in line:
            top.append(line.strip())
        depth += line.count("{") - line.count("}")
    return top


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class _Base:
    NAME = None

    @classmethod
    def setUpClass(cls):
        cls.f = FILES[cls.NAME]
        with open(os.path.join(HARNESS, "specs", cls.f["spec"]), "rb") as fh:
            cls.spec = tomllib.load(fh)
        cc = cls.spec["corrected_code"]
        cls.core_sig, cls.wrap_sig = cc["function"], cc["wrapper_function"]
        cls.lines, cls.wrap = T3.strip_comments(cc["lines"]), T3.strip_comments(cc["wrapper_lines"])
        cls.real = T3.read(os.path.join(ROOT, *cls.f["c"].split("/")))
        cls.sup = T3.read(os.path.join(ROOT, *cls.f["sup"].split("/")))
        cls.old = old_c(cls.f["blob"])

    def check(self, text):
        """Stricter than containment (test_fsh's form): each function body must EQUAL its pre-registered lines (whitespace-normalised,
        comments stripped), so a token added before the first pre-registered line (e.g. `static vars ma_n`) also fails."""
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
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "%s_alt.c" % self.NAME)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            ok, why = self.check(T3.read(p))
        print("\n  [fire] %s %s in temp copy: ok=%s (%s)" % (self.NAME, label, ok, why))
        self.assertFalse(ok)

    def alter(self, a, b):
        self.assertIn(a, self.real)
        altered = self.real.replace(a, b, 1)
        self.assertNotEqual(altered, self.real)
        return altered

    # ---- (i)
    def test_i_spec_names_the_file_and_functions(self):
        cc = self.spec["corrected_code"]
        self.assertEqual(cc["file"], self.f["c"])
        self.assertTrue(cc["function"].startswith("var %s(" % self.f["core"]))
        self.assertTrue(cc["wrapper_function"].startswith("var %s(" % self.f["wrap"]))

    def test_i_real_c_contains_lines_verbatim(self):
        ok, why = self.check(self.real)
        print("\n  [i] %s: %s" % (self.f["c"], why))
        self.assertTrue(ok, why)

    def test_i_check_ignores_whitespace_and_comments(self):
        spaced = self.real.replace(" = ", "   =\t").replace("\n    ", "\n\n\t") + "\n// trailing\n/* block */\n"
        self.assertNotEqual(spaced, self.real)
        self.assertTrue(self.check(spaced)[0])
        self.assertFalse(T3.check_corrected(self.real, self.lines, self.core_sig.replace("Core", "Core_Other"))[0])
        commented = "// " + self.lines.replace("\n", "\n// ") + "\n" + self.core_sig + " { return 0; }"
        self.assertFalse(T3.check_corrected(commented, self.lines, self.core_sig)[0])

    def test_i_no_statics_globals_decimal_literals_literal_products(self):
        code = T3.strip_comments(self.real)
        self.assertEqual(generator.lint_no_static(self.real), [])
        self.assertNotRegex(code, r"\bstatic\b|\bINITRUN\b|\bPeriod\b|#include")
        self.assertEqual(re.findall(r"\d+\.\d+", code), [])
        self.assertEqual(LITERAL_PRODUCT.findall(code), [])
        self.assertEqual(global_var_lines(code), [])

    def test_i_scans_fire(self):
        code = T3.strip_comments(self.real.replace("    var ", "    static var ", 1))
        self.assertEqual(len(generator.lint_no_static(code)), 1)
        self.assertEqual(re.findall(r"\d+\.\d+", T3.strip_comments(self.real + "\nvar q = 0.5;")), ["0.5"])
        self.assertEqual(len(LITERAL_PRODUCT.findall(T3.strip_comments(self.real + "\nvar q = 2*3;"))), 1)
        self.assertEqual(global_var_lines(T3.strip_comments("var g_x = 0;\n" + self.real)), ["var g_x = 0;"])

    # ---- (ii)
    def test_ii_blob_is_the_recorded_one(self):
        rc, out, err = git("rev-parse", "%s:%s" % (BASE_COMMIT, self.f["c"]))
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.strip(), self.f["blob"])

    def test_ii_old_to_new_token_difference_is_the_fixes_only(self):
        a = Counter(T3.tokens(self.old))
        b = Counter(T3.tokens(self.real[self.real.index("var %s(" % self.f["core"]):]))
        removed, added = a - b, b - a
        print("\n  [ii] %s removed: %s\n       added: %s" % (self.NAME, dict(removed), dict(added)))
        self.assertEqual(dict(removed), self.f["removed"])
        self.assertEqual(dict(added), self.f["added"])

    def test_ii_superseded_is_the_renamed_old_blob(self):
        ok, why = check_superseded(self.NAME, self.sup, self.old)
        print("\n  [ii] %s: %s" % (self.f["sup"], why))
        self.assertTrue(ok, why)

    def test_ii_superseded_guard_fires_on_one_name_left_unprefixed(self):
        code_names = [m for m in re.findall(r"\b%s\w+" % self.f["prefix"], T3.strip_comments(self.sup))]
        victim = code_names[0]
        plain = victim[len(self.f["prefix"]):] if self.NAME == "MAMA" else "frama_" + victim[len(self.f["prefix"]):]
        lines = self.sup.split("\n")
        for k, l in enumerate(lines):                       # first CODE occurrence only
            code = l.split("//")[0]
            if re.search(r"\b%s\b" % victim, code):
                lines[k] = re.sub(r"\b%s\b" % victim, plain, code, count=1) + l[len(code):]
                break
        ok, why = check_superseded(self.NAME, "\n".join(lines), self.old)
        print("\n  [fire] %s superseded: %s left as %s: ok=%s (%s)" % (self.NAME, victim, plain, ok, why))
        self.assertFalse(ok)

    def test_ii_every_series_call_has_an_explicit_length(self):
        for name in ("MAMA", "FRAMA"):
            for rel in (FILES[name]["c"], FILES[name]["sup"]):
                code = T3.strip_comments(T3.read(os.path.join(ROOT, *rel.split("/"))))
                self.assertEqual(series_without_length(code), [], rel)
        n = len(re.findall(r"\bseries\(", T3.strip_comments(T3.read(os.path.join(ROOT, "indicators", "ehlers", "MAMA_Superseded.c")))))
        self.assertEqual(n, 15)

    def test_ii_guard_fires_when_one_explicit_length_is_removed(self):
        if self.NAME != "MAMA":
            return
        self.assertIn("series(0.0, 7);", self.sup)
        broken = self.sup.replace("series(0.0, 7);", "series(0.0);", 1)
        ok, why = check_superseded(self.NAME, broken, self.old)
        n = series_without_length(T3.strip_comments(broken))
        print("\n  [fire] MAMA superseded with one length removed: token check ok=%s (%s); length scan: %s" % (ok, why, n))
        self.assertFalse(ok)
        self.assertEqual(n, ["series(0.0)"])
        self.assertEqual(series_without_length("var* a = series(Price[0]);"), ["series(Price[0])"])

    def test_ii_superseded_comment_changes_do_not_matter(self):
        self.assertTrue(check_superseded(self.NAME, self.sup + "\n// trailing\n", self.old)[0])

    # ---- (v)
    def test_v_no_static_lint(self):
        self.assertEqual(generator.lint_no_static(self.real), [])
        hits = generator.lint_no_static(self.sup)
        print("\n  [v] %s: 0 hits; %s: %s" % (self.f["c"], self.f["sup"], hits))
        self.assertEqual([n for _, n in hits], self.f["static_hits"])


class TestMamaCorrectedCode(_Base, unittest.TestCase):
    NAME = "MAMA"

    def test_i_no_pi_token(self):
        self.assertNotRegex(T3.strip_comments(self.real), r"\bPI\b")
        self.assertRegex(T3.strip_comments(self.real + "\nvar q = PI;"), r"\bPI\b")

    def test_i_guard_fires(self):
        for a, b, label in (("    vars ma_n  = series(0, 2);", "    static vars ma_n  = series(0, 2);", "static before vars ma_n"),
                            ("var ma_w1 = 962;  ma_w1 = ma_w1/10000;", "var ma_w1 = 0.0962;", "float32 literal w1 (division removed)"),
                            ("ma_P[0] = ma_P[1];", "", "MA-2 hold ma_P[0] = ma_P[1] removed"),
                            ("ma_pi = ma_pi*atan(1);", "ma_pi = PI;", "exact pi -> PI"),
                            ("return MAMACore(Price, FastLimit, SlowLimit, outFAMA, &maw_1, &maw_2, &maw_3);", "return maw_1;", "wrapper")):
            self.fire(self.alter(a, b), label)

    def test_i_guard_fires_when_series_moved_inside_the_if(self):
        decl = "    vars ma_S  = series(0, 7);\n"
        s = self.alter(decl.replace("\n", "\r\n") if decl.replace("\n", "\r\n") in self.real else decl, "")
        head = "    if(ma_n[0] > 5) {"
        self.assertIn(head, s)
        s = s.replace(head, head + "\n" + decl.rstrip(), 1)
        self.fire(s, "vars ma_S = series(0, 7) moved inside the if")

    def test_i_series_first_and_unconditional(self):
        body = T3.norm_ws(T3.function_body(self.real, self.core_sig))
        self.assertEqual(body.count("series("), 17)
        self.assertLess(body.rindex("series("), body.index("ma_n[0] = ma_n[1] + 1;"))
        self.assertNotRegex(body, r"if\s*\([^)]*\)\s*\{?[^;{}]*series\(")


class TestFramaCorrectedCode(_Base, unittest.TestCase):
    NAME = "FRAMA"

    def test_i_guard_fires(self):
        for a, b, label in (("    vars fr_n = series(0, 2);", "    static vars fr_n = series(0, 2);", "static before vars fr_n"),
                            ("var fr_k  = 46;  fr_k  = fr_k/10;", "var fr_k  = 4.6;", "fr_k = 4.6 (division removed)"),
                            ("if(fr_N1 > 0 && fr_N2 > 0 && fr_N3 > 0)", "if(fr_N3 > 0)", "N1 / N2 guard removed (FR-5)"),
                            ("if(fr_n[0] < N + 1)", "if(fr_n[0] < N)", "start-up N + 1 -> N (FR-4)"),
                            ("return FRAMACore(Price, High, Low, N, &frw_1, &frw_2);", "return frw_1;", "wrapper")):
            self.fire(self.alter(a, b), label)

    def test_i_series_first_and_unconditional(self):
        body = T3.norm_ws(T3.function_body(self.real, self.core_sig))
        self.assertEqual(body.count("series("), 4)
        self.assertLess(body.rindex("series("), body.index("fr_n[0] = fr_n[1] + 1;"))

    def test_ii_superseded_input_edit_only(self):
        code = T3.strip_comments(self.sup)
        for s in ("vars fro_High = High;", "vars fro_Low  = Low;", "var fro_price = Price[0];", "static var fro_prev = 0;",
                  "static int fro_init = 0;", "if(fro_N3 <= 0) return fro_prev;", "exp(-4.6 * (fro_D - 1.0))"):
            self.assertIn(s, code)
        self.assertNotRegex(code, r"\bframa_|priceHigh|priceLow")
        self.assertNotRegex(code, r"\bseries\(")                        # the superseded file allocates no series of its own


@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestCallers(unittest.TestCase):
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
    def offenders(text):
        code = T3.strip_comments(text)
        bad = []
        for m in re.finditer(r"\bFRAMA\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)", code):
            if "," not in m.group(1):
                bad.append("FRAMA(%s)" % m.group(1).strip())
        for m in re.finditer(r"\bMAMA\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)", code):
            args = [a.strip() for a in m.group(1).split(",")]
            if any(re.fullmatch(r"\d*\.\d+|\d+\.\d*", a) for a in args[1:3]) or any(re.fullmatch(r"[A-Z_]+_LIMIT", a) for a in args[1:3]):
                bad.append("MAMA(%s)" % m.group(1).strip())
        return bad

    def test_vi_no_caller_uses_the_old_interface(self):
        files = self.c_files()
        self.assertTrue(files)
        for p in files:
            self.assertEqual(self.offenders(T3.read(p)), [], p)
        for rel in CALLERS:
            code = T3.strip_comments(T3.read(os.path.join(ROOT, *rel.split("/"))))
            if "FRAMA(" in code:
                self.assertRegex(code, r"series\(\(priceHigh\(\) \+ priceLow\(\)\)/2, FRAMA_N\)")
                self.assertRegex(code, r"#define FRAMA_N\s+32\b")
                self.assertRegex(code, r"FRAMA\(\w+, \w+, \w+, FRAMA_N\)")
            if "MAMA(" in code:
                self.assertRegex(code, r"= 1;\s*\w+ = \w+/2;")
                self.assertRegex(code, r"= 1;\s*\w+ = \w+/20;")

    def test_vi_scan_fires_on_the_old_interface(self):
        self.assertEqual(self.offenders("var f = FRAMA(16);\nvar g = FRAMA(FRAMA_T);"), ["FRAMA(16)", "FRAMA(FRAMA_T)"])
        self.assertEqual(self.offenders("var m = MAMA(Price, 0.5, 0.05, &f);"), ["MAMA(Price, 0.5, 0.05, &f)"])
        self.assertEqual(self.offenders("var m = MAMA(Price, FAST_LIMIT, SLOW_LIMIT, &f);"), ["MAMA(Price, FAST_LIMIT, SLOW_LIMIT, &f)"])
        self.assertEqual(self.offenders("var m = MAMA(Price, fl, sl, &f);\nvar g = FRAMA(a, b, c, 32);"), [])
        print("\n  [fire] (vi) FRAMA(16), FRAMA(FRAMA_T), MAMA(Price, 0.5, 0.05, ...) and the FAST_LIMIT form are reported")

    def test_vi_exactly_the_four_callers_call_the_indicators(self):
        who = set()
        for p in self.c_files():
            code = T3.strip_comments(T3.read(p))
            if re.search(r"\b(MAMA|FRAMA)\s*\(", code) and not os.path.basename(p) in ("MAMA.c", "FRAMA.c") \
                    and not os.path.basename(p).startswith("GEN_"):
                who.add(os.path.relpath(p, ROOT).replace(os.sep, "/"))
        self.assertEqual(who, set(CALLERS))


if __name__ == "__main__":
    unittest.main()
