"""Tests for the HP checker behaviour (HARNESS_DESIGN D4): dc_gain-aware flat, ramp residual instead of ramp lag,
sine phase, start-up check, seed-aware IMP, floor kinds, new detection kinds.

Rule (CLAUDE.md 4.4): every new check is SEEN TO FIRE on an input that perturbs ONLY what it targets; each such
test asserts that the neighbouring checks stay PASS. Inputs: tests/hp_fixture.py (synthetic, no Zorro, no .c).
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
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)

import checker as C        # noqa: E402
import generator as G      # noqa: E402
import reference as R      # noqa: E402
import hp_fixture as FX    # noqa: E402


def cspec():
    return G.to_checker_spec(FX.toml_spec())


def rows_of(spec, cols, vid, xe=None):
    v = [v for v in spec["variants"] if v["id"] == vid][0]
    x = C.make_inputs(spec)
    yv = {i: np.array(cols["y_%s_%s" % (vid, i)]) for i in C.input_names(spec)}
    kw = {} if xe is None else dict(xe=xe)
    return {r["check_id"].split("-", 2)[2]: r for r in C.check_rows(spec, v, x, yv, **kw)}


class TestHpChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = cspec()
        cls.cols = FX.base_cols(cls.spec)

    def cols_copy(self):
        return {k: list(v) for k, v in self.cols.items()}

    def test_01_real_variant_check_list_and_pass(self):
        rs = rows_of(self.spec, self.cols, "P48")
        self.assertNotIn("ramp-lag", rs)                        # dc_gain 0: no ramp lag
        want = ["flat"] + ["gain-T%d" % t for t in FX.TS] + ["ramp-res"] \
            + ["phase-T%d" % t for t in FX.TS if t in [v for v in self.spec["variants"]
                                                       if v["id"] == "P48"][0]["phases"]] \
            + ["startup-flat", "startup-ramp"]
        self.assertEqual(sorted(rs), sorted(want))
        for k, r in rs.items():
            self.assertEqual(r["result"], "PASS", "%s diff %.3e tol %g" % (k, r["abs_diff"], r["tolerance"]))
        self.assertEqual(rs["phase-T100"]["tolerance"], FX.TOL["phase"])

    def test_02_flat_uses_dc_gain(self):
        """m_flat = max|y - dc_gain*level|. dc_gain 1 behaves as before; fire: output = level fails at dc 0."""
        y = np.full(3000, 0.0)
        self.assertEqual(C.m_flat(self.spec, y), 0.0)
        self.assertAlmostEqual(C.m_flat(self.spec, np.full(3000, 1.1)), 1.1, places=12)
        s1 = dict(self.spec, dc_gain=1.0)
        self.assertEqual(C.m_flat(s1, np.full(3000, 1.1)), 0.0)
        s_noKey = {k: v for k, v in self.spec.items() if k != "dc_gain"}
        self.assertEqual(C.m_flat(s_noKey, np.full(3000, 1.1)), 0.0)         # default dc_gain = 1
        # fire: perturb only the flat output of a real variant (DC offset after warmup)
        c = self.cols_copy()
        c["y_P48_flat"][1000] += 1e-6
        rs = rows_of(self.spec, c, "P48")
        self.assertEqual(rs["flat"]["result"], "FAIL")
        for k in rs:
            if k != "flat":
                self.assertEqual(rs[k]["result"], "PASS", k)

    def test_03_ramp_residual_fire(self):
        c = self.cols_copy()
        c["y_P48_ramp"] = [v + 1e-4 for v in c["y_P48_ramp"]]                # offset the ramp output only
        rs = rows_of(self.spec, c, "P48")
        self.assertEqual(rs["ramp-res"]["result"], "FAIL")
        self.assertAlmostEqual(rs["ramp-res"]["abs_diff"], 1e-4, places=9)
        # the offset also lies in the start-up window of the ramp: that check is not ramp-res's neighbour
        for k, r in rs.items():
            if k not in ("ramp-res", "startup-ramp"):
                self.assertEqual(r["result"], "PASS", k)

    def test_04_ramp_residual_value(self):
        """expected resid compared against the LAST 100 ramp bars: perturbing earlier bars must not fire."""
        c = self.cols_copy()
        c["y_P48_ramp"][1000] += 5e-3
        rs = rows_of(self.spec, c, "P48")
        self.assertEqual(rs["ramp-res"]["result"], "PASS")

    def test_05_phase_fire_only_phase(self):
        """Replace the T=20 sine output by a sine with the same gain and phase + 1e-3: only phase-T20 fires."""
        v = [v for v in self.spec["variants"] if v["id"] == "P48"][0]
        t, d = 20, 1e-3
        f = R.hp_code(48, k=FX.SQRT_HALF)
        n = np.arange(3000, dtype=float)
        g, ph = R.gain_at(f, t), R.phase_at(f, t)
        c = self.cols_copy()
        c["y_P48_s20"] = list(g * self.spec["amp"] * np.sin(2 * math.pi * n / t + ph + d))
        rs = rows_of(self.spec, c, "P48")
        self.assertEqual(rs["phase-T20"]["result"], "FAIL")
        self.assertAlmostEqual(rs["phase-T20"]["abs_diff"], d, delta=2e-5)       # 1e-3 + PI gap
        self.assertEqual(rs["gain-T20"]["result"], "PASS")                       # gain unchanged
        self.assertLess(abs(rs["gain-T20"]["actual"] - R.gain_at(R.hp_article(48), 20)), 3e-5)
        for k, r in rs.items():
            if k not in ("phase-T20",):
                self.assertEqual(r["result"], "PASS", k)
        self.assertIn(20, v["phases"])

    def test_06_phase_is_wrapped(self):
        self.assertAlmostEqual(C.wrap_phase(-math.pi + 1e-6 - (math.pi - 1e-6)), 2e-6, places=12)
        self.assertAlmostEqual(C.wrap_phase(4.97), 4.97 - 2 * math.pi, places=12)
        self.assertAlmostEqual(abs(C.wrap_phase(math.pi)), math.pi, places=12)
        # fire: a bare |actual - expected| would be ~2*pi here
        spec = copy.deepcopy(self.spec)
        v = [v for v in spec["variants"] if v["id"] == "P48"][0]
        v["phases"] = {5: -math.pi + 1e-6}
        c = self.cols_copy()
        n = np.arange(3000, dtype=float)
        g = R.gain_at(R.hp_article(48), 5)
        c["y_P48_s5"] = list(g * spec["amp"] * np.sin(2 * math.pi * n / 5 + math.pi - 1e-6))
        rs = rows_of(spec, c, "P48")
        self.assertEqual(rs["phase-T5"]["result"], "PASS")
        self.assertAlmostEqual(rs["phase-T5"]["abs_diff"], 2e-6, delta=1e-7)

    def test_07_phase_only_at_listed_periods(self):
        spec = copy.deepcopy(self.spec)
        v = [v for v in spec["variants"] if v["id"] == "P48"][0]
        v["phases"] = {20: v["phases"][20]}
        rs = rows_of(spec, self.cols, "P48")
        self.assertEqual([k for k in rs if k.startswith("phase")], ["phase-T20"])
        v["phases"] = {}
        rs = rows_of(spec, self.cols, "P48")
        self.assertEqual([k for k in rs if k.startswith("phase")], [])

    def test_08_startup_fire_only_startup(self):
        c = self.cols_copy()
        c["y_P48_flat"][3] += 1e-3                    # inside the warmup window, flat input only
        rs = rows_of(self.spec, c, "P48")
        self.assertEqual(rs["startup-flat"]["result"], "FAIL")
        self.assertAlmostEqual(rs["startup-flat"]["abs_diff"], 1e-3, places=9)
        for k, r in rs.items():
            if k != "startup-flat":
                self.assertEqual(r["result"], "PASS", k)
        c = self.cols_copy()
        c["y_P48_flat"][700] += 1e-3                  # after warmup: flat fires, start-up does not
        rs = rows_of(self.spec, c, "P48")
        self.assertEqual((rs["flat"]["result"], rs["startup-flat"]["result"]), ("FAIL", "PASS"))

    def test_09_seed_price_is_caught_by_startup_only(self):
        """NCS: corrected k, output history seeded at the price. Steady-state checks must stay PASS."""
        rs = rows_of(self.spec, self.cols, "NCS")
        self.assertEqual(rs["startup-flat"]["result"], "FAIL")
        self.assertGreater(rs["startup-flat"]["ratio"], 1e5)
        for k in rs:
            if not k.startswith("startup"):
                self.assertEqual(rs[k]["result"], "PASS", "%s %.3e" % (k, rs[k]["abs_diff"]))

    def test_10_startup_reference_uses_exported_x(self):
        """y_ref is simulated on the EXPORTED x columns (xe), not on make_inputs."""
        x = C.make_inputs(self.spec)
        xe = {k: v.copy() for k, v in x.items()}
        xe["ramp"] = xe["ramp"] * 2.0                 # exported ramp differs from the one the outputs came from
        rs = rows_of(self.spec, self.cols, "P48", xe=xe)
        self.assertEqual(rs["startup-ramp"]["result"], "FAIL")
        self.assertEqual(rs["startup-flat"]["result"], "PASS")
        rs0 = rows_of(self.spec, self.cols, "P48", xe=x)
        self.assertEqual(rs0["startup-ramp"]["result"], "PASS")

    def test_11_startup_unknown_model_is_error(self):
        spec = copy.deepcopy(self.spec)
        v = [v for v in spec["variants"] if v["id"] == "P48"][0]
        v["article"] = "bogus(48)"
        rs = rows_of(spec, self.cols, "P48")
        self.assertEqual(rs["startup-flat"]["result"], "ERROR")
        self.assertEqual(rs["startup-ramp"]["result"], "ERROR")

    def test_12_nonfinite_is_error(self):
        c = self.cols_copy()
        c["y_P48_s20"][700] = float("nan")
        rs = rows_of(self.spec, c, "P48")
        self.assertEqual(rs["phase-T20"]["result"], "ERROR")


class TestKindsAndReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = cspec()
        cls.cols = FX.base_cols(cls.spec)

    def test_13_kind(self):
        self.assertEqual(C._kind("HPF-P48-phase-T20"), "phase")
        self.assertEqual(C._kind("HPF-P48-ramp-res"), "resid")
        self.assertEqual(C._kind("HPF-P48-startup-flat"), "startup")
        self.assertEqual(C._kind("HPF-P48-ramp-lag"), "lag")
        self.assertEqual(C._kind("HPF-P48-gain-T5"), "gain")
        self.assertEqual(C._kind("HPF-P48-flat"), "flat")

    def run_full(self, cols, spec=None, td=None):
        spec = spec or self.spec
        header = C.header_of(spec)
        with tempfile.TemporaryDirectory() as td_:
            raw = os.path.join(td_, "raw.csv")
            with open(raw, "w", newline="") as f:
                f.write(FX.to_text(header, cols, spec["n_bars"]))
            return C.run_check(spec, raw, td_, "20260101")

    def test_14_full_run_verdict_and_counts(self):
        res = self.run_full(self.cols)
        self.assertEqual(res["errs"], [])
        # 4 real variants x (1 flat + 5 gain + 1 resid + phases + 2 startup)
        n_ph = sum(len(v["phases"]) for v in self.spec["variants"] if v["role"] == "real")
        self.assertEqual(res["counts"]["n_real"], 4 * 9 + n_ph)
        self.assertEqual((res["counts"]["n_fail"], res["counts"]["n_err"]), (0, 0))
        for vid, d in res["nc"].items():
            self.assertTrue(d["fails_as_required"], "%s detected=%s required=%s" % (vid, d["detected"], d["required"]))
            self.assertIn("phase", d["detected"])
            self.assertIn("startup", d["detected"])
            self.assertIn("resid", d["detected"])
        self.assertTrue(res["ok"], [r["check_id"] for r in res["rows"] if r["result"] != "PASS"
                                    and r["role"] in ("real", "imp", "floor")])

    def test_15_control_kinds(self):
        res = self.run_full(self.cols)
        det = {vid: d["detected"] for vid, d in res["nc"].items()}
        self.assertTrue(det["NCZ"]["resid"])
        self.assertFalse(det["NCA"]["resid"])                    # a real second-order HP has residual 0
        self.assertTrue(det["NCS"]["startup"] and not det["NCS"]["gain"] and not det["NCS"]["phase"])
        self.assertTrue(det["NCB"]["gain"])
        self.assertFalse(det["NCB"]["phase"])                    # input scale barely moves phase (7.5e-7)

    def test_16_required_kind_missing_fires(self):
        """Fire: NCS listed as needing 'gain' (it cannot) -> not detected -> verdict FAIL."""
        spec = copy.deepcopy(self.spec)
        spec["detect_required"]["NCS"] = ["gain"]
        res = self.run_full(self.cols, spec)
        self.assertFalse(res["nc"]["NCS"]["fails_as_required"])
        self.assertFalse(res["ok"])

    def test_17_results_file_trailer(self):
        header = C.header_of(self.spec)
        with tempfile.TemporaryDirectory() as td:
            raw = os.path.join(td, "raw.csv")
            with open(raw, "w", newline="") as f:
                f.write(FX.to_text(header, self.cols, self.spec["n_bars"]))
            res = C.run_check(self.spec, raw, td, "20260101")
            txt = open(res["path"], encoding="utf-8").read()
        self.assertIn("# VERDICT: PASS", txt)
        self.assertIn("phase=", txt)
        self.assertIn("startup=", txt)
        self.assertIn("resid=", txt)
        self.assertNotIn("zorro_vs_book_lag=", txt)               # dc_gain 0: no lag floor


class TestImpSeedAndFloor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = cspec()
        cls.cols = FX.base_cols(cls.spec)

    def raw(self, cols):
        return C.Raw_from_cols(cols) if hasattr(C, "Raw_from_cols") else self._raw(cols)

    def _raw(self, cols):
        r = C.Raw()
        r.header = list(cols)
        r.cols = {k: np.array(v) for k, v in cols.items()}
        r.nrows = len(cols["n"])
        return r

    def test_18_imp_replay_uses_variant_seed(self):
        rows = {r["check_id"]: r for r in C.imp_rows(self.spec, self._raw(self.cols))}
        for p in FX.REAL_PS:
            r = rows["HPF-P%d-imp-pass" % p]
            self.assertEqual(r["result"], "PASS", "%s %.3e" % (r["check_id"], r["actual"]))
        self.assertEqual(rows["HPF-NCH-imp-pass"]["result"], "PASS")      # NCH is price-seeded, replayed as such
        self.assertEqual(rows["HPF-NCH-imp-fail"]["result"], "PASS")      # fire: corrected model differs

    def test_19_imp_fires_on_wrong_seed(self):
        """Perturb ONLY the seed declared for NCH: the replay must now disagree (residual >> tol)."""
        spec = copy.deepcopy(self.spec)
        [v for v in spec["variants"] if v["id"] == "NCH"][0]["seed"] = "zero"
        rows = {r["check_id"]: r for r in C.imp_rows(spec, self._raw(self.cols))}
        self.assertEqual(rows["HPF-NCH-imp-pass"]["result"], "FAIL")
        self.assertGreater(rows["HPF-NCH-imp-pass"]["actual"], 1e-2)
        self.assertEqual(rows["HPF-P48-imp-pass"]["result"], "PASS")      # others unaffected
        # default seed (no key) = price = the old behaviour
        spec2 = copy.deepcopy(self.spec)
        for v in spec2["variants"]:
            v.pop("seed", None)
        rows2 = {r["check_id"]: r for r in C.imp_rows(spec2, self._raw(self.cols))}
        self.assertEqual(rows2["HPF-NCH-imp-pass"]["result"], "PASS")
        # no declared seed -> window n >= warmup (old behaviour): the start-up transient is not compared at all
        self.assertEqual(rows2["HPF-P48-imp-pass"]["result"], "PASS")
        self.assertIn("n>=500", rows2["HPF-P48-imp-pass"]["input"])
        # declared seed -> whole run (n >= 0); fire: declare the WRONG seed (price) for a zero-seeded real variant
        spec3 = copy.deepcopy(self.spec)
        [v for v in spec3["variants"] if v["id"] == "P48"][0]["seed"] = "price"
        rows3 = {r["check_id"]: r for r in C.imp_rows(spec3, self._raw(self.cols))}
        self.assertEqual(rows3["HPF-P48-imp-pass"]["result"], "FAIL")
        self.assertIn("n>=0", rows3["HPF-P48-imp-pass"]["input"])
        self.assertEqual(rows3["HPF-P30-imp-pass"]["result"], "PASS")

    def test_20_floor_rows_new_kinds(self):
        res_rows, nc = C.evaluate(self.spec, self._raw(self.cols))
        fl = {r["check_id"]: r for r in res_rows if r["role"] == "floor"}
        for q in ("gain", "phase", "resid", "startup"):
            self.assertIn("HPF-P48-floor-%s" % q, fl)
        self.assertNotIn("HPF-P48-floor-lag", fl)
        for r in fl.values():
            self.assertEqual(r["result"], "PASS", "%s %.3e tol %g" % (r["check_id"], r["actual"], r["tolerance"]))
        self.assertAlmostEqual(fl["HPF-P48-floor-phase"]["tolerance"], FX.TOL["phase"] / 10)

    def test_21_floor_guard_fires_for_phase(self):
        """Phase error 0.5*tol: phase check PASS, floor guard (tol/10) FAIL. Perturbs only the phase at T=20."""
        t, d = 20, 0.5 * FX.TOL["phase"]
        f = R.hp_code(48, k=FX.SQRT_HALF)
        n = np.arange(3000, dtype=float)
        c = {k: list(v) for k, v in self.cols.items()}
        c["y_P48_s20"] = list(R.gain_at(f, t) * self.spec["amp"] * np.sin(2 * math.pi * n / t + R.phase_at(f, t) + d))
        rows, nc = C.evaluate(self.spec, self._raw(c))
        by = {r["check_id"]: r for r in rows}
        self.assertEqual(by["HPF-P48-phase-T20"]["result"], "PASS")
        self.assertEqual(by["HPF-P48-floor-phase"]["result"], "FAIL")
        self.assertEqual(by["HPF-P48-floor-gain"]["result"], "PASS")
        txt = "\n".join(C.imp_trailer(self.spec, rows))
        self.assertIn("FLOOR_GUARD FAIL", txt)
        self.assertIn("HPF-P48-floor-phase", txt)


if __name__ == "__main__":
    unittest.main()
