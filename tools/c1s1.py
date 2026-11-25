"""C1S1 (docs/preregistration/C1S1_C1Screen_EURUSD_Criteria.md): C1-only screen of the verified library on EUR/USD D1.

Usage (repo root):
  python tools/c1s1.py w0   <zorro_data_dir> <history_dir> <out.csv>
  python tools/c1s1.py null <zorro_data_dir> <history_dir> <out.csv> <id>          (MAF, RFX, ROF, LRS; resumable)
  python tools/c1s1.py read <zorro_data_dir> <history_dir> <null1_runs.csv> <c1s1_null.csv> <sha1_prefix> <sha2_prefix> <out.md>
Ids: FSH, MSS, MAF, RFX, ROF, LRS (criteria table). FSH / MSS null rows = NULL1 sets O1 / O2 at x2.
"""
import csv
import hashlib
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import null1 as N  # noqa: E402
import r1_replay as R1  # noqa: E402
import r2_replay as R2  # noqa: E402
import reference_engine as E  # noqa: E402

IDS = ("FSH", "MSS", "MAF", "RFX", "ROF", "LRS")
NULL1_SET = {"FSH": "O1", "MSS": "O2"}
NEAR = 1e-9


def readings(ind1, ind2):
    """State series (+1 / -1 / 0) of the six readings from indicator values (dicts of arrays or IND columns).
    ind1: mama, fama, fish, trig, reflex (Strategy 1 models / R1 IND); ind2: mesa, sma, roof, lrsi (Strategy 2 / R2 IND)."""
    sg = lambda x: np.sign(np.asarray(x, dtype=float)).astype(int)
    sma = np.asarray(ind2["sma"], dtype=float)
    mss = np.where(np.isnan(sma), 0, sg(np.asarray(ind2["mesa"], float) - np.nan_to_num(sma)))
    return dict(FSH=sg(np.asarray(ind1["fish"], float) - np.asarray(ind1["trig"], float)), MSS=mss,
                MAF=sg(np.asarray(ind1["mama"], float) - np.asarray(ind1["fama"], float)),
                RFX=sg(ind1["reflex"]), ROF=sg(ind2["roof"]), LRS=sg(np.asarray(ind2["lrsi"], float) - 0.5))


def margins(ind1, ind2):
    """Distance of each reading's quantity from its threshold (for near-threshold counting)."""
    return dict(FSH=np.abs(np.asarray(ind1["fish"], float) - np.asarray(ind1["trig"], float)),
                MSS=np.abs(np.asarray(ind2["mesa"], float) - np.nan_to_num(np.asarray(ind2["sma"], float), nan=np.inf)),
                MAF=np.abs(np.asarray(ind1["mama"], float) - np.asarray(ind1["fama"], float)),
                RFX=np.abs(np.asarray(ind1["reflex"], float)), ROF=np.abs(np.asarray(ind2["roof"], float)),
                LRS=np.abs(np.asarray(ind2["lrsi"], float) - 0.5))


def model_ind(bars):
    return R1.indicators(bars), R2.indicators(bars)


def read_ind_cols(path, cols):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {c: np.array([float(r[c]) for r in rows]) for c in cols}


def w0_compare(model_states, zorro_states, model_margin, first=N.FT):
    """Per id: (differences outside near-threshold, near-threshold differences), trade range only."""
    out = {}
    for k in IDS:
        a, b = np.asarray(model_states[k])[first:], np.asarray(zorro_states[k])[first:]
        d = a != b
        near = d & (np.asarray(model_margin[k])[first:] < NEAR)
        out[k] = (int((d & ~near).sum()), int(near.sum()))
    return out


def w0(zdata, history, out_path):
    m1, bars, _ = N.load(zdata, history)
    i1, i2 = model_ind(bars)
    ms = readings(i1, i2)
    z1 = read_ind_cols(os.path.join(zdata, "TPL_R1d_ind_run1.csv"), ("mama", "fama", "fish", "trig", "reflex"))
    z2 = read_ind_cols(os.path.join(zdata, "TPL_R2a_ind_run3.csv"), ("mesa", "sma", "roof", "lrsi"))
    n = len(bars["c"])
    if len(z1["fish"]) != n or len(z2["mesa"]) != n:
        raise SystemExit(f"IND rows {len(z1['fish'])} / {len(z2['mesa'])} vs bars {n}")
    z2s = dict(z2)
    z2s["sma"] = np.where(np.arange(n) < 9, np.nan, z2["sma"])        # SMA defined from row 10 (PERF2 A1.1)
    zs = readings(z1, z2s)
    res = w0_compare(ms, zs, margins(i1, i2))
    rows = [dict(id=k, differ=res[k][0], near_threshold=res[k][1], result="PASS" if res[k][0] == 0 else "FAIL") for k in IDS]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)
    ok = all(r["result"] == "PASS" for r in rows)
    print("W0 PASS" if ok else "W0 FAIL")
    return ok


def setup(zdata, history, cid):
    m1, bars, states = N.load(zdata, history)
    i1, i2 = model_ind(bars)
    st = dict(states["S2"])                      # ATR (identical in both); baseline / C2 unused in C1-only mode
    st["c1"] = readings(i1, i2)[cid]
    return m1, bars, st, E.Params(baseline_mode="off")


def null(zdata, history, out_path, cid, seconds=150):
    if cid not in ("MAF", "RFX", "ROF", "LRS"):
        raise SystemExit("null runs only for MAF, RFX, ROF, LRS (FSH / MSS: NULL1 O1 / O2)")
    m1, bars, st, p = setup(zdata, history, cid)
    have = N.done_keys(out_path, ("set", "level", "offset"))
    todo = [k for k in N.offsets() if (cid, "x2", str(k)) not in have]
    N._W.update(m1=m1, bars=bars, st=st, p=p, set=cid, levels=(("x2", 2),), carrier=None)
    n = N._drive(out_path, todo, seconds)
    print(f"{cid}: {n} new offsets; left: {len(todo) - n}")


# ---- read ------------------------------------------------------------------------------------------------------------
def null_table(null1_rows, c1s1_rows):
    """offset -> {id: mean} for the six ids at x2."""
    t = {}
    for r in null1_rows:
        if r["level"] == "x2" and r["set"] in ("O1", "O2"):
            cid = "FSH" if r["set"] == "O1" else "MSS"
            t.setdefault(int(r["offset"]), {})[cid] = float(r["mean"])
    for r in c1s1_rows:
        if r["level"] == "x2":
            t.setdefault(int(r["offset"]), {})[r["set"]] = float(r["mean"])
    return t


def max_stat(table):
    full = [v for v in table.values() if all(k in v for k in IDS)]
    if len(full) != len(table):
        raise SystemExit("an offset lacks a candidate's null row")
    return np.array([max(v[k] for k in IDS) for v in full])


def passes(real, p95max):
    """R-b: real dict with mean, total_excl. Returns (bool, reasons)."""
    why = []
    if not real["mean"] > p95max:
        why.append("not above max-statistic 95th")
    if not real["mean"] > 0:
        why.append("mean <= 0")
    if not real["total_excl"] > 0:
        why.append("total without best year <= 0")
    return (not why), why


def real_stats(res, bars, mult=2):
    day = np.asarray(bars["day"][N.FT:], dtype=np.int64)
    import r1_data as D
    ymd = [D.ymd_int(d) for d in bars["day"][N.FT:]]
    by, year = {}, {}
    for hf in res.halves:
        by.setdefault(hf.trade_id, []).append(N.half_r(hf, day, mult))
        year[hf.trade_id] = max(year.get(hf.trade_id, 0), ymd[hf.exit_bar] // 10000)
    r = {k: np.mean(v) for k, v in by.items()}
    vals = np.array(list(r.values()))
    yr = {}
    for k, v in r.items():
        yr[year[k]] = yr.get(year[k], 0.0) + v
    best = sorted(yr.items(), key=lambda x: (-x[1], x[0]))[0]
    n = len(vals)
    t = vals.mean() / (vals.std(ddof=1) / np.sqrt(n))
    return dict(signals=n, halves=len(res.halves), mean=float(vals.mean()), t=float(t), total=float(vals.sum()),
                best_year=best[0], best_year_R=best[1], total_excl=float(vals.sum() - best[1]))


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read(zdata, history, null1_path, c1s1_path, s1, s2, out):
    if os.path.exists(out):
        raise SystemExit("refusing to overwrite " + out)
    for p, pre in ((null1_path, s1), (c1s1_path, s2)):
        if len(pre) < 16 or not sha(p).startswith(pre):
            raise SystemExit("sha256 mismatch " + p)
    table = null_table(list(csv.DictReader(open(null1_path))), list(csv.DictReader(open(c1s1_path))))
    mx = max_stat(table)
    p95 = float(np.percentile(mx, 95))
    m1, bars, states = N.load(zdata, history)
    i1, i2 = model_ind(bars)
    rd = readings(i1, i2)
    base = dict(states["S2"])
    o = ["# C1S1 read 1 — C1-only screen of the verified library on EUR/USD D1", "",
         f"Criteria: `docs/preregistration/C1S1_C1Screen_EURUSD_Criteria.md`. Null rows: NULL1 `{sha(null1_path)}`, "
         f"C1S1 `{sha(c1s1_path)}`. K = 6, 1,000 offsets, x2.", "",
         f"**Max-statistic null (best of six per offset):** median {np.median(mx):+.4f}, 95th percentile **{p95:+.4f}** (the bar).", "",
         "| Id | Signals | Mean signal-R | t | Total R | Best year (R) | Total w/o best year | Own-null pct | Max-null pct | Pass | Why not |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    surv = []
    for cid in IDS:
        st = dict(base, c1=rd[cid])
        res = N.run_engine(m1, bars, st, E.Params(baseline_mode="off"))
        r = real_stats(res, bars)
        own = np.array([table[k][cid] for k in table])
        ok, why = passes(r, p95)
        if ok:
            surv.append(cid)
        o.append(f"| {cid} | {r['signals']} | {r['mean']:+.4f} | {r['t']:+.2f} | {r['total']:+.2f} | {r['best_year']} "
                 f"({r['best_year_R']:+.2f}) | {r['total_excl']:+.2f} | {100 * np.mean(own <= r['mean']):.1f}% | "
                 f"{100 * np.mean(mx <= r['mean']):.1f}% | {'**PASS**' if ok else 'no'} | {'; '.join(why)} |")
    o += ["", f"**Survivors:** {', '.join(surv) if surv else 'none'}.", "",
          "Limitations (c): circular shifts are correlated draws; engine vs Zorro differ on a few halves (V1); one asset, "
          "one feed; C1-only mode is our reading of VP's C1 test (NULL1 C1).", ""]
    with open(out, "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(o))
    print("\n".join(o))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "w0" and len(argv) == 4:
        return 0 if w0(*argv[1:]) else 1
    if argv[0] == "null" and len(argv) == 5:
        null(*argv[1:])
        return 0
    if argv[0] == "read" and len(argv) == 8:
        read(*argv[1:])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
