"""Acceptance tests for the NNFX reference engine (Phase 1 step 4, stage S2).

Scenarios A1..F2 as reviewed 2026-11-22 (planning chat). Conventions:
  ATR = 0.0100; baseline 0.9950 unless stated; spread 0 unless stated.
  Bar 0 = pre-bar (C1 = -1). Bar 1 = signal bar (C1 = +1, close 1.0000).
  Entry at bar 2's open = 1.0000 for both halves: stop 0.9850, TP1 1.0100,
  trail on a close >= 1.0200, trail 0.0150 behind the best close. R = 0.0150 per half.
Expected values are hand-calculated (they are the test, not the engine's output).
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import reference_engine as E  # noqa: E402

A = 0.0100
BL = 0.9950
PRE = (0.9990, 1.0000, 0.9980, 0.9990)
SIG = (0.9995, 1.0005, 0.9990, 1.0000)
EPS = 10


def scen(rows, c1=None, c2=None, vol=None, baseline=None, ex=None, prefix=True, **params):
    """rows = bars from bar 2 on (prefix=True) or all bars (prefix=False)."""
    bars = ([PRE, SIG] if prefix else []) + list(rows)
    n = len(bars)
    if c1 is None:
        c1 = [-1] + [1] * (n - 1)
    return dict(
        o=[b[0] for b in bars], h=[b[1] for b in bars], l=[b[2] for b in bars], c=[b[3] for b in bars],
        baseline=baseline or [BL] * n, atr=[A] * n, c1=c1, c2=c2 or [1] * n,
        vol=vol or [True] * n, ex=ex or [0] * n, params=E.Params(**params))


def run(s):
    kw = dict(s)
    p = kw.pop("params")
    return E.run(p=p, **kw)


def mirror(s):
    """Reflect prices around 1.0 (p -> 2 - p), swap high/low, negate states."""
    m = dict(s)
    m["o"] = [2 - x for x in s["o"]]
    m["c"] = [2 - x for x in s["c"]]
    m["h"] = [2 - x for x in s["l"]]
    m["l"] = [2 - x for x in s["h"]]
    m["baseline"] = [2 - x for x in s["baseline"]]
    m["c1"] = [-x for x in s["c1"]]
    m["c2"] = [-x for x in s["c2"]]
    m["ex"] = [-x for x in s["ex"]]
    return m


class Base(unittest.TestCase):
    def half(self, res, k):
        return res.halves[k]

    def assertHalf(self, hf, reason, exit_price, pnl=None):
        self.assertEqual(hf.reason, reason)
        self.assertAlmostEqual(hf.exit_price, exit_price, EPS)
        if pnl is not None:
            self.assertAlmostEqual(hf.pnl, pnl, EPS)


# ---------------------------------------------------------------- scenarios
def s_A1():
    return scen([(1.0000, 1.0050, 0.9840, 0.9860)])


def s_A2():
    return scen([(1.0000, 1.0110, 0.9990, 1.0050), (1.0040, 1.0060, 0.9990, 1.0010)])


def s_A3():
    return scen([(1.0000, 1.0110, 0.9845, 1.0000)])


def s_A4():
    return scen([(1.0000, 1.0020, 0.9990, 1.0010), (0.9800, 0.9820, 0.9780, 0.9810)])


def s_A5():
    return scen([(1.0000, 1.0050, 0.9990, 1.0040), (1.0130, 1.0150, 1.0120, 1.0140)])


def s_A6():
    return scen([(1.0000, 1.0110, 0.9990, 0.9980), (0.9975, 0.9985, 0.9965, 0.9980)])


def s_P1():
    """Entry bar opens away from the signal close (probe P1): fill at 1.0010, not 1.0000."""
    return scen([(1.0010, 1.0030, 1.0000, 1.0020), (1.0020, 1.0030, 1.0010, 1.0025)])


def s_B1():
    return scen([(1.0000, 1.0110, 0.9990, 1.0090), (1.0090, 1.0220, 1.0080, 1.0210),
                 (1.0210, 1.0310, 1.0200, 1.0300), (1.0300, 1.0310, 1.0240, 1.0250),
                 (1.0250, 1.0260, 1.0140, 1.0160)])


def s_B2():
    return scen([(1.0000, 1.0110, 0.9990, 1.0090), (1.0090, 1.0200, 1.0080, 1.0190),
                 (1.0190, 1.0195, 1.0050, 1.0060), (1.0060, 1.0070, 0.9995, 1.0005)])


def s_C1():
    rows = [(1.0000, 1.0020, 0.9990, 1.0010), (1.0010, 1.0030, 1.0000, 1.0020), (1.0015, 1.0025, 1.0005, 1.0020)]
    return scen(rows, c1=[-1, 1, 1, -1, -1])


def s_C2():
    rows = [(1.0000, 1.0020, 0.9990, 1.0010), (1.0010, 1.0015, 0.9935, 0.9940), (0.9945, 0.9950, 0.9930, 0.9940)]
    return scen(rows)


def s_C3():
    rows = [(1.0000, 1.0020, 0.9990, 1.0010), (1.0010, 1.0030, 1.0000, 1.0020), (1.0015, 1.0025, 1.0005, 1.0020)]
    return scen(rows, c1=[-1, 1, 1, 0, 0])


# D / E scenarios as named functions (2026-11-23, S4 coverage set d): the same bars, states and
# parameters as the former inline test helpers, so every expected value is unchanged. Named so
# that tools/make_scenarios.py can write each one as a Zorro scenario.
def _d1(c2v):
    return scen([(1.0000, 1.0020, 0.9990, 1.0010)], c2=[1, c2v, 1])


def s_D1a():
    return _d1(-1)


def s_D1b():
    return _d1(0)


def s_D1d():
    return scen([(1.0000, 1.0020, 0.9990, 1.0010), (1.0010, 1.0020, 1.0000, 1.0010)], baseline=[0.9880] * 4)


def s_D2():
    return scen([(1.0000, 1.0020, 0.9990, 1.0010)], volume_mode="ALWAYS_NO")


def _cross(c3, c2_3=1):
    bars = [(0.9935, 0.9945, 0.9925, 0.9930), (0.9930, 0.9945, 0.9925, 0.9940),
            (0.9940, 0.9995, 0.9935, 0.9990), (0.9990, 1.0035, 0.9985, c3),
            (1.0030, 1.0040, 1.0020, 1.0035)]
    return scen(bars, prefix=False, c1=[-1, 1, 1, 1, 1], c2=[1, 1, -1, c2_3, 1])


def s_D5():
    return _cross(1.0030)


def s_D6():
    return _cross(0.9940)


def _btf(age, btf_on):
    below = (0.9935, 0.9945, 0.9925, 0.9940)
    bars = [below] * (1 + age) + [(0.9940, 0.9995, 0.9935, 0.9990), (0.9990, 1.0000, 0.9980, 0.9995)]
    n = len(bars)
    return scen(bars, prefix=False, c1=[-1] + [1] * (n - 1), btf_on=btf_on)


def s_D7a():
    return _btf(7, True)


def s_D7b():
    return _btf(6, True)


def s_D7c():
    return _btf(7, False)


def _pull(c3, c4):
    bars = [(0.9935, 0.9945, 0.9925, 0.9940), (0.9940, 0.9950, 0.9935, 0.9945),
            (0.9945, 1.0085, 0.9940, 1.0080), (1.0080, 1.0085, 1.0000, c3),
            (1.0040, 1.0070, 1.0020, c4), (1.0030, 1.0040, 1.0020, 1.0030)]
    return scen(bars, prefix=False, c1=[-1, 1, 1, 1, 1, 1])


def s_D8():
    return _pull(1.0040, 1.0050)


def s_D9():
    return _pull(1.0060, 1.0030)


def _cont(c2_5=1, dip=False):
    rows = [(1.0000, 1.0020, 0.9990, 1.0010), (1.0010, 1.0030, 1.0000, 1.0020),
            (1.0015, 1.0025, 0.9930 if dip else 1.0005, 0.9940 if dip else 1.0020),
            (1.0020, 1.0105, 1.0015, 1.0100), (1.0100, 1.0110, 1.0090, 1.0100)]
    c1 = [-1, 1, 1, -1, -1, 1, 1]
    c2 = [1, 1, 1, 1, 1, c2_5, 1]
    vol = [True, True, False, False, False, False, False]
    return scen(rows, c1=c1, c2=c2, vol=vol, volume_mode="INDICATOR")


def s_E1():
    return _cont()


def s_E2():
    return _cont(dip=True)


def s_E3():
    return _cont(c2_5=-1)


def _after_stop(cont_after_stop):
    rows = [(1.0000, 1.0010, 0.9840, 0.9960), (0.9960, 1.0000, 0.9955, 0.9990),
            (0.9990, 1.0010, 0.9985, 1.0000), (1.0000, 1.0105, 0.9995, 1.0100),
            (1.0100, 1.0110, 1.0090, 1.0100)]
    c1 = [-1, 1, 1, 1, -1, 1, 1]
    vol = [True, True] + [False] * 5
    return scen(rows, c1=c1, vol=vol, volume_mode="INDICATOR", cont_after_stop=cont_after_stop)


def s_E4a():
    return _after_stop(True)


def s_E4b():
    return _after_stop(False)


def s_R1():
    """Reversal (2026-11-23, S4 set d): C1 flips short at a close below the baseline while long.
    Bar 3 closes 0.9930 (< baseline 0.9950, within 1 ATR), C1 -> -1, C2 -1: exit the long (c1_flip)
    and enter short, both at bar 4's open 0.9935 (the only scenario where an exit and an opposite
    entry share one close: Hedge mode M-D5 and order sequence)."""
    rows = [(1.0000, 1.0040, 0.9990, 1.0020), (1.0020, 1.0025, 0.9925, 0.9930),
            (0.9935, 0.9945, 0.9915, 0.9920), (0.9920, 0.9925, 0.9830, 0.9850)]
    return scen(rows, c1=[-1, 1, 1, -1, -1, -1], c2=[1, 1, 1, -1, -1, -1])



class StopsTargetsGaps(Base):
    def test_A1_stop(self):
        r = run(s_A1())
        self.assertEqual(len(r.halves), 2)
        for hf in r.halves:
            self.assertHalf(hf, "stop", 0.9850, -0.0150)
            self.assertAlmostEqual(hf.r, -1.0, EPS)
        self.assertAlmostEqual(r.halves[0].entry, 1.0000, EPS)

    def test_A2_tp1_then_breakeven(self):
        r = run(s_A2())
        self.assertHalf(r.halves[0], "tp1", 1.0100, 0.0100)
        self.assertHalf(r.halves[1], "be", 1.0000, 0.0)
        self.assertEqual(r.halves[1].exit_bar, 3)

    def test_A3_same_bar_stop_first(self):
        r = run(s_A3())
        for hf in r.halves:
            self.assertHalf(hf, "stop", 0.9850, -0.0150)
        self.assertEqual(r.same_bar_conflicts, 1)

    def test_A4_gap_through_stop_fills_at_open(self):
        r = run(s_A4())
        for hf in r.halves:
            self.assertHalf(hf, "stop", 0.9800, -0.0200)

    def test_A5_gap_through_tp1_fills_at_open(self):
        r = run(s_A5())
        self.assertHalf(r.halves[0], "tp1", 1.0130, 0.0130)

    def test_A6_breakeven_due_but_close_below_entry(self):
        r = run(s_A6())
        self.assertHalf(r.halves[0], "tp1", 1.0100)
        self.assertHalf(r.halves[1], "be_adverse", 0.9975, -0.0025)
        self.assertEqual(r.halves[1].exit_bar, 3)
        self.assertEqual(r.be_adverse_exits, 1)


class NextOpenFill(Base):
    def test_P1_entry_at_next_open_not_signal_close(self):
        r = run(s_P1())
        for hf in r.halves:
            self.assertAlmostEqual(hf.entry, 1.0010, EPS)
            self.assertAlmostEqual(hf.stop, 1.0010 - 0.0150, EPS)
            self.assertEqual(hf.reason, "end")
        self.assertAlmostEqual(r.halves[0].tp, 1.0110, EPS)


class Trailing(Base):
    def test_B1_trail_activates_moves_on_closes_and_exits(self):
        r = run(s_B1())
        self.assertHalf(r.halves[1], "trail", 1.0150, 0.0150)
        self.assertAlmostEqual(r.halves[1].r, 1.0, EPS)
        self.assertEqual(r.halves[1].exit_bar, 6)

    def test_B2_close_below_two_atr_no_trail(self):
        r = run(s_B2())
        self.assertHalf(r.halves[1], "be", 1.0000, 0.0)
        self.assertEqual(r.halves[1].exit_bar, 5)


class CloseDecidedExits(Base):
    def test_C1_c1_flip_exits_at_next_open(self):
        r = run(s_C1())
        for hf in r.halves:
            self.assertHalf(hf, "c1_flip", 1.0015)
            self.assertEqual(hf.exit_bar, 4)

    def test_C2_baseline_close_exits_at_next_open(self):
        r = run(s_C2())
        for hf in r.halves:
            self.assertHalf(hf, "baseline", 0.9945)
            self.assertEqual(hf.exit_bar, 4)

    def test_C3_c1_to_zero_does_not_exit(self):
        r = run(s_C3())
        for hf in r.halves:
            self.assertEqual(hf.reason, "end")


class SignalDefinition(unittest.TestCase):
    def test_D3_same_side_through_zero_is_not_a_signal(self):
        self.assertEqual(E.signals([1, 0, 1]), [0, 0, 0])

    def test_D4_opposite_side_through_zero_is_a_signal(self):
        self.assertEqual(E.signals([-1, 0, 1]), [0, 0, 1])

    def test_first_nonzero_is_not_a_signal(self):
        self.assertEqual(E.signals([0, 1, 1, -1]), [0, 0, 0, -1])


class EntriesAndBlocks(Base):
    def test_D1_c2_against_or_zero_blocks(self):
        for f in (s_D1a, s_D1b):
            self.assertEqual(run(f()).halves, [], f.__name__)

    def test_D1_distance_over_one_atr_blocks_without_pullback(self):
        self.assertEqual(run(s_D1d()).halves, [])

    def test_D2_volume_always_no_blocks(self):
        self.assertEqual(run(s_D2()).halves, [])

    def test_D5_baseline_cross_with_catch_up(self):
        r = run(s_D5())
        self.assertEqual(len(r.halves), 2)
        self.assertEqual(r.halves[0].entry_bar, 4)
        self.assertEqual(r.halves[0].kind, "baseline")
        self.assertAlmostEqual(r.halves[0].entry, 1.0030, EPS)

    def test_D6_close_back_across_kills_catch_up(self):
        self.assertEqual(run(s_D6()).halves, [])

    def test_D7_bridge_too_far(self):
        self.assertEqual(run(s_D7a()).halves, [])
        self.assertEqual(len(run(s_D7b()).halves), 2)
        self.assertEqual(len(run(s_D7c()).halves), 2)

    def test_D7_refusal_recorded(self):
        # PERF2 T1: the engine records each bridge-too-far skip as the template's REFUSED row does (once per refused cross)
        r = run(s_D7a())
        self.assertEqual(len(r.refusals), 1)
        self.assertEqual(r.refusals[0][1:], (1, "bridge-too-far"))
        self.assertEqual(r.refusals[0][0], 8)        # the cross bar: 1 + age = 8 bars below, cross on bar index 8
        self.assertEqual(run(s_D7b()).refusals, [])
        self.assertEqual(run(s_D7c()).refusals, [])

    def test_D8_pullback_one_candle_then_entry(self):
        r = run(s_D8())
        self.assertEqual(len(r.halves), 2)
        self.assertEqual(r.halves[0].entry_bar, 4)
        self.assertEqual(r.halves[0].kind, "pullback")

    def test_D9_pullback_missed_no_later_entry(self):
        self.assertEqual(run(s_D9()).halves, [])


class Continuation(Base):
    def test_E1_continuation_waives_volume_and_distance(self):
        r = run(s_E1())
        self.assertEqual(len(r.halves), 4)
        self.assertEqual(r.halves[0].reason, "c1_flip")
        self.assertEqual(r.halves[2].kind, "continuation")
        self.assertEqual(r.halves[2].entry_bar, 6)

    def test_E2_baseline_close_in_between_kills_continuation(self):
        self.assertEqual(len(run(s_E2()).halves), 2)

    def test_E3_c2_against_blocks_continuation(self):
        self.assertEqual(len(run(s_E3()).halves), 2)

    def test_E4_continuation_after_stop_needs_new_signal(self):
        r = run(s_E4a())
        self.assertEqual(len(r.halves), 4)
        self.assertEqual(r.halves[0].reason, "stop")
        self.assertEqual(r.halves[2].kind, "continuation")
        self.assertEqual(r.halves[2].entry_bar, 6)

    def test_E4_variant_no_continuation_after_stop(self):
        self.assertEqual(len(run(s_E4b()).halves), 2)


class Reversal(Base):
    """R1, hand-calculated 2026-11-23 (ATR 0.0100; short entry 0.9935: stop 1.0085, TP1 0.9835)."""

    def test_R1_c1_flip_exit_and_opposite_entry_same_close(self):
        r = run(s_R1())
        self.assertEqual(len(r.halves), 4)
        for hf in r.halves[:2]:
            self.assertEqual(hf.dir, E.LONG)
            self.assertHalf(hf, "c1_flip", 0.9935, -0.0065)
            self.assertEqual(hf.exit_bar, 4)
        s1, s2 = r.halves[2], r.halves[3]
        for hf in (s1, s2):
            self.assertEqual(hf.dir, E.SHORT)
            self.assertEqual(hf.kind, "c1")
            self.assertEqual(hf.entry_bar, 4)
            self.assertAlmostEqual(hf.entry, 0.9935, EPS)
        self.assertAlmostEqual(s1.tp, 0.9835, EPS)
        # bar 5 low 0.9830 reaches TP1 0.9835; stop 1.0085 never touched (bar highs <= 0.9945)
        self.assertHalf(s1, "tp1", 0.9835, 0.0100)
        self.assertEqual(s1.exit_bar, 5)
        # bar 5 closes 0.9850, beyond entry for a short: breakeven, runner stop 1.0085 -> 0.9935;
        # history ends at bar 5, runner closed at that close (reason "end")
        self.assertAlmostEqual(s2.stop, 0.9935, EPS)
        self.assertEqual(s2.stop_reason, "be")
        self.assertHalf(s2, "end", 0.9850, 0.0085)


class CostsAndSymmetry(Base):
    def test_F1_spread_costs_each_half_exactly(self):
        off = run(s_A2())
        s = s_A2()
        s["params"] = E.Params(spread=0.0002)
        on = run(s)
        for a, b in zip(off.halves, on.halves):
            self.assertAlmostEqual(a.pnl - b.pnl, 0.0002, EPS)

    def test_F2_short_mirror_identical(self):
        for f in (s_A1, s_A2, s_A3, s_A4, s_A5, s_A6, s_B1, s_B2, s_C1, s_C2, s_C3, s_R1):
            lo, sh = run(f()), run(mirror(f()))
            self.assertEqual(len(lo.halves), len(sh.halves), f.__name__)
            for a, b in zip(lo.halves, sh.halves):
                self.assertEqual(b.dir, -a.dir, f.__name__)
                self.assertEqual(a.reason, b.reason, f.__name__)
                self.assertAlmostEqual(a.pnl, b.pnl, EPS, f.__name__)
                self.assertAlmostEqual(a.r, b.r, EPS, f.__name__)


class ConfigAgreement(unittest.TestCase):
    def test_params_defaults_match_light_c_config(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
        cfg = E.read_config(os.path.join(root, "strategies", "template", "NNFX_Config.h"))
        p = E.Params()
        for name, attr in E.CONFIG_MAP.items():
            self.assertAlmostEqual(cfg[name], getattr(p, attr), 12, name)


if __name__ == "__main__":
    unittest.main()
