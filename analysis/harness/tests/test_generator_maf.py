"""MAF stage 1: the generator's D7 path ([checks].adaptive = true) for MAMA / FAMA and FRAMA: bars inputs (point / band, affine copies
mapping x, High and Low together), five- and three-column calls through local scalars, every column on every input (copies included),
generator / checker header and slot parity, the superseded call order IMP replays, the inline control bodies (= the brief's code block
with the declared edits only), the no-static lint on the CURRENT bodies (1 and 2 hits), the pre-registered corrected lines, the spec
refusals, the local-prefix rule (gotchas 1.3), and byte-identical regeneration of ALL TEN existing specs.

Rule (CLAUDE.md 4.4): each refusal / lint is seen to fire on a deliberately broken input, one defect at a time.
Stage 2 writes MAMA_Superseded.c / FRAMA_Superseded.c and the corrected MAMA.c / FRAMA.c: until then lint may report ONLY the missing
superseded include and the current files' statics (this test passes before and after stage 2).
Git is used read-only (git show / rev-parse). No Zorro run. Labels: (a) source states, (b) verified here, (c) inference.
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
import maf_support as S      # noqa: E402

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
            ("LRSI_ArticleFidelity.toml", "GEN_LRS_LaguerreRSI.c"),
            ("FSH_ArticleFidelity.toml", "GEN_FSH_FisherTransform.c"))
BASE_COMMIT = "b7bdd69"
BLOBS = {"indicators/ehlers/MAMA.c": "bab4cbbb5961be5720bce82fc6e487e283f7f00e",
         "indicators/ehlers/FRAMA.c": "3352fbe04ed691e479564bc63d46ae181334f9bb"}
SPECS = {"MAMA": S.MAMA_SPEC, "FRAMA": S.FRAMA_SPEC}
STAGE2 = {"MAMA": ("MAMA_Superseded.c", "indicators/ehlers/MAMA.c"), "FRAMA": ("FRAMA_Superseded.c", "indicators/ehlers/FRAMA.c")}


def spec(name):
    return copy.deepcopy(G.load_spec(SPECS[name]))


def codes(sp):
    errs, _ = G.validate_spec(sp)
    return [c for c, _ in errs]


def variant(sp, vid):
    return [v for v in sp["variants"] if v["id"] == vid][0]


def git_show(rev, path):
    r = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, path)], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise AssertionError("git show %s:%s failed: %s" % (rev, path, r.stderr.strip()))
    return r.stdout


def norm(t):
    return re.sub(r"\s+", " ", t).strip()


class TestByteIdenticalRegeneration(unittest.TestCase):
    def test_01_ten_existing_specs_regenerate_the_committed_scripts(self):
        for spec_name, gen_name in EXISTING:
            sp = G.load_spec(os.path.join(HARNESS, "specs", spec_name))
            self.assertFalse(G.adaptive_of(sp), spec_name)
            text, _ = G.build_script(sp)
            with open(os.path.join(ROOT, "strategies", "tests", gen_name), "rb") as f:
                committed = f.read().replace(b"\r\n", b"\n").decode("utf-8")
            self.assertEqual(text, committed, spec_name)
        print("\n  byte-identical: %d / %d existing specs" % (len(EXISTING), len(EXISTING)))

    def test_02_the_comparison_fires(self):
        s = G.load_spec(os.path.join(HARNESS, "specs", "FSH_ArticleFidelity.toml"))
        s["zorro"]["series_len"] = 22
        with open(os.path.join(ROOT, "strategies", "tests", "GEN_FSH_FisherTransform.c"), "rb") as f:
            committed = f.read().replace(b"\r\n", b"\n").decode("utf-8")
        self.assertNotEqual(G.build_script(s)[0], committed)

    def test_03_older_checker_dicts_carry_no_adaptive_keys(self):
        for spec_name, _ in EXISTING:
            cs = G.to_checker_spec(G.load_spec(os.path.join(HARNESS, "specs", spec_name)))
            self.assertNotIn("adaptive", cs)
            self.assertFalse({k for k in cs if k.startswith("tolcols_")} | {"tol_equivariance", "tol_hull"} & set(cs))


class _Script:
    @classmethod
    def build(cls, name):
        cls.name = name
        cls.spec = spec(name)
        cls.cs = G.to_checker_spec(cls.spec)
        cls.text, cls.bodies = G.build_script(cls.spec)
        cls.p = cls.spec["batch"]["id_prefix"].lower()

    def parse(self):
        """{(column, variant, input): Y slot}, [(function, variant, input, series args)] from the call lines."""
        calls, order = {}, []
        lines = self.text.split("\n")
        call_re = re.compile(r"^\tY\[(\d+)\] = (\w+)\(([^;]*?)((?:, &%s_o_\w+)*)\);\t// (\w+) (\w+)$" % self.p)
        i = 0
        while i < len(lines):
            m = call_re.match(lines[i])
            i += 1
            if not m:
                continue
            ret, fn, args, ptrs, vid, iid = m.groups()
            v = variant(self.spec, vid)
            names = re.findall(r"&%s_o_(\w+)" % self.p, ptrs)
            self.assertEqual(names, v["outputs"][:-1], (vid, iid))
            for o in names:
                cm = re.match(r"^\tY\[(\d+)\] = %s_o_%s;$" % (self.p, o), lines[i])
                self.assertIsNotNone(cm, (vid, iid, o))
                calls[(o, vid, iid)] = int(cm.group(1))
                i += 1
            calls[(v["outputs"][-1], vid, iid)] = int(ret)
            order.append((fn, vid, iid, args))
        return calls, order

    def check_header_and_slots(self):
        calls, _ = self.parse()
        P = self.spec["batch"]["id_prefix"].upper()
        hdr_block = self.text.split("if(!%s_hdr) {" % self.p)[1].split("%s_hdr = 1;" % self.p)[0]
        names = [n for n in "".join(re.findall(r'file_append\(%s_RAW, "([^"\\]*)", 0\);' % P, hdr_block)).split(",") if n]
        self.assertEqual(names, C.header_of(self.cs))
        data = self.text.split("// --- write one row per fed bar ---")[1].split("if(n == %s_NBARS - 1)" % P)[0]
        nx = len([h for h in names if h.startswith(("x_", "xh_", "xl_"))])
        y_after = [int(s) for s in re.findall(r"Y\[(\d+)\]", data)]
        want = [calls[tuple(name.split("_", 2))] for name in names[2 + nx:]]
        self.assertEqual(y_after, want)
        self.assertEqual(len(set(y_after)), len(y_after))
        xs = re.findall(r"(X|XH|XL)\[(\d+)\]", data)
        ids = C.input_names(self.cs)
        bars = C.adaptive_bar_names(self.cs)
        self.assertEqual(xs, [("X", str(k)) for k in range(len(ids))] + [(a, str(j)) for j in range(len(bars)) for a in ("XH", "XL")])
        return len(want)


class TestMamaScript(_Script, unittest.TestCase):
    N_FLOOR = 4                 # trace, trace_phase, equivariance, equivariance_phase

    @classmethod
    def setUpClass(cls):
        cls.build("MAMA")

    def test_01_spec_valid_and_lint_reports_only_stage_2_items(self):
        errs, infos = G.validate_spec(self.spec)
        self.assertEqual(errs, [])
        self.assertEqual(len([i for i in infos if i.startswith("INFO D2 floor") and "window ok" in i]), self.N_FLOOR)
        self.assertTrue(all("NOT met" not in i and "EXCEEDS" not in i for i in infos))
        issues = G.lint_script(self.text, self.bodies, allow=G.lint_allowances(self.spec)) + G.no_static_issues(G.no_static_report(self.spec))
        sup, cfile = STAGE2[self.name]
        self.assertEqual([(r, m) for r, m in issues if not ((r == "L_INCLUDE" and sup in m) or (r == "L_NO_STATIC" and cfile in m))], [])
        print("\n  %s lint: %d issue(s), all stage-2: %s" % (self.name, len(issues), [m[:60] for _, m in issues]))

    def test_02_cli_lint_only(self):
        r = subprocess.run([sys.executable, os.path.join(HARNESS, "generator.py"), SPECS[self.name], "--lint-only"],
                           capture_output=True, text=True, encoding="utf-8")
        sup, cfile = STAGE2[self.name]
        refused = [l for l in r.stdout.splitlines() if l.startswith(("LINT REFUSED", "SPEC REFUSED"))]
        self.assertTrue(all(("L_INCLUDE" in l and sup in l) or ("L_NO_STATIC" in l and cfile in l) for l in refused), refused)
        self.assertEqual(r.returncode, 3 if refused else 0)

    def test_03_script_counts_and_five_column_calls(self):
        t = self.text
        self.assertIn("\tvar X[9];", t)
        self.assertNotIn("var XH[", t)
        self.assertEqual(len(re.findall(r"^\tvars S\d+ = series\(X\[\d+\], 34\);", t, re.M)), 9)
        _, order = self.parse()
        self.assertEqual(len(order), 67)                                     # MA05 / MA03 x 9 + 7 x 7
        self.assertIn("67 indicator calls per bar", t)
        core = [o for o in order if o[0] == "MAMACore"]
        self.assertEqual(len(core), 18)
        self.assertEqual(len(re.findall(r"= MAMACore\(S\d+, mam_g1_2, mam_g1_20, &mam_o_fama, &mam_o_period, &mam_o_alpha, &mam_o_phase\);", t)), 9)
        self.assertEqual(len(re.findall(r"= MAMACore\(S\d+, mam_g3_10, mam_g1_10, &mam_o_fama", t)), 9)
        self.assertEqual(len(re.findall(r"= MAMA_Superseded\(S\d+, mam_g1_2, mam_g1_20, &mam_o_fama\);", t)), 14)
        for nm, (a, b) in (("mam_g1_2", (1, 2)), ("mam_g1_20", (1, 20)), ("mam_g3_10", (3, 10)), ("mam_g1_10", (1, 10))):
            self.assertIn("\tvar %s = %d;\t%s = %s / %d;" % (nm, a, nm, nm, b), t)
        self.assertNotIn("&Y[", t)
        self.assertEqual(len(C.header_of(self.cs)), 2 + 9 + self.check_header_and_slots())
        self.assertIn("%d columns" % len(C.header_of(self.cs)), t)

    def test_04_copies_affine_and_called_by_real_variants_only(self):
        t = self.text
        self.assertIn("\tvar mam_k_sc = 10;\tmam_k_sc = mam_k_sc / 1;", t)
        self.assertIn("\tvar mam_c_sc = 0;\tmam_c_sc = mam_c_sc - 99;\tmam_c_sc = mam_c_sc / 10;", t)
        self.assertIn("\tvar mam_c_of = 0;\tmam_c_of = mam_c_of + 11;\tmam_c_of = mam_c_of / 10;", t)
        self.assertIn("\tX[7] = mam_k_sc * X[4] + mam_c_sc;\t// sc40", t)
        self.assertIn("\tX[8] = mam_k_of * X[4] + mam_c_of;\t// of40", t)
        _, order = self.parse()
        self.assertEqual({v for _, v, i, _ in order if i in ("sc40", "of40")}, {"MA05", "MA03"})
        self.assertEqual(C.input_names(self.cs), ["flat", "s5", "s10", "s20", "s40", "s100", "ramp", "sc40", "of40"])

    def test_05_superseded_call_order_is_what_imp_replays(self):
        _, order = self.parse()
        sup = [(v, i) for fn, v, i, _ in order if fn == "MAMA_Superseded"]
        base = ["flat", "s5", "s10", "s20", "s40", "s100", "ramp"]
        self.assertEqual(sup, [("NCS", i) for i in base] + [("NCS2", i) for i in base])
        m = R.IMP_MODELS[self.spec["imp"]["must_pass"]["NCS"]]()
        self.assertEqual([(v, i) for v, i, _ in C.adaptive_shared_slots(self.cs, m)], sup)

    def test_06_only_nc32_has_decimal_literals_and_only_ncp_has_pi(self):
        bodies = {v["id"]: v["body"].rstrip("\n") for v in self.spec["variants"] if v["kind"] == "inline"}
        rest = self.text.replace(bodies["NC32"], "")
        self.assertEqual(G._decimal_tokens(rest), [])
        self.assertEqual(sorted(set(G._decimal_tokens(bodies["NC32"]))), sorted(variant(self.spec, "NC32")["lint_allow_float32"]))
        self.assertEqual([vid for vid, b in bodies.items() if re.search(r"\bPI\b", re.sub(r"//[^\n]*", "", b))], ["NCP"])
        self.assertNotRegex(re.sub(r"//[^\n]*", "", self.text), r"\bPeriod\b")

    def test_07_control_bodies_are_the_brief_with_the_declared_edits(self):
        for vid in S.MAMA_CONTROLS:
            self.assertEqual(variant(self.spec, vid)["body"].strip("\n"), S.mama_control(vid).strip("\n"), vid)
            plain = re.sub(r"\bmx\w*?_", "ma_", S.control_body("MAMACore", "x", S.MAMA_CONTROLS[vid][1], [], "ma_"))
            self.assertIn(norm(S.brief_functions()["MAMACore"]), norm(plain), vid)     # without the edits: the brief, renamed
        with self.assertRaises(AssertionError):
            S.control_body("MAMACore", "x", "mxh_", [("var mxh_w1 = 961;", "y")], "ma_")    # an edit target that does not exist


class TestFramaScript(_Script, unittest.TestCase):
    N_FLOOR = 5                 # trace, equivariance, ramp_exact, lag, flat

    @classmethod
    def setUpClass(cls):
        cls.build("FRAMA")

    test_01_spec_valid_and_lint_reports_only_stage_2_items = TestMamaScript.test_01_spec_valid_and_lint_reports_only_stage_2_items
    test_02_cli_lint_only = TestMamaScript.test_02_cli_lint_only

    def test_03_script_counts_bars_and_three_column_calls(self):
        t = self.text
        self.assertIn("\tvar X[15];", t)
        self.assertIn("\tvar XH[8];", t)
        self.assertIn("\tvar XL[8];", t)
        self.assertIn("\tvar fra_hb = 2;\tfra_hb = fra_hb / 1000;", t)
        self.assertEqual(len(re.findall(r"^\tvars (S|SHi|SLo)\d+ = series\(X[HL]?\[\d+\], 34\);", t, re.M)), 15 + 16)
        _, order = self.parse()
        self.assertEqual(len(order), 108)                                    # FR16 / FR32 x 15 + 6 x 13
        self.assertEqual(len(re.findall(r"= FRAMACore\(S\d+, (S|SHi|SLo)\d+, (S|SLo)\d+, (16|32), &fra_o_dim, &fra_o_alpha\);", t)), 30)
        self.assertEqual(len(re.findall(r"= FRAMA_Superseded\(S\d+, \w+, \w+, 8\);", t)), 26)
        self.assertEqual(len(C.header_of(self.cs)), 2 + 15 + 16 + self.check_header_and_slots())

    def test_04_point_bars_pass_x_as_high_and_low_band_bars_their_own(self):
        _, order = self.parse()
        ids = C.input_names(self.cs)
        bars = C.adaptive_bar_names(self.cs)
        self.assertEqual(bars, ["rampB", "s5B", "s10B", "s20B", "s40B", "s100B", "sc40B", "of40B"])
        for fn, vid, iid, args in order:
            a = [s.strip() for s in args.split(",")]
            k = ids.index(iid)
            if iid in bars:
                self.assertEqual(a[:3], ["S%d" % k, "SHi%d" % bars.index(iid), "SLo%d" % bars.index(iid)], (vid, iid))
            else:
                self.assertEqual(a[:3], ["S%d" % k] * 3, (vid, iid))

    def test_05_band_and_copies_map_x_high_low_together(self):
        t = self.text
        ids = C.input_names(self.cs)
        self.assertIn("\tX[%d] = fra_k_sc * X[%d] + fra_c_sc;\t// sc40B" % (ids.index("sc40B"), ids.index("s40B")), t)
        self.assertIn("\tXH[6] = fra_k_sc * XH[4] + fra_c_sc;\t// sc40B High", t)
        self.assertIn("\tXL[6] = fra_k_sc * XL[4] + fra_c_sc;\t// sc40B Low", t)
        self.assertIn("\tXH[7] = fra_k_of * XH[4] + fra_c_of;\t// of40B High", t)
        self.assertIn("\tXH[4] = X[%d] + fra_hb;\t// s40B High" % ids.index("s40B"), t)
        self.assertIn("\tXL[0] = X[%d] - fra_hb;\t// rampB Low" % ids.index("rampB"), t)
        self.assertIn("\tX[%d] = lvl + slp * n;\t// rampB" % ids.index("rampB"), t)
        _, order = self.parse()
        self.assertEqual({v for _, v, i, _ in order if i in ("sc40B", "of40B")}, {"FR16", "FR32"})

    def test_06_superseded_call_order_is_what_imp_replays(self):
        _, order = self.parse()
        sup = [(v, i) for fn, v, i, _ in order if fn == "FRAMA_Superseded"]
        base = ["flat", "s5", "s10", "s20", "s40", "s100", "ramp", "rampB", "s5B", "s10B", "s20B", "s40B", "s100B"]
        self.assertEqual(sup, [("NCS", i) for i in base] + [("NCS2", i) for i in base])
        m = R.IMP_MODELS[self.spec["imp"]["must_pass"]["NCS"]]()
        self.assertEqual([(v, i) for v, i, _ in C.adaptive_shared_slots(self.cs, m)], sup)

    def test_07_only_nc32_has_decimal_literals(self):
        bodies = {v["id"]: v["body"].rstrip("\n") for v in self.spec["variants"] if v["kind"] == "inline"}
        self.assertEqual(G._decimal_tokens(self.text.replace(bodies["NC32"], "")), [])
        self.assertEqual(sorted(set(G._decimal_tokens(bodies["NC32"]))), ["0.01", "4.6"])
        self.assertNotRegex(re.sub(r"//[^\n]*", "", self.text), r"\bPI\b|\bPeriod\b")

    def test_08_control_bodies_are_the_brief_with_the_declared_edits(self):
        for vid in list(S.FRAMA_CONTROLS) + ["NCT"]:
            self.assertEqual(variant(self.spec, vid)["body"].strip("\n"), S.frama_control(vid).strip("\n"), vid)
        nct = S.NCT_BODY
        for l in ("fxt_D[0] = log(fxt_N1 + fxt_N2) - log(fxt_N3);", "if(fxt_n[0] == 1) fxt_F[0] = Price[0];", "if(fxt_N3 > 0) {",
                  "fxt_F[0] = fxt_A[0]*Price[0] + (fxt_u - fxt_A[0])*fxt_F[0];"):
            self.assertIn(l, nct)
        self.assertNotRegex(nct, r"N1 > 0|N2 > 0")                         # the old guard: no N1 / N2 condition


@unittest.skipIf(shutil.which("git") is None, "git not on PATH")
class TestCorrectedCodeAndLint(unittest.TestCase):
    def test_01_no_static_lint_fires_on_the_current_bodies(self):
        for path, names, ren in (("indicators/ehlers/MAMA.c", ["barCount"], ("barCount", "mao_barCount")),
                                 ("indicators/ehlers/FRAMA.c", ["frama_init", "frama_prev"], ("frama_", "fro_"))):
            r = subprocess.run(["git", "-C", ROOT, "rev-parse", "%s:%s" % (BASE_COMMIT, path)], capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), BLOBS[path])
            old = git_show(BASE_COMMIT, path)
            hits = G.lint_no_static(old)
            print("\n  no-static lint on %s:%s: %s" % (BASE_COMMIT, path, hits))
            self.assertEqual([n for _, n in hits], names)
            renamed = re.sub(r"\b%s" % ren[0], ren[1], old)                # the stage-2 superseded copy
            self.assertEqual(len(G.lint_no_static(renamed)), len(names))
            with tempfile.TemporaryDirectory() as d:
                os.makedirs(os.path.join(d, "indicators", "ehlers"))
                with open(os.path.join(d, path), "w", encoding="utf-8") as f:
                    f.write(old)
                sp = spec("MAMA" if "MAMA" in path else "FRAMA")
                rep = G.no_static_report(sp, root=d)
                self.assertEqual([n for _, n in rep[0][1]], names)
                self.assertEqual([r_ for r_, _ in G.no_static_issues(rep)], ["L_NO_STATIC"])

    def test_02_corrected_lines_are_the_briefs_and_clean(self):
        fns = S.brief_functions()
        for name, core, wrap in (("MAMA", "MAMACore", "MAMA"), ("FRAMA", "FRAMACore", "FRAMA")):
            cc = spec(name)["corrected_code"]
            self.assertEqual(norm(cc["lines"]), norm(fns[core]))
            self.assertEqual(norm(cc["wrapper_lines"]), norm(fns[wrap]))
            self.assertEqual(norm(cc["function"]), norm(S.SIG[core]))
            self.assertEqual(norm(cc["wrapper_function"]), norm(S.SIG[wrap]))
            body = "%s\n{\n%s\n}\n%s\n{\n%s\n}\n" % (cc["function"], cc["lines"], cc["wrapper_function"], cc["wrapper_lines"])
            self.assertEqual(G.lint_no_static(body), [])
            code = re.sub(r"//[^\n]*", "", cc["lines"] + cc["wrapper_lines"])
            self.assertEqual(G._decimal_tokens(code), [])                       # no decimal literal (9d.1, 9d.8)
            self.assertNotRegex(code, r"\bPeriod\b|\bPI\b|\bINITRUN\b|\bstatic\b")
            ln = [l for l in cc["lines"].strip().split("\n") if l.strip()]
            first = [i for i, l in enumerate(ln) if "series(" in l]
            self.assertEqual(first, list(range(len(first))))                    # every series() call first and unconditional (3.1)
            for l in ln:                                                         # 9d.8: no literal product / quotient starts an expression
                for rhs in re.findall(r"=\s*([^;]+);", re.sub(r"//[^\n]*", "", l)):
                    self.assertNotRegex(rhs.strip(), r"^\d+\s*[*/]\s*\d", l)
        # the brief's block contains exactly these four functions
        self.assertEqual(norm(S.brief_block()).count("var "), norm(S.brief_block()).count("var "))
        self.assertEqual(len(fns), 4)

    def test_03_prefixes_are_not_declared_elsewhere(self):
        """gotchas 1.3 (flat namespace): no .c / .h file under indicators/ or strategies/ declares an identifier with a MAF prefix, except
        the file that owns it (stage 2: MAMA.c ma_ / maw_, MAMA_Superseded.c mao_, FRAMA.c fr_ / frw_, FRAMA_Superseded.c fro_; the
        generated scripts their own and the control prefixes)."""
        own = {"ma_": "MAMA.c", "maw_": "MAMA.c", "mao_": "MAMA_Superseded.c", "fr_": "FRAMA.c", "frw_": "FRAMA.c",
               "fro_": "FRAMA_Superseded.c"}
        gen = {"mxh_", "mxf_", "mx32_", "mxp_", "mxb_", "mam_"}, {"fxe_", "fxn_", "fx32_", "fxt_", "fra_"}
        bad = []
        for top in ("indicators", "strategies"):
            for dp, _, fs in os.walk(os.path.join(ROOT, top)):
                for fn in fs:
                    if not fn.endswith((".c", ".h")):
                        continue
                    with open(os.path.join(dp, fn), encoding="utf-8", errors="replace") as f:
                        txt = G._strip(f.read())
                    for pre in list(own) + sorted(gen[0] | gen[1]):
                        if re.search(r"\b%s\w+" % pre, txt):
                            ok = (own.get(pre) == fn or (pre in gen[0] and fn == "GEN_MAM_MAMA.c")
                                  or (pre in gen[1] and fn == "GEN_FRA_FRAMA.c"))
                            if not ok:
                                bad.append((fn, pre))
        self.assertEqual(bad, [])
        # and the check fires
        self.assertTrue(re.search(r"\bfr_\w+", G._strip("var x = fr_HH;")))


class TestRefusals(unittest.TestCase):
    def test_00_unbroken_specs_are_clean(self):
        self.assertEqual(codes(spec("MAMA")), [])
        self.assertEqual(codes(spec("FRAMA")), [])

    def test_01_inputs_bars_equivariance(self):
        s = spec("FRAMA"); s["inputs"]["band_inputs"] = ["flat"]; self.assertIn("BARS_BAD", codes(s))
        s = spec("FRAMA"); s["inputs"]["band_half"] = [0, 1000]; self.assertIn("BARS_BAD", codes(s))
        s = spec("FRAMA"); s["checks"]["bars"] = False; self.assertIn("BARS_BAD", codes(s))
        s = spec("MAMA"); s["inputs"]["equivariance"]["inputs"] = ["ramp"]; self.assertIn("EQUIVARIANCE_BAD", codes(s))
        s = spec("MAMA"); s["inputs"]["equivariance"]["transforms"][0]["scale"] = [0, 1]; self.assertIn("EQUIVARIANCE_BAD", codes(s))
        s = spec("MAMA"); s["inputs"]["equivariance"]["transforms"][1]["id"] = "sc"; self.assertIn("EQUIVARIANCE_BAD", codes(s))
        s = spec("MAMA"); s["checks"]["equivariance_from_n"] = 3000; self.assertIn("EQUIVARIANCE_BAD", codes(s))
        s = spec("MAMA"); variant(s, "MA05")["equivariance"] = False; self.assertIn("EQUIVARIANCE_BAD", codes(s))

    def test_02_checks_and_tolerances(self):
        s = spec("MAMA"); s["checks"]["columns"] = ["mama", "nope"]; self.assertIn("ADAPTIVE_BAD", codes(s))
        s = spec("MAMA"); s["checks"]["level_columns"] = ["out"]; self.assertIn("ADAPTIVE_BAD", codes(s))
        s = spec("FRAMA"); s["checks"]["ramp_exact"] = {"out": "nope"}; self.assertIn("ADAPTIVE_BAD", codes(s))
        s = spec("FRAMA"); s["checks"]["hull"] = []; self.assertIn("ADAPTIVE_BAD", codes(s))
        s = spec("FRAMA"); del s["tolerances"]["hull"]; self.assertIn("STRUCT", codes(s))
        s = spec("MAMA"); s["tolerances"]["trace"]["columns"] = {"nope": 1e-8}; self.assertIn("TOL_COLUMNS_BAD", codes(s))
        s = spec("MAMA"); s["tolerances"]["trace"]["source"] = "no label"; self.assertIn("SOURCE_MISSING", codes(s))
        s = spec("FRAMA"); del s["expected"]["FR16"]["ramp_lag"]; self.assertIn("STRUCT", codes(s))

    def test_03_conditioning_section(self):
        s = spec("MAMA"); s["conditioning"]["bound"]["phase"] = 1e-10; self.assertIn("CONDITIONING_BAD", codes(s))   # not tol/10 (S2)
        s = spec("MAMA"); s["conditioning"]["order"] = s["conditioning"]["order"][:-1]; self.assertIn("CONDITIONING_BAD", codes(s))
        s = spec("MAMA"); s["expected"]["MA05"]["conditioning"]["info"]["nope"] = ["mama"]; self.assertIn("CONDITIONING_BAD", codes(s))
        s = spec("MAMA"); del s["expected"]["MA05"]["conditioning"]; self.assertIn("CONDITIONING_BAD", codes(s))

    def test_04_expected_tables_bounds_variants(self):
        s = spec("MAMA"); s["expected"]["MA05"]["article"] = "mama_article(1/20,1/2)"; self.assertIn("ARTICLE_MODEL", codes(s))
        s = spec("MAMA"); s["expected"]["MA05"]["bounds"]["alpha"]["lo"] = 0.6; self.assertIn("BOUNDS_BAD", codes(s))
        s = spec("MAMA"); s["expected"]["MA05"]["bounds"]["nope"] = {"hi": 1.0}; self.assertIn("BOUNDS_BAD", codes(s))
        s = spec("MAMA"); variant(s, "MA05")["outputs"] = ["fama", "period", "alpha", "mama"]; self.assertIn("OUTPUTS_BAD", codes(s))
        s = spec("MAMA"); variant(s, "MA05")["outputs"] = ["mama", "fama", "period", "alpha", "phase"]; self.assertIn("OUTPUTS_BAD", codes(s))
        s = spec("MAMA"); variant(s, "NCS")["outputs"] = ["mama"]; self.assertEqual(codes(s), [])     # a control may export less
        s = spec("MAMA"); s["batch"]["real_params"] = False; self.assertIn("PARAMS_BAD", codes(s))
        s = spec("MAMA"); variant(s, "NCH")["body"] = variant(s, "NCH")["body"].replace("mam_nch(", "mam_xxx("); self.assertIn("STRUCT", codes(s))

    def test_05_detect_imp(self):
        s = spec("MAMA"); s["detect"]["required"]["NCH"] = ["hull"]; self.assertIn("DETECT_BAD_KIND", codes(s))     # MAMA has no hull
        s = spec("MAMA"); del s["detect"]["required"]["NCS2"]; self.assertIn("DETECT_MISSING", codes(s))
        s = spec("FRAMA"); s["detect"]["required"]["NCE"] = ["equivariance"]; self.assertEqual(codes(s), [])
        self.assertEqual(spec("FRAMA")["detect"]["info_only"], {"NCT": ["bound"]})
        s = spec("FRAMA"); s["detect"]["info_only"]["NCT"] = ["trace"]; self.assertIn("DETECT_BAD_KIND", codes(s))   # overlaps required
        s = spec("FRAMA"); s["detect"]["info_only"]["FR16"] = ["bound"]; self.assertIn("DETECT_BAD_KIND", codes(s))  # not a control
        _, infos = G.validate_spec(spec("FRAMA"))
        nct = [i for i in infos if i.startswith("INFO D2 margin NCT")][0]
        self.assertIn("bound 1e+12x (INFO only)", nct)
        self.assertIn("10x margin met (trace)", nct)
        self.assertEqual(spec("MAMA")["variants"][2]["role"], "neg_control")                  # NCB is a control (stage 1 review)
        s = spec("MAMA"); s["imp"]["must_pass"]["NCH"] = "mama_article(1/2,1/20,w1=964/10000)"; self.assertIn("IMP_UNKNOWN_MODEL", codes(s))
        s = spec("MAMA"); del s["imp"]["must_pass"]["NCF"]; self.assertIn("IMP_BAD", codes(s))

    def test_06_float32_exemption_is_scoped_to_nc32(self):
        s = spec("FRAMA"); del variant(s, "NC32")["lint_allow_float32"]; del variant(s, "NC32")["lint_allow_reason"]
        text, bodies = G.build_script(s)
        self.assertIn("L_FLOAT32", [r for r, _ in G.lint_script(text, bodies, allow=G.lint_allowances(s))])
        s = spec("MAMA"); v = variant(s, "NCH")
        v["body"] = v["body"].replace("var mxh_w1 = 963;  mxh_w1 = mxh_w1/10000;", "var mxh_w1 = 0.0963;")
        text, bodies = G.build_script(s)
        self.assertIn("L_FLOAT32", [r for r, _ in G.lint_script(text, bodies, allow=G.lint_allowances(s))])


if __name__ == "__main__":
    unittest.main()
