"""Tests for tools/r1_replay.py: the M1 resolver on hand-built records with known answers, and its use by the engine."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import r1_data as D  # noqa: E402
import r1_replay as RP  # noqa: E402

E = RP.E


def m1(recs):
    """recs: list of (o, h, l, c); one minute apart."""
    a = np.zeros(len(recs), dtype=D.REC_DT)
    for i, (o, h, l, c) in enumerate(recs):
        a[i] = (45000 + i / 1440.0, h, l, o, c, 0, 0)
    return a


def bars_one(n):
    return dict(i0=np.array([0]), i1=np.array([n - 1]), keep=None)


def half(d, stop, tp, entry_bar=1, stop_reason="stop"):
    h = E.Half(d, 1 if tp is not None else 2, 1, "c1", entry_bar, 1.0, 0.01, stop, tp)
    h.stop_reason = stop_reason
    return h


class Resolver(unittest.TestCase):
    def ev(self, recs, halves, start="entry"):
        return RP.resolver(m1(recs), bars_one(len(recs)), start)(0, halves)

    def test_long_stop_inside_record_fills_at_level(self):
        h = half(1, 0.99, None)
        out = self.ev([(1.0, 1.001, 0.995, 0.996), (0.996, 0.997, 0.985, 0.986)], [h])
        self.assertEqual([(x[1], x[2]) for x in out], [(0.99, "stop")])

    def test_long_stop_gap_fills_at_record_open(self):
        h = half(1, 0.99, None)
        out = self.ev([(1.0, 1.001, 0.995, 0.996), (0.985, 0.986, 0.980, 0.981)], [h])
        self.assertAlmostEqual(out[0][1], np.float32(0.985), places=12)

    def test_tp_then_runner_stop_in_time_order(self):
        h1, h2 = half(1, 0.985, 1.01), half(1, 0.985, None)
        out = self.ev([(1.0, 1.011, 0.999, 1.0), (1.0, 1.0, 0.98, 0.981)], [h1, h2])
        self.assertEqual([(x[0].half, x[2]) for x in out], [(1, "tp"), (2, "stop")])
        self.assertAlmostEqual(out[0][1], 1.01, places=12)

    def test_stop_and_tp_in_one_record_stop_first(self):
        h1, h2 = half(1, 0.985, 1.01), half(1, 0.985, None)
        out = self.ev([(1.0, 1.02, 0.98, 1.0)], [h1, h2])
        self.assertEqual([x[2] for x in out], ["stop", "stop"])

    def test_start_after_skips_entry_record(self):
        h = half(1, 0.99, None, entry_bar=0)
        rec = [(1.0, 1.0, 0.98, 0.985), (0.985, 0.986, 0.984, 0.985)]
        out_e = self.ev(rec, [h], "entry")
        out_a = self.ev(rec, [h], "after")
        self.assertAlmostEqual(out_e[0][1], 0.99, places=12)                  # touched in the entry record
        self.assertAlmostEqual(out_a[0][1], np.float32(0.985), places=12)    # next record opens below: its open

    def test_short_mirror(self):
        h = half(-1, 1.01, 0.99)
        out = self.ev([(1.0, 1.0, 0.995, 0.996), (0.996, 0.997, 0.985, 0.986)], [h])
        self.assertEqual((out[0][1], out[0][2]), (0.99, "tp"))
        h = half(-1, 1.01, None)
        out = self.ev([(1.0, 1.0, 0.995, 0.996), (1.02, 1.03, 1.019, 1.02)], [h])
        self.assertAlmostEqual(out[0][1], np.float32(1.02), places=12)

    def test_no_event(self):
        self.assertEqual(self.ev([(1.0, 1.001, 0.999, 1.0)], [half(1, 0.99, 1.01)]), [])


class EngineWithM1(unittest.TestCase):
    """Five daily bars of 3 records each; C1 turns long at bar 1 (all slots agree), entry at bar 2's fill price;
    bar 3's records hit TP1 then (bar 4) the original stop for the runner (breakeven not yet active on bar 3's close?
    it is: TP1 on bar 3 -> breakeven from bar 4 -> runner closed at entry)."""

    def test_entry_at_open_fill_and_m1_exits(self):
        recs = [(1.0, 1.0, 1.0, 1.0)] * 3 + [(1.0, 1.0, 1.0, 1.0)] * 3 + \
               [(1.0005, 1.001, 1.0, 1.0002)] * 3 + \
               [(1.001, 1.012, 1.0, 1.008), (1.008, 1.009, 1.006, 1.007), (1.007, 1.008, 1.006, 1.007)] + \
               [(1.006, 1.007, 0.99, 0.995), (0.995, 0.996, 0.994, 0.995), (0.995, 0.996, 0.994, 0.995)]
        a = m1(recs)
        bars = dict(i0=np.array([0, 3, 6, 9, 12]), i1=np.array([2, 5, 8, 11, 14]), keep=None)
        o = [1.0, 1.0, 1.0005, 1.001, 1.006]
        h = [1.0, 1.0, 1.001, 1.012, 1.007]
        l = [1.0, 1.0, 1.0, 1.0, 0.99]
        c = [1.0, 1.0, 1.0002, 1.007, 0.995]
        base = [0.999] * 5
        atr = [0.01] * 5
        c1 = [-1, 1, 1, 1, 1]
        c2 = [1] * 5
        res = E.run(o, h, l, c, base, atr, c1, c2, open_fill=RP.open_fill(a, bars, "close"),
                    intrabar=RP.resolver(a, bars, "entry"))
        e = float(np.float32(1.0002))       # bar 2's first record close (fill_px "close")
        self.assertEqual(len(res.halves), 2)
        h1, h2 = res.halves
        self.assertAlmostEqual(h1.entry, e, places=12)
        self.assertEqual((h1.reason, h1.exit_bar), ("tp1", 3))
        self.assertAlmostEqual(h1.exit_price, e + 0.01, places=12)
        self.assertEqual((h2.reason, h2.exit_bar), ("be", 4))
        self.assertAlmostEqual(h2.exit_price, e, places=12)


if __name__ == "__main__":
    unittest.main()
