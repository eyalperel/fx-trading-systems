"""PREM2 (docs/preregistration/PREM2_BTCH4_Predictability_Criteria.md): directional predictability at q = 2..360 H4 bars, BTCUSDT.

Usage (repo root):
  python tools/prem2.py k3       <zip_dir>
  python tools/prem2.py null     <zip_dir> <out.csv>                    random-sign null, 1,000 draws (decisive)
  python tools/prem2.py stochvol <zip_dir> <out.csv>                    stochvol null, 1,000 draws (information)
  python tools/prem2.py pc       <zip_dir> <null.csv> <out.csv>         planted AR(1) / momentum L20 / L120 ladders
  python tools/prem2.py pc-ext   <zip_dir> <null.csv> <out.csv>         ladder extension (only after an amendment)
  python tools/prem2.py read     <zip_dir> <null.csv> <stochvol.csv> <pc.csv[+pc_ext.csv]> <sha_prefixes> <out.md>
<zip_dir>: data/crypto/binance_btcusdt_4h (Binance monthly BTCUSDT-4h-YYYY-MM.zip, CHECKSUM-verified).
Estimator, surrogates and planting are tools/prem1.py's (unchanged). The real variance ratios are computed only by `read` (K4).
"""
import csv
import datetime as dt
import glob
import hashlib
import os
import sys
import zipfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prem1 as P1  # noqa: E402  (vr, sign_surrogate(s), stochvol_*, plant_ar1, plant_mom)

QS = (2, 5, 10, 20, 40, 60, 120, 240, 360)                  # H-c
PARTS = ("all", "t1", "t2", "t3")                           # full series + thirds (S-2)
N_NULL = 1000
N_PC = 200
SEED_NULL = 20261201
SEED_PC = 20261202
SEED_SV = 20261203
SEED_PC_EXT = 20261204
LADDER = {"ar1": (0.02, 0.03, 0.05, 0.08),
          "mom20": (0.05, 0.10, 0.20, 0.30, 0.40),
          "mom120": (0.10, 0.20, 0.30, 0.40, 0.60)}
LADDER_EXT = {}                                             # filled only by a dated amendment, before the read
MOM_L = {"mom20": 20, "mom120": 120}
BAR_S = 4 * 3600

# K3 expectations (docs/research/Data_BTCUSDT_H4_Binance.md)
K3_BARS = 20160
K3_FIRST = "2017-08-17 04:00"
K3_LAST = "2026-10-31 20:00"
K3_UNITS = (16146, 4014)                                    # (ms, us) bars
K3_GAPS = ("2017-09-06 12:00", "2018-02-08 00:00", "2018-06-26 00:00", "2018-07-04 00:00", "2018-11-14 00:00",
           "2019-03-12 00:00", "2019-05-15 00:00", "2019-08-15 00:00", "2020-02-19 08:00")
K3_GAP_HOURS = (8, 32, 12, 8, 8, 8, 12, 8, 8)
K3_MISSING = 17


def utc(sec):
    return dt.datetime.fromtimestamp(int(sec), dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


# ---- data (G-a) ---------------------------------------------------------------------------------------------------
def load_bars(zip_dir):
    """Open times (s, UTC) and closes from every monthly zip, in file order. us timestamps (>= 1e14) -> s, ms -> s."""
    files = sorted(glob.glob(os.path.join(zip_dir, "BTCUSDT-4h-*.zip")))
    if not files:
        raise SystemExit("no BTCUSDT-4h-*.zip in " + zip_dir)
    t, c, units = [], [], [0, 0]
    for f in files:
        with zipfile.ZipFile(f) as z:
            for nm in z.namelist():
                for line in z.read(nm).decode().splitlines():
                    p = line.split(",")
                    ot = int(p[0])
                    if ot >= 10 ** 14:
                        units[1] += 1
                        ot //= 1000
                    else:
                        units[0] += 1
                    t.append(ot // 1000)
                    c.append(float(p[4]))
    t = np.array(t, dtype=np.int64)
    if np.any(np.diff(t) <= 0) or np.any(t % BAR_S):
        raise SystemExit("bars not strictly increasing on the 4h UTC grid")
    return dict(t=t, c=np.array(c), units=tuple(units), files=len(files))


def returns_from(bars):
    """Close to close; a gap-spanning return stays one return (G-a)."""
    return np.diff(np.log(bars["c"]))


def gaps(bars):
    """Indices i of returns r_i spanning more than one bar (t[i+1] - t[i] > 4h)."""
    return np.where(np.diff(bars["t"]) > BAR_S)[0]


def third_bounds(n):
    """Start / end indices of the three consecutive parts: base n // 3, remainder one each to the last parts."""
    sizes = [n // 3] * 3
    for i in range(n % 3):
        sizes[2 - i] += 1
    e = np.cumsum(sizes)
    return [(0, int(e[0])), (int(e[0]), int(e[1])), (int(e[1]), int(e[2]))]


# ---- statistic (S-2) ----------------------------------------------------------------------------------------------
def vr_parts(r, qs=QS):
    """(4, len(qs)): VR(q) on the full series, then on each third alone (same estimator)."""
    r = np.asarray(r, dtype=float)
    out = [[P1.vr(r, q) for q in qs]]
    for a, b in third_bounds(len(r)):
        out.append([P1.vr(r[a:b], q) for q in qs])
    return np.array(out)


def null_stats(null_v):
    """null_v: (draws, 4, nq). Standardisation and bar from the full-series row only."""
    V = np.asarray(null_v)[:, 0, :]
    m, s = V.mean(axis=0), V.std(axis=0, ddof=1)
    M = np.abs((V - m) / s).max(axis=1)
    return m, s, M, float(np.percentile(M, 95))


def flags(v4, m, s, bar, want_sign=None):
    """v4: (4, nq). Flag q: |z| > bar and sign(VR_k - 1) = sign(VR - 1) in >= 2 of 3 thirds (and = want_sign if given).
    Returns (z, flagged idx, episode idx = |z| > bar but the thirds rule fails)."""
    v4 = np.asarray(v4)
    z = (v4[0] - m) / s
    fl, ep = [], []
    for j in range(len(z)):
        if abs(z[j]) <= bar:
            continue
        sg = np.sign(v4[0, j] - 1.0)
        if sg == 0 or (np.sign(v4[1:, j] - 1.0) == sg).sum() < 2:
            ep.append(j)
            continue
        if want_sign is not None and sg != want_sign:
            continue
        fl.append(j)
    return z, fl, ep


# ---- runs ---------------------------------------------------------------------------------------------------------
FIELDS = ["draw", "part"] + [f"vr{q}" for q in QS]


def _write_parts(w, d, v4):
    for k, part in enumerate(PARTS):
        w.writerow([d, part] + [f"{x:.12f}" for x in v4[k]])


def run_null(zip_dir, out):
    r = returns_from(load_bars(zip_dir))
    rng = np.random.default_rng(SEED_NULL)
    with open(out, "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        for d in range(N_NULL):
            _write_parts(w, d, vr_parts(P1.sign_surrogate(r, rng)))
    print("null draws", N_NULL)


def run_stochvol(zip_dir, out):
    r = returns_from(load_bars(zip_dir))
    rng = np.random.default_rng(SEED_SV)
    hv, s = P1.stochvol_params(r, rng)
    print(f"stochvol params H_vol {hv:.3f} s {s}")
    with open(out, "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        for d in range(N_NULL):
            _write_parts(w, d, vr_parts(P1.stochvol_surrogate(r, hv, s, rng)))
    print("stochvol draws", N_NULL)


def read_parts(path):
    t = {}
    for row in csv.DictReader(open(path, encoding="utf-8")):
        t[(int(row["draw"]), row["part"])] = [float(row[f"vr{q}"]) for q in QS]
    draws = sorted({k[0] for k in t})
    return np.array([[t[(d, p)] for p in PARTS] for d in draws])     # (draws, 4, nq)


def plant(kind, rs, par):
    return P1.plant_ar1(rs, par) if kind == "ar1" else P1.plant_mom(rs, par, L=MOM_L[kind])


def run_pc(zip_dir, null_path, out, ladder=None, seed=SEED_PC):
    ladder = LADDER if ladder is None else ladder
    r = returns_from(load_bars(zip_dir))
    m, s, _, bar = null_stats(read_parts(null_path))
    rng = np.random.default_rng(seed)
    with open(out, "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "level", "draw", "flagged", "flagged_q", "episode_q"] + [f"vr{q}" for q in QS])
        for kind, levels in ladder.items():
            for lv in levels:
                for sign in (1, -1):
                    par = sign * lv
                    x = plant(kind, P1.sign_surrogates(r, rng, N_PC), par)
                    for d in range(N_PC):
                        v4 = vr_parts(x[d])
                        _, fl, ep = flags(v4, m, s, bar, want_sign=sign)
                        w.writerow([kind, f"{par:+.2f}", d, int(bool(fl)), ";".join(str(QS[j]) for j in fl),
                                    ";".join(str(QS[j]) for j in ep)] + [f"{v:.9f}" for v in v4[0]])
                print(kind, lv, "done", flush=True)


def k3(zip_dir):
    b = load_bars(zip_dir)
    r = returns_from(b)
    g = gaps(b)
    gl = tuple(utc(b["t"][i]) for i in g)
    n = len(b["t"])
    tb = third_bounds(len(r))
    print("files", b["files"], "bars", n, "first", utc(b["t"][0]), "last", utc(b["t"][-1]), "units (ms, us)", b["units"])
    print("gaps", len(g), "missing bars", int(((np.diff(b["t"])[g] // BAR_S) - 1).sum()))
    for i in g:
        print("  gap", utc(b["t"][i]), f"{(b['t'][i + 1] - b['t'][i]) // 3600}h r {r[i]:+.4f}")
    print("returns", len(r), "thirds", [hi - lo for lo, hi in tb],
          "third starts (bar close of first return)", [utc(b["t"][lo + 1]) for lo, _ in tb])
    gh = tuple(int((b["t"][i + 1] - b["t"][i]) // 3600) for i in g)
    miss = int(((np.diff(b["t"])[g] // BAR_S) - 1).sum())
    ok = k3_check(dict(bars=n, first=utc(b["t"][0]), last=utc(b["t"][-1]), units=b["units"], gaps=gl, gap_hours=gh,
                       missing=miss))
    print("K3 PASS" if ok else "K3 FAIL")
    return ok


def k3_check(sm):
    """K3 pass condition: every item equals the data record (docs/research/Data_BTCUSDT_H4_Binance.md)."""
    return (sm["bars"] == K3_BARS and sm["first"] == K3_FIRST and sm["last"] == K3_LAST and sm["units"] == K3_UNITS
            and sm["gaps"] == K3_GAPS and sm["gap_hours"] == K3_GAP_HOURS and sm["missing"] == K3_MISSING)


# ---- read ---------------------------------------------------------------------------------------------------------
def detection_table(pc_rows):
    acc = {}
    for row in pc_rows:
        acc.setdefault((row["kind"], float(row["level"])), []).append(int(row["flagged"]))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def levels_of(rates, kind):
    return sorted({abs(k[1]) for k in rates if k[0] == kind})


def bound(rates, kind, thr=0.9, signs=(1, -1)):
    """Smallest |level| caught >= thr for every sign in `signs` (default both: the pre-registered bound), or None."""
    for lv in levels_of(rates, kind):
        if all(rates.get((kind, sg * lv), 0) >= thr for sg in signs):
            return lv
    return None


def median_vr(pc_rows, kind, level):
    v = [[float(row[f"vr{q}"]) for q in QS] for row in pc_rows if row["kind"] == kind and float(row["level"]) == level]
    return np.median(np.array(v), axis=0) if v else None


def read(zip_dir, null_path, sv_path, pc_path, shas, out):
    if os.path.exists(out):
        raise SystemExit("refusing to overwrite " + out)
    pre, pcs = shas.split(","), pc_path.split("+")
    files = [null_path, sv_path] + pcs
    if len(pre) != len(files):
        raise SystemExit(f"{len(files)} files, {len(pre)} sha prefixes")
    for path, sp in zip(files, pre):
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if len(sp) < 16 or not h.startswith(sp):
            raise SystemExit("sha256 mismatch " + path)
    nv, sv = read_parts(null_path), read_parts(sv_path)
    m, s, _, bar = null_stats(nv)
    ms, ss, _, bar_sv = null_stats(sv)
    rows = [row for p in pcs for row in csv.DictReader(open(p, encoding="utf-8"))]
    rates = detection_table(rows)
    b = load_bars(zip_dir)
    r = returns_from(b)
    real = vr_parts(r)                                                    # the real VRs: computed here only (K4)
    z, fl, ep = flags(real, m, s, bar)
    zs, fls, eps = flags(real, ms, ss, bar_sv)
    tb = third_bounds(len(r))
    names = lambda idx: ", ".join(str(QS[j]) for j in idx) or "none"     # noqa: E731
    o = ["# PREM2 read 1 — directional predictability at 2-360 H4 bars, Binance BTCUSDT 4h", "",
         "Criteria: `docs/preregistration/PREM2_BTCH4_Predictability_Criteria.md`.", "",
         f"Returns {len(r)}; thirds {[hi - lo for lo, hi in tb]} starting {[utc(b['t'][lo + 1]) for lo, _ in tb]} (UTC bar open of "
         "the first return's close bar).", "",
         f"**Random-sign null (decisive):** bar (95th pct of max|z|) **{bar:.3f}**; null sd of VR(2) - 1 {s[0]:.4f}. "
         f"Real M = **{np.abs(z).max():.3f}**. Flagged horizons: **{names(fl)}**; episode-driven (|z| > bar, thirds rule "
         f"fails): **{names(ep)}**.", "",
         "| q | VR | null 5th / 50th / 95th | pct | z | VR third 1 | third 2 | third 3 |",
         "|---|---|---|---|---|---|---|---|"]
    for j, q in enumerate(QS):
        col = nv[:, 0, j]
        lo, md, hi = np.percentile(col, [5, 50, 95])
        o.append(f"| {q} | {real[0, j]:.4f} | {lo:.4f} / {md:.4f} / {hi:.4f} | {100 * np.mean(col <= real[0, j]):.1f}% | "
                 f"{z[j]:+.2f} | {real[1, j]:.4f} | {real[2, j]:.4f} | {real[3, j]:.4f} |")
    o += ["", f"**Stochvol null (information):** bar {bar_sv:.3f}; real M {np.abs(zs).max():.3f}; flagged: {names(fls)}; "
          f"episode-driven: {names(eps)}.", "",
          "**Positive control (detection rate, flagged with the planted sign):**", "",
          "| kind | level | rate (+) | rate (-) | median VR(q) (+), q = " + " / ".join(map(str, QS)) + " |",
          "|---|---|---|---|---|"]
    kinds = list(LADDER) + [k for k in LADDER_EXT if k not in LADDER]
    for kind in kinds:
        for lv in levels_of(rates, kind):
            mv = median_vr(rows, kind, lv)
            o.append(f"| {kind} | {lv:.2f} | {rates.get((kind, lv), float('nan')):.3f} | "
                     f"{rates.get((kind, -lv), float('nan')):.3f} | " + " / ".join(f"{x:.3f}" for x in mv) + " |")
    o += ["", "**Detection bounds (>= 90%, both signs; pre-registered rule):** "
          + "; ".join(f"{k} {bound(rates, k)}" for k in kinds)
          + ". Information, trend side (+): " + "; ".join(f"{k} {bound(rates, k, signs=(1,))}" for k in kinds)
          + "; reversal side (-): " + "; ".join(f"{k} {bound(rates, k, signs=(-1,))}" for k in kinds) + ".", "",
          "Limitations (c): one history; the random-sign null assumes sign symmetry; quote USDT not USD; memory below the "
          "bounds is invisible to this test.", ""]
    with open(out, "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(o))
    print("\n".join(o))


def main(argv):
    cmd = argv[:1]
    if cmd == ["k3"] and len(argv) == 2:
        return 0 if k3(argv[1]) else 1
    if cmd == ["null"] and len(argv) == 3:
        run_null(*argv[1:]); return 0
    if cmd == ["stochvol"] and len(argv) == 3:
        run_stochvol(*argv[1:]); return 0
    if cmd == ["pc"] and len(argv) == 4:
        run_pc(*argv[1:]); return 0
    if cmd == ["pc-ext"] and len(argv) == 4:
        if not LADDER_EXT:
            raise SystemExit("no ladder extension registered (amendment first)")
        run_pc(*argv[1:], ladder=LADDER_EXT, seed=SEED_PC_EXT); return 0
    if cmd == ["read"] and len(argv) == 7:
        read(*argv[1:]); return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
