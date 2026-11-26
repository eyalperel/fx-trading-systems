"""NULL1 (docs/preregistration/NULL1_TemplateNull_Criteria.md): the template's null distribution on EUR/USD D1.

Usage (run from the repo root; history and Zorro Data folders as arguments):
  python tools/null1.py v1   <zorro_data_dir> <history_dir> <out.csv>                 cost-model check V1 (C3)
  python tools/null1.py run  <zorro_data_dir> <history_dir> <out.csv> <set> <mult> [<max_runs>]
                                                       null runs, resumable (appends; skips offsets already in out.csv)
  python tools/null1.py pc   <zorro_data_dir> <history_dir> <out.csv> <set> <mu> [<max_runs>]
                                                       positive control (C5): carrier + null on injected prices, x2
Sets: F1, F2 (full template, Strategy 1 / 2), O1, O2 (C1-only, Fisher / MESA vs SMA(10)).
Bars: the PERF bars, cut by R1d run 1's RBAR rows (TPL_R1d_log_run1.csv in <zorro_data_dir>). Trade range rows 520..5489.

Costs (C3, K1): net half P&L = dir (exit - entry) - mult x 0.00012 + rollover, rollover = days x rate x LotAmount / 10000 /
(PIPCost / PIP) in price units, rate RollLong / RollShort, days = (exit bar date - entry bar date) in calendar days (rule
H_BAR of P5, gotchas 9d.19: one charge per 17:00 New York boundary after 12 h; both entries at a bar start and exits inside
bar u or at bar u's start give date(u) - date(entry bar)). Half-R = net / (1.5 x ATR); signal-R = mean of its two halves.
No real, unshifted C1-only result is ever computed (NULL1 Purpose): run/pc refuse offset 0.
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
import r1_replay as R1  # noqa: E402
import r2_replay as R2  # noqa: E402
import reference_engine as E  # noqa: E402

FT = 520                      # first trade row (LookBack 520)
BASE_SPREAD = 0.00012         # asset list (R1b / R2b INFO)
ROLL = {1: -0.8947, -1: 0.4259}
LOT_AMOUNT, PIP, PIPCOST = 1000.0, 0.0001, 0.08561
STOP_ATR = 1.5
CARRIER = 2485                # C5: carrier shift (half the trade range; not in the offset list)
OFFSETS_FILE = os.path.join(ROOT, "analysis", "null_template", "NULL1_offsets.csv")
OFFSETS_SHA = "f54e5308cd7daa7865b111e59f1af5b3b1a60b9733ec8f522ce9c84678753fa4"


def roll_price(dirn, days):
    return days * ROLL[dirn] * LOT_AMOUNT / 10000.0 / (PIPCOST / PIP)


def load(zdata, history):
    L = C.read_log(os.path.join(zdata, "TPL_R1d_log_run1.csv"))
    m1 = D.load_m1(history)
    var, allv = C.match_bars(m1, L["rbar"])
    bars = allv[var][1]
    m_s1, m_s2 = R1.indicators(bars), R2.indicators(bars)
    return m1, bars, dict(S1=R1.states(m_s1), S2=R2.states(m_s2))


def config(states, set_name):
    """(states dict, Params) of a set (C1 table)."""
    st = states["S1" if set_name in ("F1", "O1") else "S2"]
    p = E.Params(baseline_mode="off") if set_name.startswith("O") else E.Params()
    return st, p


def shift(c1, k):
    """C2: state'[t] = state[FT + ((t - FT - k) mod L)] on the trade range; rows before FT unchanged."""
    c1 = np.asarray(c1).copy()
    c1[FT:] = np.roll(c1[FT:], k)
    return c1


def half_r(hf, day, mult):
    days = int(day[hf.exit_bar] - day[hf.entry_bar])
    net = hf.dir * (hf.exit_price - hf.entry) - mult * BASE_SPREAD + roll_price(hf.dir, days)
    return net / (STOP_ATR * hf.atr)


def run_engine(m1, bars, st, p):
    res, _ = R1.replay(m1, bars, st, FT, p=p, start="entry", fill_px="open", fast=True)   # identical to the slow resolver (test + NULL1 record)
    return res


def signal_stats(res, bars, mult):
    day = np.asarray(bars["day"][FT:], dtype=np.int64)
    by = {}
    for hf in res.halves:
        by.setdefault(hf.trade_id, []).append(half_r(hf, day, mult))
    r = np.array([np.mean(v) for v in by.values()])
    n = len(r)
    sd = r.std(ddof=1) if n > 1 else float("nan")
    return dict(signals=n, halves=len(res.halves), mean=float(r.mean()) if n else float("nan"), total=float(r.sum()),
                t=float(r.mean() / (sd / math.sqrt(n))) if n > 1 and sd > 0 else float("nan"))


# ---- C5 injection ------------------------------------------------------------------------------------------------
def inject(m1, bars, carrier, atr, mu):
    """Float64 copy of the M1 fields with the planted drift; bars rebuilt from it. Bar t+1's records move by
    s_t x mu x ATR_t x f (f = time fraction of bar t+1), later bars by the full amount (cumulative)."""
    out = {k: np.asarray(m1[k], dtype=np.float64).copy() for k in ("t", "o", "h", "l", "c")}
    nb = len(bars["o"])
    add = np.zeros(len(out["t"]))
    cum = 0.0
    for t in range(FT - 1, nb - 1):
        i0, i1 = int(bars["i0"][t + 1]), int(bars["i1"][t + 1])
        step = carrier[t] * mu * atr[t] if carrier[t] != 0 else 0.0
        t0, t1 = bars["end_ole"][t], bars["end_ole"][t + 1]
        f = np.clip((out["t"][i0:i1 + 1] - t0) / (t1 - t0), 0.0, 1.0)
        add[i0:i1 + 1] = cum + step * f
        cum += step
    if nb:
        add[int(bars["i1"][nb - 1]) + 1:] = cum
    for k in ("o", "h", "l", "c"):
        out[k] = out[k] + add
    nbars = dict(bars)
    keep = bars.get("keep")
    for k in ("o", "h", "l", "c"):
        nbars[k] = np.asarray(bars[k], dtype=np.float64).copy()
    for t in range(FT, nb):
        idx = np.arange(int(bars["i0"][t]), int(bars["i1"][t]) + 1)
        if keep is not None:
            idx = idx[keep[idx]]
        nbars["o"][t], nbars["c"][t] = out["o"][idx[0]], out["c"][idx[-1]]
        nbars["h"][t], nbars["l"][t] = out["h"][idx].max(), out["l"][idx].min()
    return out, nbars


# ---- V1 cost-model check ------------------------------------------------------------------------------------------
def zorro_halves(log_path):
    L = C.read_log(log_path)
    risk = {k + 1: z["actual"] for k, z in enumerate(L["size"])}
    out = []
    for h in sorted(L["half"], key=lambda x: (x["group"], x["half"])):
        out.append(dict(group=h["group"], half=h["half"], entry_ymd=h["entry_ymd"], exit_ymd=h["exit_ymd"],
                        reason=h["reason"], r=h["profit"] / risk[h["group"]]))
    return out


def v1(zdata, history, out_path):
    m1, bars, states = load(zdata, history)
    day = np.asarray(bars["day"][FT:], dtype=np.int64)
    ymd = [D.ymd_int(d) for d in bars["day"][FT:]]
    rows, ok_all = [], True
    for sname, setn, log, mult in (("S1", "F1", "TPL_R1c_log_run1.csv", 2), ("S1", "F1", "TPL_R1d_log_run1.csv", 1),
                                   ("S2", "F2", "TPL_R2c_log_run1.csv", 2), ("S2", "F2", "TPL_R2b_log_run1.csv", 1)):
        st, p = config(states, setn)
        res = run_engine(m1, bars, st, p)
        eng = sorted(res.halves, key=lambda x: (x.trade_id, x.half))
        z = zorro_halves(os.path.join(zdata, log))
        same = sum(1 for e, g in zip(eng, z) if (ymd[e.entry_bar], ymd[e.exit_bar], e.reason) ==
                   (g["entry_ymd"], g["exit_ymd"], g["reason"]))
        er = {}
        for e in eng:
            er.setdefault(e.trade_id, []).append(half_r(e, day, mult))
        zr = {}
        for g in z:
            zr.setdefault(g["group"], []).append(g["r"])
        es = np.array([np.mean(v) for v in er.values()])
        zs = np.array([np.mean(v) for v in zr.values()])
        dh = [abs(half_r(e, day, mult) - g["r"]) for e, g in zip(eng, z)]
        c1_ = len(eng) == len(z)
        c2_ = same >= 0.98 * len(z)
        c3_ = abs(es.sum() - zs.sum()) <= 1.0 and abs(es.mean() - zs.mean()) <= 0.005
        ok = c1_ and c2_ and c3_
        ok_all &= ok
        rows.append(dict(log=log, mult=mult, halves_engine=len(eng), halves_zorro=len(z), same_days_reason=same,
                         share=f"{same / max(1, len(z)):.4f}", total_engine=f"{es.sum():.4f}", total_zorro=f"{zs.sum():.4f}",
                         mean_diff=f"{es.mean() - zs.mean():+.5f}", max_half_r_diff=f"{max(dh):.4f}",
                         median_half_r_diff=f"{np.median(dh):.5f}", result="PASS" if ok else "FAIL"))
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)
    print("V1 PASS" if ok_all else "V1 FAIL")
    return ok_all


# ---- null runs and positive control --------------------------------------------------------------------------------
def offsets():
    with open(OFFSETS_FILE, "rb") as f:
        raw = f.read()
    if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != OFFSETS_SHA:
        raise SystemExit("offsets file sha256 mismatch: refusing")
    return [int(r["offset"]) for r in csv.DictReader(raw.decode().splitlines())]


def done_keys(out_path, cols):
    if not os.path.exists(out_path):
        return set()
    with open(out_path, encoding="utf-8") as f:
        return {tuple(r[c] for c in cols) for r in csv.DictReader(f)}


FIELDS = ["set", "level", "offset", "signals", "halves", "mean", "total", "t"]


def append(out_path, row):
    new = not os.path.exists(out_path)
    with open(out_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


_W = {}


def _work(k):
    """One engine run (worker; context in _W, inherited by fork). Returns rows for every cost level."""
    w = _W
    if k == "carrier":
        s = dict(w["st"], c1=w["carrier"])
    else:
        s = dict(w["st"], c1=shift(w["st"]["c1"], k))
    res = run_engine(w["m1"], w["bars"], s, w["p"])
    out = []
    for lvl, mult in w["levels"]:
        r = signal_stats(res, w["bars"], mult)
        out.append(dict(set=w["set"], level=lvl, offset=k, signals=r["signals"], halves=r["halves"],
                        mean=f"{r['mean']:.6f}", total=f"{r['total']:.6f}", t=f"{r['t']:.4f}"))
    return out


def _drive(out_path, todo, seconds, workers=2):
    import multiprocessing as mp
    import time
    t0, n = time.time(), 0
    ctx = mp.get_context("fork")
    with ctx.Pool(workers) as pool:
        for rows in pool.imap(_work, todo, chunksize=1):
            for r in rows:
                append(out_path, r)
            n += 1
            if seconds and time.time() - t0 > seconds:
                pool.terminate()
                break
    return n


def run_null(zdata, history, out_path, set_name, mult, max_runs=None, seconds=150):
    """Null runs of one set. One engine run serves x0 and x2 (costs do not change the engine's trades); mult is kept in
    the signature for the CLI and must be 2."""
    if mult != 2:
        raise SystemExit("run writes x2 and x0 together: pass mult 2")
    m1, bars, states = load(zdata, history)
    st, p = config(states, set_name)
    have = done_keys(out_path, ("set", "level", "offset"))
    todo = [k for k in offsets() if (set_name, "x2", str(k)) not in have or (set_name, "x0", str(k)) not in have]
    if any(k == 0 for k in todo):
        raise SystemExit("offset 0 refused (NULL1 Purpose)")
    if max_runs:
        todo = todo[:max_runs]
    _W.update(m1=m1, bars=bars, st=st, p=p, set=set_name, levels=(("x2", 2), ("x0", 0)), carrier=None)
    n = _drive(out_path, todo, seconds)
    left = len(todo) - n
    print(f"{set_name}: {n} new offsets (x2 + x0); left in this call's list: {left}")


def run_pc(zdata, history, out_path, set_name, mu, max_runs=None, seconds=150):
    if not set_name.startswith("O"):
        raise SystemExit("positive control on O1 / O2 only (C5)")
    m1, bars, states = load(zdata, history)
    st, p = config(states, set_name)
    carrier = shift(st["c1"], CARRIER)
    m1i, barsi = inject(m1, bars, carrier, np.asarray(st["atr"]), mu)
    lvl = f"mu{mu:g}"
    have = done_keys(out_path, ("set", "level", "offset"))
    todo = [k for k in ["carrier"] + offsets() if (set_name, lvl, str(k)) not in have]
    if max_runs:
        todo = todo[:max_runs]
    _W.update(m1=m1i, bars=barsi, st=st, p=p, set=set_name, levels=((lvl, 2),), carrier=carrier)
    n = _drive(out_path, todo, seconds)
    print(f"{set_name} {lvl}: {n} new runs; left in this call's list: {len(todo) - n}")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "v1" and len(argv) == 4:
        return 0 if v1(*argv[1:4]) else 1
    if cmd == "run" and len(argv) in (6, 7):
        run_null(argv[1], argv[2], argv[3], argv[4], int(argv[5]), int(argv[6]) if len(argv) == 7 else None)
        return 0
    if cmd == "pc" and len(argv) in (6, 7):
        run_pc(argv[1], argv[2], argv[3], argv[4], float(argv[5]), int(argv[6]) if len(argv) == 7 else None)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
