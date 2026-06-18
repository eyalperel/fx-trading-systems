// =============================================================================
// FisherTransform.c
// Ehlers, TASC October 2002 — "Using The Fisher Transform"
//
// Converts normalized price into an approximately Gaussian distribution.
// Extreme readings (±2.5) are statistically meaningful reversal signals,
// unlike arbitrary RSI 70/30 levels.
//
// NNFX Role: C1 confirmation indicator (Strategy 1 — FAMA Baseline)
//
// Inputs:
//   Period  — lookback window for channel normalization (default: 10)
//
// Outputs:
//   return value — Fisher Transform value (current bar)
//   ft_Trigger   — previous bar's Fisher value (signal/trigger line)
//
// Signal: Fisher crosses above ft_Trigger → bullish
//         Fisher crosses below ft_Trigger → bearish
//
// Usage in test script:
//   var f    = FisherTransform(10);
//   var trig = ft_Trigger;
//
// Dependencies: none
//
// Zorro gotchas observed:
//   - Price = (H+L)/2 midpoint, not Close — matches Ehlers' original code
//   - Two IIR feedback loops: ft_Value1 (alpha=0.33) and ft_Fish (alpha=0.5)
//   - Both use static vars — series()-then-overwrite is unreliable in includes
//   - Trigger captured BEFORE Fish is updated — gives true previous-bar value
//   - Clamp check at ±0.99, assign ±0.999 — matches Ehlers exactly
// =============================================================================

// Global trigger line — accessible from test script after each call
var ft_Trigger = 0;

var FisherTransform(int Period) {

    // --- Price input: midpoint bar (H+L)/2 ---
    // Ehlers explicitly uses midpoint, not Close, in the original EasyLanguage
    vars ft_Mid = series((priceHigh() + priceLow()) * 0.5);

    // --- Channel: highest high and lowest low over Period bars ---
    var ft_MaxH = MaxVal(ft_Mid, Period);
    var ft_MinL = MinVal(ft_Mid, Period);

    // --- Normalize price to [-1, +1] ---
    // Maps current price position within the Period channel to [-1, +1]
    // Guard against zero range (flat price — unlikely on real data, possible in warmup)
    var ft_raw = 0;
    if(ft_MaxH - ft_MinL > 0)
        ft_raw = 2.0 * ((ft_Mid[0] - ft_MinL) / (ft_MaxH - ft_MinL) - 0.5);

    // --- Stage 1: smooth the normalized input ---
    // EMA with alpha=0.33 (0.33 + 0.67 = 1.0 — proper EMA)
    // Prevents single-bar channel spikes from contaminating the transform input
    static var ft_Value1 = 0;
    ft_Value1 = 0.33 * ft_raw + 0.67 * ft_Value1;

    // --- Clamp to prevent log(0) or log(negative) in the transform ---
    // Check fires at ±0.99; assignment is ±0.999 — matches Ehlers' exact code
    if(ft_Value1 >  0.99) ft_Value1 =  0.999;
    if(ft_Value1 < -0.99) ft_Value1 = -0.999;

    // --- Capture previous Fisher as trigger BEFORE updating Fish ---
    // ft_Trigger holds Fish from the previous bar — this is the signal line
    static var ft_Fish = 0;
    ft_Trigger = ft_Fish;

    // --- Stage 2: Fisher transform + smooth output ---
    // 0.5 * log((1+x)/(1-x)) is arctanh(x) — the Gaussian-shaping transform
    // + 0.5 * ft_Fish is a second EMA (alpha=0.5) applied to the output
    // This light feedback smooths the output without distorting the distribution
    ft_Fish = 0.5 * log((1.0 + ft_Value1) / (1.0 - ft_Value1)) + 0.5 * ft_Fish;

    return ft_Fish;
}