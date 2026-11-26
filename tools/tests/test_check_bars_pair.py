"""Tests for tools/check_bars_pair.py (C1S2 V-b): each check passes on consistent input and fails on a planted defect."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check_bars_pair as B  # noqa: E402
import check_r1 as C  # noqa: E402

INFO = dict(type="1", LookBack="520", TICKS="1", TradeModeFRC="1", Fill="3", BarOffset="1020", StartWeek="71700",
            AtrLen="14", StartDate="20120201", EndDate="20260115", PIP="0.0100000000", PIPCost="0.0581020000",
            Spread="0.0230000000", RollLong="0.282800", RollShort="-0.606800", FastLimit="0.500000", SlowLimit="0.050000")


def bars(n=700, seed=5):
    rng = np.random.default_rng(seed)
    c = 150 + np.cumsum(rng.normal(0, 0.6, n))
    return dict(o=c + rng.normal(0, 0.1, n), h=c + rng.uniform(0.2, 1.0, n), l=c - rng.uniform(0.2, 1.0, n), c=c)


def rows_from(b, model):
    return [dict(lb=0, **{f: float(model[f][k]) for f in B.FIELDS}) for k in range(len(b["c"]))]


class Info(unittest.TestCase):
    def test_ok_and_planted(self):
        rep = C.Report()
        B.check_info(rep, INFO, "EURJPY")
        self.assertEqual(rep.fails(), [])
        for k, v in (("StartDate", "20120101"), ("Spread", "0.0120000000"), ("TICKS", "0")):
            rep = C.Report()
            B.check_info(rep, dict(INFO, **{k: v}), "EURJPY")
            self.assertEqual(len(rep.fails()), 1, k)

    def test_lookback(self):
        rows = [dict(lb=1)] * 519 + [dict(lb=0)] * 5
        rep = C.Report()
        B.check_lookback(rep, rows)
        self.assertEqual(len(rep.fails()), 1)                 # 519 < 520
        rep = C.Report()
        B.check_lookback(rep, [dict(lb=1)] * 520 + [dict(lb=0)])
        self.assertEqual(rep.fails(), [])


class Wiring(unittest.TestCase):
    def test_ok_and_planted(self):
        b = bars()
        m = B.models(b)
        rep = C.Report()
        B.check_wiring(rep, rows_from(b, m), m)
        self.assertEqual(rep.fails(), [])
        rows = rows_from(b, m)
        rows[600]["fama"] += 1e-6                               # planted: one FAMA value off
        rep = C.Report()
        B.check_wiring(rep, rows, m)
        self.assertEqual([r["item"] for r in rep.fails()], ["fama"])
        rows = rows_from(b, m)
        k = next(i for i in range(560, 700) if abs(m["mama"][i] - m["fama"][i]) > 1e-3)
        rows[k]["mama"], rows[k]["fama"] = rows[k]["fama"], rows[k]["mama"]   # planted: MAF state flipped (and values swapped)
        rep = C.Report()
        B.check_wiring(rep, rows, m)
        self.assertIn("maf_states", [r["item"] for r in rep.fails()])


if __name__ == "__main__":
    unittest.main()
