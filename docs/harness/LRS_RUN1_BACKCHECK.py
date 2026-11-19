"""LRS run 1 back-check (planning chat). Independent of checker.py: own models, own measurements."""
import numpy as np, sys
raw = sys.argv[1]
D = np.genfromtxt(raw, delimiter=',', names=True)
N = len(D); n = np.arange(N); W = 700
lvl, amp, s = 11/10, 1/100, 1/10000
pi = 4*np.arctan(1.0)
Ts = (5, 10, 20, 40, 100)
tol = dict(gain=3e-5, phase=3e-5, lag=1e-3, flat=1e-9, trace=3e-5, startup=1e-6, ramp_exact=1e-12, bound=1e-12, inv=1e-9, imp=1e-9)
def col(c): return np.asarray(D[c], float)
# --- input guard
X = {'flat': np.full(N, lvl), 'alt': lvl + amp*np.where(n % 2 == 0, 1.0, -1.0), 'ramp': lvl + s*n, 'rampdn': lvl - s*n}
for T in Ts:
    X[f's{T}'] = lvl + amp*np.sin(2*pi*n/T); X[f'sc{T}'] = lvl + 10*amp*np.sin(2*pi*n/T); X[f'of{T}'] = 2*lvl + amp*np.sin(2*pi*n/T)
xg = max(np.abs(col('x_'+k) - v).max() for k, v in X.items())
print(f"input guard max |x - recomputed| = {xg:.3e}  {'PASS' if xg <= 1e-12 else 'FAIL'}")
# --- model
def model(x, g, gL0=None, form='book', seed=False, hold0=0.0, prev_shared=None):
    gL0 = g if gL0 is None else gL0
    L = [0.0]*4; R = hold0; out = np.empty(len(x)); L0s = np.empty(len(x)); L3s = np.empty(len(x)); den = np.empty(len(x))
    for i, c in enumerate(x):
        if seed and i == 0:
            L = [c]*4; out[i] = 0.5; L0s[i] = c; L3s[i] = c; den[i] = 0.0; continue
        p = L
        L0 = (1-gL0)*c + gL0*p[0]
        if form == 'book':
            L1 = -g*L0 + p[0] + g*p[1]; L2 = -g*L1 + p[1] + g*p[2]; L3 = -g*L2 + p[2] + g*p[3]
        else:
            L1 = -g*p[0] + p[0] + g*p[1]; L2 = -g*p[1] + p[1] + g*p[2]; L3 = -g*p[2] + p[2] + g*p[3]
        L = [L0, L1, L2, L3]; cu = cd = 0.0
        for a, b in ((L0, L1), (L1, L2), (L2, L3)):
            if a >= b: cu += a - b
            else: cd += b - a
        if cu + cd != 0: R = cu/(cu + cd)
        out[i] = R; L0s[i] = L0; L3s[i] = L3; den[i] = cu + cd
    return out, L0s, L3s, den
def H(g, w):
    z1 = np.exp(-1j*w); h0 = (1-g)/(1-g*z1); A = (z1-g)/(1-g*z1); return h0, h0*A**3
def fitsine(y, T):
    w = 2*pi/T; r = np.arange(W, N); M = np.c_[np.sin(w*r), np.cos(w*r), np.ones(len(r))]
    a, b, c = np.linalg.lstsq(M, y[W:], rcond=None)[0]; return np.hypot(a, b)/amp, np.arctan2(b, a)
def fitalt(y):
    r = np.arange(W, N); M = np.c_[np.where(r % 2 == 0, 1.0, -1.0), np.ones(len(r))]
    A, c = np.linalg.lstsq(M, y[W:], rcond=None)[0]; return abs(A)/amp, (0.0 if A >= 0 else pi)
def wrap(d): return (d + pi) % (2*pi) - pi
real = {'G05': 1/2, 'G07': 7/10, 'G08': 4/5}
rows = []  # (variant, check, value, tol, verdict)
def add(v, chk, val, t, required_fail=False): rows.append((v, chk, val, t, 'PASS' if val <= t else 'FAIL'))
ctrl = {'NCG': dict(gL0=1/2+1/1000), 'NC25': dict(form='tasc2025'), 'NCP': dict(seed=True), 'NCH': dict(hold0=1/2)}
specs = {**{k: (g, {}) for k, g in real.items()}, **{k: (1/2, kw) for k, kw in ctrl.items()}}
imp = {}; floor = {}
for v, (g, kw) in specs.items():
    base = real.get(v, 1/2)  # controls compared with the G05 tables/model
    gi = 0.0
    for stage, idx in (('l0', 1), ('l3', 2)):
        y = col(f'{stage}_{v}_flat'); add(v, f'{stage} flat', np.abs(y[W:] - lvl).max(), tol['flat'])
        for T in Ts:
            G, P = fitsine(col(f'{stage}_{v}_s{T}'), T); h = H(base, 2*pi/T)[idx-1]
            add(v, f'{stage} gain T{T}', abs(G - abs(h)), tol['gain']); add(v, f'{stage} phase T{T}', abs(wrap(P - np.angle(h))), tol['phase'])
        G, P = fitalt(col(f'{stage}_{v}_alt')); h = H(base, pi)[idx-1]
        add(v, f'{stage} alt gain', abs(G - abs(h)), tol['gain']); add(v, f'{stage} alt phase', abs(wrap(P - np.angle(h))), tol['phase'])
        y = col(f'{stage}_{v}_ramp'); lag = np.mean((X['ramp'] - y)[-100:])/s
        exp_lag = base/(1-base) + (3*(1+base)/(1-base) if stage == 'l3' else 0)
        add(v, f'{stage} ramp lag', abs(lag - exp_lag), tol['lag'])
    # out
    for T in Ts:
        x = col(f'x_s{T}'); mo = model(x, base)[0]; y = col(f'out_{v}_s{T}')
        md = model(x, base)[3]; m = (md/amp >= 0.01); m[:W] = False
        add(v, f'out trace T{T}', np.abs(y - mo)[m].max(), tol['trace'])
        add(v, f'out startup T{T}', np.abs(y - mo)[:W].max(), tol['startup'])
    allout = np.concatenate([col(c) for c in D.dtype.names if c.startswith(f'out_{v}_')])
    add(v, 'out bound', max(0.0, -allout.min(), allout.max() - 1), tol['bound'])
    add(v, 'out exact ramp', np.abs(col(f'out_{v}_ramp')[W:] - 1).max(), tol['ramp_exact'])
    add(v, 'out exact rampdn', np.abs(col(f'out_{v}_rampdn')[W:]).max(), tol['ramp_exact'])
    if v in real:
        for tr in ('sc', 'of'):
            add(v, f'out invar {tr}', max(np.abs(col(f'out_{v}_{tr}{T}') - col(f'out_{v}_s{T}'))[W:].max() for T in Ts), tol['inv'])
    # IMP: own model on exported x, rows >= W, l0/l3/den all base inputs, out on sines (+ copies) gated
    r = 0.0
    for inp in ['flat'] + [f's{T}' for T in Ts] + ['alt', 'ramp', 'rampdn']:
        mo, m0, m3, md = model(col(f'x_{inp}'), g, **kw)
        for nm, mm in (('l0', m0), ('l3', m3), ('den', md)):
            r = max(r, np.abs(col(f'{nm}_{v}_{inp}') - mm)[W:].max())
        if inp.startswith('s'):
            gate = md/amp >= 0.01; gate[:W] = False
            r = max(r, np.abs(col(f'out_{v}_{inp}') - mo)[gate].max())
    if v in real:
        for tr in ('sc', 'of'):
            for T in Ts:
                a_ = 10*amp if tr == 'sc' else amp
                mo, _, _, md = model(col(f'x_{tr}{T}'), g); gate = md/a_ >= 0.01; gate[:W] = False
                r = max(r, np.abs(col(f'out_{v}_{tr}{T}') - mo)[gate].max())
    imp[v] = r
# NCS / NCT: shared statics, actual call order: NCS s5 first call of the run takes the seed
nc = {}
for v in ('NCS', 'NCT'):
    r = 0.0; eff = {}
    for inp in [f's{T}' for T in Ts] + ['alt', 'ramp', 'rampdn']:
        x = col(f'x_{inp}'); seeded = (v == 'NCS' and inp == 's5')
        mo = model(x, 1/2, seed=seeded)[0]   # superseded: seed returns 0.5, later identical; hold never fires on these inputs
        r = max(r, np.abs(col(f'out_{v}_{inp}') - mo)[W:].max())
        g05 = model(x, 1/2)[0]; y = col(f'out_{v}_{inp}')
        if inp.startswith('s'):
            eff[inp] = (np.abs(y - g05)[:W].max(), np.abs(y - g05)[W:].max())
        allo = y
    imp[v] = r; nc[v] = eff
# IMP must_fail: G05 vs NCG model
mf = 0.0
for T in Ts:
    x = col(f'x_s{T}'); mo, _, _, md = model(x, 1/2, gL0=1/2+1/1000); gate = md/amp >= 0.01; gate[:W] = False
    mf = max(mf, np.abs(col(f'out_G05_s{T}') - mo)[gate].max())
# report
print("\n=== REAL variants (129 expected) ===")
nreal = sum(1 for r in rows if r[0] in real); npass = sum(1 for r in rows if r[0] in real and r[4] == 'PASS')
print(f"real checks {nreal}, PASS {npass}, FAIL {nreal - npass}")
for v in real:
    for kind, t in (('gain', 'gain'), ('phase', 'phase'), ('flat', 'flat'), ('lag', 'lag'), ('trace', 'trace'), ('startup', 'startup'), ('bound', 'bound'), ('exact', 'ramp_exact'), ('invar', 'inv')):
        vals = [r[2] for r in rows if r[0] == v and kind in r[1]]
        print(f"  {v} {kind:8s} n={len(vals):2d} max {max(vals):.3e}  tol {tol[t]:.0e}  floor-guard(tol/10) {'ok' if max(vals) <= tol[t]/10 else 'EXCEEDED'}")
for r in rows:
    if r[0] in real and r[4] == 'FAIL': print("  FAIL", r)
print("\n=== Controls: kinds with a FAIL row ===")
for v in ('NCG', 'NC25', 'NCP'):
    kinds = {}
    for r in rows:
        if r[0] == v and r[4] == 'FAIL':
            k = r[1].split()[1] if r[1].startswith('out') else r[1].split()[1]
            kinds.setdefault(k, []).append(r[2])
    print(f"  {v}: " + ", ".join(f"{k} {len(vs)} rows (max {max(vs):.6g})" for k, vs in kinds.items()))
    print(f"     total FAIL rows {sum(1 for r in rows if r[0]==v and r[4]=='FAIL')}")
print("  NCH (info): rows that would FAIL:", [r[1] for r in rows if r[0] == 'NCH' and r[4] == 'FAIL'])
for v in ('NCS', 'NCT'):
    print(f"  {v} vs G05 model (startup max, trace max) per sine:", {k: (f"{a!r}", f"{b:.3e}") for k, (a, b) in nc[v].items()})
print("\n=== IMP (own model, rows >= W) ===")
for v, r in imp.items(): print(f"  {v}: {r:.3e}  {'PASS' if r <= 1e-9 else 'FAIL'}")
print(f"  must_fail G05 vs NCG model: {mf!r}  {'FIRES' if mf > 1e-9 else 'DOES NOT FIRE'}")
print("\n=== Control FAIL rows (variant | check | value) ===")
for r in rows:
    if r[0] in ('NCG', 'NC25', 'NCP') and r[4] == 'FAIL': print(f"  {r[0]} | {r[1]} | {r[2]!r}")
a, b = nc['NCS']['s5']; print(f"  NCS | out startup T5 | {a!r}")
