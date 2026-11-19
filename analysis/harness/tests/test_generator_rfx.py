"""RFX stage 1: generator tooling for the oscillator family (D6): multi-output calls (`outputs`, out-parameters), invariance copies,
the spec refusals, lint of the RFX spec, generator / checker column and call-order parity, byte-identical regeneration of ALL SIX
existing specs (H1, SS2F, SS3F, HPF, RFF, USE).

Rule (CLAUDE.md 4.4): each refusal is seen to fire on a deliberately broken spec, one defect at a time.
The two stage-2 includes (Reflex_Superseded.c, corrected Reflex.c) may not exist yet: lint is allowed to report ONLY a missing
Reflex_Superseded.c (this test passes before and after stage 2). No Zorro run. Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rfx_support as S      # noqa: E402

G, C = S.G, S.C
HARNESS = S.HARNESS
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
EXISTING = (("H1_SuperSmoother2Pole.toml", "GEN_H1_SuperSmoother2Pole.c"),
            ("SS2_ArticleFidelity.toml", "GEN_SS2F_SuperSmoother2Pole.c"),
            ("SS3_ArticleFidelity.toml", "GEN_SS3F_SuperSmoother3Pole.c"),
            ("HP_ArticleFidelity.toml", "GEN_HPF_HighPassFilter.c"),
            ("RFF_ArticleFidelity.toml", "GEN_RFF_RoofingFilter.c"),
            ("USE_ArticleFidelity.toml", "GEN_USE_UltimateSmootherE.c"))


def rfx():
    return copy.deepcopy(G.load_spec(S.SPEC_PATH))


def codes(spec):
    errs, _ = G.validate_spec(spec)
    return [c for c, _ in errs]


def variant(spec, vid):
    return [v for v in spec["variants"] if v["id"] == vid][0]


class TestByteIdenticalRegeneration(unittest.TestCase):
    def test_01_six_existing_specs_regenerate_the_committed_scripts(self):
        for spec_name, gen_name in EXISTING:
            text, _ = G.build_script(G.load_spec(os.path.join(HARNESS, "specs", spec_name)))
            with open(os.path.join(ROOT, "strategies", "tests", gen_name), "rb") as f:
                committed = f.read().replace(b"\r\n", b"\n").decode("utf-8")
            self.assertEqual(text, committed, spec_name)


class TestRfxSpecAndScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = rfx()
        cls.cs = G.to_checker_spec(cls.spec)
        cls.text, cls.bodies = G.build_script(cls.spec)

    def test_01_spec_is_valid_and_lint_reports_only_the_stage_2_include(self):
        errs, infos = G.validate_spec(self.spec)
        self.assertEqual(errs, [])
        self.assertTrue(any("D2 floor trace" in i and "window ok" in i for i in infos))
        self.assertTrue(all("NOT met" not in i for i in infos))
        issues = G.lint_script(self.text, self.bodies, allow=G.lint_allowances(self.spec))
        stage2 = [m for r, m in issues if r == "L_INCLUDE" and "Reflex_Superseded.c" in m]
        self.assertEqual(issues, [])                       # stage 2: the three includes resolve, nothing else to report
        print("\n  lint: %d issue(s)" % len(issues))

    def test_02_script_counts(self):
        t = self.text
        self.assertEqual(len(re.findall(r"^\tvars S\d+ = series\(X\[\d+\], 3\);", t, re.M)), 18)
        self.assertIn("\tvar X[18];", t)
        self.assertIn("\tvar Y[400];", t)
        calls = re.findall(r"^\tY\[\d+\] = \w+\(S\d+, [^;]*\);\t// \w+ \w+$", t, re.M)
        self.assertEqual(len(calls), 144)
        self.assertEqual(len(re.findall(r"= ReflexCore\(S\d+, \d+, &rfx_o_sum, &rfx_o_ms\);", t)), 80)       # 4 real x 18 inputs + NC1 x 8
        self.assertEqual(len(re.findall(r"= Reflex_Superseded\(S\d+, \d+\);", t)), 16)
        self.assertEqual(len(re.findall(r"= rfx_\w+\(S\d+, \d+, &rfx_o_sum, &rfx_o_ms\);", t)), 48)           # 6 inline x 8 base inputs
        self.assertIn("340 columns", t)
        self.assertIn("144 filter calls per bar", t)
        self.assertNotRegex(G._strip(self.text.split("void run()")[1]), r"\bPI\b")
        self.assertNotRegex(re.sub(r"//[^\n]*", "", t), r"\bPeriod\b")        # reserved word (gotchas); BarPeriod is fine

    def test_03_copy_inputs_are_built_from_integers(self):
        t = self.text
        self.assertIn("\tvar lvl_sc = 11;\tlvl_sc = lvl_sc / 10;", t)
        self.assertIn("\tvar amp_sc = 1;\tamp_sc = amp_sc / 10;", t)
        self.assertIn("\tvar lvl_of = 22;\tlvl_of = lvl_of / 10;", t)
        self.assertIn("\tvar amp_of = 1;\tamp_of = amp_of / 100;", t)
        self.assertIn("\tX[8] = lvl_sc + amp_sc * sin(2 * pi_x * n / 5);", t)
        self.assertIn("\tX[17] = lvl_of + amp_of * sin(2 * pi_x * n / 100);", t)
        self.assertIn("\tX[7] = lvl + slp * n;", t)

    def parse(self):
        """Calls and their out-parameter copies: `Y[r] = fn(S, params, &rfx_o_sum, &rfx_o_ms);` is followed by one
        `Y[s] = rfx_o_<out>;` line per out-parameter, in the listed output order."""
        calls = {}
        order = []
        lines = self.text.split("\n")
        call_re = re.compile(r"^\tY\[(\d+)\] = (\w+)\(S(\d+), ([\d, ]+?)((?:, &rfx_o_\w+)*)\);\t// (\w+) (\w+)$")
        i = 0
        while i < len(lines):
            m = call_re.match(lines[i])
            i += 1
            if not m:
                continue
            ret, fn, k, params, ptrs, vid, iid = m.groups()
            outs = [v for v in self.spec["variants"] if v["id"] == vid][0]["outputs"]
            names = re.findall(r"&rfx_o_(\w+)", ptrs)
            self.assertEqual(names, outs[:-1], (vid, iid))
            for o in names:
                cm = re.match(r"^\tY\[(\d+)\] = rfx_o_%s;$" % o, lines[i])
                self.assertIsNotNone(cm, (vid, iid, o, lines[i]))          # copied BEFORE the next call
                calls[(o, vid, iid)] = int(cm.group(1))
                i += 1
            calls[(outs[-1], vid, iid)] = int(ret)
            order.append((fn, vid, iid, int(k)))
        return calls, order

    def test_03b_out_parameters_go_through_two_local_scalars(self):
        """Decided 2026-11-18 (stage 2): the proven `&scalar` form, never `&Y[k]` (gotchas 7)."""
        t = self.text
        self.assertNotIn("&Y[", t)
        self.assertEqual(t.count("\tvar rfx_o_sum;"), 1)
        self.assertEqual(t.count("\tvar rfx_o_ms;"), 1)
        self.assertLess(t.index("\tvar rfx_o_ms;"), t.index("ReflexCore(S0"))             # declared once, before the first call
        self.assertEqual(len(re.findall(r"&rfx_o_sum, &rfx_o_ms\);", t)), 128)               # 80 ReflexCore + 48 inline
        self.assertEqual(len(re.findall(r"^\tY\[\d+\] = rfx_o_sum;$", t, re.M)), 128)
        self.assertEqual(len(re.findall(r"^\tY\[\d+\] = rfx_o_ms;$", t, re.M)), 128)
        # every call line is directly followed by its two copies (the locals are reused by the next call)
        pat = r"&rfx_o_sum, &rfx_o_ms\);[^\n]*\n\tY\[\d+\] = rfx_o_sum;\n\tY\[\d+\] = rfx_o_ms;\n"
        self.assertEqual(len(re.findall(pat, t)), 128)

    def test_04_header_and_slots_agree_with_the_checker(self):
        calls, _ = self.parse()
        hdr_block = self.text.split("if(!rfx_hdr) {")[1].split("rfx_hdr = 1;")[0]
        names = "".join(re.findall(r'file_append\(RFX_RAW, "([^"\\]*)", 0\);', hdr_block)).split(",")
        names = [n for n in names if n]
        self.assertEqual(names, C.header_of(self.cs))
        data = self.text.split("// --- write one row per fed bar ---")[1].split("if(n == RFX_NBARS - 1)")[0]
        y_after = [int(s) for s in re.findall(r"Y\[(\d+)\]", data.split("strf(\"%d,%.15f", 1)[1])]
        ycols = names[2 + 18:]
        want = []
        for name in ycols:
            o, vid, iid = name.split("_", 2)
            want.append(calls[(o, vid, iid)])
        self.assertEqual(y_after, want)
        self.assertEqual(len(set(y_after)), len(y_after))
        # every header line stays short (Light-C string literals): at most 9 names per append
        self.assertLessEqual(max(len(re.findall(r"[^,]+", s)) for s in re.findall(r'file_append\(RFX_RAW, "([^"]*)", 0\);', hdr_block)), 20)
        print("\n  header/data/slots: %d y columns, one slot each, in the checker's order" % len(ycols))

    def test_05_shared_state_call_order_is_the_replay_order(self):
        """The old file's static MS is shared in CALL order: NCS (L20) on the 8 base inputs, then NCT (L14), nothing else between."""
        _, order = self.parse()
        sup = [(vid, iid) for fn, vid, iid, k in order if fn == "Reflex_Superseded"]
        ids = C.base_names(self.cs)
        self.assertEqual(sup, [("NCS", i) for i in ids] + [("NCT", i) for i in ids])
        # the replay's slot list is built the same way (rfx_support: variant-major, variant_inputs order)
        want = [(v["id"], i) for v in self.cs["variants"] if v["id"] in ("NCS", "NCT") for i in C.variant_inputs(self.cs, v)]
        self.assertEqual(sup, want)
        self.assertEqual([c[3] for c in order if c[2] == "s20"][:3], [3, 3, 3])                   # input slot of s20 = S3 everywhere

    def test_06_invariance_copies_are_called_by_real_variants_only(self):
        _, order = self.parse()
        copies = {"sc5", "sc10", "sc20", "sc40", "sc100", "of5", "of10", "of20", "of40", "of100"}
        who = {vid for fn, vid, iid, k in order if iid in copies}
        self.assertEqual(who, {"L14", "L20", "L21", "L30"})

    def test_07_raw_column_family_per_variant(self):
        hdr = C.header_of(self.cs)
        self.assertIn("sum_L20_s10", hdr)
        self.assertIn("ms_L20_ramp", hdr)
        self.assertIn("r_L20_of100", hdr)
        self.assertNotIn("sum_L20_of100", hdr)
        self.assertIn("r_NCS_alt", hdr)
        self.assertNotIn("sum_NCS_alt", hdr)


class TestRefusals(unittest.TestCase):
    def test_00_unbroken_spec_is_clean(self):
        self.assertEqual(codes(rfx()), [])

    def test_01_outputs_must_end_in_r(self):
        s = rfx()
        variant(s, "L20")["outputs"] = ["r", "sum"]
        self.assertIn("OUTPUTS_BAD", codes(s))

    def test_02_unknown_duplicate_or_missing_outputs(self):
        s = rfx(); variant(s, "L20")["outputs"] = ["sum", "foo", "r"]; self.assertIn("OUTPUTS_BAD", codes(s))
        s = rfx(); variant(s, "L20")["outputs"] = ["sum", "sum", "r"]; self.assertIn("OUTPUTS_BAD", codes(s))
        s = rfx(); del variant(s, "NCA")["outputs"]; self.assertIn("OUTPUTS_BAD", codes(s))
        s = rfx(); variant(s, "L20")["outputs"] = []; self.assertIn("OUTPUTS_BAD", codes(s))

    def test_03_real_variant_must_export_the_linear_output(self):
        s = rfx()
        variant(s, "L20")["outputs"] = ["ms", "r"]
        self.assertIn("OUTPUTS_BAD", codes(s))

    def test_04_invariance_needs_transforms_and_a_bool(self):
        s = rfx(); del s["inputs"]["invariance"]; self.assertIn("INVARIANCE_BAD", codes(s))
        s = rfx(); variant(s, "L20")["invariance"] = "yes"; self.assertIn("INVARIANCE_BAD", codes(s))
        s = rfx(); s["inputs"]["invariance"]["transforms"][0]["id"] = "s"; self.assertIn("INVARIANCE_BAD", codes(s))
        s = rfx(); s["inputs"]["invariance"]["transforms"][1]["id"] = "sc"; self.assertIn("INVARIANCE_BAD", codes(s))
        s = rfx(); s["inputs"]["invariance"]["transforms"][0]["level"] = [11]; self.assertIn("INVARIANCE_BAD", codes(s))
        s = rfx(); s["inputs"]["invariance"]["transforms"][0]["amp"] = [1, 0]; self.assertIn("INVARIANCE_BAD", codes(s))
        s = rfx(); s["inputs"]["invariance"]["transforms"] = []; self.assertIn("INVARIANCE_BAD", codes(s))

    def test_05_oscillator_keys(self):
        s = rfx(); s["checks"]["trace_gate"] = -1.0; self.assertIn("OSC_BAD", codes(s))
        s = rfx(); del s["checks"]["bound"]; self.assertIn("OSC_BAD", codes(s))
        s = rfx(); s["checks"]["linear_output"] = "r"; self.assertIn("OSC_BAD", codes(s))
        s = rfx(); del s["checks"]["trace_gate"]; self.assertIn("OSC_BAD", codes(s))          # outputs / bound without the gate

    def test_06_tolerances_and_sources(self):
        s = rfx(); del s["tolerances"]["trace"]; self.assertIn("STRUCT", codes(s))
        s = rfx(); del s["tolerances"]["invariance"]; self.assertIn("STRUCT", codes(s))
        s = rfx(); s["tolerances"]["bound"]["source"] = "no label"; self.assertIn("SOURCE_MISSING", codes(s))

    def test_07_article_model_must_be_a_reflex_model(self):
        s = rfx(); s["expected"]["L20"]["article"] = "reflex_article(0)"; self.assertIn("ARTICLE_MODEL", codes(s))
        s = rfx(); s["expected"]["L20"]["article"] = "us_article(20)"; self.assertIn("ARTICLE_MODEL", codes(s))

    def test_08_detect_kinds(self):
        s = rfx(); s["detect"]["required"]["NCW"] = ["trace", "lag"]; self.assertIn("DETECT_BAD_KIND", codes(s))
        s = rfx(); del s["detect"]["required"]["NCS"]; self.assertIn("DETECT_MISSING", codes(s))
        s = rfx(); s["detect"]["required"]["NCT"] = []; self.assertIn("DETECT_BAD_KIND", codes(s))
        # the new kinds are only valid in an oscillator spec
        u = G.load_spec(os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml"))
        u["detect"]["required"]["NCA"] = ["trace"]
        self.assertIn("DETECT_BAD_KIND", codes(u))

    def test_09_oscillator_keys_refused_in_a_plain_spec(self):
        u = G.load_spec(os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml"))
        u["variants"][0]["outputs"] = ["sum", "r"]
        self.assertIn("OSC_BAD", codes(u))
        u = G.load_spec(os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml"))
        u["inputs"]["invariance"] = {"transforms": [{"id": "sc", "level": [11, 10], "amp": [1, 10]}]}
        self.assertIn("INVARIANCE_BAD", codes(u))

    def test_10_lint_fires_on_a_float32_literal_in_a_control_body(self):
        s = rfx()
        v = variant(s, "NCW")
        v["body"] = v["body"].replace("ncw_w1 = ncw_w1 / 1000;", "ncw_w1 = 0.041;")
        text, bodies = G.build_script(s)
        issues = G.lint_script(text, bodies, allow=G.lint_allowances(s))
        self.assertIn("L_FLOAT32", [r for r, _ in issues])


if __name__ == "__main__":
    unittest.main()
