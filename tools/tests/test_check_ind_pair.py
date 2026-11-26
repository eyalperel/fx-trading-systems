"""Tests for tools/check_ind_pair.py (C1S3 V-a): each check passes on consistent input and fails on a planted defect."""
import os
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check_ind_pair as P  # noqa: E402
import check_r1 as C  # noqa: E402
import r1_replay as R1  # noqa: E402

INFO = dict(type="1", LookBack="520", TICKS="1", TradeModeFRC="1", Fill="3", BarOffset="1020", StartWeek="71700",
            AtrLen="14", StartDate="20070401", EndDate="20260529", PIP="0.0001000000", PIPCost="0.0856100000",
            Spread="0.0000800000", RollLong="-0.096800", RollShort="0.045400", LookBack2="520", FisherLen="10",
            ReflexLen="20", FramaN="32", MesaLen="20", MesaHP="48", MesaSS="10", SmaLen="10", LrsiGamma="0.500000")


def bars(n=700, seed=7):
    rng = np.random.default_rng(seed)
    c = 0.75 + np.cumsum(rng.normal(0, 0.006, n))
    return dict(o=c + rng.normal(0, 0.001, n), h=c + rng.uniform(0.002, 0.01, n), l=c - rng.uniform(0.002, 0.01, n), c=c)


def rows_from(m):
    n = len(m["fish"])
    rows = []
    for k in range(n):
        r = dict(lb=0, nmesa=float(k + 1), **{f: float(m[f][k]) for f in P.FIELDS})
        if np.isnan(r["sma"]):
            r["sma"] = 0.0                      # Zorro's own SMA before 10 outputs: a partial value, ignored by the check
        r["zsma"] = r["sma"]
        rows.append(r)
    return rows


def items(rep):
    return sorted({r["item"] for r in rep.fails()})


class Info(unittest.TestCase):
    def test_ok_and_planted(self):
        rep = C.Report()
        P.check_info(rep, INFO, "AUDUSD")
        self.assertEqual(rep.fails(), [])
        for k, v in (("FisherLen", "11"), ("FramaN", "16"), ("LrsiGamma", "0.700000"), ("EndDate", "20260115"),
                     ("LookBack2", "500")):
            rep = C.Report()
            P.check_info(rep, dict(INFO, **{k: v}), "AUDUSD")
            self.assertEqual(len(rep.fails()), 1, k)


class Wiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = bars()
        cls.m = P.models(cls.b)

    def run_check(self, rows):
        rep = C.Report()
        P.check_wiring(rep, rows, self.m)
        return rep

    def test_consistent(self):
        self.assertEqual(self.run_check(rows_from(self.m)).fails(), [])

    def test_one_value_off(self):
        rows = rows_from(self.m)
        rows[650]["frama"] += 1e-6                         # planted: one FRAMA value off (no state depends on it)
        self.assertEqual(items(self.run_check(rows)), ["frama"])

    def test_wrong_length(self):
        i1 = R1.indicators(self.b, fisher_len=11)          # planted: Fisher(11) in place of Fisher(10)
        rows = rows_from(self.m)
        for k, r in enumerate(rows):
            r["fish"], r["trig"] = float(i1["fish"][k]), float(i1["trig"][k])
        got = items(self.run_check(rows))
        self.assertIn("fish", got)
        self.assertIn("trig", got)

    def test_state_flipped(self):
        rows = rows_from(self.m)
        k = next(i for i in range(560, 700) if abs(self.m["lrsi"][i] - 0.5) > 1e-2)
        rows[k]["lrsi"] = 1.0 - rows[k]["lrsi"]            # planted: LRSI mirrored about 0.5 on one bar
        self.assertEqual(items(self.run_check(rows)), ["lrsi", "state_LRS"])

    def test_x1_and_count(self):
        rows = rows_from(self.m)
        rows[600]["zsma"] += 1e-9                          # planted: Zorro SMA differs from own SMA
        self.assertEqual(items(self.run_check(rows)), ["X1_sma"])
        rows = rows_from(self.m)
        rows[300]["nmesa"] = 299.0                         # planted: MESA output counter off
        self.assertEqual(items(self.run_check(rows)), ["nmesa"])

    def test_sma_start_ignored_only_before_row_10(self):
        rows = rows_from(self.m)
        for k in range(P.SMA_FIRST):
            rows[k]["sma"] = rows[k]["zsma"] = 123.0       # partial values before 10 outputs: ignored
        self.assertEqual(self.run_check(rows).fails(), [])
        rows[P.SMA_FIRST]["sma"] += 1e-6                   # planted: first defined SMA off
        self.assertIn("sma", items(self.run_check(rows)))

    def test_row_count(self):
        self.assertEqual(items(self.run_check(rows_from(self.m)[:-1])), ["rows"])


class LogFormat(unittest.TestCase):
    def test_field_count_guard(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "log.csv")
            with open(p, "w") as f:
                f.write("RIND,AUD/USD," + ",".join(["1"] * 19) + "\n")   # 21 fields: one value missing
            with self.assertRaises(SystemExit):
                P.read_log(p)
            with open(p, "w") as f:
                f.write("RIND,AUD/USD," + ",".join(["1"] * 20) + "\n")   # 22 fields
            info, rows, fail = P.read_log(p)
            self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
