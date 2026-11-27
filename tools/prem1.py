"""PREM1 (docs/preregistration/PREM1_D1FX_Predictability_Criteria.md): directional predictability at q = 2..60 days in D1 FX.

Usage (repo root):
  python tools/prem1.py k3       <zorro_data_dir> <history_dir>
  python tools/prem1.py null     <zorro_data_dir> <history_dir> <out.csv>          random-sign null, 1,000 draws (decisive)
  python tools/prem1.py stochvol <zorro_data_dir> <history_dir> <out.csv>          stochvol null, 1,000 draws (information)
  python tools/prem1.py pc       <zorro_data_dir> <history_dir> <null.csv> <out.csv>   planted AR(1) / momentum ladders
  python tools/prem1.py read     <zorro_data_dir> <history_dir> <null.csv> <stochvol.csv> <pc.csv> <sha_prefixes> <out.md>
Data: EUR/USD bars from <zorro_data_dir>/TPL_R1d_log_run1.csv (as NULL1); AUD/USD, EUR/JPY from IND_<pair>_log_run1.csv.
The real variance ratios are computed only by `read` (K4).
"""
import csv
import hashlib
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "analysis", "template"))
sys.path.insert(0, os.path.join(ROOT, "analysis", "null_tests", "src"))

PAIRS = ("EURUSD", "AUDUSD", "EURJPY")
QS = (2, 5, 10, 20, 40, 60)
N_NULL = 1000
SEED_NULL = 20261127
SEED_PC = 20261128
SEED_SV = 20261129            # stochvol information row (own stream)
N_PC = 200
LADDER = {"ar1": (0.01, 0.02, 0.03, 0.05), "mom": (0.02, 0.05, 0.10, 0.20)}
LADDER_EXT = {"mom": (0.30, 0.40)}      # Amendment 1 (2026-11-27): kappa ladder missed 90% on the negative side
SEED_PC_EXT = 20261130
MOM_LEN = 20
K3_BARS = {"EURUSD": 5490, "AUDUSD": 5890, "EURJPY": 4346}


# ---- data ---------------------------------------------------------------------------------------------------------
def load_closes(pair, zdata, history):
    if pair == "EURUSD":
        import null1 as N
        _, bars, _ = N.load(zdata, history)
    else:
        import c1s3
        _, bars, _, _ = c1s3.load(pair, os.path.join(zdata, f"IND_{pair}_log_run1.csv"), history)
    return bars


def returns_from(bars):
    c = np.asarray(bars["c"], dtype=float)
    return np.diff(np.log(c))


def load_all(zdata, history):
    out = {}
    for p in PAIRS:
        b = load_closes(p, zdata, history)
        out[p] = dict(bars=b, r=returns_from(b))
    return out


# ---- estimator (criteria "Statistic") -------------------------------------------------------------------------------
def vr(r, q):
    """Overlapping variance ratio with the small-sample correction (binding definition in the criteria file)."""
    r = np.asarray(r, dtype=float)
    n = len(r)
    mu = r.mean()
    sa2 = ((r - mu) ** 2).sum() / (n - 1)
    cs = np.concatenate([[0.0], np.cumsum(r)])
    sums = cs[q:] - cs[:-q]                      # r_t + ... + r_{t-q+1}, t = q..n (n - q + 1 values)
    m = q * (n - q + 1) * (1 - q / n)
    sc2 = ((sums - q * mu) ** 2).sum() / m
    return sc2 / sa2


def vr_all(r, qs=QS):
    return np.array([vr(r, q) for q in qs])


# ---- surrogates ---------------------------------------------------------------------------------------------------
def sign_surrogate(r, rng):
    """r*_t = s_t (r_t - mu), s_t independent fair +-1 (N-a)."""
    r = np.asarray(r, dtype=float)
    s = rng.integers(0, 2, size=len(r)) * 2 - 1
    return s * (r - r.mean())


def stochvol_params(r, rng):
    import surrogates as S
    hv = float(S.dfa_hurst(np.abs(r))[0])
    s, _ = S.calibrate_stochvol_s(r, hv, hv, rng)
    return hv, s


def stochvol_surrogate(r, hv, s, rng):
    import surrogates as S
    p = S.surrogate_stochvol(np.asarray(r, float), 1.0, hv, rng, s=s)
    return np.diff(np.log(p))


def plant_ar1(rs, phi):
    """x_t = phi x_{t-1} + r*_t (x_{-1} = 0); rs may be (n,) or (draws, n): time runs along the last axis."""
    rs = np.asarray(rs, dtype=float)
    x = np.empty_like(rs)
    prev = np.zeros(rs.shape[:-1])
    for t in range(rs.shape[-1]):
        prev = phi * prev + rs[..., t]
        x[..., t] = prev
    return x


def plant_mom(rs, kappa, L=MOM_LEN):
    """x_t = r*_t + kappa * mean(x_{t-1}..x_{t-L}) from t = L on; x_t = r*_t before (criteria PC-a). Last axis = time."""
    rs = np.asarray(rs, dtype=float)
    x = rs.copy()
    run = x[..., :L].sum(axis=-1)
    for t in range(L, rs.shape[-1]):
        x[..., t] = rs[..., t] + kappa * run / L
        run = run + x[..., t] - x[..., t - L]
    return x


def sign_surrogates(r, rng, k):
    """k random-sign surrogates of r as a (k, n) array."""
    r = np.asarray(r, dtype=float)
    s = rng.integers(0, 2, size=(k, len(r))) * 2 - 1
    return s * (r - r.mean())


# ---- pooled test (S-a) --------------------------------------------------------------------------------------------
def pooled_D(vr_pairs):
    """vr_pairs: (..., 3, 6) -> D (..., 6) = mean over pairs of (VR - 1)."""
    return (np.asarray(vr_pairs) - 1.0).mean(axis=-2)


def null_stats(null_vr):
    """null_vr: (draws, 3, 6). Returns mean, sd per q, null M per draw, bar (95th pct)."""
    D = pooled_D(null_vr)
    m, s = D.mean(axis=0), D.std(axis=0, ddof=1)
    M = np.abs((D - m) / s).max(axis=1)
    return m, s, M, float(np.percentile(M, 95))


def flags(vr_pairs, m, s, bar, want_sign=None):
    """Flagged horizons: |z| > bar and the sign of D on >= 2 of 3 pairs (and = want_sign if given). Returns (z, list of q idx)."""
    vr_pairs = np.asarray(vr_pairs)
    D = pooled_D(vr_pairs)
    z = (D - m) / s
    out = []
    for j in range(len(z)):
        if abs(z[j]) <= bar:
            continue
        sg = np.sign(D[j])
        if (np.sign(vr_pairs[:, j] - 1.0) == sg).sum() < 2:
            continue
        if want_sign is not None and sg != want_sign:
            continue
        out.append(j)
    return z, out


# ---- runs ---------------------------------------------------------------------------------------------------------
NULL_FIELDS = ["draw", "pair"] + [f"vr{q}" for q in QS]


def _write_vr_rows(path, rows):
    with open(path, "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(NULL_FIELDS)
        for d, p, v in rows:
            w.writerow([d, p] + [f"{x:.12f}" for x in v])


def run_null(zdata, history, out):
    data = load_all(zdata, history)
    rng = np.random.default_rng(SEED_NULL)
    rows = []
    for d in range(N_NULL):
        for p in PAIRS:
            rows.append((d, p, vr_all(sign_surrogate(data[p]["r"], rng))))
    _write_vr_rows(out, rows)
    print("null rows", len(rows))


def run_stochvol(zdata, history, out):
    data = load_all(zdata, history)
    rng = np.random.default_rng(SEED_SV)
    par = {p: stochvol_params(data[p]["r"], rng) for p in PAIRS}
    print("stochvol params (H_vol, s):", par)
    rows = []
    for d in range(N_NULL):
        for p in PAIRS:
            rows.append((d, p, vr_all(stochvol_surrogate(data[p]["r"], *par[p], rng))))
    _write_vr_rows(out, rows)
    print("stochvol rows", len(rows))


def read_vr(path):
    t = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        t[(int(r["draw"]), r["pair"])] = [float(r[f"vr{q}"]) for q in QS]
    draws = sorted({k[0] for k in t})
    return np.array([[t[(d, p)] for p in PAIRS] for d in draws])      # (draws, 3, 6)


def run_pc(zdata, history, null_path, out, ladder=None, seed=SEED_PC):
    ladder = LADDER if ladder is None else ladder
    data = load_all(zdata, history)
    m, s, _, bar = null_stats(read_vr(null_path))
    rng = np.random.default_rng(seed)
    with open(out, "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "level", "draw", "flagged", "flagged_q"] + [f"D{q}" for q in QS])
        for kind, levels in ladder.items():
            for lv in levels:
                for sign in (1, -1):
                    par = sign * lv
                    vrs = np.empty((N_PC, len(PAIRS), len(QS)))
                    for i, p in enumerate(PAIRS):
                        rs = sign_surrogates(data[p]["r"], rng, N_PC)
                        x = plant_ar1(rs, par) if kind == "ar1" else plant_mom(rs, par)
                        for d in range(N_PC):
                            vrs[d, i] = vr_all(x[d])
                    for d in range(N_PC):
                        _, fl = flags(vrs[d], m, s, bar, want_sign=sign)
                        w.writerow([kind, f"{par:+.2f}", d, int(bool(fl)), ";".join(str(QS[j]) for j in fl)]
                                   + [f"{v:.9f}" for v in pooled_D(vrs[d])])
                print(kind, lv, "done", flush=True)


def k3(zdata, history):
    data = load_all(zdata, history)
    ok = True
    for p in PAIRS:
        b = data[p]["bars"]
        n = len(b["c"])
        days = b["day"]
        import r1_data as D
        print(p, "bars", n, "expected", K3_BARS[p], "first", D.ymd_int(days[0]), "last", D.ymd_int(days[-1]),
              "zero returns", int((data[p]["r"] == 0).sum()))
        ok &= n == K3_BARS[p]
    print("K3 PASS" if ok else "K3 FAIL")
    return ok


# ---- read ---------------------------------------------------------------------------------------------------------
def detection_table(pc_rows):
    """{(kind, level): rate} for signed levels."""
    acc = {}
    for r in pc_rows:
        k = (r["kind"], float(r["level"]))
        acc.setdefault(k, []).append(int(r["flagged"]))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def levels_of(rates, kind):
    return sorted({abs(k[1]) for k in rates if k[0] == kind})


def bound(rates, kind, thr=0.9, signs=(1, -1)):
    """Smallest |level| caught >= thr for every sign in `signs` (default both: the pre-registered bound), or None.
    Levels come from the rates themselves (base ladder + Amendment 1 extension)."""
    for lv in levels_of(rates, kind):
        if all(rates.get((kind, sg * lv), 0) >= thr for sg in signs):
            return lv
    return None


def read(zdata, history, null_path, sv_path, pc_path, shas, out):
    """pc_path: one file or several joined by '+' (Amendment 1: base + extension); shas: one prefix per file, ','."""
    if os.path.exists(out):
        raise SystemExit("refusing to overwrite " + out)
    pre = shas.split(",")
    pcs = pc_path.split("+")
    files = [null_path, sv_path] + pcs
    if len(pre) != len(files):
        raise SystemExit(f"{len(files)} files, {len(pre)} sha prefixes")
    for path, sp in zip(files, pre):
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if len(sp) < 16 or not h.startswith(sp):
            raise SystemExit("sha256 mismatch " + path)
    nv, sv = read_vr(null_path), read_vr(sv_path)
    m, s, Mn, bar = null_stats(nv)
    ms, ss, Ms, bars_sv = null_stats(sv)
    rows = [r for p in pcs for r in csv.DictReader(open(p, encoding="utf-8"))]
    rates = detection_table(rows)
    data = load_all(zdata, history)
    real = np.array([vr_all(data[p]["r"]) for p in PAIRS])                 # the real VRs: computed here only (K4)
    z, fl = flags(real, m, s, bar)
    zs, fls = flags(real, ms, ss, bars_sv)
    Dr = pooled_D(real)
    Dn = pooled_D(nv)
    o = ["# PREM1 read 1 — directional predictability at 2-60 days, D1 FX (EUR/USD, AUD/USD, EUR/JPY)", "",
         "Criteria: `docs/preregistration/PREM1_D1FX_Predictability_Criteria.md`.", "",
         f"**Random-sign null (decisive):** bar (95th pct of max|z|) **{bar:.3f}**; pooled null sd of VR(2) - 1 "
         f"{s[0]:.4f}. Real M = **{np.abs(z).max():.3f}**. Flagged horizons: **{', '.join(str(QS[j]) for j in fl) or 'none'}**.", "",
         "| q | VR EUR/USD | VR AUD/USD | VR EUR/JPY | pooled D | null 5th / 50th / 95th | pct | z |",
         "|---|---|---|---|---|---|---|---|"]
    for j, q in enumerate(QS):
        lo, md, hi = np.percentile(Dn[:, j], [5, 50, 95])
        o.append(f"| {q} | {real[0, j]:.4f} | {real[1, j]:.4f} | {real[2, j]:.4f} | {Dr[j]:+.4f} | {lo:+.4f} / {md:+.4f} / "
                 f"{hi:+.4f} | {100 * np.mean(Dn[:, j] <= Dr[j]):.1f}% | {z[j]:+.2f} |")
    o += ["", f"**Stochvol null (information):** bar {bars_sv:.3f}; real M {np.abs(zs).max():.3f}; flagged: "
          f"{', '.join(str(QS[j]) for j in fls) or 'none'}.", "",
          "**Positive control (detection rate, flagged with the planted sign):**", "",
          "| kind | level | rate (+) | rate (-) |", "|---|---|---|---|"]
    for kind in LADDER:
        for lv in levels_of(rates, kind):
            o.append(f"| {kind} | {lv:.2f} | {rates.get((kind, lv), float('nan')):.3f} | {rates.get((kind, -lv), float('nan')):.3f} |")
    o += ["", f"**Detection bounds (>= 90%, both signs):** AR(1) phi = {bound(rates, 'ar1')}, momentum kappa = "
          f"{bound(rates, 'mom')} (pre-registered rule). Information (Amendment 1): sign-specific kappa_90 trend side (+) "
          f"{bound(rates, 'mom', signs=(1,))}, reversal side (-) {bound(rates, 'mom', signs=(-1,))}; phi_90 (+) "
          f"{bound(rates, 'ar1', signs=(1,))}, (-) {bound(rates, 'ar1', signs=(-1,))}.", "",
          "Limitations (c): one history per pair; equal-weight pooling; the random-sign null assumes sign symmetry; slow momentum "
          "below the kappa bound is invisible to this test.", ""]
    with open(out, "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(o))
    print("\n".join(o))


def main(argv):
    cmd = argv[:1]
    if cmd == ["k3"] and len(argv) == 3:
        return 0 if k3(*argv[1:]) else 1
    if cmd == ["null"] and len(argv) == 4:
        run_null(*argv[1:]); return 0
    if cmd == ["stochvol"] and len(argv) == 4:
        run_stochvol(*argv[1:]); return 0
    if cmd == ["pc"] and len(argv) == 5:
        run_pc(*argv[1:]); return 0
    if cmd == ["pc-ext"] and len(argv) == 5:
        run_pc(*argv[1:], ladder=LADDER_EXT, seed=SEED_PC_EXT); return 0
    if cmd == ["read"] and len(argv) == 8:
        read(*argv[1:]); return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
