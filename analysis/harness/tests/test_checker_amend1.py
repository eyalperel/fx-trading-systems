"""Tests for SS2_ArticleFidelity Amendment 1: checker/generator changes G1-G4 and the checker CLI.

Run with the rest of the suite (unittest discover): bash analysis/harness/run_tests.sh
Rule (PROJECT_STATE section 2 rule 4): every new rule has a test that is SEEN TO FAIL on a broken input.
Each test prints what it broke and what it saw.

  G1  [detect.required]: per negative control every listed kind needs >= 1 FAIL check
  G2  [ox]: raw vs reference raw, string-token equality, INFO only
  G3  results trailer carries [literal_info] and the generator's D2 INFO lines
  G4  variant count split real / neg_control; guard-fired run says "NOT evaluated"
  A1.3  an ERROR / guard in ANY variant (real or control) makes the run FAIL
  CLI   python analysis/harness/checker.py <spec.toml> <raw.csv>

Labels: (a) source states, (b) verified here, (c) inference.
Inputs are synthetic: the raw files are simulated with reference.simulate (no Zorro, no .c file read).
"""
import contextlib
import copy
import hashlib
import io
import math
import os
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
import h1_check as H1      # noqa: E402  (read-only import, as test_checker.py)
import reference as R      # noqa: E402

SPEC_PATH = os.path.join(HARNESS, "specs", "SS2_ArticleFidelity.toml")
REF_DEFAULT = "C:/Zorro/Data/H1_SS2P_raw.csv"

# (b) expected detection by [detect.required] in the committed spec (Amendment 1)
WANT_REQUIRED = {"NCA": ["gain"], "NCB": ["gain", "flat"], "NC1": ["gain", "lag"], "NC2": ["gain", "lag"]}


# ----------------------------------------------------------------------------- fixtures
def toml_spec():
    return G.load_spec(SPEC_PATH)


def cspec():
    return G.to_checker_spec(toml_spec())


def _nc2_filter():
    """NC2: cos argument in degrees (H1 NC2 / SS2F ss2f_ss_deg), PI as Zorro's float32 3.14159."""
    r2 = math.sqrt(2.0)
    c1 = math.exp(-r2 * R.PI_ZORRO / 20)
    b1 = 2.0 * c1 * math.cos(r2 * 180.0 / 20)
    c3 = -c1 * c1
    c0 = (1.0 - b1 + c1 * c1) / 2.0
    return R.Filter(b=(c0, c0), a=(b1, c3))


def filters8():
    """The 8 SS2F variants as simulated filters (real variants = the .c with Zorro's PI)."""
    return {"P10": R.ss2_code(10), "P14": R.ss2_code(14), "P20": R.ss2_code(20), "P30": R.ss2_code(30),
            "NCA": R.ss2_code(20, c1_bump=1), "NCB": R.ss2_code(20, in_bump=1),
            "NC1": R.ss2_code(21), "NC2": _nc2_filter()}


_cache = {}


def raw_lines(spec):
    """Header + 3000 rows (list of strings) of a raw CSV for the 8 SS2F variants, simulated once."""
    if "lines" not in _cache:
        x = C.make_inputs(spec)
        ins = C.input_names(spec)
        fl = filters8()
        y = {(v["id"], i): R.simulate(fl[v["id"]], x[i]) for v in spec["variants"] for i in ins}
        lines = [",".join(C.header_of(spec))]
        for k in range(spec["n_bars"]):
            vals = ["%d" % k, "%.15f" % 1.1] + ["%.15f" % x[i][k] for i in ins]
            vals += ["%.15f" % y[(v["id"], i)][k] for v in spec["variants"] for i in ins]
            lines.append(",".join(vals))
        _cache["lines"] = lines
    return list(_cache["lines"])


def set_cell(spec, lines, r, col, new):
    f = lines[r].split(",")
    f[C.header_of(spec).index(col)] = new
    lines[r] = ",".join(f)
    return lines


def text(lines):
    return "\n".join(lines) + "\n"


def write(path, content):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return path


def sha_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read_trailer(path):
    with open(path, encoding="utf-8") as f:
        return [l for l in f.read().splitlines() if l.startswith("#")]


def read_all(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def run_with_ref(spec, lines, td, ref_text=None, name="raw.csv", out="out"):
    """Write raw (+ a reference file equal to ref_text) and run the checker with [ox] pointed at it."""
    raw_p = write(os.path.join(td, name), text(lines))
    s = copy.deepcopy(spec)
    if ref_text is not None:
        ref_p = write(os.path.join(td, "ref_" + name), ref_text)
        s["ox"] = dict(reference_raw=ref_p, reference_sha256=sha_of(ref_p))
    return C.run_check(s, raw_p, os.path.join(td, out), "20260101"), s


# ----------------------------------------------------------------------------- tests
class TestAmendment1(unittest.TestCase):

    # ------------------------------------------------------------------ spec -> checker dict
    def test_spec_carries_amendment_keys(self):
        """T-Spec: the committed SS2F spec gives detect_required / ox / literal_info / info_lines."""
        d = cspec()
        self.assertEqual(d["detect_required"], WANT_REQUIRED)
        self.assertTrue(d["extended_report"])
        self.assertEqual(d["ox"]["reference_sha256"], toml_spec()["ox"]["reference_sha256"])
        self.assertEqual(d["literal_info"]["gain_max"], 1.0720e-4)
        self.assertEqual(len(d["info_lines"]), 7)       # 3 floor lines + 4 control margin lines
        self.assertEqual(len(d["variants"]), 8)
        h = G.to_checker_spec(G.load_spec(os.path.join(HARNESS, "specs", "H1_SuperSmoother2Pole.toml")))
        for k in ("detect_required", "ox", "literal_info", "info_lines", "extended_report"):
            self.assertNotIn(k, h)
        print("  T-Spec SS2F dict has detect_required=%s ox literal_info %d info_lines; the H1 spec dict has "
              "none of the new keys PASS" % (d["detect_required"], len(d["info_lines"])))

    # ------------------------------------------------------------------ G1
    def test_g1_detect_rule(self):
        """T-G1a/a2/b/c/d: a control must fail EVERY listed kind; seen to fail on broken requirements."""
        s = cspec()
        raw = C.load_raw(io.StringIO(text(raw_lines(s))))
        self.assertEqual(C.validate(s, raw), [])
        # T-G1b: as committed -> all four controls detected
        rows, nc = C.evaluate(s, raw)
        det = {v: {k: d["detected"][k] for k in d["required"]} for v, d in nc.items()}
        self.assertTrue(all(d["fails_as_required"] for d in nc.values()), det)
        self.assertEqual({v: d["required"] for v, d in nc.items()}, WANT_REQUIRED)
        print("  T-G1b all listed kinds detected: %s -> fails_as_required all True PASS" % det)
        # T-G1a: NCA fails gain only (its flat error is 0); require gain AND flat -> must NOT pass the rule
        s1 = dict(s, detect_required=dict(WANT_REQUIRED, NCA=["gain", "flat"]))
        _, nc1 = C.evaluate(s1, raw)
        self.assertTrue(nc1["NCA"]["detected"]["gain"] and not nc1["NCA"]["detected"]["flat"])
        self.assertFalse(nc1["NCA"]["fails_as_required"])
        rows1, _ = C.evaluate(s1, raw)
        self.assertFalse(C.verdict(s1, rows1, nc1, [])[0])
        print("  T-G1a NCA fails gain but not flat, flat required -> fails_as_required=False, verdict FAIL "
              "(seen to fire) PASS")
        # T-G1a2: NCA FAILS checks (gain: 9.7x tol) but its lag error 2.8e-4 < tol 1e-3 and flat error is 0;
        # require only lag -> it fails another kind, yet the rule must say not detected
        s2 = dict(s, detect_required=dict(WANT_REQUIRED, NCA=["lag"]))
        rows2, nc2 = C.evaluate(s2, raw)
        self.assertTrue(any(r["result"] == "FAIL" for r in rows2 if r["check_id"].startswith("SS2F-NCA-")))
        self.assertFalse(nc2["NCA"]["fails_as_required"])
        self.assertFalse(C.verdict(s2, rows2, nc2, [])[0])
        print("  T-G1a2 NCA fails gain checks but only lag listed -> fails_as_required=False, verdict FAIL "
              "(a FAIL on a non-listed kind is not enough) PASS")
        # T-G1c: control missing from detect_required -> strict False
        s3 = dict(s, detect_required={k: v for k, v in WANT_REQUIRED.items() if k != "NC1"})
        rows3, nc3 = C.evaluate(s3, raw)
        self.assertFalse(nc3["NC1"]["fails_as_required"])
        self.assertFalse(C.verdict(s3, rows3, nc3, [])[0])
        print("  T-G1c NC1 absent from detect_required -> fails_as_required=False, verdict FAIL PASS")
        # T-G1d: no detect_required -> old rule (any FAIL), required None
        s4 = {k: v for k, v in s.items() if k != "detect_required"}
        _, nc4 = C.evaluate(s4, raw)
        self.assertTrue(all(d["fails_as_required"] and d["required"] is None for d in nc4.values()))
        print("  T-G1d no detect_required -> any-FAIL rule, required=None for all controls (H1 behaviour) PASS")
        # a secretly-correct control (a real filter in a control slot) is still caught
        lines = raw_lines(s)
        a, b = C.header_of(s).index("y_NCA_flat"), C.header_of(s).index("y_P20_flat")
        for r in range(1, len(lines)):
            f = lines[r].split(",")
            f[a:a + 7] = f[b:b + 7]
            lines[r] = ",".join(f)
        raw5 = C.load_raw(io.StringIO(text(lines)))
        rows5, nc5 = C.evaluate(s, raw5)
        self.assertFalse(nc5["NCA"]["fails_as_required"])
        self.assertFalse(C.verdict(s, rows5, nc5, [])[0])
        print("  T-G1c2 NCA replaced by the correct P=20 output -> not detected, verdict FAIL PASS")

    def test_g1_footer_and_verdict_rows(self):
        """T-G1e: per-kind detection in the NC footer line and verdict rows; none for the H1 format."""
        s = cspec()
        with tempfile.TemporaryDirectory() as td:
            res, _ = run_with_ref(s, raw_lines(s), td)
            foot = read_trailer(res["path"])
            ncb = [l for l in foot if l.startswith("# NC NCB ")][0]
            self.assertIn("detected gain=True lag=True flat=True required=gain,flat", ncb)
            nca = [l for l in foot if l.startswith("# NC NCA ")][0]
            self.assertIn("detected gain=True lag=False flat=False required=gain", nca)
            self.assertIn("SS2F-NCB-verdict", read_all(res["path"]))
            self.assertIn("DETECTED:gain,flat", read_all(res["path"]))
            print("  T-G1e footer: '%s' PASS" % ncb[ncb.index("detected"):])
            # broken requirement writes NOT_DETECTED in the verdict row and a FAIL result
            lines = raw_lines(s)
            s2 = dict(s, detect_required=dict(WANT_REQUIRED, NCA=["gain", "flat"]))
            res2, _ = run_with_ref(s2, lines, td, name="raw2.csv", out="out2")
            self.assertFalse(res2["ok"])
            self.assertIn("NOT_DETECTED:flat", read_all(res2["path"]))
            self.assertIn("# VERDICT: FAIL", read_all(res2["path"]))
            print("  T-G1e broken requirement -> verdict row 'NOT_DETECTED:flat', file verdict FAIL PASS")
            # H1 format has no 'detected' text
            res3 = C.run_check(C.h1_spec(), write(os.path.join(td, "h1raw.csv"), H1.fake_zorro_csv()),
                               os.path.join(td, "o3"), "20260101")
            self.assertTrue(all("detected" not in l for l in read_trailer(res3["path"])))
            print("  T-G1e H1-format file: no 'detected' text in the NC lines PASS")

    def test_g1_generator_refusals(self):
        """T-G1f: the generator refuses a broken [detect] / [ox]; the committed spec is accepted."""
        self.assertEqual(G.validate_spec(toml_spec())[0], [])

        def codes(mut):
            s = toml_spec()
            mut(s)
            return [c for c, _ in G.validate_spec(s)[0]]

        def unknown(s):
            s["detect"]["required"]["NCX"] = ["gain"]

        def missing(s):
            del s["detect"]["required"]["NC1"]

        def badkind(s):
            s["detect"]["required"]["NCA"] = ["amplitude"]

        def emptykind(s):
            s["detect"]["required"]["NCA"] = []

        def noreq(s):
            del s["detect"]["required"]

        def noref(s):
            del s["ox"]["reference_raw"]

        def badsha(s):
            s["ox"]["reference_sha256"] = "abc"

        for name, fn, want in (("unknown id", unknown, "DETECT_UNKNOWN_ID"), ("control missing", missing,
                                                                             "DETECT_MISSING"),
                               ("bad kind", badkind, "DETECT_BAD_KIND"), ("empty list", emptykind,
                                                                         "DETECT_BAD_KIND"),
                               ("no [detect.required]", noreq, "DETECT_MISSING"),
                               ("[ox] without reference_raw", noref, "OX_INCOMPLETE"),
                               ("[ox] bad sha256", badsha, "OX_INCOMPLETE")):
            got = codes(fn)
            self.assertIn(want, got, "%s: %s" % (name, got))
            print("  T-G1f %-26s -> refused with %s PASS" % (name, want))
        with self.assertRaises(G.SpecError):
            s = toml_spec()
            unknown(s)
            G.to_checker_spec(s)
        print("  T-G1f to_checker_spec raises SpecError on a refused spec PASS")

    # ------------------------------------------------------------------ G2
    def test_g2_ox(self):
        """T-G2a/b: identical raw -> 0 differences; one altered token -> that column and row."""
        s = cspec()
        base = text(raw_lines(s))
        cols = C.ox_columns(s)
        self.assertEqual(len(cols), 37)                       # n, clock_close, 7 x_, 4 x 7 y_
        with tempfile.TemporaryDirectory() as td:
            ref = write(os.path.join(td, "ref.csv"), base)
            s["ox"] = dict(reference_raw=ref, reference_sha256=sha_of(ref))
            out = C.ox_compare(s, base.encode("utf-8"))
            col_lines = [l for l in out if l.startswith("# OX col=")]
            self.assertEqual(len(col_lines), 37)
            self.assertTrue(all("differing_tokens=0 first_diff_row=none" in l for l in col_lines))
            self.assertIn("columns=37 columns_differing=0 differing_tokens=0", " ".join(out))
            print("  T-G2a identical raw: 37 columns, 0 differing tokens PASS")
            # T-G2b: one altered token (+1e-6) in y_P20_s20 at data row 1234
            lines = raw_lines(s)
            old = float(lines[1235].split(",")[C.header_of(s).index("y_P20_s20")])
            lines = set_cell(s, lines, 1235, "y_P20_s20", "%.15f" % (old + 1e-6))
            out2 = C.ox_compare(s, text(lines).encode("utf-8"))
            bad = [l for l in out2 if l.startswith("# OX col=") and "differing_tokens=0" not in l]
            self.assertEqual(len(bad), 1, bad)
            self.assertIn("col=y_P20_s20 differing_tokens=1 first_diff_row=1234", bad[0])
            self.assertRegex(bad[0], r"max_abs_diff=1\.0\d\de-06")
            self.assertIn("columns_differing=1 differing_tokens=1", " ".join(out2))
            print("  T-G2b one altered token -> %s PASS" % bad[0][len("# OX "):][:90])
            # A5: shorter file -> compared to the shorter length, INFO line for the difference
            out3 = C.ox_compare(s, text(lines[:2001]).encode("utf-8"))
            self.assertTrue(any("row count differs: under test 2000, reference 3000 (compared the first 2000)"
                                in l for l in out3), out3[:3])
            print("  T-G2 shorter raw (2000 rows): 'row count differs ... compared the first 2000' PASS")
            # a non-numeric differing token must not crash the block (max_abs_diff=nan)
            lines = set_cell(s, raw_lines(s), 5, "y_P10_flat", "-1.#IND00000000000")
            out4 = C.ox_compare(s, text(lines).encode("utf-8"))
            self.assertTrue(any("col=y_P10_flat differing_tokens=1 first_diff_row=4" in l and "nan" in l
                                for l in out4))
            print("  T-G2 unparseable token: counted as a difference, max_abs_diff=nan, no crash PASS")

    def test_g2_not_available_and_verdict_unchanged(self):
        """T-G2c/d: missing reference, wrong sha256, dropped column -> 'OX not available'; the verdict never
        changes; A4: OX also runs when a guard fired."""
        s = cspec()
        base_lines = raw_lines(s)
        with tempfile.TemporaryDirectory() as td:
            s_no = {k: v for k, v in s.items() if k != "ox"}
            res_no = C.run_check(s_no, write(os.path.join(td, "raw0.csv"), text(base_lines)),
                                 os.path.join(td, "o0"), "20260101")
            self.assertTrue(res_no["ok"])
            # missing reference
            sm = dict(s, ox=dict(reference_raw=os.path.join(td, "nope.csv"), reference_sha256="0" * 64))
            r1 = C.run_check(sm, os.path.join(td, "raw0.csv"), os.path.join(td, "o1"), "20260101")
            self.assertTrue(r1["ox"][0].startswith("# OX not available: reference file not found"))
            self.assertEqual(r1["ok"], res_no["ok"])
            self.assertIn("# OX not available: reference file not found", read_all(r1["path"]))
            print("  T-G2c missing reference -> '%s'; verdict unchanged (%s) PASS"
                  % (r1["ox"][0][2:70], "PASS" if r1["ok"] else "FAIL"))
            # wrong sha256
            ref = write(os.path.join(td, "ref.csv"), text(base_lines))
            sw = dict(s, ox=dict(reference_raw=ref, reference_sha256="f" * 64))
            r2 = C.run_check(sw, os.path.join(td, "raw0.csv"), os.path.join(td, "o2"), "20260101")
            self.assertIn("reference sha256", r2["ox"][0])
            self.assertTrue(r2["ox"][0].startswith("# OX not available"))
            self.assertEqual(r2["ok"], res_no["ok"])
            print("  T-G2c wrong sha256 -> 'OX not available: reference sha256 ... differs'; verdict unchanged PASS")
            # reference lacking a column
            noy = text([",".join(c for c in l.split(",")[:-1]) for l in base_lines])
            ref2 = write(os.path.join(td, "ref2.csv"), noy)
            sc = dict(s, ox=dict(reference_raw=ref2, reference_sha256=sha_of(ref2)))
            out = C.ox_compare(sc, text(base_lines).encode("utf-8"))
            self.assertNotIn("not available", out[0])
            self.assertGreater(len(out), 30)
            print("  T-G2c reference without y_NC2_ramp (not a listed column) -> still compared, %d OX lines PASS"
                  % len(out))
            # reference lacking a LISTED column: drop x_s20
            k = C.header_of(s).index("x_s20")
            nox = text([",".join(c for j, c in enumerate(l.split(",")) if j != k) for l in base_lines])
            ref3 = write(os.path.join(td, "ref3.csv"), nox)
            sd = dict(s, ox=dict(reference_raw=ref3, reference_sha256=sha_of(ref3)))
            out = C.ox_compare(sd, text(base_lines).encode("utf-8"))
            self.assertEqual(out, ["# OX not available: column x_s20 missing in the reference file"])
            print("  T-G2c reference without listed column x_s20 -> '%s' PASS" % out[0][2:])
            # T-G2d: altered tokens do not change PASS/FAIL (verdict equals the run without [ox])
            lines = set_cell(s, raw_lines(s), 1235, "y_P20_s20", "%.15f" % 9.0)    # not a guard column
            ref_ok = write(os.path.join(td, "ref_ok.csv"), text(base_lines))
            sx = dict(s, ox=dict(reference_raw=ref_ok, reference_sha256=sha_of(ref_ok)))
            raw_p = write(os.path.join(td, "raw_alt.csv"), text(lines))
            r4 = C.run_check(sx, raw_p, os.path.join(td, "o4"), "20260101")
            r4_no = C.run_check(s_no, raw_p, os.path.join(td, "o4b"), "20260101")
            self.assertTrue(any("columns_differing=1" in l for l in r4["ox"]))
            self.assertEqual(r4["ok"], r4_no["ok"])
            self.assertEqual(r4["counts"], r4_no["counts"])
            print("  T-G2d OX reports 1 differing column; verdict and counts identical to the run without [ox] "
                  "(%s) PASS" % ("PASS" if r4["ok"] else "FAIL"))
            # A4: a guard fired (clock 0) -> OX is still computed
            glines = set_cell(s, raw_lines(s), 10, "clock_close", "0.000000000000000")
            graw = write(os.path.join(td, "raw_g.csv"), text(glines))
            r5 = C.run_check(sx, graw, os.path.join(td, "o5"), "20260101")
            self.assertIn("G_CLOCK", [g for g, _ in r5["errs"]])
            self.assertFalse(r5["ok"])
            self.assertTrue(any("col=clock_close differing_tokens=1 first_diff_row=9" in l for l in r5["ox"]))
            print("  T-G2 guard fired (G_CLOCK): run FAIL, OX still reports clock_close row 9 PASS")

    def test_g2_real_h1_reference(self):
        """T-G2e: the registered reference file exists and matches the registered sha256 (skip if absent)."""
        s = cspec()
        ref = s["ox"]["reference_raw"]
        if not os.path.isfile(ref):
            self.skipTest("T-G2e not available: reference file not found: %s" % ref)
        out = C.ox_compare(s, text(raw_lines(s)).encode("utf-8"))
        self.assertNotIn("not available", out[0])
        self.assertIn("sha256 %s verified" % s["ox"]["reference_sha256"], out[0])
        n_diff = [l for l in out if l.startswith("# OX col=") and "differing_tokens=0" not in l]
        print("  T-G2e registered H1 reference found, sha256 verified; simulated raw vs it: %d of 37 columns "
              "differ (expected: simulated is not Zorro output) PASS" % len(n_diff))

    # ------------------------------------------------------------------ G3 / G4
    def test_g3_g4_trailer(self):
        """T-G3 / T-G4a: literal_info, D2 lines, OX block and variant split in the SS2F-style results."""
        s = cspec()
        infos = G.validate_spec(toml_spec())[1]
        with tempfile.TemporaryDirectory() as td:
            res, s_ox = run_with_ref(s, raw_lines(s), td, ref_text=text(raw_lines(s)))
            foot = read_trailer(res["path"])
            blob = "\n".join(foot)
            self.assertIn("# literal_info", blob)
            self.assertIn("gain_max=%s lag_max=%s" % (s["literal_info"]["gain_max"], s["literal_info"]["lag_max"]),
                          blob)
            self.assertEqual(len(infos), 7)
            for line in infos:
                self.assertIn("# " + line, foot)
            self.assertTrue(any(l.startswith("# INFO D2 floor gain:") for l in foot))
            self.assertTrue(any(l.startswith("# INFO D2 margin NCB:") for l in foot))
            self.assertTrue(any(l.startswith("# OX summary:") for l in foot))
            print("  T-G3 trailer holds literal_info (gain_max=%s lag_max=%s), %d D2 lines, OX block PASS"
                  % (s["literal_info"]["gain_max"], s["literal_info"]["lag_max"], len(infos)))
            self.assertIn("# batch=SS2_ArticleFidelity variants_run=8 real=4 neg_control=4", foot)
            print("  T-G4a clean run: '# batch=SS2_ArticleFidelity variants_run=8 real=4 neg_control=4' PASS")
            # T-G3b: the H1 format has none of this
            res_h = C.run_check(C.h1_spec(), write(os.path.join(td, "h1.csv"), H1.fake_zorro_csv()),
                                os.path.join(td, "oh"), "20260101")
            fh = read_trailer(res_h["path"])
            self.assertTrue(all(not (l.startswith("# literal_info") or "D2" in l or l.startswith("# OX"))
                                for l in fh))
            self.assertIn("# batch=H1_SuperSmoother2Pole variants_run=6", fh)
            print("  T-G3b H1-format file: no literal_info / D2 / OX lines, plain 'variants_run=6' PASS")

    def test_g4_guard_run_wording(self):
        """T-G4b: a guard-fired run says the variants were NOT evaluated, never a bare variants_run=0."""
        s = cspec()
        with tempfile.TemporaryDirectory() as td:
            for gid, fn in (("G_CLOCK", lambda L: set_cell(s, L, 10, "clock_close", "0.000000000000000")),
                            ("G_NONFINITE", lambda L: set_cell(s, L, 700, "y_NC1_s10", "inf"))):
                res, _ = run_with_ref(s, fn(raw_lines(s)), td, name="g_%s.csv" % gid, out="o_" + gid)
                self.assertIn(gid, [g for g, _ in res["errs"]])
                self.assertFalse(res["ok"])
                body = read_all(res["path"])
                foot = read_trailer(res["path"])
                self.assertIn("variants NOT evaluated (guard fired: ", body)
                self.assertNotIn("variants_run=0", body)
                self.assertTrue(any("variants_defined=8 real=4 neg_control=4" in l for l in foot))
                self.assertTrue(any(l.startswith("# batch=") and gid in l for l in foot))
                print("  T-G4b %-12s -> '%s' PASS" % (gid, [l for l in foot if "NOT evaluated" in l][0][:96]))
            # the H1 format keeps its old wording (gated on extended_report)
            res_h = C.run_check(C.h1_spec(), write(os.path.join(td, "hb.csv"),
                                                   H1.fake_zorro_csv(mutate=lambda L: L[:-1])),
                                os.path.join(td, "oh"), "20260101")
            self.assertIn("# batch=H1_SuperSmoother2Pole variants_run=0", read_trailer(res_h["path"]))
            print("  T-G4b H1-format guard run keeps the old '# batch=... variants_run=0' line PASS")

    # ------------------------------------------------------------------ A1.3
    def test_a13_error_in_any_variant_fails(self):
        """T-A13: a non-finite value in a negative-control column, or in a real column, makes the run FAIL."""
        s = cspec()
        with tempfile.TemporaryDirectory() as td:
            for col, label in (("y_NCA_s5", "control"), ("y_P14_ramp", "real")):
                res, _ = run_with_ref(s, set_cell(s, raw_lines(s), 700, col, "inf"), td,
                                      name="a13_%s.csv" % label, out="o_" + label)
                self.assertFalse(res["ok"])
                self.assertIn("G_NONFINITE", [g for g, _ in res["errs"]])
                self.assertIn("SS2F-GUARD-G_NONFINITE", read_all(res["path"]))
                self.assertGreater(res["counts"]["n_err"], 0)
                print("  T-A13 'inf' in %s column %s -> guard ERROR row, n_err=%d, run FAIL PASS"
                      % (label, col, res["counts"]["n_err"]))
            # check-level ERROR (non-finite measurement) in a control row also fails the verdict
            rows, nc = C.evaluate(s, C.load_raw(io.StringIO(text(raw_lines(s)))))
            rows = [dict(r, result="ERROR") if r["check_id"] == "SS2F-NC1-gain-T5" else r for r in rows]
            ok, c = C.verdict(s, rows, nc, [])
            self.assertFalse(ok)
            self.assertEqual(c["n_err"], 1)
            print("  T-A13 one ERROR row in a control variant (NC1) -> verdict FAIL, n_err=1 PASS")

    # ------------------------------------------------------------------ dry run
    def test_spec2_dry_run(self):
        """T-Spec2: the committed SS2F spec against simulated output of all 8 variants (dry run, not Zorro)."""
        s = cspec()
        with tempfile.TemporaryDirectory() as td:
            ref = write(os.path.join(td, "ref.csv"), text(raw_lines(s)))
            s["ox"] = dict(reference_raw=ref, reference_sha256=sha_of(ref))
            res = C.run_check(s, write(os.path.join(td, "raw.csv"), text(raw_lines(s))),
                              os.path.join(td, "out"), "20260101")
            self.assertEqual(res["errs"], [])
            c = res["counts"]
            self.assertEqual((c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]), (28, 28, 0, 0))
            for vid, d in res["nc"].items():
                self.assertTrue(d["fails_as_required"], vid)
                for k in WANT_REQUIRED[vid]:
                    self.assertTrue(d["detected"][k], (vid, k))
            self.assertTrue(res["ok"])
            kinds = {v: ",".join(k for k in ("gain", "lag", "flat") if d["detected"][k])
                     for v, d in res["nc"].items()}
            print("  T-Spec2 dry run VERDICT PASS: real 28/28 PASS; detected kinds per control: %s; required %s; "
                  "variants_run=8 real=4 neg_control=4" % (kinds, WANT_REQUIRED))
            self.assertIn("# VERDICT: PASS", read_trailer(res["path"]))

    # ------------------------------------------------------------------ CLI
    def test_cli(self):
        """T-CLI: checker.main refuses a broken spec / missing raw, runs a good one, never overwrites."""
        s = cspec()
        with tempfile.TemporaryDirectory() as td:
            raw_p = write(os.path.join(td, "raw.csv"), text(raw_lines(s)))
            out_dir = os.path.join(td, "res")
            with open(SPEC_PATH, encoding="utf-8") as f:
                spec_text = f.read()
            # broken spec: [detect.required] NCA renamed -> unknown id + control missing
            broken = write(os.path.join(td, "broken.toml"), spec_text.replace("NCA = [\"gain\"]", "NCX = [\"gain\"]"))
            self.assertNotEqual(spec_text, read_all(broken))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = C.main([broken, raw_p, "--out-dir", out_dir, "--date", "20260101"])
            self.assertEqual(rc, 2)
            self.assertIn("SPEC REFUSED DETECT_UNKNOWN_ID", buf.getvalue())
            self.assertIn("SPEC REFUSED DETECT_MISSING", buf.getvalue())
            self.assertFalse(os.path.isdir(out_dir) and os.listdir(out_dir))
            print("  T-CLI broken spec -> exit 2, 'SPEC REFUSED DETECT_UNKNOWN_ID / DETECT_MISSING', no results "
                  "file written PASS")
            # missing raw
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = C.main([SPEC_PATH, os.path.join(td, "nope.csv"), "--out-dir", out_dir])
            self.assertEqual(rc, 2)
            self.assertIn("REFUSED: raw file not found", buf.getvalue())
            print("  T-CLI missing raw file -> exit 2, 'REFUSED: raw file not found' PASS")
            # good run in-process: PASS verdict is expected (simulated clean data); exit code 0
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = C.main([SPEC_PATH, raw_p, "--out-dir", out_dir, "--date", "20260101"])
            out = buf.getvalue()
            self.assertEqual(rc, 0, out)
            self.assertIn("VERDICT: PASS", out)
            p1 = os.path.join(out_dir, "SS2_ArticleFidelity_20260101.csv")
            self.assertIn("results: " + p1, out)
            self.assertTrue(os.path.isfile(p1))
            # second run: exclusive create -> new _run2 file, the first is untouched
            before = read_all(p1)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = C.main([SPEC_PATH, raw_p, "--out-dir", out_dir, "--date", "20260101"])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.isfile(os.path.join(out_dir, "SS2_ArticleFidelity_20260101_run2.csv")))
            self.assertEqual(read_all(p1), before)
            print("  T-CLI good run -> exit 0, verdict PASS, results path printed; second run writes _run2, first "
                  "file unchanged PASS")
            # a failing run exits 1 (a control replaced by the correct output)
            lines = raw_lines(s)
            a, b = C.header_of(s).index("y_NCA_flat"), C.header_of(s).index("y_P20_flat")
            for r in range(1, len(lines)):
                f = lines[r].split(",")
                f[a:a + 7] = f[b:b + 7]
                lines[r] = ",".join(f)
            bad_raw = write(os.path.join(td, "bad_raw.csv"), text(lines))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = C.main([SPEC_PATH, bad_raw, "--out-dir", os.path.join(td, "res2"), "--date", "20260101"])
            self.assertEqual(rc, 1)
            self.assertIn("VERDICT: FAIL", buf.getvalue())
            print("  T-CLI control that does not fail -> exit 1, 'VERDICT: FAIL' PASS")
            # real command line: python analysis/harness/checker.py <spec> <raw>
            r = subprocess.run([sys.executable, os.path.join(HARNESS, "checker.py"), SPEC_PATH, raw_p,
                                "--out-dir", os.path.join(td, "res3"), "--date", "20260101"],
                               capture_output=True, text=True, encoding="utf-8", cwd=td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("VERDICT: PASS", r.stdout)
            print("  T-CLI 'python checker.py <spec> <raw>' as a subprocess -> exit 0, VERDICT: PASS PASS")

    # ------------------------------------------------------------------ Amendment 2: effect corrections
    def test_effect_corrections(self):
        """T-EC: [effect_corrections.<id>] supersedes single quantities of [variants.effect] in the INFO
        margin lines (reporting only); refused when malformed; absent -> lines as before (H1)."""
        def margin(infos, vid):
            return [l for l in infos if l.startswith("INFO D2 margin %s:" % vid)][0]

        t = toml_spec()
        infos = G.validate_spec(t)[1]
        ncb = margin(infos, "NCB")
        self.assertIn("lag 3.53e+04x", ncb)
        self.assertTrue(ncb.endswith("(corrected: lag, Amendment 2)"), ncb)
        self.assertIn("gain 84.3x", ncb)                       # uncorrected quantities keep [variants.effect]
        self.assertIn("flat 2.78e+06x", ncb)
        print("  T-EC NCB: %s PASS" % ncb[len("INFO D2 margin "):])
        want = {"NCA": "INFO D2 margin NCA: error/tolerance gain 32.4x, lag 0.276x, flat 0x -> 10x margin met (gain)",
                "NC1": "INFO D2 margin NC1: error/tolerance gain 1.17e+03x, lag 223x, flat 0x -> 10x margin met "
                       "(gain)",
                "NC2": "INFO D2 margin NC2: error/tolerance gain 5.77e+03x, lag 1.39e+03x, flat 0x -> 10x margin "
                       "met (gain)"}
        for vid, line in want.items():
            self.assertEqual(margin(infos, vid), line)
        print("  T-EC NCA, NC1, NC2 lines unchanged (exact, no 'corrected') PASS")
        # counter-check: without the correction the old (wrong) number shows, so the test can fail
        t0 = toml_spec()
        del t0["effect_corrections"]
        old = margin(G.validate_spec(t0)[1], "NCB")
        self.assertIn("lag 0.0036x", old)
        self.assertNotIn("corrected", old)
        print("  T-EC correction removed -> NCB shows 'lag 0.0036x', no 'corrected' text (test can fail) PASS")
        # the INFO lines reach the checker dict and the results trailer; the verdict logic is untouched
        d = G.to_checker_spec(toml_spec())
        self.assertIn(ncb, d["info_lines"])
        # refusals
        def codes(mut):
            x = toml_spec()
            mut(x)
            return [c for c, _ in G.validate_spec(x)[0]]

        cases = (
            ("unknown id", lambda x: x["effect_corrections"].update(
                NCX=dict(lag=1.0, source="(b) test")), "EFFECT_CORRECTION_UNKNOWN_ID"),
            ("real-variant id", lambda x: x["effect_corrections"].update(
                P10=dict(lag=1.0, source="(b) test")), "EFFECT_CORRECTION_UNKNOWN_ID"),
            ("bad quantity", lambda x: x["effect_corrections"]["NCB"].update(amplitude=1.0),
             "EFFECT_CORRECTION_BAD"),
            ("non-numeric value", lambda x: x["effect_corrections"]["NCB"].update(lag="35.3"),
             "EFFECT_CORRECTION_BAD"),
            ("no source", lambda x: x["effect_corrections"]["NCB"].pop("source"), "EFFECT_CORRECTION_BAD"),
            ("source without label", lambda x: x["effect_corrections"]["NCB"].update(source="measured"),
             "EFFECT_CORRECTION_BAD"),
            ("no quantity", lambda x: x["effect_corrections"].update(
                NCB=dict(source="(b) test")), "EFFECT_CORRECTION_BAD"))
        for name, fn, want_code in cases:
            got = codes(fn)
            self.assertIn(want_code, got, "%s: %s" % (name, got))
            print("  T-EC %-22s -> refused with %s PASS" % (name, want_code))
        x = toml_spec()
        x["effect_corrections"]["NCB"]["amplitude"] = 1.0
        with self.assertRaises(G.SpecError):
            G.to_checker_spec(x)
        # H1 (no [effect_corrections]): INFO lines identical to those printed before the change
        h1 = G.load_spec(os.path.join(HARNESS, "specs", "H1_SuperSmoother2Pole.toml"))
        self.assertNotIn("effect_corrections", h1)
        self.assertEqual(G.validate_spec(h1)[1], [
            "INFO D2 floor gain: floor 6.185e-07 x10 = 6.185e-06 <= tolerance 1.000e-04 -> window ok",
            "INFO D2 floor lag: floor 5.429e-06 x10 = 5.429e-05 <= tolerance 1.000e-03 -> window ok",
            "INFO D2 floor flat: floor 2.200e-16 x10 = 2.200e-15 <= tolerance 1.000e-09 -> window ok",
            "INFO D2 margin NC1: error/tolerance gain 351x, lag 223x, flat 0x -> 10x margin met (gain)",
            "INFO D2 margin NC2: error/tolerance gain 1.73e+03x, lag 1.39e+03x, flat 0x -> 10x margin met (gain)"])
        print("  T-EC H1 spec: 5 INFO lines identical to the pre-change output PASS")


if __name__ == "__main__":
    unittest.main()
