"""
run_btc.py — crypto arm of the cycle-premise null test.

Identical pipeline, metrics and nulls to run_experiment.py; only the null
CALIBRATION differs (H estimated from BTC itself: H_ret=0.523, H_vol=0.90).

period_stability uses step=50 here rather than the FX arm's step=25: BTC has
5,927 bars vs 2,236, and 215 rolling Welch windows was the runtime
bottleneck. 108 windows gives the same statistic. Applied identically to real
and surrogate series, so within-asset comparisons are valid; raw stability
values are NOT directly comparable across assets.

EXECUTION NOTE: this was originally run in two passes (nulls C+D, then A+B)
to fit sandbox time limits. This consolidated script reproduces all four in
one run and is the canonical version.
"""
import numpy as np, pandas as pd, sys, time, warnings
warnings.filterwarnings('ignore'); sys.path.insert(0, 'src')
from pipeline import full_pipeline_fast
from metrics import compute_all, BURN_IN
import metrics as M
from surrogates import (surrogate_bootstrap, surrogate_fgn, surrogate_iaaft,
                        surrogate_stochvol, surrogate_fgn_plus_sine)

# widen period_stability step for the longer BTC series (see docstring)
_orig = M.period_stability
M.period_stability = lambda x, win=250, step=50: _orig(x, win, step)
M.METRICS['period_stability'] = M.period_stability

N = 1000
H_RET, H_VOL, S_VOL = 0.523, 0.90, 1.0
SEED = 20260803

df = pd.read_csv('data/CyberCycle_Surrogate_BTCUSD_H4.csv', header=None,
                 names=['bar', 'price', 'roofing', 'cycle', 'trigger'])
price = df.price.values
rets = np.diff(np.log(price))
p0 = price[0]
rng = np.random.default_rng(SEED)
KEYS = list(M.METRICS.keys())


def met(px):
    _, c, _ = full_pipeline_fast(px)
    return compute_all(c, burn_in=BURN_IN)


real = met(price)
print("=" * 72)
print(f"REAL BTC/USD H4  ({len(price)-BURN_IN} bars post burn-in {BURN_IN})")
print("=" * 72)
for k in KEYS:
    print(f"  {k:20s} {real[k]:14.4f}")

NULLS = {
    'A_bootstrap': lambda: surrogate_bootstrap(rets, p0, rng),
    'B_fgn':       lambda: surrogate_fgn(rets, p0, H_RET, rng),
    # n_iter=50: spectral error 0.0015, converged (200 gave 0.0011)
    'C_iaaft':     lambda: surrogate_iaaft(rets, p0, rng, n_iter=50),
    'D_stochvol':  lambda: surrogate_stochvol(rets, p0, H_VOL, rng, s=S_VOL),
}

res = {}
for n, g in NULLS.items():
    t = time.time()
    res[n] = pd.DataFrame([met(g()) for _ in range(N)])
    res[n].to_csv(f'out/btc_null_{n}.csv', index=False)
    print(f"{n} done {time.time()-t:.0f}s", flush=True)


def p2(v, o):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    return min(1.0, 2 * min((v >= o).mean(), (v <= o).mean()))


pv = pd.DataFrame({n: [p2(d[k].values, real[k]) for k in KEYS]
                   for n, d in res.items()}, index=KEYS)
pv.to_csv('out/pvalues_btc.csv')
pd.Series(real).to_csv('out/real_metrics_btc.csv')
print("\n" + "=" * 72)
print(f"BTC/USD H4 — TWO-SIDED RANK p-VALUES (N={N})")
print("=" * 72)
print(pv.round(4).to_string())
print(f"\nminimum p across all {pv.size} tests: {pv.values.min():.3f}")

# positive control: detection power
thr = np.percentile(res['D_stochvol']['peak_prominence'].values, 95)
print(f"\n=== DETECTION POWER (vs Null-D 95th pct {thr:.2f}) ===")
rows = []
for snr in [-20, -16, -14, -12, -10]:
    pr = np.array([met(surrogate_fgn_plus_sine(rets, p0, H_RET, rng, 20.0, snr))
                   ['peak_prominence'] for _ in range(150)])
    rows.append({'snr_db': snr, 'detect_rate': (pr > thr).mean()})
    print(f"  SNR {snr:+4d} dB  detect {(pr>thr).mean():.3f}")
pd.DataFrame(rows).to_csv('out/control_power_btc.csv', index=False)
