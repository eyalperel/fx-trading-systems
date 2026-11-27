"""C1S3 (docs/preregistration/C1S3_FiveC1_Pooled_Criteria.md): FSH, MSS, RFX, ROF, LRS C1-only, pooled over AUD/USD + EUR/JPY.

Usage (repo root):
  python tools/c1s3.py pairing                                                   writes analysis/c1screen/C1S3_pairing.csv
  python tools/c1s3.py null <PAIR> <IND_log.csv> <history_dir> <out.csv> [seconds]   resumable; all five ids per offset
  python tools/c1s3.py read <IND_AUDUSD.csv> <IND_EURJPY.csv> <history_dir> <null.csv> <sha_prefix> <out.md>
Bars: Python R1-rule bars (+ EUR/JPY fillers) cut to Zorro's RIND rows of the pair's TPL_IND_PAIR log (VB1 / VW2 PASS first).
Offsets: C1S2's files (reused, P-a). Costs: spread x2 + asset-list rollover (decisive); x2 without rollover, x0 (information).
"""
import csv
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
import check_ind_pair as P  # noqa: E402
import c1s1  # noqa: E402
import c1s2  # noqa: E402
import null1 as N  # noqa: E402
import reference_engine as E  # noqa: E402

FT = 520
IDS = P.IDS
PAIRS = ("AUDUSD", "EURJPY")
PAIR_SEED = 20261126
PAIRING = os.path.join(ROOT, "analysis", "c1screen", "C1S3_pairing.csv")
OFFSET_SHA = {"AUDUSD": "69ffaa73280e71d3849468ee4ba521f1d75bd09b93df92d14d18bf0ed64e745c",
              "EURJPY": "2a357ac8eb2c4b5c194f14aeb918b548e94ed4c1acb1531135f6dbeed8cc1bb3"}


# ---- data ---------------------------------------------------------------------------------------------------------
def load(pair, ind_log, history):
    """(m1, bars, model, states): states[id] = the reading's C1 state on Zorro's bars from the reference models."""
    _, rows, _ = P.read_log(ind_log)
    m1 = D.load_m1(history, stem=pair, years=P.PAIRS[pair]["years"])
    var, allv = C.match_bars(m1, rows, fillers=P.PAIRS[pair].get("fillers"))
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
        raise SystemExit(f"first trade bar index {ft}, expected {FT}")
    model = P.models(bars)
    i1, i2 = P._ind({f: np.asarray(model[f], float) for f in P.FIELDS}, len(bars["c"]))
    rd = c1s1.readings(i1, i2)
    return m1, bars, model, {k: np.asarray(rd[k], int) for k in IDS}


def base_states(model, c1):
    """C1-only mode: baseline and C2 are unused by the engine (baseline_mode off); ATR from the model."""
    n = len(c1)
    return dict(baseline=np.asarray(model["frama"], float), atr=np.asarray(model["atr"], float), c1=c1,
                c2=np.ones(n, int))


def read_offsets(pair):
    path = c1s2.offsets_path(pair)
    raw = open(path, "rb").read()
    if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != OFFSET_SHA[pair]:
        raise SystemExit(f"{path}: sha256 mismatch: refusing")
    return [int(r["offset"]) for r in csv.DictReader(raw.decode().splitlines())]


# ---- pairing (P-a) ------------------------------------------------------------------------------------------------
def make_pairing(off_a, off_e, seed=PAIR_SEED):
    pi = np.random.default_rng(seed).permutation(len(off_e))
    return [(i, off_a[i], off_e[int(pi[i])]) for i in range(len(off_a))]


def write_pairing(path=PAIRING):
    rows = make_pairing(read_offsets("AUDUSD"), read_offsets("EURJPY"))
    txt = "draw,aud_offset,eurjpy_offset\n" + "".join(f"{i},{a},{e}\n" for i, a, e in rows)
    with open(path, "x", newline="\n") as f:
        f.write(txt)
    print("pairing", len(rows), "draws; sha256", hashlib.sha256(txt.encode()).hexdigest())


def read_pairing(path=PAIRING):
    with open(path, encoding="utf-8") as f:
        return [(int(r["draw"]), int(r["aud_offset"]), int(r["eurjpy_offset"])) for r in csv.DictReader(f)]


# ---- statistics ---------------------------------------------------------------------------------------------------
def trade_rs(pair, res, bars, mult, roll=True):
    """[(signal-R, exit calendar year)] per signal (two halves averaged), as c1s2.stats."""
    day = np.asarray(bars["day"][FT:], dtype=np.int64)
    ymd = [D.ymd_int(d) for d in bars["day"][FT:]]
    by, year = {}, {}
    for hf in res.halves:
        by.setdefault(hf.trade_id, []).append(c1s2.half_r(pair, hf, day, mult, roll))
        year[hf.trade_id] = max(year.get(hf.trade_id, 0), ymd[hf.exit_bar] // 10000)
    return [(float(np.mean(v)), year[k]) for k, v in by.items()]


def stats(trs):
    vals = np.array([r for r, _ in trs])
    n = len(vals)
    yr = {}
    for r, y in trs:
        yr[y] = yr.get(y, 0.0) + r
    best = sorted(yr.items(), key=lambda x: (-x[1], x[0]))[0] if yr else (None, 0.0)
    sd = vals.std(ddof=1) if n > 1 else float("nan")
    return dict(signals=n, mean=float(vals.mean()) if n else float("nan"), total=float(vals.sum()),
                t=float(vals.mean() / (sd / math.sqrt(n))) if n > 1 and sd > 0 else float("nan"),
                best_year=best[0], best_year_R=best[1], total_excl=float(vals.sum() - best[1]))


def pooled_null(table, pairing):
    """table[(id, pair, offset)] = (signals, total). Returns {id: array of pooled means per draw}, array of max."""
    pm = {}
    for cid in IDS:
        v = []
        for _, oa, oe in pairing:
            sa, ta = table[(cid, "AUDUSD", oa)]
            se, te = table[(cid, "EURJPY", oe)]
            v.append((ta + te) / (sa + se))
        pm[cid] = np.array(v)
    return pm, np.max(np.vstack([pm[c] for c in IDS]), axis=0)


def passes(pooled, per_pair, bar):
    """P-a rule: (pass, reasons)."""
    why = []
    if not pooled["mean"] > bar:
        why.append("not above max-null 95th")
    if not pooled["mean"] > 0:
        why.append("pooled mean <= 0")
    for pair, s in per_pair.items():
        if not s["mean"] > 0:
            why.append(f"{pair} mean <= 0")
    if not pooled["total_excl"] > 0:
        why.append("pooled total without best year <= 0")
    return (not why), why


# ---- null runs ----------------------------------------------------------------------------------------------------
FIELDS = ["set", "pair", "level", "offset", "signals", "halves", "mean", "total", "t"]


def append(out_path, row):
    new = not os.path.exists(out_path)
    with open(out_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def _work(k):
    w = N._W
    out = []
    for cid in IDS:
        s = dict(w["base"], c1=N.shift(w["states"][cid], k))
        res = N.run_engine(w["m1"], w["bars"], s, E.Params(baseline_mode="off"))
        trs = trade_rs(w["pair"], res, w["bars"], 2)
        r = stats(trs)
        out.append(dict(set=cid, pair=w["pair"], level="x2", offset=k, signals=r["signals"], halves=len(res.halves),
                        mean=f"{r['mean']:.6f}", total=f"{r['total']:.6f}", t=f"{r['t']:.4f}"))
    return out


def null(pair, ind_log, history, out_path, seconds=150):
    m1, bars, model, states = load(pair, ind_log, history)
    have = {}
    if os.path.exists(out_path):
        for r in csv.DictReader(open(out_path, encoding="utf-8")):
            have.setdefault((r["pair"], r["offset"]), set()).add(r["set"])
    partial = [k for k, v in have.items() if k[0] == pair and v != set(IDS)]
    if partial:
        raise SystemExit(f"partial offsets in {out_path}: {partial[:3]} (an offset writes all five ids or none)")
    todo = [k for k in read_offsets(pair) if (pair, str(k)) not in have]
    if any(k == 0 for k in todo):
        raise SystemExit("offset 0 refused")
    N._W.update(m1=m1, bars=bars, pair=pair, states=states, base=base_states(model, states["FSH"]))
    import multiprocessing as mp
    import time
    t0, n = time.time(), 0
    with mp.get_context("fork").Pool(2) as pool:
        for rows in pool.imap(_work, todo, chunksize=1):
            for r in rows:
                append(out_path, r)
            n += 1
            if seconds and time.time() - t0 > seconds:
                pool.terminate()
                break
    print(f"{pair}: {n} new offsets (x 5 ids); left {len(todo) - n}")


# ---- read ---------------------------------------------------------------------------------------------------------
def null_table(rows):
    t = {}
    for r in rows:
        if r["level"] == "x2":
            key = (r["set"], r["pair"], int(r["offset"]))
            if key in t:
                raise SystemExit(f"duplicate null row {key}")
            t[key] = (int(r["signals"]), float(r["total"]))
    return t


def read(log_aud, log_jpy, history, null_path, sha_prefix, out):
    if os.path.exists(out):
        raise SystemExit("refusing to overwrite " + out)
    h = hashlib.sha256(open(null_path, "rb").read()).hexdigest()
    if len(sha_prefix) < 16 or not h.startswith(sha_prefix):
        raise SystemExit("sha256 mismatch " + null_path)
    table = null_table(list(csv.DictReader(open(null_path, encoding="utf-8"))))
    if len(table) != len(IDS) * 2 * 1000:
        raise SystemExit(f"{len(table)} null rows, {len(IDS) * 2000} expected")
    pairing = read_pairing()
    pm, mx = pooled_null(table, pairing)
    bar = float(np.percentile(mx, 95))
    real = {}
    for pair, log in (("AUDUSD", log_aud), ("EURJPY", log_jpy)):
        m1, bars, model, states = load(pair, log, history)
        for cid in IDS:
            res = N.run_engine(m1, bars, base_states(model, states[cid]), E.Params(baseline_mode="off"))
            real[(cid, pair)] = {lvl: trade_rs(pair, res, bars, mult, roll)
                                 for lvl, mult, roll in (("x2", 2, True), ("x2nr", 2, False), ("x0", 0, False))}
    o = ["# C1S3 read 1 — FSH, MSS, RFX, ROF, LRS (C1-only), pooled AUD/USD + EUR/JPY", "",
         f"Criteria: `docs/preregistration/C1S3_FiveC1_Pooled_Criteria.md`. Null rows sha256 `{h}`. Pairing "
         f"`analysis/c1screen/C1S3_pairing.csv`.", "",
         f"**Pooled max-statistic null (best of 5 per draw), x2:** median {np.median(mx):+.4f}, **95th percentile {bar:+.4f}** "
         "(the bar).", "",
         "| Id | Signals (AUD / JPY) | Pooled mean x2 | t | Total R | Best year (R) | Total w/o best year | AUD/USD mean | "
         "EUR/JPY mean | Own-null median (5th / 95th) | Own-null pct | Max-null pct | Pass | Why not | x2 no roll | x0 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    npass = 0
    for cid in IDS:
        per = {p: stats(real[(cid, p)]["x2"]) for p in PAIRS}
        pool = stats(real[(cid, "AUDUSD")]["x2"] + real[(cid, "EURJPY")]["x2"])
        pnr = stats(real[(cid, "AUDUSD")]["x2nr"] + real[(cid, "EURJPY")]["x2nr"])
        p0 = stats(real[(cid, "AUDUSD")]["x0"] + real[(cid, "EURJPY")]["x0"])
        ok, why = passes(pool, per, bar)
        npass += ok
        v = pm[cid]
        o.append(f"| {cid} | {per['AUDUSD']['signals']} / {per['EURJPY']['signals']} | {pool['mean']:+.4f} | {pool['t']:+.2f} | "
                 f"{pool['total']:+.2f} | {pool['best_year']} ({pool['best_year_R']:+.2f}) | {pool['total_excl']:+.2f} | "
                 f"{per['AUDUSD']['mean']:+.4f} | {per['EURJPY']['mean']:+.4f} | {np.median(v):+.4f} "
                 f"({np.percentile(v, 5):+.4f} / {np.percentile(v, 95):+.4f}) | {100 * np.mean(v <= pool['mean']):.1f}% | "
                 f"{100 * np.mean(mx <= pool['mean']):.1f}% | {'**PASS**' if ok else 'no'} | {'; '.join(why)} | "
                 f"{pnr['mean']:+.4f} | {p0['mean']:+.4f} |")
    o += ["", f"**Survivors:** {npass}.", "",
          "Limitations (c): circular shifts are correlated draws; the engine is checked against Zorro on EUR/USD trades (V1) and "
          "on these pairs' bars and indicators only (VB1 / VW2); rollover is a 2025-07-28 snapshot; one feed per pair.", ""]
    with open(out, "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(o))
    print("\n".join(o))


def main(argv):
    if argv[:1] == ["pairing"] and len(argv) == 1:
        write_pairing()
        return 0
    if argv[:1] == ["null"] and len(argv) in (5, 6):
        null(*argv[1:5], seconds=int(argv[5]) if len(argv) == 6 else 150)
        return 0
    if argv[:1] == ["read"] and len(argv) == 7:
        read(*argv[1:])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
