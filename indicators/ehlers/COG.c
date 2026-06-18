// =============================================================================
// COG.c
// Ehlers, TASC May 2002 — "The Center Of Gravity Oscillator"
//
// Zero-lag oscillator. Computes the balance point of price mass within a
// lookback window. No recursive feedback — pure FIR computation — so the
// output responds to the current bar with no phase delay.
//
// NNFX Role: C1/C2 candidate — zero-lag turning point detection
//
// Inputs:
//   Period  — observation window length (default: 10)
//
// Outputs:
//   return value — COG value (current bar)
//   cog_Trigger  — previous bar's COG value (signal/trigger line)
//
// Signal: COG crosses above cog_Trigger → bullish
//         COG crosses below cog_Trigger → bearish
//
// Usage in test script:
//   var c    = COG(10);
//   var trig = cog_Trigger;
//
// Dependencies: none
//
// Zorro gotchas observed:
//   - Price = (H+L)/2 midpoint — matches Ehlers' original EasyLanguage code
//   - Older bars get HIGHER weights (weight = 1 + count) — not a bug
//     count=0 is the current bar (weight 1), count=Period-1 is oldest (weight Period)
//   - Denominator guard: flat price during warmup can produce Denom=0
//   - series() used for output — gives cog_Trigger = CG[1] automatically
//     COG has no IIR state so series() is safe here (no overwrite pattern)
//   - Negative sign on result: without it, COG falls when price rises
//     The inversion makes CG oscillate in phase with price direction
// =============================================================================

// Global trigger line — accessible from test script after each call
var cog_Trigger = 0;

var COG(int Period) {

    // --- Price input: midpoint bar (H+L)/2 ---
    vars cog_Mid = series((priceHigh() + priceLow()) * 0.5);

    // --- Weighted sum over Period bars ---
    // Numerator:   sum of (position_weight * price)
    // Denominator: sum of prices
    // Weight = (1 + count): count=0 → weight 1 (current bar, lightest)
    //                        count=Period-1 → weight Period (oldest bar, heaviest)
    // Older bars pull the center of gravity backward in time.
    // When recent prices rise above older prices, the heavy old weights
    // pull the center back — negative sign flips this so COG rises with price.
    var cog_Num   = 0;
    var cog_Denom = 0;
    int cog_count;
    for(cog_count = 0; cog_count < Period; cog_count++) {
        cog_Num   += (1 + cog_count) * cog_Mid[cog_count];
        cog_Denom += cog_Mid[cog_count];
    }

    // --- Compute COG with denominator guard ---
    var cog_val = 0;
    if(cog_Denom != 0)
        cog_val = -cog_Num / cog_Denom;

    // --- Build output series for trigger access ---
    // series() shifts automatically each bar — cog_Out[1] = previous bar's COG
    // Safe to use series() here because COG has no IIR feedback to corrupt
    vars cog_Out    = series(cog_val);
    cog_Trigger     = cog_Out[1];

    return cog_Out[0];
}