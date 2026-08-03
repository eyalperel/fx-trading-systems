"""
metrics.py — detection statistics computed on the CyberCycle output.

Every metric is computed identically on real and surrogate series, on bars
BURN_IN onward, so the zero-state IIR transient (measured at ~200 bars in the
port validation) cannot contribute to any difference.

The discriminating metric is peak_prominence. A genuine cycle gives a TALL,
NARROW spectral peak. A Slutsky/filter artefact gives a BROAD, LOW bump at
the filter's resonant frequency. Both yield a 'dominant period' if you take
an argmax — only the first is a cycle. Prominence separates them; argmax
does not.
"""

import numpy as np
from scipy import signal

BURN_IN = 300          # discard IIR transient (zero-state + lfilter startup)
FS = 1.0               # 1 sample per bar


def welch_psd(x, nperseg=512):
    """Welch PSD, linear-detrended. Returns (freq, power) excluding DC."""
    f, P = signal.welch(x, fs=FS, nperseg=min(nperseg, len(x)),
                        detrend='linear')
    return f[1:], P[1:]


def dominant_period(x):
    """Period at maximum spectral power. Always returns something — that is
    the point: an argmax over a smooth spectrum still reports a 'cycle'."""
    f, P = welch_psd(x)
    return 1.0 / f[np.argmax(P)]


def peak_prominence(x):
    """
    Peak PSD divided by the MEDIAN PSD over the filter passband (10-48 bars).

    Median rather than mean: the mean is dragged up by the peak itself,
    which would understate prominence exactly when a real cycle is present.
    Restricted to the passband because power outside it has been filtered
    away by construction and would inflate the ratio artificially.
    """
    f, P = welch_psd(x)
    band = (f >= 1.0 / 48) & (f <= 1.0 / 10)
    if band.sum() < 4:
        return np.nan
    return P[band].max() / np.median(P[band])


def zero_cross_period(x):
    """
    Mean period from zero crossings (2 x mean half-cycle length).

    Independent of the spectral estimate, so it cross-checks
    dominant_period: a real oscillation agrees on both, a broadband
    process need not.
    """
    s = np.sign(x - np.mean(x))
    idx = np.where(np.diff(s) != 0)[0]
    if len(idx) < 3:
        return np.nan
    return 2.0 * np.mean(np.diff(idx))


def period_stability(x, win=250, step=25):
    """
    Std of the dominant period measured in rolling windows.

    A tradable cycle must hold its period long enough to extrapolate.
    High variance here means the 'dominant cycle' is a wandering argmax,
    which is unusable regardless of how strong it looks in aggregate.
    """
    per = []
    for a in range(0, len(x) - win, step):
        seg = x[a:a + win]
        f, P = signal.welch(seg, fs=FS, nperseg=min(256, len(seg)),
                            detrend='linear')
        f, P = f[1:], P[1:]
        band = (f >= 1.0 / 48) & (f <= 1.0 / 10)
        if band.sum() >= 4:
            per.append(1.0 / f[band][np.argmax(P[band])])
    return np.std(per) if len(per) > 2 else np.nan


def acf_at_half_period(x):
    """
    Autocorrelation at half the dominant period.

    A genuine oscillation MUST be strongly negatively autocorrelated half a
    cycle away (peak aligns with trough). Broadband noise shaped by a filter
    need not be. Returned negated so that LARGER = MORE cyclical, keeping
    all metrics oriented the same way.
    """
    p = dominant_period(x)
    lag = int(round(p / 2))
    if lag < 1 or lag >= len(x) // 4:
        return np.nan
    y = x - x.mean()
    denom = np.dot(y, y)
    return -np.dot(y[:-lag], y[lag:]) / denom if denom > 0 else np.nan


def rms_amplitude(x):
    """RMS of the oscillator output — how large the swings are."""
    return float(np.std(x, ddof=1))


METRICS = {
    'dominant_period':  dominant_period,
    'peak_prominence':  peak_prominence,
    'zero_cross_period': zero_cross_period,
    'period_stability': period_stability,
    'acf_half_period':  acf_at_half_period,
    'rms_amplitude':    rms_amplitude,
}


def compute_all(cycle_output, burn_in=BURN_IN):
    """All metrics on one CyberCycle output, post burn-in."""
    x = np.asarray(cycle_output, dtype=float)[burn_in:]
    return {k: fn(x) for k, fn in METRICS.items()}
