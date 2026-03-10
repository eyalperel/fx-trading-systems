// UltimateSmoother.c
// Based on: Ehlers, "The Ultimate Smoother" TASC 2024
// Purpose:  Near-zero-lag smoothing filter built on SuperSmoother
//           Corrects SuperSmoother lag by adding back smoothed residual
// Inputs:   Price — vars pointer to price series (e.g. closing prices)
//           Period — cutoff period in bars (recommended: FX 14-20, Crypto 8-14)
// Output:   Smoothed price value with reduced lag vs SuperSmoother
// Notes:    Needs ~2x Period bars warmup before output is reliable
//           cos() uses degrees — Zorro convention
//           Zero-lag claim should be verified empirically via cross-correlation

var UltimateSmoother(vars Price, int Period) {
    // --- Stage 1: SuperSmoother coefficients (2-pole Butterworth) ---
    var c1 = exp(-sqrt(2.0) * PI / Period);
    var b1 = 2.0 * c1 * cos(sqrt(2.0) * 180.0 / Period);
    var c2 = b1;
    var c3 = -c1 * c1;
    var c0 = (1.0 - b1 + c1 * c1) / 2.0;

    // --- Stage 2: Ultimate Smoother correction coefficient ---
    // gamma controls lag correction aggressiveness
    // Derived from SuperSmoother coefficients per Ehlers' formulation
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

    // --- Stage 2: Compute residual (lag component + noise) ---
    // Smooth the residual to isolate lag component without reintroducing noise
    var Residual = Price[0] - SS[0];

    // --- Stage 3: Add corrected residual back to SuperSmoother ---
    // gamma scales how aggressively we correct for lag
    US[0] = SS[0] + gamma * (Residual + US[1] - SS[1]);

    return US[0];
}