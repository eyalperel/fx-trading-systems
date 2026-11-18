// =============================================================
// UltimateSmootherE.c — UltimateSmoother (Ehlers' published form)
//
// Source (a): Ehlers, John F. (2024), "The Ultimate Smoother",
//   Technical Analysis of Stocks & Commodities, V.42:04, pp.8-15,
//   sidebar "UltimateSmoother Function, In EasyLanguage".
//   US = input - HP, with the V.42:04 $HighPass (NOT the HP-A of
//   V.32:1 that HighPassFilter.c implements).
//
// CONSTRUCTION (a): output = input - highpass(input). At low
//   frequencies the highpass output is ~0, so the input passes
//   through unchanged. At high frequencies the highpass output
//   ~= input, so the subtraction cancels it. Filtering is by
//   cancellation, not by averaging.
//
// Ehlers' caveat (a, article conclusion 3): output is LESS smooth
//   than SuperSmoother. He recommends SuperSmoother where
//   smoothness matters more than lag.
//
// Constants (D1 rule 1): 1.414 -> sqrt(2), built in us_k so no
//   expression starts with a literal product (b, gotchas 9d.8).
//   Ehlers' degrees are converted to radians.
//
// Start-up (a): the first 3 outputs equal Price (EasyLanguage
//   CurrentBar < 4). us_n is a per-instance counter equal to
//   CurrentBar (1 on this instance's first call); it replaces the
//   global Bar < 4 of the earlier file. (c) series(0, 2) giving
//   us_n[1] = 0 on the first call is expected (gotchas 9d.6);
//   verified by the s20 start-up check (spec finding 7).
//
// Measured properties (b, spec [findings]): DC gain 1, Nyquist
//   gain 0, ramp lag 0. Passband gain is > 1 (peak ~1.27 near
//   T = 1.3 P) and phase at T = P is about -0.62 rad, so the
//   article's "zero lag" holds at DC, not across the pass band
//   (spec O_PASSBAND).
//
// SUFFIX 'E': the earlier, different algorithm is kept as
//   UltimateSmoother_W5_Superseded.c. (b) It does not implement
//   the cited article (PROJECT_STATE section 1.1); see GOTCHAS
//   section 8 for the method used to validate it.
//
// STATE: uses series(), not statics, because Ultimate Bands
//   requires TWO independent instances per bar (centre line at
//   Length, smooth true range at STRLength). series() allocates
//   by call order, valid only while every call is unconditional
//   and the call sequence never varies between bars
//   (GOTCHAS 3.1). Both series() calls (us_n, us_US) precede the
//   early return. Do not place a call to this inside an if().
//
// Locals prefixed us_ (GOTCHAS 1.3, flat namespace).
//
// Parameters:
//   Price  : input series
//   Period : critical period in bars (article uses 20)
//
// Returns: smoothed value, unity DC gain
//
// Verification: analysis/harness/specs/USE_ArticleFidelity.toml
//   (pre-registered ca4454b). NOT verified until that run passes.
// =============================================================

var UltimateSmootherE(vars Price, int Period) {
    var us_k = sqrt(2.0);
    var us_a1 = exp(-us_k*PI/Period);
    var us_b1 = 2.0*us_a1*cos(us_k*PI/Period);
    var us_c2 = us_b1;
    var us_c3 = -us_a1*us_a1;
    var us_c1 = (1.0 + us_c2 - us_c3)/4.0;
    vars us_n = series(0, 2);
    us_n[0] = us_n[1] + 1;
    vars us_US = series(Price[0], 3);
    if(us_n[0] < 4) {
        us_US[0] = Price[0];
        return us_US[0];
    }
    us_US[0] = (1.0 - us_c1)*Price[0] + (2.0*us_c1 - us_c2)*Price[1]
             - (us_c1 + us_c3)*Price[2] + us_c2*us_US[1] + us_c3*us_US[2];
    return us_US[0];
}
