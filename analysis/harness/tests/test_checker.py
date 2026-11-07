"""Self-test for analysis/harness/checker.py (STEP2_HANDOFF.md, Stage 2, checks C1-C8).

Run:  python -m unittest discover -s analysis/harness/tests -v
h1_check.py is imported read-only (C2, C6); no H1 file is modified.
C3 reads the Zorro raw file in place (never copied). Path override: environment variable
H1_RAW_CSV. If the file is missing or its sha256 differs, C3 is skipped ("C3 not available"),
which is not a FAIL.
Lines starting 'INFO' are reported values, never PASS/FAIL.
"""
import csv
import hashlib
import io
import math
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.join(HERE, "..")
sys.path.insert(0, HARNESS)
import checker as C        # noqa: E402
import h1_check as H1      # noqa: E402  (read-only import)
import reference as R      # noqa: E402

RUN2_RESULTS = os.path.join(HARNESS, "results", "H1_SuperSmoother2Pole_20261105_run2.csv")
RAW_DEFAULT = "C:/Zorro/Data/H1_SS2P_raw.csv"
# sha256 recorded in H1_SuperSmoother2Pole_20261105_run2.csv line 49 (b)
RAW_SHA = "e8ffc04300e8ffb02221917d08f245aa492d410367f9f7d51ba5601b040c5a6f"

SPEC = C.h1_spec()
INS = C.input_names(SPEC)


# ----------------------------------------------------------------------------- helpers
_sim_cache = {}


def _sim(f, x, key):
    k = (f.b, f.a, key)
    if k not in _sim_cache:
        _sim_cache[k] = R.simulate(f, x)
    return _sim_cache[k]


def build_csv(spec, filters, mutate=None):
    """Text of a raw CSV as the Zorro harness would write it, from reference.simulate."""
    x = C.make_inputs(spec)
    ins = C.input_names(spec)
    y = {(v["id"], i): _sim(filters[v["id"]], x[i], i) for v in spec["variants"] for i in ins}
    lines = [",".join(C.header_of(spec))]
    for k in range(spec["n_bars"]):
        vals = ["%d" % k, "%.15f" % 1.1] + ["%.15f" % x[i][k] for i in ins]
        vals += ["%.15f" % y[(v["id"], i)][k] for v in spec["variants"] for i in ins]
        lines.append(",".join(vals))
    if mutate:
        lines = mutate(lines)
    return "\n".join(lines) + "\n"


def parse_results(path):
    """-> (data rows as dicts, footer lines starting with '#')."""
    with open(path, encoding="utf-8") as f:
        text = f.read().splitlines()
    foot = [l for l in text if l.startswith("#")]
    data = [l for l in text if not l.startswith("#") and not l.startswith('"#')]
    return list(csv.DictReader(data)), foot


def row_cell(lines, r, col, new):
    f = lines[r].split(",")
    f[C.header_of(SPEC).index(col)] = new
    lines[r] = ",".join(f)
    return lines


def _drop_col(lines):
    k = C.header_of(SPEC).index("y_P20_s20")
    return [",".join(c for j, c in enumerate(l.split(",")) if j != k) for l in lines]


def _dup_n(lines):
    lines[101] = lines[100]
    return lines


def _ragged(lines):
    lines[300] = lines[300].rsplit(",", 1)[0]
    return lines


# guard id -> (description, mutation of the list of lines or of the whole text)
H = C.header_of(SPEC)
MUTATIONS = [
    ("G_EMPTY", "empty file", lambda L: [], True),
    ("G_RAGGED", "row 300 missing its last field", _ragged, False),
    ("G_UNPARSEABLE", "MSVC NaN token", lambda L: row_cell(L, 700, "y_P20_s10", "-1.#IND00000000000"), False),
    ("G_NONFINITE", "'inf' value", lambda L: row_cell(L, 700, "y_P14_ramp", "inf"), False),
    ("G_HEADER", "a column missing", _drop_col, False),
    ("G_ROWCOUNT", "file ends at 2999 rows", lambda L: L[:-1], False),
    ("G_N_REPEAT", "n repeated (x[n] fed twice)", _dup_n, False),
    ("G_N_GAP", "row deleted (x[n] skipped)", lambda L: L[:50] + L[51:], False),
    ("G_N_SEQUENCE", "last n = -1 (no repeat, no gap, not 0..N-1)",
     lambda L: row_cell(L, len(L) - 1, "n", "-1"), False),
    ("G_CLOCK", "clock_close = 0 (no data / wrong asset)", lambda L: row_cell(L, 10, "clock_close", "0.000000000000000"), False),
    ("G_INPUT_MISMATCH", "x_s20 corrupted by 1e-6",
     lambda L: row_cell(L, 400, "x_s20", "%.15f" % (float(L[400].split(",")[H.index("x_s20")]) + 1e-6)), False),
]


def h1_text(mutate=None, y_override=None):
    t = H1.fake_zorro_csv(y_override=y_override, mutate=mutate)
    return t


def mutated_h1_text(fn, whole_text):
    if whole_text:
        return ""
    return H1.fake_zorro_csv(mutate=fn)


# ----------------------------------------------------------------------------- tests
class TestChecker(unittest.TestCase):

    # ------------------------------------------------------------------ C1
    def test_c1_measurement_accuracy(self):
        """C1: checker measures reference.simulate output vs reference analytic, tol 1e-9."""
        x = C.make_inputs(SPEC)
        cases = [("ss2_code(pi) P=%d" % p, R.ss2_code(p, pi_value=math.pi)) for p in (10, 14, 20, 30)]
        cases.append(("EMA(0.4)", R.ema(0.4)))
        worst = 0.0
        for name, f in cases:
            yv = {i: R.simulate(f, x[i]) for i in INS}
            flat, gains, lag = C.measure(SPEC, x, yv)
            for t, g in zip(SPEC["ts"], gains):
                d = abs(g - R.gain_at(f, t))
                worst = max(worst, d)
                self.assertLessEqual(d, 1e-9, "%s gain T=%d" % (name, t))
            dl = abs(lag - R.ramp_lag(f))
            worst = max(worst, dl)
            self.assertLessEqual(dl, 1e-9, name + " lag")
            print("  C1 %-18s worst gain diff %.3e  lag diff %.3e  PASS"
                  % (name, max(abs(g - R.gain_at(f, t)) for t, g in zip(SPEC["ts"], gains)), dl))
        print("  INFO C1 worst checker measurement error %.3e (checker term of the D2 floor)" % worst)

    # ------------------------------------------------------------------ C2
    def _compare_with_h1(self, text, tag):
        rh = H1.load_raw(io.StringIO(text))
        rc = C.load_raw(io.StringIO(text))
        self.assertEqual(H1.validate(rh), [], tag)
        self.assertEqual(C.validate(SPEC, rc), [], tag)
        rows_h, nc_h, _, _ = H1.evaluate(rh)
        rows_c, nc_c = C.evaluate(SPEC, rc)
        by_id = {r["check_id"]: r for r in rows_c}
        self.assertEqual(len(rows_h), len(rows_c), tag)
        x = H1.make_inputs()
        worst = 0.0
        for rh_ in rows_h:
            rc_ = by_id[rh_["check_id"]]
            self.assertEqual(rh_["result"], rc_["result"], "%s %s" % (tag, rh_["check_id"]))
            self.assertEqual(rh_["actual"], "%.6f" % rc_["actual"], rh_["check_id"])
            self.assertEqual(rh_["expected"], "%.6f" % rc_["expected"], rh_["check_id"])
        for v in H1.VARIANTS:
            yv = {i: rh.cols["y_%s_%s" % (v, i)] for i in H1.INPUTS}
            f_, g_, l_ = H1.measure(x, yv)
            cid = lambda s: by_id["H1-%s-%s" % (v, s)]["actual"]   # noqa: E731
            vals = [(f_, cid("flat"))] + [(g, cid("gain-T%d" % t)) for t, g in zip(H1.TS, g_)] \
                + [(l_, cid("ramp-lag"))]
            for a, b in vals:
                worst = max(worst, abs(a - b))
        self.assertLessEqual(worst, 1e-12, tag)
        for v in ("NC1", "NC2"):
            self.assertEqual(nc_h[v], nc_c[v]["fails_as_required"], tag + " " + v)
        return worst, len(rows_c)

    def test_c2_same_verdicts_as_h1(self):
        """C2: checker rows vs h1_check.evaluate() on clean and altered fake files; guard ids
        vs h1_check.validate() on every mutation. Values equal to 1e-12, PASS/FAIL identical."""
        worst, n = self._compare_with_h1(h1_text(), "clean")
        print("  C2 clean file: %d rows, PASS/FAIL identical, worst value diff %.3e PASS" % (n, worst))
        x = H1.make_inputs()
        wrong = {("P20", i): H1.simulate(x[i], 21) for i in H1.INPUTS}
        w2, _ = self._compare_with_h1(h1_text(y_override=wrong), "P20 slot = P21")
        fine = {("NC1", i): H1.simulate(x[i], 20) for i in H1.INPUTS}
        w3, _ = self._compare_with_h1(h1_text(y_override=fine), "NC1 secretly correct")
        print("  C2 altered filters (P20 slot=P21; NC1 secretly correct): identical, worst %.3e PASS"
              % max(w2, w3))
        # the altered files must change verdicts (else the comparison could not fail)
        rows_c, _ = C.evaluate(SPEC, C.load_raw(io.StringIO(h1_text(y_override=wrong))))
        self.assertTrue(any(r["result"] == "FAIL" for r in rows_c if r["role"] == "real"))
        # guard ids: checker == H1 on every mutation that H1 has (the 3 new ones have no H1 twin)
        for gid, desc, fn, whole in MUTATIONS:
            if gid in ("G_EMPTY", "G_RAGGED", "G_N_SEQUENCE"):
                continue
            text = H1.fake_zorro_csv(mutate=fn)
            eh = [g for g, _ in H1.validate(H1.load_raw(io.StringIO(text)))]
            ec = [g for g, _ in C.validate(SPEC, C.load_raw(io.StringIO(text)))]
            self.assertEqual(eh, ec, gid)
            self.assertIn(gid, ec)
        print("  C2 guard ids identical to h1_check.validate on 8 shared mutations PASS")

    # ------------------------------------------------------------------ C3
    def test_c3_h1_run2_reproduction(self):
        """C3: checker on H1's real Zorro raw file vs H1 run-2 results, exact at %.6f."""
        path = os.environ.get("H1_RAW_CSV", RAW_DEFAULT)
        if not os.path.isfile(path):
            self.skipTest("C3 not available: raw file not found: %s" % path)
        with open(path, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        if sha != RAW_SHA:
            self.skipTest("C3 not available: sha256 differs (%s != %s)" % (sha, RAW_SHA))
        if not os.path.isfile(RUN2_RESULTS):
            self.skipTest("C3 not available: run-2 results file not found: %s" % RUN2_RESULTS)
        with open(path, "rb") as f:
            raw = C.load_raw(io.StringIO(f.read().decode("utf-8", errors="replace")))
        self.assertEqual(C.validate(SPEC, raw), [], "guards on the real raw file")
        rows, nc = C.evaluate(SPEC, raw)
        stored, _ = parse_results(RUN2_RESULTS)
        by_id = {r["check_id"]: r for r in rows}
        n_cmp = 0
        for s in stored:
            if s["check_id"].endswith("-verdict"):
                vid = s["check_id"].split("-")[1]
                self.assertEqual(s["actual"], "FAILS_AS_REQUIRED" if nc[vid]["fails_as_required"] else "DID_NOT_FAIL")
                self.assertEqual(s["result"], "PASS")
                continue
            r = by_id[s["check_id"]]
            self.assertEqual(s["expected"], "%.6f" % r["expected"], s["check_id"])
            self.assertEqual(s["actual"], "%.6f" % r["actual"], s["check_id"])
            self.assertEqual(s["result"], r["result"], s["check_id"])
            self.assertEqual(s["tolerance"], "%g" % r["tolerance"], s["check_id"])
            n_cmp += 1
        self.assertEqual(n_cmp, len(rows))
        real = [r for r in rows if r["role"] == "real"]
        self.assertEqual((len(real), sum(r["result"] == "PASS" for r in real)), (28, 28))
        self.assertTrue(nc["NC1"]["fails_as_required"] and nc["NC2"]["fails_as_required"])
        print("  C3 H1 run 2 reproduced: %d rows equal at %%.6f; 28/28 PASS; NC1+NC2 fail as required PASS"
              % n_cmp)

    # ------------------------------------------------------------------ C4 / C5
    def test_c4_each_guard_fires_and_writes_error_row(self):
        """C4: each of the eleven guards fires on its own broken file and writes an ERROR row."""
        self.assertEqual(len(MUTATIONS), 11)
        with tempfile.TemporaryDirectory() as td:
            for gid, desc, fn, whole in MUTATIONS:
                text = "" if whole else H1.fake_zorro_csv(mutate=fn)
                rawp = os.path.join(td, "raw_%s.csv" % gid)
                with open(rawp, "w", encoding="utf-8", newline="") as f:
                    f.write(text)
                res = C.run_check(SPEC, rawp, os.path.join(td, "out_" + gid), "20260101")
                ids = [g for g, _ in res["errs"]]
                data, _ = parse_results(res["path"])
                err_rows = [r["check_id"] for r in data if r["result"] == "ERROR"]
                self.assertIn(gid, ids, "%s did not fire; fired %s" % (gid, ids))
                self.assertIn("H1-GUARD-" + gid, err_rows)
                self.assertFalse(res["ok"])
                print("  C4 %-17s fires (%s); ERROR row written; all fired: %s PASS" % (gid, desc, ids))

    def test_c5_clean_file_no_false_alarm(self):
        """C5: clean file fires no guard and writes zero ERROR rows."""
        with tempfile.TemporaryDirectory() as td:
            rawp = os.path.join(td, "raw.csv")
            with open(rawp, "w", encoding="utf-8", newline="") as f:
                f.write(H1.fake_zorro_csv())
            res = C.run_check(SPEC, rawp, td, "20260101")
            data, _ = parse_results(res["path"])
            self.assertEqual(res["errs"], [])
            self.assertEqual(sum(r["result"] == "ERROR" for r in data), 0)
            self.assertTrue(res["ok"])
            print("  C5 clean file: 0 guards fired, 0 ERROR rows, verdict PASS (%d PASS) PASS"
                  % res["counts"]["n_pass"])

    # ------------------------------------------------------------------ C6
    def test_c6_inputs_equal_h1(self):
        """C6: checker inputs == h1_check.make_inputs() for H1's parameters, tol 1e-12."""
        xc, xh = C.make_inputs(SPEC), H1.make_inputs()
        self.assertEqual(sorted(xc), sorted(xh))
        worst = max(float(abs(xc[k] - xh[k]).max()) for k in xh)
        print("  C6 inputs vs h1_check.make_inputs: worst |diff| %.3e tol 1e-12 %s"
              % (worst, "PASS" if worst <= 1e-12 else "FAIL"))
        self.assertLessEqual(worst, 1e-12)

    # ------------------------------------------------------------------ C7
    def test_c7_results_writer(self):
        """C7: no overwrite, _run2 naming, footer sha256 == fresh hash, footer counts == rows."""
        with tempfile.TemporaryDirectory() as td:
            rawp = os.path.join(td, "raw.csv")
            with open(rawp, "w", encoding="utf-8", newline="") as f:
                f.write(H1.fake_zorro_csv())
            res1 = C.run_check(SPEC, rawp, td, "20260101")
            self.assertTrue(res1["path"].endswith("H1_SuperSmoother2Pole_20260101.csv"))
            def slurp(pth):
                with open(pth, encoding="utf-8") as fh:
                    return fh.read()
            before = slurp(res1["path"])
            with self.assertRaises(FileExistsError):
                C.write_results(res1["path"], SPEC, res1["rows"], res1["nc"], [], rawp, res1["sha256"])
            self.assertEqual(slurp(res1["path"]), before)
            print("  C7 second write to the same name refused (FileExistsError), file unchanged PASS")
            res2 = C.run_check(SPEC, rawp, td, "20260101")
            self.assertTrue(res2["path"].endswith("_run2.csv"))
            res3 = C.run_check(SPEC, rawp, td, "20260101")
            self.assertTrue(res3["path"].endswith("_run3.csv"))
            print("  C7 next names: %s, %s PASS" % (os.path.basename(res2["path"]), os.path.basename(res3["path"])))
            # footer sha == fresh hash, footer counts == row counts (clean file, then a guard file)
            bad = os.path.join(td, "bad.csv")
            with open(bad, "w", encoding="utf-8", newline="") as f:
                f.write(H1.fake_zorro_csv(mutate=_dup_n))
            res_bad = C.run_check(SPEC, bad, os.path.join(td, "o2"), "20260101")
            for res, rp in ((res1, rawp), (res_bad, bad)):
                data, foot = parse_results(res["path"])
                with open(rp, "rb") as f:
                    fresh = hashlib.sha256(f.read()).hexdigest()
                rawline = [l for l in foot if l.startswith("# raw_file=")][0]
                self.assertTrue(rawline.endswith("sha256=" + fresh))
                self.assertIn(rp, rawline)
                cnt = [l for l in foot if l.startswith("# real_checks=")][0]
                real = [r for r in data if r["role"] == "real"]
                want = "# real_checks=%d PASS=%d FAIL=%d ERROR=%d" % (
                    len(real), sum(r["result"] == "PASS" for r in real),
                    sum(r["result"] == "FAIL" for r in real),
                    sum(r["result"] == "ERROR" for r in data))
                self.assertEqual(cnt, want)
                self.assertIn("# batch=H1_SuperSmoother2Pole variants_run=%d" % (6 if not res["errs"] else 0),
                              foot)
            print("  C7 footer sha256 == fresh hash; footer counts == row counts (clean and guard file) PASS")

    # ------------------------------------------------------------------ C8
    def test_c8_nc_report_reproduces_stage1(self):
        """C8: NC report on simulated NC-A / NC-B output, P=20, reproduces stage 1 numbers."""
        ex = C._h1_expect()
        spec = dict(SPEC, variants=[
            dict(id="P20", params="P=20", role="real", expected=ex[20]),
            dict(id="NCA", params="NC-A c1 +1 in 3rd digit", role="neg_control", expected=ex[20]),
            dict(id="NCB", params="NC-B c0 +1 in 3rd digit", role="neg_control", expected=ex[20])])
        filters = {"P20": R.ss2_code(20), "NCA": R.ss2_code(20, c1_bump=1),
                   "NCB": R.ss2_code(20, in_bump=1)}
        raw = C.load_raw(io.StringIO(build_csv(spec, filters)))
        self.assertEqual(C.validate(spec, raw), [])
        rows, nc = C.evaluate(spec, raw)
        ts = spec["ts"]
        quoted = {"NCA": 9.71, "NCB": 25.28}
        want = {"NCA": (True, False), "NCB": (True, True)}
        for vid in ("NCA", "NCB"):
            f = filters[vid]
            stage1 = max(abs(R.gain_at(f, t) - e) for t, e in zip(ts, ex[20][1])) / spec["tol_gain"]
            got = nc[vid]["max_ratio"]["gain"]
            rel = abs(got - stage1) / stage1
            print("  C8 %s gain ratio %.6f (stage-1 analytic %.6f, rel diff %.2e, tol 1e-6); "
                  "fails_as_required=%s margin10_met=%s PASS" % (vid, got, stage1, rel,
                                                                nc[vid]["fails_as_required"],
                                                                nc[vid]["margin10_met"]))
            self.assertLessEqual(rel, 1e-6)
            self.assertLessEqual(abs(got - quoted[vid]) / quoted[vid], 1e-3)   # stage 1 report, 3-4 digits
            self.assertEqual((nc[vid]["fails_as_required"], nc[vid]["margin10_met"]), want[vid])
        # the report's fields can disagree: NCA fails but misses the 10x margin (9.71x)
        self.assertLess(nc["NCA"]["max_ratio"]["gain"], 10)

    def test_c8b_nc_secretly_correct_is_reported(self):
        """Guard: a control that is really the correct filter must report fails_as_required=False
        and the file verdict must not be PASS (a control that passes means the harness is broken)."""
        ex = C._h1_expect()
        spec = dict(SPEC, variants=[
            dict(id="P20", params="P=20", role="real", expected=ex[20]),
            dict(id="NCA", params="secretly correct", role="neg_control", expected=ex[20])])
        filters = {"P20": R.ss2_code(20, pi_value=math.pi), "NCA": R.ss2_code(20, pi_value=math.pi)}
        raw = C.load_raw(io.StringIO(build_csv(spec, filters)))
        rows, nc = C.evaluate(spec, raw)
        ok, _ = C.verdict(spec, rows, nc, [])
        print("  C8b secretly-correct control: fails_as_required=%s, file verdict %s (must be FAIL) PASS"
              % (nc["NCA"]["fails_as_required"], "PASS" if ok else "FAIL"))
        self.assertFalse(nc["NCA"]["fails_as_required"])
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
