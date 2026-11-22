"""ATR stage 1: reference models (reference.atr_mt4 / atr_shared) against the planning chat's numbers (docs/harness/ATR_STAGE1_NUMBERS.py and its
saved output), items 1-6 of the brief. No .c file is read, Zorro is not run."""
import os
import re
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))

import atr_support as A   # noqa: E402
import reference as R     # noqa: E402

_N = {}


def nums():
    if "n" not in _N:
        _N["n"] = A.numbers()
    return _N["n"]


def planning_lines():
    with open(A.NUMBERS_OUT, encoding="utf-8") as f:
        return f.read().split("\n")


class ModelGrammar(unittest.TestCase):
    def test_article_model_resolves(self):
        self.assertEqual(R.adaptive_article_model("atr_mt4(14)"), R.atr_mt4(14))
        self.assertEqual(R.adaptive_article_model("atr_mt4(20)").P, 20)

    def test_restricted_grammar_refuses_everything_else(self):
        for bad in ("atr_mt4(0)", "atr_mt4(14,avg=wilder)", "atr_mt4(__import__('os'))", "atr_mt4(1e1)", "atr_mt4()", "ATR(14)", None, 14):
            self.assertIsNone(R.adaptive_article_model(bad), bad)

    def test_hooks_validated(self):
        for kw in (dict(tr_kind="x"), dict(avg="ema"), dict(first="none"), dict(startup="x")):
            with self.assertRaises(ValueError):
                R.atr_mt4(14, **kw)
        for P in (0, -1, 1.5, True, "14"):
            with self.assertRaises(ValueError):
                R.atr_mt4(P)

    def test_imp_registry_has_every_control_model(self):
        for k in ("atr_mt4(14)", "atr_mt4(20)", "atr_mt4(15)", "atr_mt4(14,first=with_tr0)", "atr_mt4(14,avg=wilder)",
                  "atr_mt4(14,tr_kind=hl)", "atr_mt4(14,startup=tr)", "atr_shared(14,14)[0]", "atr_shared(14,14)[1]"):
            self.assertIn(k, R.IMP_MODELS)
            self.assertIsNotNone(R.IMP_MODELS[k]())


class ModelVsPlanning(unittest.TestCase):
    """The tooling model against ATR_STAGE1_NUMBERS.py's model on every input, both variants (operation order may differ: rounding only)."""

    def test_atr_mt4_equals_planning_model(self):
        P = A.planning_numbers()
        inp = P.make_inputs()
        worst = 0.0
        for per in (14, 20):
            for k, (H, L, C) in inp.items():
                tr, a = P.atr_model(H, L, C, P=per)
                o = R.simulate_atr(R.atr_mt4(per), C, H, L)
                worst = max(worst, float(np.max(np.abs(o.tr - tr))), float(np.max(np.abs(o.atr - a))))
        self.assertLessEqual(worst, 1e-15)

    def test_control_models_equal_planning_hooks(self):
        P = A.planning_numbers()
        inp = P.make_inputs()
        ctl = {"NCW": (dict(P=15), R.atr_mt4(15)), "NC0": (dict(first="with_tr0"), R.atr_mt4(14, first="with_tr0")),
               "NCWi": (dict(avg="wilder"), R.atr_mt4(14, avg="wilder")), "NCR": (dict(tr_kind="hl"), R.atr_mt4(14, tr_kind="hl")),
               "NCZ": (dict(startup="tr"), R.atr_mt4(14, startup="tr"))}
        for c, (kw, m) in ctl.items():
            kw = dict(kw)
            kw.setdefault("P", 14)
            worst = 0.0
            for k, (H, L, C) in inp.items():
                tr, a = P.atr_model(H, L, C, **kw)
                o = R.simulate_atr(m, C, H, L)
                worst = max(worst, float(np.max(np.abs(o.tr - tr))), float(np.max(np.abs(o.atr - a))))
            self.assertLessEqual(worst, 1e-15, c)


class Item1Conditioning(unittest.TestCase):
    """Item 1: every (input, column) pair classified CHECKED, none INFO; every printed value of the planning output reproduced by the tooling's
    classifier (same seed and draw order)."""

    def test_no_info_pairs_and_all_values_reproduce(self):
        n = nums()
        self.assertEqual(n["info"], {"AT14": {}, "AT20": {}})
        sec, seen = None, 0
        for ln in planning_lines():
            m = re.match(r"===== (AT\d+)", ln)
            if m:
                sec = m.group(1)
            m = re.match(r"\s+(\w+)\s+tr ([\d.e+-]+)\s+atr ([\d.e+-]+)\s+-> (\w+)", ln)
            if m and sec:
                i = m.group(1)
                self.assertEqual(m.group(4), "checked")
                self.assertEqual("%.3e" % n["conditioning"][sec][i]["tr"], m.group(2), (sec, i))
                self.assertEqual("%.3e" % n["conditioning"][sec][i]["atr"], m.group(3), (sec, i))
                seen += 1
        self.assertEqual(seen, 32)

    def test_every_pair_far_below_the_bound(self):
        n = nums()
        for v, d in n["conditioning"].items():
            for i, c in d.items():
                for col, val in c.items():
                    self.assertLessEqual(val, 1e-13 / 100, (v, i, col))      # largest 4.4e-16: > 200x below the 1e-13 bound


class Items2to5(unittest.TestCase):
    def test_item2_known_answers_and_startup(self):
        F = nums()["findings"]
        for v, bound in (("AT14", 1.2e-17), ("AT20", 1.2e-17)):
            self.assertEqual(F["known_diff_%s_flat" % v], 0.0)
            for i in ("ramp", "rampdn"):
                self.assertLessEqual(F["known_diff_%s_%s" % (v, i)], bound)
            for i in ("flatB", "rampB", "rampdnB"):
                self.assertLessEqual(F["known_diff_%s_%s" % (v, i)], 4.41e-17)
            self.assertEqual(F["zero_rows_max_%s" % v], 0.0)
        self.assertEqual(F["startup_s20_AT14"], 0.002107897511639391)
        self.assertEqual(F["startup_s20_AT20"], 0.0020000000000000018)

    def test_item3_bounds(self):
        F = nums()["findings"]
        for v in ("AT14", "AT20"):
            self.assertEqual(F["atr_min_every_input_%s" % v], 0.0)
            self.assertEqual(F["tr_minus_range_min_%s" % v], 0.0)
            self.assertEqual(F["window_hull_rel_violation_max_%s" % v], 0.0)

    def test_item4_equivariance_within_the_rule(self):
        """Planning item 4 (AT14: sc tr 1.998e-15, atr 4.701e-16; of tr 4.441e-16, atr 6.332e-17; AT20 sc atr 4.406e-16, of atr 4.510e-17). The tooling builds
        the copies the way the generated script does (High' = k High + c), the planning script as 10 x - 9.9 + 10 h: rounding differs. A difference is a finding
        only above 10x the item-1 value of that (input, column) or 1e-15 (brief)."""
        F, n = nums()["findings"], nums()
        plan = {("AT14", "sc", "tr"): 1.998e-15, ("AT14", "sc", "atr"): 4.701e-16, ("AT14", "of", "tr"): 4.441e-16, ("AT14", "of", "atr"): 6.332e-17,
                ("AT20", "sc", "atr"): 4.406e-16, ("AT20", "of", "atr"): 4.510e-17}
        for (v, t, c), pv in plan.items():
            lim = max(10 * n["conditioning"][v]["s40B"][c], 1e-15)
            self.assertLessEqual(abs(F["equiv_model_%s_%s_%s" % (v, t, c)] - pv), lim, (v, t, c))

    def test_item5_imp_estimate(self):
        F = nums()["findings"]
        for v, (tr, atr) in (("AT14", (8.882e-16, 3.782e-16)), ("AT20", (8.882e-16, 3.652e-16))):
            self.assertEqual("%.3e" % max(F[k] for k in F if k.startswith("imp_est_%s_" % v) and k.endswith("_tr")), "%.3e" % tr)
            self.assertEqual("%.3e" % max(F[k] for k in F if k.startswith("imp_est_%s_" % v) and k.endswith("_atr")), "%.3e" % atr)
        self.assertLessEqual(nums()["floor"]["trace"] * 10, 8.9e-15)


class Item6Controls(unittest.TestCase):
    def test_every_printed_atr_effect_reproduces(self):
        """The planning output's per-input atr effects (%.2e) for NCW, NC0, NCWi, NCR, NCZ equal the tooling's (within the 1% brief rule: here exact
        at 3 digits)."""
        F = nums()["findings"]
        seen = 0
        for ln in planning_lines():
            m = re.match(r"\s+(NCW|NC0|NCWi|NCR|NCZ)\s+atr\s+(.*)", ln)
            if not m:
                continue
            for kv in m.group(2).split():
                i, s = kv.split(":")
                mine, plan = F["effect_%s_atr" % m.group(1)][i], float(s)
                self.assertLessEqual(abs(mine - plan), 0.01 * max(abs(plan), 1e-17) + 1e-17, (m.group(1), i))
                seen += 1
        self.assertEqual(seen, 5 * 16)

    def test_headline_effects_and_blind_inputs(self):
        F = nums()["findings"]
        e = lambda c, col="atr": F["effect_%s_%s" % (c, col)]
        self.assertAlmostEqual(max(e("NCW").values()), 7.673e-3, delta=7.673e-3 * 0.01)
        self.assertAlmostEqual(max(e("NC0").values()), 2.738e-4, delta=2.738e-4 * 0.01)
        self.assertAlmostEqual(max(e("NCWi").values()), 1.870e-4, delta=1.870e-4 * 0.01)
        self.assertAlmostEqual(max(e("NCR").values()), 7.892e-3, delta=7.892e-3 * 0.01)
        self.assertAlmostEqual(max(e("NCR", "tr").values()), 1.176e-2, delta=1.176e-2 * 0.01)
        self.assertAlmostEqual(max(e("NCZ").values()), 9.711e-3, delta=9.711e-3 * 0.01)
        blind = lambda c: sorted(i for i, d in e(c).items() if d <= 1e-11)
        self.assertEqual(blind("NCW"), ["flat"])
        self.assertEqual(blind("NC0"), ["flat"])
        self.assertEqual(blind("NCZ"), ["flat"])
        self.assertEqual(blind("NCWi"), ["flat", "flatB", "ramp", "rampB", "rampdn", "rampdnB"])
        self.assertEqual(blind("NCR"), ["flat", "flatB", "rampB", "rampdnB"])
        first, last = F["first_row_gt_10tol_NCW_atr"], F["last_row_gt_10tol_NCW_atr"]
        self.assertEqual({v for v in first.values() if v >= 0}, {14})
        self.assertEqual({v for v in last.values() if v >= 0}, {14, 2999})
        self.assertEqual({v for v in F["first_row_gt_10tol_NCZ_atr"].values() if v >= 0}, {1})
        self.assertEqual({v for v in F["last_row_gt_10tol_NCZ_atr"].values() if v >= 0}, {13})
        self.assertEqual({v for v in F["first_row_gt_10tol_NCWi_atr"].values() if v >= 0}, {15})


class SharedStateOrder(unittest.TestCase):
    """MAF lesson 1: NCS numbers come from the call order of the GENERATED script, never from the input list."""

    def test_generated_order_is_variant_major_and_parsed_from_the_script(self):
        n = nums()
        o = n["generated_order"]
        self.assertEqual(len(o), 32)
        self.assertEqual([v for v, _ in o], ["NCS"] * 16 + ["NCS2"] * 16)
        self.assertEqual([i for _, i in o[:16]], [i for _, i in o[16:]])
        # the generator's input order: base inputs (flat, sines, ramp, rampdn), then the band inputs in [inputs].band_inputs order
        self.assertEqual([i for _, i in o[:16]], ["flat", "s5", "s10", "s20", "s40", "s100", "ramp", "rampdn",
                                                   "flatB", "rampB", "rampdnB", "s5B", "s10B", "s20B", "s40B", "s100B"])

    def test_checker_slots_equal_the_script_order(self):
        import checker as C
        spec, cs, x, bars = A.load()
        slots = C.adaptive_shared_slots(cs, R.atr_shared((14, 14), 0))
        self.assertEqual([(v, i) for v, i, _ in slots], A.generated_call_order(spec, ("NCS", "NCS2")))

    def test_order_matters_and_no_instance_input_pair_is_weak(self):
        """The two assumed planning orders give different numbers than the generated order (min 2.570e-3 here vs 2.581e-3 / 3.265e-3 assumed); every
        (instance, input) differs from AT14 by >= 10x the trace tolerance in the generated order (the brief expects none below)."""
        n = nums()
        g, alt = n["ncs"]["generated"], n["ncs"]["input_major"]
        self.assertEqual(len(g), 32)
        self.assertGreater(min(v["ratio"] for v in g.values()), 10.0)
        self.assertGreater(min(v["ratio"] for v in alt.values()), 10.0)
        self.assertNotEqual(min(v["effect"] for v in g.values()), min(v["effect"] for v in alt.values()))
        self.assertGreater(max(abs(g[k]["effect"] - alt[k]["effect"]) for k in g), 1e-6)

    def test_shared_model_against_manual_two_slot_run(self):
        """Hand-rolled replay of the NCS body for two slots on one input (same bars): independent of simulate_atr_shared's code path."""
        spec, cs, x, bars = A.load()
        xs, Hs, Ls = x["s20B"], bars["s20B"][0], bars["s20B"][1]
        out = R.simulate_atr_shared([14, 14], [xs, xs], [Hs, Hs], [Ls, Ls])
        trs = R._atr_tr(Hs, Ls, xs, "mt4")
        prev, a1, a2 = 0.0, np.zeros(len(xs)), np.zeros(len(xs))
        for t in range(len(xs)):
            for arr in (a1, a2):
                v = 0.0
                if t + 1 == 15:
                    v = sum(trs[t - i] for i in range(14)) / 14
                elif t + 1 > 15:
                    v = prev + (trs[t] - trs[t - 14]) / 14
                prev = v
                arr[t] = v
        np.testing.assert_array_equal(out[0].atr, a1)
        np.testing.assert_array_equal(out[1].atr, a2)
        self.assertGreater(float(np.max(np.abs(out[1].atr - R.simulate_atr(R.atr_mt4(14), xs, Hs, Ls).atr))), 1e-4)


if __name__ == "__main__":
    unittest.main()
