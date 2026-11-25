"""R2 replay (PERF2 P-2): Strategy 2 variant 0 indicator values and slot states from the harness reference models, on the
same Python-built 17:00 New York bars as R1. The engine + M1 layer is r1_replay's (R-D6), unchanged.

Strategy 2 variant 0 (PERF2 slot table; T3 amendment 1):
  baseline FRAMA N = 32 on Price (H+L)/2 with High / Low          (a) TASC V.23:10
  C1       MESA Stochastic (20, 48, 10) on Close vs SMA(10) of its own output, two-lines cross   (a) V.32:1, V18; (c) reading
  C2       Laguerre RSI gamma 0.5 on Close vs 0.5                  (a) Cybernetic Analysis p. 221; (c) reading
  ATR      ATR(14) MT4                                             (a) NNFX [V03, V16]
SMA (PERF2 decision 2a): plain mean of the last n MESA outputs; C1 state 0 until n outputs exist (rows 0 .. n-2).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "analysis", "harness"))
import reference as R  # noqa: E402
import r1_replay as RP  # noqa: E402

replay = RP.replay   # same engine + M1 layer as R1 (R-D6)


def sma_last(x, n):
    """Mean of x[t-n+1 .. t] for t >= n - 1 (summed oldest first, as the Light-C loop); NaN before (no value yet).
    (b) Summation order: the .c loop adds x[n-1] .. x[0] (oldest first); this model does the same, so the two agree
    to rounding of identical operations."""
    x = np.asarray(x, dtype=float)
    out = np.full(len(x), np.nan)
    for t in range(n - 1, len(x)):
        s = 0.0
        for j in range(n - 1, -1, -1):
            s += x[t - j]
        out[t] = s / n
    return out


def indicators(bars, frama_n=32, mesa=(20, 48, 10), sma_n=10, gamma=0.5, atr_len=14):
    """Strategy 2 indicator values on bars (dict of arrays from r1_data.daily_bars, cut to Zorro's first bar)."""
    mid = (bars["h"] + bars["l"]) * 0.5
    fr = R.simulate_frama(R.frama_article(frama_n), mid, H=bars["h"], L=bars["l"])
    ms = R.simulate_mesa(R.mesa_code(*mesa), bars["c"])
    sm = sma_last(ms.out, sma_n)
    lr = R.simulate_lrsi(R.lrsi_article(gamma), bars["c"])
    at = R.simulate_atr(R.atr_mt4(atr_len), bars["c"], bars["h"], bars["l"])
    return dict(frama=fr.out, dim=fr.dim, alpha=fr.alpha, mesa=ms.out, roof=ms.roof, stoc=ms.stoc, sma=sm,
                lrsi=lr.out, l0=lr.l0, l3=lr.l3, den=lr.den, atr=at.atr, tr=at.tr)


def states(ind):
    """Slot states (T3.1): C1 = sign(MESA - SMA), 0 where the SMA has no value yet; C2 = sign(LRSI - 0.5)."""
    sm = np.asarray(ind["sma"])
    d = np.where(np.isnan(sm), 0.0, np.asarray(ind["mesa"]) - np.nan_to_num(sm))
    return dict(baseline=ind["frama"], atr=ind["atr"], c1=np.sign(d).astype(int),
                c2=np.sign(np.asarray(ind["lrsi"]) - 0.5).astype(int))
