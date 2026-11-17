"""Tests for the RFF checker tooling (stage 1): the alternating (Nyquist) input, the alt gain and the gated alt phase
(PASS / FAIL where checked, SKIP where gain < phase_gate, ERROR where the table is inconsistent with the gate), the
check counts, the SKIP trailer, Cascade models in IMP, and an end-to-end run of the real RFF spec on a synthetic raw
file built from each variant's own model.

Rule (CLAUDE.md 4.4): every guard is SEEN TO FIRE on a deliberately broken input. No .c file is read, no Zorro run.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import copy
import math
import os
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rff_support as S      # noqa: E402

C, R, G = S.C, S.R, S.G

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None


def variant(cs_, vid):
    return copy.deepcopy([v for v in cs_["variants"] if v["id"] == vid][0])


def alt_rows(cs_, v, yv):
    return [r for r in C.check_rows(cs_, v, S.inputs(), yv, xe=S.inputs()) if r["check_id"].endswith(("gain-alt", "phase-alt"))]


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
class TestAltInputAndMeasurements(unittest.TestCase):
    def test_01_inputs(self):
        cs_ = S.cs()
        x = S.inputs()
        self.assertEqual(C.input_names(cs_), ["flat", "s5", "s10", "s20", "s40", "s100", "alt", "ramp"])
        n = np.arange(cs_["n_bars"])
        want = cs_["level"] + cs_["amp"] * np.where(n % 2 == 0, 1.0, -1.0)
        self.assertTrue(np.array_equal(x["alt"], want))
        self.assertGreater(x["alt"][0], x["alt"][1])                          # (-1)^0 = +1 first, then -1
        self.assertAlmostEqual(x["alt"][0] - x["alt"][1], 2 * cs_["amp"], delta=1e-15)
        old = dict(cs_)
        old.pop("alt")
        self.assertEqual(C.input_names(old), ["flat", "s5", "s10", "s20", "s40", "s100", "ramp"])
        self.assertNotIn("alt", C.make_inputs(old))

    def test_02_gain_alt_known_answers(self):
        """The (-1)^n fit returns |H(-1)|: EMA(0.5): 0.5/1.5; -0.5*x: 0.5; and the ramp-free flat filter 1.0."""
        cs_ = S.cs()
        for f, want in ((R.ema(0.5), 1.0 / 3.0), (R.Filter(b=(-0.5,), a=()), 0.5), (R.Filter(b=(1.0,), a=()), 1.0)):
            y = R.simulate(f, S.inputs()["alt"])
            self.assertAlmostEqual(C.m_gain_alt(cs_, y), want, delta=1e-9)
            self.assertAlmostEqual(C.m_gain_alt(cs_, y), R.gain_at(f, 2), delta=1e-9)       # = the analytic reference

    def test_03_phase_alt_is_zero_or_pi(self):
        cs_ = S.cs()
        pos = R.simulate(R.ema(0.5), S.inputs()["alt"])
        neg = R.simulate(R.Filter(b=(-0.5,), a=()), S.inputs()["alt"])
        self.assertEqual(C.m_phase_alt(cs_, pos), 0.0)
        self.assertEqual(C.m_phase_alt(cs_, neg), math.pi)
        # the reference convention: phase_at(f, 2) = 0 / +-pi; wrap_phase makes +-pi equal
        for f, y in ((R.ema(0.5), pos), (R.Filter(b=(-0.5,), a=()), neg)):
            self.assertLess(abs(C.wrap_phase(C.m_phase_alt(cs_, y) - R.phase_at(f, 2))), 1e-12)
        self.assertEqual(C.wrap_phase(math.pi - (-math.pi)), 0.0)

    def test_04_guard_fires_gain_alt_on_the_wrong_input(self):
        """Feeding a sine response instead of the alt response gives a visibly different gain (the measurement is not blind)."""
        cs_ = S.cs()
        f = R.ema(0.5)
        self.assertGreater(abs(C.m_gain_alt(cs_, R.simulate(f, S.inputs()["s5"])) - R.gain_at(f, 2)), 0.05)


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
class TestGateSkipFiresAndDoesNotFire(unittest.TestCase):
    """The phase gate binds for the first time (decision 2A): same code path, one table below the gate, one above."""

    def setUp(self):
        self.cs = copy.deepcopy(S.cs())
        self.f_pos, self.f_neg = R.ema(0.5), R.Filter(b=(-0.5,), a=())
        self.yv_pos = {i: R.simulate(self.f_pos, S.inputs()[i]) for i in C.input_names(self.cs)}
        self.yv_neg = {i: R.simulate(self.f_neg, S.inputs()[i]) for i in C.input_names(self.cs)}

    def test_05_gate_fires_row_is_skip_not_pass(self):
        v = variant(self.cs, "P48S10")                         # gain_alt 6e-18 < gate 0.05, no phase_alt
        rows = alt_rows(self.cs, v, self.yv_pos)
        ph = [r for r in rows if r["check_id"].endswith("phase-alt")]
        self.assertEqual(len(ph), 1)
        self.assertEqual(ph[0]["result"], "SKIP")
        self.assertEqual(ph[0]["role"], "skip")
        self.assertIn("gain < phase_gate", ph[0]["input"])
        self.assertIn("0.05", ph[0]["input"])
        self.assertTrue(math.isnan(ph[0]["actual"]))
        print("\n  [gate fires] %s: %s | %s" % (ph[0]["check_id"], ph[0]["result"], ph[0]["input"]))

    def test_06_gate_does_not_fire_phase_is_checked_pass(self):
        for f, yv in ((self.f_pos, self.yv_pos), (self.f_neg, self.yv_neg)):
            v = variant(self.cs, "P48S10")
            v["gain_alt"], v["phase_alt"] = R.gain_at(f, 2), R.phase_at(f, 2)         # 1/3, 0 | 0.5, +-pi: above the gate
            rows = alt_rows(self.cs, v, yv)
            ph = [r for r in rows if r["check_id"].endswith("phase-alt")][0]
            self.assertEqual(ph["result"], "PASS", ph)
            self.assertEqual(ph["role"], "real")
            self.assertLess(ph["abs_diff"], 1e-12)
            gn = [r for r in rows if r["check_id"].endswith("gain-alt")][0]
            self.assertEqual(gn["result"], "PASS", gn)
            print("\n  [gate does not fire] expected gain %.4f: phase row %s (actual %r, expected %r)"
                  % (v["gain_alt"], ph["result"], ph["actual"], ph["expected"]))

    def test_07_checked_phase_row_can_fail(self):
        """Fire: a sign error (output inverted) at Nyquist: expected phase 0, measured pi -> FAIL; the gain still PASSes."""
        v = variant(self.cs, "P48S10")
        v["gain_alt"], v["phase_alt"] = R.gain_at(self.f_neg, 2), 0.0           # table says in phase, output is inverted
        rows = alt_rows(self.cs, v, self.yv_neg)
        ph = [r for r in rows if r["check_id"].endswith("phase-alt")][0]
        self.assertEqual(ph["result"], "FAIL")
        self.assertAlmostEqual(ph["abs_diff"], math.pi, delta=1e-12)
        self.assertEqual([r for r in rows if r["check_id"].endswith("gain-alt")][0]["result"], "PASS")

    def test_08_inconsistent_table_is_error_never_silent(self):
        """gain_alt >= gate but no phase_alt (a hand-built dict the generator would have refused): ERROR, not SKIP."""
        v = variant(self.cs, "P48S10")
        v["gain_alt"] = 0.5
        ph = [r for r in alt_rows(self.cs, v, self.yv_neg) if r["check_id"].endswith("phase-alt")][0]
        self.assertEqual(ph["result"], "ERROR")
        self.assertNotEqual(ph["role"], "skip")

    def test_09_gain_alt_fail_and_nonfinite(self):
        v = variant(self.cs, "P48S10")                         # expects ~0 at Nyquist; feed a filter that passes it
        g = [r for r in alt_rows(self.cs, v, self.yv_pos) if r["check_id"].endswith("gain-alt")][0]
        self.assertEqual(g["result"], "FAIL")
        self.assertGreater(g["ratio"], 1000)
        bad = dict(self.yv_pos)
        bad["alt"] = np.full(self.cs["n_bars"], float("nan"))
        g = [r for r in alt_rows(self.cs, v, bad) if r["check_id"].endswith("gain-alt")][0]
        self.assertEqual(g["result"], "ERROR")

    def test_10_check_counts(self):
        """n_checks: a table without phase_alt counts the alt gain only (16 per real variant, 64 for four); with
        phase_alt it counts both (17). Without the flag the count is the old one."""
        cs_ = S.cs()
        real = [v for v in cs_["variants"] if v["role"] == "real"]
        self.assertEqual([C.n_checks(cs_, v) for v in real], [16, 16, 16, 16])
        v = variant(cs_, "P48S10")
        v["phase_alt"] = 0.0
        self.assertEqual(C.n_checks(cs_, v), 17)
        old = dict(cs_)
        old.pop("alt")
        self.assertEqual(C.n_checks(old, variant(cs_, "P48S10")), 15)            # no alt: flat + 5 gains + 5 phases + resid + 3 start-ups
        rows = C.check_rows(cs_, real[0], S.inputs(), S.own_model_outputs()["P48S10"], xe=S.inputs())
        self.assertEqual(len(rows), 17)                                           # 16 checks + 1 SKIP row
        self.assertEqual(sum(r["result"] == "SKIP" for r in rows), 1)
        self.assertEqual(len([r for r in rows if r["role"] == "real"]), 16)


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
class TestEndToEndOnTheRealSpec(unittest.TestCase):
    """The RFF spec + the new tooling on a synthetic raw file = what a perfect Zorro run would export."""

    @classmethod
    def setUpClass(cls):
        cls.cs = S.cs()
        cls.header = C.header_of(cls.cs)
        cls.tmp = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_raw(self, cols, tag):
        d = os.path.join(self.tmp.name, tag)
        os.makedirs(d, exist_ok=True)
        raw = os.path.join(d, "raw.csv")
        with open(raw, "w", encoding="utf-8", newline="") as f:
            f.write(S.to_text(self.header, cols, self.cs["n_bars"]))
        res = C.run_check(self.cs, raw, d, "20261117")
        with open(res["path"], encoding="utf-8") as f:
            res["text"] = f.read()
        return res

    def test_11_header_has_the_alt_columns(self):
        self.assertEqual(len(self.header), 2 + 8 + 11 * 8)
        self.assertIn("x_alt", self.header)
        self.assertIn("y_NCU_alt", self.header)
        self.assertEqual(self.header.index("x_alt"), self.header.index("x_s100") + 1)

    def test_12_clean_run_passes(self):
        res = self.run_raw(S.raw_cols(), "clean")
        c = res["counts"]
        print("\n  [e2e] own-model raw: ok=%s real=%d PASS=%d FAIL=%d ERROR=%d" % (res["ok"], c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]))
        self.assertEqual(res["errs"], [])
        self.assertEqual((c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]), (64, 64, 0, 0))
        self.assertTrue(res["ok"], res["text"][-600:])
        skips = [r for r in res["rows"] if r["result"] == "SKIP"]
        self.assertEqual(len(skips), 11)                                           # 4 real + 7 controls
        self.assertEqual(sorted(r["role"] for r in skips), ["skip"] * 11)
        self.assertTrue(all(r["check_id"].endswith("-phase-alt") for r in skips))
        self.assertEqual(sum(r["result"] == "ERROR" for r in res["rows"]), 0)
        self.assertTrue(all(d["fails_as_required"] for d in res["nc"].values()))
        self.assertEqual(len(res["nc"]), 7)
        imp = [r for r in res["rows"] if r["role"] == "imp"]
        floor = [r for r in res["rows"] if r["role"] == "floor"]
        self.assertEqual((len(imp), len(floor)), (13, 16))
        self.assertTrue(all(r["result"] == "PASS" for r in imp + floor))
        self.assertIn("# SKIP=11 (alt phase where the expected gain < phase_gate 0.05", res["text"])
        self.assertIn("# real_checks=64 PASS=64 FAIL=0 ERROR=0", res["text"])
        self.assertIn("variants_run=11 real=4 neg_control=7", res["text"])
        self.assertIn(",SKIP,skip", res["text"].replace("\r", ""))
        self.assertIn("# VERDICT: PASS", res["text"])

    def test_13_detection_follows_detect_required(self):
        res = self.run_raw(S.raw_cols(), "detect")
        req = S.spec()["detect"]["required"]
        for vid, d in res["nc"].items():
            self.assertEqual(d["required"], req[vid])
            for k in req[vid]:
                self.assertTrue(d["detected"][k], (vid, k))
        # NCU is the only control whose alt gain FAILs
        failing_alt = {r["check_id"].split("-")[1] for r in res["rows"] if r["check_id"].endswith("gain-alt") and r["result"] == "FAIL"}
        self.assertEqual(failing_alt, {"NCU"})
        # NCO (planning chat: "detection by start-up only; confirm"): start-up is the required kind (1e6 x tolerance). The
        # T = 20 gain effect is 2.1e-5 < 3e-5, but the MAX over the five periods is 2.2x (gain) and 4.7x (phase) the
        # tolerance, so those kinds also FAIL here; neither reaches the 10x margin, hence only start-up is required.
        nco = res["nc"]["NCO"]
        self.assertTrue(nco["detected"]["startup"])
        self.assertLess(nco["max_ratio"]["gain"], 10)
        self.assertLess(nco["max_ratio"]["phase"], 10)
        self.assertGreater(nco["max_ratio"]["startup"], 1e5)
        t20 = [r for r in res["rows"] if r["check_id"] == "RFF-NCO-gain-T20"][0]
        self.assertLess(t20["abs_diff"], 3e-5)                                     # the planning-chat number holds at T = 20

    def test_14_guard_fires_altered_alt_input_column(self):
        """G_INPUT_MISMATCH covers alt: one flipped sign in x_alt trips the guard, the run is not evaluated."""
        cols = S.raw_cols()
        cols["x_alt"][1234] = cols["x_alt"][1234] + 2 * self.cs["amp"]
        res = self.run_raw(cols, "altx")
        gids = [g for g, _ in res["errs"]]
        print("\n  [fire] x_alt[1234] sign flipped: guards %s" % gids)
        self.assertIn("G_INPUT_MISMATCH", gids)
        self.assertFalse(res["ok"])
        self.assertEqual(res["rows"], [])
        self.assertIn("# VERDICT: FAIL", res["text"])

    def test_15_guard_fires_missing_alt_column(self):
        cols = S.raw_cols()
        hdr = [h for h in self.header if h != "x_alt"]
        d = os.path.join(self.tmp.name, "noalt")
        os.makedirs(d, exist_ok=True)
        raw = os.path.join(d, "raw.csv")
        with open(raw, "w", encoding="utf-8", newline="") as f:
            f.write(S.to_text(hdr, cols, self.cs["n_bars"]))
        res = C.run_check(self.cs, raw, d, "20261117")
        self.assertIn("G_HEADER", [g for g, _ in res["errs"]])
        self.assertFalse(res["ok"])

    def test_16_wrong_real_output_fails_and_wrong_control_is_not_detected(self):
        """A real variant that is really the NC1s pipeline -> its checks FAIL; a control that is really the corrected
        pipeline -> 'NOT_DETECTED'. Both verdicts are FAIL: the verdict is not a rubber stamp."""
        y = S.own_model_outputs()
        res = self.run_raw(S.raw_cols({"P30S10": y["NC1s"]}), "wrongreal")
        print("\n  [fire] P30S10 replaced by the NC1s output: ok=%s real FAIL=%d" % (res["ok"], res["counts"]["n_fail"]))
        self.assertFalse(res["ok"])
        self.assertGreater(res["counts"]["n_fail"], 0)
        imp_p30 = [r for r in res["rows"] if r["check_id"] == "RFF-P30S10-imp-pass"][0]
        self.assertEqual(imp_p30["result"], "FAIL")                               # IMP sees it too
        res = self.run_raw(S.raw_cols({"NCU": y["P48S10"]}), "wrongctrl")
        self.assertFalse(res["ok"])
        self.assertFalse(res["nc"]["NCU"]["fails_as_required"])
        self.assertIn("NOT_DETECTED", res["text"])

    def test_17_imp_must_fail_fires_when_the_old_pipeline_is_in_a_real_slot(self):
        """P48S10 carrying the NCO (old) output: its must_fail replay (NCO model) becomes ~0 -> that row FAILs; start-up
        checks FAIL as well."""
        y = S.own_model_outputs()
        res = self.run_raw(S.raw_cols({"P48S10": y["NCO"]}), "oldinreal")
        row = [r for r in res["rows"] if r["check_id"] == "RFF-P48S10-imp-fail"][0]
        self.assertEqual(row["result"], "FAIL")
        self.assertLess(row["actual"], 1e-9)
        self.assertFalse(res["ok"])
        self.assertTrue(any(r["result"] == "FAIL" and "startup" in r["check_id"] and "P48S10" in r["check_id"]
                            for r in res["rows"]))

    def test_18_results_file_is_never_overwritten(self):
        d = os.path.join(self.tmp.name, "twice")
        os.makedirs(d, exist_ok=True)
        raw = os.path.join(d, "raw.csv")
        with open(raw, "w", encoding="utf-8", newline="") as f:
            f.write(S.to_text(self.header, S.raw_cols(), self.cs["n_bars"]))
        r1 = C.run_check(self.cs, raw, d, "20261117")
        r2 = C.run_check(self.cs, raw, d, "20261117")
        self.assertNotEqual(r1["path"], r2["path"])
        self.assertTrue(r2["path"].endswith("_run2.csv"))


if __name__ == "__main__":
    unittest.main()
