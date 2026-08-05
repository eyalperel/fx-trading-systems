///////////////////////////////////////////////////////
// Alpha-Beta (g-h) Filter - constant-gain tracker
//
// PROVENANCE (corrected 2026-08-05):
//   Previously labelled "Ehlers Kalman Filter". No such
//   article exists in the 102-article TASC library;
//   "Every Little Bit Helps" was mis-mapped to this slot
//   and concerns averaging open+close at Nyquist.
//   This is an alpha-beta (g-h) filter from radar tracking
//   literature (Benedict-Bordner; Kalata tracking index).
//   Renamed accordingly. See git 5255472.
//
// RELATION TO KALMAN:
//   An alpha-beta filter IS the steady-state limit of a
//   Kalman filter for a constant-velocity target with FIXED
//   noise covariances. What is missing is covariance
//   propagation - the part that makes Kalman adaptive.
//   "Optimal minimum-variance estimator" is therefore FALSE
//   for this filter: a fixed gain is optimal only if it
//   happens to match the true process/measurement noise ratio.
//
// Inputs:  Price - price series (vars)
//          Gain  - beta (velocity gain). USABLE RANGE [0.02, 0.20]
//
// Output:  One-step-ahead FORECAST of price. NOT a smoothed
//          estimate of the current bar. See below.
//
// ---------------------------------------------------------
// MEASURED CHARACTERISTICS (input sigma = 1.0, white noise)
// ---------------------------------------------------------
//   Gain   alpha    out sigma   step overshoot
//   0.02   0.200    0.410        21.6%
//   0.05   0.316    0.542        22.6%
//   0.10   0.447    0.688        23.7%
//   0.20   0.632    0.908        26.2%
//   0.246  0.702    1.000  <-- NOISE-NEUTRAL CROSSOVER
//   0.30   0.775    1.100        29.4%   AMPLIFIES NOISE
//   0.60   1.095    1.792        69.5%   AMPLIFIES NOISE
//   0.90   1.342    3.451       124.2%   AMPLIFIES NOISE
//
//   ** Above Gain ~0.246 this filter AMPLIFIES noise. **
//   ** Above Gain 0.5, alpha = sqrt(2*Gain) > 1 and the    **
//   ** position update overshoots the measurement EVERY bar.**
//   Earlier documentation said "Gain 0.6-0.9 typical".
//   That guidance was wrong and is retracted.
//
// ---------------------------------------------------------
// STRUCTURAL PROPERTY - READ BEFORE USING
// ---------------------------------------------------------
//   Output LEADS price by exactly 1.000 bar on a ramp, at
//   ALL gains. Cause: the recursion omits the alpha-beta
//   prediction step (x_pred = x[1] + v[1]) and instead adds
//   velocity post-hoc, double-counting it.
//
//   Consequence: this is a ONE-STEP-AHEAD FORECAST, not a
//   current-state estimate. It WILL overshoot at turning
//   points, because extrapolated velocity points the wrong
//   way exactly when the trend reverses.
//
//   DO NOT document or use this as a smoother. A plain EMA
//   smooths harder at equivalent settings:
//     alpha-beta Gain=0.10 -> sigma 0.688, leads 1.00 bar
//     EMA alpha=0.40       -> sigma 0.496, lags  1.50 bars
//   The alpha-beta buys a 1-bar lead, NOT smoothness.
//   Whether that lead has value is an empirical question.
//
// STABILITY: char. poly L^2 - (2-alpha-Gain)L + (1-alpha).
//   Spectral radius < 1 up to Gain ~1.06, so it will not
//   diverge - it simply stops doing anything useful long
//   before that point.
//
// CONFIRMED SOUND: sqrt(Gain*2) is NOT a typo. It is the
//   critical-damping relation beta = alpha^2 / 2, i.e.
//   alpha = sqrt(2*beta), standard in alpha-beta design.
//
// Notes:   Uses series() for state - call unconditionally
//          every bar (allocation is by call order).
//          Locals prefixed ab_ (flat namespace).
// Theory:  docs/indicators/ (Week 12 Day 2 analysis)
///////////////////////////////////////////////////////
var AlphaBetaFilter(vars Price, var Gain)
{
    // alpha (position gain) derived from beta (velocity gain)
    // via the critical-damping relation beta = alpha^2/2.
    var ab_alpha = sqrt(Gain * 2.0);

    // State: position estimate and velocity estimate.
    // Position seeded at Price[0]; velocity seeded at 0
    // (no trend assumed at startup).
    var* ab_Kf  = series(Price[0], 2);
    var* ab_Vel = series(0.0, 2);

    // Residual against the PREVIOUS ESTIMATE (not a prediction -
    // this is the structural deviation that produces the 1-bar lead)
    var ab_dk = Price[0] - ab_Kf[1];

    // Position correction
    var ab_smooth = ab_Kf[1] + ab_dk * ab_alpha;

    // Velocity correction
    ab_Vel[0] = ab_Vel[1] + Gain * ab_dk;

    // Velocity added on top -> one-step-ahead extrapolation
    ab_Kf[0] = ab_smooth + ab_Vel[0];

    return ab_Kf[0];
}