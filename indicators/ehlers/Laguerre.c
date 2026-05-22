// =============================================================
// Laguerre.c — Laguerre Filter
// Author: John Ehlers | Implementation: Week 9
// Reference: "Laguerre Filters" TASC
//
// Four-stage Laguerre polynomial chain. Achieves smoothing
// equivalent to a long-period EMA with lag of a short-period
// EMA. Basis function efficiency — each stage adds frequency
// resolution, not additional lag.
//
// Parameters:
//   gamma : memory depth, range [0, 1] (default 0.5)
//     → 0 : no smoothing, output tracks price
//     → 1 : infinite smoothing, output frozen
//
// Returns: Laguerre filtered price
// =============================================================

var Laguerre(var gamma) {

    // --- Median price ---
    var lag_price = (priceHigh() + priceLow()) / 2.0;

    // --- IIR state: previous values of each stage ---
    static var lag_L0 = 0;
    static var lag_L1 = 0;
    static var lag_L2 = 0;
    static var lag_L3 = 0;

    // Initialize all stages to price on first call
    if(lag_L0 == 0) {
        lag_L0 = lag_price;
        lag_L1 = lag_price;
        lag_L2 = lag_price;
        lag_L3 = lag_price;
    }

    // --- Four-stage Laguerre chain ---
    // L0: single-pole IIR (EMA with alpha = 1-gamma)
    // L1-L3: each peels a frequency band from the residual
    var lag_L0_new = (1.0 - gamma) * lag_price + gamma * lag_L0;
    var lag_L1_new = -gamma * lag_L0_new + lag_L0 + gamma * lag_L1;
    var lag_L2_new = -gamma * lag_L1_new + lag_L1 + gamma * lag_L2;
    var lag_L3_new = -gamma * lag_L2_new + lag_L2 + gamma * lag_L3;

    // --- Update state ---
    lag_L0 = lag_L0_new;
    lag_L1 = lag_L1_new;
    lag_L2 = lag_L2_new;
    lag_L3 = lag_L3_new;

    // --- Weighted output: binomial 1-2-2-1 weights ---
    // Middle stages doubled — carry most balanced frequency content
    return (lag_L0 + 2.0*lag_L1 + 2.0*lag_L2 + lag_L3) / 6.0;
}