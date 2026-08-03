"""
run_experiment.py — the null-hypothesis test of Ehlers' cycle premise.

For each null model, generate N surrogate PRICE series, push each through the
Zorro-validated RoofingFilter -> CyberCycle pipeline, compute detection
metrics on the output, and locate the REAL EUR/USD value within the resulting
null distribution.

p-value is rank-based and two-sided:
    p = 2 * min(P(surrogate >= real), P(surrogate <= real))
A small p means the real series is atypical of that null.
"""

import numpy as np
import pandas as pd
import sys
import time
import warnings

warnings.filterwarnings('ignore')
sys.path.insert(0, 'src')

from pipeline import full_pipeline_fast
from metrics import compute_all, METRICS, BURN_IN
from surrogates import (surrogate_bootstrap, surrogate_fgn, surrogate_iaaft,
                        surrogate_stochvol, surrogate_fgn_plus_sine)

N_SURR = 1000
H_RET, H_VOL, S_VOL = 0.460, 0.75, 1.0
SEED = 20260803

df = pd.read_csv('data/CyberCycle_Surrogate_EURUSD_D1.csv', header=None,
                 names=['bar', 'price', 'roofing', 'cycle', 'trigger'])
price = df.price.values
rets = np.diff(np.log(price))
p0 = price[0]
rng = np.random.default_rng(SEED)

KEYS = list(METRICS.keys())


def metrics_of_price(px):
    _, cyc, _ = full_pipeline_fast(px)
    return compute_all(cyc, burn_in=BURN_IN)


# ---- real -------------------------------------------------------------
real = metrics_of_price(price)
print("=" * 78)
print(f"REAL EUR/USD D1  ({len(price) - BURN_IN} bars after burn-in {BURN_IN})")
print("=" * 78)
for k in KEYS:
    print(f"  {k:20s} {real[k]:12.4f}")

# ---- nulls ------------------------------------------------------------
NULLS = {
    'A_bootstrap': lambda: surrogate_bootstrap(rets, p0, rng),
    'B_fgn':       lambda: surrogate_fgn(rets, p0, H_RET, rng),
    'C_iaaft':     lambda: surrogate_iaaft(rets, p0, rng),
    'D_stochvol':  lambda: surrogate_stochvol(rets, p0, H_VOL, rng, s=S_VOL),
}

results = {}
for name, gen in NULLS.items():
    t0 = time.time()
    rows = []
    for i in range(N_SURR):
        rows.append(metrics_of_price(gen()))
        if (i + 1) % 250 == 0:
            print(f"  {name}: {i+1}/{N_SURR}  ({time.time()-t0:.0f}s)", flush=True)
    results[name] = pd.DataFrame(rows)
    print(f"{name} done in {time.time()-t0:.0f}s", flush=True)

# ---- p-values ---------------------------------------------------------
def two_sided_p(null_vals, obs):
    v = np.asarray(null_vals, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) == 0 or not np.isfinite(obs):
        return np.nan
    hi = (v >= obs).mean()
    lo = (v <= obs).mean()
    return min(1.0, 2.0 * min(hi, lo))


pvals = pd.DataFrame(index=KEYS, columns=list(NULLS), dtype=float)
summary = []
for name, dfr in results.items():
    for k in KEYS:
        pvals.loc[k, name] = two_sided_p(dfr[k].values, real[k])
        v = dfr[k].values
        v = v[np.isfinite(v)]
        summary.append({'null': name, 'metric': k, 'real': real[k],
                        'null_mean': v.mean(), 'null_std': v.std(),
                        'null_p5': np.percentile(v, 5),
                        'null_p95': np.percentile(v, 95),
                        'p': pvals.loc[k, name]})

pd.DataFrame(summary).to_csv('out/summary.csv', index=False)
pvals.to_csv('out/pvalues.csv')
for name, dfr in results.items():
    dfr.to_csv(f'out/null_{name}.csv', index=False)
pd.Series(real).to_csv('out/real_metrics.csv')

print("\n" + "=" * 78)
print(f"TWO-SIDED RANK p-VALUES  (N={N_SURR} per null)")
print("=" * 78)
print(pvals.round(4).to_string())
print("\nsaved to out/")
