# indicator_metrics.py
# Purpose: Reusable validation metrics for Ehlers indicator library
# Used by: Indicator_Analysis_Template.ipynb (every indicator in Weeks 5-14)
# Author: Gusbi
# Created: Week 4 Day 3

import numpy as np
import pandas as pd


def calculate_lag(price: pd.Series, indicator: pd.Series, max_lag: int = 50) -> dict:
    """
    Measures how many bars the indicator lags behind price using cross-correlation.

    Cross-correlation slides the indicator forward/backward in time relative to price
    and finds the offset (lag) where the two series are most similar to each other.

    Parameters
    ----------
    price     : raw price series (e.g. Close prices)
    indicator : smoothed indicator output series
    max_lag   : how many bars forward/backward to search (default 50)

    Returns
    -------
    dict with:
        'lag_bars'    : int   — bars of lag detected
        'correlation' : float — strength of match at that lag (0 to 1)
    """

    # Step 1: Align the two series and drop any NaN rows
    # NaNs appear at the start of indicator series during the warmup period
    df = pd.DataFrame({'price': price, 'indicator': indicator}).dropna()

    # Step 2: Subtract the mean from each series (zero-centering)
    # This removes the effect of different absolute price levels
    # e.g. EUR/USD ~1.10 vs BTC ~40000 — without this, the scale difference
    # would dominate the correlation calculation
    p = df['price'] - df['price'].mean()
    ind = df['indicator'] - df['indicator'].mean()

    # Step 3: Compute cross-correlation at each lag offset from 0 to max_lag
    # We only search positive lags (indicator behind price, not ahead)
    # because a smoothed indicator can never lead price — only lag it
    correlations = []
    for k in range(0, max_lag + 1):
        if k == 0:
            # No shift — compare series as-is
            r = np.corrcoef(p, ind)[0, 1]
        else:
            # Shift indicator forward by k bars
            # p[k:] aligns with ind[:-k] — we're asking:
            # "if price moved k bars ago, does the indicator reflect it now?"
            r = np.corrcoef(p[k:], ind[:-k])[0, 1]
        correlations.append(r)

    # Step 4: The lag is the offset where correlation is highest
    lag_bars = int(np.argmax(correlations))
    best_correlation = float(correlations[lag_bars])

    return {
        'lag_bars': lag_bars,
        'correlation': round(best_correlation, 4)
    }


def calculate_lag_oscillator(price: pd.Series, indicator: pd.Series, max_lag: int = 50) -> dict:
    """
    Measures lag/lead of an OSCILLATOR-type indicator (detrended, mean-reverting)
    relative to price — as opposed to calculate_lag(), which is built for
    trend-following smoothers that track price level directly.

    Two corrections vs calculate_lag(), both needed for indicators like Reflex,
    Cyber Cycle, or MESA Stochastic:

    1. First-differences price before correlating. Week 5 finding: standard
       cross-correlation fails on trending data because the shared trend
       dominates and masks true lag. calculate_lag() only zero-centers
       (subtracts the mean), which does not remove a trend. First-differencing
       does. This matters here because price is non-stationary/trending while
       an oscillator like Reflex is stationary — correlating them directly
       compares two series with fundamentally different statistical character.

    2. Searches negative lags as well as positive. calculate_lag() only
       searches forward (indicator can only lag, never lead) — a correct
       assumption for smoothers, but exactly the assumption an indicator like
       Reflex is explicitly designed to violate (its whole claim is zero lag
       or lead at cycle turning points). This function searches both
       directions so a genuine lead isn't floored at zero.

    Parameters
    ----------
    price     : raw price series (e.g. Close prices)
    indicator : oscillator output series
    max_lag   : bars to search in each direction (default 50)

    Returns
    -------
    dict with:
        'lag_bars'      : int   — negative = indicator LEADS price,
                                   positive = indicator LAGS price,
                                   0 = in-phase
        'correlation'   : float — strength of match at that offset
        'interpretation': str   — 'leads' / 'lags' / 'in-phase'
    """
    df = pd.DataFrame({'price': price, 'indicator': indicator}).dropna()

    # First-difference price to remove trend (Week 5 finding)
    p = df['price'].diff().values[1:]
    ind = df['indicator'].values[1:]  # align length with differenced price

    p = p - p.mean()
    ind = ind - ind.mean()
    n = len(p)

    correlations = {}
    for k in range(-max_lag, max_lag + 1):
        if k == 0:
            a, b = p, ind
        elif k > 0:
            # indicator LAGS price by k bars
            a, b = p[:n - k], ind[k:]
        else:
            kk = -k
            # indicator LEADS price by kk bars
            a, b = p[kk:], ind[:n - kk]
        if len(a) < 10:
            continue
        correlations[k] = np.corrcoef(a, b)[0, 1]

    best_k = max(correlations, key=lambda k: correlations[k])
    interpretation = 'leads' if best_k < 0 else ('lags' if best_k > 0 else 'in-phase')

    return {
        'lag_bars': best_k,
        'correlation': round(correlations[best_k], 4),
        'interpretation': interpretation
    }


def calculate_snr(price: pd.Series, indicator: pd.Series, period: int) -> dict:
    """
    Measures how much noise the indicator removes compared to raw price,
    and benchmarks it against a simple SMA of the same period.

    SNR = std(indicator) / std(price - indicator)

    A higher SNR means the indicator is smoother relative to the noise it removes.
    We compare to SMA(period) as the baseline — any indicator should beat this.

    Parameters
    ----------
    price     : raw price series
    indicator : smoothed indicator output series
    period    : the period used by the indicator (used to build SMA benchmark)

    Returns
    -------
    dict with:
        'snr_indicator' : float — SNR of the indicator
        'snr_sma'       : float — SNR of a plain SMA (same period) as benchmark
        'snr_improvement' : float — how much better indicator is vs SMA (ratio)
        'passes'        : bool  — True if indicator SNR > SMA SNR
    """

    # Step 1: Align and drop NaNs
    sma = price.rolling(window=period).mean()
    df = pd.DataFrame({
        'price': price,
        'indicator': indicator,
        'sma': sma
    }).dropna()

    # Step 2: Calculate noise for each series
    # Noise = what the smoother couldn't explain = price minus the smooth output
    # A good smoother leaves very little noise (small residual)
    noise_indicator = df['price'] - df['indicator']
    noise_sma = df['price'] - df['sma']

    # Step 3: Calculate SNR for indicator and SMA
    # std(indicator) = how much the signal itself varies (we want this to be meaningful)
    # std(noise)     = how much leftover noise there is (we want this small)
    # Higher ratio = better noise reduction
    snr_indicator = df['indicator'].std() / noise_indicator.std()
    snr_sma = df['sma'].std() / noise_sma.std()

    # Step 4: How much better is the indicator vs the SMA?
    # ratio > 1.0 means the indicator beats the SMA on noise reduction
    # ratio < 1.0 means the SMA is actually smoother — indicator FAILS this test
    snr_improvement = snr_indicator / snr_sma

    return {
        'snr_indicator': round(snr_indicator, 4),
        'snr_sma': round(snr_sma, 4),
        'snr_improvement': round(snr_improvement, 4),
        'passes': bool(snr_indicator > snr_sma)
    }


def compare_fx_crypto(
    fx_price: pd.Series,
    fx_indicator: pd.Series,
    crypto_price: pd.Series,
    crypto_indicator: pd.Series,
    period: int
) -> dict:
    """
    Compares indicator behavior on FX (EUR/USD D1) vs Crypto (BTC/USD H4).

    Direct comparison is impossible because FX prices (~1.10) and crypto prices
    (~40,000) are on completely different scales. We normalize both to z-scores
    first, then compare behavior metrics side by side.

    Z-score normalization: z = (value - mean) / std
    After this, both series have mean=0 and std=1, making them directly comparable.

    Parameters
    ----------
    fx_price        : EUR/USD close price series
    fx_indicator    : indicator output on EUR/USD
    crypto_price    : BTC/USD close price series
    crypto_indicator: indicator output on BTC/USD
    period          : indicator period (for SMA benchmark)

    Returns
    -------
    dict with side-by-side metrics for FX and Crypto:
        'fx_lag_bars'         : int
        'crypto_lag_bars'     : int
        'fx_snr_improvement'  : float
        'crypto_snr_improvement': float
        'fx_indicator_std'    : float  — volatility of indicator on FX (normalized)
        'crypto_indicator_std': float  — volatility of indicator on Crypto (normalized)
        'recommendation'      : str    — plain English summary
    """

    # Step 1: Z-score normalize both indicator series
    # This removes the scale difference between FX and crypto prices
    # so we're comparing apples to apples
    def zscore(series: pd.Series) -> pd.Series:
        return (series - series.mean()) / series.std()

    fx_ind_norm = zscore(fx_indicator.dropna())
    crypto_ind_norm = zscore(crypto_indicator.dropna())

    # Step 2: Run lag calculation on both
    fx_lag = calculate_lag(fx_price, fx_indicator)
    crypto_lag = calculate_lag(crypto_price, crypto_indicator)

    # Step 3: Run SNR calculation on both
    fx_snr = calculate_snr(fx_price, fx_indicator, period)
    crypto_snr = calculate_snr(crypto_price, crypto_indicator, period)

    # Step 4: Compare normalized indicator volatility
    # Higher std on crypto means the indicator moves more — expected due to
    # crypto's higher volatility. If crypto std is similar to FX, the indicator
    # may be over-smoothing and missing crypto's faster cycles.
    fx_std = round(float(fx_ind_norm.std()), 4)
    crypto_std = round(float(crypto_ind_norm.std()), 4)

    # Step 5: Build a plain English recommendation
    lag_diff = crypto_lag['lag_bars'] - fx_lag['lag_bars']
    if lag_diff > 2:
        rec = "Indicator lags more on crypto — consider reducing period for BTC/USD."
    elif lag_diff < -2:
        rec = "Indicator is faster on crypto — current period may be too sensitive."
    else:
        rec = "Lag is consistent across FX and crypto — same period likely works for both."

    return {
        'fx_lag_bars': fx_lag['lag_bars'],
        'crypto_lag_bars': crypto_lag['lag_bars'],
        'fx_snr_improvement': fx_snr['snr_improvement'],
        'crypto_snr_improvement': crypto_snr['snr_improvement'],
        'fx_indicator_std': fx_std,
        'crypto_indicator_std': crypto_std,
        'recommendation': rec
    }


def generate_validation_report(
    indicator_name: str,
    price_fx: pd.Series,
    indicator_fx: pd.Series,
    price_crypto: pd.Series,
    indicator_crypto: pd.Series,
    period: int
) -> dict:
    """
    Runs all validation metrics and produces a single PASS/FAIL verdict.

    This is the top-level function called at the end of every indicator's
    Jupyter analysis notebook. It aggregates calculate_lag, calculate_snr,
    and compare_fx_crypto into one unified report.

    PASS criteria (ALL must be true):
      1. Indicator lag <= SMA lag of same period on FX
      2. Indicator lag <= SMA lag of same period on Crypto
      3. SNR improvement > 1.0 on FX (beats plain SMA)
      4. SNR improvement > 1.0 on Crypto (beats plain SMA)

    Parameters
    ----------
    indicator_name  : string label for the report header
    price_fx        : EUR/USD close price series
    indicator_fx    : indicator output on EUR/USD
    price_crypto    : BTC/USD close price series
    indicator_crypto: indicator output on BTC/USD
    period          : indicator period (used for SMA benchmark throughout)

    Returns
    -------
    dict with all metrics + final verdict, also prints formatted report to console
    """

    # Step 1: Build SMA benchmark series for lag comparison
    # This is the baseline every indicator must beat or match
    sma_fx = price_fx.rolling(window=period).mean()
    sma_crypto = price_crypto.rolling(window=period).mean()

    # Step 2: Calculate SMA lag on both assets
    # We compare indicator lag directly against this number
    sma_lag_fx = calculate_lag(price_fx, sma_fx)
    sma_lag_crypto = calculate_lag(price_crypto, sma_crypto)

    # Step 3: Calculate indicator lag on both assets
    ind_lag_fx = calculate_lag(price_fx, indicator_fx)
    ind_lag_crypto = calculate_lag(price_crypto, indicator_crypto)

    # Step 4: Calculate SNR on both assets
    snr_fx = calculate_snr(price_fx, indicator_fx, period)
    snr_crypto = calculate_snr(price_crypto, indicator_crypto, period)

    # Step 5: Cross-asset comparison
    cross = compare_fx_crypto(
        price_fx, indicator_fx,
        price_crypto, indicator_crypto,
        period
    )

    # Step 6: Apply PASS/FAIL criteria
    # Each criterion is evaluated independently so you can see exactly
    # which test failed if the indicator doesn't pass overall
    criteria = {
        'lag_ok_fx':     ind_lag_fx['lag_bars'] <= sma_lag_fx['lag_bars'],
        'lag_ok_crypto': ind_lag_crypto['lag_bars'] <= sma_lag_crypto['lag_bars'],
        'snr_ok_fx':     snr_fx['passes'],
        'snr_ok_crypto': snr_crypto['passes'],
    }

    # Overall verdict: ALL criteria must pass
    overall_pass = all(criteria.values())
    verdict = "✅ PASS — indicator approved for library" if overall_pass else "❌ FAIL — do not add to library"

    # Step 7: Print formatted report to console
    # This is what you'll see at the bottom of every Jupyter notebook
    print("=" * 60)
    print(f"  VALIDATION REPORT: {indicator_name}  (period={period})")
    print("=" * 60)

    print("\n--- LAG (bars) ---")
    print(f"  FX    — Indicator: {ind_lag_fx['lag_bars']} bars | SMA: {sma_lag_fx['lag_bars']} bars  →  {'✅' if criteria['lag_ok_fx'] else '❌'}")
    print(f"  Crypto— Indicator: {ind_lag_crypto['lag_bars']} bars | SMA: {sma_lag_crypto['lag_bars']} bars  →  {'✅' if criteria['lag_ok_crypto'] else '❌'}")

    print("\n--- SNR IMPROVEMENT vs SMA ---")
    print(f"  FX    — {snr_fx['snr_improvement']:.4f}x  →  {'✅' if criteria['snr_ok_fx'] else '❌'}")
    print(f"  Crypto— {snr_crypto['snr_improvement']:.4f}x  →  {'✅' if criteria['snr_ok_crypto'] else '❌'}")

    print("\n--- CROSS-ASSET ---")
    print(f"  {cross['recommendation']}")

    print("\n--- VERDICT ---")
    print(f"  {verdict}")
    print("=" * 60)

    # Step 8: Return everything as a dict so the notebook can store results
    # and build a comparison table across indicators over Weeks 5-14
    return {
        'indicator_name': indicator_name,
        'period': period,
        'fx_lag_bars': ind_lag_fx['lag_bars'],
        'crypto_lag_bars': ind_lag_crypto['lag_bars'],
        'sma_lag_fx': sma_lag_fx['lag_bars'],
        'sma_lag_crypto': sma_lag_crypto['lag_bars'],
        'snr_improvement_fx': snr_fx['snr_improvement'],
        'snr_improvement_crypto': snr_crypto['snr_improvement'],
        'cross_asset': cross,
        'criteria': criteria,
        'passes': overall_pass,
        'verdict': verdict
    }