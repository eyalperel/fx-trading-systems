"""R2 checker (PERF2 P-2): real-data runs of the NNFX template for Strategy 2 variant 0 on EUR/USD D1.

Usage: python tools/check_r2.py a <template_log.csv> <ind.csv> <history_dir> <results.csv>   (R2a, costs off, + T1 replay)
       python tools/check_r2.py b <template_log.csv> <ind.csv> <history_dir> <results.csv>   (R2b, costs x1)
       python tools/check_r2.py c <template_log.csv> <ind.csv> <history_dir> <results.csv>   (R2c, costs, spread x2)
Exit 0 = PASS. Criteria: docs/preregistration/PERF2_Strategy2_EURUSD_Criteria.md (P-2) and TPL_R1_Criteria.md (check
definitions). MECHANICS ONLY: no P&L, win rate or R summary is computed or printed.

Reuses check_r1 (bars B1, sizing K1, equity K3 / K3b, profit K4, lots K5, margin K6, K0 levels, half comparison) and
replaces the Strategy 1 parts:
  K0  INFO settings incl. FramaN 32, MesaLen 20, MesaHP 48, MesaSS 10, C1SmaLen 10, LrsiGamma 0.5, AtrLen 14, BtfOn 1;
      b / c: SpreadMult 1 / 2, every HALF row pays base spread x mult (check_r1.check_k0_levels)
  W1  every IND field equals the r2_replay models (|z - m| <= 1e-10 + 1e-9 |m|) on the matched bars from Zorro's first
      bar; 'sma' compared from the row where s2_C1SmaLen MESA outputs exist (earlier rows hold no SMA by definition, C1
      state 0 there: S1); 'nmesa' = row index + 1 exactly
  X1  own SMA vs Zorro SMA() on the same rows: |own - zorro| <= 1e-9 |own| + 1e-15; earlier rows reported (INFO)
  S1  BAR-row c1, c2, baseline, atr equal the model's; bars within 1e-9 of a threshold counted, not failed
  T1  (a) halves equal the engine + M1 layer under ONE (fill_px, start) alternative, and the template's bridge-too-far
      REFUSED rows (days) equal the engine's refusals
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_r1 as C  # noqa: E402
import r1_data as D  # noqa: E402
import r2_replay as R2  # noqa: E402

TOL_IND_ABS, TOL_IND_REL = C.TOL_IND_ABS, C.TOL_IND_REL
TOL_X1_REL, TOL_X1_ABS = 1e-9, 1e-15
NEAR = 1e-9
SMA_N = 10
IND_FIELDS = ("frama", "dim", "alpha", "mesa", "roof", "stoc", "sma", "lrsi", "l0", "l3", "den", "atr", "tr")
MULT = {"b": 1, "c": 2}
WANT = {"type": "1", "FixedLots": "0", "Capital": "100000.00", "LookBack": "520", "TradeModeFRC": "1", "Fill": "3",
        "Hedge": "2", "TICKS": "1", "BarOffset": "1020", "StartWeek": "71700", "FramaN": "32", "MesaLen": "20",
        "MesaHP": "48", "MesaSS": "10", "C1SmaLen": "10", "LrsiGamma": "0.500000", "AtrLen": "14", "BtfOn": "1",
        "LotAmount": "1000"}


class ColumnCountError(Exception):
    pass


def read_ind(path):
    """IND rows by header name. Every data row must have exactly the header's field count (PERF2 Amendment 4: R2a runs 1-2
    carried a stray last column that DictReader would otherwise drop silently)."""
    rows = []
    with open(path, encoding="utf-8") as f:
        rd = csv.reader(f)
        head = next(rd)
        bad = [k + 2 for k, r in enumerate(rd) if r and len(r) != len(head)]
    if bad:
        raise ColumnCountError(f"{path}: {len(bad)} IND rows do not have {len(head)} fields (first at line {bad[0]})")
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            x = {k: float(r[k]) for k in ("open", "high", "low", "close", "zsma") + IND_FIELDS}
            x.update(bar=int(r["bar"]), ymd=int(r["ymd"]), lookback=int(r["lookback"]), nmesa=int(round(float(r["nmesa"]))))
            rows.append(x)
    return rows


def read_refused(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for r in csv.reader(f):
            if r and r[0] == "REFUSED":
                out.append(dict(ymd=int(r[2]), reason=r[3], kind=r[4] if len(r) > 4 else ""))
    return out


def check_wiring(rep, ind_rows, model, bars, sma_n=SMA_N):
    n = len(ind_rows)
    if n != len(bars["o"]):
        rep.add("W1", "rows", False, len(bars["o"]), n)
        return
    for f in IND_FIELDS:
        z = np.array([r[f] for r in ind_rows])
        m = np.asarray(model[f], dtype=float)
        use = ~np.isnan(m)
        err = np.where(use, np.abs(z - np.nan_to_num(m)), 0.0)
        tol = TOL_IND_ABS + TOL_IND_REL * np.abs(np.nan_to_num(m))
        badk = np.nonzero((err > tol) & use)[0]
        rep.add("W1", f, len(badk) == 0, "|z - m| <= 1e-10 + 1e-9|m|", f"{len(badk)} rows off; max err {err.max():.3e}",
                f"rows compared {int(use.sum())} of {n}")
    cnt = np.array([r["nmesa"] for r in ind_rows])
    rep.add("W1", "nmesa", bool(np.all(cnt == np.arange(1, n + 1))), "nmesa = row + 1", f"first {cnt[:3].tolist()}")
    px = np.array([[r["open"], r["high"], r["low"], r["close"]] for r in ind_rows])
    pb = np.stack([bars["o"], bars["h"], bars["l"], bars["c"]], axis=1)
    rep.add("W1", "ind_prices", np.abs(px - pb).max() <= C.TOL_BAR, "IND prices = bars", f"{np.abs(px - pb).max():.3e}")


def check_x1(rep, ind_rows, sma_n=SMA_N):
    own = np.array([r["sma"] for r in ind_rows])
    zs = np.array([r["zsma"] for r in ind_rows])
    k0 = sma_n - 1
    err = np.abs(own[k0:] - zs[k0:])
    tol = TOL_X1_REL * np.abs(own[k0:]) + TOL_X1_ABS
    bad = int((err > tol).sum())
    rep.add("X1", "sma_vs_zorro", bad == 0 and len(err) > 0, "|own - SMA()| <= 1e-9|own| + 1e-15 from row n-1",
            f"{bad} of {len(err)} off; max err {err.max() if len(err) else float('nan'):.3e}")
    early = int((np.abs(own[:k0] - zs[:k0]) > TOL_X1_REL * np.abs(own[:k0]) + TOL_X1_ABS).sum())
    rep.add("X1", "startup_rows", True, "reported", f"{early} of {k0} start-up rows differ", status="INFO")


def check_states(rep, bar_rows, st, model, day_index):
    near = mism = 0
    for r in bar_rows:
        k = day_index.get(r["ymd"])
        if k is None:
            mism += 1
            continue
        sm = model["sma"][k]
        nb = ((not np.isnan(sm) and abs(model["mesa"][k] - sm) < NEAR) or abs(model["lrsi"][k] - 0.5) < NEAR
              or abs(r["c"] - model["frama"][k]) < NEAR)
        same = (r["c1"] == st["c1"][k] and r["c2"] == st["c2"][k]
                and abs(r["base"] - model["frama"][k]) <= TOL_IND_ABS + TOL_IND_REL * abs(model["frama"][k])
                and abs(r["atr"] - model["atr"][k]) <= TOL_IND_ABS + TOL_IND_REL * abs(model["atr"][k]))
        if not same:
            if nb:
                near += 1
            else:
                mism += 1
    rep.add("S1", "states", mism == 0, "template states = model", f"{mism} differ", f"near-threshold {near} (counted)")


def compare_refusals(eng, days_ymd, refused):
    """Engine bridge-too-far refusals (bar, dir, reason) vs the template's REFUSED bridge-too-far rows (by day)."""
    e = sorted(days_ymd[t] for t, _, why in eng if why == "bridge-too-far")
    z = sorted(r["ymd"] for r in refused if r["reason"] == "bridge-too-far")
    return [] if e == z else [f"engine {len(e)} {e[:5]} vs template {len(z)} {z[:5]}"]


def check_replay(rep, m1, bars, st, first_trade, halves, refused):
    days_ymd = [D.ymd_int(d) for d in bars["day"][first_trade:]]
    fits, detail = [], {}
    for fp in ("open", "close"):
        for start in ("entry", "after"):
            res, _ = R2.replay(m1, bars, st, first_trade, start=start, fill_px=fp)
            bad = C.compare_halves(C.engine_halves(res, days_ymd), halves) + compare_refusals(res.refusals, days_ymd, refused)
            detail[(fp, start)] = (bad, res)
            if not bad:
                fits.append((fp, start))
    rep.add("T1", "replay", len(fits) >= 1, "halves and bridge-too-far refusals = engine + M1 layer under one alternative",
            f"fits {fits or 'none'}; " + "; ".join(f"{k}: {len(v[0])} diffs" for k, v in detail.items()),
            " | ".join(sorted(detail.values(), key=lambda v: len(v[0]))[0][0][:5]))
    if fits:
        res = detail[fits[0]][1]
        rep.add("T1", "same_bar_conflicts", True, "reported", res.same_bar_conflicts, status="INFO")
        rep.add("T1", "btf_refusals", True, "reported", len(res.refusals), status="INFO")
    return fits


def run(mode, log_path, ind_path, history, out_path):
    rep = C.Report()
    L = C.read_log(log_path)
    refused = read_refused(log_path)
    kmode = "a" if mode == "a" else "b"
    ind = read_ind(ind_path)
    info = L["info"]
    want = dict(WANT)
    want["costs"] = "0" if mode == "a" else "1"
    bad = [k for k, v in want.items() if info.get(k) != v]
    rep.add("K0", "info", not bad, "settings", ",".join(f"{k}={info.get(k)}" for k in bad) or "ok")
    rep.add("K0", "no_error_rows", not L["error"] and not L["fail"], "none", len(L["error"]) + len(L["fail"]),
            " | ".join((L["error"] + L["fail"])[:3]))
    if mode in MULT:
        C.check_k0_levels(rep, L, MULT[mode])
    m1 = D.load_m1(history)
    var, allv = C.match_bars(m1, L["rbar"])
    rep.add("B1", "bars", var is not None, "RBAR = Python bars, rule (same, own) + holidays (R1 Amendment 1)",
            f"fits {var}; " + "; ".join(f"{k}: {v[0]}" for k, v in allv.items()))
    C.check_bar_times(rep, L["rbar"])
    if var is None:
        rep.add("W1", "skipped", False, "bars matched", "no variant")
    else:
        bars = allv[var][1]
        r0 = L["rbar"][0]
        diff0 = max(abs(r0[k] - bars[k][0]) for k in ("o", "h", "l", "c"))
        patched = diff0 > C.TOL_BAR          # R1 Amendment 2: replace only a first bar that really differs (partial)
        if patched:
            for k in ("o", "h", "l", "c"):
                bars[k] = bars[k].copy()
                bars[k][0] = r0[k]
        rep.add("B1", "first_bar", True, "Zorro first bar used only if partial",
                f"{r0['ymd']}, max diff to the full bar {diff0:.3e}, replaced {patched}", status="INFO")
        model = R2.indicators(bars)
        st = R2.states(model)
        day_index = {D.ymd_int(d): k for k, d in enumerate(bars["day"])}
        check_wiring(rep, ind, model, bars)
        check_x1(rep, ind)
        check_states(rep, L["bar"], st, model, day_index)
        first_trade = next(k for k, r in enumerate(L["rbar"]) if r["lb"] == 0)
        if mode == "a":
            check_replay(rep, m1, bars, st, first_trade, L["half"], refused)
    close_by_ymd = {r["ymd"]: r["c"] for r in L["rbar"]}
    ind_by_ymd = {r["ymd"]: r for r in ind}
    C.check_sizing(rep, L, ind_by_ymd, close_by_ymd)
    C.check_equity(rep, L, close_by_ymd, kmode)
    C.check_profit(rep, L, info, kmode, per_half_spread=mode in MULT)
    C.check_lots(rep, L, info)
    C.check_margin(rep, L)
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
    if len(argv) != 5 or argv[0] not in ("a", "b", "c"):
        print(__doc__)
        return 2
    try:
        rep = run(*argv)
    except ColumnCountError as e:
        print("RUN FAIL (K0 ind_columns):", e)
        return 1
    return 0 if not rep.fails() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
