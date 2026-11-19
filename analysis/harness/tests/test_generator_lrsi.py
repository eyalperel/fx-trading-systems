"""LRSI stage 1: generator tooling for the Laguerre RSI: real-valued parameters built from integers ([batch].real_params, [n, d] pairs),
four columns per call (l0 / l3 / den by out-parameter, out returned), linear checks on two outputs (expected_outputs), the falling ramp
`rampdn`, ramp_exact / startup_output keys, per-variant skip_inputs (Amendment 1 A), the no-static pre-run lint ([lint].no_static,
Amendment 1 C), the spec refusals, generator / checker column parity, and byte-identical regeneration of ALL EIGHT existing specs.

Rule (CLAUDE.md 4.4): each refusal / lint is seen to fire on a deliberately broken input, one defect at a time.
Stage 2 writes LaguerreRSI_Superseded.c and the corrected LaguerreRSI.c: until then lint may report ONLY the missing
LaguerreRSI_Superseded.c include and the two statics of the current LaguerreRSI.c (this test passes before and after stage 2).
Git is used read-only (git show). No Zorro run. Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lrs_support as S      # noqa: E402

G, C, R = S.G, S.C, S.R
HARNESS, ROOT = S.HARNESS, S.ROOT
EXISTING = (("H1_SuperSmoother2Pole.toml", "GEN_H1_SuperSmoother2Pole.c"),
            ("SS2_ArticleFidelity.toml", "GEN_SS2F_SuperSmoother2Pole.c"),
            ("SS3_ArticleFidelity.toml", "GEN_SS3F_SuperSmoother3Pole.c"),
            ("HP_ArticleFidelity.toml", "GEN_HPF_HighPassFilter.c"),
            ("RFF_ArticleFidelity.toml", "GEN_RFF_RoofingFilter.c"),
            ("USE_ArticleFidelity.toml", "GEN_USE_UltimateSmootherE.c"),
            ("RFX_ArticleFidelity.toml", "GEN_RFX_Reflex.c"),
            ("MESA_ArticleFidelity.toml", "GEN_MST_MESAStochastic.c"))
OLD_COMMIT = "6382607"                       # the superseded LaguerreRSI.c (review base, mtime 2026-08-21)
REL_C = "indicators/ehlers/LaguerreRSI.c"
BASE = ["flat", "s5", "s10", "s20", "s40", "s100", "alt", "ramp", "rampdn"]


def lrs():
    return copy.deepcopy(G.load_spec(S.SPEC_PATH))


def codes(spec):
    errs, _ = G.validate_spec(spec)
    return [c for c, _ in errs]


def variant(spec, vid):
    return [v for v in spec["variants"] if v["id"] == vid][0]


def stage2_issue(rule, msg):
    return ((rule == "L_INCLUDE" and "LaguerreRSI_Superseded.c" in msg)
            or (rule == "L_NO_STATIC" and REL_C in msg))


class TestByteIdenticalRegeneration(unittest.TestCase):
    def test_01_eight_existing_specs_regenerate_the_committed_scripts(self):
        for spec_name, gen_name in EXISTING:
            text, _ = G.build_script(G.load_spec(os.path.join(HARNESS, "specs", spec_name)))
            with open(os.path.join(ROOT, "strategies", "tests", gen_name), "rb") as f:
                committed = f.read().replace(b"\r\n", b"\n").decode("utf-8")
            self.assertEqual(text, committed, spec_name)
        print("\n  byte-identical: %d / %d existing specs" % (len(EXISTING), len(EXISTING)))

    def test_02_the_comparison_fires(self):
        s = G.load_spec(os.path.join(HARNESS, "specs", "MESA_ArticleFidelity.toml"))
        s["variants"][0]["params"] = [15, 48, 10]
        text, _ = G.build_script(s)
        with open(os.path.join(ROOT, "strategies", "tests", "GEN_MST_MESAStochastic.c"), "rb") as f:
            self.assertNotEqual(text, f.read().replace(b"\r\n", b"\n").decode("utf-8"))

    def test_03_older_specs_still_refuse_pairs(self):
        """[n, d] pairs are opt-in ([batch].real_params): an older spec refuses them exactly as before (test_generator_rff 08)."""
        s = G.load_spec(os.path.join(HARNESS, "specs", "RFF_ArticleFidelity.toml"))
        s["variants"][0]["params"] = [[48, 10]]
        self.assertIn("PARAMS_BAD", codes(s))


class TestLrsSpecAndScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = lrs()
        cls.cs = G.to_checker_spec(cls.spec)
        cls.text, cls.bodies = G.build_script(cls.spec)

    def test_01_spec_is_valid_and_lint_reports_only_stage_2_items(self):
        errs, infos = G.validate_spec(self.spec)
        self.assertEqual(errs, [])
        self.assertEqual(len([i for i in infos if i.startswith("INFO D2 floor") and "window ok" in i]), 8)
        self.assertTrue(all("NOT met" not in i and "EXCEEDS" not in i for i in infos))
        issues = G.lint_script(self.text, self.bodies, allow=G.lint_allowances(self.spec)) \
            + G.no_static_issues(G.no_static_report(self.spec))
        self.assertEqual([(r, m) for r, m in issues if not stage2_issue(r, m)], [])
        self.assertLessEqual(len(issues), 2)
        print("\n  lint: %d issue(s), all stage-2: %s" % (len(issues), [m for _, m in issues]))

    def test_02_cli_lint_only(self):
        r = subprocess.run([sys.executable, os.path.join(HARNESS, "generator.py"), S.SPEC_PATH, "--lint-only"],
                           capture_output=True, text=True, encoding="utf-8")
        refused = [l for l in r.stdout.splitlines() if l.startswith(("LINT REFUSED", "SPEC REFUSED"))]
        self.assertTrue(all(("L_INCLUDE" in l and "LaguerreRSI_Superseded.c" in l) or ("L_NO_STATIC" in l and REL_C in l)
                            for l in refused), refused)
        self.assertEqual(r.returncode, 3 if refused else 0)
        self.assertIn("INFO L_NO_STATIC %s" % REL_C, r.stdout)

    def test_03_script_counts(self):
        t = self.text
        self.assertEqual(len(re.findall(r"^\tvars S\d+ = series\(X\[\d+\], 3\);", t, re.M)), 19)
        self.assertIn("\tvar X[19];", t)
        calls = re.findall(r"^\tY\[\d+\] = \w+\(S\d+, [^;]*\);\t// \w+ \w+$", t, re.M)
        self.assertEqual(len(calls), 109)                               # 3 x 19 + 4 x 9 + 2 x 8
        self.assertEqual(len(re.findall(r"= LaguerreRSICore\(S\d+, lrs_g\d+_\d+, &lrs_o_l0, &lrs_o_l3, &lrs_o_den\);", t)), 57)
        self.assertEqual(len(re.findall(r"= lrs_n\w+\(S\d+, lrs_g1_2, &lrs_o_l0, &lrs_o_l3, &lrs_o_den\);", t)), 36)
        self.assertEqual(len(re.findall(r"= LaguerreRSI_Superseded\(S\d+, lrs_g1_2\);", t)), 16)
        self.assertIn("319 columns", t)
        self.assertIn("109 filter calls per bar", t)
        self.assertNotRegex(re.sub(r"//[^\n]*", "", t), r"\bPeriod\b")
        self.assertEqual(re.findall(r'^#include "([^"]+)"', t, re.M), self.spec["zorro"]["include"])
        self.assertEqual(len(C.header_of(self.cs)), 319)

    def test_04_real_valued_parameter_built_from_integers(self):
        t = self.text
        for n, d in ((1, 2), (7, 10), (4, 5)):
            nm = "lrs_g%d_%d" % (n, d)
            self.assertEqual(t.count("\tvar %s = %d;\t%s = %s / %d;" % (nm, n, nm, nm, d)), 1, nm)
            self.assertLess(t.index("\tvar %s = " % nm), t.index("\tvars S0 = series"))      # built before any series / call
        self.assertIn("// REALS:    real-valued parameters built at run time from integers", t)
        self.assertEqual(len(re.findall(r"LaguerreRSICore\(S\d+, lrs_g7_10,", t)), 19)
        self.assertEqual(len(re.findall(r"LaguerreRSICore\(S\d+, lrs_g4_5,", t)), 19)
        self.assertEqual(G._decimal_tokens(t), [])                                          # no decimal literal anywhere

    def test_05_four_columns_per_call_through_local_scalars(self):
        t = self.text
        self.assertNotIn("&Y[", t)
        self.assertEqual([t.count("\tvar lrs_o_%s;" % o) for o in ("l0", "l3", "den")], [1, 1, 1])
        self.assertNotIn("lrs_o_out", t)
        pat = r"&lrs_o_l0, &lrs_o_l3, &lrs_o_den\);[^\n]*\n\tY\[\d+\] = lrs_o_l0;\n\tY\[\d+\] = lrs_o_l3;\n\tY\[\d+\] = lrs_o_den;\n"
        self.assertEqual(len(re.findall(pat, t)), 93)                                        # every 4-output call, copies directly after

    def test_06_rampdn_input(self):
        t = self.text
        self.assertIn("\tX[7] = lvl + slp * n;", t)
        self.assertIn("\tX[8] = lvl - slp * n;", t)
        self.assertIn("| rampdn level-slope*n", t)
        self.assertEqual(G.input_ids(self.spec)[:9], BASE)
        self.assertEqual(C.base_names(self.cs), BASE)
        x = C.make_inputs(self.cs)
        self.assertEqual(float(x["rampdn"][2999]), 1.1 - 1e-4 * 2999)

    def parse(self):
        calls, order = {}, []
        lines = self.text.split("\n")
        call_re = re.compile(r"^\tY\[(\d+)\] = (\w+)\(S(\d+), ([\w, ]+?)((?:, &lrs_o_\w+)*)\);\t// (\w+) (\w+)$")
        i = 0
        while i < len(lines):
            m = call_re.match(lines[i])
            i += 1
            if not m:
                continue
            ret, fn, k, params, ptrs, vid, iid = m.groups()
            v = variant(self.spec, vid)
            self.assertEqual(params, ", ".join("lrs_g%d_%d" % tuple(p) for p in v["params"]), (vid, iid))
            self.assertEqual(G.input_ids(self.spec)[int(k)], iid)
            names = re.findall(r"&lrs_o_(\w+)", ptrs)
            self.assertEqual(names, v["outputs"][:-1], (vid, iid))
            for o in names:
                cm = re.match(r"^\tY\[(\d+)\] = lrs_o_%s;$" % o, lines[i])
                self.assertIsNotNone(cm, (vid, iid, o))
                calls[(o, vid, iid)] = int(cm.group(1))
                i += 1
            calls[(v["outputs"][-1], vid, iid)] = int(ret)
            order.append((fn, vid, iid))
        return calls, order

    def test_07_header_and_slots_agree_with_the_checker(self):
        calls, _ = self.parse()
        hdr_block = self.text.split("if(!lrs_hdr) {")[1].split("lrs_hdr = 1;")[0]
        names = [n for n in "".join(re.findall(r'file_append\(LRS_RAW, "([^"\\]*)", 0\);', hdr_block)).split(",") if n]
        self.assertEqual(names, C.header_of(self.cs))
        data = self.text.split("// --- write one row per fed bar ---")[1].split("if(n == LRS_NBARS - 1)")[0]
        y_after = [int(s) for s in re.findall(r"Y\[(\d+)\]", data.split("strf(\"%d,%.15f", 1)[1])]
        want = [calls[tuple(name.split("_", 2))] for name in names[2 + 19:]]
        self.assertEqual(y_after, want)
        self.assertEqual(len(set(y_after)), len(y_after))
        print("\n  header/data/slots: %d y columns in the checker's order" % len(want))

    def test_08_skip_inputs_and_the_superseded_call_order(self):
        _, order = self.parse()
        sup = [(vid, iid) for fn, vid, iid in order if fn == "LaguerreRSI_Superseded"]
        self.assertEqual(sup, [("NCS", i) for i in BASE[1:]] + [("NCT", i) for i in BASE[1:]])        # flat skipped, s5 first
        model = R.IMP_MODELS[self.spec["imp"]["must_pass"]["NCS"]]()
        self.assertEqual([(v, i) for v, i, _ in C.lrsi_shared_slots(self.cs, model)], sup)          # IMP replays the ACTUAL order
        self.assertIn("// SKIPPED:  no call, no column, no check for NCS on flat, NCT on flat", self.text)
        h = C.header_of(self.cs)
        self.assertNotIn("out_NCS_flat", h)
        self.assertNotIn("out_NCT_flat", h)
        self.assertIn("out_NCS_s5", h)
        self.assertEqual(C.skipped_pairs(self.cs), [("NCS", "flat"), ("NCT", "flat")])

    def test_09_invariance_copies_are_called_by_real_variants_only(self):
        who = {re.search(r"// (\w+) (\w+)$", l).group(1) for l in self.text.split("\n") if re.search(r"// \w+ (sc|of)\d+$", l)}
        self.assertEqual(who, set(S.REAL))

    def test_10_checker_dict_carries_the_new_keys(self):
        self.assertEqual(self.cs["osc"], dict(gate=0.01, bound=[0.0, 1.0], linear=["l0", "l3"], bound_output="out",
                                              ramp_exact={"ramp": 1.0, "rampdn": 0.0}, startup=True))
        self.assertTrue(self.cs["rampdn"])
        self.assertEqual((self.cs["tol_startup"], self.cs["tol_ramp_exact"], self.cs["tol_trace"]), (1e-6, 1e-12, 3e-5))
        g05 = [v for v in self.cs["variants"] if v["id"] == "G05"][0]
        self.assertEqual(sorted(g05["linear_tables"]), ["l0", "l3"])
        self.assertEqual(g05["linear_tables"]["l3"]["expected"][2], 10.0)
        self.assertEqual(g05["linear_tables"]["l3"]["phase_alt"], R.lrsi_alt_phase(0.5, 3))
        self.assertTrue(any(l.startswith("INFO L_NO_STATIC %s" % REL_C) for l in self.cs["info_lines"]))


class TestRefusals(unittest.TestCase):
    def test_00_unbroken_spec_is_clean(self):
        self.assertEqual(codes(lrs()), [])

    def test_01_real_params(self):
        for bad in ([[0, 2]], [[1, 2, 3]], [[1.0, 2]], [[1, -2]], [[True, 2]], [[1, 2], "x"]):
            s = lrs(); variant(s, "G05")["params"] = bad; self.assertIn("PARAMS_BAD", codes(s), bad)
        s = lrs(); del s["batch"]["real_params"]; self.assertIn("PARAMS_BAD", codes(s))           # pairs need the opt-in
        s = lrs(); s["batch"]["real_params"] = "yes"; self.assertIn("PARAMS_BAD", codes(s))
        s = lrs(); variant(s, "G05")["params"] = [[1, 2], 3]; self.assertEqual(codes(s), [])       # pair + integer: valid

    def test_02_linear_outputs_and_tables(self):
        s = lrs(); s["checks"]["linear_output"] = ["l0", "l0"]; self.assertIn("OSC_BAD", codes(s))
        s = lrs(); s["checks"]["linear_output"] = ["l0", "den"]; self.assertIn("OSC_BAD", codes(s))
        s = lrs(); s["checks"]["linear_output"] = []; self.assertIn("OSC_BAD", codes(s))
        s = lrs(); variant(s, "G05")["outputs"] = ["l0", "den", "out"]; self.assertIn("OUTPUTS_BAD", codes(s))     # real: both linear
        s = lrs(); del variant(s, "G05")["expected_outputs"]; self.assertIn("EXPECTED_OUTPUTS_BAD", codes(s))
        s = lrs(); variant(s, "G05")["expected_outputs"] = {"l0": "G05_l0"}; self.assertIn("EXPECTED_OUTPUTS_BAD", codes(s))
        s = lrs(); variant(s, "G05")["expected_outputs"]["l3"] = "G05_l9"; self.assertIn("EXPECTED_OUTPUTS_BAD", codes(s))
        s = lrs(); variant(s, "NCS")["expected_outputs"] = {"l0": "G05_l0"}; self.assertIn("EXPECTED_OUTPUTS_BAD", codes(s))
        m = G.load_spec(os.path.join(HARNESS, "specs", "MESA_ArticleFidelity.toml"))
        m["variants"][0]["expected_outputs"] = {"roof": "L14"}
        self.assertIn("EXPECTED_OUTPUTS_BAD", codes(m))                                              # single linear output

    def test_03_rampdn_ramp_exact_startup_output(self):
        s = lrs(); s["inputs"]["ramp_down"] = 1; self.assertIn("RAMPDN_BAD", codes(s))
        s = lrs(); s["inputs"]["ramp_down"] = False; self.assertIn("RAMP_EXACT_BAD", codes(s))      # rampdn key without the input
        s = lrs(); s["checks"]["ramp_exact"] = {"ramp": "1"}; self.assertIn("RAMP_EXACT_BAD", codes(s))
        s = lrs(); s["checks"]["ramp_exact"] = {"flat": 1.0}; self.assertIn("RAMP_EXACT_BAD", codes(s))
        s = lrs(); del s["tolerances"]["ramp_exact"]; self.assertIn("STRUCT", codes(s))
        s = lrs(); s["checks"]["startup_output"] = "yes"; self.assertIn("OSC_BAD", codes(s))
        s = lrs(); del s["tolerances"]["startup"]; self.assertIn("STRUCT", codes(s))
        u = G.load_spec(os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml"))
        u["checks"]["ramp_exact"] = {"ramp": 1.0}
        self.assertIn("OSC_BAD", codes(u))                                                           # needs the oscillator check set
        u = G.load_spec(os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml"))
        u["checks"]["startup_output"] = True
        self.assertIn("OSC_BAD", codes(u))

    def test_04_skip_inputs(self):
        for bad in (["s5"], ["sc5"], ["flat", "flat"], [], "flat", ["nope"]):
            s = lrs(); variant(s, "NCS")["skip_inputs"] = bad; self.assertIn("SKIP_BAD", codes(s), bad)
        s = lrs(); variant(s, "NCG")["skip_inputs"] = ["flat"]; self.assertIn("SKIP_BAD", codes(s))     # exports a linear output
        s = lrs(); variant(s, "NCS")["skip_inputs"] = ["flat", "alt"]; self.assertEqual(codes(s), [])
        u = G.load_spec(os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml"))
        u["variants"][0]["skip_inputs"] = ["flat"]
        self.assertIn("SKIP_BAD", codes(u))

    def test_05_detect_kinds(self):
        s = lrs(); s["detect"]["required"]["NCG"] = ["ramp_exact"]; self.assertEqual(codes(s), [])     # a kind the spec checks
        m = G.load_spec(os.path.join(HARNESS, "specs", "MESA_ArticleFidelity.toml"))
        m["detect"]["required"]["NCA"] = ["ramp_exact"]
        self.assertIn("DETECT_BAD_KIND", codes(m))                                                      # not checked there
        s = lrs(); s["detect"]["required"]["NCS"] = ["resid"]; self.assertIn("DETECT_BAD_KIND", codes(s))

    def test_06_lint_section(self):
        s = lrs(); s["lint"]["no_static"] = []; self.assertIn("LINT_SECTION_BAD", codes(s))
        s = lrs(); s["lint"]["no_static"] = "x.c"; self.assertIn("LINT_SECTION_BAD", codes(s))
        s = lrs(); s["lint"]["source"] = "no label"; self.assertIn("SOURCE_MISSING", codes(s))

    def test_07_lint_fires_on_a_float32_literal_in_a_control_body(self):
        s = lrs()
        v = variant(s, "NCG")
        v["body"] = v["body"].replace("var ncg_q = gamma + ncg_e;", "var ncg_q = gamma + 0.001;")
        text, bodies = G.build_script(s)
        self.assertIn("L_FLOAT32", [r for r, _ in G.lint_script(text, bodies, allow=G.lint_allowances(s))])


def git_show(rev, path):
    r = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, path)], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise AssertionError("git show %s:%s failed: %s" % (rev, path, r.stderr.strip()))
    return r.stdout


@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestNoStaticLint(unittest.TestCase):
    """Amendment 1 C: the corrected LaguerreRSI.c must contain no `static` token (comments excluded); seen to fire on the superseded body."""

    def test_01_fires_on_the_superseded_body(self):
        old = git_show(OLD_COMMIT, REL_C)
        hits = G.lint_no_static(old)
        print("\n  no-static lint on %s:%s: %s" % (OLD_COMMIT, REL_C, hits))
        self.assertEqual([n for _, n in hits], ["lr_init", "lr_prevRSI"])
        renamed = old.replace("lr_", "lro_")                                           # the stage-2 superseded copy
        self.assertEqual([n for _, n in G.lint_no_static(renamed)], ["lro_init", "lro_prevRSI"])
        with tempfile.TemporaryDirectory() as d:                                       # through the report path, on a copy
            os.makedirs(os.path.join(d, "indicators", "ehlers"))
            with open(os.path.join(d, REL_C), "w", encoding="utf-8") as f:
                f.write(old)
            rep = G.no_static_report(lrs(), root=d)
            self.assertEqual([n for _, n in rep[0][1]], ["lr_init", "lr_prevRSI"])
            self.assertEqual([r for r, _ in G.no_static_issues(rep)], ["L_NO_STATIC"])
            self.assertIn("FAIL lr_init line", G.no_static_lines(rep)[0])

    def test_02_clean_on_the_pre_registered_lines(self):
        cc = lrs()["corrected_code"]
        body = "%s\n{\n%s\n}\n%s\n{\n%s\n}\n" % (cc["function"], cc["lines"], cc["wrapper_function"], cc["wrapper_lines"])
        self.assertEqual(G.lint_no_static(body), [])
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "indicators", "ehlers"))
            with open(os.path.join(d, REL_C), "w", encoding="utf-8") as f:
                f.write("// static var lr_old;  (a comment, excluded)\n/* static int x; */\n" + body)
            rep = G.no_static_report(lrs(), root=d)
            self.assertEqual(rep, [(REL_C, [])])
            self.assertEqual(G.no_static_issues(rep), [])
            self.assertIn(": 0 static tokens (comments excluded): PASS", G.no_static_lines(rep)[0])
            rep = G.no_static_report(lrs(), root=os.path.join(d, "missing"))
            self.assertEqual(rep, [(REL_C, None)])
            self.assertEqual([r for r, _ in G.no_static_issues(rep)], ["L_NO_STATIC"])

    def test_03_comments_and_strings_excluded_tokens_not(self):
        self.assertEqual(G.lint_no_static('// static int a;\nprintf("static var b;");\nvar staticky = 1;\n'), [])
        self.assertEqual(G.lint_no_static("var f() {\n  static var q = 0;\n}"), [(2, "q")])
        self.assertEqual(G.lint_no_static("static int* p;"), [(1, "p")])

    def test_04_pre_registered_lines_follow_the_light_c_rules(self):
        cc = lrs()["corrected_code"]
        code = cc["lines"] + cc["wrapper_lines"]
        self.assertEqual(G._decimal_tokens(code), [])                                     # no decimal literal (9d.1, 9d.8)
        self.assertNotRegex(code, r"\bPeriod\b|\bPI\b|\bINITRUN\b")
        ser = [i for i, l in enumerate(cc["lines"].strip().split("\n")) if "series(" in l]
        self.assertEqual(ser, [0, 1, 2, 3, 4])                                             # the five series() calls first (3.1)


if __name__ == "__main__":
    unittest.main()
