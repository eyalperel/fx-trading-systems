"""Phase 1 step 5 worksheet: one R1a trade (or one refused signal), laid out for a check against the NNFX rules by hand.

Usage: python tools/step5_worksheet.py <group>            (a trade of TPL_R1a_log_run2.csv)
       python tools/step5_worksheet.py btf <yyyymmdd>     (a bridge-too-far refusal)
Inputs: C:/Zorro/Data/TPL_R1a_log_run2.csv and _ind_run2.csv, C:/Zorro/History/EURUSD_*.t6 (raw M1, R1 bar rule).
Prints daily bars around the trade with the slot values, the template's levels, SIZE row, HALF rows, and the M1 records at
which each intrabar exit happened. No performance figure (R-D1): profits are not printed.
Plan: docs/preregistration/STEP5_HandChecked_Trades.md.
"""
import collections
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_r1 as C  # noqa: E402
import r1_data as D  # noqa: E402

ZD = os.environ.get("ZORRO_DATA", "C:/Zorro/Data")
ZH = os.environ.get("ZORRO_HISTORY", "C:/Zorro/History")


def load():
    L = C.read_log(os.path.join(ZD, "TPL_R1a_log_run2.csv"))
    ind = {r["ymd"]: r for r in C.read_ind(os.path.join(ZD, "TPL_R1a_ind_run2.csv"))}
    m1 = D.load_m1(ZH)
    bars = D.daily_bars(m1)
    return L, ind, m1, bars


def sgn(x):
    return (x > 0) - (x < 0)


def bar_table(L, ind, d0, d1):
    days = [r["ymd"] for r in L["rbar"] if d0 <= r["ymd"] <= d1]
    rb = {r["ymd"]: r for r in L["rbar"]}
    print(f"{'day':>10} {'open':>8} {'high':>8} {'low':>8} {'close':>8} | {'FAMA':>8} {'side':>4} | {'Fish':>7} {'Fish[1]':>7} "
          f"{'C1':>3} | {'Reflex':>7} {'C2':>3} | {'ATR pips':>8}")
    for y in days:
        b, x = rb[y], ind[y]
        print(f"{y:>10} {b['o']:8.5f} {b['h']:8.5f} {b['l']:8.5f} {b['c']:8.5f} | {x['fama']:8.5f} {sgn(b['c'] - x['fama']):>4d} | "
              f"{x['fish']:7.3f} {x['trig']:7.3f} {sgn(x['fish'] - x['trig']):>3d} | {x['reflex']:7.3f} {sgn(x['reflex']):>3d} | "
              f"{x['atr'] * 10000:8.1f}")
    return days


def m1_cross(m1, bars, ymd, level, d, kind):
    """First M1 record of day ymd that reaches level (stop: adverse side, tp: favourable side)."""
    k = [D.ymd_int(x) for x in bars["day"]].index(ymd)
    for i in range(bars["i0"][k], bars["i1"][k] + 1):
        lo, hi = float(m1["l"][i]), float(m1["h"][i])
        adverse = (lo <= level) if d == 1 else (hi >= level)
        favour = (hi >= level) if d == 1 else (lo <= level)
        if (kind == "stop" and adverse) or (kind == "tp" and favour):
            t = D.ole_to_dt(m1["t"][i]).astimezone(D.NY)
            return f"{t:%a %Y-%m-%d %H:%M} NY  o {m1['o'][i]:.5f} h {hi:.5f} l {lo:.5f} c {m1['c'][i]:.5f}"
    return "not reached"


def trade(group):
    L, ind, m1, bars = load()
    hs = sorted([h for h in L["half"] if h["group"] == group], key=lambda h: h["half"])
    en = [e for e in L["enter"] if e["group"] == group][0]
    sz = L["size"][group - 1]
    days_all = [r["ymd"] for r in L["rbar"]]
    di = days_all.index(en["ymd"])
    last_exit = max(h["exit_ymd"] for h in hs)
    prev = sorted([h for h in L["half"] if h["group"] == group - 1], key=lambda h: h["half"])
    d = hs[0]["dir"]
    print(f"TRADE #{group}: {'LONG' if d == 1 else 'SHORT'}, entry kind '{hs[0]['kind']}', decided at the close of {en['ymd']}, "
          f"filled {hs[0]['entry_ymd']}")
    if prev:
        print(f"Previous trade #{group - 1}: {'long' if prev[0]['dir'] == 1 else 'short'} '{prev[0]['kind']}', entry "
              f"{prev[0]['entry_ymd']}, exits {[(h['half'], h['reason'], h['exit_ymd']) for h in prev]}")
    print("\nDaily bars (17:00 New York close); side = sign(close - FAMA); C1 = sign(Fish - Fish[1]); C2 = sign(Reflex)")
    bar_table(L, ind, days_all[max(0, di - 8)], days_all[min(len(days_all) - 1, days_all.index(last_exit) + 1)])
    a = en["atr"]
    e = hs[0]["entry"]
    stop = e - d * 1.5 * a
    tp = e + d * 1.0 * a
    print(f"\nAt the decision close {en['ymd']}: ATR {a:.8f} ({a * 10000:.2f} pips); |close - FAMA| = "
          f"{abs([r for r in L['rbar'] if r['ymd'] == en['ymd']][0]['c'] - ind[en['ymd']]['fama']) * 10000:.2f} pips")
    print(f"Fill (first M1 record's open of {hs[0]['entry_ymd']}): {e:.5f}")
    print(f"Stop = fill - dir x 1.5 x ATR = {stop:.5f};  TP1 = fill + dir x 1 x ATR = {tp:.5f}")
    print(f"\nSizing (SIZE row): Equity {sz['eq']:.2f}, 1% = {sz['target']:.2f}, stop {sz['stop_pips']:.4f} pips, "
          f"PIPCost {sz['pipcost']}, risk per lot {sz['risk_lot']:.6f}, raw {sz['raw']:.4f} -> lots {sz['lots']} per half")
    print("\nHalves (Zorro):")
    for h in hs:
        lots = round(h["units"] / (sz["pipcost"] / sz["pip"]))
        print(f"  half {h['half']}: entry {h['entry']:.5f} on {h['entry_ymd']}; exit {h['exit']:.5f} on {h['exit_ymd']} "
              f"reason {h['reason']}; lots {lots}")
        if h["reason"] in ("stop", "be", "trail"):
            lvl = h["exit"]
            print(f"     first M1 record reaching {lvl:.5f}: {m1_cross(m1, bars, h['exit_ymd'], lvl, d, 'stop')}")
        if h["reason"] == "tp1":
            print(f"     first M1 record reaching TP1 {tp:.5f}: {m1_cross(m1, bars, h['exit_ymd'], tp, d, 'tp')}")


def btf(ymd):
    L, ind, m1, bars = load()
    days_all = [r["ymd"] for r in L["rbar"]]
    di = days_all.index(ymd)
    print(f"REFUSED SIGNAL (bridge-too-far candidate) at the close of {ymd}")
    open_now = [h for h in L["half"] if h["entry_ymd"] <= ymd < h["exit_ymd"]]
    print(f"Trades open at that close: {len(open_now)}")
    print("\nDaily bars:")
    bar_table(L, ind, days_all[max(0, di - 14)], days_all[min(len(days_all) - 1, di + 2)])
    nxt = [h for h in L["half"] if h["entry_ymd"] > ymd][:1]
    print(f"\nNext trade entered: {nxt[0]['entry_ymd'] if nxt else 'none'} (group {nxt[0]['group'] if nxt else '-'})")


if __name__ == "__main__":
    if sys.argv[1] == "btf":
        btf(int(sys.argv[2]))
    else:
        trade(int(sys.argv[1]))
