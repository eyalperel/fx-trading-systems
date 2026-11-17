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
import re
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


def _ss3_filter(a1, arg, in_bump=0):
    """3-pole coefficient block shared by ss3_*: a1 = pole factor, arg = cosine argument (radians)."""
    b1 = 2.0 * a1 * math.cos(arg)
    c1 = a1 * a1
    coef2 = b1 + c1
    coef3 = -(c1 + b1 * c1)
    coef4 = c1 * c1
    coef1 = 1.0 - coef2 - coef3 - coef4
    if in_bump:
        coef1 = bump3(coef1, in_bump)
    return Filter(b=(coef1,), a=(coef2, coef3, coef4))


def ss3_article(period):
    """SuperSmoother 3-pole, Cybernetic Analysis Fig. 13.11 with the SS3 spec replacements
    (1.738 -> sqrt(3) by D1 Amendment 1 rule 4; 3.14159 -> exact pi). (a) source:
      a1 = expvalue(-3.14159/Period); b1 = 2*a1*Cosine(1.738*180/Period); c1 = a1*a1;
      coef2 = b1 + c1; coef3 = -(c1 + b1*c1); coef4 = c1*c1; coef1 = 1 - coef2 - coef3 - coef4;
      Filt3 = coef1*Price + coef2*Filt3[1] + coef3*Filt3[2] + coef4*Filt3[3].
    Cosine takes degrees: cos(sqrt(3)*180/P deg) = cos(sqrt(3)*pi/P rad)."""
    pi = math.pi
    return _ss3_filter(math.exp(-pi / period), math.sqrt(3.0) * pi / period)


def ss3_code(period, pi_value=PI_ZORRO, a1_bump=0, in_bump=0, deg=False):
    """The [corrected_code] lines of the SS3 spec (indicators/ehlers/SuperSmoother3Pole.c after the fix):
        var a1 = exp(-PI / Period);
        var b1 = 2.0 * a1 * cos(sqrt(3.0) * PI / Period);  c1 = a1*a1; coef2..coef4, coef1 as above.
    Negative-control hooks (default off): a1_bump = NCA (+units in 3rd digit of a1 BEFORE b1, c1, coefs);
    in_bump = NCB (+units in 3rd digit of coef1 AFTER the coefs); deg = NC2 (cos argument sqrt(3)*180/P)."""
    a1 = math.exp(-pi_value / period)
    if a1_bump:
        a1 = bump3(a1, a1_bump)
    arg = math.sqrt(3.0) * 180.0 / period if deg else math.sqrt(3.0) * pi_value / period
    return _ss3_filter(a1, arg, in_bump)


def ss3_printed(period):
    """NCL: the book listing as printed, constants 314159/100000 (exp) and 1738/1000 (cosine factor,
    with Zorro's PI). For the NCL effect only; the exact-pi-in-cosine 'degrees' form is a test helper."""
    a1 = math.exp(-(314159.0 / 100000) / period)
    return _ss3_filter(a1, (1738.0 / 1000) * PI_ZORRO / period)


def ss3_hybrid(period, pi_value=PI_ZORRO):
    """NCH: the superseded hybrid SuperSmoother3Pole.c body (spec [[variants]] NCH):
        c1 = b1 + a1; c2 = -(b1*a1 + a1*a1); c3 = a1*a1*a1; c0 = (1 - c1 - c2 - c3)/2;
        Filt = c0*(Price[0]+Price[1]) + c1*Filt[1] + c2*Filt[2] + c3*Filt[3]  (real pole a1, averaged input)."""
    a1 = math.exp(-pi_value / period)
    b1 = 2.0 * a1 * math.cos(math.sqrt(3.0) * pi_value / period)
    c1 = b1 + a1
    c2 = -(b1 * a1 + a1 * a1)
    c3 = a1 * a1 * a1
    c0 = (1.0 - c1 - c2 - c3) / 2.0
    return Filter(b=(c0, c0), a=(c1, c2, c3))


def _hp_filter(alpha1, in_bump=0, fb2_bump=0, num="2nd"):
    """High-pass coefficient block shared by hp_*: alpha1 -> (b, a).
        input weight c = (1 - alpha1/2)^2;  fb1 = 2(1 - alpha1);  fb2 = (1 - alpha1)^2
        HP[n] = c*(x - 2x[1] + x[2]) + fb1*HP[1] - fb2*HP[2]      (num = "2nd")
        HP[n] = c*(x - x[1])         + fb1*HP[1] - fb2*HP[2]      (num = "1st")
    in_bump / fb2_bump: bump3 on c / on fb2 after alpha1 is final."""
    c = (1.0 - alpha1 / 2.0) * (1.0 - alpha1 / 2.0)
    if in_bump:
        c = bump3(c, in_bump)
    fb1 = 2.0 * (1.0 - alpha1)
    fb2 = (1.0 - alpha1) * (1.0 - alpha1)
    if fb2_bump:
        fb2 = bump3(fb2, fb2_bump)
    if num == "2nd":
        b = (c, -2.0 * c, c)
    elif num == "1st":
        b = (c, -c)
    else:
        raise ValueError("num must be '2nd' or '1st', got %r" % (num,))
    return Filter(b=b, a=(fb1, -fb2))


def hp_article(period):
    """HighPassFilter, HP-A: TASC V.32:1 2014 / V.33:09 2015. (a) EasyLanguage, degrees:
        alpha1 = (Cosine(.707*360/P) + Sine(.707*360/P) - 1) / Cosine(.707*360/P);
        HP = (1 - alpha1/2)*(1 - alpha1/2)*(x - 2*x[1] + x[2]) + 2*(1 - alpha1)*HP[1] - (1 - alpha1)*(1 - alpha1)*HP[2];
    EasyLanguage Vars HP(0): the source's HP history starts at 0 (simulate(..., seed='zero')).
    D1 rule 1: .707 -> 1/sqrt(2) (equals the named constant to every printed digit), exact pi (degrees form:
    360/P deg = 2*pi/P rad). Same (b, a) representation as the ss2/ss3 models."""
    arg = (1.0 / math.sqrt(2.0)) * 2.0 * math.pi / period
    alpha1 = (math.cos(arg) + math.sin(arg) - 1.0) / math.cos(arg)
    return _hp_filter(alpha1)


# the float32 value of the decimal literal 0.707 as Zorro stores it (gotchas 9d.1, b)
K_F32_0707 = float(np.float32(0.707))


def hp_code(period, k=K_F32_0707, pi_value=PI_ZORRO, alpha_bump=0, in_bump=0, fb2_bump=0, deg=False, num="2nd"):
    """HighPassFilter as indicators/ehlers/HighPassFilter.c computes it (b: read 2026-11-16):
        var alpha1 = (cos(0.707*2.0*PI / HPPeriod) + sin(0.707*2.0*PI / HPPeriod) - 1.0) / cos(0.707*2.0*PI / HPPeriod);
        HP[0] = (1.0 - alpha1/2.0)*(1.0 - alpha1/2.0)*(Price[0] - 2.0*Price[1] + Price[2])
                + 2.0*(1.0 - alpha1)*HP[1] - (1.0 - alpha1)*(1.0 - alpha1)*HP[2];   HP = series(Price[0], 3)
    k defaults to float32(0.707): the decimal literal 0.707 is float32 in this Zorro build (9d.1, b).
    k = sqrt(2)/2 (double) is the corrected line. Seeding is a property of the run (simulate seed='price' is
    series(Price[0], 3), the current .c), not of the coefficients.
    Negative-control hooks (default off): alpha_bump = bump3 on alpha1 BEFORE the coefficients; in_bump = bump3 on
    (1-alpha1/2)^2; fb2_bump = bump3 on (1-alpha1)^2; deg = trig arguments in degrees (k*360/P); num = '1st' uses
    the first-difference numerator x - x[1] (the 1-pole form, V.34:09)."""
    arg = k * 360.0 / period if deg else k * 2.0 * pi_value / period
    alpha1 = (math.cos(arg) + math.sin(arg) - 1.0) / math.cos(arg)
    if alpha_bump:
        alpha1 = bump3(alpha1, alpha_bump)
    return _hp_filter(alpha1, in_bump=in_bump, fb2_bump=fb2_bump, num=num)


_ARTICLE_RE = re.compile(r"hp_article\((\d{1,4})\)")


def article_model(name):
    """Resolve a spec's article-model string ('hp_article(48)') to a Filter. Restricted grammar, no eval;
    unknown -> None. Used by the checker's start-up check (reference model for expected values)."""
    m = _ARTICLE_RE.fullmatch(name) if isinstance(name, str) else None
    return hp_article(int(m.group(1))) if m and int(m.group(1)) > 0 else None


# [imp] model strings (spec) -> filter. Explicit registry, no eval.
IMP_MODELS = {"ss3_code(%d, PI_ZORRO)" % p: (lambda p=p: ss3_code(p)) for p in (10, 14, 20, 30)}
IMP_MODELS["ss3_hybrid(20, PI_ZORRO)"] = lambda: ss3_hybrid(20)
# HighPassFilter (c: names chosen here, the HP spec may extend this table): corrected line (k = sqrt(2)/2, Zorro PI)
# for the four filter periods, and the current .c (k = float32(0.707)) at P = 48 for the seed-price control NCH.
for _p in (20, 30, 48, 125):
    IMP_MODELS["hp_code(%d, PI_ZORRO, SQRT_HALF)" % _p] = (lambda p=_p: hp_code(p, k=math.sqrt(2.0) / 2.0))
IMP_MODELS["hp_code(48, PI_ZORRO, F32_0707)"] = lambda: hp_code(48)


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


def phase_at(f, t):
    """arg H(exp(-j*w)), w = 2*pi/t, in (-pi, pi]. Sign convention = the checker's fit: x = level + amp*sin(w n),
    fit y = a*sin + b*cos + c, phase = atan2(b, a) = arg H (positive = output leads). (b: test_03 compares the
    analytic value with an lstsq fit of a simulated sine.) Undefined where the gain is 0."""
    return float(np.angle(_hz(f, 2.0 * math.pi / t)))


def _poly(coefs, q):
    return sum(c * q ** k for k, c in enumerate(coefs))


def _dpoly(coefs, q):
    return sum(k * c * q ** (k - 1) for k, c in enumerate(coefs) if k)


def ramp_residual(f, level, slope, n=0):
    """Steady-state output of f on the ramp x[n] = level + slope*n (HARNESS_DESIGN D4 rule 4).
    With H(q) = B(q)/D(q), q = z^-1, B = sum b_k q^k, D = 1 - sum a_k q^k:  sum_k h_k (n-k) = n*H(1) - H'(1), so
        y_ss(n) = H(1)*(level + slope*n) - slope*H'(1),   H' = (B'D - B D')/D^2 at q = 1.
    For DC gain 0 this is the constant -slope*H'(1) (n is then irrelevant; 0 for a double zero at DC).
    Reduces to x[n] - slope*ramp_lag(f) at DC gain 1. (b: simulation cross-checks in test_reference_hp.py.)"""
    bq = list(f.b)
    dq = [1.0] + [-a for a in f.a]
    B, D, dB, dD = _poly(bq, 1.0), _poly(dq, 1.0), _dpoly(bq, 1.0), _dpoly(dq, 1.0)
    h1 = B / D
    dh1 = (dB * D - B * dD) / (D * D)
    return float(h1 * (level + slope * n) - slope * dh1)


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


def simulate(f, x, seed=None):
    """Run the recursion on array x. Input history before n = 0 is x[0] (Zorro series seeding, gotchas 9d.6).
    Output history before n = 0 (`seed`):
        None or "price"  y[-k] = x[0]  (as h1_check.simulate; = series(Price[0], n) in the .c). Default: SS2/SS3
                         behaviour byte-identical.
        "zero"           y[-k] = 0     (the article's EasyLanguage `Vars: HP(0)`, HP-A)."""
    if seed not in (None, "price", "zero"):
        raise ValueError("seed must be None, 'price' or 'zero', got %r" % (seed,))
    x = np.asarray(x, dtype=float)
    y = np.empty(len(x))
    nb, na = len(f.b), len(f.a)
    y_hist = 0.0 if seed == "zero" else x[0]
    for n in range(len(x)):
        acc = 0.0
        for k in range(nb):
            acc += f.b[k] * (x[n - k] if n - k >= 0 else x[0])
        for k in range(na):
            acc += f.a[k] * (y[n - k - 1] if n - k - 1 >= 0 else y_hist)
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
