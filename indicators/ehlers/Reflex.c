// =============================================================
// Reflex.c -- Reflex (Ehlers' published form), zero-lag oscillator
//
// Source (a): Ehlers, John F. (2020), "Reflex: A New Zero-Lag
//   Indicator", Technical Analysis of Stocks & Commodities,
//   V.38:02, pp. 6-8, 21, sidebar "EasyLanguage Code For Reflex
//   Indicator". Formula (a), degrees converted to radians:
//     a1 = exp(-1.414*pi / (.5*Length));
//     b1 = 2*a1*cos(1.414*pi / (.5*Length));
//     c2 = b1;  c3 = -a1*a1;  c1 = 1 - c2 - c3;
//     Filt = c1*(Price + Price[1])/2 + c2*Filt[1] + c3*Filt[2];
//     Slope = (Filt[Length] - Filt) / Length;
//     Sum = sum over count = 1..Length of (Filt + count*Slope) - Filt[count];
//     Sum = Sum / Length;
//     MS = .04*Sum*Sum + .96*MS[1];
//     If MS <> 0 Then Reflex = Sum / SquareRoot(MS);
//
// Deviations from the earlier file, fixed (b); review
//   docs/harness/REFLEX_SOURCE_REVIEW.md (05be788):
//   R-1 MS is a per-instance series (was a file-static shared by
//       every call).
//   R-2 the smoothing length is the REAL .5*Length; the
//       SuperSmoother is computed in this file (was the int
//       Length/2 via SuperSmoother2Pole(int)).
//   R-3 the MS weights are built from integers (gotchas 9d.1).
//   R-5 this header.
//
// Constants (D1 rule 1): 1.414 -> sqrt(2), built in rx_k so no
//   expression starts with a literal product (gotchas 9d.8).
//   Ehlers' degrees are converted to radians.
//
// Start-up (a): the source states no rule (R-4). Filt history
//   starts at the first price (series(Price[0], ...), gotchas 9d.6),
//   MS starts at 0. (b) MS memory is 0.96^n: its start-up effect is
//   below 1e-12 after 677 bars; treat the first ~700 bars as
//   warm-up.
//
// Properties (b), spec [findings]: Sum (exported by ReflexCore) is
//   linear, has DC gain 0 and is zero on a ramp; |Reflex| <= 5
//   exactly (and attained). On flat or ramp input Reflex is
//   rounding noise divided by rounding noise
//   (O_RAMP_ILLCONDITIONED): do not read it there.
// O_ZEROLAG (b): at T = Length the summation stage has phase 0,
//   but the SuperSmoother(Length/2) adds about -0.62 rad at
//   Length = 20 (about 2 bars): Reflex is not zero-lag at its own
//   design period.
//
// STATE: both series() calls are unconditional and come before any
//   use (gotchas 3.1); every instance has its own Filt and MS.
//
// Verification: analysis/harness/specs/RFX_ArticleFidelity.toml
//   (pre-registered 960ae09). NOT verified until that run passes.
// =============================================================

var ReflexCore(vars Price, int Length, var* pSum, var* pMS)
{
    var rx_half = Length;
    rx_half = rx_half/2;
    var rx_k = sqrt(2.0);
    var rx_a1 = exp(-rx_k*PI/rx_half);
    var rx_b1 = 2.0*rx_a1*cos(rx_k*PI/rx_half);
    var rx_c2 = rx_b1;
    var rx_c3 = -rx_a1*rx_a1;
    var rx_c1 = 1.0 - rx_c2 - rx_c3;
    var rx_w1 = 4;
    rx_w1 = rx_w1/100;
    var rx_w2 = 96;
    rx_w2 = rx_w2/100;
    vars rx_Filt = series(Price[0], Length + 2);
    vars rx_MS = series(0, 2);
    rx_Filt[0] = rx_c1*(Price[0] + Price[1])/2.0 + rx_c2*rx_Filt[1] + rx_c3*rx_Filt[2];
    var rx_Slope = (rx_Filt[Length] - rx_Filt[0])/Length;
    var rx_Sum = 0;
    int rx_i;
    for(rx_i = 1; rx_i <= Length; rx_i++)
        rx_Sum += (rx_Filt[0] + rx_i*rx_Slope) - rx_Filt[rx_i];
    rx_Sum = rx_Sum/Length;
    rx_MS[0] = rx_w1*rx_Sum*rx_Sum + rx_w2*rx_MS[1];
    var rx_R = 0;
    if(rx_MS[0] > 0)
        rx_R = rx_Sum/sqrt(rx_MS[0]);
    *pSum = rx_Sum;
    *pMS = rx_MS[0];
    return rx_R;
}

var Reflex(vars Price, int Length)
{
    var rx_s;
    var rx_m;
    return ReflexCore(Price, Length, &rx_s, &rx_m);
}
