"""MAMA/FAMA + FRAMA source-review model (float64, independent of harness tooling).

Sources (a):
  MAMA: Ehlers, TASC V.19:9 (2001), Sidebar Fig. 1 (EasyLanguage), PDF p. 5.
  FRAMA: Ehlers, TASC V.23:10 (2005), "FRAMA EasyLanguage code" sidebar, PDF p. 3.
Models:
  mama_src   - the sidebar: vars start 0, body only if CurrentBar > 5, a var not
               assigned on a bar HOLDS its previous value (EasyLanguage semantics).
  mama_code  - indicators/ehlers/MAMA.c as written: series() defaults re-set every
               bar (Period 20, Phase 0), series padded with first value, price seeds,
               first 5 calls return Price; optional float32 literals; optional PI.
  frama_src  - the sidebar with H = L = x (synthetic close-only bars), N = full window.
  frama_code - indicators/ehlers/FRAMA.c (T = half window; seed on first call; hold when N3 <= 0).
Inputs as earlier reviews: level 1.1, sine amplitude 0.01, ramp slope 1e-4, 3000 bars.
"""
import math
import numpy as np

f32 = lambda v: float(np.float32(v))
NB = 3000


def inputs():
    n = np.arange(NB)
    d = {"flat": np.full(NB, 1.1), "ramp": 1.1 + 1e-4 * n}
    for T in (5, 10, 20, 40, 100):
        d[f"s{T}"] = 1.1 + 0.01 * np.sin(2 * math.pi * n / T)
    return d


def get(a, i, k, pad):
    j = i - k
    return a[j] if j >= 0 else pad


def mama_src(x, FL=0.5, SL=0.05, lit=None, pi=math.pi, period0=0.0):
    c = lit or {}
    L = lambda s: c.get(s, float(s))
    w1, w2, kA, kB = L(".0962"), L(".5769"), L(".075"), L(".54")
    a2, a8, a33, a67, k15, k67 = L(".2"), L(".8"), L(".33"), L(".67"), L("1.5"), L(".67")
    n = len(x)
    S, De, I1, Q1, jI, jQ, I2, Q2, Re, Im, P, Ph, M, F, AL = (np.zeros(n) for _ in range(15))
    P0 = period0
    for i in range(n):
        cb = i + 1
        # hold: every var starts the bar at its previous value
        for arr, init in ((S, 0), (De, 0), (I1, 0), (Q1, 0), (jI, 0), (jQ, 0), (I2, 0), (Q2, 0),
                          (Re, 0), (Im, 0), (P, P0), (Ph, 0), (M, 0), (F, 0)):
            arr[i] = arr[i - 1] if i > 0 else init
        if cb <= 5:
            continue
        g = lambda a, k, pad=0.0: get(a, i, k, pad)
        S[i] = (4 * x[i] + 3 * g(x, 1) + 2 * g(x, 2) + g(x, 3)) / 10
        pf = kA * g(P, 1, P0) + kB
        ht = lambda a: (w1 * a[i] + w2 * g(a, 2) - w2 * g(a, 4) - w1 * g(a, 6)) * pf
        De[i] = ht(S)
        Q1[i] = ht(De)
        I1[i] = g(De, 3)
        jI[i] = ht(I1)
        jQ[i] = ht(Q1)
        I2[i] = I1[i] - jQ[i]
        Q2[i] = Q1[i] + jI[i]
        I2[i] = a2 * I2[i] + a8 * g(I2, 1)
        Q2[i] = a2 * Q2[i] + a8 * g(Q2, 1)
        Re[i] = I2[i] * g(I2, 1) + Q2[i] * g(Q2, 1)
        Im[i] = I2[i] * g(Q2, 1) - Q2[i] * g(I2, 1)
        Re[i] = a2 * Re[i] + a8 * g(Re, 1)
        Im[i] = a2 * Im[i] + a8 * g(Im, 1)
        p1 = g(P, 1, P0)
        if Im[i] != 0 and Re[i] != 0:
            P[i] = 360 / (math.atan(Im[i] / Re[i]) * 180 / pi)
        if P[i] > k15 * p1: P[i] = k15 * p1
        if P[i] < k67 * p1: P[i] = k67 * p1
        if P[i] < 6: P[i] = 6
        if P[i] > 50: P[i] = 50
        P[i] = a2 * P[i] + a8 * p1
        if I1[i] != 0:
            Ph[i] = math.atan(Q1[i] / I1[i]) * 180 / pi
        dp = g(Ph, 1) - Ph[i]
        if dp < 1: dp = 1
        al = FL / dp
        if al < SL: al = SL
        if al > FL: al = FL
        AL[i] = al
        M[i] = al * x[i] + (1 - al) * g(M, 1)
        F[i] = 0.5 * al * M[i] + (1 - 0.5 * al) * g(F, 1)
    return dict(mama=M, fama=F, period=P, alpha=AL, phase=Ph)


def mama_code(x, FL=0.5, SL=0.05, lit=None, pi=f32(3.14159), counter_offset=0):
    """MAMA.c lines 65-181. counter_offset>0 emulates a shared static barCount
    already advanced by another instance (R-1 class)."""
    c = lit or {}
    L = lambda s: c.get(s, float(s))
    w1, w2, kA, kB = L("0.0962"), L("0.5769"), L("0.075"), L("0.54")
    a2, a8, a33, a67, k15, k67 = L("0.2"), L("0.8"), L("0.33"), L("0.67"), L("1.5"), L("0.67")
    n = len(x)
    S, De, I1, Q1, jI, jQ, I2, Q2, Re, Im, P, SP, Ph, M, F, AL = (np.zeros(n) for _ in range(16))
    x0 = x[0]
    for i in range(n):
        bc = i + 1 + counter_offset
        # series(v): [0] = v each call; history padded with the first call's value
        S[i], M[i], F[i] = x[i], x[i], x[i]
        P[i], SP[i] = 20.0, 20.0
        for a in (De, I1, Q1, jI, jQ, I2, Q2, Re, Im, Ph):
            a[i] = 0.0
        if bc <= 5:
            continue
        pad = {id(S): x0, id(M): x0, id(F): x0, id(P): 20.0, id(SP): 20.0}
        g = lambda a, k: get(a, i, k, pad.get(id(a), x0 if a is x else 0.0))
        S[i] = (4.0 * x[i] + 3.0 * g(x, 1) + 2.0 * g(x, 2) + g(x, 3)) / 10.0
        pf = kA * g(P, 1) + kB
        ht = lambda a: (w1 * a[i] + w2 * g(a, 2) - w2 * g(a, 4) - w1 * g(a, 6)) * pf
        De[i] = ht(S); Q1[i] = ht(De); I1[i] = g(De, 3); jI[i] = ht(I1); jQ[i] = ht(Q1)
        I2[i] = I1[i] - jQ[i]; Q2[i] = Q1[i] + jI[i]
        I2[i] = a2 * I2[i] + a8 * g(I2, 1); Q2[i] = a2 * Q2[i] + a8 * g(Q2, 1)
        Re[i] = I2[i] * g(I2, 1) + Q2[i] * g(Q2, 1)
        Im[i] = I2[i] * g(Q2, 1) - Q2[i] * g(I2, 1)
        Re[i] = a2 * Re[i] + a8 * g(Re, 1); Im[i] = a2 * Im[i] + a8 * g(Im, 1)
        p1 = g(P, 1)
        if Im[i] != 0.0 and Re[i] != 0.0:
            P[i] = 360.0 / (math.atan(Im[i] / Re[i]) * 180.0 / pi)
        if P[i] > k15 * p1: P[i] = k15 * p1
        if P[i] < k67 * p1: P[i] = k67 * p1
        if P[i] < 6.0: P[i] = 6.0
        if P[i] > 50.0: P[i] = 50.0
        P[i] = a2 * P[i] + a8 * p1
        if I1[i] != 0.0:
            Ph[i] = math.atan(Q1[i] / I1[i]) * 180.0 / pi
        dp = g(Ph, 1) - Ph[i]
        if dp < 1.0: dp = 1.0
        al = FL / dp
        if al < SL: al = SL
        if al > FL: al = FL
        AL[i] = al
        M[i] = al * x[i] + (1.0 - al) * g(M, 1)
        F[i] = 0.5 * al * M[i] + (1.0 - 0.5 * al) * g(F, 1)
    return dict(mama=M, fama=F, period=P, alpha=AL, phase=Ph)


def frama_src(x, N=16, k46=4.6, k01=0.01, H=None, Lo=None):
    H = x if H is None else H
    Lo = x if Lo is None else Lo
    n = len(x); h = N // 2
    Filt = np.zeros(n); Dim = np.zeros(n); AL = np.zeros(n)
    dim = 0.0
    for i in range(n):
        hh = lambda k: H[max(i - k, 0)]; ll = lambda k: Lo[max(i - k, 0)]  # pre-start ambiguous (MaxBarsBack); Filt overwritten there
        N3 = (max(hh(k) for k in range(N)) - min(ll(k) for k in range(N))) / N
        N1 = (max(hh(k) for k in range(h)) - min(ll(k) for k in range(h))) / h
        N2 = (max(hh(k) for k in range(h, N)) - min(ll(k) for k in range(h, N))) / h
        if N1 > 0 and N2 > 0 and N3 > 0:
            dim = (math.log(N1 + N2) - math.log(N3)) / math.log(2)
        al = math.exp(-k46 * (dim - 1))
        if al < k01: al = k01
        if al > 1: al = 1
        Filt[i] = al * x[i] + (1 - al) * (Filt[i - 1] if i else 0.0)
        if i + 1 < N + 1:
            Filt[i] = x[i]
        Dim[i] = dim; AL[i] = al
    return dict(out=Filt, dim=Dim, alpha=AL)


def frama_code(x, T=16, k46=f32(4.6), k01=f32(0.01), H=None, Lo=None):
    H = x if H is None else H
    Lo = x if Lo is None else Lo
    n = len(x); out = np.zeros(n); prev = None
    for i in range(n):
        hh = lambda k: H[max(i - k, 0)]; ll = lambda k: Lo[max(i - k, 0)]  # series() padding (9d.6)
        Hi1 = max(hh(k) for k in range(T)); Lo1 = min(ll(k) for k in range(T))
        N1 = (Hi1 - Lo1) / T
        Hi2 = max(hh(k) for k in range(T, 2 * T)); Lo2 = min(ll(k) for k in range(T, 2 * T))
        N2 = (Hi2 - Lo2) / T
        N3 = (max(Hi1, Hi2) - min(Lo1, Lo2)) / (2.0 * T)
        if prev is None: prev = x[i]
        if N3 <= 0:
            out[i] = prev; continue
        lg = math.log(N1 + N2) if N1 + N2 > 0 else -math.inf   # Zorro log(0) = -inf (c: C library)
        D = (lg - math.log(N3)) / math.log(2.0)
        a = math.exp(-k46 * (D - 1.0))
        if a > 1.0: a = 1.0
        if a < k01: a = k01
        prev = a * x[i] + (1.0 - a) * prev
        out[i] = prev
    return dict(out=out)


def mx(a, b, r0=0):
    return float(np.max(np.abs(a[r0:] - b[r0:])))


if __name__ == "__main__":
    X = inputs()
    F32 = {k: f32(float(k)) for k in ("0.0962", "0.5769", "0.075", "0.54", "0.2", "0.8", "0.33", "0.67")}
    F32src = {k: f32(float(k)) for k in (".0962", ".5769", ".075", ".54", ".2", ".8", ".33", ".67")}
    print("== MAMA / FAMA (FL .5, SL .05); rows >= 1000 unless stated ==")
    print("in     | src FAMA range        | code-src FAMA all/>=1000 | f32lit fama | PI gap fama | shared-ctr(+1) fama all | mean alpha src | period src min..max")
    for k, x in X.items():
        s = mama_src(x)
        cd = mama_code(x, pi=math.pi)                        # code structure, float64 literals, exact pi
        c32 = mama_code(x, lit=F32, pi=math.pi)              # + float32 literals
        cpi = mama_code(x, pi=f32(3.14159))                  # + Zorro PI
        csh = mama_code(x, pi=math.pi, counter_offset=1)     # second instance on a shared barCount
        r = slice(1000, None)
        print(f"{k:6s} | {s['fama'][r].min():.6f}..{s['fama'][r].max():.6f} | "
              f"{mx(cd['fama'], s['fama']):.3e} / {mx(cd['fama'], s['fama'], 1000):.3e} | "
              f"{mx(c32['fama'], cd['fama'], 1000):.3e} | {mx(cpi['fama'], cd['fama'], 1000):.3e} | "
              f"{mx(csh['fama'], cd['fama']):.3e} | {s['alpha'][r].mean():.4f} | "
              f"{s['period'][r].min():.3f}..{s['period'][r].max():.3f}")
    # MAMA source vs code: how long does the start-up difference last?
    for k in ("s20", "s100", "ramp"):
        s = mama_src(X[k]); cd = mama_code(X[k], pi=math.pi)
        d = np.abs(cd["fama"] - s["fama"]); last = np.nonzero(d > 1e-12)[0]
        print(f"  start-up {k}: FAMA src vs code max {d.max():.3e}, last row > 1e-12: {last[-1] if len(last) else None}; "
              f"MAMA last row > 1e-12: {np.nonzero(np.abs(cd['mama'] - s['mama']) > 1e-12)[0][-1]}")
    # ramp known answers (src): lag of MAMA and FAMA
    s = mama_src(X["ramp"]); n = np.arange(NB); xr = X["ramp"]
    print(f"  ramp src rows>=1000: MAMA lag {np.mean((xr-s['mama'])[1000:])/1e-4:.12f}  FAMA lag {np.mean((xr-s['fama'])[1000:])/1e-4:.12f}  alpha min/max {s['alpha'][1000:].min()}/{s['alpha'][1000:].max()}")
    s = mama_src(X["flat"])
    print(f"  flat src: MAMA |x-M| at row 1000 {abs(X['flat'][1000]-s['mama'][1000]):.3e}, FAMA {abs(X['flat'][1000]-s['fama'][1000]):.3e}; period {s['period'][1000]}")
    # Period hold vs series-default: count rows where Im or Re == 0 on the sines, src
    print("\n== FRAMA (H = L = x) ==")
    print("in     | src N16 range            | code T16 (N32) vs src N16 | code T8 vs src N16 all / >=200 | f32 lit (T8) | src alpha mean | dim min..max")
    for k, x in X.items():
        s = frama_src(x, 16); c16 = frama_code(x, 16, k46=4.6, k01=0.01)
        c8 = frama_code(x, 8, k46=4.6, k01=0.01); c8f = frama_code(x, 8)
        print(f"{k:6s} | {s['out'][200:].min():.6f}..{s['out'][200:].max():.6f} | {mx(c16['out'], s['out'], 200):.3e} | "
              f"{mx(c8['out'], s['out']):.3e} / {mx(c8['out'], s['out'], 200):.3e} | {mx(c8f['out'], c8['out'], 200):.3e} | "
              f"{s['alpha'][200:].mean():.4f} | {s['dim'][200:].min():.4f}..{s['dim'][200:].max():.4f}")
    s = frama_src(X["ramp"], 16)
    print(f"  ramp src: lag rows>=200 {np.mean((X['ramp']-s['out'])[200:])/1e-4:.3e} bars; dim {s['dim'][500]:.12f} (log2(4*7/15) = {math.log2(28/15):.12f})")
    # code hold rule vs source on a sine with flat stretches: build an input with a flat segment
    y = X["s20"].copy(); y[1000:1100] = y[1000]
    s = frama_src(y, 16); c8 = frama_code(y, 8, k46=4.6, k01=0.01)
    print(f"  flat stretch (rows 1000-1099 held) in s20: max |code - src| rows 1000-1300 {mx(c8['out'][:1300], s['out'][:1300], 1000):.3e}")
