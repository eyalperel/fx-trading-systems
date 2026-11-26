"""C1S2 Zorro check (P4: V-b): bars and MAMA / FAMA / ATR of a new dev pair equal Python's, before any read.

Usage: python tools/check_bars_pair.py <AUDUSD|EURJPY> <BARS_log.csv> <history_dir> <results.csv>
Exit 0 = PASS. Criteria: docs/preregistration/C1S2_MAF_OtherPairs_Criteria.md ("Zorro checks before any read").
No trades exist in the run; nothing about performance is computed.
  VB0  INFO settings (pair-specific dates and asset-list costs) and >= 520 bars before the first trade bar
  VB1  RBAR (from RIND rows) equal the Python bars of the R1 rule on every day (first bar exempt if partial); 17:00 New York
  VW1  MAMA, FAMA, period, alpha, phase, ATR, TR equal the reference models (1e-10 + 1e-9 |m|); MAF states equal the model's
       (near-threshold bars, |MAMA - FAMA| < 1e-9, counted, not failed)
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "analysis", "harness"))
import r1_data as D  # noqa: E402
import check_r1 as C  # noqa: E402
import reference as R  # noqa: E402

TOL_ABS, TOL_REL = 1e-10, 1e-9
NEAR = 1e-9
FIELDS = ("mama", "fama", "period", "alpha", "phase", "atr", "tr")
PAIRS = {
    "AUDUSD": dict(asset="AUD/USD", years=range(2002, 2027), StartDate="20070401", EndDate="20260529", PIP=0.0001,
                   PIPCost=0.08561, Spread=0.00008, RollLong=-0.0968, RollShort=0.0454),
    "EURJPY": dict(asset="EUR/JPY", years=range(2010, 2027), StartDate="20120201", EndDate="20260115", PIP=0.01,
                   PIPCost=0.058102, Spread=0.023, RollLong=0.2828, RollShort=-0.6068),
}
WANT = {"type": "1", "LookBack": "520", "TICKS": "1", "TradeModeFRC": "1", "Fill": "3", "BarOffset": "1020",
        "StartWeek": "71700", "AtrLen": "14"}


def read_log(path):
    info, rows, fail = {}, [], []
    with open(path, encoding="utf-8") as f:
        for r in csv.reader(f):
            if not r:
                continue
            if r[0] == "INFO":
                info = dict(x.split("=", 1) for x in r[3:] if "=" in x)
            elif r[0] == "RIND":
                if len(r) != 17:
                    raise SystemExit(f"RIND row with {len(r)} fields, 17 expected (gotchas 9d.24)")
                v = [float(x) for x in r[6:]]
                rows.append(dict(bar=int(r[2]), ymd=int(r[3]), w=float(r[4]), lb=int(r[5]), o=v[0], h=v[1], l=v[2], c=v[3],
                                 mama=v[4], fama=v[5], period=v[6], alpha=v[7], phase=v[8], atr=v[9], tr=v[10]))
            elif r[0] == "ASSETFAIL":
                fail.append(",".join(r))
    return info, rows, fail


def check_info(rep, info, pair):
    p = PAIRS[pair]
    bad = [f"{k}={info.get(k)}" for k, v in WANT.items() if info.get(k) != v]
    for k in ("StartDate", "EndDate"):
        if info.get(k) != p[k]:
            bad.append(f"{k}={info.get(k)}")
    for k in ("PIP", "PIPCost", "Spread", "RollLong", "RollShort"):
        try:
            if abs(float(info.get(k, "nan")) - p[k]) > 1e-6 * max(1.0, abs(p[k])):
                bad.append(f"{k}={info.get(k)}")
        except ValueError:
            bad.append(f"{k}={info.get(k)}")
    for k, v in (("FastLimit", 0.5), ("SlowLimit", 0.05)):
        if abs(float(info.get(k, "nan")) - v) > 1e-6:
            bad.append(f"{k}={info.get(k)}")
    rep.add("VB0", "info", not bad, "settings and asset-list costs", ", ".join(bad) or "ok")


def check_lookback(rep, rows):
    ft = next((k for k, r in enumerate(rows) if r["lb"] == 0), None)
    rep.add("VB0", "lookback_bars", ft is not None and ft >= 520, ">= 520 bars before the first trade bar", ft)
    return ft


def models(bars):
    mid = (bars["h"] + bars["l"]) * 0.5
    mm = R.simulate_mama(R.mama_article((1, 2), (1, 20)), mid)
    at = R.simulate_atr(R.atr_mt4(14), bars["c"], bars["h"], bars["l"])
    return dict(mama=mm.mama, fama=mm.fama, period=mm.period, alpha=mm.alpha, phase=mm.phase, atr=at.atr, tr=at.tr)


def check_wiring(rep, rows, model):
    n = len(rows)
    if n != len(model["mama"]):
        rep.add("VW1", "rows", False, len(model["mama"]), n)
        return
    for f in FIELDS:
        z = np.array([r[f] for r in rows])
        m = np.asarray(model[f], float)
        err = np.abs(z - m)
        bad = int((err > TOL_ABS + TOL_REL * np.abs(m)).sum())
        rep.add("VW1", f, bad == 0, "|z - m| <= 1e-10 + 1e-9|m|", f"{bad} rows off; max err {err.max():.3e}")
    zs = np.sign(np.array([r["mama"] - r["fama"] for r in rows])).astype(int)
    ms = np.sign(np.asarray(model["mama"]) - np.asarray(model["fama"])).astype(int)
    d = zs != ms
    near = d & (np.abs(np.asarray(model["mama"]) - np.asarray(model["fama"])) < NEAR)
    rep.add("VW1", "maf_states", int((d & ~near).sum()) == 0, "MAF states = model", f"{int((d & ~near).sum())} differ",
            f"near-threshold {int(near.sum())} (counted)")


def run(pair, log_path, history, out_path):
    rep = C.Report()
    info, rows, fail = read_log(log_path)
    rep.add("VB0", "no_assetfail", not fail, "none", len(fail))
    check_info(rep, info, pair)
    check_lookback(rep, rows)
    m1 = D.load_m1(history, stem=pair, years=PAIRS[pair]["years"])
    var, allv = C.match_bars(m1, rows)
    rep.add("VB1", "bars", var is not None, "RBAR = Python bars, rule (same, own) + holidays",
            f"fits {var}; " + "; ".join(f"{k}: {v[0]}" for k, v in allv.items()))
    C.check_bar_times(rep, rows)
    if var is not None:
        bars = allv[var][1]
        r0 = rows[0]
        diff0 = max(abs(r0[k] - bars[k][0]) for k in ("o", "h", "l", "c"))
        if diff0 > C.TOL_BAR:
            for k in ("o", "h", "l", "c"):
                bars[k] = bars[k].copy()
                bars[k][0] = r0[k]
        rep.add("VB1", "first_bar", True, "Zorro first bar used only if partial",
                f"{r0['ymd']}, diff {diff0:.3e}, replaced {diff0 > C.TOL_BAR}", status="INFO")
        check_wiring(rep, rows, models(bars))
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["check", "item", "result", "expected", "got", "note"])
        w.writeheader()
        w.writerows(rep.rows)
    for r in rep.rows:
        print(r["check"], r["item"], r["result"], r["got"], r["note"])
    print("RUN PASS" if not rep.fails() else "RUN FAIL")
    return rep


def main(argv):
    if len(argv) != 4 or argv[0] not in PAIRS:
        print(__doc__)
        return 2
    return 0 if not run(*argv).fails() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
