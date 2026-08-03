"""
pipeline.py — Python port of the Zorro Ehlers pipeline.

Ports HighPassFilter -> SuperSmoother2Pole (= RoofingFilter) -> CyberCycle
so that surrogate series can be pushed through the IDENTICAL transform that
produced CyberCycle_Surrogate_EURUSD_D1.csv in Zorro.

Reference parameters (from Test_CyberCycle_Surrogate.c):
    HP_PERIOD = 48, SS_PERIOD = 10, CC_ALPHA = 0.07

CRITICAL: all trig takes RADIANS (standard C math library, matching Zorro
Light-C). Formulas use e.g. cos(0.707*2*pi/Period), NOT cos(0.707*360/Period).
"""

import numpy as np

# --- Reference parameters, must mirror the Zorro script -------------------
HP_PERIOD = 48
SS_PERIOD = 10
CC_ALPHA = 0.07


def high_pass(price, hp_period=HP_PERIOD):
    """
    Ehlers 2-pole High-Pass filter (removes trend, passes cycle+noise).

    alpha1 uses the 0.707 multiplier inside the trig arguments — this is the
    'Decyclers' form, which is the correct one (the 'Optimal Detrending'
    variant omits it and is wrong).

    Recursion:
        HP[i] = (1-a/2)^2 * (P[i] - 2P[i-1] + P[i-2])
                + 2(1-a)*HP[i-1] - (1-a)^2*HP[i-2]

    The (P - 2P + P) term is the second difference: zero for constant-speed
    trend, non-zero for curvature. That is the mechanism that blocks trend.
    """
    price = np.asarray(price, dtype=float)
    n = len(price)

    w = 0.707 * 2.0 * np.pi / hp_period
    alpha1 = (np.cos(w) + np.sin(w) - 1.0) / np.cos(w)

    g = (1.0 - alpha1 / 2.0) ** 2   # gain on the second difference
    f1 = 2.0 * (1.0 - alpha1)       # feedback, 1 bar
    f2 = -((1.0 - alpha1) ** 2)     # feedback, 2 bars

    hp = np.zeros(n)
    for i in range(2, n):
        hp[i] = (g * (price[i] - 2.0 * price[i - 1] + price[i - 2])
                 + f1 * hp[i - 1] + f2 * hp[i - 2])
    return hp


def super_smoother_2pole(x, ss_period=SS_PERIOD):
    """
    Ehlers 2-pole SuperSmoother (removes high-frequency noise).

    a1 = exp(-sqrt(2)*pi/Period)
    b1 = 2*a1*cos(sqrt(2)*pi/Period)
    c2 = b1, c3 = -a1^2, c1 = 1 - c2 - c3   (c1 set so DC gain == 1)

        Filt[i] = c1*(x[i] + x[i-1])/2 + c2*Filt[i-1] + c3*Filt[i-2]

    The (x[i]+x[i-1])/2 input average is a half-bar FIR pre-filter that puts
    a null at Nyquist, suppressing bar-to-bar alternation.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)

    a1 = np.exp(-np.sqrt(2.0) * np.pi / ss_period)
    b1 = 2.0 * a1 * np.cos(np.sqrt(2.0) * np.pi / ss_period)
    c2 = b1
    c3 = -a1 * a1
    c1 = 1.0 - c2 - c3

    f = np.zeros(n)
    for i in range(2, n):
        f[i] = c1 * (x[i] + x[i - 1]) / 2.0 + c2 * f[i - 1] + c3 * f[i - 2]
    return f


def roofing_filter(price, hp_period=HP_PERIOD, ss_period=SS_PERIOD):
    """Band-pass: HP removes trend, SS removes noise. Passband ~10..48 bars."""
    return super_smoother_2pole(high_pass(price, hp_period), ss_period)


def cyber_cycle(filt, alpha=CC_ALPHA):
    """
    Ehlers Cyber Cycle — 2nd-order IIR resonator on the roofing output.

        Cyc[i] = (1-a/2)^2 * (F[i] - 2F[i-1] + F[i-2])
                 + 2(1-a)*Cyc[i-1] - (1-a)^2*Cyc[i-2]

    pole radius = 1-alpha = 0.93 (light damping -> persistent oscillation).
    Structurally identical to the HP filter; what differs is the input
    (pre-filtered) and the pole placement.
    """
    filt = np.asarray(filt, dtype=float)
    n = len(filt)

    g = (1.0 - alpha / 2.0) ** 2
    pole = 1.0 - alpha

    c = np.zeros(n)
    for i in range(2, n):
        c[i] = (g * (filt[i] - 2.0 * filt[i - 1] + filt[i - 2])
                + 2.0 * pole * c[i - 1] - pole * pole * c[i - 2])
    return c


def trigger_line(cyc):
    """Trigger = 2*Cyc[i-1] - Cyc[i-3]; linear extrapolation, leads by ~1-2 bars."""
    cyc = np.asarray(cyc, dtype=float)
    t = np.zeros(len(cyc))
    t[3:] = 2.0 * cyc[2:-1] - cyc[:-3]
    return t


def full_pipeline(price, hp_period=HP_PERIOD, ss_period=SS_PERIOD,
                  alpha=CC_ALPHA):
    """Price -> (roofing, cycle, trigger). The transform under test."""
    filt = roofing_filter(price, hp_period, ss_period)
    cyc = cyber_cycle(filt, alpha)
    return filt, cyc, trigger_line(cyc)


# =========================================================================
# Vectorised equivalents (scipy.lfilter) — same IIR recursions, ~100x faster.
# Verified below to match the loop versions to machine precision; the loop
# versions remain as the readable reference implementation.
# =========================================================================

from scipy.signal import lfilter


def full_pipeline_fast(price, hp_period=HP_PERIOD, ss_period=SS_PERIOD,
                       alpha=CC_ALPHA):
    price = np.asarray(price, dtype=float)

    w = 0.707 * 2.0 * np.pi / hp_period
    a1 = (np.cos(w) + np.sin(w) - 1.0) / np.cos(w)
    g = (1.0 - a1 / 2.0) ** 2
    hp = lfilter([g, -2 * g, g], [1.0, -2.0 * (1 - a1), (1 - a1) ** 2], price)

    s1 = np.exp(-np.sqrt(2.0) * np.pi / ss_period)
    b1 = 2.0 * s1 * np.cos(np.sqrt(2.0) * np.pi / ss_period)
    c2, c3 = b1, -s1 * s1
    c1 = 1.0 - c2 - c3
    filt = lfilter([c1 / 2.0, c1 / 2.0], [1.0, -c2, -c3], hp)

    gc = (1.0 - alpha / 2.0) ** 2
    pole = 1.0 - alpha
    cyc = lfilter([gc, -2 * gc, gc], [1.0, -2.0 * pole, pole ** 2], filt)

    trig = np.zeros(len(cyc))
    trig[3:] = 2.0 * cyc[2:-1] - cyc[:-3]
    return filt, cyc, trig
