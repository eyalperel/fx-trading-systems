"""Reference model for linear filters (harness step 2, stage 1).

Implements docs/harness/STEP2_HANDOFF.md, Stage 1 (design: docs/harness/HARNESS_DESIGN.md).
Computes expected values for a linear IIR filter from a formula, never by reading a .c file's
output. The one place a .c file is read is `ss2_code`, whose coefficient lines are quoted below.

Filter form (direct form):   y[n] = sum_k b[k]*x[n-k]  +  sum_k a[k-1]*y[n-k]   (k = 1..)
    b = (b0, b1, ...)      feed-forward taps, b[k] multiplies x[n-k]
    a = (a1, a2, ...)      feedback taps,     a[k-1] multiplies y[n-k]
    H(z) = B(z^-1) / (1 - A(z^-1)),  evaluated at z^-1 = exp(-j*w).

Labels: (a) source states; (b) measured/verified here; (c) inference.
"""
import math
from collections import namedtuple

import numpy as np

Filter = namedtuple("Filter", "b a")

# --------------------------------------------------------------------------------------
# Literal-constant replacement table (HARNESS_DESIGN D1, literal-constant rule).
# literal, exact value used by ss2_article, source.
# --------------------------------------------------------------------------------------
LITERAL_REPLACEMENTS = [
    # (literal as printed, exact replacement, source / label)
    ("1.414",   math.sqrt(2.0), "sqrt(2). Equals the named constant to every printed digit only after "
                                "rounding to 4 sig. digits (1.41421...->1.414); HARNESS_DESIGN D1 "
                                "decided (ii): replace. Article: TASC V.42:04 (a, as quoted in D1)."),
    ("3.14159", math.pi,        "pi. TASC V.42:04 (a, as quoted in D1); D1 rule 1."),
]
# `Cosine(1.414*180/Period)` is in degrees in the article, = cos(sqrt(2)*pi/Period) in radians.

# Zorro's PI macro: `#define PI 3.14159` (gotchas 9d.2, b), but the value actually used is
# float32(3.14159) = 3.141590118... (gotchas 9d.1/9d.2, b).
PI_ZORRO = float(np.float32(3.14159))

# --------------------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------------------


def _ss2_from(period, pi_exp, pi_cos, root2):
    c1 = math.exp(-root2 * pi_exp / period)
    b1 = 2.0 * c1 * math.cos(root2 * pi_cos / period)
    c3 = -c1 * c1
    c0 = (1.0 - b1 + c1 * c1) / 2.0
    return c0, b1, c3, c1


def ss2_article(period):
    """SuperSmoother 2-pole from the article formula with the D1 replacements.

    The D1 replacements (1.414 -> sqrt(2), 3.14159 -> pi) are in LITERAL_REPLACEMENTS. The
    cosine argument is 1.414*180/Period degrees = sqrt(2)*pi/Period radians.
    (a) Source: TASC V.42:04, sidebar "SuperSmoother Function, In EasyLanguage" (STEP2_HANDOFF
    Amendment 1, A1.3): a1 = expvalue(-1.414*3.14159 / Period); b1 = 2*a1*Cosine(1.414*180 /
    Period); c2 = b1; c3 = -a1*a1; c1 = 1 - c2 - c3. The article's output equation is
    Filt = c1*(Price+Price[1])/2 + c2*Filt[1] + c3*Filt[2] and equals the .c's
    c0*(P0+P1) with c0 = (1-b1+a1^2)/2 (b: identical to rounding, test_01/test_02).
    """
    root2, pi = math.sqrt(2.0), math.pi
    a1 = math.exp(-root2 * pi / period)
    b1 = 2.0 * a1 * math.cos(root2 * pi / period)
    c2, c3 = b1, -a1 * a1
    c1 = 1.0 - c2 - c3
    return Filter(b=(c1 / 2.0, c1 / 2.0), a=(c2, c3))


def ss2_code(period, pi_value=PI_ZORRO, c1_scale=None, c1_bump=0, in_bump=0):
    """SuperSmoother 2-pole exactly as indicators/ehlers/SuperSmoother2Pole.c computes it.

    Quoted verbatim from the .c (b: read in this session):
        L3:  var c1 = exp(-sqrt(2.0) * PI / Period);
        L4:  var b1 = 2.0 * c1 * cos(sqrt(2.0) * PI / Period);
        L5:  var c2 = b1;
        L6:  var c3 = -c1 * c1;
        L7:  var c0 = (1.0 - b1 + c1 * c1) / 2.0;
        L20: Filt[0] = c0 * (Price[0] + Price[1])
        L21:         + c2 * Filt[1]
        L22:         + c3 * Filt[2];
    PI is used inside BOTH the exponent (L3) and the cosine (L4). pi_value defaults to Zorro's
    float32(3.14159) (gotchas 9d.1/9d.2, b); pass math.pi for the exact-pi form, which is what
    H1's EXPECT table was computed with (h1_check.py coeffs()).

    Negative-control hooks (default off; used only by the self-test):
      c1_bump  NC-A: add `c1_bump` units in the 3rd significant digit of c1 BEFORE b1, c3, c0
               are derived from it (L3 changed; L4-L7 follow, so DC gain stays 1).
      in_bump  NC-B: add `in_bump` units in the 3rd significant digit of c0 AFTER all
               coefficients are computed; both input taps (L20, same c0) change, so DC gain != 1.
    """
    root2 = math.sqrt(2.0)
    c1 = math.exp(-root2 * pi_value / period)
    if c1_bump:
        c1 = bump3(c1, c1_bump)
    b1 = 2.0 * c1 * math.cos(root2 * pi_value / period)
    c2 = b1
    c3 = -c1 * c1
    c0 = (1.0 - b1 + c1 * c1) / 2.0
    if in_bump:
        c0 = bump3(c0, in_bump)
    return Filter(b=(c0, c0), a=(c2, c3))


def bump3(v, units=1):
    """Add `units` to the 3rd significant digit of v (e.g. 0.8007 -> 0.8017)."""
    step = 10.0 ** (math.floor(math.log10(abs(v))) - 2)
    return v + units * step


def ema(alpha):
    """y[n] = alpha*x[n] + (1-alpha)*y[n-1]. Measuring-tool known answer (CLAUDE.md §4.5)."""
    return Filter(b=(alpha,), a=(1.0 - alpha,))


# --------------------------------------------------------------------------------------
# Analytic measurements
# --------------------------------------------------------------------------------------


def _hz(f, w):
    """H at z^-1 = exp(-j*w)."""
    zi = np.exp(-1j * w)
    num = sum(bk * zi ** k for k, bk in enumerate(f.b))
    den = 1.0 - sum(ak * zi ** (k + 1) for k, ak in enumerate(f.a))
    return num / den


def dc_gain(f):
    return float(abs(_hz(f, 0.0)))


def gain_at(f, t):
    """Steady-state gain for a sine of period t bars: |H(exp(-j*2*pi/t))|."""
    return float(abs(_hz(f, 2.0 * math.pi / t)))


def ramp_lag(f):
    """Ramp lag = group delay at w -> 0, closed form (bars).

    tau = sum(k*b_k)/sum(b_k) + sum(k*a_k)/(1 - sum(a_k)),  a_k the feedback taps (k >= 1).
    Derivation: delay(N) = sum k b_k / sum b_k for N = sum b_k z^-k; D = 1 - sum a_k z^-k has
    delay sum k (-a_k) / (1 - sum a_k) and enters with a minus sign. (b: verified against
    simulation in test_reference.py.)
    """
    sb = sum(f.b)
    num = sum(k * bk for k, bk in enumerate(f.b)) / sb
    sa = sum(f.a)
    den = sum((k + 1) * ak for k, ak in enumerate(f.a)) / (1.0 - sa)
    return float(num + den)


# --------------------------------------------------------------------------------------
# Simulation (cross-check only) -- measurement logic copied from analysis/harness/h1_check.py
# (simulate(), m_gain(), m_lag(), make_inputs()); H1 files are not modified.
# --------------------------------------------------------------------------------------
N_BARS = 3000
W = 500                 # h1_check.W
FLAT_LEVEL = 1.1        # h1_check.FLAT_LEVEL
AMP = 0.01              # h1_check.AMP
RAMP_SLOPE = 0.0001     # h1_check.RAMP_SLOPE


def simulate(f, x):
    """Run the recursion on array x. Seeds y[-k] = x[0], x[-k] = x[0] (as h1_check.simulate)."""
    x = np.asarray(x, dtype=float)
    y = np.empty(len(x))
    nb, na = len(f.b), len(f.a)
    for n in range(len(x)):
        acc = 0.0
        for k in range(nb):
            acc += f.b[k] * (x[n - k] if n - k >= 0 else x[0])
        for k in range(na):
            acc += f.a[k] * (y[n - k - 1] if n - k - 1 >= 0 else x[0])
        y[n] = acc
    return y


def sim_gain(f, t, n_bars=N_BARS, w=W):
    """Least-squares sine gain on the simulated output (h1_check.m_gain)."""
    n = np.arange(n_bars, dtype=float)
    x = FLAT_LEVEL + AMP * np.sin(2 * math.pi * n / t)
    y = simulate(f, x)[w:]
    ww = 2 * math.pi * n[w:] / t
    A = np.column_stack([np.sin(ww), np.cos(ww), np.ones_like(ww)])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return float(math.hypot(coef[0], coef[1]) / AMP)


def sim_lag(f, n_bars=N_BARS):
    """Mean (x - y)/slope over the last 100 bars of a ramp (h1_check.m_lag)."""
    n = np.arange(n_bars, dtype=float)
    x = FLAT_LEVEL + RAMP_SLOPE * n
    y = simulate(f, x)
    return float(np.mean((x[-100:] - y[-100:]) / RAMP_SLOPE))


def sim_dc_error(f, n_bars=N_BARS, w=W):
    """max |y - level| on a flat input after w bars (h1_check.m_flat)."""
    x = np.full(n_bars, FLAT_LEVEL)
    return float(np.max(np.abs(simulate(f, x)[w:] - FLAT_LEVEL)))
