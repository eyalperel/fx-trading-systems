"""DIAG1 (docs/preregistration/DIAG1_S2Slots_ZeroCost_Criteria.md + Amendment 1): Strategy 2's slot set with random C1 at
true x0 (decisive) and x0r (spread 0, rollover in; information), five arms, three pairs, calendar-year jackknife.

Usage (repo root):
  python tools/diag1.py null EURUSD <zorro_data_dir> <history_dir> <out.csv> [seconds]
  python tools/diag1.py null <AUDUSD|EURJPY> <IND_log.csv> <history_dir> <out.csv> [seconds]
  python tools/diag1.py g0   <out.csv> <null1_runs.csv>
  python tools/diag1.py read <out.csv> <sha_prefix> <report.md>
Arms (G-a): A0 = F2 (E.Params()), A1 = btf off, A2 = C2 neutral (c2 := the shifted c1), A3 = C2 neutral + btf off,
A4 = O2 (baseline_mode off). C1 = MSS states circularly shifted; baseline FRAMA, C2 LRSI, ATR unshifted (NULL1 F2).
Each output row: one (arm, pair, offset, level) with signals, halves, total and per-exit-year sums "year:R:n;...".
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
import r2_replay as R2  # noqa: E402
import null1 as N  # noqa: E402
import c1s2  # noqa: E402
import c1s3  # noqa: E402
import reference_engine as E  # noqa: E402

FT = N.FT
ARMS = ("A0", "A1", "A2", "A3", "A4")
PAIRS = ("EURUSD", "AUDUSD", "EURJPY")
LEVELS = ("x0", "x0r")
G0_TOL = 5e-7                      # NULL1 stored mean / total at 6 decimals (Amendment 1)
CONTRASTS = (("A0-A4", "A0", "A4"), ("A3-A4", "A3", "A4"), ("A0-A1", "A0", "A1"), ("A0-A2", "A0", "A2"))


def arm_config(arm, st):
    """(states, Params) of an arm, given Strategy 2 states whose c1 is already shifted."""
    s = dict(st)
    if arm in ("A2", "A3"):
        s["c2"] = np.asarray(st["c1"]).copy()                 # C2 neutral: always agrees with C1 (input only)
    if arm == "A4":
        return s, E.Params(baseline_mode="off")
    return s, E.Params(btf_on=arm not in ("A1", "A3"))


# ---- data ---------------------------------------------------------------------------------------------------------
def load(pair, src, history):
    """(m1, bars, Strategy 2 states, offsets)."""
    if pair == "EURUSD":
        m1, bars, states = N.load(src, history)
        return m1, bars, states["S2"], N.offsets()
    m1, bars, model, _ = c1s3.load(pair, src, history)
    return m1, bars, R2.states(model), c1s3.read_offsets(pair)


def half_r(pair, hf, day, level):
    """x0: no spread, no rollover. x0r: spread 0, asset-list rollover in (NULL1's x0 definition)."""
    if level == "x0":
        return hf.dir * (hf.exit_price - hf.entry) / (N.STOP_ATR * hf.atr)
    if pair == "EURUSD":
        return N.half_r(hf, day, 0)
    return c1s2.half_r(pair, hf, day, 0, roll=True)


def summarise(pair, res, bars, level):
    """(signals, halves, total, {year: [R, n]}) with signal-R = mean of the signal's halves, year = last exit year."""
    day = np.asarray(bars["day"][FT:], dtype=np.int64)
    ymd = [D.ymd_int(d) for d in bars["day"][FT:]]
    by, year = {}, {}
    for hf in res.halves:
        by.setdefault(hf.trade_id, []).append(half_r(pair, hf, day, level))
        year[hf.trade_id] = max(year.get(hf.trade_id, 0), ymd[hf.exit_bar] // 10000)
    yr = {}
    for k, v in by.items():
        e = yr.setdefault(year[k], [0.0, 0])
        e[0] += float(np.mean(v))
        e[1] += 1
    return len(by), len(res.halves), float(sum(e[0] for e in yr.values())), yr


def fmt_years(yr):
    return ";".join(f"{y}:{yr[y][0]:.9f}:{yr[y][1]}" for y in sorted(yr))


def parse_years(s):
    out = {}
    for part in filter(None, s.split(";")):
        y, r, n = part.split(":")
        out[int(y)] = [float(r), int(n)]
    return out


# ---- null runs ----------------------------------------------------------------------------------------------------
FIELDS = ["arm", "pair", "level", "offset", "signals", "halves", "mean", "total", "years"]


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
    base = dict(w["st"], c1=N.shift(w["st"]["c1"], k))
    for arm in ARMS:
        s, p = arm_config(arm, base)
        res = N.run_engine(w["m1"], w["bars"], s, p)
        for lvl in LEVELS:
            n, nh, tot, yr = summarise(w["pair"], res, w["bars"], lvl)
            out.append(dict(arm=arm, pair=w["pair"], level=lvl, offset=k, signals=n, halves=nh,
                            mean=f"{tot / n:.9f}" if n else "nan", total=f"{tot:.9f}", years=fmt_years(yr)))
    return out


def null(pair, src, history, out_path, seconds=150):
    m1, bars, st, offs = load(pair, src, history)
    have = {}
    if os.path.exists(out_path):
        for r in csv.DictReader(open(out_path, encoding="utf-8")):
            have.setdefault((r["pair"], r["offset"]), set()).add((r["arm"], r["level"]))
    full = {(a, l) for a in ARMS for l in LEVELS}
    partial = [k for k, v in have.items() if k[0] == pair and v != full]
    if partial:
        raise SystemExit(f"partial offsets in {out_path}: {partial[:3]}")
    todo = [k for k in offs if (pair, str(k)) not in have]
    if any(k == 0 for k in todo):
        raise SystemExit("offset 0 refused")
    N._W.update(m1=m1, bars=bars, pair=pair, st=st)
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
    print(f"{pair}: {n} new offsets (x 5 arms x 2 levels); left {len(todo) - n}")


# ---- G0 -----------------------------------------------------------------------------------------------------------
def g0_compare(diag_rows, null1_rows):
    """EUR/USD A0 / A4 at x0r vs NULL1 F2 / O2 x0 rows: {arm: (offsets compared, offsets off)}."""
    ref = {}
    for r in null1_rows:
        if r["level"] == "x0" and r["set"] in ("F2", "O2"):
            ref[("A0" if r["set"] == "F2" else "A4", int(r["offset"]))] = r
    out = {}
    for arm in ("A0", "A4"):
        got = {int(r["offset"]): r for r in diag_rows if r["arm"] == arm and r["pair"] == "EURUSD" and r["level"] == "x0r"}
        off = 0
        for k, g in got.items():
            q = ref.get((arm, k))
            if (q is None or int(g["signals"]) != int(q["signals"]) or int(g["halves"]) != int(q["halves"])
                    or abs(float(g["mean"]) - float(q["mean"])) > G0_TOL or abs(float(g["total"]) - float(q["total"])) > G0_TOL):
                off += 1
        out[arm] = (len(got), off)
    return out


def g0(out_path, null1_path):
    res = g0_compare(list(csv.DictReader(open(out_path, encoding="utf-8"))),
                     list(csv.DictReader(open(null1_path, encoding="utf-8"))))
    ok = all(n == 1000 and off == 0 for n, off in res.values())
    for arm, (n, off) in res.items():
        print(f"G0 {arm}: {n} offsets compared, {off} off")
    print("G0 PASS" if ok else "G0 FAIL")
    return ok


# ---- read: calendar-year jackknife (J-a) ----------------------------------------------------------------------------
def blocks(rows, arm, level, pairs=PAIRS):
    """{year: [R, n]} summed over offsets and the given pairs."""
    b = {}
    for r in rows:
        if r["arm"] == arm and r["level"] == level and r["pair"] in pairs:
            for y, (R, n) in parse_years(r["years"]).items():
                e = b.setdefault(y, [0.0, 0])
                e[0] += R
                e[1] += n
    return b


def jackknife(b_a, b_b=None):
    """Estimate (mean of a, or mean a - mean b), delete-one-year jackknife SE, z. Means are total R / total signals."""
    years = sorted(set(b_a) | set(b_b or {}))

    def est(excl=None):
        def m(b):
            R = sum(v[0] for y, v in b.items() if y != excl)
            n = sum(v[1] for y, v in b.items() if y != excl)
            return R / n
        return m(b_a) - (m(b_b) if b_b is not None else 0.0)

    full = est()
    J = len(years)
    loo = np.array([est(y) for y in years])
    se = math.sqrt((J - 1) / J * float(((loo - loo.mean()) ** 2).sum()))
    return full, se, (full / se if se > 0 else float("nan"))


def read(out_path, sha_prefix, report):
    if os.path.exists(report):
        raise SystemExit("refusing to overwrite " + report)
    h = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    if len(sha_prefix) < 16 or not h.startswith(sha_prefix):
        raise SystemExit("sha256 mismatch " + out_path)
    rows = list(csv.DictReader(open(out_path, encoding="utf-8")))
    keys = {(r["arm"], r["pair"], r["level"], r["offset"]) for r in rows}
    if len(keys) != len(rows) or len(rows) != len(ARMS) * len(PAIRS) * len(LEVELS) * 1000:
        raise SystemExit(f"{len(rows)} rows ({len(keys)} unique), {len(ARMS) * len(PAIRS) * len(LEVELS) * 1000} expected")
    o = ["# DIAG1 read 1 — Strategy 2 slot set with random C1, true x0 (decisive) and x0r (information)", "",
         f"Criteria: `docs/preregistration/DIAG1_S2Slots_ZeroCost_Criteria.md` (+ Amendment 1). Rows sha256 `{h}`.", ""]
    for level in LEVELS:
        o += [f"## {level}{' (decisive)' if level == 'x0' else ' (information: spread 0, rollover in)'}", "",
              "| Arm | EUR/USD | AUD/USD | EUR/JPY | Pooled | SE (jackknife) | z | Signals pooled |", "|---|---|---|---|---|---|---|---|"]
        for arm in ARMS:
            per = [blocks(rows, arm, level, (p,)) for p in PAIRS]
            m = [sum(v[0] for v in b.values()) / sum(v[1] for v in b.values()) for b in per]
            pb = blocks(rows, arm, level)
            est, se, z = jackknife(pb)
            o.append(f"| {arm} | {m[0]:+.4f} | {m[1]:+.4f} | {m[2]:+.4f} | {est:+.4f} | {se:.4f} | {z:+.2f} | "
                     f"{sum(v[1] for v in pb.values())} |")
        o += ["", "| Contrast | EUR/USD | AUD/USD | EUR/JPY | Pooled | SE | z |", "|---|---|---|---|---|---|---|"]
        for name, a, b in CONTRASTS:
            per = [jackknife(blocks(rows, a, level, (p,)), blocks(rows, b, level, (p,)))[0] for p in PAIRS]
            est, se, z = jackknife(blocks(rows, a, level), blocks(rows, b, level))
            o.append(f"| {name} | {per[0]:+.4f} | {per[1]:+.4f} | {per[2]:+.4f} | {est:+.4f} | {se:.4f} | {z:+.2f} |")
        o.append("")
    # reading rule (true x0)
    a0p = [blocks(rows, "A0", "x0", (p,)) for p in PAIRS]
    a0m = [sum(v[0] for v in b.values()) / sum(v[1] for v in b.values()) for b in a0p]
    est, se, z = jackknife(blocks(rows, "A0", "x0"))
    slot = est < 0 and z <= -2 and all(m < 0 for m in a0m)
    o += ["## Reading rule (true x0)", "",
          f"- Slot set costs R (pooled A0 < 0, z <= -2, negative on all 3 pairs): **{'MET' if slot else 'not met'}** "
          f"(pooled {est:+.4f}, z {z:+.2f}, per pair {', '.join(f'{m:+.4f}' for m in a0m)})."]
    for name, a, b in CONTRASTS[1:]:
        per = [jackknife(blocks(rows, a, "x0", (p,)), blocks(rows, b, "x0", (p,)))[0] for p in PAIRS]
        e, s_, zz = jackknife(blocks(rows, a, "x0"), blocks(rows, b, "x0"))
        sgn = sum((np.sign(x) == np.sign(e)) for x in per)
        met = zz <= -2 and sgn >= 2
        o.append(f"- {name} costs R (z <= -2 pooled, same sign on >= 2 of 3 pairs): **{'MET' if met else 'not met'}** "
                 f"({e:+.4f}, z {zz:+.2f}, same sign on {sgn} of 3).")
    e4, s4, z4 = jackknife(blocks(rows, "A4", "x0"))
    o += [f"- Sanity A4 (random C1 alone, true x0): {e4:+.4f}, z {z4:+.2f}"
          f"{' — |z| >= 2: flagged (artefact or long / short drift capture, (c))' if abs(z4) >= 2 else ''}.", "",
          "## Rollover contribution (x0r - x0), pooled", "", "| Arm | x0r - x0 |", "|---|---|"]
    for arm in ARMS:
        d, _, _ = jackknife(blocks(rows, arm, "x0r"), blocks(rows, arm, "x0"))
        o.append(f"| {arm} | {d:+.4f} |")
    o += ["", "Limitations (c): circular shifts are correlated draws; ~19 calendar-year blocks; rollover is a 2025-07-28 "
          "snapshot; diagnostic only, nothing is selected from it.", ""]
    with open(report, "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(o))
    print("\n".join(o))


def main(argv):
    if argv[:1] == ["null"] and len(argv) in (5, 6):
        null(*argv[1:5], seconds=int(argv[5]) if len(argv) == 6 else 150)
        return 0
    if argv[:1] == ["g0"] and len(argv) == 3:
        return 0 if g0(*argv[1:]) else 1
    if argv[:1] == ["read"] and len(argv) == 4:
        read(*argv[1:])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
