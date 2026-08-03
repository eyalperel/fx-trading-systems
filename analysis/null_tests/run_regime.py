"""
run_regime.py — regime-conditional extension of the cycle-premise null test.

MOTIVATION
The aggregate test (run_experiment.py / run_btc.py) computes one prominence
per series. If cycles appear only in specific volatility regimes, averaging
across 2,000+ bars would wash them out. This is the most defensible
challenge to the aggregate null result, so it is tested directly.

WHY ROLLING WINDOWS AND NOT REGIME SEGMENTS
Segmenting by volatility state gives median contiguous run lengths of 5-15
bars on both assets, with only 1-8 runs reaching 200 bars. A 10-48 bar
passband cannot be measured in a 5-bar segment. Concatenating same-regime
segments would introduce artificial discontinuities and manufacture spurious
spectral content -- precisely the artefact class under investigation. Rolling
windows use all the data and introduce no splices.

STATISTICS (each computed on the CyberCycle output)
    S1  max window prominence      -> intermittent cycle ANYWHERE
    S2  95th pct window prominence -> same, robust to one outlier window
    S3  Spearman corr(prominence, window volatility)
                                   -> cycling ASSOCIATED with vol regime

POSITIVE CONTROL
Injects a sinusoid only where volatility is in the top tercile, so the
control matches the hypothesis under test rather than a global cycle.
"""

import numpy as np
import pandas as pd
import sys
import time
import warnings

warnings.filterwarnings('ignore')
sys.path.insert(0, 'src')

from scipy import signal
from scipy.stats import spearmanr
from pipeline import full_pipeline_fast
from metrics import BURN_IN
from surrogates import (surrogate_bootstrap, surrogate_fgn, surrogate_iaaft,
                        surrogate_stochvol, _fgn_davies_harte, _amplitude_adjust)

WIN = 250          # window length: >=5 cycles of the 48-bar passband edge
N_SURR = 500


def window_prominence(x, win=WIN, step=25):
    """Peak prominence in the 10-48 bar passband, per rolling window."""
    out = []
    for a in range(0, len(x) - win + 1, step):
        seg = x[a:a + win]
        f, P = signal.welch(seg, nperseg=min(256, len(seg)), detrend='linear')
        f, P = f[1:], P[1:]
        b = (f >= 1.0 / 48) & (f <= 1.0 / 10)
        out.append(P[b].max() / np.median(P[b]) if b.sum() >= 4 else np.nan)
    return np.array(out)


def window_vol(rets, win=WIN, step=25):
    """Mean absolute return per window -- realised volatility proxy."""
    return np.array([np.mean(np.abs(rets[a:a + win]))
                     for a in range(0, len(rets) - win + 1, step)])


def regime_stats(price, step):
    """S1, S2, S3 for one price series."""
    _, cyc, _ = full_pipeline_fast(price)
    c = cyc[BURN_IN:]
    r = np.diff(np.log(price))[BURN_IN:]
    prom = window_prominence(c, WIN, step)
    vol = window_vol(r, WIN, step)
    n = min(len(prom), len(vol))
    prom, vol = prom[:n], vol[:n]
    ok = np.isfinite(prom) & np.isfinite(vol)
    rho = spearmanr(prom[ok], vol[ok]).correlation if ok.sum() > 8 else np.nan
    return {'S1_max_prom': np.nanmax(prom),
            'S2_p95_prom': np.nanpercentile(prom, 95),
            'S3_corr_vol': rho}


def control_regime_cycle(rets, p0, H, rng, period=20.0, snr_db=0.0,
                         vol_win=60):
    """Positive control: cycle injected ONLY in top-tercile volatility bars."""
    n = len(rets)
    z = _fgn_davies_harte(n, H, rng)
    r = _amplitude_adjust(z, np.sort(rets))

    v = pd.Series(np.abs(r)).rolling(vol_win, min_periods=1).mean().values
    mask = (v >= np.nanpercentile(v, 67)).astype(float)

    amp = np.sqrt(2.0 * np.var(r) * 10.0 ** (snr_db / 10.0))
    t = np.arange(n)
    sine = amp * np.sin(2 * np.pi * t / period + rng.uniform(0, 2 * np.pi))
    r = r + sine * mask
    return p0 * np.exp(np.concatenate([[0.0], np.cumsum(r)]))


def run_asset(label, csv, H_ret, H_vol, step, seed=20260803):
    df = pd.read_csv(csv, header=None,
                     names=['bar', 'price', 'roofing', 'cycle', 'trigger'])
    price = df.price.values
    rets = np.diff(np.log(price))
    p0 = price[0]
    rng = np.random.default_rng(seed)

    real = regime_stats(price, step)
    print("=" * 74)
    print(f"{label} — REGIME-CONDITIONAL TEST")
    print("=" * 74)
    for k, v in real.items():
        print(f"  {k:16s} {v:10.4f}")

    nulls = {
        'A_bootstrap': lambda: surrogate_bootstrap(rets, p0, rng),
        'B_fgn':       lambda: surrogate_fgn(rets, p0, H_ret, rng),
        'C_iaaft':     lambda: surrogate_iaaft(rets, p0, rng, n_iter=50),
        'D_stochvol':  lambda: surrogate_stochvol(rets, p0, H_vol, rng, s=1.0),
    }
    res = {}
    for n, g in nulls.items():
        t = time.time()
        res[n] = pd.DataFrame([regime_stats(g(), step) for _ in range(N_SURR)])
        print(f"  {n} done {time.time()-t:.0f}s", flush=True)

    def p2(v, o):
        v = np.asarray(v, float); v = v[np.isfinite(v)]
        return min(1.0, 2 * min((v >= o).mean(), (v <= o).mean()))

    print(f"\n  two-sided rank p-values (N={N_SURR}):")
    print(f"  {'stat':16s}" + "".join(f"{k.split('_')[0]:>10s}" for k in nulls))
    pv = {}
    for k in real:
        pv[k] = {n: p2(d[k].values, real[k]) for n, d in res.items()}
        print(f"  {k:16s}" + "".join(f"{pv[k][n]:10.3f}" for n in nulls))

    print(f"\n  REAL percentile within each null:")
    for k in real:
        print(f"  {k:16s}" + "".join(
            f"{(d[k].values < real[k]).mean()*100:9.1f}%" for d in res.values()))

    # positive control against the strictest null
    thrD = np.percentile(res['D_stochvol']['S1_max_prom'].values, 95)
    print(f"\n  DETECTION POWER, regime-localised cycle (Null-D S1 95th = {thrD:.2f}):")
    rows = []
    for snr in [-20, -16, -14, -12, -10, -6]:
        s = np.array([regime_stats(
            control_regime_cycle(rets, p0, H_ret, rng, 20.0, snr), step)['S1_max_prom']
            for _ in range(120)])
        rows.append({'snr_db': snr, 'detect_rate': (s > thrD).mean()})
        print(f"    SNR {snr:+4d} dB  detect {(s>thrD).mean():.3f}")

    pd.DataFrame(pv).to_csv(f'out/regime_pvalues_{label.split("/")[0]}.csv')
    pd.DataFrame(rows).to_csv(f'out/regime_power_{label.split("/")[0]}.csv',
                              index=False)
    pd.Series(real).to_csv(f'out/regime_real_{label.split("/")[0]}.csv')
    return real, res


if __name__ == "__main__":
    run_asset('EURUSD D1', 'data/CyberCycle_Surrogate_EURUSD_D1.csv',
              0.460, 0.75, step=25)
    print()
    run_asset('BTCUSD H4', 'data/CyberCycle_Surrogate_BTCUSD_H4.csv',
              0.523, 0.90, step=50)
