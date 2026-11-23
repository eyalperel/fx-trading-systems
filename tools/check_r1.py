"""R1 checker (decisions R-D1..R-D7): first EUR/USD real-data run of the NNFX template, Strategy 1 variant 0.

Usage: python tools/check_r1.py a <template_log.csv> <ind.csv> <history_dir> <results.csv>    (R1a, no costs)
       python tools/check_r1.py b <template_log.csv> <ind.csv> <history_dir> <results.csv>    (R1b, asset-list costs)
Exit 0 = PASS. Criteria: docs/preregistration/TPL_R1_Criteria.md (committed before each run).
MECHANICS ONLY (R-D1): no P&L, win rate or R summary is computed or printed.

Rows read: INFO (settings), RBAR (script: Bar, ymd, wdate, lookback, o, h, l, c), BAR (template's own, in nx_bar:
Bar, t, ymd, ok, o, h, l, c, c1, c2, base, atr, vol, ex), SIZE / ERROR / HALF / ACCT / ENTER (template), IND (strategy).

Checks (ids as in the criteria doc):
  K0  setup         INFO values; no ERROR, ASSETFAIL row
  B1  bars          Zorro's RBAR rows equal ONE Python bar variant (r1_data.BAR_VARIANTS) on every day of Zorro's range;
                    each bar ends 17:00 New York (wdate within 1 s)
  W1  wiring        IND values equal the reference models on the matched bars from Zorro's first bar
                    (|z - m| <= 1e-10 + 1e-9 |m|); Reflex rows with model ms = 0 excluded (start-up, R-4)
  S1  states        the template's BAR-row states (c1, c2, baseline, atr) equal the model's; near-threshold bars counted
  T1  replay (a)    Zorro's halves equal the engine with the M1 layer under ONE (fill_px, start) alternative
                    (r1_replay); entry / exit price 1e-5, day, reason; 'end' halves entry only
  K1  sizing        every SIZE row recomputes from its own inputs (M-D8); its ATR equals the IND ATR of that bar
  K3  equity (a)    SIZE and ACCT Equity = Capital + closed profits + open value at the close (HALF rows)
  K3b balance (b)   ACCT Balance = Capital + closed profits
  K4  profit (a)    profit = dir (exit - entry) units;  (b) cost identity incl. spread, commission, rollover (P5)
  K5  lots          each half's lots (units / (PIPCost / PIP)) equal its signal's SIZE lots
  K6  margin        no MARGINCALL; margin share reported
"""
import csv
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r1_data as D  # noqa: E402
import r1_replay as RP  # noqa: E402

CAPITAL = 100000.0
RISK_HALF = 1.0             # % per half (nx_RiskPct / 2)
STOP_ATR = 1.5
LEVERAGE = 20.0
TOL_BAR = 1e-9              # prices printed %.10f of float32 values
TOL_IND_ABS, TOL_IND_REL = 1e-10, 1e-9
TOL_PRICE = 1e-5            # S4 C3
TOL_REL = 1e-8              # K1 (as P6)
TOL_EQ_ABS, TOL_EQ_REL = 0.01, 1e-7
TOL_PROFIT_ABS, TOL_PROFIT_REL = 2e-3, 1e-6   # TradeProfit is float32 (gotchas 9d.11)
IND_FIELDS = ("mama", "fama", "period", "alpha", "phase", "fish", "trig", "raw", "v1", "rng", "reflex", "sum", "ms",
              "atr", "tr")
WANT_A = {"costs": "0", "type": "1", "FixedLots": "0", "Capital": "100000.00", "LookBack": "520", "TradeModeFRC": "1",
          "Fill": "3", "Hedge": "2", "TICKS": "1", "BarOffset": "1020", "StartWeek": "71700", "FisherLen": "10",
          "ReflexLen": "20", "AtrLen": "14", "LotAmount": "1000"}


def read_log(path):
    L = dict(info={}, rbar=[], bar=[], size=[], error=[], half=[], acct=[], enter=[], fail=[])
    with open(path, encoding="utf-8") as f:
        for r in csv.reader(f):
            if not r:
                continue
            k = r[0]
            if k == "INFO":
                L["info"] = dict(x.split("=", 1) for x in r[3:] if "=" in x)
            elif k == "RBAR":
                L["rbar"].append(dict(bar=int(r[2]), ymd=int(r[3]), w=float(r[4]), lb=int(r[5]), o=float(r[6]),
                                      h=float(r[7]), l=float(r[8]), c=float(r[9])))
            elif k == "BAR" and len(r) >= 16:
                L["bar"].append(dict(bar=int(r[2]), ymd=int(r[4]), ok=int(r[5]), c=float(r[9]), c1=int(r[10]),
                                     c2=int(r[11]), base=float(r[12]), atr=float(r[13])))
            elif k == "SIZE":
                v = [float(x) for x in r[3:]]
                L["size"].append(dict(ymd=int(r[2]), eq=v[0], bal=v[1], mt=v[2], atr=v[3], pip=v[4], pipcost=v[5],
                                      lotamount=v[6], pct=v[7], target=v[8], stop_pips=v[9], risk_lot=v[10], raw=v[11],
                                      lots=int(v[12]), actual=v[13], mc=v[14], margin=v[15]))
            elif k == "ERROR":
                L["error"].append(",".join(r))
            elif k == "ASSETFAIL":
                L["fail"].append(",".join(r))
            elif k == "HALF":
                L["half"].append(dict(group=int(r[2]), half=int(r[3]), dir=int(r[4]), kind=r[5], entry_ymd=int(r[6]),
                                      entry=float(r[7]), exit_ymd=int(r[8]), exit=float(r[9]), reason=r[10],
                                      profit=float(r[14]), roll=float(r[15]), comm=float(r[16]), spread=float(r[17]),
                                      units=float(r[18])))
            elif k == "ACCT":
                L["acct"].append(dict(bar=int(r[2]), ymd=int(r[3]), eq=float(r[4]), bal=float(r[5]), mt=float(r[6]),
                                      mcall=int(r[7])))
            elif k == "ENTER":
                L["enter"].append(dict(ymd=int(r[2]), group=int(r[3]), dir=int(r[4]), kind=r[5], atr=float(r[6])))
    return L


def read_ind(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for r in rd:
            x = {k: float(r[k]) for k in ("open", "high", "low", "close") + IND_FIELDS}
            x.update(bar=int(r["bar"]), ymd=int(r["ymd"]), lookback=int(r["lookback"]))
            rows.append(x)
    return rows


class Report:
    def __init__(self):
        self.rows = []

    def add(self, cid, item, ok, expected, got, note="", status=None):
        self.rows.append(dict(check=cid, item=item, result=status or ("PASS" if ok else "FAIL"), expected=expected,
                              got=got, note=note))

    def fails(self):
        return [r for r in self.rows if r["result"] == "FAIL"]


# ---- B1 bars ---------------------------------------------------------------------------------------------------
def match_bars(m1, rbar):
    """(variant, bars cut to Zorro's range, per-variant mismatch counts). variant None if none matches."""
    z = {r["ymd"]: r for r in rbar}
    zdays = [r["ymd"] for r in rbar]
    lo, hi = min(zdays), max(zdays)
    out = {}
    for var in D.BAR_VARIANTS:
        b = D.daily_bars(m1, edge=var[0], friday=var[1])
        ymd = np.array([D.ymd_int(d) for d in b["day"]])
        sel = (ymd >= lo) & (ymd <= hi)
        py = ymd[sel]
        bad = 0
        if list(py) != zdays:
            bad = len(set(py) ^ set(zdays)) + (0 if set(py) != set(zdays) else 1)
        else:
            for k, d in list(zip(np.nonzero(sel)[0], py))[1:]:   # first bar may be partial (gotchas 9d.14)
                r = z[d]
                if max(abs(r["o"] - b["o"][k]), abs(r["h"] - b["h"][k]), abs(r["l"] - b["l"][k]),
                       abs(r["c"] - b["c"][k])) > TOL_BAR:
                    bad += 1
        cut = {k: (v[sel] if k not in ("keep",) else v) for k, v in b.items()}
        out[var] = (bad, cut)
    fits = [v for v, (bad, _) in out.items() if bad == 0]
    return (fits[0] if fits else None), out


def check_bar_times(rep, rbar):
    bad = []
    for r in rbar:
        y, m, d = r["ymd"] // 10000, r["ymd"] // 100 % 100, r["ymd"] % 100
        import datetime as dt
        want = D.dt_to_ole(dt.datetime(y, m, d, 17, tzinfo=D.NY).astimezone(D.UTC))
        if abs(r["w"] - want) * 86400 > 1.0:
            bad.append(r["ymd"])
    rep.add("B1", "bar_end_17NY", not bad, "every RBAR ends 17:00 New York", f"{len(bad)} off", ",".join(map(str, bad[:5])))


# ---- W1 wiring / S1 states --------------------------------------------------------------------------------------
def check_wiring(rep, ind_rows, model, bars):
    n = len(ind_rows)
    if n != len(bars["o"]):
        rep.add("W1", "rows", False, len(bars["o"]), n)
        return
    for f in IND_FIELDS:
        z = np.array([r[f] for r in ind_rows])
        m = np.asarray(model[f], dtype=float)
        excl = np.zeros(n, bool)
        if f in ("reflex",):
            excl = np.asarray(model["ms"]) == 0
        err = np.abs(z - m)
        tol = TOL_IND_ABS + TOL_IND_REL * np.abs(m)
        badk = np.nonzero((err > tol) & ~excl)[0]
        rep.add("W1", f, len(badk) == 0, "|z - m| <= 1e-10 + 1e-9|m|",
                f"{len(badk)} rows off; max err {err[~excl].max():.3e}", f"excluded {int(excl.sum())}")
    px = np.array([[r["open"], r["high"], r["low"], r["close"]] for r in ind_rows])
    pb = np.stack([bars["o"], bars["h"], bars["l"], bars["c"]], axis=1)
    rep.add("W1", "ind_prices", np.abs(px - pb).max() <= TOL_BAR, "IND prices = bars", f"{np.abs(px - pb).max():.3e}")


def check_states(rep, bar_rows, st, model, day_index):
    near = mism = 0
    for r in bar_rows:
        k = day_index.get(r["ymd"])
        if k is None:
            mism += 1
            continue
        df = model["fish"][k] - model["trig"][k]
        nb = abs(df) < 1e-9 or abs(model["reflex"][k]) < 1e-9 or abs(r["c"] - model["fama"][k]) < 1e-9
        same = (r["c1"] == st["c1"][k] and r["c2"] == st["c2"][k]
                and abs(r["base"] - model["fama"][k]) <= TOL_IND_ABS + TOL_IND_REL * abs(model["fama"][k])
                and abs(r["atr"] - model["atr"][k]) <= TOL_IND_ABS + TOL_IND_REL * abs(model["atr"][k]))
        if not same:
            if nb:
                near += 1
            else:
                mism += 1
    rep.add("S1", "states", mism == 0, "template states = model", f"{mism} differ", f"near-threshold {near} (counted)")


# ---- T1 replay --------------------------------------------------------------------------------------------------
def engine_halves(res, days_ymd):
    out = []
    for hf in sorted(res.halves, key=lambda x: (x.trade_id, x.half)):
        out.append(dict(dir=hf.dir, half=hf.half, kind=hf.kind, entry_ymd=days_ymd[hf.entry_bar], entry=hf.entry,
                        exit_ymd=days_ymd[hf.exit_bar], exit=hf.exit_price, reason=hf.reason))
    return out


def compare_halves(exp, got):
    """List of mismatch strings (empty = equal)."""
    got = sorted(got, key=lambda x: (x["group"], x["half"]))
    bad = []
    if len(exp) != len(got):
        bad.append(f"n {len(exp)} vs {len(got)}")
    for j, (e, g) in enumerate(zip(exp, got)):
        if (e["dir"], e["half"], e["kind"], e["entry_ymd"]) != (g["dir"], g["half"], g["kind"], g["entry_ymd"]) \
                or abs(e["entry"] - g["entry"]) > TOL_PRICE:
            bad.append(f"h{j} entry {e['entry_ymd']} {e['entry']:.5f} vs {g['entry_ymd']} {g['entry']:.5f}")
            continue
        if e["reason"] == "end":
            continue
        if e["reason"] != g["reason"] or e["exit_ymd"] != g["exit_ymd"] or abs(e["exit"] - g["exit"]) > TOL_PRICE:
            bad.append(f"h{j} exit {e['reason']} {e['exit_ymd']} {e['exit']:.5f} vs {g['reason']} {g['exit_ymd']} "
                       f"{g['exit']:.5f}")
    return bad


def check_replay(rep, m1, bars, st, first_trade, halves):
    days_ymd = [D.ymd_int(d) for d in bars["day"][first_trade:]]
    fits, detail = [], {}
    for fp in ("open", "close"):
        for start in ("entry", "after"):
            res, _ = RP.replay(m1, bars, st, first_trade, start=start, fill_px=fp)
            bad = compare_halves(engine_halves(res, days_ymd), halves)
            detail[(fp, start)] = (bad, res)
            if not bad:
                fits.append((fp, start))
    rep.add("T1", "replay", len(fits) >= 1, "Zorro halves = engine + M1 layer under one alternative",
            f"fits {fits or 'none'}; " + "; ".join(f"{k}: {len(v[0])} diffs" for k, v in detail.items()),
            " | ".join(next(iter(sorted(detail.values(), key=lambda v: len(v[0]))))[0][:5]))
    if fits:
        res = detail[fits[0]][1]
        rep.add("T1", "same_bar_conflicts", True, "reported", res.same_bar_conflicts, status="INFO")
    return fits


# ---- K1 / K3 / K4 / K5 / K6 --------------------------------------------------------------------------------------
def rel(a, b):
    return abs(a - b) / max(1.0, abs(b))


def check_sizing(rep, L, ind_by_ymd, close_by_ymd):
    bad = []
    for z in L["size"]:
        pct = RISK_HALF
        target = z["eq"] * pct / 100.0
        stop_pips = STOP_ATR * z["atr"] / z["pip"]
        risk_lot = stop_pips * z["pipcost"]
        raw = target / risk_lot
        mc = close_by_ymd.get(z["ymd"], float("nan")) * z["pipcost"] / z["pip"] / LEVERAGE
        ia = ind_by_ymd.get(z["ymd"], {}).get("atr", float("nan"))
        ok = (rel(z["pct"], pct) < TOL_REL and rel(z["target"], target) < TOL_REL and rel(z["risk_lot"], risk_lot) < TOL_REL
              and rel(z["raw"], raw) < TOL_REL and z["lots"] == math.floor(raw) and rel(z["actual"], z["lots"] * risk_lot) < TOL_REL
              and rel(z["mc"], mc) < TOL_REL and rel(z["margin"], 2 * z["lots"] * z["mc"]) < TOL_REL
              and abs(z["atr"] - ia) <= TOL_IND_ABS + TOL_IND_REL * abs(ia))
        if not ok:
            bad.append(z["ymd"])
    rep.add("K1", "size_rows", not bad and len(L["size"]) > 0, "every SIZE row recomputes", f"{len(bad)} of {len(L['size'])} off",
            ",".join(map(str, bad[:5])))


def open_value(halves, ymd, close):
    v = 0.0
    for h in halves:
        if h["entry_ymd"] <= ymd and (h["exit_ymd"] > ymd):
            v += h["dir"] * (close - h["entry"]) * h["units"]
    return v


def closed_profit(halves, ymd):
    return sum(h["profit"] for h in halves if h["exit_ymd"] <= ymd)


def check_equity(rep, L, close_by_ymd, mode):
    hv = L["half"]
    bad = []
    for z in L["size"]:
        if mode == "a":
            want = CAPITAL + closed_profit(hv, z["ymd"]) + open_value(hv, z["ymd"], close_by_ymd[z["ymd"]])
            if abs(z["eq"] - want) > TOL_EQ_ABS + TOL_EQ_REL * abs(want):
                bad.append(("SIZE", z["ymd"], z["eq"], want))
    for a in L["acct"]:
        if mode == "a":
            want = CAPITAL + closed_profit(hv, a["ymd"]) + open_value(hv, a["ymd"], close_by_ymd.get(a["ymd"], float("nan")))
            if abs(a["eq"] - want) > TOL_EQ_ABS + TOL_EQ_REL * abs(want):
                bad.append(("ACCT", a["ymd"], a["eq"], want))
        want_b = CAPITAL + closed_profit(hv, a["ymd"])
        if abs(a["bal"] - want_b) > TOL_EQ_ABS + TOL_EQ_REL * abs(want_b):
            bad.append(("BAL", a["ymd"], a["bal"], want_b))
    cid = "K3" if mode == "a" else "K3b"
    rep.add(cid, "equity", not bad, "Equity / Balance from HALF rows", f"{len(bad)} off", str(bad[:3]))


def check_profit(rep, L, info, mode):
    bad = []
    spread = float(info.get("Spread", "0"))
    for h in L["half"]:
        base = h["dir"] * (h["exit"] - h["entry"]) * h["units"]
        want = base if mode == "a" else base - spread * h["units"] - h["comm"] + h["roll"]
        if mode == "a" and (abs(h["roll"]) > 1e-9 or abs(h["comm"]) > 1e-9):
            bad.append(("costs", h["group"], h["half"]))
        if abs(h["profit"] - want) > TOL_PROFIT_ABS + TOL_PROFIT_REL * abs(want):
            bad.append((h["group"], h["half"], h["profit"], want))
    rep.add("K4", "profit", not bad and len(L["half"]) > 0, "profit identity per half", f"{len(bad)} off", str(bad[:3]))
    if mode == "b":
        rl, rs = float(info["RollLong"]), float(info["RollShort"])
        badr = []
        lot_amount = float(info["LotAmount"])
        for h in L["half"]:
            lots = h["units"] / (float(info["PIPCost"]) / float(info["PIP"]))
            # (a) spread.htm: rollover per 10000 contracts per day for currencies; contracts = lots x LotAmount
            rate = (rl if h["dir"] == 1 else rs) * lots * lot_amount / 10000.0
            n = h["roll"] / rate if rate else 0.0
            if abs(n - round(n)) > 1e-3:
                badr.append((h["group"], h["half"], n))
        rep.add("K4", "roll_integer_days", not badr, "rollover = whole days x rate", f"{len(badr)} off", str(badr[:3]))


def check_lots(rep, L, info):
    pip, pc = float(info["PIP"]), float(info["PIPCost"])
    lots_by_group = {}
    for k, z in enumerate(L["size"]):
        lots_by_group[k + 1] = z["lots"]
    bad = []
    for h in L["half"]:
        lots = round(h["units"] / (pc / pip))
        if lots_by_group.get(h["group"]) != lots:
            bad.append((h["group"], h["half"], lots, lots_by_group.get(h["group"])))
    rep.add("K5", "half_lots", not bad, "half lots = SIZE lots of its signal", f"{len(bad)} off", str(bad[:3]))


def check_margin(rep, L):
    mc = [a for a in L["acct"] if a["mcall"]]
    rep.add("K6", "no_margincall", not mc, "no MARGINCALL", len(mc))
    share = max((a["mt"] / a["eq"] for a in L["acct"] if a["eq"] > 0), default=0.0)
    rep.add("K6", "max_margin_share", True, "reported", f"{share:.4f}", status="INFO")


def run(mode, log_path, ind_path, history, out_path):
    rep = Report()
    L = read_log(log_path)
    ind = read_ind(ind_path)
    info = L["info"]
    want = dict(WANT_A)
    want["costs"] = "0" if mode == "a" else "1"
    bad = [k for k, v in want.items() if info.get(k) != v]
    rep.add("K0", "info", not bad, "settings", ",".join(bad) or "ok")
    rep.add("K0", "no_error_rows", not L["error"] and not L["fail"], "none", len(L["error"]) + len(L["fail"]),
            " | ".join((L["error"] + L["fail"])[:3]))
    m1 = D.load_m1(history)
    var, allv = match_bars(m1, L["rbar"])
    rep.add("B1", "bars", var is not None, "RBAR = one Python variant",
            f"fits {var}; " + "; ".join(f"{k}: {v[0]}" for k, v in allv.items()))
    check_bar_times(rep, L["rbar"])
    if var is None:
        rep.add("W1", "skipped", False, "bars matched", "no variant")
    else:
        bars = allv[var][1]
        r0 = L["rbar"][0]           # gotchas 9d.14: Zorro's first bar may be partial; the models start from Zorro's values
        diff0 = max(abs(r0[k] - bars[k][0]) for k in ("o", "h", "l", "c"))
        for k in ("o", "h", "l", "c"):
            bars[k] = bars[k].copy()
            bars[k][0] = r0[k]
        rep.add("B1", "first_bar", True, "Zorro first bar used", f"{r0['ymd']}, max diff to the full bar {diff0:.3e}",
                status="INFO")
        model = RP.indicators(bars)
        st = RP.states(model)
        day_index = {D.ymd_int(d): k for k, d in enumerate(bars["day"])}
        check_wiring(rep, ind, model, bars)
        check_states(rep, L["bar"], st, model, day_index)
        first_trade = next(k for k, r in enumerate(L["rbar"]) if r["lb"] == 0)
        if mode == "a":
            check_replay(rep, m1, bars, st, first_trade, L["half"])
    close_by_ymd = {r["ymd"]: r["c"] for r in L["rbar"]}
    ind_by_ymd = {r["ymd"]: r for r in ind}
    check_sizing(rep, L, ind_by_ymd, close_by_ymd)
    check_equity(rep, L, close_by_ymd, mode)
    check_profit(rep, L, info, mode)
    check_lots(rep, L, info)
    check_margin(rep, L)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["check", "item", "result", "expected", "got", "note"])
        w.writeheader()
        w.writerows(rep.rows)
    for r in rep.fails():
        print("FAIL", r)
    print(f"rows {len(rep.rows)}, FAIL {len(rep.fails())}; halves {len(L['half'])}; bar variant {var}")
    print("RUN PASS" if not rep.fails() else "RUN FAIL")
    return rep


def main(argv):
    if len(argv) != 5 or argv[0] not in ("a", "b"):
        print(__doc__)
        return 2
    rep = run(*argv)
    return 0 if not rep.fails() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
