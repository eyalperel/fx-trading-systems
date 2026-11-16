"""Tests for the SS3 tooling: checker [imp] (pass item 6), floor guard (pass item 7), generator acceptance of
[corrected_code] / [imp] / [tolerances.imp] / `rule`.

Run with the rest of the suite: bash analysis/harness/run_tests.sh
Rule (CLAUDE.md section 4.4): every guard is SEEN TO FIRE on a deliberately broken input. Each test prints what
it broke and what it saw. Inputs are synthetic raw files built with reference.simulate (no Zorro, no .c read).

Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import math
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)

import checker as C        # noqa: E402
import generator as G      # noqa: E402
import reference as R      # noqa: E402

SS3 = os.path.join(HARNESS, "specs", "SS3_ArticleFidelity.toml")
SS2 = os.path.join(HARNESS, "specs", "SS2_ArticleFidelity.toml")

REQUIRED = {"NCA": ["gain", "lag"], "NCB": ["gain", "lag", "flat"], "NCL": ["gain", "lag"],
            "NCH": ["gain", "lag"], "NC1": ["gain", "lag"], "NC2": ["gain", "lag"]}


def toml_spec():
    return G.load_spec(SS3)


def cspec():
    return G.to_checker_spec(toml_spec())


def filters10():
    """The 10 SS3F variants as simulated filters (real variants = the corrected .c with Zorro's PI)."""
    return {"P10": R.ss3_code(10), "P14": R.ss3_code(14), "P20": R.ss3_code(20), "P30": R.ss3_code(30),
            "NCA": R.ss3_code(20, a1_bump=1), "NCB": R.ss3_code(20, in_bump=1), "NCL": R.ss3_printed(20),
            "NCH": R.ss3_hybrid(20), "NC1": R.ss3_code(21), "NC2": R.ss3_code(20, deg=True)}


def build_cols(spec, override=None):
    """-> {column: list of float} for the raw file; override: {variant id: Filter} replaces that variant."""
    x = C.make_inputs(spec)
    ins = C.input_names(spec)
    fl = filters10()
    fl.update(override or {})
    cols = {"n": [float(k) for k in range(spec["n_bars"])], "clock_close": [1.1] * spec["n_bars"]}
    for i in ins:
        cols["x_" + i] = [float(v) for v in x[i]]
    for v in spec["variants"]:
        for i in ins:
            cols["y_%s_%s" % (v["id"], i)] = [float(t) for t in R.simulate(fl[v["id"]], x[i])]
    return cols


_cache = {}


def base_cols(spec):
    if "cols" not in _cache:
        _cache["cols"] = build_cols(spec)
    return {k: list(v) for k, v in _cache["cols"].items()}


def to_text(spec, cols):
    h = C.header_of(spec)
    lines = [",".join(h)]
    for r in range(spec["n_bars"]):
        lines.append(",".join(("%d" % cols[c][r]) if c == "n" else ("%.15f" % cols[c][r]) for c in h))
    return "\n".join(lines) + "\n"


def run(spec, cols, td, date="20260101"):
    raw_p = os.path.join(td, "raw.csv")
    with open(raw_p, "w", encoding="utf-8", newline="") as f:
        f.write(to_text(spec, cols))
    return C.run_check(spec, raw_p, os.path.join(td, "out"), date)


def trailer(path):
    with open(path, encoding="utf-8") as f:
        return [l for l in f.read().splitlines() if l.startswith("#")]


def rows_of(res, role):
    return [r for r in res["rows"] if r["role"] == role]


def items_1_to_6_pass(res):
    c = res["counts"]
    return (c["n_real"] == 28 and c["n_pass"] == 28 and c["n_err"] == 0 and not res["errs"]
            and all(d["fails_as_required"] for d in res["nc"].values())
            and all(r["result"] == "PASS" for r in rows_of(res, "imp")))


class TestSS3Tooling(unittest.TestCase):

    def test_a_clean_synthetic_full_pass(self):
        """(a) clean synthetic raw: verdict PASS, 28/28 real, all 6 controls detected on required kinds,
        6 IMP rows PASS (5 must_pass + NCH must_fail), 8 floor rows PASS, trailer carries the INFO lines."""
        s = cspec()
        self.assertEqual(s["imp"]["tol"], 1e-9)
        with tempfile.TemporaryDirectory() as td:
            res = run(s, base_cols(s), td)
            self.assertTrue(res["ok"], [r for r in res["rows"] if r["result"] != "PASS" and r["role"] != "neg_control"])
            self.assertEqual((res["counts"]["n_real"], res["counts"]["n_pass"], res["counts"]["n_err"]), (28, 28, 0))
            det = {v: {k: d["detected"][k] for k in d["required"]} for v, d in res["nc"].items()}
            self.assertEqual({v: d["required"] for v, d in res["nc"].items()}, REQUIRED)
            self.assertTrue(all(d["fails_as_required"] for d in res["nc"].values()), det)
            imp = rows_of(res, "imp")
            self.assertEqual(len(imp), 6)
            self.assertTrue(all(r["result"] == "PASS" for r in imp))
            fl = rows_of(res, "floor")
            self.assertEqual(len(fl), 8)
            self.assertTrue(all(r["result"] == "PASS" for r in fl))
            tr = trailer(res["path"])
            self.assertEqual(sum(l.startswith("# O_PEAK") for l in tr), 4)
            self.assertEqual(sum(l.startswith("# O_IMP_RESIDUAL") for l in tr), 4)
            self.assertEqual(sum(l.startswith("# IMP ") for l in tr), 6)
            self.assertFalse(any("FLOOR_GUARD" in l for l in tr))
            self.assertEqual(tr[-1], "# VERDICT: PASS")
            print("  (a) clean synthetic: VERDICT PASS, real 28/28, controls detected %s" % det)
            print("      IMP residuals: %s" % {r["check_id"].split("-", 1)[1]: "%.1e" % r["actual"] for r in imp})
            print("      " + [l for l in tr if l.startswith("# O_PEAK SS3F") or l.startswith("# O_PEAK P10")][0])

    def test_b_one_value_perturbed_imp_fails(self):
        """(b) one real-variant y value +1e-6 at one bar after warmup -> its IMP row FAIL, run FAIL
        (items 1-5 are untouched: the perturbation is invisible to the gain / lag checks)."""
        s = cspec()
        cols = base_cols(s)
        cols["y_P20_s20"][1000] += 1e-6
        with tempfile.TemporaryDirectory() as td:
            res = run(s, cols, td)
            imp = {r["check_id"]: r for r in rows_of(res, "imp")}
            r = imp["SS3F-P20-imp-pass"]
            self.assertEqual(r["result"], "FAIL")
            self.assertGreaterEqual(r["actual"], 9e-7)
            self.assertFalse(res["ok"])
            others = [v for k, v in imp.items() if k != "SS3F-P20-imp-pass"]
            self.assertTrue(all(o["result"] == "PASS" for o in others))
            self.assertEqual(res["counts"]["n_pass"], 28)
            print("  (b) y_P20_s20[1000] += 1e-6 -> IMP P20 residual %.3e > 1e-09 FAIL; other IMP rows PASS; "
                  "real 28/28; VERDICT FAIL" % r["actual"])

    def test_c_nch_equals_code_must_fail_violated(self):
        """(c) NCH column replaced by ss3_code(20) output -> NCH must_fail row FAIL (replay residual 0 <= tol)
        -> run FAIL. Isolated: with NCH removed from must_pass the must_fail row alone fails the run
        (the control is also not detected, a second reason; the IMP row shows the guard itself)."""
        s = cspec()
        cols = build_cols(s, override={"NCH": R.ss3_code(20)})
        with tempfile.TemporaryDirectory() as td:
            res = run(s, cols, td)
            imp = {r["check_id"]: r for r in rows_of(res, "imp")}
            mf = imp["SS3F-NCH-imp-fail"]
            self.assertEqual(mf["result"], "FAIL")
            self.assertLessEqual(mf["actual"], 1e-9)
            self.assertFalse(res["ok"])
            print("  (c) NCH column := ss3_code(20): must_fail residual %.3e <= 1e-09 -> FAIL; must_pass NCH "
                  "residual %.3e -> %s; VERDICT FAIL" % (mf["actual"], imp["SS3F-NCH-imp-pass"]["actual"],
                                                       imp["SS3F-NCH-imp-pass"]["result"]))
        s2 = copy.deepcopy(s)
        del s2["imp"]["must_pass"]["NCH"]
        with tempfile.TemporaryDirectory() as td:
            res2 = run(s2, cols, td)
            imp2 = rows_of(res2, "imp")
            self.assertEqual([(r["check_id"], r["result"]) for r in imp2 if r["result"] == "FAIL"],
                             [("SS3F-NCH-imp-fail", "FAIL")])
            self.assertFalse(res2["ok"])
            print("      isolated (NCH removed from must_pass): only SS3F-NCH-imp-fail FAILs; VERDICT FAIL")

    def test_d_floor_guard_fires_alone(self):
        """(d) P20 real variant generated with a slightly wrong pi (pi_value = PI_ZORRO*(1+eps)), eps chosen so
        max gain |diff| vs ss3_article is ~5e-6 (> 3e-6 floor guard, < 3e-5 gain tol). IMP's model for that
        variant is pointed at the same filter (test-local registry patch). IMP PASS, items 1-6 PASS,
        only item 7 (floor guard) fires."""
        s = cspec()
        book = R.ss3_article(20)

        def gerr(eps):
            return max(abs(R.gain_at(R.ss3_code(20, pi_value=R.PI_ZORRO * (1 + eps)), t) - R.gain_at(book, t))
                       for t in (5, 10, 20, 40, 100))
        lo, hi = -1e-4, 0.0                 # gerr(0) = 8.7e-7 (the PI gap); more negative eps -> larger error
        for _ in range(80):
            mid = (lo + hi) / 2
            if gerr(mid) > 5e-6:
                lo = mid
            else:
                hi = mid
        eps = (lo + hi) / 2
        flt = R.ss3_code(20, pi_value=R.PI_ZORRO * (1 + eps))
        ge = gerr(eps)
        lag_e = abs(R.ramp_lag(flt) - R.ramp_lag(book))
        self.assertTrue(4.9e-6 <= ge <= 5.1e-6, ge)
        self.assertLess(lag_e, 1e-4)
        cols = build_cols(s, override={"P20": flt})
        with mock.patch.dict(R.IMP_MODELS, {"ss3_code(20, PI_ZORRO)": lambda: flt}):
            with tempfile.TemporaryDirectory() as td:
                res = run(s, cols, td)
                tr = trailer(res["path"])
        self.assertTrue(items_1_to_6_pass(res))
        bad = [r["check_id"] for r in rows_of(res, "floor") if r["result"] != "PASS"]
        self.assertEqual(bad, ["SS3F-P20-floor-gain"])
        self.assertFalse(res["ok"])
        self.assertTrue(any("FLOOR_GUARD FAIL: tolerance window invalid" in l for l in tr))
        print("  (d) eps=%.6e (pi_value=PI_ZORRO*(1+eps)): P20 gain err %.3e (floor guard 3e-6, tol 3e-5), "
              "lag err %.3e" % (eps, ge, lag_e))
        print("      items 1-6 PASS (real 28/28, controls detected, IMP all PASS); floor rows FAIL: %s; "
              "VERDICT FAIL; trailer: %s" % (bad, [l for l in tr if "FLOOR_GUARD" in l][0][:70] + "..."))

    def test_unknown_model_is_error_row(self):
        """A model string outside the registry (spec bypassing the generator) -> IMP ERROR row -> run FAIL."""
        s = cspec()
        s["imp"] = dict(s["imp"], must_pass=dict(s["imp"]["must_pass"], P10="ss3_code(11, PI_ZORRO)"))
        with tempfile.TemporaryDirectory() as td:
            res = run(s, base_cols(s), td)
            r = [x for x in rows_of(res, "imp") if x["check_id"] == "SS3F-P10-imp-pass"][0]
            self.assertEqual(r["result"], "ERROR")
            self.assertFalse(res["ok"])
            self.assertGreaterEqual(res["counts"]["n_err"], 1)
            print("  unknown model 'ss3_code(11, PI_ZORRO)' -> IMP row ERROR, n_err=%d, VERDICT FAIL"
                  % res["counts"]["n_err"])

    def test_no_imp_spec_unchanged(self):
        """SS2 / H1 specs have no [imp]: no 'imp' key, no IMP trailer lines, no imp/floor rows."""
        for p in (SS2, os.path.join(HARNESS, "specs", "H1_SuperSmoother2Pole.toml")):
            d = G.to_checker_spec(G.load_spec(p))
            self.assertNotIn("imp", d)
            self.assertEqual(C.imp_trailer(d, [dict(role="real")]), [])
        print("  SS2 and H1 checker specs carry no 'imp'; imp_trailer() returns [] PASS")


class TestSS3Generator(unittest.TestCase):

    def test_ss3_spec_valid_and_lint_clean(self):
        s = toml_spec()
        errs, infos = G.validate_spec(s)
        self.assertEqual(errs, [])
        text, bodies = G.build_script(s)
        self.assertEqual(len(bodies), 5)                       # NCA NCB NCL NCH NC2 (NC1 is a param variant)
        self.assertEqual(G.lint_script(text, bodies), [])
        self.assertIn("series(Price[0], 4)", "".join(bodies))
        self.assertIn("314159.0 / 100000", "".join(bodies))
        print("  SS3 spec valid; %d inline bodies (series(Price[0], 4), integer-built constants) lint clean PASS"
              % len(bodies))

    def test_lint_fires_on_decimal_literal(self):
        """Broken input: the printed literal 1.738 in an inline body -> L_FLOAT32."""
        s = toml_spec()
        s2 = copy.deepcopy(s)
        for v in s2["variants"]:
            if v["id"] == "NCL":
                v["body"] = v["body"].replace("1738.0 / 1000", "1.738")
        text, bodies = G.build_script(s2)
        rules = [r for r, _ in G.lint_script(text, bodies)]
        self.assertIn("L_FLOAT32", rules)
        print("  body with literal 1.738 -> lint %s PASS" % rules)

    def test_refusals(self):
        """Each broken new key is refused with its own code (guard seen to fire)."""
        def codes(mut):
            s = copy.deepcopy(toml_spec())
            mut(s)
            return [c for c, _ in G.validate_spec(s)[0]]
        cases = [
            ("IMP_UNKNOWN_MODEL", lambda s: s["imp"]["must_pass"].update(P10="ss3_code(11, PI_ZORRO)")),
            ("IMP_UNKNOWN_ID", lambda s: s["imp"]["must_pass"].update(ZZZ="ss3_code(10, PI_ZORRO)")),
            ("IMP_TOL_MISSING", lambda s: s["tolerances"].pop("imp")),
            ("SOURCE_MISSING", lambda s: s["tolerances"]["imp"].update(source="no label")),
            ("IMP_BAD", lambda s: s["imp"].update(must_fail=[1])),
            ("CORRECTED_CODE_BAD", lambda s: s["corrected_code"].update(lines="  ")),
            ("CORRECTED_CODE_BAD", lambda s: s["corrected_code"].pop("function")),
            ("LITERAL_INCOMPLETE", lambda s: s["literal_replacements"][0].update(rule="")),
            ("DETECT_BAD_KIND", lambda s: s["detect"]["required"].update(NCA=["gain", "phase"])),
        ]
        for want, mut in cases:
            got = codes(mut)
            self.assertIn(want, got)
            print("  broken spec -> %s fires PASS" % want)
        self.assertEqual(codes(lambda s: None), [])


if __name__ == "__main__":
    unittest.main()
