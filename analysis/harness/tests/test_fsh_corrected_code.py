"""Permanent pre-run tests for FSH (spec FSH_ArticleFidelity.toml, pre-run conditions i, ii, v and vi).

  (i)  indicators/ehlers/FisherTransform.c contains [corrected_code].lines inside FisherCore and .wrapper_lines inside
       FisherTransform (whitespace-normalised, comments stripped); the guard is SEEN TO FIRE on in-memory / temp copies.
  (ii) The old FisherTransform.c (git blob 259954ed90f4674733f41c46b6694c5f1320cfd0, read from git) -> new file differs only by
       F-1, F-2, F-3, F-7 (+ Core / wrapper structure); the token difference is printed and asserted exactly.
       FisherTransform_Superseded.c equals the old blob after the renames, the Price parameter and the input line.
  (v)  no `static` in FisherTransform.c (generator.lint_no_static); 2 hits on the superseded file (fto_Value1, fto_Fish).
  (vi) no caller in the repo still reads ft_Trigger or calls FisherTransform( with one argument.
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

SPEC = os.path.join(HARNESS, "specs", "FSH_ArticleFidelity.toml")
REL_C = "indicators/ehlers/FisherTransform.c"
REL_SUP = "indicators/ehlers/FisherTransform_Superseded.c"
OLD_BLOB = "259954ed90f4674733f41c46b6694c5f1320cfd0"
CORE_SIG = "var FisherCore(vars Price, int Len, var* pRaw, var* pV1, var* pRng, var* pTrig)"
WRAP_SIG = "var FisherTransform(vars Price, int Len)"
CALLERS = ("strategies/tests/Test_Fisher_IFT_COG.c", "strategies/tests/Test_S1_C2_Audit.c")


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
    s = re.sub(r"\bft_", "fto_", old).replace("var FisherTransform(int Period)", "var FisherTransform_Superseded(vars Price, int Period)")
    return s.replace("vars fto_Mid = series((priceHigh() + priceLow()) * 0.5);", "vars fto_Mid = Price;")


def check_superseded(sup_text, old):
    a, b = T3.tokens(renamed_old(old)), T3.tokens(sup_text)
    if a == b:
        return True, "token-identical to the renamed old blob"
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return False, "first token difference at %d: %r vs %r" % (k, x, y)
    return False, "length differs: %d vs %d tokens" % (len(a), len(b))


LITERAL_PRODUCT = re.compile(r"(?:^|[=(,;{]|\breturn)\s*\d+(?:\.\d+)?\s*[*/]\s*\d")


def literal_product_hits(code):
    return LITERAL_PRODUCT.findall(code)


def global_var_lines(code):
    """Declarations of var / vars at brace depth 0 that are not function definitions."""
    depth, top = 0, []
    for line in code.split("\n"):
        if depth == 0 and re.match(r"\s*vars?\b", line) and "(" not in line:
            top.append(line.strip())
        depth += line.count("{") - line.count("}")
    return top


# (b) token multiset difference old file -> new file (FisherCore + wrapper), measured 2026-11-19 and asserted exactly. The new
# identifiers are renames (ft_ -> fi_). By decision:
#  F-1: both statics + INITRUN resets (static x2, if x2, is x2, INITRUN x2), the global ft_Trigger (x2), state now series fi_V / fi_F.
#  F-2: `series((priceHigh() + priceLow()) * 0.5)` -> the Price parameter (priceHigh, priceLow, +, 0.5; ft_Mid -> Price).
#  F-3: 0.33, 0.67, 0.99 x2, 0.999 x2, 0.5 x3 more, 1.0 x2 -> integer-built constants (33/100 ... 999/1000, 1/2, fi_u = 1).
#  F-7: Core signature with 4 out-parameters, the four out assignments, the wrapper (fi_w1..fi_w4, `&`).
#  also (pre-registered form, same arithmetic): `2.0*((x - lo)/rng - .5)` -> four steps (`fi_raw = fi_raw*2` etc.), Period -> Len.
EXPECTED_REMOVED = {'ft_Trigger': 2, '(': 9, 'Period': 3, ')': 9, 'ft_Mid': 4, 'priceHigh': 1, '+': 1, 'priceLow': 1, '0.5': 4, 'ft_MaxH': 3,
                    'ft_MinL': 4, 'ft_raw': 3, 'if': 2, '-': 1, '2.0': 1, 'static': 2, 'ft_Value1': 10, 'is': 2, 'INITRUN': 2,
                    '0.33': 1, '0.67': 1, '0.99': 2, '0.999': 2, 'ft_Fish': 6, '1.0': 2}
EXPECTED_ADDED = {'var': 17, 'FisherCore': 2, 'vars': 3, 'Price': 6, ',': 13, 'int': 1, 'Len': 5, '*': 7, 'pRaw': 2, 'pV1': 2, 'pRng': 2,
                  'pTrig': 2, '{': 2, 'fi_V': 10, '=': 20, 'series': 1, '0': 9, '2': 4, ';': 25, 'fi_F': 5, 'fi_a': 4, '33': 1, '/': 5,
                  '100': 3, 'fi_b': 4, '67': 1, 'fi_t': 5, '99': 1, 'fi_c': 5, '999': 1, '1000': 1, 'fi_h': 6, '1': 5, 'fi_hi': 2,
                  'fi_lo': 3, 'fi_rng': 4, 'fi_raw': 10, '[': 13, ']': 13, '}': 2, 'fi_nt': 4, 'fi_nc': 4, 'fi_u': 3, 'fi_num': 2,
                  'fi_den': 2, 'return': 1, 'fi_w1': 2, 'fi_w2': 2, 'fi_w3': 2, 'fi_w4': 2, '&': 4}


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestFSHCorrectedCode(unittest.TestCase):
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
            p = os.path.join(d, "FisherTransform_alt.c")
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
        alterations = (("    var fi_hi = MaxVal(Price, Len);", "    static var fi_hi = MaxVal(Price, Len);"),        # static added
                       ("var fi_a = 33;   fi_a = fi_a/100;", "var fi_a = 0.33;"),                                 # float32 literal (F-3)
                       ("*pTrig = fi_F[1];", "*pTrig = fi_F[0];"),                                                # trigger not delayed
                       ("if(fi_V[0] > fi_t)  fi_V[0] = fi_c;", "if(fi_V[0] > fi_t)  fi_V[0] = fi_t;"),           # clamp set value
                       ("return FisherCore(Price, Len, &fi_w1, &fi_w2, &fi_w3, &fi_w4);", "return fi_w1;"),      # wrapper
                       ("fi_F[0] = fi_h*log(fi_num/fi_den) + fi_h*fi_F[1];", "fi_F[0] = fi_h*log(fi_num/fi_den) + fi_h*fi_F[0];"))
        for a, b in alterations:
            self.assertIn(a, self.real)
            altered = self.real.replace(a, b, 1)
            self.assertNotEqual(altered, self.real, a)
            self.fire(altered, "%s -> %s" % (a.strip(), b.strip()))

    def test_i_guard_fires_when_series_moved_inside_the_if(self):
        s = self.real
        decl = "    vars fi_V = series(0, 2);\n"
        self.assertIn(decl, s)
        s = s.replace(decl, "", 1)
        old = "    if(fi_rng > 0) {\n"
        self.assertIn(old, s)
        s = s.replace(old, old + "    " + decl.strip() + "\n", 1)
        self.assertNotEqual(s, self.real)
        ok, why = check_both(s, self.lines, self.wrap)
        print("\n  [fire] vars fi_V = series(0, 2); moved inside the if: ok=%s (%s)" % (ok, why))
        self.assertFalse(ok)

    def test_i_guard_fires_on_wrong_function_and_comment_only_lines(self):
        self.assertFalse(T3.check_corrected(self.real, self.lines, CORE_SIG.replace("Core", "Core_Other"))[0])
        commented = "// " + self.lines.replace("\n", "\n// ") + "\n" + CORE_SIG + " { return 0; }"
        self.assertFalse(T3.check_corrected(commented, self.lines, CORE_SIG)[0])

    def test_i_real_c_has_both_series_first(self):
        body = T3.norm_ws(T3.function_body(self.real, CORE_SIG))
        for name in ("fi_V", "fi_F"):
            self.assertIn("vars %s = series(0, 2);" % name, body)
            self.assertLess(body.index("vars %s = series(" % name), body.index("var fi_a = 33;"))
        self.assertEqual(body.count("series("), 2)
        self.assertNotRegex(body, r"if\s*\([^)]*\)\s*\{?[^;{}]*series\(")

    def test_i_no_statics_no_globals_no_decimal_literals_no_period(self):
        code = T3.strip_comments(self.real)
        self.assertEqual(generator.lint_no_static(self.real), [])
        self.assertNotRegex(code, r"\bstatic\b")
        self.assertNotRegex(code, r"\bINITRUN\b")
        self.assertNotRegex(code, r"\bPeriod\b")
        self.assertNotRegex(code, r"\bft_")
        self.assertEqual(re.findall(r"\d+\.\d+", code), [])
        self.assertEqual(literal_product_hits(code), [])
        self.assertEqual(global_var_lines(code), [])

    def test_i_static_literal_and_global_scans_fire(self):
        altered = self.real.replace("    var fi_hi = ", "    static var fi_hi = ", 1)
        self.assertEqual([n for _, n in generator.lint_no_static(altered)], ["fi_hi"])
        altered2 = self.real.replace("var fi_a = 33;   fi_a = fi_a/100;", "var fi_a = 0.33;", 1)
        self.assertEqual(re.findall(r"\d+\.\d+", T3.strip_comments(altered2)), ["0.33"])
        altered3 = self.real.replace("var fi_u = 1;", "var fi_u = 2*0.5*1;", 1)
        self.assertEqual(len(literal_product_hits(T3.strip_comments(altered3))), 1)
        altered4 = "var ft_Trigger = 0;\n" + self.real
        code4 = T3.strip_comments(altered4)
        self.assertRegex(code4, r"\bft_")
        self.assertEqual(global_var_lines(code4), ["var ft_Trigger = 0;"])
        print("\n  [fire] static / 0.33 / 2*0.5*1 / global var ft_Trigger added: each scan sees it")

    # ---- (ii)
    def test_ii_blob_is_the_recorded_one(self):
        rc, out, err = git("rev-parse", "258b24a:%s" % REL_C)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.strip(), OLD_BLOB)

    def test_ii_old_to_new_token_difference_is_the_fixes_only(self):
        a = Counter(T3.tokens(old_c()))
        b = Counter(T3.tokens(self.real[self.real.index(CORE_SIG):]))
        removed, added = a - b, b - a
        print("\n  [ii] removed tokens: %s\n       added tokens: %s" % (dict(removed), dict(added)))
        self.assertEqual(dict(removed), EXPECTED_REMOVED)
        self.assertEqual(dict(added), EXPECTED_ADDED)

    def test_ii_old_blob_has_what_the_diff_removes(self):
        old = T3.strip_comments(old_c())
        for s in ("static var ft_Value1", "static var ft_Fish", "var ft_Trigger = 0;", "* 0.5)", "0.33 * ft_raw", "(1.0 + ft_Value1)"):
            self.assertIn(s, old)

    def test_ii_guard_fires_on_any_extra_change(self):
        a = Counter(T3.tokens(old_c()))
        for x, y in (("fi_h*log(fi_num", "fi_a*log(fi_num"), ("if(fi_rng > 0)", "if(fi_rng >= 0)")):
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
        self.assertNotRegex(code, r"\bft_")
        for s in ("static var fto_Value1 = 0;", "static var fto_Fish = 0;", "var fto_Trigger = 0;", "0.33 * fto_raw", "vars fto_Mid = Price;"):
            self.assertIn(s, code)

    def test_ii_superseded_guard_fires(self):
        for a, b in (("static var fto_Value1 = 0;", "static var ft_Value1 = 0;"), ("0.33 * fto_raw", "0.34 * fto_raw"),
                     ("fto_Value1 >  0.99", "fto_Value1 >  0.98"), ("vars fto_Mid = Price;   //", "vars fto_Mid = series(Price[0]);   //")):
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
        print("\n  [v] FisherTransform.c: 0 hits; FisherTransform_Superseded.c: %s" % hits)
        self.assertEqual([n for _, n in hits], ["fto_Value1", "fto_Fish"])

    # ---- (vi)
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
        if re.search(r"\bft_Trigger\b", code):
            bad.append("reads ft_Trigger")
        for m in re.finditer(r"\bFisherTransform\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)", code):
            args = m.group(1)
            if "," not in args and "vars Price" not in args:
                bad.append("FisherTransform(%s)" % args.strip())
        return bad

    def test_vi_no_caller_uses_the_old_interface(self):
        real_c = os.path.normpath(os.path.join(ROOT, *REL_C.split("/")))
        files = [p for p in self.c_files() if os.path.normpath(p) != real_c]
        self.assertTrue(files)
        for p in files:
            if os.path.basename(p) == "FisherTransform_Superseded.c":
                continue  # its own global fto_Trigger is the control's, and it has no ft_ token (asserted in test_ii)
            self.assertEqual(self.offenders(T3.read(p)), [], p)
        for rel in CALLERS:
            code = T3.strip_comments(T3.read(os.path.join(ROOT, *rel.split("/"))))
            self.assertRegex(code, r"series\(\(priceHigh\(\) \+ priceLow\(\)\)/2")

    # ---- (vi) flat namespace: fi_ belongs to FisherCore only (gotchas 1.3)
    @staticmethod
    def fi_declarations(text):
        code = T3.strip_comments(text)
        return re.findall(r"\b(?:vars?|int|float|double|static)\s+(?:\*\s*)?(fi_\w*)", code)

    def test_vi_no_other_file_declares_fi_identifiers(self):
        real_c = os.path.normpath(os.path.join(ROOT, *REL_C.split("/")))
        n = 0
        for p in self.c_files():
            if os.path.normpath(p) == real_c:
                continue
            n += 1
            self.assertEqual(self.fi_declarations(T3.read(p)), [], p)
        self.assertGreater(n, 0)
        self.assertNotEqual(self.fi_declarations(self.real), [])  # the scan does see FisherCore's own

    def test_vi_fi_scan_fires_on_the_old_caller(self):
        old_caller = ("    vars fi_mid = series((priceHigh() + priceLow())/2, 10);\n    var fi_raw = 0;\n"
                      "    var fisher = FisherCore(fi_mid, 10, &fi_raw, &a, &b, &c);\n")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "Old_Caller.c")
            with open(p, "w", encoding="utf-8") as f:
                f.write(old_caller)
            hits = self.fi_declarations(T3.read(p))
        print("\n  [fire] (vi) temp copy of the old caller declares: %s" % hits)
        self.assertEqual(hits, ["fi_mid", "fi_raw"])

    def test_vi_scan_fires_on_the_old_interface(self):
        self.assertEqual(self.offenders("var f = FisherTransform(10);\nvar t = ft_Trigger;"), ["reads ft_Trigger", "FisherTransform(10)"])
        self.assertEqual(self.offenders("var f = FisherTransform(Price, 10);"), [])
        print("\n  [fire] (vi) the old call `FisherTransform(10)` and `ft_Trigger` are both reported")


if __name__ == "__main__":
    unittest.main()
