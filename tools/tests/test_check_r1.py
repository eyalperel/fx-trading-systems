"""Tests for tools/check_r1.py: each check passes on consistent inputs and fails on a planted defect."""
import datetime as dt
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check_r1 as C  # noqa: E402
import r1_data as D  # noqa: E402

INFO = dict(PIP="0.0001000000", PIPCost="0.0856100000", LotAmount="1000", Spread="0.0001200000",
            RollLong="-0.894700", RollShort="0.425900")
UNITS = 856.1 * 77          # 77 lots at PIPCost / PIP = 856.1


def m1_days():
    """Records on Mon 2024-03-04 .. Wed 03-06, every 6 h from Sunday 18:00 New York, plus one exactly at 17:00."""
    recs = []
    p = 1.08
    t = dt.datetime(2024, 3, 3, 18, tzinfo=D.NY)
    while t < dt.datetime(2024, 3, 6, 17, tzinfo=D.NY):
        p += 0.0001
        recs.append((D.dt_to_ole(t.astimezone(D.UTC)), p + 0.0002, p - 0.0002, p, p + 0.0001))
        t += dt.timedelta(hours=1)
    a = np.zeros(len(recs), dtype=D.REC_DT)
    for i, (w, h, l, o, c) in enumerate(recs):
        a[i] = (w, h, l, o, c, 0, 0)
    return a


def rbar_from(b):
    out = []
    for k, d in enumerate(b["day"]):
        out.append(dict(bar=k, ymd=D.ymd_int(d), w=b["end_ole"][k], lb=0, o=b["o"][k], h=b["h"][k], l=b["l"][k], c=b["c"][k]))
    return out


class Bars(unittest.TestCase):
    def test_match_and_planted_ohlc(self):
        m1 = m1_days()
        b = D.daily_bars(m1)                       # Amendment 1 rule (same, own) + holidays
        rb = rbar_from(b)
        var, _ = C.match_bars(m1, rb)
        self.assertEqual(var, D.BAR_RULE)
        rb_other = rbar_from(D.daily_bars(m1, edge="next"))   # Zorro bars built by another rule: rejected
        var, _ = C.match_bars(m1, rb_other)
        self.assertIsNone(var)
        rb[1] = dict(rb[1], c=rb[1]["c"] + 1e-5)
        var, _ = C.match_bars(m1, rb)
        self.assertIsNone(var)
        rb = rbar_from(b)           # the first bar is exempt (partial first bar, gotchas 9d.14)
        rb[0] = dict(rb[0], o=rb[0]["o"] + 1e-4)
        var, _ = C.match_bars(m1, rb)
        self.assertIsNotNone(var)

    def test_bar_time_planted(self):
        b = D.daily_bars(m1_days())
        rb = rbar_from(b)
        rep = C.Report()
        C.check_bar_times(rep, rb)
        self.assertEqual(rep.fails(), [])
        rb[0] = dict(rb[0], w=rb[0]["w"] + 1.0 / 24)
        rep = C.Report()
        C.check_bar_times(rep, rb)
        self.assertEqual(len(rep.fails()), 1)


class Halves(unittest.TestCase):
    def exp(self):
        return [dict(dir=1, half=1, kind="c1", entry_ymd=20240305, entry=1.08, exit_ymd=20240306, exit=1.09, reason="tp1"),
                dict(dir=1, half=2, kind="c1", entry_ymd=20240305, entry=1.08, exit_ymd=20240307, exit=1.08, reason="end")]

    def got(self):
        return [dict(e, group=1) for e in self.exp()]

    def test_equal(self):
        self.assertEqual(C.compare_halves(self.exp(), self.got()), [])

    def test_planted_exit_price_day_reason(self):
        for k, v in (("exit", 1.0901), ("exit_ymd", 20240307), ("reason", "stop")):
            g = self.got()
            g[0][k] = v
            self.assertEqual(len(C.compare_halves(self.exp(), g)), 1, k)

    def test_end_half_compared_on_entry_only(self):
        g = self.got()
        g[1]["exit"] = 1.2
        self.assertEqual(C.compare_halves(self.exp(), g), [])
        g[1]["entry"] = 1.081
        self.assertEqual(len(C.compare_halves(self.exp(), g)), 1)


def size_row(eq=100000.0, atr=0.0080, close=1.08, lots=None):
    pip, pc = 0.0001, 0.08561
    sp = 1.5 * atr / pip
    rl = sp * pc
    raw = eq * 0.01 / rl
    lt = int(raw // 1) if lots is None else lots
    mc = close * pc / pip / 20
    return dict(ymd=20240305, eq=eq, bal=eq, mt=0.0, atr=atr, pip=pip, pipcost=pc, lotamount=1000, pct=1.0,
                target=eq * 0.01, stop_pips=sp, risk_lot=rl, raw=raw, lots=lt, actual=lt * rl, mc=mc, margin=2 * lt * mc)


class Money(unittest.TestCase):
    def L(self, **kw):
        L = dict(size=[size_row(**kw)], half=[], acct=[], error=[], fail=[])
        return L

    def test_sizing(self):
        rep = C.Report()
        C.check_sizing(rep, self.L(), {20240305: dict(atr=0.0080)}, {20240305: 1.08})
        self.assertEqual(rep.fails(), [])
        rep = C.Report()
        C.check_sizing(rep, self.L(lots=78), {20240305: dict(atr=0.0080)}, {20240305: 1.08})
        self.assertEqual(len(rep.fails()), 1)
        rep = C.Report()      # SIZE ATR not the IND ATR of that bar
        C.check_sizing(rep, self.L(), {20240305: dict(atr=0.0081)}, {20240305: 1.08})
        self.assertEqual(len(rep.fails()), 1)

    def halves(self):
        return [dict(group=1, half=1, dir=1, entry_ymd=20240304, entry=1.08, exit_ymd=20240305, exit=1.09,
                     profit=0.01 * UNITS, roll=0.0, comm=0.0, units=UNITS),
                dict(group=1, half=2, dir=1, entry_ymd=20240304, entry=1.08, exit_ymd=20240307, exit=1.10,
                     profit=0.02 * UNITS, roll=0.0, comm=0.0, units=UNITS)]

    def test_equity_and_planted(self):
        hv = self.halves()
        eq = C.CAPITAL + 0.01 * UNITS + (1.085 - 1.08) * UNITS
        L = dict(size=[dict(size_row(eq=eq), ymd=20240305)], half=hv,
                 acct=[dict(ymd=20240305, eq=eq, bal=C.CAPITAL + 0.01 * UNITS, mt=0.0, mcall=0)])
        rep = C.Report()
        C.check_equity(rep, L, {20240305: 1.085}, "a")
        self.assertEqual(rep.fails(), [])
        L["acct"][0]["eq"] += 1.0
        rep = C.Report()
        C.check_equity(rep, L, {20240305: 1.085}, "a")
        self.assertEqual(len(rep.fails()), 1)

    def test_profit_and_costs(self):
        L = dict(half=self.halves())
        rep = C.Report()
        C.check_profit(rep, L, INFO, "a")
        self.assertEqual(rep.fails(), [])
        L["half"][0]["profit"] += 1.0
        rep = C.Report()
        C.check_profit(rep, L, INFO, "a")
        self.assertEqual(len(rep.fails()), 1)
        hv = self.halves()        # R1b: spread x units, rollover 3 days of the long rate
        roll = 3 * -0.8947 * 77 * 1000 / 10000
        for h in hv:
            h["roll"] = roll
            h["profit"] = h["dir"] * (h["exit"] - h["entry"]) * h["units"] - 0.00012 * h["units"] + roll
        rep = C.Report()
        C.check_profit(rep, dict(half=hv), INFO, "b")
        self.assertEqual(rep.fails(), [])
        hv[1]["roll"] = roll * 1.5
        rep = C.Report()
        C.check_profit(rep, dict(half=hv), INFO, "b")
        self.assertEqual(len(rep.fails()), 2)          # identity and whole-day rollover

    def test_lots(self):
        L = dict(size=[size_row(atr=0.01)], half=self.halves())      # 1000 / (150 x 0.08561) = 77.87 -> 77 lots
        self.assertEqual(L["size"][0]["lots"], 77)
        rep = C.Report()
        C.check_lots(rep, L, INFO)
        self.assertEqual(rep.fails(), [])
        L["half"][1]["units"] = 856.1 * 76
        rep = C.Report()
        C.check_lots(rep, L, INFO)
        self.assertEqual(len(rep.fails()), 1)

    def test_margincall(self):
        rep = C.Report()
        C.check_margin(rep, dict(acct=[dict(eq=1.0, mt=0.1, mcall=1)]))
        self.assertEqual(len(rep.fails()), 1)


class Wiring(unittest.TestCase):
    def test_wiring_planted(self):
        n = 40
        rng = np.random.default_rng(3)
        c = 1.08 + np.cumsum(rng.normal(0, 0.002, n))
        bars = dict(o=c, h=c + 0.001, l=c - 0.001, c=c)
        import r1_replay as RP
        model = RP.indicators(bars)
        rows = []
        for k in range(n):
            r = {f: float(model[f][k]) for f in C.IND_FIELDS}
            r.update(open=c[k], high=c[k] + 0.001, low=c[k] - 0.001, close=c[k], bar=k, ymd=k, lookback=0)
            rows.append(r)
        rep = C.Report()
        C.check_wiring(rep, rows, model, bars)
        self.assertEqual(rep.fails(), [])
        rows[30]["fama"] += 1e-8
        rep = C.Report()
        C.check_wiring(rep, rows, model, bars)
        self.assertEqual([f["item"] for f in rep.fails()], ["fama"])


if __name__ == "__main__":
    unittest.main()



class Data(unittest.TestCase):
    def test_holiday_folds_into_next_bar(self):
        recs = []
        for day, hh in ((dt.date(2018, 1, 1), 10), (dt.date(2018, 1, 2), 10)):      # Monday 1 January is a holiday
            t = dt.datetime(day.year, day.month, day.day, hh, tzinfo=D.NY)
            recs.append((D.dt_to_ole(t.astimezone(D.UTC)), 1.2, 1.1, 1.15, 1.16))
        a = np.zeros(len(recs), dtype=D.REC_DT)
        for i, (w, h, l, o, c) in enumerate(recs):
            a[i] = (w, h, l, o, c, 0, 0)
        b = D.daily_bars(a)
        self.assertEqual([D.ymd_int(d) for d in b["day"]], [20180102])
        b = D.daily_bars(a, holidays=False)
        self.assertEqual([D.ymd_int(d) for d in b["day"]], [20180101, 20180102])
