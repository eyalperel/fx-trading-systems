"""
run_regime2.py — regime-conditional test, REVISED STATISTIC.

WHY REVISED: v1 used max-window-prominence. Its positive control detected a
regime-localised cycle only 10.8% of the time at -6 dB -- essentially no
power, so its non-rejections were meaningless. Cause: a maximum over ~67
windows AND over all passband frequencies has a heavy-tailed null
(Null-D 95th pct = 61.45 vs real 20.47). Multiple-comparison inflation.

REVISED STATISTICS -- means, not maxima, plus a targeted contrast:
    M_hi    mean prominence in top-tercile volatility windows
    M_lo    mean prominence in bottom-tercile volatility windows
    D_hilo  M_hi - M_lo   <- DIRECTLY tests "cycles live in a vol regime"
    M_all   mean prominence across all windows

The v1 failure is retained in the record: the positive control doing its
job is the reason a null result here can be trusted.
"""
import numpy as np
import pandas as pd
import sys
import time
import warnings

warnings.filterwarnings('ignore')
sys.path.insert(0, 'src')

from scipy import signal
from pipeline import full_pipeline_fast
from metrics import BURN_IN
from surrogates import (surrogate_bootstrap, surrogate_fgn, surrogate_iaaft,
                        surrogate_stochvol, _fgn_davies_harte,
                        _amplitude_adjust)

WIN = 250
N_SURR = 300


def win_prom(x, step):
    out = []
    for a in range(0, len(x) - WIN + 1, step):
        f, P = signal.welch(x[a:a + WIN], nperseg=256, detrend='linear')
        f, P = f[1:], P[1:]
        b = (f >= 1 / 48) & (f <= 1 / 10)
        out.append(P[b].max() / np.median(P[b]) if b.sum() >= 4 else np.nan)
    return np.array(out)


def win_vol(r, step):
    return np.array([np.mean(np.abs(r[a:a + WIN]))
                     for a in range(0, len(r) - WIN + 1, step)])


def stats(price, step):
    _, cyc, _ = full_pipeline_fast(price)
    c = cyc[BURN_IN:]
    r = np.diff(np.log(price))[BURN_IN:]
    prom = win_prom(c, step)
    vol = win_vol(r, step)
    n = min(len(prom), len(vol))
    prom, vol = prom[:n], vol[:n]
    ok = np.isfinite(prom) & np.isfinite(vol)
    prom, vol = prom[ok], vol[ok]
    if len(prom) < 9:
        return {k: np.nan for k in ['M_hi', 'M_lo', 'D_hilo', 'M_all']}
    hi = vol >= np.percentile(vol, 67)
    lo = vol <= np.percentile(vol, 33)
    Mh, Ml = prom[hi].mean(), prom[lo].mean()
    return {'M_hi': Mh, 'M_lo': Ml, 'D_hilo': Mh - Ml, 'M_all': prom.mean()}


def control(rets, p0, H, rng, period=20.0, snr_db=0.0, vol_win=60):
    """Cycle injected ONLY in top-tercile volatility bars."""
    n = len(rets)
    z = _fgn_davies_harte(n, H, rng)
    r = _amplitude_adjust(z, np.sort(rets))
    v = pd.Series(np.abs(r)).rolling(vol_win, min_periods=1).mean().values
    mask = (v >= np.nanpercentile(v, 67)).astype(float)
    amp = np.sqrt(2.0 * np.var(r) * 10.0 ** (snr_db / 10.0))
    t = np.arange(n)
    sine = amp * np.sin(2 * np.pi * t / period + rng.uniform(0, 2 * np.pi))
    return p0 * np.exp(np.concatenate([[0.0], np.cumsum(r + sine * mask)]))


def run(label, csv, H_ret, H_vol, step, nulls_subset=None, seed=20260803):
    df = pd.read_csv(csv, header=None,
                     names=['bar', 'price', 'roofing', 'cycle', 'trigger'])
    price = df.price.values
    rets = np.diff(np.log(price))
    p0 = price[0]
    rng = np.random.default_rng(seed)

    real = stats(price, step)
    print("=" * 70)
    print(f"{label} — REGIME-CONDITIONAL TEST (revised statistic)")
    print("=" * 70)
    for k, v in real.items():
        print(f"  {k:8s} {v:9.3f}")

    allnulls = {
        'A_bootstrap': lambda: surrogate_bootstrap(rets, p0, rng),
        'B_fgn':       lambda: surrogate_fgn(rets, p0, H_ret, rng),
        'C_iaaft':     lambda: surrogate_iaaft(rets, p0, rng, n_iter=30),
        'D_stochvol':  lambda: surrogate_stochvol(rets, p0, H_vol, rng, s=1.0),
    }
    nulls = {k: v for k, v in allnulls.items()
             if nulls_subset is None or k in nulls_subset}

    res = {}
    for n, g in nulls.items():
        t = time.time()
        res[n] = pd.DataFrame([stats(g(), step) for _ in range(N_SURR)])
        print(f"  {n} {time.time()-t:.0f}s", flush=True)

    def p2(v, o):
        v = np.asarray(v, float); v = v[np.isfinite(v)]
        return min(1.0, 2 * min((v >= o).mean(), (v <= o).mean()))

    print(f"\n  p-values (N={N_SURR}):")
    print(f"  {'stat':8s}" + "".join(f"{k.split('_')[0]:>10s}" for k in nulls))
    pv = {}
    for k in real:
        pv[k] = {n: p2(d[k].values, real[k]) for n, d in res.items()}
        print(f"  {k:8s}" + "".join(f"{pv[k][n]:10.3f}" for n in nulls))

    print(f"\n  REAL percentile in each null:")
    for k in real:
        print(f"  {k:8s}" + "".join(
            f"{(d[k].values < real[k]).mean()*100:9.1f}%" for d in res.values()))

    key = 'D_stochvol' if 'D_stochvol' in res else list(res)[0]
    thr = np.percentile(res[key]['D_hilo'].values, 95)
    print(f"\n  POWER on D_hilo (null {key} 95th = {thr:.3f}):")
    rows = []
    for snr in [-25, -20, -18, -16, -14, -12, -10]:
        s = np.array([stats(control(rets, p0, H_ret, rng, 20.0, snr), step)['D_hilo']
                      for _ in range(100)])
        rows.append({'snr_db': snr, 'detect_rate': (s > thr).mean()})
        print(f"    SNR {snr:+4d} dB  detect {(s>thr).mean():.3f}")

    tag = label.split()[0]
    pd.DataFrame(pv).to_csv(f'out/regime2_pvalues_{tag}.csv')
    pd.DataFrame(rows).to_csv(f'out/regime2_power_{tag}.csv', index=False)
    pd.Series(real).to_csv(f'out/regime2_real_{tag}.csv')


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else 'fx'
    if which == 'fx':
        run('EURUSD D1', 'data/CyberCycle_Surrogate_EURUSD_D1.csv',
            0.460, 0.75, 25)
    else:
        run('BTCUSD H4', 'data/CyberCycle_Surrogate_BTCUSD_H4.csv',
            0.523, 0.90, 50, nulls_subset=['A_bootstrap', 'B_fgn', 'D_stochvol'])
