// UltimateSmoother_W5_Superseded.c
//
// SUPERSEDED - RETAINED AS A RECORD, NOT FOR USE.
// Production code should call UltimateSmootherE.c, which implements
// Ehlers' published filter. This file is kept because the Week 5
// reasoning behind it is instructive, not because it is useful.
//
// WHAT THIS IS
//   A SuperSmoother2Pole with a small fraction of the residual
//   (Price - SuperSmoother) added back, intended to cancel lag.
//
// WHAT IT IS NOT
//   It does not implement Ehlers, "The Ultimate Smoother" (TASC 2024),
//   despite being written against that article. The published filter is
//   Price - HighPass(Price); this is SuperSmoother + gamma*residual.
//   Different mechanism, different result.
//
// MEASURED LAG (ramp method, Test_USLag.c, Period = 20)
//   UltimateSmootherE  (published)   0.0000 bars
//   this file                        3.8725 bars
//   SuperSmoother2Pole               4.0387 bars
//   Removes 0.166 bars of SuperSmoother's lag - 4.1%.
//   Week 5 recorded this file as VALIDATED and "near-zero-lag".
//
// WHY THE APPROACH CANNOT WORK
//   The residual Price - SuperSmoother contains the filter's lag AND the
//   noise the filter removed, summed into one number. No coefficient can
//   add back one without the other: expanding the correction gives
//   gamma*Price + (1-gamma)*SuperSmoother, a blend. Any lag recovered
//   arrives with proportional noise. The published filter avoids this by
//   computing the fast component separately with a high-pass filter and
//   subtracting it, rather than trying to split a residual.
//
// VALIDATION NOTE
//   Lag must be measured on a synthetic ramp (Test_USLag.c), not by
//   detrended cross-correlation. Detrending removes the trend a ramp
//   consists of, and the resulting correlation reports ~0 lag for filters
//   that plainly lag. The original header specified cross-correlation.
//
// INTERFACE (unchanged from the original file)
//   Price  : vars pointer to a price series, e.g. closing prices
//   Period : cutoff period in bars
//   Returns: smoothed value. Needs ~2x Period bars of warmup before the
//            output is reliable. cos() takes radians.
//
// Reviewed and relabelled Week 14 session 1, 2026-08-31.
// See docs/indicators/UltimateSmoother_Lag_2026-08-12.md and Week13_Notes.md 3.1

var UltimateSmoother_W5_Superseded(vars Price, int Period) {
    // --- Stage 1: SuperSmoother coefficients (2-pole Butterworth) ---
    var c1 = exp(-sqrt(2.0) * PI / Period);
    var b1 = 2.0 * c1 * cos(sqrt(2.0) * PI / Period);
    var c2 = b1;
    var c3 = -c1 * c1;
    var c0 = (1.0 - b1 + c1 * c1) / 2.0;

    // --- Stage 2: "correction" coefficient ---
    // NOTE: gamma is numerically identical to c0 above. Since c3 = -c1*c1,
    // (1 - c2 - c3)/2 is the same expression as (1 - b1 + c1*c1)/2. It is
    // SuperSmoother's own input coefficient under a different name, not a
    // separately derived correction term. At Period = 20 its value is
    // 0.0395 - far too small to offset four bars of lag, which is why this
    // filter removes only 4.1% of it.
    var gamma = (1.0 - c2 - c3) / 2.0;

    // --- Filter states ---
    var* SS   = series(Price[0], 3);   // SuperSmoother state
    var* US   = series(Price[0], 3);   // Ultimate Smoother state

    // --- During warmup: return price directly ---
    if(Init) {
        SS[0] = Price[0];
        US[0] = Price[0];
        return Price[0];
    }

    // --- Stage 1: Apply SuperSmoother ---
    SS[0] = c0 * (Price[0] + Price[1])
          + c2 * SS[1]
          + c3 * SS[2];

    // --- Stage 2: Compute residual ---
    // The residual is lag and removed noise summed into one number. It is
    // used raw - it is NOT smoothed, despite what the original comment here
    // claimed. Nothing in this file isolates the lag component from the
    // noise component, and no scalar coefficient could.
    var Residual = Price[0] - SS[0];

    // --- Stage 3: Add corrected residual back to SuperSmoother ---
    // gamma scales how aggressively we correct for lag
    US[0] = SS[0] + gamma * (Residual + US[1] - SS[1]);

    return US[0];
}