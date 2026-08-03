"""
surrogates.py — null-model generators for the Ehlers cycle-premise test.

Every generator returns a PRICE series of the same length as the real one,
so it can be pushed through the identical validated pipeline.

Nulls
-----
A  bootstrap     IID resample of real log-returns -> cumsum.
                 Kills all time-ordering. Keeps the fat-tailed marginal.
B  fgn           Fractional Gaussian noise at DFA-estimated Hurst,
                 amplitude-adjusted to the real return marginal.
                 == Ehlers' own 2015 'market is pink noise' model.
C  iaaft         Iterative amplitude-adjusted Fourier transform.
                 Preserves power spectrum AND marginal exactly; randomises
                 phase. Tests phase coherence, i.e. tradability.
P  fgn+sine      Positive control: Null B plus a known sinusoid at a set
                 SNR. Calibrates detection power.
"""

import numpy as np


# =========================================================================
# Hurst estimation — DFA
# =========================================================================

def dfa_hurst(x, scales=None, order=1):
    """
    Detrended Fluctuation Analysis.

    Preferred over classic rescaled-range (R/S) because R/S is badly biased
    upward on short-memory data, which would inflate H and make Null B an
    artificially strong (unfair) null.

    Returns (H, scales, fluctuations) so the log-log fit can be inspected —
    a DFA estimate quoted without its scaling plot is not trustworthy.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    y = np.cumsum(x - x.mean())          # integrated profile

    if scales is None:
        # log-spaced; floor 8 avoids fit-order artefacts, ceiling n/8 keeps
        # >=8 windows per scale so F(s) stays stable
        scales = np.unique(np.round(
            np.logspace(np.log10(8), np.log10(n // 8), 24)).astype(int))

    fluct = []
    for s in scales:
        n_win = n // s
        if n_win < 8:
            fluct.append(np.nan)
            continue
        # non-overlapping windows, forward and backward for full coverage
        segs = np.concatenate([
            y[:n_win * s].reshape(n_win, s),
            y[n - n_win * s:].reshape(n_win, s)])
        t = np.arange(s)
        resid_var = []
        for seg in segs:
            coef = np.polyfit(t, seg, order)
            resid_var.append(np.mean((seg - np.polyval(coef, t)) ** 2))
        fluct.append(np.sqrt(np.mean(resid_var)))

    fluct = np.array(fluct)
    ok = np.isfinite(fluct) & (fluct > 0)
    H = np.polyfit(np.log(scales[ok]), np.log(fluct[ok]), 1)[0]
    return H, scales[ok], fluct[ok]


# =========================================================================
# helpers
# =========================================================================

def _to_price(log_returns, p0):
    """Log-returns -> price path anchored at p0."""
    return p0 * np.exp(np.concatenate([[0.0], np.cumsum(log_returns)]))


def _amplitude_adjust(x, target_sorted):
    """
    Replace values of x by target values of equal rank.

    Forces the marginal distribution to match the real returns exactly while
    preserving the rank-ordering (and hence most of the dependence structure).
    Without this, a Gaussian null could be rejected merely for lacking fat
    tails — which would tell us nothing about cycles.
    """
    out = np.empty_like(x)
    out[np.argsort(x)] = target_sorted
    return out


# =========================================================================
# Null A — bootstrap random walk
# =========================================================================

def surrogate_bootstrap(returns, p0, rng):
    """IID resample with replacement. Destroys all temporal dependence."""
    r = rng.choice(returns, size=len(returns), replace=True)
    return _to_price(r, p0)


# =========================================================================
# Null B — fractional Gaussian noise (Davies-Harte, exact)
# =========================================================================

def _fgn_davies_harte(n, H, rng):
    """
    Exact fractional Gaussian noise via circulant embedding.

    Exact rather than approximate because an approximate fGn could carry
    spurious spectral structure of its own — which is precisely the artefact
    class this whole experiment exists to detect.
    """
    k = np.arange(n + 1)
    # fGn autocovariance at unit variance
    g = 0.5 * (np.abs(k - 1) ** (2 * H) - 2 * np.abs(k) ** (2 * H)
               + np.abs(k + 1) ** (2 * H))

    # circulant first row of size 2n
    row = np.concatenate([g[:n + 1], g[1:n][::-1]])
    lam = np.fft.fft(row).real
    lam[lam < 0] = 0.0                      # clip tiny negative eigenvalues
    m = len(row)

    w = rng.standard_normal(m) + 1j * rng.standard_normal(m)
    y = np.fft.fft(np.sqrt(lam / (2.0 * m)) * w)
    return y.real[:n]


def surrogate_fgn(returns, p0, H, rng):
    """fGn at Hurst H, amplitude-adjusted to the real return marginal."""
    z = _fgn_davies_harte(len(returns), H, rng)
    r = _amplitude_adjust(z, np.sort(returns))
    return _to_price(r, p0)


# =========================================================================
# Null C — IAAFT
# =========================================================================

def surrogate_iaaft(returns, p0, rng, n_iter=200, tol=1e-8):
    """
    Iterative amplitude-adjusted Fourier transform.

    Alternately enforces (a) the target power spectrum and (b) the target
    marginal, until both hold to numerical precision. Result has the SAME
    spectrum as the real series but randomised phases.

    NOTE ON INTERPRETATION: because the spectrum is preserved, any spectral
    peak is reproduced by construction. This null therefore cannot test
    whether a cycle EXISTS — it tests whether the cycle's PHASE is coherent,
    i.e. whether it could be extrapolated and traded.
    """
    x = np.asarray(returns, dtype=float)
    n = len(x)
    target_amp = np.abs(np.fft.rfft(x))
    target_sorted = np.sort(x)

    y = rng.permutation(x)
    prev = None
    for _ in range(n_iter):
        # (a) impose spectrum, keep current phases
        Y = np.fft.rfft(y)
        phase = np.angle(Y)
        y = np.fft.irfft(target_amp * np.exp(1j * phase), n=n)
        # (b) impose marginal
        y = _amplitude_adjust(y, target_sorted)

        if prev is not None and np.max(np.abs(y - prev)) < tol:
            break
        prev = y.copy()

    return _to_price(y, p0)


# =========================================================================
# Control P — positive control, known cycle injected
# =========================================================================

def surrogate_stochvol(returns, p0, H_vol, rng, s=None):
    """
    Null D — stochastic volatility with long memory.

        r_t = sigma_t * e_t ,  e_t IID (resampled standardised real returns)
        log sigma_t = s * fGn(H_vol)

    Contains NO cycle and NO return-level memory, but DOES reproduce
    volatility clustering. Motivation: DFA on |returns| gave H = 0.658, so
    the long memory in FX lives in volatility, not in returns. Amplitude
    modulation pushed through a resonator can mimic an intermittent cycle —
    an artefact mechanism distinct from Slutsky, untested by nulls A/B/C.

    `s` (log-vol scale) is calibrated externally by calibrate_stochvol_s to
    reproduce the observed DFA exponent of |returns|.
    """
    n = len(returns)
    if s is None:
        s = 0.5
    z = _fgn_davies_harte(n, H_vol, rng)
    z = z / z.std()
    sigma = np.exp(s * z)

    e = rng.choice(returns / returns.std(), size=n, replace=True)
    r = sigma * e

    # Force the marginal to the real returns. Without this the lognormal
    # volatility produces kurtosis ~50 vs the real 2.0, and the null could
    # then be rejected for having the wrong TAILS rather than the wrong
    # cycle structure — a false positive. Rank-ordering (hence the
    # volatility clustering) is preserved.
    r = _amplitude_adjust(r, np.sort(returns))
    return _to_price(r, p0)


def calibrate_stochvol_s(returns, H_vol, target_dfa_abs, rng,
                         grid=None, n_rep=6):
    """
    Find log-vol scale `s` reproducing the observed DFA(|returns|).

    Necessary because the IID multiplier e_t attenuates the volatility
    process's long memory: feeding H_vol straight in would UNDER-shoot the
    target and make Null D a weaker (unfairly easy) null.
    """
    if grid is None:
        grid = np.linspace(0.1, 1.6, 16)
    best, best_err = grid[0], np.inf
    for s in grid:
        est = []
        for _ in range(n_rep):
            p = surrogate_stochvol(returns, 1.0, H_vol, rng, s=s)
            est.append(dfa_hurst(np.abs(np.diff(np.log(p))))[0])
        err = abs(np.mean(est) - target_dfa_abs)
        if err < best_err:
            best, best_err = s, err
    return best, best_err


def surrogate_fgn_plus_sine(returns, p0, H, rng, period=20.0, snr_db=0.0):
    """
    Null B plus a sinusoid of known period at a specified SNR.

    snr_db = 10*log10(sine_power / noise_power), both measured on returns.
    Sweeping snr_db maps the detection threshold of the pipeline+metrics,
    converting a null result from 'we found nothing' into 'a cycle above
    X dB would have been found; none was'.
    """
    z = _fgn_davies_harte(len(returns), H, rng)
    r = _amplitude_adjust(z, np.sort(returns))

    noise_power = np.var(r)
    amp = np.sqrt(2.0 * noise_power * 10.0 ** (snr_db / 10.0))
    t = np.arange(len(r))
    sine = amp * np.sin(2.0 * np.pi * t / period + rng.uniform(0, 2 * np.pi))

    return _to_price(r + sine, p0)
