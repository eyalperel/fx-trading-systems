"""Planning-chat numbers for the MAF stage 1 prompt (full precision). Uses MAMA_FRAMA_REVIEW_MODEL.py.
Corrected models = source models with exact constants and exact pi (S1). FRAMA on point bars (H = L = x) and band bars
(H = x + h, L = x - h, h = 0.002). Copies for equivariance: sc = 10 x - 9.9 (amp 0.1), of = x + 1.1 (level 2.2); band scaled with x.
All rows unless stated. Seeds fixed."""
import math
import numpy as np
from MAMA_FRAMA_REVIEW_MODEL import inputs, mama_src, mama_code, frama_src, frama_code, f32, NB

X = inputs()
H0 = 0.002
rng = np.random.default_rng(20261120)
MA = {"MA05": (0.5, 0.05), "MA03": (0.3, 0.1)}
FR = {"FR16": 16, "FR32": 32}
CM = ("mama", "fama", "alpha", "period", "phase")
CF = ("out", "dim", "alpha")
F32 = {k: f32(float(k)) for k in (".0962", ".5769", ".075", ".54", ".2", ".8", ".33", ".67")}


def mx(a, b, r0=0):
    return float(np.max(np.abs(np.asarray(a)[r0:] - np.asarray(b)[r0:])))


def band(x, k=1.0):
    return x + k * H0, x - k * H0


def fr(x, N, b=False, **kw):
    if b:
        H, L = band(x)
        return frama_src(x, N, H=H, Lo=L, **kw)
    return frama_src(x, N, **kw)


def cond(fn, x, cols, n=5):
    base = fn(x); out = {c: 0.0 for c in cols}
    for _ in range(n):
        p = fn(x * (1 + 2.0 ** -52 * rng.integers(-1, 2, NB)))
        for c in cols: out[c] = max(out[c], mx(p[c], base[c]))
    return out


print("== 1. MAMA conditioning (rule 3), per column, all rows, 5 perturbations; tol/10: 1e-10 (mama, fama, alpha, period), 1e-9 (phase) ==")
LIM = {"mama": 1e-10, "fama": 1e-10, "alpha": 1e-10, "period": 1e-10, "phase": 1e-9}
for v, (FL, SL) in MA.items():
    for k, x in X.items():
        c = cond(lambda y: mama_src(y, FL, SL), x, CM)
        ok = all(c[q] <= LIM[q] for q in CM)
        print(f"  {v} {k:5s} {'CHECKED' if ok else 'INFO   '} " + " ".join(f"{q} {c[q]:.3e}" for q in CM))

print("\n== 2. MAMA facts (corrected model), all rows ==")
for v, (FL, SL) in MA.items():
    for k in ("s10", "s20", "s40", "s100"):
        s = mama_src(X[k], FL, SL)
        a = s["alpha"][5:]; p = s["period"]
        print(f"  {v} {k:5s} alpha [{a.min()!r}, {a.max()!r}] period max {p.max()!r} period rows>=1000 [{p[1000:].min()!r}, {p[1000:].max()!r}] "
              f"FAMA rows>=1000 [{s['fama'][1000:].min()!r}, {s['fama'][1000:].max()!r}]")
    # equivariance, s40
    x = X["s40"]; s = mama_src(x, FL, SL); sc = mama_src(10 * x - 9.9, FL, SL); of = mama_src(x + 1.1, FL, SL)
    print(f"  {v} equivariance s40: sc mama {mx(sc['mama'], 10*s['mama']-9.9):.3e} fama {mx(sc['fama'], 10*s['fama']-9.9):.3e} alpha {mx(sc['alpha'], s['alpha']):.3e} | "
          f"of mama {mx(of['mama'], s['mama']+1.1):.3e} fama {mx(of['fama'], s['fama']+1.1):.3e} alpha {mx(of['alpha'], s['alpha']):.3e}")
    # IMP residual estimate: replay the %.15f-rounded x
    for k in ("s10", "s20", "s40", "s100"):
        x = X[k]; s = mama_src(x, FL, SL); r = mama_src(np.array([float(f"{t:.15f}") for t in x]), FL, SL)
        print(f"  {v} {k:5s} IMP(%.15f x) " + " ".join(f"{q} {mx(r[q], s[q]):.3e}" for q in CM))

print("\n== 3. MAMA control effects vs the real model, checked inputs, all rows, per column ==")
CTRL = {"NCH every .0962 -> .0963": dict(lit={".0962": 0.0963}), "NCF FAMA .5 -> .51": dict(fama_k=0.51),
        "NC32 float32 literals (exact pi)": dict(lit=F32), "NCP Zorro PI (float32 3.14159)": dict(pi=f32(3.14159)),
        "NCB(info) .67 -> .68": dict(lit={".67": 0.68})}
for v, (FL, SL) in MA.items():
    for name, kw in CTRL.items():
        for k in ("s10", "s20", "s40", "s100"):
            a = mama_src(X[k], FL, SL, **kw); b = mama_src(X[k], FL, SL)
            print(f"  {v} {name:34s} {k:5s} " + " ".join(f"{q} {mx(a[q], b[q]):.6e}" for q in CM))
    for k in ("s10", "s20", "s40", "s100"):
        a = mama_code(X[k], FL, SL, pi=f32(3.14159)); b = mama_src(X[k], FL, SL)
        print(f"  {v} {'NCS-single (old file, one instance)':34s} {k:5s} " + " ".join(f"{q} {mx(a[q], b[q]):.6e}" for q in ("mama", "fama", "alpha", "period")))

print("\n== 4. FRAMA conditioning (rule 3), all rows; tol/10 = 1e-11 ==")
for v, N in FR.items():
    for b in (False, True):
        for k, x in X.items():
            if b and k == "flat": continue
            c = cond(lambda y: fr(y, N, b), x, CF)
            print(f"  {v} {k + ('B' if b else ''):6s} " + " ".join(f"{q} {c[q]:.3e}{'' if c[q] <= 1e-11 else ' INFO'}" for q in CF))

print("\n== 5. FRAMA known answers and facts ==")
for v, N in FR.items():
    s = fr(X["ramp"], N)
    print(f"  {v} point ramp: max |out - x| rows >= {N}: {mx(s['out'], X['ramp'], N):.3e}; dim {s['dim'][500]!r} = log2(4(N/2-1)/(N-1)) = {math.log2(4*(N/2-1)/(N-1))!r}")
    s = fr(X["ramp"], N, True)
    r1 = 1e-4 * (N / 2 - 1) + 2 * H0; r3 = 1e-4 * (N - 1) + 2 * H0
    D = math.log2(4 * r1 / r3); a = math.exp(-4.6 * (D - 1)); lag = (1 - a) / a
    meas = np.mean((X["ramp"] - s["out"])[-100:]) / 1e-4
    last = np.nonzero(np.abs((X['ramp'] - s['out']) / 1e-4 - lag) > 1e-9)[0]
    print(f"  {v} band ramp: D = log2(4 r1/r3) = {D!r} (model {s['dim'][2000]!r}); alpha {a!r}; lag (1-a)/a = {lag!r}; "
          f"measured (last 100 rows) {meas!r}; last row |lag_n - lag| > 1e-9: {last[-1] if len(last) else None}")
    for b in (False, True):
        for k in ("s5", "s10", "s20", "s40", "s100"):
            s = fr(X[k], N, b)
            print(f"  {v} {k + ('B' if b else ''):5s} alpha [{s['alpha'].min()!r}, {s['alpha'].max()!r}] dim max {s['dim'].max()!r} out rows>=200 [{s['out'][200:].min():.9f}, {s['out'][200:].max():.9f}]")
    x = X["s40"]; Hb, Lb = band(x); s = frama_src(x, N, H=Hb, Lo=Lb)
    sc = frama_src(10 * x - 9.9, N, H=10 * Hb - 9.9, Lo=10 * Lb - 9.9); of = frama_src(x + 1.1, N, H=Hb + 1.1, Lo=Lb + 1.1)
    print(f"  {v} equivariance s40B: sc out {mx(sc['out'], 10*s['out']-9.9):.3e} dim {mx(sc['dim'], s['dim']):.3e} alpha {mx(sc['alpha'], s['alpha']):.3e} | "
          f"of out {mx(of['out'], s['out']+1.1):.3e} dim {mx(of['dim'], s['dim']):.3e} alpha {mx(of['alpha'], s['alpha']):.3e}")
    for k in ("s20", "s100"):
        for b in (False, True):
            x = X[k]; s = fr(x, N, b); xr = np.array([float(f"{t:.15f}") for t in x])
            r = fr(xr, N, b) if not b else frama_src(xr, N, H=np.array([float(f'{t:.15f}') for t in band(x)[0]]), Lo=np.array([float(f'{t:.15f}') for t in band(x)[1]]))
            print(f"  {v} {k + ('B' if b else ''):5s} IMP(%.15f x, H, L) " + " ".join(f"{q} {mx(r[q], s[q]):.3e}" for q in CF))

print("\n== 6. FRAMA control effects vs the real model, all rows, per column (point | band) ==")
FC = {"NCE 4.6 -> 4.61": lambda x, N, b: fr(x, N, b, k46=4.61), "NCN window N + 2": lambda x, N, b: fr(x, N + 2, b),
      "NC32 float32 4.6 / .01": lambda x, N, b: fr(x, N, b, k46=f32(4.6), k01=f32(0.01))}
for v, N in FR.items():
    for name, fn in FC.items():
        for k in ("ramp", "s5", "s10", "s20", "s40", "s100"):
            a = fn(X[k], N, False); b0 = fr(X[k], N); ab = fn(X[k], N, True); bb = fr(X[k], N, True)
            print(f"  {v} {name:24s} {k:5s} " + " ".join(f"{q} {mx(a[q], b0[q]):.6e}" for q in CF) + " | " + " ".join(f"{q} {mx(ab[q], bb[q]):.6e}" for q in CF))
    # NCT: old start-up only (seed on first call, EMA from the second call, padded windows), corrected elsewhere
    for k in ("ramp", "s5", "s10", "s20", "s40", "s100"):
        for b in (False, True):
            H, L = band(X[k]) if b else (X[k], X[k])
            o = frama_code(X[k], N // 2, k46=4.6, k01=0.01, H=H, Lo=L)["out"]; s = fr(X[k], N, b)
            print(f"  {v} {'NCT old start-up+guard':24s} {k + ('B' if b else ''):5s} out {mx(o, s['out']):.6e}")
