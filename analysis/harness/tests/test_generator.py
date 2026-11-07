"""Self-test for analysis/harness/generator.py (STEP2_HANDOFF.md, Stage 3 + Amendment 2, G1-G9).

Run:  bash analysis/harness/run_tests.sh      (or python -m unittest discover -s analysis/harness/tests -v)
Generated scripts are written to a temporary directory, never to strategies/tests/ (A2.3).
The H1 harness .c is only read (G2, G5) and hashed (G8).
"""
import copy
import hashlib
import io
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(HARNESS, "..", ".."))
sys.path.insert(0, HARNESS)
import checker as C        # noqa: E402
import generator as G      # noqa: E402

SPEC_PATH = os.path.join(HARNESS, "specs", "H1_SuperSmoother2Pole.toml")
H1_C = os.path.join(REPO, "strategies", "tests", "H1_SuperSmoother2Pole_Harness.c")
TESTS_DIR = os.path.join(REPO, "strategies", "tests")
CALL_RE = re.compile(r"^\s*Y\[(\d+)\]\s*=\s*(\w+)\((\w+),\s*(\d+)\);")


def spec():
    return G.load_spec(SPEC_PATH)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def calls_of(lines):
    out = []
    for ln in lines:
        m = CALL_RE.match(ln)
        if m:
            out.append((int(m.group(1)), m.group(2), m.group(3), int(m.group(4))))
    return out


def func_text(text, name):
    """Text of `var <name>(...) { ... }` by brace matching."""
    i = text.index("var %s(" % name)
    j = text.index("{", i)
    depth = 0
    for k in range(j, len(text)):
        depth += text[k] == "{"
        depth -= text[k] == "}"
        if depth == 0:
            return text[i:k + 1]
    raise AssertionError("unbalanced braces")


def norm(s):
    return " ".join(s.split())


def refused(s):
    errs, _ = G.validate_spec(s)
    return [c for c, _ in errs]


def find_bash():
    cands = [os.environ.get("BASH_EXE"), "C:/Program Files/Git/bin/bash.exe"]
    w = shutil.which("bash")
    if w and "system32" not in w.lower():
        cands.insert(1, w)
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


class TestGenerator(unittest.TestCase):

    # ------------------------------------------------------------------ G1
    def test_g1_spec_to_checker_dict(self):
        """G1: H1 spec -> checker dict equals stage 2's hand-written H1 dict, exact."""
        d = G.to_checker_spec(spec())
        want = C.h1_spec()
        self.assertEqual(d, want)
        print("  G1 spec -> checker dict == checker.h1_spec() (exact, %d keys, %d variants) PASS"
              % (len(d), len(d["variants"])))
        bad = spec()
        bad["tolerances"]["gain"]["value"] = 2e-4
        self.assertNotEqual(G.to_checker_spec(bad), want)
        print("  G1 guard: gain tolerance changed in the spec -> dict differs (comparison can fail) PASS")

    # ------------------------------------------------------------------ G2
    def test_g2_call_list_vs_h1_harness(self):
        """G2: ordered (slot, function, input series, parameter) tuples == H1 .c lines 114-155."""
        with open(H1_C, encoding="utf-8") as f:
            h1_lines = f.read().split("\n")[113:155]          # lines 114..155 (1-based)
        want = calls_of(h1_lines)
        self.assertEqual(len(want), 42, "H1 lines 114-155 must hold exactly the 42 calls")
        text, _ = G.build_script(spec())
        got = calls_of(text.split("\n"))
        self.assertEqual(got, want)
        print("  G2 %d call tuples identical to H1 harness lines 114-155 (exact) PASS" % len(got))
        s2 = spec()
        s2["variants"][2]["param"] = 21
        self.assertNotEqual(calls_of(G.build_script(s2)[0].split("\n")), want)
        print("  G2 guard: one parameter changed in the spec -> call list differs PASS")

    # ------------------------------------------------------------------ G3
    def _header_of_script(self, text, prefix="H1"):
        blk = text[text.index("if(!h1_hdr) {"):text.index("h1_hdr = 1;")]
        parts = re.findall(r'file_append\(%s_RAW, "((?:[^"\\]|\\.)*)", 0\);' % prefix, blk)
        joined = "".join(parts)
        self.assertTrue(joined.endswith("\\n"))
        return joined[:-2]

    def test_g3_header_matches_checker(self):
        """G3: raw CSV header written by the generated script == checker's expected header."""
        s = spec()
        text, _ = G.build_script(s)
        got = self._header_of_script(text)
        want = ",".join(C.header_of(G.to_checker_spec(s)))
        self.assertEqual(got, want)
        print("  G3 header identical to checker.header_of (%d columns, exact string) PASS" % len(got.split(",")))
        s2 = spec()
        s2["variants"][0]["id"] = "Q10"
        self.assertNotEqual(self._header_of_script(G.build_script(s2)[0]), want)
        print("  G3 guard: variant renamed -> header differs from the original checker header PASS")

    # ------------------------------------------------------------------ G4
    def test_g4_input_expressions(self):
        """G4: input expressions of the generated script, evaluated in Python (math namespace
        only), equal the checker inputs for n = 0..N-1, tol 1e-12."""
        s = spec()
        text, _ = G.build_script(s)
        lines = text.split("\n")
        a = next(i for i, l in enumerate(lines) if "// --- constants" in l)
        b = next(i for i, l in enumerate(lines) if "// --- inputs" in l)
        c = next(i for i, l in enumerate(lines) if "// --- input series" in l)
        ns = {"sin": math.sin, "atan": math.atan}
        for l in lines[a + 1:b]:
            for stmt in l.replace("var ", "").split(";"):
                if stmt.strip():
                    exec(stmt.strip(), {"atan": math.atan}, ns)      # e.g. lvl = 11 ; lvl = lvl / 10
        exprs = {}
        for l in lines[b + 1:c]:
            m = re.match(r"\s*X\[(\d+)\] = (.+);", l)
            if m:
                exprs[int(m.group(1))] = m.group(2)
        chk = G.to_checker_spec(s)
        x = C.make_inputs(chk)
        ids = G.input_ids(s)
        self.assertEqual(sorted(exprs), list(range(len(ids))))
        worst = 0.0
        for k, iid in enumerate(ids):
            code = compile(exprs[k], "<X[%d]>" % k, "eval")
            for n in range(chk["n_bars"]):
                v = eval(code, {"__builtins__": {}}, dict(ns, n=n))
                worst = max(worst, abs(v - x[iid][n]))
        print("  G4 %d input expressions x %d bars vs checker inputs: worst |diff| %.3e tol 1e-12 %s"
              % (len(ids), chk["n_bars"], worst, "PASS" if worst <= 1e-12 else "FAIL"))
        self.assertLessEqual(worst, 1e-12)
        # guard: a wrong amplitude constant must be seen
        ns2 = dict(ns, amp=ns["amp"] * 1.001)
        k = 3
        d = max(abs(eval(exprs[k], {"__builtins__": {}}, dict(ns2, n=n)) - x[ids[k]][n]) for n in range(200))
        self.assertGreater(d, 1e-12)
        print("  G4 guard: amplitude changed by 0.1%% -> mismatch %.3e seen PASS" % d)

    # ------------------------------------------------------------------ G5
    def test_g5_inline_nc_body(self):
        """G5: inline NC function in the generated script == H1 h1_ss_deg, whitespace-normalised."""
        with open(H1_C, encoding="utf-8") as f:
            want = norm(func_text(f.read(), "h1_ss_deg"))
        text, bodies = G.build_script(spec())
        got = norm(func_text(text, "h1_ss_deg"))
        self.assertEqual(got, want)
        self.assertEqual(len(bodies), 1)
        print("  G5 inline NC2 body identical to H1 h1_ss_deg (%d chars, whitespace-normalised) PASS" % len(got))
        s2 = spec()
        s2["variants"][5]["body"] = s2["variants"][5]["body"].replace("180.0", "90.0")
        self.assertNotEqual(norm(func_text(G.build_script(s2)[0], "h1_ss_deg")), want)
        print("  G5 guard: 180.0 -> 90.0 in the spec body -> differs from H1 PASS")

    # ------------------------------------------------------------------ G6
    def test_g6_validator_refusals(self):
        """G6: the validator fires on each deliberately broken spec, with the right reason."""
        base = spec()
        errs, infos = G.validate_spec(base)
        self.assertEqual(errs, [])
        self.assertGreaterEqual(len(infos), 5)
        print("  G6 clean H1 spec accepted; %d INFO lines:" % len(infos))
        for i in infos:
            print("     " + i)

        def mk(fn):
            s = copy.deepcopy(base)
            fn(s)
            return s

        def rm_nc(s):
            s["variants"] = [v for v in s["variants"] if v["role"] != "neg_control"]

        def lit(**kw):
            def f(s):
                r = dict(literal="1.414", exact=math.sqrt(2.0), source="(a) TASC V.42:04")
                r.update(kw)
                for k in [k for k, v in r.items() if v is None]:
                    del r[k]
                s["literal_replacements"] = [r]
            return f
        cases = [
            ("batch prefix contains '-'", lambda s: s["batch"].update(id_prefix="H-1"), "ID_HYPHEN"),
            ("variant id contains '-'", lambda s: s["variants"][0].update(id="P-10"), "ID_HYPHEN"),
            ("variant id not a C fragment (space)", lambda s: s["variants"][0].update(id="P 10"), "ID_NOT_C"),
            ("variant id not a C fragment (dot)", lambda s: s["variants"][1].update(id="P.14"), "ID_NOT_C"),
            ("input id: sine period not a positive int", lambda s: s["inputs"].update(sine_periods=[5, 10, 20, 40, -100]), "ID_NOT_C"),
            ("tolerance without source", lambda s: s["tolerances"]["gain"].pop("source"), "SOURCE_MISSING"),
            ("tolerance source without (a)/(b)/(c)", lambda s: s["tolerances"]["lag"].update(source="H1 criteria"), "SOURCE_MISSING"),
            ("expected table without source", lambda s: s["expected"]["P20"].pop("source"), "SOURCE_MISSING"),
            ("expected table with unlabelled source", lambda s: s["expected"]["P10"].update(source="table"), "SOURCE_MISSING"),
            ("no negative control", rm_nc, "NO_NEG_CONTROL"),
            ("D1 literal replacement without exact value", lit(exact=None), "LITERAL_INCOMPLETE"),
            ("D1 literal replacement without literal", lit(literal=None), "LITERAL_INCOMPLETE"),
            ("D1 literal replacement without source", lit(source=None), "LITERAL_INCOMPLETE"),
            ("D1 literal replacement with unlabelled source", lit(source="TASC"), "LITERAL_INCOMPLETE"),
        ]
        for desc, fn, code in cases:
            got = refused(mk(fn))
            print("  G6 refused: %-46s -> %s %s" % (desc, got, "PASS" if code in got else "FAIL"))
            self.assertIn(code, got, desc)
            with self.assertRaises(G.SpecError):
                G.build_script(mk(fn))                       # the generator itself refuses
        ok = mk(lit())
        self.assertEqual(refused(ok), [])
        print("  G6 complete D1 literal replacement (literal, exact, source) accepted PASS")
        # INFO only, never a refusal: a tolerance below floor x 10
        tight = mk(lambda s: s["tolerances"]["gain"].update(value=1e-6))
        errs, infos = G.validate_spec(tight)
        self.assertEqual(errs, [])
        self.assertTrue(any("EXCEEDS TOLERANCE" in i for i in infos))
        weak = mk(lambda s: s["variants"][4]["effect"].update(gain=1e-5, lag=1e-5))
        errs, infos = G.validate_spec(weak)
        self.assertEqual(errs, [])
        self.assertTrue(any("NC1" in i and "NOT met" in i for i in infos))
        print("  G6 INFO-only: floor x10 > tolerance and a control below 10x are reported, spec not refused PASS")

    # ------------------------------------------------------------------ G7
    def test_g7_lint(self):
        """G7: lint fires on each broken script (one per rule) and passes the generated H1 script;
        Amendment 2: PI in input construction refused, same token inside an inline NC body accepted."""
        s = spec()
        text, bodies = G.build_script(s)
        base = TESTS_DIR
        self.assertEqual(G.lint_script(text, bodies, base), [])
        self.assertIn("PI", bodies[0])
        print("  G7 generated H1 script passes the lint (PI inside the inline NC body accepted, A2.2) PASS")

        def rules(t, b=bodies):
            return [r for r, _ in G.lint_script(t, b, base)]
        broken = [
            ("PI in input construction (A2.2)", text.replace("2 * pi_x * n / 5", "2 * PI * n / 5"), "L_PI"),
            ("decimal literal 1.1 (not float32-exact)", text.replace("X[0] = lvl;", "X[0] = 1.1;"), "L_FLOAT32"),
            ("decimal literal 0.01", text.replace("X[6] = lvl + slp * n;", "X[6] = lvl + 0.01 * n;"), "L_FLOAT32"),
            ("file_append after quit() in the same block",
             text.replace('quit("H1 batch complete: 3000 rows written");',
                          'quit("H1 batch complete: 3000 rows written");\n\t\t\tfile_append(H1_RAW, "late", 0);'), "L_QUIT"),
            ("missing include", text.replace("SuperSmoother2Pole.c", "NoSuchIndicator.c"), "L_INCLUDE"),
        ]
        for desc, t, rule in broken:
            got = rules(t)
            print("  G7 refused: %-46s -> %s %s" % (desc, got, "PASS" if rule in got else "FAIL"))
            self.assertIn(rule, got, desc)
        # PI scope: the same PI in an inline body is accepted only because it is declared inline
        self.assertIn("L_PI", rules(text, b=[]))
        print("  G7 scope: the same PI is refused if the body is not declared inline (lint is not blind) PASS")
        # lint rules still apply inside inline bodies (A2.1)
        body2 = bodies[0].replace("sqrt(2.0) * 180.0", "sqrt(2.1) * 180.0")
        self.assertNotEqual(body2, bodies[0])
        self.assertIn("L_FLOAT32", rules(text.replace(bodies[0], body2), b=[body2]))
        print("  G7 A2.1: decimal literal 2.1 inside an inline body is still refused PASS")
        # float32 exactness boundary: exact binary fractions pass, 1.1 / 0.01 do not
        self.assertEqual(G.lint_script("x = 2.0 + 180.0 + 0.5 + 1.0;", (), base), [])
        self.assertEqual([r for r, _ in G.lint_script("x = 1.1 + 0.01;", (), base)], ["L_FLOAT32", "L_FLOAT32"])
        print("  G7 literals: 2.0, 180.0, 0.5, 1.0 pass; 1.1, 0.01 refused PASS")
        # the generator refuses to write a failing script and writes nothing
        s2 = spec()
        s2["zorro"]["include"] = "../../indicators/ehlers/NoSuchIndicator.c"
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(G.LintError):
                G.write_script(s2, td, include_base=base)
            self.assertEqual(os.listdir(td), [])
        print("  G7 write_script refuses a lint failure and leaves no file PASS")

    # ------------------------------------------------------------------ G8
    def test_g8_write_script_no_overwrite(self):
        """G8: script written under a new name in a temp dir; an existing .c is never overwritten;
        the H1 harness (and strategies/tests/) unchanged: sha256 before = after."""
        before = sha(H1_C)
        listing_before = sorted(os.listdir(TESTS_DIR))
        s = spec()
        with tempfile.TemporaryDirectory() as td:
            path = G.write_script(s, td)
            self.assertTrue(path.startswith(td))
            self.assertNotEqual(os.path.basename(path), os.path.basename(H1_C))
            with open(path, encoding="utf-8") as f:
                written = f.read()
            self.assertEqual(written, G.build_script(s)[0])
            print("  G8 written: %s (%d bytes), new name, temp dir PASS" % (os.path.basename(path), len(written)))
            with self.assertRaises(FileExistsError):
                G.write_script(s, td)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), written)
            print("  G8 second write to the same name refused (FileExistsError), file unchanged PASS")
            # decoy: an existing .c with the H1 harness's own name must not be overwritten
            decoy = os.path.join(td, "H1_SuperSmoother2Pole_Harness.c")
            with open(decoy, "w", encoding="utf-8") as f:
                f.write("// decoy\n")
            s2 = spec()
            s2["batch"]["script_name"] = "H1_SuperSmoother2Pole_Harness"
            with self.assertRaises(FileExistsError):
                G.write_script(s2, td)
            with open(decoy, encoding="utf-8") as f:
                self.assertEqual(f.read(), "// decoy\n")
            print("  G8 existing H1-named .c in the target dir refused, content unchanged PASS")
        after = sha(H1_C)
        self.assertEqual(before, after)
        self.assertEqual(listing_before, sorted(os.listdir(TESTS_DIR)))
        print("  G8 H1 harness sha256 before = after (%s...); strategies/tests listing unchanged PASS" % after[:12])

    # ------------------------------------------------------------------ G9
    def test_g9_run_tests_summary(self):
        """G9: run_tests.sh summary counts == unittest's own counts; skips listed with reason.
        Runs the script on a fixture suite (running it on this suite would recurse)."""
        bash = find_bash()
        if bash is None:
            self.skipTest("G9 not available: no usable bash found (set BASH_EXE)")
        fixture = (
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_a(self): pass\n"
            "    def test_b(self): pass\n"
            "    def test_c(self): self.fail('deliberate failure')\n"
            "    def test_d(self): raise RuntimeError('deliberate error')\n"
            "    def test_e(self): self.skipTest('reason one')\n"
            "    def test_f(self):\n"
            "        '''has a docstring'''\n"
            "        self.skipTest('reason two')\n")
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "test_fixture_g9.py"), "w", encoding="utf-8") as f:
                f.write(fixture)
            res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
                unittest.defaultTestLoader.discover(td, pattern="test_fixture_g9.py"))
            sys.modules.pop("test_fixture_g9", None)
            if td in sys.path:
                sys.path.remove(td)
            n, f_, e_, s_ = res.testsRun, len(res.failures), len(res.errors), len(res.skipped)
            want = "TOTAL %d  PASS %d  FAIL %d  ERROR %d  SKIP %d" % (n, n - f_ - e_ - s_, f_, e_, s_)
            script = os.path.join(HARNESS, "run_tests.sh").replace("\\", "/")
            env = dict(os.environ, HARNESS_TEST_DIR=td.replace("\\", "/"))
            r = subprocess.run([bash, script], capture_output=True, text=True, env=env, encoding="utf-8")
            out = r.stdout
            last = [l for l in out.splitlines() if l.startswith("TOTAL")][-1]
            self.assertEqual(last, want, out + r.stderr)
            self.assertNotEqual(r.returncode, 0)             # failures present -> non-zero exit
            skips = [l for l in out.splitlines() if l.startswith("SKIP  ")]
            self.assertEqual(len(skips), 2, out)
            self.assertTrue(any("reason one" in l for l in skips) and any("reason two" in l for l in skips))
            print("  G9 summary '%s' == unittest's own counts (exact); %d skips listed with reasons PASS"
                  % (last, len(skips)))
            for l in skips:
                print("     " + l)


if __name__ == "__main__":
    unittest.main()
