"""Tests for tools/perf_report.py (PERF1 criteria P-1 items 1-13, P-3 verdict, P-4 near-miss).

Everything is synthetic: the test writes its own logs; no Zorro log is read. Expected values are hand-calculated (as
fractions in the comments). Each guard is seen to fire on a deliberately broken input (CLAUDE.md 4.4).

The trade list (EUR/USD, pip 0.0001, PIPCost 1.0 EUR per pip per lot, so units = lots x 10000; spread 1 pip = 0.0001):
  id decision   fill      dir kind         S  lots risk/half  half 1                         half 2
  G1 2010-03-01 2010-03-02 +1 c1           60 16   960   (target 1000)  tp1  1.1041 03-04  +638   be     1.1000 03-10  -19
  G2 2010-05-28 2010-06-01 -1 baseline     45 22   990   (target 1000)  stop 1.2045 06-01  -1012  stop   1.2045 06-01  -1012
  G3 2010-09-06 2010-09-07 +1 continuation 60 16   960                 tp1  1.3041 09-09  +640   trail  1.3300 2011-01-05 +4774
  G4 2011-01-31 2011-02-01 -1 c1           45 22   990                 tp1  1.3470 02-03  +643   c1_flip 1.3450 02-20 +1086
  G5 2011-05-09 2011-05-10 +1 pullback     60 16   960                 stop 1.3940 05-12  -977   stop   1.3940 05-12  -977
  G6 2011-08-01 2011-08-02 -1 continuation 45 22   990                 tp1  1.3970 08-04  +638   end    1.3900 09-01  +2184
Profit of a half = dir x (exit - entry) x units - spread x units + roll (the template's cost identity); rolls:
G1 -2, -3; G3 0, -10; G4 +5, +8; G5 -1, -1; G6 0, +6; G2 0.
Signal-R = (P&L h1 + P&L h2) / (2 x risk/half): G1 619/1920, G2 -2024/1980, G3 5414/1920, G4 1729/1980,
G5 -1954/1920, G6 2822/1980.
"""
import collections
import datetime as dt
import os
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import perf_report as PR  # noqa: E402

PIP = 0.0001
SPREAD = 0.0001
INFO_OK = "INFO,EUR/USD,0,costs=1,PIP=0.0001000000,PIPCost=1.0000000000,Spread=0.0001000000,SpreadMult=1.000000,Tp1Atr=1.000000,RefusedLog=1"


def half_spec(exit_ymd, exit_px, reason, profit, roll):
    return dict(exit_ymd=exit_ymd, exit=exit_px, reason=reason, profit=profit, roll=roll)


def sig_spec(group, decision, fill, d, kind, s_pips, lots, entry, h1, h2):
    return dict(group=group, decision=decision, fill=fill, dir=d, kind=kind, s=s_pips, lots=lots, entry=entry,
                atr=s_pips / 1.5 * PIP, h=(h1, h2))


HAND = [
    sig_spec(1, 20100301, 20100302, 1, "c1", 60, 16, 1.1000,
             half_spec(20100304, 1.1041, "tp1", 638.0, -2.0), half_spec(20100310, 1.1000, "be", -19.0, -3.0)),
    sig_spec(2, 20100528, 20100601, -1, "baseline", 45, 22, 1.2000,
             half_spec(20100601, 1.2045, "stop", -1012.0, 0.0), half_spec(20100601, 1.2045, "stop", -1012.0, 0.0)),
    sig_spec(3, 20100906, 20100907, 1, "continuation", 60, 16, 1.3000,
             half_spec(20100909, 1.3041, "tp1", 640.0, 0.0), half_spec(20110105, 1.3300, "trail", 4774.0, -10.0)),
    sig_spec(4, 20110131, 20110201, -1, "c1", 45, 22, 1.3500,
             half_spec(20110203, 1.3470, "tp1", 643.0, 5.0), half_spec(20110222, 1.3450, "c1_flip", 1086.0, 8.0)),
    sig_spec(5, 20110509, 20110510, 1, "pullback", 60, 16, 1.4000,
             half_spec(20110512, 1.3940, "stop", -977.0, -1.0), half_spec(20110512, 1.3940, "stop", -977.0, -1.0)),
    sig_spec(6, 20110801, 20110802, -1, "continuation", 45, 22, 1.4000,
             half_spec(20110804, 1.3970, "tp1", 638.0, 0.0), half_spec(20110901, 1.3900, "end", 2184.0, 6.0)),
]
# hand-chosen bars (high, low) where the test needs a particular situation; every other day gets a benign bar
SPECIAL_BARS = {
    20100304: (1.1045, 1.1010),     # G1 TP1 bar: TP 1.1040 reached, stop 1.0940 not
    20100601: (1.2050, 1.1960),     # G2 fill bar: stop 1.2045 AND TP 1.1970 both inside -> same-bar, resolved as stop
    20100909: (1.3045, 1.3010),
    20110203: (1.3490, 1.3465),
    20110512: (1.4010, 1.3935),
    20110804: (1.3990, 1.3965),
}


def weekdays(a, b):
    d0 = dt.date(a // 10000, a // 100 % 100, a % 100)
    d1 = dt.date(b // 10000, b // 100 % 100, b % 100)
    d = d0
    while d <= d1:
        if d.weekday() < 5:
            yield d.year * 10000 + d.month * 100 + d.day
        d += dt.timedelta(days=1)


def make_bars(specs, special=SPECIAL_BARS):
    bars = {}
    for s in specs:
        for h in s["h"]:
            for d in weekdays(s["fill"], h["exit_ymd"]):
                e = s["entry"]
                bars[d] = special.get(d, (e + 0.0020, e - 0.0020))
    bars.update({d: v for d, v in special.items() if d in bars})
    return bars


def write_log(path, specs, bars, refused=(), info=INFO_OK, stops=(), extra_rows=(), drop=(), tamper=None):
    """Write a synthetic template log. refused: (ymd, reason, kind). drop: row prefixes to leave out."""
    rows = ["kind,asset,a,b,c,d,e,f,g,h,i,j,k,l,m,n", info]
    for s in specs:
        lots, sp = s["lots"], s["s"]
        rows.append("SIZE,EUR/USD,%d,100000.000000,100000.000000,0.000000,%.15f,0.000100000000000,1.000000000000000,1000,"
                    "1.000000,1000.000000,%.12f,%.15f,%.10f,%d,%.6f,1.0000000000,1.000000"
                    % (s["decision"], s["atr"], sp, sp * 1.0, 1000.0 / sp, lots, lots * sp * 1.0))
        rows.append("ENTER,EUR/USD,%d,%d,%d,%s,%.15f" % (s["decision"], s["group"], s["dir"], s["kind"], s["atr"]))
    for ymd, reason, kind in refused:
        if reason in ("lots", "risk", "margin"):
            rows.append("SIZE,EUR/USD,%d,100000.0,100000.0,0.0,0.004,0.0001,1.0,1000,1.0,1000.0,60.0,60.0,0.5,0,0.0,1.0,1.0"
                        % ymd)
            rows.append("ERROR,EUR/USD,%d,%s,test refusal" % (ymd, reason))
        rows.append("REFUSED,EUR/USD,%d,%s,%s" % (ymd, reason, kind))
    halves = []
    for s in specs:
        units = s["lots"] * 10000.0
        for k, h in enumerate(s["h"], 1):
            profit = h["profit"] if tamper is None else tamper(s, k, h["profit"])
            halves.append((h["exit_ymd"], "HALF,EUR/USD,%d,%d,%d,%s,%d,%.15f,%d,%.15f,%s,0,0,0,%.8f,%.8f,0.00000000,%.10f,%.8f"
                           % (s["group"], k, s["dir"], s["kind"], s["fill"], s["entry"], h["exit_ymd"], h["exit"],
                              h["reason"], profit, h["roll"], SPREAD, units)))
    halves.sort(key=lambda x: x[0])                       # close order (stable)
    rows += [r for _, r in halves if not any(r.startswith(p) for p in drop)]
    rows += list(stops) + list(extra_rows)
    bar = 0
    for d in sorted(bars):
        rows.append("RBAR,EUR/USD,%d,%d,0.0,0,0.0,%.10f,%.10f,0.0" % (bar, d, bars[d][0], bars[d][1]))
        rows.append("ACCT,,%d,%d,100000.000000,100000.000000,5000.000000,0" % (bar, d))
        bar += 1
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(rows) + "\n")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def p(self, name):
        return os.path.join(self.tmp.name, name)

    def model(self, specs=HAND, basis="actual", **kw):
        path = self.p("log.csv")
        write_log(path, specs, make_bars(specs), **kw)
        L = PR.read_log(path)
        asset, sigs = PR.build_model(L, basis)
        return L, sigs

    def stats(self, kind="all", **kw):
        L, sigs = self.model(**kw)
        bars = PR.BarSet(L["rbar"]["EUR/USD"])
        return PR.compute_stats([s for s in sigs if PR.in_kind(kind, s.kind)],
                                [r for r in L["refused"] if PR.in_kind(kind, r["kind"])], bars, 1.0)


class Items(Base):
    """Items 1-13 on the hand list, for all / standard / continuation."""

    def test_item1_counts(self):
        for kind, ns in (("all", 6), ("standard", 4), ("continuation", 2)):
            S = self.stats(kind)
            self.assertEqual((S["n_signals"], S["n_halves"]), (ns, 2 * ns), kind)

    def test_item2_total_and_mean_signal_R(self):
        # all: 215471/63360 = 3.400741792929...; std (G1,G2,G4,G5): -10699/12672 = -0.844302398989...;
        # cont (G3,G6): 134483/31680 = 4.245044191919...
        for kind, tot, n in (("all", 3.400741792929293, 6), ("standard", -0.844302398989899, 4),
                             ("continuation", 4.245044191919192, 2)):
            S = self.stats(kind)
            self.assertAlmostEqual(S["total_R"], tot, places=9, msg=kind)
            self.assertAlmostEqual(S["mean_R"], tot / n, places=9, msg=kind)

    def test_signal_R_each(self):
        _, sigs = self.model()
        want = [619 / 1920, -2024 / 1980, 5414 / 1920, 1729 / 1980, -1954 / 1920, 2822 / 1980]
        for s, w in zip(sigs, want):
            self.assertAlmostEqual(s.R, w, places=12)

    def test_item3_mean_half_R(self):
        # all: TP1 half mean 0.0975431397306 (=sum of half-1 profit/risk /6), runner 1.0360374579125, all halves their mean
        S = self.stats("all")
        self.assertAlmostEqual(S["mean_half_R_tp1"], 0.09754313973063973, places=9)
        self.assertAlmostEqual(S["mean_half_R_runner"], 1.0360374579124578, places=9)
        self.assertAlmostEqual(S["mean_half_R"], 0.5667902988215489, places=9)
        S = self.stats("standard")
        self.assertAlmostEqual(S["mean_half_R_tp1"], -0.18146306818181818, places=9)
        self.assertAlmostEqual(S["mean_half_R_runner"], -0.24068813131313133, places=9)
        S = self.stats("continuation")
        self.assertAlmostEqual(S["mean_half_R_tp1"], 0.6555555555555556, places=9)
        self.assertAlmostEqual(S["mean_half_R_runner"], 3.5894886363636362, places=9)

    def test_half_R_uses_actual_risk(self):
        # G1 half 1: 638 / 960 (actual: 16 lots x 60 pips x 1.0); the target risk 1000 would give 0.638
        _, sigs = self.model()
        self.assertAlmostEqual(sigs[0].halves[0].R, 638 / 960, places=12)
        self.assertAlmostEqual(sigs[0].halves[0].risk, 960.0, places=9)

    def test_planted_defect_target_risk_changes_half_R(self):
        _, good = self.model()
        _, bad = self.model(basis="target")
        self.assertAlmostEqual(bad[0].halves[0].R, 0.638, places=12)            # 638 / 1000
        self.assertGreater(abs(bad[0].halves[0].R - good[0].halves[0].R), 0.02)
        self.assertGreater(abs(bad[0].R - good[0].R), 0.01)                      # 619/2000 vs 619/1920
        self.assertAlmostEqual(bad[0].R, 619 / 2000, places=12)

    def test_item4_win_rate(self):
        # wins: G1, G3, G4, G6
        for kind, w, n in (("all", 4, 6), ("standard", 2, 4), ("continuation", 2, 2)):
            S = self.stats(kind)
            self.assertEqual((S["wins"], S["n_signals"]), (w, n))
            self.assertAlmostEqual(S["win_rate"], w / n)

    def test_breakeven_exit_pays_spread_counts_as_loss(self):
        # G1 half 2: breakeven exit at the entry price = -spread x units = -16, plus roll -3 -> -19 EUR, -19/960 R
        _, sigs = self.model()
        self.assertAlmostEqual(sigs[0].halves[1].R, -19 / 960, places=12)
        self.assertEqual(sigs[0].halves[1].reason, "be")
        # a signal whose two halves sum to 0 is a loss even when half 1 won (R = 0 is not a win):
        # h1 tp1 = 656 - 16 = +640; h2 breakeven at the entry price: 0 - 16 + roll -624 = -640 -> signal-R = 0
        a = sig_spec(1, 20100301, 20100302, 1, "c1", 60, 16, 1.1000,
                     half_spec(20100304, 1.1041, "tp1", 640.0, 0.0), half_spec(20100305, 1.1000, "be", -640.0, -624.0))
        L, sigs = self.model([a])
        self.assertAlmostEqual(sigs[0].R, 0.0, places=12)
        S = PR.compute_stats(sigs, [], PR.BarSet(make_bars([a])), 1.0)
        self.assertEqual((S["wins"], S["n_signals"]), (0, 1))

    def test_item5_max_drawdown_known_answers(self):
        # all: peak after G1 half 1 = 638/1920 = 0.33229167; trough after both G2 halves = -0.69982639; DD = 1189/1152
        # second drawdown (G5, peak 2.99319760 -> 1.97548927) is 1.01770833, smaller
        self.assertAlmostEqual(self.stats("all")["max_dd"], 1189 / 1152, places=9)
        # standard: peak 0.33229167 (after G1h1); after G4 0.1734; after G5 -0.84430240 -> DD 74549/63360 = 1.17659407
        self.assertAlmostEqual(self.stats("standard")["max_dd"], 74549 / 63360, places=9)
        # continuation: every half wins -> DD 0
        self.assertEqual(self.stats("continuation")["max_dd"], 0.0)

    def test_drawdown_function(self):
        self.assertEqual(PR.max_drawdown([]), 0.0)
        self.assertAlmostEqual(PR.max_drawdown([-1.0, 0.5]), 1.0)                     # peak starts at 0
        self.assertAlmostEqual(PR.max_drawdown([1.0, -0.5, -0.25, 2.0, -1.0]), 1.0)   # peak 1 -> 0.25 (0.75), then 2.75 -> 1.75 (1.0)
        self.assertAlmostEqual(PR.max_drawdown([1.0, -2.0, 3.0, -1.5]), 2.0)          # peak 1 -> -1 (2.0); later 2 -> 0.5 is 1.5
        self.assertEqual(PR.max_drawdown([1.0, 1.0, 1.0]), 0.0)

    def test_item6_swap_in_R(self):
        # all: -17/1920 + 19/1980 = 0.00074179292929; % of total R = x / 3.40074179 x 100 = 0.0218127
        S = self.stats("all")
        self.assertAlmostEqual(S["swap_R"], 0.0007417929292929293, places=12)
        self.assertAlmostEqual(S["swap_pct"], 0.021812680128648402, places=9)
        S = self.stats("standard")      # G1 -5/1920, G4 13/1980, G5 -2/1920 -> -7/1920 + 13/1980 = 0.0029198232
        self.assertAlmostEqual(S["swap_R"], 0.0029198232323232325, places=12)
        self.assertAlmostEqual(S["swap_pct"], -0.34582671277689503, places=9)
        S = self.stats("continuation")  # G3 -10/1920 + G6 6/1980 = -0.0021780303
        self.assertAlmostEqual(S["swap_R"], -0.002178030303030303, places=12)

    def test_item7_spread_cost_in_R(self):
        # 1 pip x lots per half: G1,G3,G5 = 32/1920 each; G2,G4,G6 = 44/1980 each -> 0.05 + 0.0666667 = 0.1166667
        self.assertAlmostEqual(self.stats("all")["spread_R"], 0.11666666666666667, places=12)
        self.assertAlmostEqual(self.stats("standard")["spread_R"], 0.07777777777777778, places=12)   # 64/1920 + 88/1980 = 1/30 + 2/45
        self.assertAlmostEqual(self.stats("continuation")["spread_R"], 0.03888888888888889, places=12)

    def test_item8_same_bar_stop_and_tp1(self):
        # only G2: its fill bar 2010-06-01 spans stop 1.2045 (high 1.2050) and TP1 1.1970 (low 1.1960); half 1 exit = stop
        S = self.stats("all")
        self.assertEqual(S["same_bar"], dict(count=1, resolved={"stop": 1}))
        self.assertEqual(self.stats("standard")["same_bar"]["count"], 1)
        self.assertEqual(self.stats("continuation")["same_bar"]["count"], 0)

    def test_same_bar_exit_bar_rule(self):
        # half 1 leaves by a close-decided exit: its exit bar is not part of its life, so a bar there with both
        # levels inside does not count; with a level exit (stop) the same bar counts
        sp = sig_spec(1, 20100301, 20100302, 1, "c1", 60, 16, 1.1000,
                      half_spec(20100304, 1.1010, "c1_flip", 144.0, 0.0), half_spec(20100304, 1.1010, "c1_flip", 144.0, 0.0))
        bars = {20100302: (1.1020, 1.0980), 20100303: (1.1020, 1.0980), 20100304: (1.1045, 1.0935)}
        for reason, want in (("c1_flip", 0), ("stop", 1)):
            sp["h"][0]["reason"] = reason
            path = self.p("sb.csv")
            write_log(path, [sp], bars)
            L = PR.read_log(path)
            _, sigs = PR.build_model(L)
            self.assertEqual(PR.same_bar(sigs, PR.BarSet(L["rbar"]["EUR/USD"]), 1.0)["count"], want, reason)

    def test_item9_long_tp1_halves(self):
        # long half 1 with reason tp1: G1 (standard) and G3 (continuation); G5 is long but stops; shorts do not count
        self.assertEqual(self.stats("all")["long_tp1"], 2)
        self.assertEqual(self.stats("standard")["long_tp1"], 1)
        self.assertEqual(self.stats("continuation")["long_tp1"], 1)

    def test_item10_exit_reasons(self):
        S = self.stats("all")
        self.assertEqual(S["exits"], {"tp1": 4, "be": 1, "stop": 4, "trail": 1, "c1_flip": 1, "end": 1})
        self.assertEqual(self.stats("standard")["exits"], {"tp1": 2, "be": 1, "stop": 4, "c1_flip": 1})
        self.assertEqual(self.stats("continuation")["exits"], {"tp1": 2, "trail": 1, "end": 1})
        self.assertEqual(sum(S["exits"].values()), S["n_halves"])

    def test_item11_refused_signals(self):
        ref = [(20100401, "lots", "standard"), (20110301, "bridge-too-far", "standard"), (20110401, "margin", "continuation")]
        self.assertEqual(self.stats("all", refused=ref)["refused"], {"lots": 1, "bridge-too-far": 1, "margin": 1})
        self.assertEqual(self.stats("standard", refused=ref)["refused"], {"lots": 1, "bridge-too-far": 1})
        self.assertEqual(self.stats("continuation", refused=ref)["refused"], {"margin": 1})

    def test_item12_total_R_per_exit_year(self):
        # signal placed whole in the year of its last exit: G1, G2 -> 2010; G3 (runner exits 2011-01-05), G4, G5, G6 -> 2011
        S = self.stats("all")
        self.assertEqual(sorted(S["by_year"]), [2010, 2011])
        self.assertAlmostEqual(S["by_year"][2010], 619 / 1920 - 2024 / 1980, places=12)         # -0.69982639
        self.assertAlmostEqual(S["by_year"][2011], 4.100568181818182, places=9)
        self.assertAlmostEqual(sum(S["by_year"].values()), S["total_R"], places=12)
        self.assertEqual(sorted(self.stats("continuation")["by_year"]), [2011])

    def test_item13_longs_vs_shorts(self):
        # longs G1, G3, G5: 3, 2.12447917; shorts G2, G4, G6: 3, 1.27626263
        S = self.stats("all")
        self.assertEqual(S["longs"][0], 3)
        self.assertAlmostEqual(S["longs"][1], 2.1244791666666667, places=9)
        self.assertEqual(S["shorts"][0], 3)
        self.assertAlmostEqual(S["shorts"][1], 1.2762626262626262, places=9)
        self.assertAlmostEqual(self.stats("standard")["longs"][1], -0.6953125, places=9)

    def test_runner_stop_moves_parsed(self):
        stops = ["STOP,EUR/USD,20100908,3,1.3000000000,be", "STOP,EUR/USD,20101101,3,1.3200000000,trail"]
        _, sigs = self.model(stops=stops)
        self.assertEqual(sigs[2].halves[1].moves, [(20100908, 1.3), (20101101, 1.32)])
        self.assertEqual(sigs[2].halves[0].moves, [])


class Guards(Base):
    """Each log guard is seen to fire on a deliberately broken input."""

    def test_profit_identity(self):
        with self.assertRaisesRegex(PR.DataError, "cost identity"):
            self.model(tamper=lambda s, k, p: p + 50.0 if (s["group"], k) == (1, 1) else p)

    def test_missing_half(self):
        with self.assertRaisesRegex(PR.DataError, r"need exactly \[1, 2\]"):
            self.model(drop=("HALF,EUR/USD,3,2,",))

    def test_half_without_enter(self):
        extra = ["HALF,EUR/USD,9,1,1,c1,20100302,1.1,20100304,1.1041,tp1,0,0,0,638.0,-2.0,0.0,0.0001,160000.0"]
        with self.assertRaisesRegex(PR.DataError, "no ENTER"):
            self.model(extra_rows=extra)

    def test_size_row_without_enter_or_error(self):
        extra = ["SIZE,EUR/USD,20100101,100000.0,100000.0,0.0,0.004,0.0001,1.0,1000,1.0,1000.0,60.0,60.0,0.5,0,0.0,1.0,1.0"]
        with self.assertRaisesRegex(PR.DataError, "neither an ENTER row nor an ERROR"):
            self.model(extra_rows=extra)

    def test_units_do_not_match_lots(self):
        # the writer derives units from lots, so break the units of the first HALF row (16 lots -> 15 lots of units)
        path = self.p("u.csv")
        write_log(path, HAND, make_bars(HAND))
        txt = open(path, encoding="utf-8").read().replace("160000.00000000", "150000.00000000", 1)
        open(path, "w", encoding="utf-8").write(txt)
        with self.assertRaises(PR.DataError):
            PR.build_model(PR.read_log(path))

    def test_refused_rows_must_match_error_rows(self):
        path = self.p("r.csv")
        write_log(path, HAND, make_bars(HAND), refused=[(20100401, "lots", "standard")])
        txt = open(path, encoding="utf-8").read().replace("ERROR,EUR/USD,20100401,lots,test refusal\n", "")
        open(path, "w", encoding="utf-8").write(txt)
        with self.assertRaisesRegex(PR.DataError, "differ from ERROR rows"):
            PR.check_refused(PR.read_log(path))

    def test_bar_missing_for_a_half(self):
        L, sigs = self.model()
        bars = PR.BarSet({d: v for d, v in L["rbar"]["EUR/USD"].items() if d != 20100601})
        with self.assertRaisesRegex(PR.DataError, "no bar for entry"):
            PR.same_bar(sigs, bars, 1.0)

    def test_two_assets_refused(self):
        extra = ["ENTER,GBP/USD,20100301,1,1,c1,0.004"]
        with self.assertRaisesRegex(PR.DataError, "exactly one asset"):
            self.model(extra_rows=extra)

    def test_missing_fields_named(self):
        for token, needle in (("Tp1Atr=1.000000", "Tp1Atr"), (",RefusedLog=1", "RefusedLog"), ("PIP=0.0001000000,", "PIP")):
            path = self.p("m.csv")
            write_log(path, HAND, make_bars(HAND), info=INFO_OK.replace(token, "", 1))
            miss = PR.missing_fields(PR.read_log(path))
            self.assertTrue(any(needle in m for m in miss), (token, miss))
        path = self.p("m.csv")
        write_log(path, HAND, make_bars(HAND))
        self.assertEqual(PR.missing_fields(PR.read_log(path)), [])          # all present: nothing missing


class TemplateFormat(Base):
    """The INFO row exactly as TPL_R1_EURUSD.c prints it (R1d / R1c) and as R1b printed it (before PERF1 A1.1)."""
    R1B = ("INFO,EUR/USD,0,costs=1,type=1,list=29,FixedLots=0,Capital=100000.00,RiskPct=2.000000,Leverage=20.000000,"
           "LookBack=520,TradeModeFRC=1,Fill=3,Hedge=2,TICKS=1,BarOffset=1020,StartWeek=71700,PIP=0.0001000000,"
           "PIPCost=0.0856100023,LotAmount=1000,Spread=0.0001200000,RollLong=-0.894700,RollShort=0.425900,"
           "Commission=0.000000,FastLimit=0.500000,SlowLimit=0.050000,FisherLen=10,ReflexLen=20,AtrLen=14")
    R1D = R1B + ",SpreadMult=1.000000,Tp1Atr=1.000000,RefusedLog=1"

    def log(self, info):
        path = self.p("t.csv")
        write_log(path, HAND, make_bars(HAND), info=info)
        return PR.read_log(path)

    def test_new_info_row_has_nothing_missing(self):
        L = self.log(self.R1D)
        self.assertEqual(L["info"]["Tp1Atr"], "1.000000")
        self.assertEqual(PR.missing_fields(L), [])

    def test_old_info_row_still_stops_with_exit_3(self):
        miss = PR.missing_fields(self.log(self.R1B))
        self.assertEqual(len(miss), 2)
        self.assertTrue("Tp1Atr" in miss[0] and "RefusedLog" in miss[1])
        l1, l2 = self.p("a.csv"), self.p("b.csv")
        for q in (l1, l2):
            write_log(q, HAND, make_bars(HAND), info=self.R1B)
        hist = self.p("h")
        os.makedirs(hist)
        args = ["--x1", l1, "--x2", l2, "--sha-x1", PR.sha256_file(l1)[:16], "--sha-x2", PR.sha256_file(l2)[:16],
                "--history", hist, "--out", self.p("o.md")]
        self.assertEqual(PR.main(args), 3)
        self.assertFalse(os.path.exists(self.p("o.md")))

    def test_refused_rows_in_template_format(self):
        ref = [(20100401, "bridge-too-far", "standard"), (20100402, "lots", "continuation"), (20100403, "risk", "standard"),
               (20100404, "margin", "standard")]
        path = self.p("r.csv")
        write_log(path, HAND, make_bars(HAND), info=self.R1D, refused=ref)
        L = PR.read_log(path)
        PR.check_refused(L)                       # REFUSED rows agree with the ERROR rows
        self.assertEqual(sorted(r["reason"] for r in L["refused"]), ["bridge-too-far", "lots", "margin", "risk"])
        PR.build_model(L)
        L["refused"].append(dict(asset="EUR/USD", ymd=20100405, reason="btf", kind="standard"))
        with self.assertRaisesRegex(PR.DataError, "unknown reason"):
            PR.check_refused(L)


class Verdict(unittest.TestCase):
    """P-3: four synthetic lists, one per verdict path, each with its hand-calculated t."""

    @staticmethod
    def spread_years(per_year, years):
        return [(r, y) for y in years for r in per_year]

    def test_continue_evidence(self):
        # 4 years x (6 x +1.0, 4 x -0.5): n 40, mean 0.4, SS = 24 x 0.36 + 16 x 0.81 = 21.6, sd = sqrt(21.6/39) = 0.7442084,
        # t = 0.4 / (0.7442084 / sqrt(40)) = 3.39935. Best year = first (tie, all 4.0); removing it leaves 12 > 0.
        v = PR.verdict(self.spread_years([1.0] * 6 + [-0.5] * 4, (2010, 2011, 2012, 2013)))
        self.assertEqual(v["verdict"], PR.VERDICT_EVIDENCE)
        self.assertAlmostEqual(v["t"], 3.3993463423951904, places=9)
        self.assertEqual((v["n"], v["best_year"]), (40, 2010))
        self.assertAlmostEqual(v["total"], 16.0)
        self.assertAlmostEqual(v["total_excl"], 12.0)

    def test_continue_no_evidence(self):
        # 4 years x (4 x +1, 3 x -1): n 28, total 4, mean 1/7, sd = 1.0079053, t = 0.75; removing one year (+1) leaves 3 > 0
        v = PR.verdict(self.spread_years([1, 1, 1, 1, -1, -1, -1], (2010, 2011, 2012, 2013)))
        self.assertEqual(v["verdict"], PR.VERDICT_NO_EVIDENCE)
        self.assertAlmostEqual(v["t"], 0.75, places=9)
        self.assertAlmostEqual(v["total_excl"], 3.0)

    def test_stop_on_mean(self):
        # mean exactly 0 (the boundary: <= 0 stops): [+1, -1] in each of 2 years
        v = PR.verdict(self.spread_years([1.0, -1.0], (2010, 2011)))
        self.assertEqual(v["verdict"], PR.VERDICT_STOP)
        self.assertEqual(v["mean"], 0.0)
        # clearly negative mean: [+1, -3] in each of 2 years
        v = PR.verdict(self.spread_years([1.0, -3.0], (2010, 2011)))
        self.assertEqual(v["verdict"], PR.VERDICT_STOP)
        self.assertAlmostEqual(v["mean"], -1.0)

    def test_stop_on_best_year_removal_even_with_t_above_2(self):
        # 2010: 10 x +3.0 (30), 2011: 10 x -1.0 (-10): total 20, mean 1.0, sd 2.0519567, t = 2.17945 >= 2,
        # but removing 2010 leaves -10 <= 0 -> STOP
        v = PR.verdict([(3.0, 2010)] * 10 + [(-1.0, 2011)] * 10)
        self.assertGreaterEqual(v["t"], 2.0)
        self.assertAlmostEqual(v["t"], 2.1794494717703374, places=9)
        self.assertEqual(v["best_year"], 2010)
        self.assertAlmostEqual(v["total_excl"], -10.0)
        self.assertEqual(v["verdict"], PR.VERDICT_STOP)
        # same list without the loss year: removal leaves nothing -> total_excl 0 <= 0 -> STOP (a single year has no support)
        v = PR.verdict([(3.0, 2010)] * 10)
        self.assertEqual(v["verdict"], PR.VERDICT_STOP)

    def test_wording_exact(self):
        self.assertEqual(PR.VERDICT_EVIDENCE, "CONTINUE — evidence")
        self.assertEqual(PR.VERDICT_NO_EVIDENCE, "CONTINUE — no evidence yet")
        self.assertEqual(PR.VERDICT_STOP, "STOP")

    def test_best_year_is_the_highest_total(self):
        v = PR.verdict([(1.0, 2010), (5.0, 2011), (2.0, 2012), (-1.0, 2012)])
        self.assertEqual((v["best_year"], v["best_year_R"]), (2011, 5.0))

    def test_too_few_signals(self):
        with self.assertRaises(PR.DataError):
            PR.verdict([(1.0, 2010)])

    def test_hand_list_verdict(self):
        # the hand list: mean 0.5668 > 0, but 2011 carries +4.1006; without it total = -0.6998 -> STOP
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "l.csv")
        write_log(path, HAND, make_bars(HAND))
        _, sigs = PR.build_model(PR.read_log(path))
        v = PR.verdict([(s.R, s.year) for s in sigs])
        self.assertEqual((v["best_year"], v["verdict"]), (2011, PR.VERDICT_STOP))
        self.assertAlmostEqual(v["total_excl"], 619 / 1920 - 2024 / 1980, places=12)


class Sha(Base):
    def test_prefix_match_and_mismatch(self):
        path = self.p("f.bin")
        with open(path, "wb") as f:
            f.write(b"abc")
        full = PR.sha256_file(path)
        self.assertEqual(full, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")   # known sha256("abc")
        self.assertEqual(PR.verify_sha(path, full[:16], "x"), full)
        with self.assertRaises(PR.ShaMismatch):
            PR.verify_sha(path, "ba7816bf8f01ceff", "x")          # one nibble off
        with self.assertRaises(PR.ShaMismatch):
            PR.verify_sha(path, "ba78", "x")                      # a short prefix would match too much
        with self.assertRaises(PR.ShaMismatch):
            PR.verify_sha(path, "", "x")

    def run_main(self, sha1, sha2, out="out.md", log2=None, info=INFO_OK, read=None):
        l1, l2 = self.p("x1.csv"), self.p("x2.csv")
        write_log(l1, HAND, make_bars(HAND), info=info)
        write_log(l2, HAND, make_bars(HAND), info=info)
        hist = self.p("hist")
        os.makedirs(hist, exist_ok=True)
        for y in (2010, 2011):
            with open(os.path.join(hist, f"EURUSD_{y}.t6"), "wb") as f:
                f.write(b"history %d" % y)
        s1 = PR.sha256_file(l1)[:16] if sha1 is None else sha1
        s2 = PR.sha256_file(l2)[:16] if sha2 is None else sha2
        args = ["--x1", l1, "--x2", l2, "--sha-x1", s1, "--sha-x2", s2, "--history", hist, "--out", self.p(out)]
        if read is not None:
            args += ["--read", read]
        old = PR.load_history_bars
        PR.load_history_bars = lambda history, asset, y0, y1: PR.BarSet(make_bars(HAND))
        self.addCleanup(setattr, PR, "load_history_bars", old)
        return PR.main(args)

    def test_main_refuses_on_sha_mismatch_and_writes_nothing(self):
        self.assertEqual(self.run_main("0123456789abcdef", None), 2)
        self.assertFalse(os.path.exists(self.p("out.md")))
        self.assertEqual(self.run_main(None, "0123456789abcdef"), 2)
        self.assertFalse(os.path.exists(self.p("out.md")))

    def test_main_ok_with_matching_prefixes_and_never_overwrites(self):
        self.assertEqual(self.run_main(None, None), 0)
        text = open(self.p("out.md"), encoding="utf-8").read()
        self.assertIn("PERF1 read 1", text)
        self.assertIn("**STOP**", text)                           # hand list: best year removal leaves -0.6998
        self.assertIn("Variants counted: **1**", text)
        self.assertIn("EURUSD_2010.t6", text)
        self.assertIn(PR.sha256_file(self.p("x1.csv")), text)
        self.assertEqual(self.run_main(None, None), 2)            # the output exists: refused

    def test_perf2_synthetic_strategy2_log(self):
        # PERF2 P-5.2: perf_report.py on a synthetic log carrying Strategy 2's INFO row exits 0 before any R2 click;
        # header, criteria path, variant count and disclosure are PERF2's, the PERF1 lines are absent.
        info = ("INFO,EUR/USD,0,costs=1,PIP=0.0001000000,PIPCost=1.0000000000,Spread=0.0001000000,FramaN=32,MesaLen=20,"
                "MesaHP=48,MesaSS=10,C1SmaLen=10,LrsiGamma=0.500000,AtrLen=14,BtfOn=1,SpreadMult=1.000000,Tp1Atr=1.000000,"
                "RefusedLog=1")
        self.assertEqual(self.run_main(None, None, info=info, read="perf2"), 0)
        text = open(self.p("out.md"), encoding="utf-8").read()
        self.assertIn("PERF2 read 1 — Strategy 2 v0", text)
        self.assertIn("PERF2_Strategy2_EURUSD_Criteria.md", text)
        self.assertIn("project-wide strategy variants tested: **2**", text)
        self.assertIn("no Strategy 2 trade outcome was hand-checked", text)
        self.assertNotIn("PERF1", text)
        self.assertNotIn("Phase 1 step 5", text)
        for n in range(1, 14):
            self.assertIn(f"| {n} ", text, f"item {n}")

    def test_main_stops_on_missing_field(self):
        info = INFO_OK.replace("Tp1Atr=1.000000,", "")
        self.assertEqual(self.run_main(None, None, info=info), 3)
        self.assertFalse(os.path.exists(self.p("out.md")))

    def test_report_has_all_columns_and_items(self):
        self.assertEqual(self.run_main(None, None), 0)
        text = open(self.p("out.md"), encoding="utf-8").read()
        for col in ("all x1", "all x2", "standard x1", "standard x2", "continuation x1", "continuation x2"):
            self.assertIn(col, text)
        for n in range(1, 14):
            self.assertIn(f"| {n} ", text, f"item {n}")
        self.assertIn("exit year 2007", text)
        self.assertIn("exit year 2026", text)
        self.assertIn("near-miss", text)


class NearMiss(unittest.TestCase):
    """P-4.2 on a hand-made bar set with known margins (pips)."""

    @staticmethod
    def half(entry_ymd, exit_ymd, reason, d, num, entry, moves=(), s_pips=60.0, atr=0.0040):
        sig = types.SimpleNamespace(size=dict(stop_pips=s_pips, pip=PIP), atr=atr, group=1)
        return types.SimpleNamespace(entry_ymd=entry_ymd, exit_ymd=exit_ymd, reason=reason, dir=d, half=num, entry=entry,
                                     moves=list(moves), sig=sig)

    def setUp(self):
        # A long half 1 (stop 1.0940, TP 1.1040): stop margins 10, 56, 60; TP margins 10, 2, -1 (crossed by 1 pip)
        # B short half 1 (stop 1.2060, TP 1.1960): stop margins 1, -2 (crossed by 2 pips); TP margins 30, 35
        # C long runner (stop 1.2940, moved to 1.3010 at the close of 07-01): stop margins 50 (initial), 1 (moved), -2
        # D long half 1 closed by c1_flip: its exit bar (08-02) is outside its life, the 0.5 pip margin there is ignored
        self.bars = PR.BarSet({
            20100302: (1.1030, 1.0950), 20100303: (1.1038, 1.0996), 20100304: (1.1041, 1.1000),
            20100601: (1.2059, 1.1990), 20100602: (1.2062, 1.1995),
            20100701: (1.3050, 1.2990), 20100702: (1.3050, 1.3011), 20100703: (1.3050, 1.3008),
            20100801: (1.4020, 1.3990), 20100802: (1.4020, 1.39405)})
        self.sigs = [types.SimpleNamespace(halves=[h]) for h in (
            self.half(20100302, 20100304, "tp1", 1, 1, 1.1000),
            self.half(20100601, 20100602, "stop", -1, 1, 1.2000),
            self.half(20100701, 20100703, "be", 1, 2, 1.3000, moves=[(20100701, 1.3010)]),
            self.half(20100801, 20100802, "c1_flip", 1, 1, 1.4000))]

    def test_margins_of_each_half(self):
        want = {0: ([10, 56, 60], [10, 2, -1]), 1: ([1, -2], [30, 35]), 2: ([50, 1, -2], []), 3: ([50], [20])}
        for i, sg in enumerate(self.sigs):
            st, tl = PR.margins(sg.halves[0], self.bars, PIP, 1.0)
            for got, w in ((st, want[i][0]), (tl, want[i][1])):
                self.assertEqual(len(got), len(w), i)
                for g, x in zip(got, w):
                    self.assertAlmostEqual(g, x, places=6, msg=str(i))

    def test_flip_counts(self):
        r = PR.near_miss(self.sigs, self.bars, PIP, 1.0)
        self.assertEqual(r["halves"], 4)
        # shift 0.5: nothing within 0.5 pip (D's 0.5 pip is in the excluded exit bar); shift 1: B stop (1), C stop moved (1);
        # A's TP overshoot is exactly 1 pip (a tie is no flip); shift 2: B, C and A's TP (margin 2)
        self.assertEqual(r["flips"][0.5], dict(stop=0, tp1=0, either=0))
        self.assertEqual(r["flips"][1.0], dict(stop=2, tp1=0, either=2))
        self.assertEqual(r["flips"][2.0], dict(stop=2, tp1=1, either=3))

    def test_closest_approach_and_overshoot(self):
        r = PR.near_miss(self.sigs, self.bars, PIP, 1.0)
        self.assertAlmostEqual(r["stop_min_gap"], 1.0, places=6)
        self.assertAlmostEqual(r["tp1_min_gap"], 2.0, places=6)
        self.assertEqual((r["stop_crossed"], r["tp1_crossed"]), (2, 1))
        self.assertAlmostEqual(r["stop_min_over"], 2.0, places=6)
        self.assertAlmostEqual(r["tp1_min_over"], 1.0, places=6)

    def test_moved_stop_is_used(self):
        # planted defect: runner stop moves ignored -> C's stop margin on 07-02 becomes 71 pips and its flip at 1 pip vanishes
        self.sigs[2].halves[0].moves = []
        r = PR.near_miss(self.sigs, self.bars, PIP, 1.0)
        self.assertEqual(r["flips"][1.0]["stop"], 1)                # B only: differs from the 2 above

    def test_exit_bar_of_close_decided_exit_excluded(self):
        # planted defect: treat D's exit as a level exit -> its exit bar enters the life, the 0.5 pip margin flips at 0.5
        self.sigs[3].halves[0].reason = "stop"
        r = PR.near_miss(self.sigs, self.bars, PIP, 1.0)
        self.assertEqual(r["flips"][0.5]["stop"], 1)

    def test_no_bar_for_a_half_stops(self):
        with self.assertRaises(PR.DataError):
            PR.near_miss(self.sigs, PR.BarSet({20100302: (1.1, 1.09)}), PIP, 1.0)


if __name__ == "__main__":
    unittest.main()
