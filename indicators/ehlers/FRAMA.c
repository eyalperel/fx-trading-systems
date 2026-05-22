// =============================================================
// FRAMA.c — Fractal Adaptive Moving Average
// Author: John Ehlers | Implementation: Week 9
// Reference: "Fractal Adaptive Moving Averages" TASC
//
// Adapts EMA speed using fractal dimension of price:
//   D → 1 (trending)  → alpha → 1.0  (fast, tracks price)
//   D → 2 (noisy)     → alpha → 0.01 (slow, ignores noise)
//
// Parameters:
//   T : half-period (full window = 2T bars, default T=16)
//
// Returns: FRAMA value (adaptive EMA of median price)
// =============================================================

var FRAMA(int T) {

    // --- Build High/Low series for range computation ---
    vars frama_High = series(priceHigh());
    vars frama_Low  = series(priceLow());

    // --- Median price ---
    var frama_price = (priceHigh() + priceLow()) / 2.0;

    // --- Box 1: bars 0 to T-1 (most recent half) ---
    var frama_Hi1 = frama_High[0];
    var frama_Lo1 = frama_Low[0];
    int frama_i;
    for(frama_i = 1; frama_i < T; frama_i++) {
        if(frama_High[frama_i] > frama_Hi1) frama_Hi1 = frama_High[frama_i];
        if(frama_Low[frama_i]  < frama_Lo1) frama_Lo1 = frama_Low[frama_i];
    }
    var frama_N1 = (frama_Hi1 - frama_Lo1) / T;

    // --- Box 2: bars T to 2T-1 (older half) ---
    var frama_Hi2 = frama_High[T];
    var frama_Lo2 = frama_Low[T];
    for(frama_i = T+1; frama_i < 2*T; frama_i++) {
        if(frama_High[frama_i] > frama_Hi2) frama_Hi2 = frama_High[frama_i];
        if(frama_Low[frama_i]  < frama_Lo2) frama_Lo2 = frama_Low[frama_i];
    }
    var frama_N2 = (frama_Hi2 - frama_Lo2) / T;

    // --- Full window: bars 0 to 2T-1 ---
    var frama_Hi3 = frama_Hi1;
    var frama_Lo3 = frama_Lo1;
    for(frama_i = T; frama_i < 2*T; frama_i++) {
        if(frama_High[frama_i] > frama_Hi3) frama_Hi3 = frama_High[frama_i];
        if(frama_Low[frama_i]  < frama_Lo3) frama_Lo3 = frama_Low[frama_i];
    }
    var frama_N3 = (frama_Hi3 - frama_Lo3) / (2.0 * T);

    // --- IIR state: initialize to price on first call ---
    static var frama_prev = 0;
    if(frama_prev == 0) frama_prev = frama_price;

    // --- Guard: flat price → no update ---
    if(frama_N3 <= 0) return frama_prev;

    // --- Fractal dimension ---
    var frama_D = (log(frama_N1 + frama_N2) - log(frama_N3)) / log(2.0);

    // --- Adaptive alpha ---
    var frama_alpha = exp(-4.6 * (frama_D - 1.0));
    if(frama_alpha > 1.0)  frama_alpha = 1.0;
    if(frama_alpha < 0.01) frama_alpha = 0.01;

    // --- EMA update ---
    var frama_out = frama_alpha * frama_price + (1.0 - frama_alpha) * frama_prev;
    frama_prev = frama_out;

    return frama_out;
}