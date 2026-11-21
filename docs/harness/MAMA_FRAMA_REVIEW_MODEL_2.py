"""Second pass: conditioning, shared state, FRAMA hold rule, bounds, equivariance.
Uses MAMA_FRAMA_REVIEW_MODEL.py (same folder). Seeds fixed (20261120)."""
import math
import numpy as np
from MAMA_FRAMA_REVIEW_MODEL import inputs, mama_src, mama_code, frama_src, frama_code, mx, f32, NB

X = inputs()
rng = np.random.default_rng(20261120)

print("== MAMA conditioning: 1-ulp relative input perturbation (x * (1 + 2^-52 * u), u in {-1,0,1}), source model ==")
print("in     | max|dFAMA| all / >=1000 | max|dMAMA| >=1000 | rows>=1000 where alpha differs | alpha clamped share (FL / SL / interior)")
for k, x in X.items():
    s = mama_src(x)
    xp = x * (1 + 2.0 ** -52 * rng.integers(-1, 2, NB))
    p = mama_src(xp)
    r = slice(1000, None)
    a = s["alpha"][r]
    print(f"{k:6s} | {mx(p['fama'], s['fama']):.3e} / {mx(p['fama'], s['fama'], 1000):.3e} | {mx(p['mama'], s['mama'], 1000):.3e} | "
          f"{int(np.sum(np.abs(p['alpha'][r] - a) > 1e-9))} | {np.mean(a == 0.5):.3f} / {np.mean(a == 0.05):.3f} / {np.mean((a > 0.05) & (a < 0.5)):.3f}")

print("\n== MAMA s5 float32-literal jump: where and why ==")
x = X["s5"]
F32 = {k: f32(float(k)) for k in ("0.0962", "0.5769", "0.075", "0.54", "0.2", "0.8", "0.33", "0.67")}
cd = mama_code(x, pi=math.pi); c32 = mama_code(x, lit=F32, pi=math.pi)
d = np.abs(c32["fama"] - cd["fama"]); i = int(np.argmax(d[1000:])) + 1000
da = np.nonzero(np.abs(c32["alpha"] - cd["alpha"]) > 1e-9)[0]
print(f"  max at row {i}: {d[i]:.3e}; alpha differs on {len(da)} rows, first {da[:5]}; "
      f"alpha there {cd['alpha'][da[:3]]} vs {c32['alpha'][da[:3]]}")
print(f"  phase step there (code64): {[round(cd['phase'][j-1]-cd['phase'][j],6) for j in da[:3]]}")

print("\n== MAMA shared barCount (second instance sees the counter one ahead) ==")
for k in ("s20", "s100", "ramp"):
    a = mama_code(X[k], pi=math.pi); b = mama_code(X[k], pi=math.pi, counter_offset=1)
    dd = np.abs(a["fama"] - b["fama"]); last = np.nonzero(dd > 1e-12)[0]
    print(f"  {k}: max {dd.max():.3e}, last row > 1e-12: {last[-1] if len(last) else None}")

print("\n== MAMA Period init 20 / series defaults vs source (start-up only?) - isolate: source with period0=20 ==")
for k in ("s20", "s100"):
    s0 = mama_src(X[k]); s20 = mama_src(X[k], period0=20.0)
    dd = np.abs(s0["fama"] - s20["fama"]); last = np.nonzero(dd > 1e-12)[0]
    print(f"  {k}: max {dd.max():.3e}, last row > 1e-12: {last[-1] if len(last) else None}")

print("\n== FRAMA hold rule: step and random walk (H = L = x), N = 16 ==")
step = np.full(NB, 1.1); step[1000:] = 1.2
rw = 1.1 + np.cumsum(rng.normal(0, 0.005, NB))
stair = 1.1 + 0.001 * (np.arange(NB) // 16)        # flat for 16 bars, then a step: N1 or N2 = 0 often
for k, x in (("step", step), ("rw", rw), ("stair16", stair)):
    s = frama_src(x, 16); c = frama_code(x, 8, k46=4.6, k01=0.01)
    dd = np.abs(s["out"] - c["out"]); last = np.nonzero(dd > 1e-12)[0]
    print(f"  {k}: max |code - src| all {dd.max():.3e}, rows>=200 {dd[200:].max():.3e}, last row > 1e-12 {last[-1] if len(last) else None}")

print("\n== FRAMA start-up memory: alpha floor .01 => .99^n < 1e-12 from n =", math.ceil(math.log(1e-12) / math.log(0.99)), "==")
print("== FRAMA shared statics: two instances (N16 then N32) on one input share frama_prev / frama_init ==")


def frama_two_shared(x, T1, T2):
    """Both calls per bar read and write ONE frama_prev (code lines 74-93)."""
    n = len(x); o1 = np.zeros(n); o2 = np.zeros(n); prev = None
    for i in range(n):
        outs = []
        for T in (T1, T2):
            hh = lambda k: x[max(i - k, 0)]
            r1 = max(hh(k) for k in range(T)) - min(hh(k) for k in range(T))
            r2 = max(hh(k) for k in range(T, 2 * T)) - min(hh(k) for k in range(T, 2 * T))
            r3 = max(hh(k) for k in range(2 * T)) - min(hh(k) for k in range(2 * T))
            N1, N2, N3 = r1 / T, r2 / T, r3 / (2.0 * T)
            if prev is None: prev = x[i]
            if N3 <= 0: outs.append(prev); continue
            D = ((math.log(N1 + N2) if N1 + N2 > 0 else -math.inf) - math.log(N3)) / math.log(2.0)
            a = min(1.0, max(0.01, math.exp(-4.6 * (D - 1.0))))
            prev = a * x[i] + (1.0 - a) * prev; outs.append(prev)
        o1[i], o2[i] = outs
    return o1, o2


for k in ("s20", "s40", "rw"):
    x = rw if k == "rw" else X[k]
    o1, o2 = frama_two_shared(x, 8, 16)
    a1 = frama_code(x, 8, 4.6, 0.01)["out"]; a2 = frama_code(x, 16, 4.6, 0.01)["out"]
    print(f"  {k}: instance 1 off by {mx(o1, a1, 200):.3e}, instance 2 off by {mx(o2, a2, 200):.3e} (rows >= 200)")

print("\n== Structural bounds (source models, every row) ==")
for k, x in X.items():
    s = mama_src(x); f = frama_src(x, 16)
    a = s["alpha"][6:]
    print(f"  {k:6s} MAMA alpha in [{a.min():.4f},{a.max():.4f}]  FRAMA alpha in [{f['alpha'].min():.4f},{f['alpha'].max():.4f}]  "
          f"FRAMA out within [min x, max x] so far: {bool(np.all((f['out'] >= np.minimum.accumulate(x) - 1e-15) & (f['out'] <= np.maximum.accumulate(x) + 1e-15)))}")
print("\n== Equivariance (FRAMA(k x + c) = k FRAMA(x) + c; MAMA same?) s40, k = 3, c = 0.5 ==")
x = X["s40"]
f = frama_src(x, 16)["out"]; g = frama_src(3 * x + 0.5, 16)["out"]
m = mama_src(x); mm = mama_src(3 * x + 0.5)
print(f"  FRAMA max |g - (3f+.5)| rows>=0: {np.max(np.abs(g - (3 * f + 0.5))):.3e}")
print(f"  MAMA  max |.. | rows>=1000: {mx(mm['mama'], 3 * m['mama'] + 0.5, 1000):.3e}; FAMA {mx(mm['fama'], 3 * m['fama'] + 0.5, 1000):.3e}; alpha {mx(mm['alpha'], m['alpha'], 1000):.3e}")
