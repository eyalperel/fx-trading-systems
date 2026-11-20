"""FSH stage 1: generator tooling for the Fisher Transform: five columns per call (raw / v1 / rng / trig by out-parameter, out returned),
no linear stage ([checks].linear_stage = false), trace on several outputs with per-output gates, one bound per output, ramp_exact per
output, the new kinds trigger / flat_zero, the spec refusals, generator / checker column parity, the superseded call order, the no-static
lint on the superseded body, the pre-registered corrected lines, and byte-identical regeneration of ALL NINE existing specs.

Rule (CLAUDE.md 4.4): each refusal / lint is seen to fire on a deliberately broken input, one defect at a time.
Stage 2 writes FisherTransform_Superseded.c and the corrected FisherTransform.c: until then lint may report ONLY the missing
FisherTransform_Superseded.c include and the two statics of the current FisherTransform.c (this test passes before and after stage 2).
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
import fsh_support as S      # noqa: E402

G, C, R = S.G, S.C, S.R
HARNESS, ROOT = S.HARNESS, S.ROOT
EXISTING = (("H1_SuperSmoother2Pole.toml", "GEN_H1_SuperSmoother2Pole.c"),
            ("SS2_ArticleFidelity.toml", "GEN_SS2F_SuperSmoother2Pole.c"),
            ("SS3_ArticleFidelity.toml", "GEN_SS3F_SuperSmoother3Pole.c"),
            ("HP_ArticleFidelity.toml", "GEN_HPF_HighPassFilter.c"),
            ("RFF_ArticleFidelity.toml", "GEN_RFF_RoofingFilter.c"),
            ("USE_ArticleFidelity.toml", "GEN_USE_UltimateSmootherE.c"),
            ("RFX_ArticleFidelity.toml", "GEN_RFX_Reflex.c"),
            ("MESA_ArticleFidelity.toml", "GEN_MST_MESAStochastic.c"),
            ("LRSI_ArticleFidelity.toml", "GEN_LRS_LaguerreRSI.c"))
OLD_COMMIT = "bdc83da"                       # the superseded FisherTransform.c (review base; blob 259954ed)
OLD_BLOB = "259954ed90f4674733f41c46b6694c5f1320cfd0"
REL_C = "indicators/ehlers/FisherTransform.c"
BASE = ["flat", "s5", "s10", "s20", "s40", "s100", "ramp", "rampdn"]
OUTS5 = ["raw", "v1", "rng", "trig", "out"]


def fsh():
    return copy.deepcopy(G.load_spec(S.SPEC_PATH))


def codes(spec):
    errs, _ = G.validate_spec(spec)
    return [c for c, _ in errs]


def variant(spec, vid):
    return [v for v in spec["variants"] if v["id"] == vid][0]


def stage2_issue(rule, msg):
    return ((rule == "L_INCLUDE" and "FisherTransform_Superseded.c" in msg)
            or (rule == "L_NO_STATIC" and REL_C in msg))


def git_show(rev, path):
    r = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, path)], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise AssertionError("git show %s:%s failed: %s" % (rev, path, r.stderr.strip()))
    return r.stdout


class TestByteIdenticalRegeneration(unittest.TestCase):
    def test_01_nine_existing_specs_regenerate_the_committed_scripts(self):
        for spec_name, gen_name in EXISTING:
            text, _ = G.build_script(G.load_spec(os.path.join(HARNESS, "specs", spec_name)))
            with open(os.path.join(ROOT, "strategies", "tests", gen_name), "rb") as f:
                committed = f.read().replace(b"\r\n", b"\n").decode("utf-8")
            self.assertEqual(text, committed, spec_name)
        print("\n  byte-identical: %d / %d existing specs" % (len(EXISTING), len(EXISTING)))

    def test_02_the_comparison_fires(self):
        s = G.load_spec(os.path.join(HARNESS, "specs", "LRSI_ArticleFidelity.toml"))
        s["inputs"]["warmup"] = 701
        text, _ = G.build_script(s)
        with open(os.path.join(ROOT, "strategies", "tests", "GEN_LRS_LaguerreRSI.c"), "rb") as f:
            committed = f.read().replace(b"\r\n", b"\n").decode("utf-8")
        s["zorro"]["series_len"] = 4
        self.assertNotEqual(G.build_script(s)[0], committed)

    def test_03_older_checker_dicts_carry_no_fsh_keys(self):
        for spec_name in ("RFX_ArticleFidelity.toml", "MESA_ArticleFidelity.toml", "LRSI_ArticleFidelity.toml"):
            cs = G.to_checker_spec(G.load_spec(os.path.join(HARNESS, "specs", spec_name)))
            self.assertFalse(set(cs["osc"]) & {"trace_outputs", "clamp_gate", "bounds", "ramp_exact_outputs", "trigger", "flat_zero"})
            self.assertNotIn("tol_trigger", cs)
            self.assertNotIn("tol_flat_zero", cs)


class TestFshSpecAndScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = fsh()
        cls.cs = G.to_checker_spec(cls.spec)
        cls.text, cls.bodies = G.build_script(cls.spec)

    def test_01_spec_is_valid_and_lint_reports_only_stage_2_items(self):
        errs, infos = G.validate_spec(self.spec)
        self.assertEqual(errs, [])
        self.assertEqual(len([i for i in infos if i.startswith("INFO D2 floor") and "window ok" in i]), 6)
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
        self.assertTrue(all(("L_INCLUDE" in l and "FisherTransform_Superseded.c" in l) or ("L_NO_STATIC" in l and REL_C in l)
                            for l in refused), refused)
        self.assertEqual(r.returncode, 3 if refused else 0)
        self.assertIn("INFO L_NO_STATIC %s" % REL_C, r.stdout)

    def test_03_script_counts(self):
        t = self.text
        self.assertEqual(len(re.findall(r"^\tvars S\d+ = series\(X\[\d+\], 21\);", t, re.M)), 18)      # series_len 21 >= Len 20
        self.assertIn("\tvar X[18];", t)
        calls = re.findall(r"^\tY\[\d+\] = \w+\(S\d+, [^;]*\);\t// \w+ \w+$", t, re.M)
        self.assertEqual(len(calls), 100)                                # 2 x 18 + 6 x 8 + 2 x 8
        self.assertEqual(len(re.findall(r"= FisherCore\(S\d+, (10|20), &fsh_o_raw, &fsh_o_v1, &fsh_o_rng, &fsh_o_trig\);", t)), 36)
        self.assertEqual(len(re.findall(r"= fsh_n\w+\(S\d+, 10, &fsh_o_raw, &fsh_o_v1, &fsh_o_rng, &fsh_o_trig\);", t)), 48)
        self.assertEqual(len(re.findall(r"= FisherTransform_Superseded\(S\d+, 10\);", t)), 16)
        self.assertIn("376 columns", t)
        self.assertIn("100 filter calls per bar", t)
        self.assertNotRegex(re.sub(r"//[^\n]*", "", t), r"\bPeriod\b")
        self.assertEqual(re.findall(r'^#include "([^"]+)"', t, re.M), self.spec["zorro"]["include"])
        self.assertEqual(len(C.header_of(self.cs)), 376)
        self.assertEqual(sum(C.n_checks(self.cs, v) for v in self.cs["variants"] if v["role"] == "real"), 56)

    def test_04_five_columns_per_call_through_local_scalars(self):
        t = self.text
        self.assertNotIn("&Y[", t)
        self.assertEqual([t.count("\tvar fsh_o_%s;" % o) for o in ("raw", "v1", "rng", "trig")], [1, 1, 1, 1])
        self.assertNotIn("fsh_o_out", t)
        pat = (r"&fsh_o_raw, &fsh_o_v1, &fsh_o_rng, &fsh_o_trig\);[^\n]*\n\tY\[\d+\] = fsh_o_raw;\n\tY\[\d+\] = fsh_o_v1;\n"
               r"\tY\[\d+\] = fsh_o_rng;\n\tY\[\d+\] = fsh_o_trig;\n")
        self.assertEqual(len(re.findall(pat, t)), 84)                     # every 5-output call, copies directly after
        self.assertEqual(G._decimal_tokens(t.replace(self.bodies[[i for i, v in enumerate(
            [v for v in self.spec["variants"] if v["kind"] == "inline"]) if v["id"] == "NC32"][0]], "")), [])   # only NC32 has literals

    def parse(self):
        calls, order = {}, []
        lines = self.text.split("\n")
        call_re = re.compile(r"^\tY\[(\d+)\] = (\w+)\(S(\d+), ([\w, ]+?)((?:, &fsh_o_\w+)*)\);\t// (\w+) (\w+)$")
        i = 0
        while i < len(lines):
            m = call_re.match(lines[i])
            i += 1
            if not m:
                continue
            ret, fn, k, params, ptrs, vid, iid = m.groups()
            v = variant(self.spec, vid)
            self.assertEqual(params, ", ".join(str(p) for p in v["params"]), (vid, iid))
            self.assertEqual(G.input_ids(self.spec)[int(k)], iid)
            names = re.findall(r"&fsh_o_(\w+)", ptrs)
            self.assertEqual(names, v["outputs"][:-1], (vid, iid))
            for o in names:
                cm = re.match(r"^\tY\[(\d+)\] = fsh_o_%s;$" % o, lines[i])
                self.assertIsNotNone(cm, (vid, iid, o))
                calls[(o, vid, iid)] = int(cm.group(1))
                i += 1
            calls[(v["outputs"][-1], vid, iid)] = int(ret)
            order.append((fn, vid, iid))
        return calls, order

    def test_05_header_and_slots_agree_with_the_checker(self):
        calls, _ = self.parse()
        hdr_block = self.text.split("if(!fsh_hdr) {")[1].split("fsh_hdr = 1;")[0]
        names = [n for n in "".join(re.findall(r'file_append\(FSH_RAW, "([^"\\]*)", 0\);', hdr_block)).split(",") if n]
        self.assertEqual(names, C.header_of(self.cs))
        data = self.text.split("// --- write one row per fed bar ---")[1].split("if(n == FSH_NBARS - 1)")[0]
        y_after = [int(s) for s in re.findall(r"Y\[(\d+)\]", data.split("strf(\"%d,%.15f", 1)[1])]
        want = [calls[tuple(name.split("_", 2))] for name in names[2 + 18:]]
        self.assertEqual(y_after, want)
        self.assertEqual(len(set(y_after)), len(y_after))
        print("\n  header/data/slots: %d y columns in the checker's order" % len(want))

    def test_06_superseded_call_order_is_what_imp_replays(self):
        _, order = self.parse()
        sup = [(vid, iid) for fn, vid, iid in order if fn == "FisherTransform_Superseded"]
        self.assertEqual(sup, [("NCS", i) for i in BASE] + [("NCT", i) for i in BASE])
        model = R.IMP_MODELS[self.spec["imp"]["must_pass"]["NCS"]]()
        self.assertEqual([(v, i) for v, i, _ in C.fisher_shared_slots(self.cs, model)], sup)
        self.assertNotIn("// SKIPPED:", self.text)

    def test_07_invariance_copies_are_called_by_real_variants_only(self):
        who = {re.search(r"// (\w+) (\w+)$", l).group(1) for l in self.text.split("\n") if re.search(r"// \w+ (sc|of)\d+$", l)}
        self.assertEqual(who, set(S.REAL))

    def test_08_checker_dict_carries_the_new_keys(self):
        o = self.cs["osc"]
        self.assertIsNone(o["linear"])
        self.assertIsNone(o["bound"])
        self.assertEqual(o["trace_outputs"], {"raw": ["range"], "v1": ["range", "clamp"], "out": ["range", "clamp"]})
        self.assertEqual(o["clamp_gate"], 1e-6)
        self.assertEqual(o["bounds"], {"raw": [-1.0, 1.0], "v1": [-0.999, 0.999], "out": R.FISHER_LN1999})
        self.assertEqual(o["ramp_exact_outputs"]["out"], {"ramp": "model", "rampdn": "model"})
        self.assertTrue(o["trigger"])
        self.assertEqual(o["flat_zero"], ["raw", "v1", "out"])
        self.assertEqual((self.cs["tol_trace"], self.cs["tol_trigger"], self.cs["tol_flat_zero"]), (1e-9, 0.0, 1e-12))
        self.assertIsNone(self.cs["tol_gain"])
        self.assertIsNone(self.cs["tol_flat"])
        self.assertEqual([v["expected"] for v in self.cs["variants"]][0], (None, [], None))
        self.assertTrue(any(l.startswith("INFO L_NO_STATIC %s" % REL_C) for l in self.cs["info_lines"]))


class TestRefusals(unittest.TestCase):
    def test_00_unbroken_spec_is_clean(self):
        self.assertEqual(codes(fsh()), [])

    def test_01_linear_stage(self):
        s = fsh(); s["checks"]["linear_stage"] = "no"; self.assertIn("LINEAR_STAGE_BAD", codes(s))
        s = fsh(); s["checks"]["linear_output"] = "raw"; self.assertIn("OSC_BAD", codes(s))
        s = fsh(); del s["checks"]["linear_stage"]; self.assertIn("OSC_BAD", codes(s))       # then a linear output is required
        s = fsh(); s["tolerances"]["gain"] = dict(value=3e-5, source="(c) x"); self.assertIn("LINEAR_NOT_APPLICABLE", codes(s))
        s = fsh(); s["expected"]["FR10"]["gains"] = [1, 1, 1, 1, 1]; self.assertIn("LINEAR_NOT_APPLICABLE", codes(s))
        s = fsh(); s["expected"]["FR10"]["article"] = "fisher_article(0)"; self.assertIn("ARTICLE_MODEL", codes(s))
        m = G.load_spec(os.path.join(HARNESS, "specs", "MESA_ArticleFidelity.toml"))
        del m["checks"]["linear_output"]
        self.assertIn("OSC_BAD", codes(m))                                                    # older specs: still required

    def test_02_trace_outputs_and_clamp_gate(self):
        for bad in ({}, {"raw": []}, {"raw": ["clamp"]}, {"raw": ["range", "range"]}, {"nope": ["range"]}, {"raw": ["range", "x"]},
                    ["raw"]):
            s = fsh(); s["checks"]["trace_outputs"] = bad; self.assertIn("TRACE_OUTPUTS_BAD", codes(s), bad)
        s = fsh(); del s["checks"]["clamp_gate"]; self.assertIn("TRACE_OUTPUTS_BAD", codes(s))
        s = fsh(); s["checks"]["clamp_gate"] = 0; self.assertIn("TRACE_OUTPUTS_BAD", codes(s))
        s = fsh(); s["checks"]["trace_outputs"] = {"raw": ["range"], "v1": ["range"], "out": ["range"]}
        self.assertIn("TRACE_OUTPUTS_BAD", codes(s))                                            # clamp_gate given, never used
        s = fsh(); del s["checks"]["clamp_gate"]; s["checks"]["trace_outputs"] = {"out": ["range"]}
        self.assertEqual(codes(s), [])

    def test_03_bounds(self):
        for bad in ({}, {"raw": [1.0, -1.0]}, {"raw": [-1.0]}, {"out": -1.0}, {"out": "7.6"}, {"nope": 1.0}):
            s = fsh(); s["checks"]["bounds"] = bad; self.assertIn("BOUNDS_BAD", codes(s), bad)
        s = fsh(); s["checks"]["bound"] = 7.6; self.assertIn("OSC_BAD", codes(s))              # exclusive with bounds
        s = fsh(); del s["checks"]["bounds"]; self.assertIn("OSC_BAD", codes(s))               # one of the two is needed

    def test_04_ramp_exact_outputs_trigger_flat_zero(self):
        for bad in ({}, {"raw": {}}, {"raw": {"flat": 0.0}}, {"out": {"ramp": "Model"}}, {"nope": {"ramp": 1.0}}):
            s = fsh(); s["checks"]["ramp_exact_outputs"] = bad; self.assertIn("RAMP_EXACT_BAD", codes(s), bad)
        s = fsh(); s["checks"]["ramp_exact"] = {"ramp": 1.0}; self.assertIn("RAMP_EXACT_BAD", codes(s))
        s = fsh(); s["checks"]["trigger"] = 1; self.assertIn("TRIGGER_BAD", codes(s))
        s = fsh(); del s["tolerances"]["trigger"]; self.assertIn("STRUCT", codes(s))
        for bad in ([], ["raw", "raw"], "raw", ["nope"]):
            s = fsh(); s["checks"]["flat_zero"] = bad; self.assertIn("FLAT_ZERO_BAD", codes(s), bad)
        s = fsh(); del s["tolerances"]["flat_zero"]; self.assertIn("STRUCT", codes(s))
        u = G.load_spec(os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml"))
        u["checks"]["trigger"] = True
        self.assertIn("OSC_BAD", codes(u))                                                     # needs the oscillator check set

    def test_05_real_variant_must_export_every_checked_output(self):
        s = fsh(); variant(s, "FR10")["outputs"] = ["raw", "rng", "trig", "out"]; self.assertIn("OUTPUTS_BAD", codes(s))
        s = fsh(); variant(s, "FR10")["outputs"] = ["raw", "v1", "rng", "out"]; self.assertIn("OUTPUTS_BAD", codes(s))   # trig
        s = fsh(); variant(s, "NCS")["outputs"] = ["out"]; self.assertEqual(codes(s), [])          # a control may export less

    def test_06_detect_kinds(self):
        s = fsh(); s["detect"]["required"]["NCW"] = ["trigger"]; self.assertEqual(codes(s), [])
        s = fsh(); s["detect"]["required"]["NCW"] = ["gain"]; self.assertIn("DETECT_BAD_KIND", codes(s))   # no linear stage
        m = G.load_spec(os.path.join(HARNESS, "specs", "LRSI_ArticleFidelity.toml"))
        m["detect"]["required"]["NCG"] = ["flat_zero"]
        self.assertIn("DETECT_BAD_KIND", codes(m))                                                # not checked there

    def test_07_float32_exemption_is_scoped_to_nc32(self):
        s = fsh(); del variant(s, "NC32")["lint_allow_float32"]; del variant(s, "NC32")["lint_allow_reason"]
        text, bodies = G.build_script(s)
        self.assertIn("L_FLOAT32", [r for r, _ in G.lint_script(text, bodies, allow=G.lint_allowances(s))])
        s = fsh(); v = variant(s, "NCW")
        v["body"] = v["body"].replace("var ncw_a = 331;  ncw_a = ncw_a/1000;", "var ncw_a = 0.331;")
        text, bodies = G.build_script(s)
        self.assertIn("L_FLOAT32", [r for r, _ in G.lint_script(text, bodies, allow=G.lint_allowances(s))])


@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestNoStaticLint(unittest.TestCase):
    """F-1: the corrected FisherTransform.c must contain no `static` token (comments excluded); seen to fire on the superseded body."""

    def test_01_fires_on_the_superseded_body(self):
        r = subprocess.run(["git", "-C", ROOT, "rev-parse", "%s:%s" % (OLD_COMMIT, REL_C)], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), OLD_BLOB)
        old = git_show(OLD_COMMIT, REL_C)
        hits = G.lint_no_static(old)
        print("\n  no-static lint on %s:%s: %s" % (OLD_COMMIT, REL_C, hits))
        self.assertEqual([n for _, n in hits], ["ft_Value1", "ft_Fish"])
        renamed = old.replace("ft_", "fto_")                                           # the stage-2 superseded copy
        self.assertEqual([n for _, n in G.lint_no_static(renamed)], ["fto_Value1", "fto_Fish"])
        self.assertIn("var ft_Trigger = 0;", old)                                      # (c) a non-static global: NOT seen by this lint
        self.assertNotIn("ft_Trigger", [n for _, n in hits])
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "indicators", "ehlers"))
            with open(os.path.join(d, REL_C), "w", encoding="utf-8") as f:
                f.write(old)
            rep = G.no_static_report(fsh(), root=d)
            self.assertEqual([n for _, n in rep[0][1]], ["ft_Value1", "ft_Fish"])
            self.assertEqual([r_ for r_, _ in G.no_static_issues(rep)], ["L_NO_STATIC"])

    def test_02_clean_on_the_pre_registered_lines(self):
        cc = fsh()["corrected_code"]
        body = "%s\n{\n%s\n}\n%s\n{\n%s\n}\n" % (cc["function"], cc["lines"], cc["wrapper_function"], cc["wrapper_lines"])
        self.assertEqual(G.lint_no_static(body), [])

    def test_03_pre_registered_lines_follow_the_light_c_rules(self):
        cc = fsh()["corrected_code"]
        code = cc["lines"] + cc["wrapper_lines"]
        self.assertEqual(G._decimal_tokens(code), [])                                     # no decimal literal (9d.1, 9d.8)
        self.assertNotRegex(code, r"\bPeriod\b|\bPI\b|\bINITRUN\b|\bstatic\b")
        ln = cc["lines"].strip().split("\n")
        self.assertEqual([i for i, l in enumerate(ln) if "series(" in l], [0, 1])           # both series() calls first (3.1)
        for l in ln:                                                                         # 9d.8: no expression starts with a literal
            for rhs in re.findall(r"=\s*([^;]+);", l):                                       #       product / quotient
                self.assertNotRegex(rhs.strip(), r"^\d+\s*[*/]", l)
        self.assertIn("fi_raw = fi_raw*2;", code)

    def test_04_pre_registered_lines_are_the_briefs(self):
        """The spec's [corrected_code] is the brief's code block verbatim (whitespace-normalised)."""
        with open(os.path.join(ROOT, "docs", "harness", "FISHER_STAGE1_PROMPT.md"), encoding="utf-8") as f:
            brief = f.read()
        block = re.search(r"```c\n(.*?)```", brief, re.S).group(1)
        cc = fsh()["corrected_code"]
        mine = "%s\n{\n%s\n}\n\n%s\n{\n%s\n}\n" % (cc["function"], cc["lines"].strip("\n"), cc["wrapper_function"],
                                                    cc["wrapper_lines"].strip("\n"))
        norm = lambda t: re.sub(r"\s+", " ", t).strip()
        self.assertEqual(norm(mine), norm(block))


if __name__ == "__main__":
    unittest.main()
