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


def ss2_code(period, pi_value=PI_ZORRO, c1_scale=None, c1_bump=0, in_bump=0, deg=False, unaveraged=False):
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
    RFF stage 1 hooks (default off, existing callers unchanged):
      deg         NC2: the cosine argument is sqrt(2)*180/Period (degrees fed to cos(), gotchas 2); exponent unchanged.
      unaveraged  NCU: the input is not averaged: Filt = (1 - b1 + c1*c1)*Price[0] + c2*Filt[1] + c3*Filt[2]
                  (full weight 2*c0 on Price[0], no Price[1] term). DC gain stays 1.
    """
    root2 = math.sqrt(2.0)
    c1 = math.exp(-root2 * pi_value / period)
    if c1_bump:
        c1 = bump3(c1, c1_bump)
    b1 = 2.0 * c1 * math.cos(root2 * 180.0 / period if deg else root2 * pi_value / period)
    c2 = b1
    c3 = -c1 * c1
    c0 = (1.0 - b1 + c1 * c1) / 2.0
    if in_bump:
        c0 = bump3(c0, in_bump)
    if unaveraged:
        return Filter(b=(1.0 - b1 + c1 * c1,), a=(c2, c3))
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

# The old HighPassFilter.c writes 0.707*2.0*PI / HPPeriod with all-literal factors. Zorro 3.11 folds the product
# 0.707*2.0*PI at compile time to this float32 value; the division, trig and recursion are plain double.
# (b) measured: strategies/tests/PROBE_LiteralEval_20261117.c, label L04 (= L17), results/PROBE_LiteralEval_20261117.csv,
#     commit ba54022. (c) The rule that produces this value is unknown: no standard rounding of float32(0.707) x
#     float32(PI) reproduces it (3-4 float32 ulps off), so it is a measured constant, not a derived one.
ZORRO_FOLD_0707x2xPI = 4.44221019744873047


def hp_theta(period, k=K_F32_0707, pi_value=PI_ZORRO, deg=False, theta_const=None):
    """The trig argument of hp_code: theta_const / period when theta_const is given (the folded literal product,
    ZORRO_FOLD_0707x2xPI), else k*360/period (deg) or k*2*pi_value/period."""
    if theta_const is not None:
        return theta_const / period
    return k * 360.0 / period if deg else k * 2.0 * pi_value / period


def hp_alpha(period, k=K_F32_0707, pi_value=PI_ZORRO, deg=False, theta_const=None):
    """alpha1 of hp_code, before any negative-control bump."""
    arg = hp_theta(period, k=k, pi_value=pi_value, deg=deg, theta_const=theta_const)
    return (math.cos(arg) + math.sin(arg) - 1.0) / math.cos(arg)


def hp_code(period, k=K_F32_0707, pi_value=PI_ZORRO, alpha_bump=0, in_bump=0, fb2_bump=0, deg=False, num="2nd",
            theta_const=None):
    """HighPassFilter as indicators/ehlers/HighPassFilter.c computes it (b: read 2026-11-16):
        var alpha1 = (cos(0.707*2.0*PI / HPPeriod) + sin(0.707*2.0*PI / HPPeriod) - 1.0) / cos(0.707*2.0*PI / HPPeriod);
        HP[0] = (1.0 - alpha1/2.0)*(1.0 - alpha1/2.0)*(Price[0] - 2.0*Price[1] + Price[2])
                + 2.0*(1.0 - alpha1)*HP[1] - (1.0 - alpha1)*(1.0 - alpha1)*HP[2];   HP = series(Price[0], 3)
    k defaults to float32(0.707): the decimal literal 0.707 is float32 in this Zorro build (9d.1, b).
    k = sqrt(2)/2 (double) is the corrected line. Seeding is a property of the run (simulate seed='price' is
    series(Price[0], 3), the current .c), not of the coefficients.
    Negative-control hooks (default off): alpha_bump = bump3 on alpha1 BEFORE the coefficients; in_bump = bump3 on
    (1-alpha1/2)^2; fb2_bump = bump3 on (1-alpha1)^2; deg = trig arguments in degrees (k*360/P); num = '1st' uses
    the first-difference numerator x - x[1] (the 1-pole form, V.34:09).
    theta_const (default None): the trig argument is theta_const / period, k and pi_value unused. With
    theta_const = ZORRO_FOLD_0707x2xPI this is the OLD .c as Zorro 3.11 compiles it (Amendment 2, NCH must_pass)."""
    alpha1 = hp_alpha(period, k=k, pi_value=pi_value, deg=deg, theta_const=theta_const)
    if alpha_bump:
        alpha1 = bump3(alpha1, alpha_bump)
    return _hp_filter(alpha1, in_bump=in_bump, fb2_bump=fb2_bump, num=num)


# ---------------------------------------------------------------------------------------------------
# Cascades (RFF stage 1). A cascade of two linear filters is one linear filter: H = H_f * H_g, i.e. polynomial
# products of the numerators and of the denominators 1 - sum a_k q^k. `cascade` returns that single Filter (seed:
# the whole run); `simulate_cascade` runs the stages one after the other, each with its own seed (needed where
# the stages are seeded differently, e.g. the old HP with a price seed feeding the SuperSmoother).
# ---------------------------------------------------------------------------------------------------
def cascade(f, g):
    """One Filter equal to f followed by g (H = Hf*Hg). b = conv(bf, bg); D = conv(Df, Dg), a = -D[1:]."""
    df = np.array([1.0] + [-a for a in f.a])
    dg = np.array([1.0] + [-a for a in g.a])
    d = np.convolve(df, dg)
    return Filter(b=tuple(float(v) for v in np.convolve(np.array(f.b), np.array(g.b))),
                  a=tuple(float(-v) for v in d[1:]))


def roof_article(hp, ss):
    """RoofingFilter as the article defines it (TASC V.32:1 2014 sidebar): the article HP followed by the article
    SuperSmoother 2-pole, exact constants (D1 rule 1). Seed 'zero' in simulate (EasyLanguage Vars HP(0), Filt(0))."""
    return cascade(hp_article(hp), ss2_article(ss))


def roof_code(hp, ss, ss_c1_bump=0, ss_in_bump=0, ss_deg=False, ss_unaveraged=False):
    """The corrected RoofingFilter.c (spec [corrected_code]: rf_hp = series(HighPassFilter(Price, HPPeriod), 3);
    SuperSmoother2Pole(rf_hp, SSPeriod)) as one Filter: hp_code(k = sqrt(2)/2) followed by ss2_code, Zorro PI.
    Simulated with seed 'zero' it equals simulate_cascade([(hp, 'zero'), (ss, 'price')]) (test).
    Control hooks (default off), all acting on the SuperSmoother stage: ss_c1_bump = NCA (ss2_code c1_bump),
    ss_in_bump = NCB (in_bump), ss_unaveraged = NCU, ss_deg = NC2 (cos argument in degrees)."""
    return cascade(hp_code(hp, k=math.sqrt(2.0) / 2.0),
                   ss2_code(ss, c1_bump=ss_c1_bump, in_bump=ss_in_bump, deg=ss_deg, unaveraged=ss_unaveraged))


Cascade = namedtuple("Cascade", "stages")            # stages: tuple of (Filter, seed), applied in order


def roof_nco(hp, ss):
    """NCO: the pipeline of the current (old) RoofingFilter.c: the OLD HighPassFilter body (literal 0.707 folded to
    ZORRO_FOLD_0707x2xPI, history seeded at the price level) feeding SuperSmoother2Pole (price seed = its own first
    input). Not representable as one filter (the HP stage has a price seed): a Cascade for simulate_cascade."""
    return Cascade(stages=((hp_code(hp, theta_const=ZORRO_FOLD_0707x2xPI), "price"), (ss2_code(ss), "price")))


def simulate_cascade(stages, x):
    """Run stages [(Filter, seed), ...] one after the other: each stage's input is the previous stage's output, its
    input history before n = 0 is its own first input and its output history is seeded per `seed` (as simulate)."""
    cur = np.asarray(x, dtype=float)
    for f, seed in stages:
        cur = simulate(f, cur, seed=seed)
    return cur


def simulate_any(model, x, seed=None):
    """simulate() for a Filter, simulate_cascade() for a Cascade (its stages carry their own seeds; `seed` unused),
    Seeded: its own seed, Complement: x - f(x) with f's own seed (USE stage 1)."""
    if isinstance(model, Cascade):
        return simulate_cascade(model.stages, x)
    if isinstance(model, Seeded):
        return simulate(model.filter, x, seed=model.seed)
    if isinstance(model, Complement):
        x = np.asarray(x, dtype=float)
        return x - simulate(model.f, x, seed=model.seed)
    return simulate(model, x, seed=seed)


# ---------------------------------------------------------------------------------------------------
# UltimateSmoother (USE stage 1). (a) Source: Ehlers, "The Ultimate Smoother", TASC V.42:04 (2024), sidebar
# "UltimateSmoother Function, In EasyLanguage":
#     a1 = expvalue(-1.414*3.14159 / Period);  b1 = 2*a1*Cosine(1.414*180 / Period);  c2 = b1;  c3 = -a1*a1;
#     c1 = (1 + c2 - c3) / 4;
#     If CurrentBar >= 4 Then US = (1 - c1)*Price + (2*c1 - c2)*Price[1] - (c1 + c3)*Price[2] + c2*US[1] + c3*US[2];
#     If CurrentBar < 4 Then US = Price;
# D1 rule 1: 1.414 -> sqrt(2), 3.14159 -> pi, degrees -> radians. Start-up: the first 3 outputs equal Price
# (seed "pass3"); the recursion starts on the 4th call.
# ---------------------------------------------------------------------------------------------------
Seeded = namedtuple("Seeded", "filter seed")          # a Filter that carries its own seed (IMP models, USE stage 1)
Complement = namedtuple("Complement", "f seed")       # y = x - f(x), f simulated with its own seed


def _us_filter(a1, arg, c1_div=4.0):
    """Coefficient block of the UltimateSmoother: a1 = pole factor, arg = cosine argument (radians)."""
    b1 = 2.0 * a1 * math.cos(arg)
    c2, c3 = b1, -a1 * a1
    c1 = (1.0 + c2 - c3) / c1_div
    return Filter(b=(1.0 - c1, 2.0 * c1 - c2, -(c1 + c3)), a=(c2, c3))


def us_article(period):
    """UltimateSmoother from the article formula with the D1 replacements (exact sqrt(2) and pi)."""
    return _us_filter(math.exp(-math.sqrt(2.0) * math.pi / period), math.sqrt(2.0) * math.pi / period)


def us_code(period, pi_value=PI_ZORRO, c1_div=4.0, deg=False):
    """The [corrected_code] lines of the USE spec (indicators/ehlers/UltimateSmootherE.c after the fix):
        us_k = sqrt(2.0); us_a1 = exp(-us_k*PI/Period); us_b1 = 2.0*us_a1*cos(us_k*PI/Period); us_c2 = us_b1;
        us_c3 = -us_a1*us_a1; us_c1 = (1.0 + us_c2 - us_c3)/4.0; 3-term numerator, 2 feedback terms.
    Control hooks (default off): c1_div = NCB (divisor of c1, 4 -> 4.01); deg = NC2 (cosine argument sqrt(2)*180/P,
    exponent unchanged). The start-up seed is NOT part of the coefficients: simulate(seed='pass3')."""
    a1 = math.exp(-math.sqrt(2.0) * pi_value / period)
    arg = math.sqrt(2.0) * 180.0 / period if deg else math.sqrt(2.0) * pi_value / period
    return _us_filter(a1, arg, c1_div)


def us_nca(period, add=1.0 / 1000, pi_value=PI_ZORRO):
    """NCA: a1 + `add` BEFORE b1, c3 and c1 are derived; the cosine argument is unchanged. The control body writes
    `us_a1 = us_a1 + <1/1000 built from a variable>` (gotchas 9d.8)."""
    a1 = math.exp(-math.sqrt(2.0) * pi_value / period) + add
    return _us_filter(a1, math.sqrt(2.0) * pi_value / period)


def us_printed(period, pi_value=PI_ZORRO):
    """NCL (INFO): the article as printed, 1.414 and 3.14159 built from integers (1414/1000, 314159/100000) in the
    exponent; the cosine's 180 degrees is the library's PI (Zorro float32 PI, as ss3_printed): cos(1.414*PI/P).
    (b) With exact pi in the cosine instead the effect vs us_article(20) is gain 1.0708e-4 / phase 1.4277e-4; with Zorro
    PI it is 1.0724e-4 / 1.4296e-4 (the planning chat's 1.072e-4 / 1.430e-4 are the Zorro-PI values)."""
    k = 1414.0 / 1000
    a1 = math.exp(-k * (314159.0 / 100000) / period)
    return _us_filter(a1, k * pi_value / period)


def one_minus(f, seed="zero"):
    """Complement model y = x - f(x) with f simulated under its own `seed` (NCX: f = the verified HighPassFilter,
    k = sqrt(2)/2, seed zero)."""
    return Complement(f=f, seed=seed)


def one_minus_filter(f):
    """The complement as ONE Filter: H = 1 - N/D = (D - N)/D, so b = D - f.b (padded), a = f.a. (b: test_one_minus)
    As one filter it equals the Complement model when the output history is x[0] ('price' seed) and f's history is 0."""
    d = [1.0] + [-a for a in f.a]
    n = max(len(d), len(f.b))
    d += [0.0] * (n - len(d))
    b = list(f.b) + [0.0] * (n - len(f.b))
    return Filter(b=tuple(float(di - bi) for di, bi in zip(d, b)), a=f.a)


def as_filter(model):
    """The Filter whose analytic H the model has (for gain_at / phase_at): Filter, Seeded, Complement. Cascade: None."""
    if isinstance(model, Filter):
        return model
    if isinstance(model, Seeded):
        return model.filter
    if isinstance(model, Complement):
        return one_minus_filter(model.f)
    return None


_ARTICLE_RE = re.compile(r"hp_article\((\d{1,4})\)")
_US_ARTICLE_RE = re.compile(r"us_article\((\d{1,4})\)")
_ROOF_ARTICLE_RE = re.compile(r"roof_article\((\d{1,4}),\s*(\d{1,4})\)")


def article_model(name):
    """Resolve a spec's article-model string ('hp_article(48)', 'roof_article(48,10)') to a Filter. Restricted
    grammar, no eval; unknown -> None. Used by the checker's start-up check (reference model for expected values)."""
    if not isinstance(name, str):
        return None
    m = _ARTICLE_RE.fullmatch(name)
    if m and int(m.group(1)) > 0:
        return hp_article(int(m.group(1)))
    m = _ROOF_ARTICLE_RE.fullmatch(name)
    if m and int(m.group(1)) > 0 and int(m.group(2)) > 0:
        return roof_article(int(m.group(1)), int(m.group(2)))
    m = _US_ARTICLE_RE.fullmatch(name)
    if m and int(m.group(1)) > 0:
        return us_article(int(m.group(1)))
    return None


# [imp] model strings (spec) -> filter. Explicit registry, no eval.
IMP_MODELS = {"ss3_code(%d, PI_ZORRO)" % p: (lambda p=p: ss3_code(p)) for p in (10, 14, 20, 30)}
IMP_MODELS["ss3_hybrid(20, PI_ZORRO)"] = lambda: ss3_hybrid(20)
# HighPassFilter (c: names chosen here, the HP spec may extend this table): corrected line (k = sqrt(2)/2, Zorro PI)
# for the four filter periods, and the current .c (k = float32(0.707)) at P = 48 for the seed-price control NCH.
for _p in (20, 30, 48, 125):
    IMP_MODELS["hp_code(%d, PI_ZORRO, SQRT_HALF)" % _p] = (lambda p=_p: hp_code(p, k=math.sqrt(2.0) / 2.0))
IMP_MODELS["hp_code(48, PI_ZORRO, F32_0707)"] = lambda: hp_code(48)
# The old .c as Zorro 3.11 compiles it (all-literal product folded at compile time; probe ba54022, L04): Amendment 2.
IMP_MODELS["hp_code(48, ZORRO_FOLD_0707x2xPI)"] = lambda: hp_code(48, theta_const=ZORRO_FOLD_0707x2xPI)
# HP negative controls, own models (c: names chosen here). Explicit entries, no eval; k = sqrt(2)/2, Zorro PI.
_SQRT_HALF = math.sqrt(2.0) / 2.0
IMP_MODELS["hp_code(48, PI_ZORRO, SQRT_HALF, alpha_bump=1)"] = lambda: hp_code(48, k=_SQRT_HALF, alpha_bump=1)
IMP_MODELS["hp_code(48, PI_ZORRO, SQRT_HALF, in_bump=1)"] = lambda: hp_code(48, k=_SQRT_HALF, in_bump=1)
IMP_MODELS["hp_code(48, PI_ZORRO, SQRT_HALF, fb2_bump=1)"] = lambda: hp_code(48, k=_SQRT_HALF, fb2_bump=1)
IMP_MODELS["hp_code(48, PI_ZORRO, SQRT_HALF, num=1st)"] = lambda: hp_code(48, k=_SQRT_HALF, num="1st")
IMP_MODELS["hp_code(49, PI_ZORRO, SQRT_HALF)"] = lambda: hp_code(49, k=_SQRT_HALF)
IMP_MODELS["hp_code(20, PI_ZORRO, SQRT_HALF, deg)"] = lambda: hp_code(20, k=_SQRT_HALF, deg=True)


# RoofingFilter (RFF stage 1; c: names chosen here). Real variants and the controls' own models, explicit entries.
for _hp, _ss in ((48, 10), (30, 10), (125, 10), (48, 20)):
    IMP_MODELS["roof_code(%d, %d)" % (_hp, _ss)] = (lambda h=_hp, s=_ss: roof_code(h, s))
IMP_MODELS["roof_code(48, 10, ss_c1_bump=1)"] = lambda: roof_code(48, 10, ss_c1_bump=1)
IMP_MODELS["roof_code(48, 10, ss_in_bump=1)"] = lambda: roof_code(48, 10, ss_in_bump=1)
IMP_MODELS["roof_code(48, 10, ss_unaveraged)"] = lambda: roof_code(48, 10, ss_unaveraged=True)
IMP_MODELS["roof_code(48, 10, ss_deg)"] = lambda: roof_code(48, 10, ss_deg=True)
IMP_MODELS["roof_code(49, 10)"] = lambda: roof_code(49, 10)
IMP_MODELS["roof_code(48, 11)"] = lambda: roof_code(48, 11)
IMP_MODELS["roof_nco(48, 10)"] = lambda: roof_nco(48, 10)

# UltimateSmootherE (USE stage 1; c: names chosen here). Every model carries its own seed (Seeded / Complement), so a
# must_fail replay can use another seed than the variant declares (NCS replayed with the pass3 model).
for _p in (10, 14, 20, 30):
    IMP_MODELS["us_code(%d, pass3)" % _p] = (lambda p=_p: Seeded(us_code(p), "pass3"))
IMP_MODELS["us_code(21, pass3)"] = lambda: Seeded(us_code(21), "pass3")                          # NC1
IMP_MODELS["us_code(20, pass4)"] = lambda: Seeded(us_code(20), "pass4")                          # NCS
IMP_MODELS["us_code(20, pass3, c1_div=4.01)"] = lambda: Seeded(us_code(20, c1_div=401.0 / 100), "pass3")    # NCB
IMP_MODELS["us_code(20, pass3, deg)"] = lambda: Seeded(us_code(20, deg=True), "pass3")           # NC2
IMP_MODELS["us_nca(20, pass3)"] = lambda: Seeded(us_nca(20), "pass3")                            # NCA
IMP_MODELS["us_printed(20, pass3)"] = lambda: Seeded(us_printed(20), "pass3")                    # NCL (INFO variant)
IMP_MODELS["us_nx(20)"] = lambda: one_minus(hp_code(20, k=math.sqrt(2.0) / 2.0), "zero")         # NCX: x - HighPassFilter




# ---------------------------------------------------------------------------------------------------
# Reflex (RFX stage 1; HARNESS_DESIGN D6, docs/harness/REFLEX_SOURCE_REVIEW.md). (a) Source: Ehlers, "Reflex: A New Zero-Lag
# Indicator", TASC V.38:02 (2020), sidebar "EasyLanguage Code For Reflex Indicator":
#     a1 = expvalue(-1.414*3.14159 / (.5*Length));  b1 = 2*a1*Cosine(1.414*180 / (.5*Length));
#     c2 = b1;  c3 = -a1*a1;  c1 = 1 - c2 - c3;
#     Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2];
#     Slope = (Filt[Length] - Filt) / Length;
#     Sum = 0;  For count = 1 to Length Begin Sum = Sum + (Filt + count*Slope) - Filt[count]; End;  Sum = Sum / Length;
#     MS = .04*Sum*Sum + .96*MS[1];   If MS <> 0 Then Reflex = Sum / SquareRoot(MS);
# D1 rule 1: 1.414 -> sqrt(2), 3.14159 -> pi, degrees -> radians; D1 rule 2: .5, .04, .96 literal. `.5*Length` is REAL (R-2).
# No start-up rule is printed (R-4): Filt history = the first price (series(Price[0], ...)), MS starts at 0.
# Operation order follows the corrected code / the sidebar line by line (the ramp rows depend on rounding noise, finding 5).
# ---------------------------------------------------------------------------------------------------
ReflexModel = namedtuple("ReflexModel", "L half w1 w2 root2 pi_exp pi_cos deg a1_add div")
ReflexOut = namedtuple("ReflexOut", "sum ms r")
SharedModel = namedtuple("SharedModel", "Ls index")     # old Reflex.c: ONE static MS shared by the listed calls, call order

F32_004 = float(np.float32(0.04))      # the old Reflex.c literals (R-3, gotchas 9d.1)
F32_096 = float(np.float32(0.96))


def reflex_article(L, half=None, w1=None, w2=None, root2=None, pi_exp=None, pi_cos=None, deg=False, a1_add=0.0,
                   div=None):
    """The article Reflex as a model (D1: exact sqrt(2) and pi; weights 4/100 and 96/100). Keyword hooks (default off)
    are the negative controls / the Zorro-side variants:
        half   fixed smoothing period instead of L/2 (NCH: the old integer half length)
        w1, w2 MS weights (NCW 41/1000, 959/1000; old float32 weights, finding 10)
        root2, pi_exp, pi_cos   constants (NCL: 1414/1000, 314159/100000, Zorro PI; code: Zorro PI in both)
        deg    NC2: the cosine argument in degrees, sqrt(2)*180/half
        a1_add NCA: added to a1 before b1, c3 and c1 are derived
        div    NCK: divisor of Sum (default L)"""
    return ReflexModel(L=L, half=half, w1=4.0 / 100 if w1 is None else w1, w2=96.0 / 100 if w2 is None else w2,
                       root2=math.sqrt(2.0) if root2 is None else root2, pi_exp=math.pi if pi_exp is None else pi_exp,
                       pi_cos=math.pi if pi_cos is None else pi_cos, deg=deg, a1_add=a1_add, div=div)


def reflex_code(L, **kw):
    """The [corrected_code] lines of the RFX spec (Zorro PI in the exponent and the cosine): reflex_article with
    pi_exp = pi_cos = PI_ZORRO. Same keyword hooks as reflex_article."""
    kw.setdefault("pi_exp", PI_ZORRO)
    kw.setdefault("pi_cos", PI_ZORRO)
    return reflex_article(L, **kw)


def _reflex_coefs(m):
    half = m.L / 2.0 if m.half is None else float(m.half)
    a1 = math.exp(-m.root2 * m.pi_exp / half) + m.a1_add
    arg = m.root2 * 180.0 / half if m.deg else m.root2 * m.pi_cos / half
    b1 = 2.0 * a1 * math.cos(arg)
    c2, c3 = b1, -a1 * a1
    return 1.0 - c2 - c3, c2, c3


def _reflex_step(F, L, div, w1, w2, ms_prev):
    """One bar after F (list, newest last, >= L+1 entries) got its new Filt: (sum, ms, r). C order of operations."""
    t = len(F) - 1
    f0 = F[t]
    slope = (F[t - L] - f0) / L
    s = 0.0
    for c in range(1, L + 1):
        s += (f0 + c * slope) - F[t - c]
    s = s / (L if div is None else div)
    ms = w1 * s * s + w2 * ms_prev
    return s, ms, (s / math.sqrt(ms) if ms > 0 else 0.0)


def simulate_reflex(m, x):
    """Run a ReflexModel on x: ReflexOut(sum, ms, r) arrays. Filt history before n = 0 = x[0] (price seed), MS starts 0."""
    x = np.asarray(x, dtype=float)
    c1, c2, c3 = _reflex_coefs(m)
    L = m.L
    F = [float(x[0])] * (L + 2)
    ssum, ms_a, r = np.empty(len(x)), np.empty(len(x)), np.empty(len(x))
    ms = 0.0
    for n in range(len(x)):
        p1 = x[n - 1] if n else x[0]
        F.append(c1 * (x[n] + p1) / 2.0 + c2 * F[-1] + c3 * F[-2])
        ssum[n], ms, r[n] = _reflex_step(F, L, m.div, m.w1, m.w2, ms)
        ms_a[n] = ms
    return ReflexOut(ssum, ms_a, r)


def simulate_shared(Ls, xs):
    """The OLD Reflex.c (superseded): per call slot an integer-half SuperSmoother2Pole (Zorro PI, price seed) feeding a
    Filt series seeded with that slot's first output, float32 weights, and ONE MS shared by every slot, updated slot after
    slot in the given order on every bar (`static var rx_MS`, R-1). Ls: L per slot; xs: input array per slot, same order
    as the generator's calls. Returns [ReflexOut] per slot."""
    nb = len(xs[0])
    ss = [simulate(ss2_code(L // 2), x) for L, x in zip(Ls, xs)]                # SS2 output per slot (own price seed)
    F = [[float(s[0])] * (L + 2) for L, s in zip(Ls, ss)]
    outs = [ReflexOut(np.empty(nb), np.empty(nb), np.empty(nb)) for _ in Ls]
    ms = 0.0
    for n in range(nb):
        for k, (L, s) in enumerate(zip(Ls, ss)):
            F[k].append(float(s[n]))
            sm, ms, r = _reflex_step(F[k], L, None, F32_004, F32_096, ms)
            outs[k].sum[n], outs[k].ms[n], outs[k].r[n] = sm, ms, r
    return outs


def reflex_superseded(Ls, index=0):
    """Model handle for [imp]: the old Reflex.c called once per bar for each L in Ls (call order); `index` = which call."""
    return SharedModel(Ls=tuple(Ls), index=index)


def reflex_sum_filter(L, half=None, pi_value=None):
    """Sum as ONE linear filter of the price (finding 1): H_Sum = G(z) * H_SS(half), G = (L-1)/(2L) (1 + z^-L)
    - (1/L) sum_{k=1}^{L-1} z^-k. Exact constants unless pi_value is given (then reflex_code's)."""
    half = L / 2.0 if half is None else half
    ss = ss2_article(half) if pi_value is None else ss2_code(half, pi_value=pi_value)
    g = [(L - 1.0) / (2.0 * L)] + [-1.0 / L] * (L - 1) + [(L - 1.0) / (2.0 * L)]
    return Filter(b=tuple(float(v) for v in np.convolve(g, ss.b)), a=ss.a)


_REFLEX_ARTICLE_RE = re.compile(r"reflex_article\((\d{1,3})\)")


def reflex_article_model(name):
    """Resolve a spec's article-model string ('reflex_article(20)') to a ReflexModel. Restricted grammar, no eval."""
    m = _REFLEX_ARTICLE_RE.fullmatch(name) if isinstance(name, str) else None
    return reflex_article(int(m.group(1))) if m and int(m.group(1)) > 0 else None


# [imp] model registry for RFX (c: names chosen here). Zorro-PI code models for the real variants, controls' own models.
for _L in (14, 20, 21, 30):
    IMP_MODELS["reflex_code(%d)" % _L] = (lambda L=_L: reflex_code(L))
IMP_MODELS["reflex_code(22)"] = lambda: reflex_code(22)                                           # NC1
IMP_MODELS["reflex_article(20)"] = lambda: reflex_article(20)                                    # NCS must_fail replay
IMP_MODELS["reflex_nca(20)"] = lambda: reflex_code(20, a1_add=1.0 / 1000)                        # NCA
IMP_MODELS["reflex_nc2(20)"] = lambda: reflex_code(20, deg=True)                                 # NC2
IMP_MODELS["reflex_nch(21)"] = lambda: reflex_code(21, half=10.0)                                # NCH: integer half length
IMP_MODELS["reflex_nck(20)"] = lambda: reflex_code(20, div=19)                                   # NCK: divisor L-1
IMP_MODELS["reflex_ncw(20)"] = lambda: reflex_code(20, w1=41.0 / 1000, w2=959.0 / 1000)          # NCW
IMP_MODELS["reflex_printed(20)"] = lambda: reflex_code(20, root2=1414.0 / 1000, pi_exp=314159.0 / 100000)   # NCL (cos: Zorro PI)
IMP_MODELS["reflex_superseded(20,14)[0]"] = lambda: reflex_superseded((20, 14), 0)               # NCS (instance 1, L20)
IMP_MODELS["reflex_superseded(20,14)[1]"] = lambda: reflex_superseded((20, 14), 1)               # NCT (instance 2, L14)

# ---------------------------------------------------------------------------------------------------
# MESAStochastic (MST stage 1; HARNESS_DESIGN D6, docs/harness/MESASTOCHASTIC_SOURCE_REVIEW.md). (a) Source: Ehlers, "Predictive
# And Successful Indicators", TASC V.32:1 (2014), sidebar "EasyLanguage Code To Compute The MESA Stochastic Indicator":
#     HP / Filt = the Roofing Filter (48, 10);  HighestC / LowestC over Filt[0..Length-1] (Length bars);
#     Stoc = (Filt - LowestC) / (HighestC - LowestC);
#     MESAStochastic = c1*(Stoc + Stoc[1])/2 + c2*MESAStochastic[1] + c3*MESAStochastic[2]   (the SuperSmoother(10) coefficients)
# D1 rule 1: .707 -> sqrt(2)/2, 1.414 -> sqrt(2), 3.14159 -> pi, degrees -> radians. Scale 0-1, no zero-range guard, no start-up rule.
# Library conventions (M-4 / M-5 / M-6), implemented by default: Roof from the RFF cascade (HP history 0, input history = first
# price, first Roof = 0); the window history is seeded with the first Roof value; zero range -> Stoc = 0.5 (`fallback`); the
# final SuperSmoother starts with Stoc and output histories at the first Stoc (`final_seed = "first"`).
# ---------------------------------------------------------------------------------------------------
MesaModel = namedtuple("MesaModel", "L hp ss win scale fallback da_final literals final_seed pi_value")
MesaOut = namedtuple("MesaOut", "roof stoc out rng")        # rng = HighestC - LowestC per row (the trace gate quantity)


def mesa_article(L, hp, ss, win=None, scale=1.0, fallback=0.5, da_final=0.0, literals="exact", final_seed="first",
                 pi_value=None):
    """The article MESAStochastic (exact constants, D1) with the library conventions. Keyword hooks (default off):
        win         window length (default L; NCW: L + 1, review M-1)
        scale       multiplier of the raw stochastic before the final smoothing (default 1.0; the old file: 100)
        fallback    Stoc when HighestC == LowestC (default 0.5, M-6; the old file: 50)
        da_final    NCA: added to the final SuperSmoother's a1 before b1, c3 and c1 are derived (Roof untouched)
        literals    "exact" | "printed" (NCL: .707, 1.414, 3.14159 built from integers in HP, the roofing SS and the final SS;
                    the cosines use the library's PI, as the other INFO variants)
        final_seed  "first" (library: Stoc and output histories start at the first Stoc) | "zero" (the source: both start at 0)
        pi_value    None = exact pi (the article tables); PI_ZORRO = the code (see mesa_code)"""
    if literals not in ("exact", "printed"):
        raise ValueError("literals must be 'exact' or 'printed', got %r" % (literals,))
    if final_seed not in ("first", "zero"):
        raise ValueError("final_seed must be 'first' or 'zero', got %r" % (final_seed,))
    return MesaModel(L=L, hp=hp, ss=ss, win=win, scale=scale, fallback=fallback, da_final=da_final, literals=literals,
                     final_seed=final_seed, pi_value=pi_value)


def mesa_code(L, hp, ss, **kw):
    """The [corrected_code] of the MST spec: mesa_article with Zorro's PI (and k = sqrt(2)/2 in the HP, as HighPassFilter.c)."""
    kw.setdefault("pi_value", PI_ZORRO)
    return mesa_article(L, hp, ss, **kw)


def mesa_superseded(L, hp, ss):
    """The OLD MESAStochastic.c: window L + 1 (M-1), scale 100 (M-2), fallback 50, same seeds, Zorro PI."""
    return mesa_code(L, hp, ss, win=L + 1, scale=100.0, fallback=50.0)


def _ss2_general(period, root2, pi_exp, pi_cos, a1_add=0.0):
    """SuperSmoother 2-pole in the article's own form: a1 = exp(-root2*pi_exp/P) + a1_add; b1 = 2 a1 cos(root2*pi_cos/P); c2 = b1;
    c3 = -a1^2; c1 = 1 - c2 - c3; Filt = c1*(x + x1)/2 + c2*Filt[1] + c3*Filt[2]."""
    a1 = math.exp(-root2 * pi_exp / period) + a1_add
    b1 = 2.0 * a1 * math.cos(root2 * pi_cos / period)
    c2, c3 = b1, -a1 * a1
    c1 = 1.0 - c2 - c3
    return Filter(b=(c1 / 2.0, c1 / 2.0), a=(c2, c3))


def _mesa_filters(m):
    """(HP filter, roofing SS filter, final SS filter) of a MesaModel."""
    if m.literals == "printed":
        k, k1, k2 = 707.0 / 1000, 1414.0 / 1000, 314159.0 / 100000
        hpf = hp_code(m.hp, k=k)                                                    # Zorro PI in the trig arguments
        ssr = _ss2_general(m.ss, k1, k2, PI_ZORRO)
        ssf = _ss2_general(m.ss, k1, k2, PI_ZORRO, m.da_final)
        return hpf, ssr, ssf
    if m.pi_value is None:
        hpf, ssr = hp_article(m.hp), ss2_article(m.ss)
        ssf = _ss2_general(m.ss, math.sqrt(2.0), math.pi, math.pi, m.da_final) if m.da_final else ssr
    else:
        hpf, ssr = hp_code(m.hp, k=math.sqrt(2.0) / 2.0, pi_value=m.pi_value), ss2_code(m.ss, pi_value=m.pi_value)
        ssf = (_ss2_general(m.ss, math.sqrt(2.0), m.pi_value, m.pi_value, m.da_final) if m.da_final else ssr)
    return hpf, ssr, ssf


def simulate_mesa(m, x):
    """Run a MesaModel on x: MesaOut(roof, stoc, out, rng) arrays (float64)."""
    x = np.asarray(x, dtype=float)
    hpf, ssr, ssf = _mesa_filters(m)
    roof = simulate(cascade(hpf, ssr), x, seed="zero")                              # RFF O_SEED: HP history 0, input history x[0] (the RFF cascade model, one filter)
    win = m.L if m.win is None else m.win
    pad = np.concatenate([np.full(win - 1, roof[0]), roof])                         # window history seeded with the first Roof
    v = np.lib.stride_tricks.sliding_window_view(pad, win)
    hh, ll = v.max(axis=1), v.min(axis=1)
    rng = hh - ll
    ok = rng != 0.0
    stoc = np.full(len(x), float(m.fallback))
    stoc[ok] = m.scale * (roof[ok] - ll[ok]) / rng[ok]                              # C order: (scale*(Roof - LL))/(HH - LL)
    if m.final_seed == "zero":
        out = simulate(ssf, np.concatenate([[0.0], stoc]), seed="zero")[1:]         # Stoc[1] = 0 and the output history 0
    else:
        out = simulate(ssf, stoc, seed="price")                                     # both histories start at the first Stoc
    return MesaOut(roof, stoc, out, rng)


_MESA_ARTICLE_RE = re.compile(r"mesa_article\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})\)")


def mesa_article_model(name):
    """Resolve a spec's article-model string ('mesa_article(20,48,10)') to a MesaModel. Restricted grammar, no eval."""
    m = _MESA_ARTICLE_RE.fullmatch(name) if isinstance(name, str) else None
    if not m or min(int(g) for g in m.groups()) <= 0:
        return None
    return mesa_article(*(int(g) for g in m.groups()))


def osc_article_model(name):
    """Article model of an oscillator spec: reflex_article(L), mesa_article(L,hp,ss) or lrsi_article(n/d); None if unknown."""
    return reflex_article_model(name) or mesa_article_model(name) or lrsi_article_model(name)


def mesa_roof_filter(hp, ss):
    """The Roof stage of mesa_article as ONE linear filter (analytic tables): the RFF article cascade."""
    return roof_article(hp, ss)


# [imp] model registry for MST (c: names chosen here).
for _L, _hp, _ss in ((14, 48, 10), (20, 48, 10), (30, 48, 10), (20, 48, 20), (22, 48, 10), (20, 40, 10)):
    IMP_MODELS["mesa_code(%d,%d,%d)" % (_L, _hp, _ss)] = (lambda L=_L, h=_hp, s=_ss: mesa_code(L, h, s))
IMP_MODELS["mesa_article(20,48,10)"] = lambda: mesa_article(20, 48, 10)                             # NCS must_fail replay
IMP_MODELS["mesa_code(20,48,10,final_seed=zero)"] = lambda: mesa_code(20, 48, 10, final_seed="zero")   # NCZ
IMP_MODELS["mesa_code(20,48,10,win=21)"] = lambda: mesa_code(20, 48, 10, win=21)                  # NCW
IMP_MODELS["mesa_code(20,48,10,da_final=1/1000)"] = lambda: mesa_code(20, 48, 10, da_final=1.0 / 1000)   # NCA
IMP_MODELS["mesa_printed(20,48,10)"] = lambda: mesa_article(20, 48, 10, literals="printed")        # NCL
IMP_MODELS["mesa_superseded(20,48,10)"] = lambda: mesa_superseded(20, 48, 10)                      # NCS


# ---------------------------------------------------------------------------------------------------
# Laguerre RSI (LRSI stage 1; HARNESS_DESIGN D6, docs/harness/LAGUERRERSI_SOURCE_REVIEW.md). (a) Source: Ehlers, Cybernetic Analysis
# for Stocks and Futures (Wiley 2004), ch. 14, Fig. 14.8, p. 221:
#     L0 = (1 - gamma)*Close + gamma*L0[1];
#     L1 = - gamma *L0 + L0[1] + gamma *L1[1];   L2, L3 likewise;
#     CU = 0; CD = 0; If L0 >= L1 then CU = L0 - L1 Else CD = L1 - L0;  (L1/L2, L2/L3 likewise, accumulated)
#     If CU + CD <> 0 then RSI = CU / (CU + CD);
# All variables start at 0 (Vars: L0(0) ... RSI(0)); bar 1 is computed (L-1); RSI holds its previous value when CU + CD = 0, initial 0
# (L-2). No trig, no PI, no decimal literal in the corrected code: model = code (no Zorro-PI variant). The model uses the BOOK term order.
# (b) Transfer functions: L0 = (1 - g)/(1 - g z^-1); each later stage multiplies by the allpass A = (z^-1 - g)/(1 - g z^-1).
# ---------------------------------------------------------------------------------------------------
LrsiModel = namedtuple("LrsiModel", "g g_l0 form seed hold0")
LrsiOut = namedtuple("LrsiOut", "l0 l1 l2 l3 den out")
LrsiShared = namedtuple("LrsiShared", "gs index")     # old LaguerreRSI.c: file statics lr_init / lr_prevRSI shared by the listed calls
LRSI_FORMS = ("book", "tasc2025")
LRSI_SEEDS = ("zero", "price")


def lrsi_article(g, g_l0=None, form="book", seed="zero", hold0=0.0):
    """The Fig. 14.8 Laguerre RSI as a model. Keyword hooks (default = the source) are the controls / INFO variants:
        g_l0   gamma used in the L0 line only (NCG: g + 1/1000); L1..L3 keep g
        form   "book" (Fig. 14.8: L1 = -g*L0 + L0[1] + g*L1[1]) | "tasc2025" (NC25, review L-6: L1 = -g*L0[1] + L0[1] + g*L1[1],
               a delayed EMA, not an allpass)
        seed   "zero" (the source, L-1) | "price" (NCP: the old start-up per instance: on the first call every stage = Close, the
               bar is not computed, the call returns 0.5, l0 = l3 = Close and den = 0 on that row; the hold is not touched)
        hold0  initial held RSI (source 0; NCH: 1/2, L-2)"""
    if form not in LRSI_FORMS:
        raise ValueError("form must be one of %s, got %r" % (LRSI_FORMS, form))
    if seed not in LRSI_SEEDS:
        raise ValueError("seed must be one of %s, got %r" % (LRSI_SEEDS, seed))
    return LrsiModel(g=float(g), g_l0=None if g_l0 is None else float(g_l0), form=form, seed=seed, hold0=float(hold0))


def _lrsi_stages(c, g, gl, form, p):
    """One bar of the four stages, book term order (p = previous [L0, L1, L2, L3]). Returns [L0, L1, L2, L3]."""
    L0 = (1.0 - gl) * c + gl * p[0]
    if form == "book":
        L1 = -g * L0 + p[0] + g * p[1]
        L2 = -g * L1 + p[1] + g * p[2]
        L3 = -g * L2 + p[2] + g * p[3]
    else:                                                     # tasc2025: the previous upstream value in the first term
        L1 = -g * p[0] + p[0] + g * p[1]
        L2 = -g * p[1] + p[1] + g * p[2]
        L3 = -g * p[2] + p[2] + g * p[3]
    return [L0, L1, L2, L3]


def _lrsi_cucd(L):
    """CU, CD of Fig. 14.8 (adjacent pairs, >= to CU, else CD; accumulated in the book's order)."""
    cu = cd = 0.0
    for a, b in ((L[0], L[1]), (L[1], L[2]), (L[2], L[3])):
        if a >= b:
            cu = cu + a - b
        else:
            cd = cd + b - a
    return cu, cd


def simulate_lrsi(m, x):
    """Run an LrsiModel on x: LrsiOut(l0, l1, l2, l3, den = CU + CD, out) arrays (float64)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    o = {k: np.empty(n) for k in LrsiOut._fields}
    gl = m.g if m.g_l0 is None else m.g_l0
    L = [0.0] * 4
    rsi = m.hold0
    for t in range(n):
        c = float(x[t])
        if m.seed == "price" and t == 0:
            L = [c] * 4
            for k, v in zip(("l0", "l1", "l2", "l3", "den", "out"), (c, c, c, c, 0.0, 0.5)):
                o[k][t] = v
            continue
        L = _lrsi_stages(c, m.g, gl, m.form, L)
        cu, cd = _lrsi_cucd(L)
        if cu + cd != 0:
            rsi = cu / (cu + cd)
        for k, v in zip(("l0", "l1", "l2", "l3", "den", "out"), (L[0], L[1], L[2], L[3], cu + cd, rsi)):
            o[k][t] = v
    return LrsiOut(**o)


def lrsi_superseded(gs, index=0):
    """Model handle for [imp]: the OLD LaguerreRSI.c (LaguerreRSI_Superseded) called once per bar for each gamma in gs (call order);
    `index` = which instance."""
    return LrsiShared(gs=tuple(float(g) for g in gs), index=index)


def simulate_lrsi_shared(gs, xs):
    """The OLD LaguerreRSI.c, superseded (read 2026-11-19; review L-1 / L-2 / L-3). One call slot per (gamma, input) in the
    generator's ACTUAL call order; per slot its own four series(0, 2) stages; TWO file statics shared by every slot:
        lr_init     the first call with Close[0] > 0 (of the whole run, any slot) sets its stages to Close, does not compute the bar
                    and returns 0.5; every later call of every slot finds lr_init = 1 and computes from its zero history (= the source)
        lr_prevRSI  starts at 0.5; on a CU + CD == 0 row ANY slot returns the last ratio written by ANY slot
    The file's own `if(is(INITRUN))` resets never run in a generated script (it returns at INITRUN before any indicator call), so a
    second [Test] press without a Zorro restart would seed nothing (c). Returns [LrsiOut] per slot (den = 0 on the seed row)."""
    nb = len(xs[0])
    xs = [np.asarray(x, dtype=float) for x in xs]
    outs = [{k: np.empty(nb) for k in LrsiOut._fields} for _ in xs]
    Ls = [[0.0] * 4 for _ in xs]
    init, prev = 0, 0.5
    for t in range(nb):
        for k, (g, x) in enumerate(zip(gs, xs)):
            c = float(x[t])
            o = outs[k]
            if not init and c > 0:
                Ls[k] = [c] * 4
                init = 1
                for f, v in zip(LrsiOut._fields, (c, c, c, c, 0.0, 0.5)):
                    o[f][t] = v
                continue
            L = Ls[k] = _lrsi_stages(c, g, g, "book", Ls[k])
            cu, cd = _lrsi_cucd(L)
            if cu + cd != 0:
                prev = cu / (cu + cd)
            for f, v in zip(LrsiOut._fields, (L[0], L[1], L[2], L[3], cu + cd, prev)):
                o[f][t] = v
    return [LrsiOut(**o) for o in outs]


def lrsi_l0_filter(g):
    """L0 as one linear filter: (1 - g)/(1 - g z^-1) (an EMA, DC gain 1, ramp lag g/(1 - g))."""
    return Filter(b=(1.0 - g,), a=(g,))


def lrsi_allpass(g):
    """One Laguerre allpass stage A = (z^-1 - g)/(1 - g z^-1) (|A| = 1, DC gain 1, ramp lag (1 + g)/(1 - g))."""
    return Filter(b=(-g, 1.0), a=(g,))


def lrsi_l3_filter(g):
    """L3 = L0 x A^3 as one linear filter (cascade)."""
    f = lrsi_l0_filter(g)
    for _ in range(3):
        f = cascade(f, lrsi_allpass(g))
    return f


def lrsi_h(g, stage, w):
    """H of Laguerre stage `stage` (0..3) at frequency w, PRODUCT form H_L0 x A^stage evaluated directly (no polynomial expansion:
    the expanded L3 cascade loses ~2e-12 at g = 0.8, the product form is exact to rounding)."""
    zi = np.exp(-1j * w)
    return (1.0 - g) / (1.0 - g * zi) * ((zi - g) / (1.0 - g * zi)) ** stage


def lrsi_gain(g, stage, t):
    """|H| of stage `stage` for a sine of period t bars (t = 2: Nyquist)."""
    return float(abs(lrsi_h(g, stage, 2.0 * math.pi / t)))


def lrsi_phase(g, stage, t):
    """arg H in (-pi, pi] of stage `stage` at period t (same convention as phase_at)."""
    return float(np.angle(lrsi_h(g, stage, 2.0 * math.pi / t)))


def lrsi_alt_phase(g, stage):
    """Phase at Nyquist as the checker measures it: 0 if H(-1) >= 0, else pi. H(-1) = (1-g)/(1+g) x (-1)^stage exactly."""
    return 0.0 if stage % 2 == 0 else math.pi


def lrsi_lag(g, stage):
    """Ramp lag (group delay at DC) of stage `stage`, closed form: g/(1 - g) + stage (1 + g)/(1 - g)."""
    return g / (1.0 - g) + stage * (1.0 + g) / (1.0 - g)


def alt_phase(f):
    """Phase at Nyquist exactly as the checker measures it (m_phase_alt): 0 if Re H(-1) >= 0, else pi (H(-1) is real)."""
    return 0.0 if float(np.real(_hz(f, math.pi))) >= 0 else math.pi


_LRSI_ARTICLE_RE = re.compile(r"lrsi_article\((\d{1,4})/(\d{1,4})\)")


def lrsi_article_model(name):
    """Resolve 'lrsi_article(n/d)' (gamma = n/d, 0 < gamma < 1) to an LrsiModel. Restricted grammar, no eval."""
    m = _LRSI_ARTICLE_RE.fullmatch(name) if isinstance(name, str) else None
    if not m or int(m.group(2)) <= 0 or not 0 < int(m.group(1)) < int(m.group(2)):
        return None
    return lrsi_article(int(m.group(1)) / int(m.group(2)))


# [imp] model registry for LRS (c: names chosen here). gamma built as n/d (the generator builds it at run time from the same integers).
for _n, _d in ((1, 2), (7, 10), (4, 5)):
    IMP_MODELS["lrsi_article(%d/%d)" % (_n, _d)] = (lambda n=_n, d=_d: lrsi_article(n / d))
IMP_MODELS["lrsi_article(1/2,hold0=1/2)"] = lambda: lrsi_article(0.5, hold0=1.0 / 2)                    # NCH (INFO)
IMP_MODELS["lrsi_article(1/2,g_l0=1/2+1/1000)"] = lambda: lrsi_article(0.5, g_l0=0.5 + 1.0 / 1000)        # NCG
IMP_MODELS["lrsi_article(1/2,form=tasc2025)"] = lambda: lrsi_article(0.5, form="tasc2025")              # NC25
IMP_MODELS["lrsi_article(1/2,seed=price)"] = lambda: lrsi_article(0.5, seed="price")                    # NCP
IMP_MODELS["lrsi_superseded(1/2,1/2)[0]"] = lambda: lrsi_superseded((0.5, 0.5), 0)                    # NCS (instance 1)
IMP_MODELS["lrsi_superseded(1/2,1/2)[1]"] = lambda: lrsi_superseded((0.5, 0.5), 1)                    # NCT (instance 2, INFO)


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


_PASS_RE = re.compile(r"pass(\d+)")


def pass_n(seed):
    """n of a 'pass<n>' seed string, else None."""
    m = _PASS_RE.fullmatch(seed) if isinstance(seed, str) else None
    return int(m.group(1)) if m else None


def simulate(f, x, seed=None):
    """Run the recursion on array x. Input history before n = 0 is x[0] (Zorro series seeding, gotchas 9d.6).
    Output history before n = 0 (`seed`):
        None or "price"  y[-k] = x[0]  (as h1_check.simulate; = series(Price[0], n) in the .c). Default: SS2/SS3
                         behaviour byte-identical.
        "zero"           y[-k] = 0     (the article's EasyLanguage `Vars: HP(0)`, HP-A).
        "pass<n>"        USE stage 1: output = input for the first n samples (y[k] = x[k], k < n), recursion from
                         sample n on with the real input history and the output history = those passthrough outputs
                         (EasyLanguage `If CurrentBar < n+1 Then US = Price`, V.42:04). Output history before 0
                         (only reachable when n < len(a)) is x[0]."""
    n_pass = pass_n(seed)
    if seed not in (None, "price", "zero") and n_pass is None:
        raise ValueError("seed must be None, 'price', 'zero' or 'pass<n>', got %r" % (seed,))
    x = np.asarray(x, dtype=float)
    y = np.empty(len(x))
    nb, na = len(f.b), len(f.a)
    y_hist = 0.0 if seed == "zero" else x[0]
    for n in range(len(x)):
        if n_pass is not None and n < n_pass:
            y[n] = x[n]
            continue
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
