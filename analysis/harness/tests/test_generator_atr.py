"""ATR stage 1: the spec (specs/ATR_MT4Fidelity.toml) through the generator: validation, the generated script, the pre-registered corrected code and
control bodies, the no-static lint, the call order of the shared-state control, and BYTE-IDENTICAL regeneration of the 12 existing specs.
No .c file is written, Zorro is not run."""
import copy
import glob
import hashlib
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))

import atr_support as A   # noqa: E402
import checker as C       # noqa: E402
import generator as G     # noqa: E402
import maf_support as M   # noqa: E402
import reference as R     # noqa: E402

SPECS = os.path.join(A.HARNESS, "specs")
BASELINE = os.path.join(HERE, "regen_baseline.json")


def spec():
    return G.load_spec(A.SPEC)


def norm(text):
    """Comments stripped, whitespace collapsed (the corrected-code comparison of the earlier specs)."""
    text = re.sub(r"//[^\n]*", " ", text)
    return " ".join(text.split())


class ExistingSpecsUnchanged(unittest.TestCase):
    """The tooling extensions are opt-in: the 12 existing specs regenerate BYTE-IDENTICAL scripts and the MAMA / FRAMA checker output is unchanged
    (baseline: tests/regen_baseline.json, taken before the ATR edits)."""

    @classmethod
    def setUpClass(cls):
        with open(BASELINE, encoding="utf-8") as f:
            cls.base = json.load(f)

    def test_there_are_12_existing_specs_and_all_regenerate_byte_identical(self):
        paths = sorted(p for p in glob.glob(os.path.join(SPECS, "*.toml")) if not os.path.basename(p).startswith("ATR_"))
        self.assertEqual(len(paths), 12)
        self.assertEqual(sorted(self.base["scripts"]), sorted(os.path.basename(p) for p in paths))
        for p in paths:
            text, _ = G.build_script(G.load_spec(p))
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), self.base["scripts"][os.path.basename(p)], os.path.basename(p))

    def test_baseline_would_catch_a_change(self):
        """Guard seen to fire: one byte more in a regenerated script changes the hash."""
        p = os.path.join(SPECS, "FRAMA_ArticleFidelity.toml")
        text, _ = G.build_script(G.load_spec(p))
        self.assertNotEqual(hashlib.sha256((text + " ").encode()).hexdigest(), self.base["scripts"]["FRAMA_ArticleFidelity.toml"])

    def test_maf_checker_output_unchanged(self):
        for p in (M.MAMA_SPEC, M.FRAMA_SPEC):
            name = os.path.basename(p)
            rows, _ = M.evaluated(p)
            h = hashlib.sha256(json.dumps([(r["check_id"], r["result"], "%.3e" % r["abs_diff"]) for r in rows]).encode()).hexdigest()
            self.assertEqual(h, self.base["eval"][name], name)
            vals, _ = C.conditioning_table(M.load(p)[1])
            h = hashlib.sha256(json.dumps({t: {i: {c: "%.6e" % v for c, v in d.items()} for i, d in x.items()} for t, x in vals.items()},
                                          sort_keys=True).encode()).hexdigest()
            self.assertEqual(h, self.base["conditioning"][name], name)


class SpecValidation(unittest.TestCase):
    def test_spec_is_valid_and_margins_hold(self):
        errs, infos = G.validate_adaptive(spec())
        self.assertEqual(errs, [])
        self.assertTrue(all("window ok" in i for i in infos if "D2 floor" in i), infos)
        self.assertTrue(all("10x margin met" in i for i in infos if "D2 margin" in i), infos)
        self.assertEqual(len([i for i in infos if "D2 margin" in i]), 7)

    def test_variant_and_check_counts(self):
        sp = spec()
        real = [v for v in sp["variants"] if v["role"] == "real"]
        ctl = [v for v in sp["variants"] if v["role"] == "neg_control"]
        self.assertEqual([v["id"] for v in real], ["AT14", "AT20"])
        self.assertEqual([v["id"] for v in ctl], list(A.CONTROLS))
        cs = G.to_checker_spec(sp)
        self.assertEqual(sum(C.n_checks(cs, v) for v in cs["variants"] if v["role"] == "real"), 90)
        self.assertEqual(len(sp["variants"]), 9)

    def test_every_control_has_a_required_kind_at_10x(self):
        sp = spec()
        self.assertEqual(sorted(sp["detect"]["required"]), sorted(A.CONTROLS))
        for vid, ks in sp["detect"]["required"].items():
            self.assertTrue(ks, vid)
            eff = [v for v in sp["variants"] if v["id"] == vid][0]["effect"]
            for k in ks:
                self.assertGreaterEqual(eff[k] / sp["tolerances"][k]["value"], 10.0, (vid, k))

    def test_refusals(self):
        def errs(edit):
            sp = copy.deepcopy(spec())
            edit(sp)
            return [c for c, _ in G.validate_adaptive(sp)[0]]
        self.assertIn("BARS_BAD", errs(lambda s: s["checks"].update(bar_args="xyz")))
        self.assertIn("ADAPTIVE_BAD", errs(lambda s: s["checks"].update(window_hull={"atr": "atr"})))
        self.assertIn("ADAPTIVE_BAD", errs(lambda s: s["checks"].update(known_value={"atr": {"nope": [1, 2]}})))
        self.assertIn("ADAPTIVE_BAD", errs(lambda s: s["checks"].update(range_bound=["nope"])))
        self.assertIn("ADAPTIVE_BAD", errs(lambda s: s["inputs"].update(ramp_down="yes")))
        self.assertIn("STRUCT", errs(lambda s: s["expected"]["AT14"].pop("window")))
        self.assertIn("STRUCT", errs(lambda s: s["tolerances"]["trace"].update(abs=1e-15)))     # only bound / window_hull take abs
        self.assertIn("STRUCT", errs(lambda s: s["tolerances"].pop("window_hull")))
        self.assertIn("STRUCT", errs(lambda s: s["tolerances"].pop("known_value")))

    def test_flat_band_input_needs_the_opt_in_flag(self):
        """A band copy of flat is accepted only with [inputs].band_flat = true (the older specs refuse it; test_generator_maf pins that)."""
        sp = copy.deepcopy(spec())
        self.assertTrue(sp["inputs"]["band_flat"])
        sp["inputs"]["band_flat"] = False
        self.assertIn("BARS_BAD", [c for c, _ in G.validate_adaptive(sp)[0]])
        del sp["inputs"]["band_flat"]
        self.assertIn("BARS_BAD", [c for c, _ in G.validate_adaptive(sp)[0]])

    def test_older_style_spec_still_refuses_flat_band_when_not_a_base_id(self):
        sp = copy.deepcopy(spec())
        sp["inputs"]["band_inputs"] = ["nope"]
        self.assertIn("BARS_BAD", [c for c, _ in G.validate_adaptive(sp)[0]])


class GeneratedScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sp = spec()
        cls.text, cls.bodies = G.build_script(cls.sp)

    def test_lint_issues_are_exactly_the_two_stage2_ones(self):
        issues = G.lint_script(self.text, self.bodies, allow=G.lint_allowances(self.sp)) + G.no_static_issues(G.no_static_report(self.sp))
        self.assertEqual(sorted(r for r, _ in issues), ["L_INCLUDE", "L_NO_STATIC"])
        self.assertTrue(all("ATR.c" in m for _, m in issues))
        self.assertFalse(os.path.exists(os.path.join(A.ROOT, "indicators", "nnfx", "ATR.c")))        # stage 1 writes no .c file

    def test_include_is_the_nnfx_path_and_script_name(self):
        self.assertIn('#include "../../indicators/nnfx/ATR.c"', self.text)
        self.assertTrue(self.text.startswith("// GEN_ATR_MT4.c"))
        self.assertIn("point bars pass x as High, Low and Close.", self.text)

    def test_input_expressions_have_no_decimal_literal_and_rampdn_is_built(self):
        self.assertIn("X[7] = lvl - slp * n;\t// rampdn", self.text)
        self.assertIn("var atr_hb = 2;\tatr_hb = atr_hb / 10000;", self.text)
        self.assertIn("var atr_k_sc = 10;\tatr_k_sc = atr_k_sc / 1;", self.text)
        self.assertFalse([r for r, _ in G.lint_script(self.text, self.bodies) if r in ("L_FLOAT32", "L_PI", "L_QUIT")])

    def test_series_lengths_and_unconditional_series_calls(self):
        for line in self.text.split("\n"):
            if "series(" in line and not line.strip().startswith("//"):
                self.assertRegex(line, r"series\((?:0|X\[\d+\]|XH\[\d+\]|XL\[\d+\]), [^)]+\)", line)         # explicit length everywhere (9d.10)
        self.assertIn("vars S0 = series(X[0], 22);", self.text)
        # no series() inside an if(): the harness calls are straight-line, the bodies declare them first
        for b in self.bodies:
            body = b.split("{", 1)[1]
            first_stmt = [ln for ln in body.split("\n") if ln.strip() and not ln.strip().startswith("//")]
            self.assertTrue(all("series(" in ln for ln in first_stmt[:3 if "static" not in b else 2]), b[:80])
            self.assertNotRegex(body, r"if\s*\([^)]*\)\s*[^;{]*series\(")

    def test_call_count_and_header(self):
        self.assertIn("// CALLS:    148 indicator calls per bar", self.text)
        self.assertEqual(self.text.count("&atr_o_tr);"), 18 + 18 + 5 * 16)            # the 7 two-output variants; NCS / NCS2 export atr only

    def test_call_lines_per_variant(self):
        per = {}
        for line in self.text.split("\n"):
            m = re.match(r"\s*Y\[\d+\] = \w+\(.*\);\s*// (\w+) (\w+)\s*$", line)
            if m:
                per.setdefault(m.group(1), []).append(m.group(2))
        self.assertEqual({k: len(v) for k, v in per.items()}, {"AT14": 18, "AT20": 18, "NCW": 16, "NC0": 16, "NCWi": 16, "NCR": 16, "NCZ": 16,
                                                              "NCS": 16, "NCS2": 16})
        self.assertEqual(sum(len(v) for v in per.values()), 148)
        self.assertIn("sc40B", per["AT14"])
        self.assertNotIn("sc40B", per["NCW"])


class CorrectedCodeAndControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sp = spec()
        cls.fns = A.brief_functions()

    def test_spec_lines_equal_the_brief_code_block(self):
        cc = self.sp["corrected_code"]
        self.assertEqual(norm(cc["lines"]), norm(self.fns["ATRMT4Core"]))
        self.assertEqual(norm(cc["wrapper_lines"]), norm(self.fns["ATRMT4"]))
        self.assertEqual(cc["file"], "indicators/nnfx/ATR.c")

    def test_brief_code_follows_the_light_c_rules(self):
        core = self.fns["ATRMT4Core"] + self.fns["ATRMT4"]
        code = re.sub(r"//[^\n]*", "", core)
        self.assertEqual(G.lint_no_static(core), [])
        self.assertFalse(G._DECIMAL_RE.search(code))                              # no decimal literal (9d.1, 9d.8)
        self.assertNotIn("?", code)                                               # no ternary
        self.assertNotRegex(code, r"\bPI\b")
        self.assertNotRegex(code, r"\bPeriod\b")
        sers = re.findall(r"series\(([^)]*)\)", code)
        self.assertEqual(len(sers), 3)
        self.assertTrue(all("," in s for s in sers))                              # explicit length on every series()
        first = [ln.strip() for ln in code.split("\n") if ln.strip()][:3]
        self.assertTrue(all("series(" in ln for ln in first))                     # unconditional and first (3.1)
        self.assertEqual(sorted(set(re.findall(r"\b(at_\w+)", code))), ["at_A", "at_TR", "at_i", "at_n", "at_s", "at_th", "at_tl"])

    def test_inline_bodies_are_exactly_the_derived_ones(self):
        for vid in ("NC0", "NCWi", "NCR", "NCZ", "NCS"):
            v = [u for u in self.sp["variants"] if u["id"] == vid][0]
            self.assertEqual(v["body"].rstrip("\n"), A.control_body(vid).rstrip("\n"), vid)
        ncs2 = [u for u in self.sp["variants"] if u["id"] == "NCS2"][0]
        self.assertEqual((ncs2["kind"], ncs2["function"]), ("param", "atr_ncs"))
        ncw = [u for u in self.sp["variants"] if u["id"] == "NCW"][0]
        self.assertEqual((ncw["kind"], ncw["params"]), ("param", [15]))

    def test_each_control_differs_from_the_corrected_body_by_its_edit_only(self):
        core = re.sub(r"\bat_", "zz_", self.fns["ATRMT4Core"])
        for vid in ("NC0", "NCWi", "NCR", "NCZ"):
            fn, pre, edits = A.ATR_CONTROLS[vid]
            body = A.control_body(vid).split("{", 1)[1].rsplit("}", 1)[0]
            ref = re.sub(r"\bat_", pre, self.fns["ATRMT4Core"])
            a, b = ref.split("\n"), body.strip("\n").split("\n")
            added = [ln for ln in b if ln not in a]
            removed = [ln for ln in a if ln not in b]
            self.assertLessEqual(len(removed), 1, vid)
            self.assertTrue(added, vid)
            self.assertNotEqual(core, body)

    def test_edit_helper_refuses_a_missing_or_repeated_target(self):
        with self.assertRaises(AssertionError):
            A._edit("a b a", [("a", "c")])
        with self.assertRaises(AssertionError):
            A._edit("a b", [("zzz", "c")])

    def test_ncs_has_exactly_one_static_and_the_lint_fires_on_it(self):
        hits = G.lint_no_static(A.control_body("NCS"))
        self.assertEqual(hits, [(1, "ats_prev")])
        self.assertEqual(G.lint_no_static(self.fns["ATRMT4Core"] + self.fns["ATRMT4"]), [])
        for vid in ("NC0", "NCWi", "NCR", "NCZ"):
            self.assertEqual(G.lint_no_static(A.control_body(vid)), [], vid)
        # the check wired to the spec fires on a file holding the NCS body (a temp copy), and is clean on the corrected code
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "indicators", "nnfx"))
            fp = os.path.join(d, "indicators", "nnfx", "ATR.c")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(A.control_body("NCS"))
            rep = G.no_static_report(self.sp, root=d)
            self.assertEqual(len(G.no_static_issues(rep)), 1)
            self.assertIn("ats_prev", G.no_static_issues(rep)[0][1])
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.fns["ATRMT4Core"])
            self.assertEqual(G.no_static_issues(G.no_static_report(self.sp, root=d)), [])


class SharedStateCallOrder(unittest.TestCase):
    def test_ncs_calls_in_the_script_equal_the_checker_slots_and_the_imp_replay_uses_them(self):
        sp = spec()
        cs = G.to_checker_spec(sp)
        order = A.generated_call_order(sp, ("NCS", "NCS2"))
        slots = C.adaptive_shared_slots(cs, R.atr_shared((14, 14), 0))
        self.assertEqual([(v, i) for v, i, _ in slots], order)
        self.assertEqual([p for _, _, p in slots], [14] * 32)
        # the same replay the checker's IMP uses, spelled out in the script's order, reproduces the own-model NCS output
        _, _, x, bars = A.load()
        out = A._ncs_order_replay(cs, x, bars, order)
        own = M.own_model_outputs(A.SPEC)
        for (vid, i), o in out.items():
            self.assertEqual(float(abs(o.atr - own[vid]["atr"][i]).max()), 0.0, (vid, i))

    def test_a_reordered_band_list_changes_the_generated_order(self):
        """The call order follows [inputs].band_inputs: reordering it changes the script's NCS order (and therefore the NCS numbers), which is why
        the order is parsed from the script, never assumed."""
        sp = copy.deepcopy(spec())
        sp["inputs"]["band_inputs"] = list(reversed(sp["inputs"]["band_inputs"]))
        self.assertNotEqual(A.generated_call_order(sp, ("NCS",)), A.generated_call_order(spec(), ("NCS",)))


if __name__ == "__main__":
    unittest.main()
