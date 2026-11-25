"""Tests for tools/check_r2.py and tools/r2_replay.py (PERF2 P-2): each check passes on consistent inputs and fails on a
planted defect (incl. the two PERF2 names: SMA length 9, C1 read at the 0.5 midline)."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check_r2 as C2  # noqa: E402
import r2_replay as R2  # noqa: E402


def bars(n=900, seed=7):
    rng = np.random.default_rng(seed)
    c = 1.10 + np.cumsum(rng.normal(0, 0.006, n))
    h = c + rng.uniform(0.001, 0.008, n)
    l = c - rng.uniform(0.001, 0.008, n)
    o = c + rng.normal(0, 0.001, n)
    return dict(o=o, h=h, l=l, c=c)


def ind_rows(b, model, sma=None, zsma=None, nmesa=None):
    n = len(b["c"])
    own = model["sma"] if sma is None else sma
    own = np.where(np.isnan(own), 0.123, own)          # Zorro holds some value on rows 0..n-2 (not compared)
    zs = own if zsma is None else zsma
    cnt = np.arange(1, n + 1) if nmesa is None else nmesa
    rows = []
    for k in range(n):
        r = dict(open=b["o"][k], high=b["h"][k], low=b["l"][k], close=b["c"][k], zsma=zs[k], nmesa=int(cnt[k]),
                 bar=k, ymd=20200101 + k, lookback=0)
        for f in C2.IND_FIELDS:
            r[f] = float(own[k]) if f == "sma" else float(model[f][k])
        rows.append(r)
    return rows


def bar_rows(b, st, c1=None):
    c1 = st["c1"] if c1 is None else c1
    return [dict(ymd=20200101 + k, c=b["c"][k], c1=int(c1[k]), c2=int(st["c2"][k]), base=st["baseline"][k],
                 atr=st["atr"][k]) for k in range(len(b["c"]))]


class Model(unittest.TestCase):
    def test_sma_known_answer(self):
        s = R2.sma_last(np.arange(1, 21, dtype=float), 10)
        self.assertTrue(np.isnan(s[8]))
        self.assertEqual(s[9], 5.5)
        self.assertEqual(s[19], 15.5)

    def test_c1_zero_until_sma(self):
        st = R2.states(R2.indicators(bars()))
        self.assertTrue(np.all(st["c1"][:9] == 0))
        self.assertTrue(np.all(np.abs(st["c1"][9:]) <= 1))


class Wiring(unittest.TestCase):
    def setUp(self):
        self.b = bars()
        self.m = R2.indicators(self.b)

    def run_w1(self, rows):
        rep = C2.C.Report()
        C2.check_wiring(rep, rows, self.m, self.b)
        return rep.fails()

    def test_consistent(self):
        self.assertEqual(self.run_w1(ind_rows(self.b, self.m)), [])

    def test_planted_sma_length_9(self):
        f = self.run_w1(ind_rows(self.b, self.m, sma=R2.sma_last(self.m["mesa"], 9)))
        self.assertEqual([r["item"] for r in f], ["sma"])

    def test_planted_nmesa(self):
        n = len(self.b["c"])
        f = self.run_w1(ind_rows(self.b, self.m, nmesa=np.arange(0, n)))
        self.assertEqual([r["item"] for r in f], ["nmesa"])


class X1(unittest.TestCase):
    def setUp(self):
        self.b = bars()
        self.m = R2.indicators(self.b)

    def test_consistent_and_planted(self):
        rep = C2.C.Report()
        C2.check_x1(rep, ind_rows(self.b, self.m))
        self.assertEqual(rep.fails(), [])
        own = np.nan_to_num(self.m["sma"], nan=0.123)
        z = own.copy()
        z[400] += 1e-6
        rep = C2.C.Report()
        C2.check_x1(rep, ind_rows(self.b, self.m, zsma=z))
        self.assertEqual(len(rep.fails()), 1)


class States(unittest.TestCase):
    def test_consistent_and_planted_midline(self):
        b = bars()
        m = R2.indicators(b)
        st = R2.states(m)
        di = {20200101 + k: k for k in range(len(b["c"]))}
        rep = C2.C.Report()
        C2.check_states(rep, bar_rows(b, st), st, m, di)
        self.assertEqual(rep.fails(), [])
        mid = np.sign(m["mesa"] - 0.5).astype(int)     # planted: C1 read at the 0.5 midline (the pre-amendment reading)
        rep = C2.C.Report()
        C2.check_states(rep, bar_rows(b, st, c1=mid), st, m, di)
        self.assertEqual(len(rep.fails()), 1)


class Refusals(unittest.TestCase):
    def test_equal_and_planted(self):
        days = [20200101 + k for k in range(20)]
        eng = [(3, 1, "bridge-too-far"), (12, -1, "bridge-too-far")]
        z = [dict(ymd=20200104, reason="bridge-too-far", kind="standard"),
             dict(ymd=20200113, reason="bridge-too-far", kind="standard"),
             dict(ymd=20200115, reason="lots", kind="standard")]           # other reasons are not compared here
        self.assertEqual(C2.compare_refusals(eng, days, z), [])
        self.assertEqual(len(C2.compare_refusals(eng[:1], days, z)), 1)          # engine missed one
        self.assertEqual(len(C2.compare_refusals(eng, days, z[:1] + z[2:])), 1)  # template missed one


if __name__ == "__main__":
    unittest.main()
