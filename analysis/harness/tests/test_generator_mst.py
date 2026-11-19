"""MST stage 1: generator tooling for MESAStochastic: three-output calls (roof / stoc out-parameters, `out` returned), three-parameter
variants, the two-sided bound keys ([checks].bound = [lo, hi] + bound_output), `startup_info`, the spec refusals, lint of the MST spec,
generator / checker column parity, and byte-identical regeneration of ALL SEVEN existing specs (H1, SS2F, SS3F, HPF, RFF, USE, RFX).

Rule (CLAUDE.md 4.4): each refusal is seen to fire on a deliberately broken spec, one defect at a time.
Stage 2 writes MESAStochastic_Superseded.c and the corrected MESAStochastic.c: until then lint may report ONLY the missing
MESAStochastic_Superseded.c include (this test passes before and after stage 2). No Zorro run.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mst_support as S      # noqa: E402

G, C = S.G, S.C
HARNESS, ROOT = S.HARNESS, S.ROOT
EXISTING = (("H1_SuperSmoother2Pole.toml", "GEN_H1_SuperSmoother2Pole.c"),
            ("SS2_ArticleFidelity.toml", "GEN_SS2F_SuperSmoother2Pole.c"),
            ("SS3_ArticleFidelity.toml", "GEN_SS3F_SuperSmoother3Pole.c"),
            ("HP_ArticleFidelity.toml", "GEN_HPF_HighPassFilter.c"),
            ("RFF_ArticleFidelity.toml", "GEN_RFF_RoofingFilter.c"),
            ("USE_ArticleFidelity.toml", "GEN_USE_UltimateSmootherE.c"),
            ("RFX_ArticleFidelity.toml", "GEN_RFX_Reflex.c"))


def mst():
    return copy.deepcopy(G.load_spec(S.SPEC_PATH))


def codes(spec):
    errs, _ = G.validate_spec(spec)
    return [c for c, _ in errs]


def variant(spec, vid):
    return [v for v in spec["variants"] if v["id"] == vid][0]


class TestByteIdenticalRegeneration(unittest.TestCase):
    def test_01_seven_existing_specs_regenerate_the_committed_scripts(self):
        for spec_name, gen_name in EXISTING:
            text, _ = G.build_script(G.load_spec(os.path.join(HARNESS, "specs", spec_name)))
            with open(os.path.join(ROOT, "strategies", "tests", gen_name), "rb") as f:
                committed = f.read().replace(b"\r\n", b"\n").decode("utf-8")
            self.assertEqual(text, committed, spec_name)
        print("\n  byte-identical: %d / %d existing specs" % (len(EXISTING), len(EXISTING)))

    def test_02_the_comparison_fires(self):
        s = G.load_spec(os.path.join(HARNESS, "specs", "RFX_ArticleFidelity.toml"))
        s["variants"][0]["params"] = [15]
        text, _ = G.build_script(s)
        with open(os.path.join(ROOT, "strategies", "tests", "GEN_RFX_Reflex.c"), "rb") as f:
            self.assertNotEqual(text, f.read().replace(b"\r\n", b"\n").decode("utf-8"))


class TestMstSpecAndScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = mst()
        cls.cs = G.to_checker_spec(cls.spec)
        cls.text, cls.bodies = G.build_script(cls.spec)

    def test_01_spec_is_valid_and_lint_reports_only_the_stage_2_include(self):
        errs, infos = G.validate_spec(self.spec)
        self.assertEqual(errs, [])
        self.assertTrue(any("D2 floor trace" in i and "window ok" in i for i in infos))
        self.assertTrue(all("NOT met" not in i and "EXCEEDS" not in i for i in infos))
        issues = G.lint_script(self.text, self.bodies, allow=G.lint_allowances(self.spec))
        other = [(r, m) for r, m in issues if not (r == "L_INCLUDE" and "MESAStochastic_Superseded.c" in m)]
        self.assertEqual(other, [])
        self.assertLessEqual(len(issues), 1)
        print("\n  lint: %d issue(s) (stage-2 include: %s)" % (len(issues), [m for _, m in issues]))

    def test_02_script_counts(self):
        t = self.text
        self.assertEqual(len(re.findall(r"^\tvars S\d+ = series\(X\[\d+\], 3\);", t, re.M)), 18)
        self.assertIn("\tvar X[18];", t)
        self.assertIn("\tvar Y[368];", t)
        calls = re.findall(r"^\tY\[\d+\] = \w+\(S\d+, [^;]*\);\t// \w+ \w+$", t, re.M)
        self.assertEqual(len(calls), 128)
        self.assertEqual(len(re.findall(r"= MESAStochasticCore\(S\d+, \d+, \d+, \d+, &mst_o_roof, &mst_o_stoc\);", t)), 88)  # 4 x 18 + NCP, NC1 x 8
        self.assertEqual(len(re.findall(r"= MESAStochastic_Superseded\(S\d+, 20, 48, 10\);", t)), 8)
        self.assertEqual(len(re.findall(r"= mst_n\w+\(S\d+, 20, 48, 10, &mst_o_roof, &mst_o_stoc\);", t)), 32)            # 4 inline x 8
        self.assertEqual(len(re.findall(r"= MESAStochasticCore\(S\d+, 20, 40, 10,", t)), 8)                               # NCP
        self.assertEqual(len(re.findall(r"= MESAStochasticCore\(S\d+, 20, 48, 20,", t)), 18)                              # S20
        self.assertIn("308 columns", t)
        self.assertIn("128 filter calls per bar", t)
        self.assertNotRegex(re.sub(r"//[^\n]*", "", t), r"\bPeriod\b")
        incs = re.findall(r'^#include "([^"]+)"', t, re.M)
        self.assertEqual(incs, self.spec["zorro"]["include"])

    def test_03_out_parameters_go_through_two_local_scalars(self):
        t = self.text
        self.assertNotIn("&Y[", t)
        self.assertEqual((t.count("\tvar mst_o_roof;"), t.count("\tvar mst_o_stoc;")), (1, 1))
        self.assertNotIn("mst_o_out", t)                                                   # out is the return value
        pat = r"&mst_o_roof, &mst_o_stoc\);[^\n]*\n\tY\[\d+\] = mst_o_roof;\n\tY\[\d+\] = mst_o_stoc;\n"
        self.assertEqual(len(re.findall(pat, t)), 120)                                     # every 3-output call, copies directly after

    def parse(self):
        calls = {}
        lines = self.text.split("\n")
        call_re = re.compile(r"^\tY\[(\d+)\] = (\w+)\(S(\d+), ([\d, ]+?)((?:, &mst_o_\w+)*)\);\t// (\w+) (\w+)$")
        i = 0
        while i < len(lines):
            m = call_re.match(lines[i])
            i += 1
            if not m:
                continue
            ret, fn, k, params, ptrs, vid, iid = m.groups()
            v = variant(self.spec, vid)
            self.assertEqual([int(p) for p in params.split(", ")], v["params"], (vid, iid))
            names = re.findall(r"&mst_o_(\w+)", ptrs)
            self.assertEqual(names, v["outputs"][:-1], (vid, iid))
            for o in names:
                cm = re.match(r"^\tY\[(\d+)\] = mst_o_%s;$" % o, lines[i])
                self.assertIsNotNone(cm, (vid, iid, o))
                calls[(o, vid, iid)] = int(cm.group(1))
                i += 1
            calls[(v["outputs"][-1], vid, iid)] = int(ret)
        return calls

    def test_04_header_and_slots_agree_with_the_checker(self):
        calls = self.parse()
        hdr_block = self.text.split("if(!mst_hdr) {")[1].split("mst_hdr = 1;")[0]
        names = [n for n in "".join(re.findall(r'file_append\(MST_RAW, "([^"\\]*)", 0\);', hdr_block)).split(",") if n]
        self.assertEqual(names, C.header_of(self.cs))
        data = self.text.split("// --- write one row per fed bar ---")[1].split("if(n == MST_NBARS - 1)")[0]
        y_after = [int(s) for s in re.findall(r"Y\[(\d+)\]", data.split("strf(\"%d,%.15f", 1)[1])]
        want = [calls[tuple(name.split("_", 2))] for name in names[2 + 18:]]
        self.assertEqual(y_after, want)
        self.assertEqual(len(set(y_after)), len(y_after))
        print("\n  header/data/slots: %d y columns in the checker's order" % len(want))

    def test_05_invariance_copies_are_called_by_real_variants_only(self):
        who = {re.search(r"// (\w+) (\w+)$", l).group(1) for l in self.text.split("\n")
               if re.search(r"// \w+ (sc|of)\d+$", l)}
        self.assertEqual(who, set(S.REAL))

    def test_06_checker_dict_carries_the_new_keys(self):
        self.assertEqual(self.cs["osc"], dict(gate=0.01, bound=[0.0, 1.0], linear="roof", bound_output="stoc"))
        self.assertEqual([v["id"] for v in self.cs["variants"] if v.get("startup_info")], ["NCZ"])
        self.assertEqual(self.cs["tol_trace"], 5e-5)
        self.assertEqual(self.cs["tol_bound"], 1e-12)


class TestRefusals(unittest.TestCase):
    def test_00_unbroken_spec_is_clean(self):
        self.assertEqual(codes(mst()), [])

    def test_01_outputs_end_in_one_return_name(self):
        s = mst(); variant(s, "L20")["outputs"] = ["roof", "out", "stoc"]; self.assertIn("OUTPUTS_BAD", codes(s))
        s = mst(); variant(s, "L20")["outputs"] = ["roof", "r", "out"]; self.assertIn("OUTPUTS_BAD", codes(s))    # two return names
        s = mst(); variant(s, "L20")["outputs"] = ["roof", "stoc", "foo"]; self.assertIn("OUTPUTS_BAD", codes(s))
        s = mst(); variant(s, "L20")["outputs"] = ["stoc", "out"]; self.assertIn("OUTPUTS_BAD", codes(s))         # real: must export roof

    def test_02_two_sided_bound(self):
        s = mst(); s["checks"]["bound"] = [1.0, 0.0]; self.assertIn("OSC_BAD", codes(s))
        s = mst(); s["checks"]["bound"] = [0.0, 0.5, 1.0]; self.assertIn("OSC_BAD", codes(s))
        s = mst(); s["checks"]["bound"] = [0.0, "1"]; self.assertIn("OSC_BAD", codes(s))
        s = mst(); del s["checks"]["bound_output"]; self.assertIn("OSC_BAD", codes(s))
        s = mst(); s["checks"]["bound_output"] = "roof"; self.assertIn("OSC_BAD", codes(s))            # linear output
        s = mst(); s["checks"]["bound_output"] = "hh"; self.assertIn("OSC_BAD", codes(s))
        s = mst(); s["checks"]["bound"] = 1.0; self.assertIn("OSC_BAD", codes(s))                      # bound_output needs a pair
        s = mst(); s["checks"]["bound"] = -1.0; del s["checks"]["bound_output"]; self.assertIn("OSC_BAD", codes(s))
        s = mst(); s["checks"]["bound"] = 1.0; del s["checks"]["bound_output"]; self.assertEqual(codes(s), [])   # Reflex form still valid

    def test_03_linear_output(self):
        s = mst(); s["checks"]["linear_output"] = "out"; self.assertIn("OSC_BAD", codes(s))
        s = mst(); s["checks"]["linear_output"] = "stoc"; self.assertIn("OSC_BAD", codes(s))

    def test_04_startup_info(self):
        s = mst(); variant(s, "NCZ")["startup_info"] = "yes"; self.assertIn("OSC_BAD", codes(s))
        u = G.load_spec(os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml"))
        u["variants"][0]["startup_info"] = True
        self.assertIn("OSC_BAD", codes(u))
        u = G.load_spec(os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml"))
        u["checks"]["bound_output"] = "stoc"
        self.assertIn("OSC_BAD", codes(u))

    def test_05_article_model_must_be_an_oscillator_model(self):
        s = mst(); s["expected"]["L20"]["article"] = "mesa_article(20,48)"; self.assertIn("ARTICLE_MODEL", codes(s))
        s = mst(); s["expected"]["L20"]["article"] = "mesa_article(0,48,10)"; self.assertIn("ARTICLE_MODEL", codes(s))
        s = mst(); s["expected"]["L20"]["article"] = "mesa_code(20,48,10)"; self.assertIn("ARTICLE_MODEL", codes(s))

    def test_06_three_params_are_integers(self):
        s = mst(); variant(s, "L20")["params"] = [20, 48.0, 10]; self.assertIn("PARAMS_BAD", codes(s))
        s = mst(); variant(s, "L20")["params"] = []; self.assertIn("PARAMS_BAD", codes(s))

    def test_07_lint_fires_on_a_float32_literal_in_a_control_body(self):
        s = mst()
        v = variant(s, "NCA")
        v["body"] = v["body"].replace("nca_a1 = nca_a1 + nca_e;", "nca_a1 = nca_a1 + 0.001;")
        text, bodies = G.build_script(s)
        self.assertIn("L_FLOAT32", [r for r, _ in G.lint_script(text, bodies, allow=G.lint_allowances(s))])


if __name__ == "__main__":
    unittest.main()
