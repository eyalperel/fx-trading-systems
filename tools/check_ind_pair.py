"""C1S3 Zorro check (V-a): bars and the indicators of FSH, MSS, RFX, ROF, LRS plus FRAMA / ATR on a new dev pair equal
Python's, before any C1S3 or DIAG1 run.

Usage: python tools/check_ind_pair.py <AUDUSD|EURJPY> <IND_log.csv> <history_dir> <results.csv>
Exit 0 = PASS. Criteria: docs/preregistration/C1S3_FiveC1_Pooled_Criteria.md ("Zorro checks before any read").
No trades exist in the run; nothing about performance is computed. (VC0, the Zorro window, is read by Claude from the
pasted Error lines and recorded in the criteria file; it is not a checker item.)
  VB0  INFO settings (pair dates, asset-list costs, indicator parameters) and >= 520 bars before the first trade bar
  VB1  RBAR (from RIND rows) equal the Python bars of the R1 rule (+ EUR/JPY fillers, C1S2 A1) on every day; 17:00 NY
  VW2  fish, trig, mesa, roof, sma, reflex, lrsi, frama, atr, tr equal the reference models (1e-10 + 1e-9 |m|; sma from row
       10, as PERF2 A1.1); nmesa = row number; X1 own SMA = Zorro SMA (1e-12 + 1e-12 |m|, from row 10); the five state
       series from Zorro's values = the model's (near-threshold |x| < 1e-9 counted, not failed)
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
import check_bars_pair as B  # noqa: E402
import r1_replay as R1  # noqa: E402
import r2_replay as R2  # noqa: E402
import c1s1  # noqa: E402

TOL_ABS, TOL_REL = 1e-10, 1e-9
X1_ABS, X1_REL = 1e-12, 1e-12
NEAR = 1e-9
SMA_FIRST = 9                       # row index of the first defined SMA(10) (10 MESA outputs)
IDS = ("FSH", "MSS", "RFX", "ROF", "LRS")
FIELDS = ("fish", "trig", "mesa", "roof", "sma", "reflex", "lrsi", "frama", "atr", "tr")
NFIELD = 22                         # kind + 21 values (TPL_IND_PAIR.c specifier comment; gotchas 9d.24)
PAIRS = B.PAIRS
WANT = dict(B.WANT, LookBack2="520", FisherLen="10", ReflexLen="20", FramaN="32", MesaLen="20", MesaHP="48", MesaSS="10",
            SmaLen="10")


def read_log(path):
    info, rows, fail = {}, [], []
    with open(path, encoding="utf-8") as f:
        for r in csv.reader(f):
            if not r:
                continue
            if r[0] == "INFO":
                info = dict(x.split("=", 1) for x in r[3:] if "=" in x)
            elif r[0] == "RIND":
                if len(r) != NFIELD:
                    raise SystemExit(f"RIND row with {len(r)} fields, {NFIELD} expected (gotchas 9d.24)")
                v = [float(x) for x in r[6:]]
                rows.append(dict(bar=int(r[2]), ymd=int(r[3]), w=float(r[4]), lb=int(r[5]), o=v[0], h=v[1], l=v[2], c=v[3],
                                 fish=v[4], trig=v[5], mesa=v[6], roof=v[7], sma=v[8], zsma=v[9], nmesa=v[10],
                                 reflex=v[11], lrsi=v[12], frama=v[13], atr=v[14], tr=v[15]))
            elif r[0] == "ASSETFAIL":
                fail.append(",".join(r))
    return info, rows, fail


def check_info(rep, info, pair):
    p = PAIRS[pair]
    bad = [f"{k}={info.get(k)}" for k, v in WANT.items() if info.get(k) != v]
    for k in ("StartDate", "EndDate"):
        if info.get(k) != p[k]:
            bad.append(f"{k}={info.get(k)}")
    for k, v in [(k, p[k]) for k in ("PIP", "PIPCost", "Spread", "RollLong", "RollShort")] + [("LrsiGamma", 0.5)]:
        try:
            if abs(float(info.get(k, "nan")) - v) > 1e-6 * max(1.0, abs(v)):
                bad.append(f"{k}={info.get(k)}")
        except ValueError:
            bad.append(f"{k}={info.get(k)}")
    rep.add("VB0", "info", not bad, "settings, asset-list costs, indicator parameters", ", ".join(bad) or "ok")


def models(bars):
    i1, i2 = R1.indicators(bars), R2.indicators(bars)
    return dict(fish=i1["fish"], trig=i1["trig"], reflex=i1["reflex"], mesa=i2["mesa"], roof=i2["roof"], sma=i2["sma"],
                lrsi=i2["lrsi"], frama=i2["frama"], atr=i2["atr"], tr=i2["tr"])


def _ind(src, n):
    """Indicator dicts in the shape c1s1.readings / margins expect (MAF not a C1S3 candidate: zeros)."""
    z = np.zeros(n)
    i1 = dict(mama=z, fama=z, fish=src["fish"], trig=src["trig"], reflex=src["reflex"])
    i2 = dict(mesa=src["mesa"], sma=src["sma"], roof=src["roof"], lrsi=src["lrsi"])
    return i1, i2


def check_wiring(rep, rows, model):
    n = len(rows)
    if n != len(model["fish"]):
        rep.add("VW2", "rows", False, len(model["fish"]), n)
        return
    z = {f: np.array([r[f] for r in rows], dtype=float) for f in FIELDS + ("zsma", "nmesa")}
    z["sma"] = np.where(np.arange(n) < SMA_FIRST, np.nan, z["sma"])     # SMA defined from row 10 (PERF2 A1.1)
    for f in FIELDS:
        m = np.asarray(model[f], float)
        ok = ~np.isnan(m) if f == "sma" else np.ones(n, bool)
        err = np.abs(z[f][ok] - m[ok])
        bad = int((err > TOL_ABS + TOL_REL * np.abs(m[ok])).sum())
        if f == "sma":
            bad += int(np.isnan(z["sma"][ok]).sum() + (~ok[SMA_FIRST:]).sum())   # model must be defined from row 10
        rep.add("VW2", f, bad == 0, "|z - m| <= 1e-10 + 1e-9|m|", f"{bad} rows off; max err {err.max():.3e}")
    cnt_bad = int((z["nmesa"] != np.arange(1, n + 1)).sum())
    rep.add("VW2", "nmesa", cnt_bad == 0, "MESA output count = row number", f"{cnt_bad} rows off")
    k = np.arange(n) >= SMA_FIRST
    xe = np.abs(z["zsma"][k] - z["sma"][k])
    xbad = int((xe > X1_ABS + X1_REL * np.abs(z["sma"][k])).sum())
    rep.add("VW2", "X1_sma", xbad == 0, "own SMA = Zorro SMA (1e-12 + 1e-12|m|)", f"{xbad} rows off; max {xe.max():.3e}")
    zi1, zi2 = _ind(z, n)
    mi1, mi2 = _ind({f: np.asarray(model[f], float) for f in FIELDS}, n)
    zs, ms, mg = c1s1.readings(zi1, zi2), c1s1.readings(mi1, mi2), c1s1.margins(mi1, mi2)
    for cid in IDS:
        d = np.asarray(zs[cid]) != np.asarray(ms[cid])
        near = d & (np.asarray(mg[cid]) < NEAR)
        rep.add("VW2", f"state_{cid}", int((d & ~near).sum()) == 0, "states = model",
                f"{int((d & ~near).sum())} differ", f"near-threshold {int(near.sum())} (counted)")


def run(pair, log_path, history, out_path):
    if os.path.exists(out_path):
        raise SystemExit(f"{out_path} exists: results are never overwritten")
    rep = C.Report()
    info, rows, fail = read_log(log_path)
    rep.add("VB0", "no_assetfail", not fail, "none", len(fail))
    check_info(rep, info, pair)
    B.check_lookback(rep, rows)
    m1 = D.load_m1(history, stem=pair, years=PAIRS[pair]["years"])
    var, allv = C.match_bars(m1, rows, fillers=PAIRS[pair].get("fillers"))
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
    with open(out_path, "x", newline="") as f:
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
