"""P6 sizing probe checker (M-D8): one Zorro run of TPL_Sizing.c, 15 synthetic assets.

Usage: python tools/check_sizing.py <zorro_log.csv> <results.csv>    (exit 0 = PASS)
       python tools/check_sizing.py --predict                        (print the model's predictions)
Criteria: docs/preregistration/TPL_Sizing_Criteria.md (committed before the run).

Rule under test, per half (M-D8.1-8.3):
    Lots = floor( Equity x (RISK_PCT / 2) / 100 / ((STOP_ATR x ATR / PIP) x PIPCost) )
Refusals (M-D8.2, M-D8.5, runtime risk guard), in this order: below 1 lot; actual risk above the
configured risk; MarginTotal + 2 x Lots x MarginCost above Equity. MarginCost = close x PIPCost / PIP / 20.

Checks (ids as in the criteria doc):
  K0 setup     INFO rows: 15 assets, assetType 1, FixedLots 0, Capital 100000, RiskPct 2, Leverage 20,
               StopAtr 1.5, Fill 3, Hedge 2, TICKS 1; no ASSETFAIL row
  K1 formula   every SIZE row recomputed from its own logged inputs (pct, target, stop pips, risk per
               lot, raw, floor, actual, MarginCost from the ASSET row's close, margin)
  K2 refusals  ERROR rows exactly: A1_GLOT lots, A1_CMR risk, A1_GMRG margin; those assets no HALF row;
               every other asset the engine's number of halves; no ACCT row with MARGINCALL
  K3 model     Equity and Lots of every SIZE row equal the from-scratch model (expected trades, model lots,
               spread 0) under ONE timing alternative for the whole run:
                 TA: every asset's trades counted at this bar's close (state after the bar)
                 TB: assets later in the loop than the deciding one counted at the previous bar's close
               and every ACCT row (after the loop: all assets current) equals the model at this bar's close
  K4 halves    each HALF row's lots (TradeUnits / (PIPCost / PIP)) equal its signal's SIZE lots; both halves
               of a signal have equal lots
Observations (reported, not criteria): MarginTotal at each SIZE / ACCT row vs two margin models;
max MarginTotal / Equity; rounding error per signal.
"""
import csv
import datetime as dt
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_scenarios as M  # noqa: E402

E = M.E
START = dt.date(2024, 3, 6)
CAPITAL = 100000.0
RISK_PCT = 2.0          # nx_RiskPct (NNFX_Config.h)
NHALVES = 2
STOP_ATR = 1.5          # nx_StopAtr
LEVERAGE = 20.0
TOL_EQ = 0.05           # EUR; fills differ from the engine by <= 1e-5 (S4 C3; run 2: 1.4e-8)
TOL_REL = 1e-8          # K1: recomputation from logged values (Equity 6 decimals, ATR / PIP / PIPCost 15)
GUARDS = {"A1_GLOT": "lots", "A1_CMR": "risk", "A1_GMRG": "margin"}


def names():
    return list(M.SIZED)


def params(n):
    _, pair, (num, den), pip_den, off, mut = M.SIZED[n]
    return dict(pair=pair, pipcost=num / den, pip=1.0 / pip_den, offset=off, mut=mut)


def scenarios():
    """Per asset: days, closes, ATR per bar, engine halves (same build as the generator writes)."""
    M.MAX_LEN = max(M.scenario_len(x) for x in M.all_names())
    out = {}
    for n in names():
        s, days = M.build(n, START)
        kw = dict(s)
        kw.pop("order")
        p = kw.pop("params")
        res = E.run(p=p, **kw)
        out[n] = dict(days=days, c=list(s["c"]), atr=list(s["atr"]), halves=res.halves)
    return out


def size(eq, atr, pip, pipcost, mut=0):
    pct = RISK_PCT / NHALVES if mut != M.MUT_R2 else RISK_PCT
    target = eq * pct / 100.0
    stop_pips = STOP_ATR * atr / pip
    risk_lot = stop_pips * pipcost
    raw = target / risk_lot
    return dict(pct=pct, target=target, stop_pips=stop_pips, risk_lot=risk_lot, raw=raw,
                lots=math.floor(raw))


def model(timing):
    """Signals in time order, each with the model's Equity at its decision and its lots / refusal.

    Equity = CAPITAL + closed P&L + open P&L at the close (spread 0). A half counts as closed at bar tau
    if exit_bar <= tau, as open if entry_bar <= tau < exit_bar. Asset k's state time when asset j decides
    at bar t: t, except under TB for k later in the loop than j: t - 1.
    """
    sc = scenarios()
    order = names()
    pos = {n: i for i, n in enumerate(order)}
    nbar = len(sc[order[0]]["days"])
    # signals per asset: groups of halves with the same entry bar (decision bar = entry bar - 1)
    sig = []
    for n in order:
        by = {}
        for h in sc[n]["halves"]:
            by.setdefault(h.entry_bar, []).append(h)
        for eb, hs in sorted(by.items()):
            sig.append(dict(asset=n, dec_bar=eb - 1, halves=hs))
    sig.sort(key=lambda x: (x["dec_bar"], pos[x["asset"]]))
    taken = []   # (asset, half, lots) of signals that traded

    def equity(t, j, tb):
        eq = CAPITAL
        for n, h, lots in taken:
            tau = t - 1 if (tb and pos[n] > pos[j]) else t
            u = params(n)["pipcost"] / params(n)["pip"] * lots
            if h.exit_bar <= tau and h.reason != "end":
                eq += h.dir * (h.exit_price - h.entry) * u
            elif h.entry_bar <= tau:
                eq += h.dir * (sc[n]["c"][tau] - h.entry) * u
        return eq

    margin_open = []   # (asset, half, lots, margin per lot at entry decision)
    for x in sig:
        n, t = x["asset"], x["dec_bar"]
        pr = params(n)
        eq = equity(t, n, timing == "TB")
        z = size(eq, sc[n]["atr"][t], pr["pip"], pr["pipcost"], pr["mut"])
        cap = eq * RISK_PCT / NHALVES / 100.0
        mc = sc[n]["c"][t] * pr["pipcost"] / pr["pip"] / LEVERAGE
        mt = sum(lots * m for (k, h, lots, m) in margin_open if h.entry_bar <= t < h.exit_bar)
        margin = NHALVES * z["lots"] * mc
        refuse = None
        if z["lots"] < 1:
            refuse = "lots"
        elif z["lots"] * z["risk_lot"] > cap:
            refuse = "risk"
        elif mt + margin > eq:
            refuse = "margin"
        x.update(eq=eq, ymd=int(sc[n]["days"][t].strftime("%Y%m%d")), refuse=refuse, mc=mc, mt_model=mt, **z)
        if refuse is None:
            for h in x["halves"]:
                taken.append((n, h, z["lots"]))
                margin_open.append((n, h, z["lots"], mc))
    acct = {}
    for t in range(nbar):
        last = order[-1]
        acct[int(sc[last]["days"][t].strftime("%Y%m%d"))] = equity(t, last, False)
    return sig, acct


def read_log(path):
    L = dict(info={}, size=[], error=[], half=[], acct=[], asset={}, fail=[])
    with open(path, encoding="utf-8") as f:
        for r in csv.reader(f):
            if not r:
                continue
            k = r[0]
            if k == "INFO":
                L["info"][r[1]] = dict(x.split("=", 1) for x in r[3:] if "=" in x)
            elif k == "SIZE":
                v = [float(x) for x in r[3:]]
                L["size"].append(dict(asset=r[1], ymd=int(r[2]), eq=v[0], bal=v[1], mt=v[2], atr=v[3], pip=v[4],
                                      pipcost=v[5], lotamount=v[6], pct=v[7], target=v[8], stop_pips=v[9],
                                      risk_lot=v[10], raw=v[11], lots=int(v[12]), actual=v[13], mc=v[14],
                                      margin=v[15]))
            elif k == "ERROR":
                L["error"].append(dict(asset=r[1], ymd=r[2], kind=r[3] if len(r) > 3 else ""))
            elif k == "HALF":
                L["half"].append(dict(asset=r[1], group=int(r[2]), half=int(r[3]), dir=int(r[4]),
                                      entry_ymd=int(r[6]), units=float(r[18])))
            elif k == "ACCT":
                L["acct"].append(dict(bar=int(r[2]), ymd=int(r[3]), eq=float(r[4]), bal=float(r[5]),
                                      mt=float(r[6]), mcall=int(r[7])))
            elif k == "ASSET":
                L["asset"][(r[1], int(r[3]))] = dict(close=float(r[4]), pip=float(r[5]), pipcost=float(r[6]))
            elif k == "ASSETFAIL":
                L["fail"].append(r[1])
    return L


def rel(a, b):
    return abs(a - b) / max(1.0, abs(b))


def check(L):
    rows = []
    pair_of = {params(n)["pair"]: n for n in names()}

    def add(cid, asset, ok, expected, got, note=""):
        rows.append(dict(check=cid, asset=asset, result="PASS" if ok else "FAIL",
                         expected=expected, got=got, note=note))

    # K0
    add("K0", "-", not L["fail"], "no ASSETFAIL", len(L["fail"]))
    add("K0", "-", len(L["info"]) == len(names()), len(names()), len(L["info"]))
    want = {"type": "1", "FixedLots": "0", "Capital": "100000.00", "Fill": "3", "Hedge": "2", "TICKS": "1"}
    for a, d in L["info"].items():
        bad = [k for k, v in want.items() if d.get(k) != v]
        bad += [k for k, v in (("RiskPct", RISK_PCT), ("Leverage", LEVERAGE), ("StopAtr", STOP_ATR))
                if abs(float(d.get(k, "nan")) - v) > 1e-9]
        add("K0", a, not bad, "settings", ",".join(bad) or "ok")
    # K1
    for z in L["size"]:
        n = pair_of.get(z["asset"], z["asset"])
        r = size(z["eq"], z["atr"], z["pip"], z["pipcost"], 0)
        a = L["asset"].get((z["asset"], z["ymd"]))
        mc = a["close"] * z["pipcost"] / z["pip"] / LEVERAGE if a else float("nan")
        ok = (rel(z["pct"], r["pct"]) < TOL_REL and rel(z["target"], r["target"]) < TOL_REL
              and rel(z["stop_pips"], r["stop_pips"]) < TOL_REL and rel(z["risk_lot"], r["risk_lot"]) < TOL_REL
              and rel(z["raw"], r["raw"]) < TOL_REL and z["lots"] == r["lots"] == math.floor(z["raw"])
              and rel(z["actual"], z["lots"] * z["risk_lot"]) < TOL_REL
              and rel(z["mc"], mc) < TOL_REL and rel(z["margin"], NHALVES * z["lots"] * z["mc"]) < TOL_REL)
        if n in M.SIZED and params(n)["mut"]:   # planted bug: the correct rule must NOT hold here
            rows.append(dict(check="K1", asset=n, result="DETECTED" if not ok else "FAIL",
                             expected=f"lots {r['lots']} at pct {r['pct']}", got=f"lots {z['lots']} at pct {z['pct']}",
                             note=f"control (planted risk %), ymd {z['ymd']}"))
            continue
        add("K1", n, ok, f"lots {r['lots']} at pct {r['pct']}", f"lots {z['lots']} at pct {z['pct']}",
            f"ymd {z['ymd']}")
    # K2
    errs = {}
    for e in L["error"]:
        errs.setdefault(pair_of.get(e["asset"], e["asset"]), []).append(e["kind"])
    halves = {}
    for h in L["half"]:
        n = pair_of.get(h["asset"], h["asset"])
        halves[n] = halves.get(n, 0) + 1
    sc = scenarios()
    for n in names():
        if n in GUARDS:
            add("K2", n, errs.get(n) == [GUARDS[n]] and halves.get(n, 0) == 0,
                f"ERROR {GUARDS[n]}, 0 halves", f"ERROR {errs.get(n)}, {halves.get(n, 0)} halves")
        else:
            add("K2", n, n not in errs and halves.get(n, 0) == len(sc[n]["halves"]),
                f"no ERROR, {len(sc[n]['halves'])} halves", f"ERROR {errs.get(n)}, {halves.get(n, 0)} halves")
    mc_rows = [a for a in L["acct"] if a["mcall"]]
    add("K2", "-", not mc_rows, "no MARGINCALL", len(mc_rows))
    # K3: one timing alternative for the whole run
    verdict = {}
    for tm in ("TA", "TB"):
        sig, acct = model(tm)
        by = {(params(x["asset"])["pair"], x["ymd"]): x for x in sig}
        bad = []
        for z in L["size"]:
            x = by.get((z["asset"], z["ymd"]))
            if x is None or abs(z["eq"] - x["eq"]) > TOL_EQ or z["lots"] != x["lots"]:
                bad.append((z["asset"], z["ymd"]))
        missing = len(sig) - len(L["size"])
        verdict[tm] = (bad, missing, sig, acct)
    fits = [tm for tm in ("TA", "TB") if not verdict[tm][0] and verdict[tm][1] == 0]
    add("K3", "-", len(fits) >= 1, "SIZE rows match TA or TB",
        f"fits {fits or 'none'}; TA bad {len(verdict['TA'][0])}, TB bad {len(verdict['TB'][0])}",
        "both fit: timing not distinguishable on this run" if len(fits) == 2 else "")
    _, _, _, acct = verdict["TA"]
    badA = [a["ymd"] for a in L["acct"] if a["ymd"] in acct and abs(a["eq"] - acct[a["ymd"]]) > TOL_EQ]
    add("K3", "-", not badA and len(L["acct"]) > 0, "ACCT Equity = model at bar close",
        f"{len(badA)} of {len(L['acct'])} rows off", ",".join(map(str, badA[:5])))
    # K4
    lots_of = {(z["asset"], z["ymd"]): z["lots"] for z in L["size"]}
    sig_days = {}
    for n in names():
        for h in sc[n]["halves"]:
            sig_days[(params(n)["pair"], int(sc[n]["days"][h.entry_bar].strftime("%Y%m%d")))] = \
                int(sc[n]["days"][h.entry_bar - 1].strftime("%Y%m%d"))
    for h in L["half"]:
        n = pair_of.get(h["asset"], h["asset"])
        pr = params(n) if n in M.SIZED else None
        dec = sig_days.get((h["asset"], h["entry_ymd"]))
        lots = round(h["units"] / (pr["pipcost"] / pr["pip"])) if pr else -1
        add("K4", n, dec is not None and lots_of.get((h["asset"], dec)) == lots,
            lots_of.get((h["asset"], dec)), lots, f"half {h['half']} entry {h['entry_ymd']}")
    return rows, verdict


def main(argv):
    if argv and argv[0] == "--predict":
        for tm in ("TA", "TB"):
            sig, _ = model(tm)
            print(f"timing {tm}")
            for x in sig:
                print(f"  {x['asset']:8s} {params(x['asset'])['pair']} dec {x['ymd']} eq {x['eq']:.4f} raw {x['raw']:.6f} "
                      f"lots {x['lots']} actual {x['lots'] * x['risk_lot']:.4f} target {x['target']:.4f} "
                      f"refuse {x['refuse']} MC {x['mc']:.6f} margin {NHALVES * x['lots'] * x['mc']:.2f}")
        return 0
    if len(argv) != 2:
        print(__doc__)
        return 2
    rows, verdict = check(read_log(argv[0]))
    with open(argv[1], "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["check", "asset", "result", "expected", "got", "note"])
        w.writeheader()
        w.writerows(rows)
    fails = [r for r in rows if r["result"] == "FAIL"]
    for r in fails:
        print("FAIL", r)
    det = [r for r in rows if r["result"] == "DETECTED"]
    if not det:
        fails.append(dict(check="K1", asset="A1_CMR", result="FAIL", expected="DETECTED", got="no row", note=""))
        print("FAIL planted risk % not detected by K1 (no DETECTED row)")
    print(f"rows {len(rows)}, FAIL {len(fails)}, DETECTED {len(det)}; timing fits: "
          f"{[tm for tm in ('TA', 'TB') if not verdict[tm][0] and verdict[tm][1] == 0]}")
    print("RUN PASS" if not fails else "RUN FAIL")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
