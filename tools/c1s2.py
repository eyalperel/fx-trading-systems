"""C1S2 (docs/preregistration/C1S2_MAF_OtherPairs_Criteria.md): MAMA vs FAMA (C1-only) on AUD/USD and EUR/JPY.

Usage (repo root):
  python tools/c1s2.py offsets <PAIR> <BARS_log.csv> <history_dir>              writes analysis/c1screen/C1S2_offsets_<PAIR>.csv
  python tools/c1s2.py null    <PAIR> <BARS_log.csv> <history_dir> <out.csv>    resumable null runs (x2 with rollover)
  python tools/c1s2.py read    <BARS_AUDUSD.csv> <BARS_EURJPY.csv> <history_dir> <null.csv> <sha_prefix> <out.md>
Bars: the Python R1-rule bars cut to Zorro's RIND rows of the pair's BARS log (VB1 PASS required first).
Costs (P3: K1): spread x2 + asset-list rollover per pair; information rows x2 without rollover and x0 (read only).
"""
import csv
import datetime as dt
import hashlib
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "analysis", "template"))
import r1_data as D  # noqa: E402
import check_r1 as C  # noqa: E402
import check_bars_pair as B  # noqa: E402
import null1 as N  # noqa: E402
import reference_engine as E  # noqa: E402

FT = 520
SEED = 20261125
LOT_AMOUNT = 1000.0
COST = {p: dict(spread=v["Spread"], roll={1: v["RollLong"], -1: v["RollShort"]}, pip=v["PIP"], pipcost=v["PIPCost"])
        for p, v in B.PAIRS.items()}


def roll_price(pair, dirn, days):
    c = COST[pair]
    return days * c["roll"][dirn] * LOT_AMOUNT / 10000.0 / (c["pipcost"] / c["pip"])


def half_r(pair, hf, day, mult, roll=True):
    days = int(day[hf.exit_bar] - day[hf.entry_bar])
    net = hf.dir * (hf.exit_price - hf.entry) - mult * COST[pair]["spread"] + (roll_price(pair, hf.dir, days) if roll else 0.0)
    return net / (1.5 * hf.atr)


def load(pair, bars_log, history):
    _, rows, _ = B.read_log(bars_log)
    m1 = D.load_m1(history, stem=pair, years=B.PAIRS[pair]["years"])
    var, allv = C.match_bars(m1, rows)
    if var is None:
        raise SystemExit("bars do not match (VB1): refusing")
    bars = allv[var][1]
    r0 = rows[0]
    if max(abs(r0[k] - bars[k][0]) for k in ("o", "h", "l", "c")) > C.TOL_BAR:
        for k in ("o", "h", "l", "c"):
            bars[k] = bars[k].copy()
            bars[k][0] = r0[k]
    ft = next(k for k, r in enumerate(rows) if r["lb"] == 0)
    if ft != FT:
        raise SystemExit(f"first trade bar index {ft}, expected {FT} (C1S2 Range gate)")
    m = B.models(bars)
    c1 = np.sign(np.asarray(m["mama"]) - np.asarray(m["fama"])).astype(int)
    st = dict(baseline=np.asarray(m["fama"]), atr=np.asarray(m["atr"]), c1=c1, c2=np.ones(len(c1), int))
    return m1, bars, st


def offsets_path(pair):
    return os.path.join(ROOT, "analysis", "c1screen", f"C1S2_offsets_{pair}.csv")


def make_offsets(L):
    rng = np.random.default_rng(SEED)
    return np.sort(rng.choice(np.arange(260, L - 260 + 1), size=1000, replace=False))


def write_offsets(pair, bars_log, history):
    _, bars, _ = load(pair, bars_log, history)
    L = len(bars["c"]) - FT
    off = make_offsets(L)
    txt = "index,offset\n" + "".join(f"{i},{o}\n" for i, o in enumerate(off))
    with open(offsets_path(pair), "x", newline="\n") as f:
        f.write(txt)
    print(pair, "L", L, "offsets", len(off), off.min(), off.max(), "sha256", hashlib.sha256(txt.encode()).hexdigest())


def read_offsets(pair):
    with open(offsets_path(pair), encoding="utf-8") as f:
        return [int(r["offset"]) for r in csv.DictReader(f)]


def stats(pair, res, bars, mult, roll=True):
    day = np.asarray(bars["day"][FT:], dtype=np.int64)
    ymd = [D.ymd_int(d) for d in bars["day"][FT:]]
    by, year = {}, {}
    for hf in res.halves:
        by.setdefault(hf.trade_id, []).append(half_r(pair, hf, day, mult, roll))
        year[hf.trade_id] = max(year.get(hf.trade_id, 0), ymd[hf.exit_bar] // 10000)
    r = {k: float(np.mean(v)) for k, v in by.items()}
    vals = np.array(list(r.values()))
    n = len(vals)
    yr = {}
    for k, v in r.items():
        yr[year[k]] = yr.get(year[k], 0.0) + v
    best = sorted(yr.items(), key=lambda x: (-x[1], x[0]))[0] if yr else (None, 0.0)
    sd = vals.std(ddof=1) if n > 1 else float("nan")
    return dict(signals=n, halves=len(res.halves), mean=float(vals.mean()) if n else float("nan"),
                t=float(vals.mean() / (sd / math.sqrt(n))) if n > 1 and sd > 0 else float("nan"), total=float(vals.sum()),
                best_year=best[0], best_year_R=best[1], total_excl=float(vals.sum() - best[1]))


def _work(k):
    w = N._W
    s = dict(w["st"], c1=N.shift(w["st"]["c1"], k))
    res = N.run_engine(w["m1"], w["bars"], s, w["p"])
    r = stats(w["pair"], res, w["bars"], 2)
    return [dict(set=w["pair"], level="x2", offset=k, signals=r["signals"], halves=r["halves"], mean=f"{r['mean']:.6f}",
                 total=f"{r['total']:.6f}", t=f"{r['t']:.4f}")]


def null(pair, bars_log, history, out_path, seconds=150):
    m1, bars, st = load(pair, bars_log, history)
    have = N.done_keys(out_path, ("set", "level", "offset"))
    todo = [k for k in read_offsets(pair) if (pair, "x2", str(k)) not in have]
    if any(k == 0 for k in todo):
        raise SystemExit("offset 0 refused")
    N._W.update(m1=m1, bars=bars, st=st, p=E.Params(baseline_mode="off"), pair=pair)
    import multiprocessing as mp
    import time
    t0, n = time.time(), 0
    with mp.get_context("fork").Pool(2) as pool:
        for rows in pool.imap(_work, todo, chunksize=1):
            for r in rows:
                N.append(out_path, r)
            n += 1
            if time.time() - t0 > seconds:
                pool.terminate()
                break
    print(f"{pair}: {n} new offsets; left {len(todo) - n}")


def passes(real, p95):
    why = []
    if not real["mean"] > p95:
        why.append("not above own-null 95th")
    if not real["mean"] > 0:
        why.append("mean <= 0")
    if not real["total_excl"] > 0:
        why.append("total without best year <= 0")
    return (not why), why


def read(log_aud, log_jpy, history, null_path, sha_prefix, out):
    if os.path.exists(out):
        raise SystemExit("refusing to overwrite " + out)
    h = hashlib.sha256(open(null_path, "rb").read()).hexdigest()
    if len(sha_prefix) < 16 or not h.startswith(sha_prefix):
        raise SystemExit("sha256 mismatch " + null_path)
    rows = list(csv.DictReader(open(null_path)))
    o = ["# C1S2 read 1 — MAMA vs FAMA (C1-only) on AUD/USD and EUR/JPY", "",
         f"Criteria: `docs/preregistration/C1S2_MAF_OtherPairs_Criteria.md`. Null rows sha256 `{h}`.", "",
         "| Pair | Signals | Mean signal-R x2 | t | Total R | Best year (R) | Total w/o best year | Own-null 95th | Own-null pct | "
         "Pass | Why not | x2 no rollover: mean | x0: mean |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    allpass = True
    for pair, log in (("AUDUSD", log_aud), ("EURJPY", log_jpy)):
        m1, bars, st = load(pair, log, history)
        res = N.run_engine(m1, bars, st, E.Params(baseline_mode="off"))
        r = stats(pair, res, bars, 2)
        rn = stats(pair, res, bars, 2, roll=False)
        r0 = stats(pair, res, bars, 0, roll=False)
        nv = np.array([float(x["mean"]) for x in rows if x["set"] == pair and x["level"] == "x2"])
        if len(nv) != 1000:
            raise SystemExit(f"{pair}: {len(nv)} null rows, 1000 expected")
        p95 = float(np.percentile(nv, 95))
        ok, why = passes(r, p95)
        allpass &= ok
        hole = ""
        if pair == "EURJPY":
            ymd = [D.ymd_int(d) for d in bars["day"][FT:]]
            across = [hf for hf in res.halves if ymd[hf.entry_bar] <= 20171211 and ymd[hf.exit_bar] >= 20180102]
            hole = f" ({len(across)} halves open across the 2017-12-12..2018-01-01 hole)"
        o.append(f"| {pair}{hole} | {r['signals']} | {r['mean']:+.4f} | {r['t']:+.2f} | {r['total']:+.2f} | {r['best_year']} "
                 f"({r['best_year_R']:+.2f}) | {r['total_excl']:+.2f} | {p95:+.4f} | {100 * np.mean(nv <= r['mean']):.1f}% | "
                 f"{'**PASS**' if ok else 'no'} | {'; '.join(why)} | {rn['mean']:+.4f} | {r0['mean']:+.4f} |")
    o += ["", f"**MAF passes C1S2 (both pairs):** {'YES' if allpass else 'NO'}.", "",
          "Limitations (c): circular shifts are correlated draws; the engine is checked against Zorro on EUR/USD trades (V1) "
          "and on these pairs' bars and indicators only (VB1 / VW1); rollover is a 2025-07-28 snapshot; one feed per pair.", ""]
    with open(out, "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(o))
    print("\n".join(o))


def main(argv):
    if len(argv) >= 1 and argv[0] == "offsets" and len(argv) == 4:
        write_offsets(*argv[1:])
        return 0
    if len(argv) >= 1 and argv[0] == "null" and len(argv) == 5:
        null(*argv[1:])
        return 0
    if len(argv) >= 1 and argv[0] == "read" and len(argv) == 7:
        read(*argv[1:])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
