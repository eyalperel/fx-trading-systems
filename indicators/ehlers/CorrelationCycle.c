///////////////////////////////////////////////////////
// Correlation Cycle Indicator - John F. Ehlers
//
// From:  "Correlation As A Cycle Indicator"
//        TASC V.38:06 (2020), pp. 8-15
//
// MECHANISM (corrected 2026-08-05): quadrature projection.
//   Real = Pearson( Price,  cos(2*pi*n/Period) )
//   Imag = Pearson( Price, -sin(2*pi*n/Period) )
// Price is correlated against a FIXED-PERIOD cosine/sine
// basis - NOT against itself at various lags. This is a
// normalised single-bin DFT over a sliding window, i.e. a
// matched filter at one frequency. It is a LINEAR PROJECTION.
//
//   *** NOT an autocorrelation method. ***
// The Week 12 Day 2 notes and roadmap v4.3 both described
// this as autocorrelation-based and claimed it was
// mechanistically independent of band-pass filtering.
// That was wrong - see docs/research/ for the correction.
// Slutsky-Yule applies: projecting a random walk onto a
// 20-bar cosine yields an oscillating Real/Imag pair.
//
// WHAT IS ACTUALLY TESTABLE HERE (and was not tested in
// Week 11): PHASE COHERENCE. Ehlers claims phase advances
// steadily (~360/Period deg per bar) in "cycle mode" and
// flatlines in "trend mode". Week 11 measured spectral peak
// PROMINENCE, a different property. Phase regularity is a
// distinct, falsifiable claim.
//
// Inputs:  Price   - price series (vars)
//          Period  - assumed cycle period (Ehlers uses 20;
//                    he suggests 14 to bias toward phase lead)
// Outputs (via pointers, all computed in one pass):
//          pReal      - correlation with cosine, [-1, +1]
//          pImag      - correlation with -sine,  [-1, +1]
//          pAngleRaw  - phase BEFORE the monotonicity ratchet
//          pAngle     - phase AFTER  the ratchet (Ehlers')
//          pState     - -1 downtrend / 0 cycle / +1 uptrend
//
// *** RATCHET WARNING - relevant to the null test ***
// Ehlers applies:
//     if(Angle[1] - Angle < 270 && Angle < Angle[1])
//         Angle = Angle[1];
// This FORBIDS phase from decreasing except across a wrap.
// Consequently the "flatline" he presents as evidence of
// trend mode is PARTLY MANUFACTURED by the smoother: when
// phase would retreat, it is held flat. The flatline
// signature will therefore appear on ANY input, including
// pure noise. The null test must use pAngleRaw.
//
// Notes:  Trig in RADIANS. Ehlers publishes DEGREES
//         (360*n/Period -> 2*PI*n/Period; his 9 deg/bar
//         state threshold -> 0.15708 rad/bar).
//         No IIR state - full window recomputation each bar,
//         so no series() call-order constraint.
//         Locals prefixed cyc_ (flat namespace; cc_ is taken
//         by CyberCycle).
///////////////////////////////////////////////////////
void CorrelationCycle(vars Price, int Period,
                      var* pReal, var* pImag,
                      var* pAngleRaw, var* pAngle, var* pState)
{
    int cyc_n;
    var cyc_X, cyc_Y;
    var cyc_Sx, cyc_Sy, cyc_Sxx, cyc_Sxy, cyc_Syy;
    var cyc_denom;
    var cyc_Real = 0, cyc_Imag = 0;

    // ---- Correlate price with a COSINE wave of the given period ----
    cyc_Sx = 0; cyc_Sy = 0; cyc_Sxx = 0; cyc_Sxy = 0; cyc_Syy = 0;
    for(cyc_n = 0; cyc_n < Period; cyc_n++) {
        cyc_X = Price[cyc_n];
        cyc_Y = cos(2.0 * PI * cyc_n / Period);
        cyc_Sx  += cyc_X;
        cyc_Sy  += cyc_Y;
        cyc_Sxx += cyc_X * cyc_X;
        cyc_Sxy += cyc_X * cyc_Y;
        cyc_Syy += cyc_Y * cyc_Y;
    }
    cyc_denom = (Period*cyc_Sxx - cyc_Sx*cyc_Sx) * (Period*cyc_Syy - cyc_Sy*cyc_Sy);
    if(cyc_denom > 0)
        cyc_Real = (Period*cyc_Sxy - cyc_Sx*cyc_Sy) / sqrt(cyc_denom);

    // ---- Correlate price with a NEGATIVE SINE wave (quadrature) ----
    // The derivative of cosine is -sine, so this component leads by
    // exactly 90 degrees - it is the rate-of-change channel.
    cyc_Sx = 0; cyc_Sy = 0; cyc_Sxx = 0; cyc_Sxy = 0; cyc_Syy = 0;
    for(cyc_n = 0; cyc_n < Period; cyc_n++) {
        cyc_X = Price[cyc_n];
        cyc_Y = -sin(2.0 * PI * cyc_n / Period);
        cyc_Sx  += cyc_X;
        cyc_Sy  += cyc_Y;
        cyc_Sxx += cyc_X * cyc_X;
        cyc_Sxy += cyc_X * cyc_Y;
        cyc_Syy += cyc_Y * cyc_Y;
    }
    cyc_denom = (Period*cyc_Sxx - cyc_Sx*cyc_Sx) * (Period*cyc_Syy - cyc_Sy*cyc_Sy);
    if(cyc_denom > 0)
        cyc_Imag = (Period*cyc_Sxy - cyc_Sx*cyc_Sy) / sqrt(cyc_denom);

    *pReal = cyc_Real;
    *pImag = cyc_Imag;

    // ---- Phase angle, Ehlers' construction ----
    // Reproduced exactly, including the unusual 90 + arctan(Real/Imag)
    // form. atan2 would be cleaner but this must be HIS indicator.
    var cyc_angle = 0;
    if(cyc_Imag != 0)
        cyc_angle = 90.0 + atan(cyc_Real / cyc_Imag) * 180.0 / PI;
    if(cyc_Imag > 0)
        cyc_angle = cyc_angle - 180.0;

    *pAngleRaw = cyc_angle;   // UNRATCHETED - use this for the null test

    // ---- Monotonicity ratchet (see RATCHET WARNING above) ----
    static var cyc_prevAngle = 0;
    static int  cyc_seeded   = 0;
    if(!cyc_seeded) { cyc_prevAngle = cyc_angle; cyc_seeded = 1; }

    if(cyc_prevAngle - cyc_angle < 270.0 && cyc_angle < cyc_prevAngle)
        cyc_angle = cyc_prevAngle;

    // ---- Market state ----
    // Ehlers: trend declared when phase rate of change < 9 deg/bar
    // (equivalent to a cycle period >= 40 bars, which he treats as
    // untradeable as a cycle).
    var cyc_dAngle = cyc_angle - cyc_prevAngle;
    var cyc_state = 0;
    // NOTE: Zorro Light-C does not support the ternary operator (? :).
    // Written as an explicit if/else.
    if(fabs(cyc_dAngle) < 9.0) {
        if(cyc_angle >= 0) cyc_state = 1;
        else               cyc_state = -1;
    }

    cyc_prevAngle = cyc_angle;

    *pAngle = cyc_angle;
    *pState = cyc_state;
}