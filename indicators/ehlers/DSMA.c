// =============================================================
// DSMA.c — Deviation-Scaled Moving Average
// Author: John Ehlers | Implementation: Week 9
// Reference: "The Deviation-Scaled Moving Average" TASC
//
// Adapts EMA speed using volatility normalization:
//   Large deviation from average → alpha large → tracks fast
//   Small deviation (noise)     → alpha small → barely moves
//
// The deviation is z-scored (divided by rolling StdDev),
// making alpha computation scale-independent. Same parameters
// work across EUR/USD and BTC/USD without retuning.
//
// Dependencies (include in test script before this file):
//   SuperSmoother2Pole.c
//
// Parameters:
//   dsma_rf : pre-computed RoofingFilter value (current bar)
//             computed ONCE in test script, passed in here
//             avoids double-call corruption
//   Period  : lookback for StdDev + SuperSmoother (default 20)
//
// Returns: DSMA value (adaptive EMA of median price)
// =============================================================

var DSMA(var dsma_rf, int Period) {

    // --- Median price ---
    var dsma_price = (priceHigh() + priceLow()) / 2.0;

    // --- Accumulate RoofingFilter history in a series ---
    // series() pushes dsma_rf into index [0] each bar,
    // shifting older values to [1], [2], ... automatically
    var* dsma_rf_hist = series(dsma_rf);

    // --- Rolling standard deviation of RoofingFilter output ---
    // RoofingFilter is zero-mean by design → mean ≈ 0
    // so variance = mean of squares (RMS variance)
    var dsma_sum2 = 0;
    int dsma_i;
    for(dsma_i = 0; dsma_i < Period; dsma_i++)
        dsma_sum2 += dsma_rf_hist[dsma_i] * dsma_rf_hist[dsma_i];
    var dsma_var = dsma_sum2 / Period;

    // --- IIR state ---
    static var dsma_prev = 0;
    if(is(INITRUN)) dsma_prev = 0;   // statics persist across runs

    // --- Guard: flat price → no update ---
    if(dsma_var <= 0) return dsma_prev;
    var dsma_sigma = sqrt(dsma_var);

    // --- Z-score: current deviation in units of typical deviation ---
    // Absolute value: we want magnitude, not direction
    var dsma_zscore = dsma_rf / dsma_sigma;
    if(dsma_zscore < 0) dsma_zscore = -dsma_zscore;

    // --- Promote z-score scalar to series for SuperSmoother ---
    // SuperSmoother2Pole requires vars (series), not var (scalar)
    var* dsma_z_series = series(dsma_zscore);

    // --- Smooth z-score to stabilize alpha ---
    // Raw z-score is noisy — SuperSmoother prevents alpha from
    // jumping bar-to-bar due to single-bar outliers
    var dsma_alpha = SuperSmoother2Pole(dsma_z_series, Period);

    // --- Clamp to valid EMA range [0, 1] ---
    if(dsma_alpha > 1.0) dsma_alpha = 1.0;
    if(dsma_alpha < 0.0) dsma_alpha = 0.0;

    // --- Adaptive EMA update ---
    var dsma_out = dsma_alpha * dsma_price + (1.0 - dsma_alpha) * dsma_prev;
    dsma_prev = dsma_out;

    return dsma_out;
}
