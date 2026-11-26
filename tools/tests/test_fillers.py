"""Tests for r1_data.insert_fillers / check_r1.match_bars(fillers=...) (C1S2 Amendment 1: Zorro's gap filler bars).
Each case is seen to fail on a planted defect."""
import datetime as dt
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import check_r1 as C  # noqa: E402
import r1_data as D  # noqa: E402
import r1_replay as RP  # noqa: E402
from test_check_r1 import m1_days, rbar_from  # noqa: E402


def m1_hole():
    """m1_days() with every record of the Tue 2024-03-05 bar (Mon 17:00 .. Tue 17:00 New York) removed: a quote hole."""
    a = m1_days()
    lo = D.dt_to_ole(dt.datetime(2024, 3, 4, 17, tzinfo=D.NY).astimezone(D.UTC))
    hi = D.dt_to_ole(dt.datetime(2024, 3, 5, 17, tzinfo=D.NY).astimezone(D.UTC))
    return a[~((a["t"] > lo) & (a["t"] <= hi))]


def zorro_rows(m1, fill):
    """Zorro-like RBAR rows: record bars plus one flat filler bar on 2024-03-05 repeating the last quote before the hole."""
    b = D.daily_bars(m1)
    rows = rbar_from(b)
    last = m1[np.searchsorted(m1["t"], D.dt_to_ole(dt.datetime(2024, 3, 4, 17, tzinfo=D.NY).astimezone(D.UTC)),
                              side="right") - 1]
    o, h, l, c = (float(last[k]) for k in ("o", "h", "l", "c"))
    w = D.dt_to_ole(dt.datetime(2024, 3, 5, 17, tzinfo=D.NY).astimezone(D.UTC))
    rows.insert(1, dict(bar=1, ymd=20240305, w=w, lb=0, o=o, h=h, l=l, c=c))
    fill[20240305] = (o, h, l, c)
    return rows


class Fillers(unittest.TestCase):
    def setUp(self):
        self.m1 = m1_hole()
        self.fill = {}
        self.rows = zorro_rows(self.m1, self.fill)
        self.assertEqual([r["ymd"] for r in self.rows], [20240304, 20240305, 20240306])

    def test_without_fillers_fails(self):          # the EUR/JPY bar run 1 FAIL, reproduced
        var, allv = C.match_bars(self.m1, self.rows)
        self.assertIsNone(var)

    def test_with_fillers_matches(self):
        var, allv = C.match_bars(self.m1, self.rows, fillers=self.fill)
        self.assertEqual(var, D.BAR_RULE)
        b = allv[var][1]
        self.assertEqual(b["i1"][1], b["i0"][1] - 1)                    # no records in the filler bar
        self.assertEqual(b["i0"][1], b["i0"][2])                        # i0 = first record after it

    def test_planted_wrong_value_fails(self):
        bad = {k: (o, h + 0.001, l, c) for k, (o, h, l, c) in self.fill.items()}
        var, _ = C.match_bars(self.m1, self.rows, fillers=bad)
        self.assertIsNone(var)

    def test_filler_on_a_day_with_records_refused(self):
        with self.assertRaises(ValueError):
            D.daily_bars(self.m1, fillers={20240306: (1, 1, 1, 1)})
        with self.assertRaises(ValueError):                             # day with records but no bar of its own: also refused
            D.daily_bars(m1_days(), fillers={20240305: (1, 1, 1, 1)})

    def test_market_fill_on_filler_bar_at_next_record(self):
        b = D.daily_bars(self.m1, fillers=self.fill)
        px = RP.open_fill(self.m1, b)
        self.assertEqual(px[1], float(self.m1["o"][b["i0"][2]]))
        self.assertEqual(px[1], px[2])


if __name__ == "__main__":
    unittest.main()
