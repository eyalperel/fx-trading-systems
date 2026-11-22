"""ATR stage 1: the checker's D7 extensions (rampdn bars inputs, two-column calls, the `scale` equivariance role, the window_hull and known_value kinds,
the absolute bound allowance, the range bound) on the ATR spec's own-model raw file, each with a deliberately broken input (CLAUDE.md 4.4).
No .c file is read, Zorro is not run."""
import copy
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))

import atr_support as A   # noqa: E402
import checker as C       # noqa: E402
import generator as G     # noqa: E402
import maf_support as M   # noqa: E402

_cache = {}


def base():
    if "b" not in _cache:
        spec, cs, x, bars = A.load()
        raw = M.synth_raw(A.SPEC)
        _cache["b"] = (spec, cs, x, bars, raw)
    return _cache["b"]


def mutated(edits):
    """Evaluate a copy of the perfect raw file with {column: [(row, delta)]} applied. Returns {check_id suffix: row}."""
    spec, cs, x, bars, raw = base()
    r2 = C.Raw()
    r2.header, r2.nrows = list(raw.header), raw.nrows
    r2.cols = {k: v.copy() for k, v in raw.cols.items()}
    for col, lst in edits.items():
        for row, d in lst:
            r2.cols[col][row] += d
    rows, nc = C.evaluate(cs, r2)
    return {r["check_id"]: r for r in rows}, nc


def res(rows, cid):
    return rows["ATR-" + cid]["result"]


class InputsAndColumns(unittest.TestCase):
    def test_rampdn_is_a_bars_input_and_exact(self):
        spec, cs, x, bars, raw = base()
        names = C.input_names(cs)
        self.assertEqual(names[:8], ["flat", "s5", "s10", "s20", "s40", "s100", "ramp", "rampdn"])
        self.assertIn("rampdnB", names)
        n = np.arange(cs["n_bars"], dtype=float)
        np.testing.assert_array_equal(x["rampdn"], cs["level"] - cs["slope"] * n)
        np.testing.assert_array_equal(x["rampdnB"], x["rampdn"])
        h = cs["adaptive"]["band_half"]
        np.testing.assert_array_equal(bars["rampdnB"][0], x["rampdn"] + h)
        np.testing.assert_array_equal(bars["rampdnB"][1], x["rampdn"] - h)
        np.testing.assert_array_equal(bars["rampdn"][0], x["rampdn"])      # point bars: H = L = x
        self.assertEqual(sorted(cs["adaptive"]["band"]), sorted(i + "B" for i in ("flat", "ramp", "rampdn", "s5", "s10", "s20", "s40", "s100")))

    def test_without_the_flag_there_is_no_rampdn(self):
        sp = G.load_spec(os.path.join(A.HARNESS, "specs", "FRAMA_ArticleFidelity.toml"))
        self.assertNotIn("rampdn", G.adaptive_base_ids(sp))
        sp2 = copy.deepcopy(G.load_spec(A.SPEC))
        sp2["inputs"]["ramp_down"] = False
        self.assertNotIn("rampdn", G.adaptive_input_ids(sp2))

    def test_two_column_calls(self):
        spec, cs, x, bars, raw = base()
        v = [u for u in cs["variants"] if u["id"] == "AT14"][0]
        cols = C.variant_columns(cs, v)
        self.assertEqual([o for o, _, _ in cols[:18]], ["tr"] * 18)
        self.assertEqual([o for o, _, _ in cols[18:]], ["atr"] * 18)
        self.assertEqual(cols[0][2], "tr_AT14_flat")
        self.assertEqual(cols[18][2], "atr_AT14_flat")
        text, _ = G.build_script(spec)
        self.assertIn("Y[1] = ATRMT4Core(S0, S0, S0, 14, &atr_o_tr);\t// AT14 flat", text)      # return value atr in slot 1, tr in slot 0
        self.assertIn("Y[0] = atr_o_tr;", text)
        # a band input passes its own High / Low series first, the close (S) last
        self.assertRegex(text, r"ATRMT4Core\(SHi0, SLo0, S\d+, 14, &atr_o_tr\);\t// AT14 flatB")

    def test_every_check_has_a_kind_and_counts(self):
        spec, cs, x, bars, raw = base()
        rows, nc = C.evaluate(cs, raw)
        per = {}
        for r in rows:
            if r["role"] == "real":
                per.setdefault(r["check_id"].split("-")[1], []).append(r)
        for vid in ("AT14", "AT20"):
            kinds = {}
            for r in per[vid]:
                kinds[C._kind(r["check_id"])] = kinds.get(C._kind(r["check_id"]), 0) + 1
            self.assertEqual(kinds, {"trace": 32, "bound": 2, "window_hull": 1, "known_value": 6, "equivariance": 4}, vid)
            self.assertEqual(len(per[vid]), 45)
            self.assertEqual(C.n_checks(cs, [v for v in cs["variants"] if v["id"] == vid][0]), 45)


class PerfectRun(unittest.TestCase):
    def test_all_real_checks_pass_and_every_control_is_detected_as_required(self):
        spec, cs, x, bars, raw = base()
        self.assertEqual(C.validate(cs, raw), [])
        rows, nc = C.evaluate(cs, raw)
        ok, c = C.verdict(cs, rows, nc, [])
        self.assertEqual((c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]), (90, 90, 0, 0))
        self.assertTrue(ok)
        for vid, d in nc.items():
            self.assertTrue(d["fails_as_required"], vid)
            self.assertTrue(d["margin10_met"], vid)
        self.assertEqual(sorted(nc), sorted(A.CONTROLS))
        # the required lists are what the spec registers
        self.assertEqual(nc["NCZ"]["required"], ["trace"])
        self.assertEqual(nc["NCWi"]["required"], ["trace", "window_hull"])

    def test_wrong_asset_guard_fires(self):
        spec, cs, x, bars, raw = base()
        r2 = C.Raw()
        r2.header, r2.nrows, r2.cols = list(raw.header), raw.nrows, {k: v.copy() for k, v in raw.cols.items()}
        r2.cols["clock_close"] = r2.cols["clock_close"] * 100.0           # e.g. a JPY / gold price
        self.assertIn("G_CLOCK", [g for g, _ in C.validate(cs, r2)])

    def test_exported_band_high_guard_fires(self):
        spec, cs, x, bars, raw = base()
        r2 = C.Raw()
        r2.header, r2.nrows, r2.cols = list(raw.header), raw.nrows, {k: v.copy() for k, v in raw.cols.items()}
        r2.cols["xh_s5B"][100] += 1e-9
        self.assertIn("G_INPUT_MISMATCH", [g for g, _ in C.validate(cs, r2)])


class ScaleRole(unittest.TestCase):
    def test_fires_on_a_1e9_scale_error(self):
        spec, cs, x, bars, raw = base()
        col = raw.cols["atr_AT14_sc40B"]
        rows, _ = mutated({"atr_AT14_sc40B": [(500, col[500] * 1e-9)]})        # a 1e-9 relative scale error on one value
        self.assertEqual(res(rows, "AT14-equiv-sc-atr"), "FAIL")
        self.assertGreater(rows["ATR-AT14-equiv-sc-atr"]["ratio"], 1.0)
        self.assertEqual(res(rows, "AT14-equiv-of-atr"), "PASS")

    def test_fires_on_an_offset_error_too(self):
        """A copy that carries the offset (an affine map instead of a scale) is wrong for a `scale` column."""
        spec, cs, x, bars, raw = base()
        rows, _ = mutated({"atr_AT14_of40B": [(500, 1.1)]})
        self.assertEqual(res(rows, "AT14-equiv-of-atr"), "FAIL")

    def test_ignores_the_offset_of_the_transform(self):
        """The reference of a scale column is |k| x base: changing the transform's offset in the checker spec changes nothing."""
        spec, cs, x, bars, raw = base()
        cs2 = copy.deepcopy(cs)
        for t in cs2["adaptive"]["transforms"].values():
            t["offset"] = 123.456
        rows, _ = C.evaluate(cs2, raw)
        m = {r["check_id"]: r for r in rows}
        for vid in ("AT14", "AT20"):
            for t in ("sc", "of"):
                for c in ("tr", "atr"):
                    self.assertEqual(m["ATR-%s-equiv-%s-%s" % (vid, t, c)]["result"], "PASS")
        # while a LEVEL column of the same spec would now fail (the offset does enter there): the role changes the reference
        cs3 = copy.deepcopy(cs2)
        cs3["adaptive"]["level_columns"], cs3["adaptive"]["scale_columns"] = ["atr", "tr"], []
        rows, _ = C.evaluate(cs3, raw)
        self.assertTrue(any(r["check_id"].startswith("ATR-AT14-equiv-sc") and r["result"] == "FAIL" for r in rows))

    def test_rejects_a_level_role_on_a_scale_column(self):
        sp = copy.deepcopy(G.load_spec(A.SPEC))
        sp["checks"]["level_columns"] = ["atr"]
        errs, _ = G.validate_adaptive(sp)
        self.assertIn("ADAPTIVE_BAD", [e for e, _ in errs])
        sp = copy.deepcopy(G.load_spec(A.SPEC))
        sp["checks"]["scale_columns"] = ["nope"]
        self.assertIn("ADAPTIVE_BAD", [e for e, _ in G.validate_adaptive(sp)[0]])


class WindowHull(unittest.TestCase):
    """flatB: TR = 4e-4 on every row, so atr sits ON both edges of its window: any excess shows."""

    def test_fires_on_one_row_out_by_1e12(self):
        rows, _ = mutated({"atr_AT14_flatB": [(100, 1e-12)]})
        self.assertEqual(res(rows, "AT14-whull-atr"), "FAIL")
        self.assertGreater(rows["ATR-AT14-whull-atr"]["ratio"], 100.0)

    def test_fires_on_a_relative_1e9_excess_and_on_the_low_side(self):
        rows, _ = mutated({"atr_AT14_flatB": [(100, 4e-4 * 1e-9)]})
        self.assertEqual(res(rows, "AT14-whull-atr"), "FAIL")
        rows, _ = mutated({"atr_AT14_flatB": [(100, -1e-12)]})
        self.assertEqual(res(rows, "AT14-whull-atr"), "FAIL")

    def test_inside_the_allowance_passes(self):
        """4e-16 (= 1e-12 relative of 4e-4) is inside the relative allowance plus the absolute 1e-15: no fire (the pre-registered reading)."""
        rows, _ = mutated({"atr_AT14_flatB": [(100, 4e-16)]})
        self.assertEqual(res(rows, "AT14-whull-atr"), "PASS")
        rows, _ = mutated({"atr_AT14_flatB": [(100, 5e-16)]})
        self.assertEqual(res(rows, "AT14-whull-atr"), "PASS")

    def test_window_start_row_is_the_tables_window(self):
        """Rows before the window (n < P) are not read: a value out by 1e-6 at row 10 does not touch the hull row (it fails the trace)."""
        rows, _ = mutated({"atr_AT14_flatB": [(10, 1e-6)]})
        self.assertEqual(res(rows, "AT14-whull-atr"), "PASS")
        self.assertEqual(res(rows, "AT14-trace-atr-flatB"), "FAIL")
        rows, _ = mutated({"atr_AT20_flatB": [(100, 1e-12)]})
        self.assertEqual(res(rows, "AT20-whull-atr"), "FAIL")

    def test_uses_the_models_tr_when_the_variant_exports_no_tr(self):
        """NCS exports atr only: its hull row reads the model's TR. A perfect run of the NCS body fails the hull (shared state)."""
        spec, cs, x, bars, raw = base()
        rows, _ = C.evaluate(cs, raw)
        m = {r["check_id"]: r for r in rows}
        self.assertEqual(m["ATR-NCS-whull-atr"]["result"], "FAIL")
        self.assertNotIn("ATR-NCS-bound-tr-range", m)


class KnownValueAndBounds(unittest.TestCase):
    def test_known_value_fires_and_passes(self):
        rows, _ = mutated({"atr_AT14_flatB": [(100, 1e-9)]})
        self.assertEqual(res(rows, "AT14-known-atr-flatB"), "FAIL")
        rows, _ = mutated({"atr_AT14_flatB": [(100, 1e-13)]})
        self.assertEqual(res(rows, "AT14-known-atr-flatB"), "PASS")
        rows, _ = mutated({"atr_AT14_ramp": [(14, 1e-9)]})                     # row P itself is read
        self.assertEqual(res(rows, "AT14-known-atr-ramp"), "FAIL")
        rows, _ = mutated({"atr_AT14_ramp": [(13, 1e-9)]})                     # row P-1 is not (start-up rows are the trace's job)
        self.assertEqual(res(rows, "AT14-known-atr-ramp"), "PASS")
        self.assertEqual(res(rows, "AT14-trace-atr-ramp"), "FAIL")

    def test_atr_bound_has_an_absolute_allowance(self):
        rows, _ = mutated({"atr_AT14_s5": [(100, -0.01)]})                     # atr goes negative
        self.assertEqual(res(rows, "AT14-bound-atr"), "FAIL")
        spec, cs, x, bars, raw = base()
        base_atr = raw.cols["atr_AT14_flat"]                                   # exactly 0 on flat: a -1e-16 dip is inside the 1e-15 allowance
        rows, _ = mutated({"atr_AT14_flat": [(100, -1e-16)]})
        self.assertEqual(res(rows, "AT14-bound-atr"), "PASS")
        rows, _ = mutated({"atr_AT14_flat": [(100, -1e-14)]})
        self.assertEqual(res(rows, "AT14-bound-atr"), "FAIL")
        self.assertEqual(base_atr[100], 0.0)

    def test_range_bound_tr_ge_high_minus_low(self):
        spec, cs, x, bars, raw = base()
        rows, _ = mutated({"tr_AT14_rampB": [(50, -1e-9)]})
        self.assertEqual(res(rows, "AT14-bound-tr-range"), "FAIL")
        rows, _ = mutated({"tr_AT14_rampB": [(50, -5e-16)]})
        self.assertEqual(res(rows, "AT14-bound-tr-range"), "PASS")
        rows, _ = mutated({"tr_AT14_rampB": [(0, -1e-3)]})                     # row 0 is not read (no previous close)
        self.assertEqual(res(rows, "AT14-bound-tr-range"), "PASS")

    def test_the_old_relative_bound_is_unchanged_without_abs(self):
        """A spec without [tolerances.bound].abs keeps the old row tolerance |bound| x tol (the older specs' behaviour)."""
        spec, cs, x, bars, raw = base()
        cs2 = copy.deepcopy(cs)
        cs2["tol_bound_abs"] = 0.0
        rows, _ = C.evaluate(cs2, raw)
        m = {r["check_id"]: r for r in rows}
        self.assertEqual(m["ATR-AT14-bound-atr"]["tolerance"], 0.0)
        self.assertEqual(m["ATR-AT14-bound-atr"]["result"], "PASS")


class ImpAndFloor(unittest.TestCase):
    def test_imp_rows_pass_and_must_fail_fire(self):
        spec, cs, x, bars, raw = base()
        rows, _ = C.evaluate(cs, raw)
        imp = {r["check_id"]: r for r in rows if r["role"] == "imp"}
        self.assertEqual(len(imp), 9 + 2)
        for vid in ("AT14", "AT20") + A.CONTROLS:
            self.assertEqual(imp["ATR-%s-imp-pass" % vid]["result"], "PASS", vid)
            self.assertEqual(imp["ATR-%s-imp-pass" % vid]["actual"], 0.0)
        self.assertEqual(imp["ATR-AT14-imp-fail"]["result"], "PASS")
        self.assertGreater(imp["ATR-AT14-imp-fail"]["ratio"], 1e6)
        self.assertEqual(imp["ATR-NCS-imp-fail"]["result"], "PASS")
        self.assertGreater(imp["ATR-NCS-imp-fail"]["ratio"], 1e6)

    def test_imp_fires_when_a_real_variant_is_replayed_with_the_wrong_model(self):
        """Guard seen to fire: AT14's exported columns replayed with the AT20 model (wrong period) exceed the tolerance."""
        spec, cs, x, bars, raw = base()
        cs2 = copy.deepcopy(cs)
        cs2["imp"]["must_pass"]["AT14"] = "atr_mt4(20)"
        rows = C.imp_rows(cs2, raw)
        r = [q for q in rows if q["check_id"] == "ATR-AT14-imp-pass"][0]
        self.assertEqual(r["result"], "FAIL")

    def test_shared_replay_in_the_wrong_order_fails_imp(self):
        """The NCS replay is order-sensitive: slots in the input-major order do not reproduce the perfect run (the lesson's failure mode)."""
        spec, cs, x, bars, raw = base()
        order = [(vid, i) for i in C.adaptive_traced(cs) for vid in ("NCS", "NCS2")]
        out = A._ncs_order_replay(cs, x, bars, order)
        wrong = max(float(np.max(np.abs(out[("NCS", "s20")].atr - raw.cols["atr_NCS_s20"]))), 0.0)
        self.assertGreater(wrong, 1e-6)

    def test_floor_rows_cover_trace_equivariance_known(self):
        spec, cs, x, bars, raw = base()
        rows, _ = C.evaluate(cs, raw)
        fl = [r["check_id"] for r in rows if r["role"] == "floor"]
        for vid in ("AT14", "AT20"):
            for k in ("trace", "equivariance", "known_value"):
                self.assertIn("ATR-%s-floor-%s" % (vid, k), fl)
        self.assertFalse(any("window_hull" in c or "bound" in c for c in fl))
        self.assertTrue(all(r["result"] == "PASS" for r in rows if r["role"] == "floor"))


if __name__ == "__main__":
    unittest.main()
