// =============================================================
// UltimateSmootherE.c — UltimateSmoother (Ehlers' published form)
//
// Reference: Ehlers, John F. (2024), "The Ultimate Smoother",
//   Technical Analysis of Stocks & Commodities, V.42:04, pp.8-15.
//   Coefficients and recursion transcribed from the article's
//   "UltimateSmoother Function, In EasyLanguage" sidebar.
//
// CONSTRUCTION: output = input - highpass(input). At low
//   frequencies the highpass output is ~0, so the input passes
//   through unchanged in BOTH amplitude and phase — this is
//   where the zero-lag claim comes from. At high frequencies the
//   highpass output ~= input, so the subtraction cancels it.
//   Filtering is by cancellation, not by averaging.
//
// Ehlers' own caveat: output is LESS smooth than SuperSmoother,
//   because the cancellation is imperfect. He recommends
//   SuperSmoother where smoothness matters more than lag.
//
// SUFFIX 'E': coexists with the pre-existing UltimateSmoother.c,
//   which implements a DIFFERENT algorithm (SuperSmoother plus a
//   scaled residual correction, gamma = (1-c2-c3)/2). That file
//   does not match the cited article and its Week 5 validation
//   used detrended cross-correlation — a method later found to
//   report 0.00 bars lag for an EMA with true lag 1.50
//   (GOTCHAS section 8). Both are kept for comparison.
//
// STATE: uses series(), not statics, because Ultimate Bands
//   requires TWO independent instances per bar (centre line at
//   Length, smooth true range at STRLength). series() allocates
//   by call order — valid only while every call is unconditional
//   and the call sequence never varies between bars
//   (GOTCHAS 3.1). Do not place a call to this inside an if().
//
// Locals prefixed us_ (GOTCHAS 1.3 — flat namespace).
//
// Parameters:
//   Price  : input series
//   Period : critical period in bars (article uses 20)
//
// Returns: smoothed value, unity DC gain
// =============================================================

var UltimateSmootherE(vars Price, int Period) {

    // --- Coefficients (Ehlers publishes degrees; radians here) ---
    var us_a1 = exp(-1.414 * PI / Period);
    var us_b1 = 2.0 * us_a1 * cos(1.414 * PI / Period);
    var us_c2 = us_b1;
    var us_c3 = -us_a1 * us_a1;
    var us_c1 = (1.0 + us_c2 - us_c3) / 4.0;

    // --- Output state: 3 bars (current + two feedback terms) ---
    vars us_US = series(Price[0], 3);

    // --- Warmup: article seeds with the raw price for 4 bars ---
    if(Bar < 4) {
        us_US[0] = Price[0];
        return us_US[0];
    }

    // --- Ehlers' recursion ---
    // Numerator coefficients sum to (1 - c2 - c3), which is also
    // the denominator — hence unity DC gain.
    us_US[0] = (1.0 - us_c1) * Price[0]
             + (2.0 * us_c1 - us_c2) * Price[1]
             - (us_c1 + us_c3) * Price[2]
             + us_c2 * us_US[1]
             + us_c3 * us_US[2];

    return us_US[0];
}
