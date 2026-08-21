// =============================================================
// Laguerre.c — Laguerre Filter (4-stage, book version)
// Author: John Ehlers | Implementation: Week 9
//
// Reference: Ehlers, John F. (2004), "Cybernetic Analysis for
//   Stocks and Futures", Wiley. Chapter 14, Figure 14.5.
//   Input is the median price (H+L)/2; L0 is an EMA-seeded
//   single-pole section; four stages; binomial 1-2-2-1 weights.
//
// NOT the TASC 2025 article "Laguerre Filters" — that variant
//   is a DIFFERENT algorithm (UltimateSmoother-seeded L0, five
//   stages L0-L4, 1-4-6-4-1 weights, gamma 0.8, Close input)
//   and is implemented separately. Corrected Week 13 Day 2:
//   header previously cited the article for book code.
//
// Four-stage Laguerre polynomial chain. Achieves smoothing
// equivalent to a long-period EMA with lag of a short-period
// EMA. Basis function efficiency — each stage adds frequency
// resolution, not additional lag.
//
// Parameters:
//   gamma : memory depth, range [0, 1]
//     NOTE ON THE DEFAULT. Figure 14.5 declares gamma(.8) for the
//     FILTER. 0.5 is the default of the Laguerre RSI in Figure
//     14.8, a different indicator on a later page. Week 9 adopted
//     0.5 for this file; no reason is recorded and none is
//     inferred. It is a legitimate parameter choice, but it is
//     NOT the book's value for this filter. Verified against the
//     source Week 13 Day 3.
//     Also note Fig 14.5 takes (H+L)/2 as input, which this file
//     does; Fig 14.8's RSI takes Close.
//     -> 0 : no smoothing, output tracks price
//     -> 1 : infinite smoothing, output frozen
//
// State: IIR state is held in statics, which persist for the
//   lifetime of the LOADED SCRIPT — across repeated [Test]
//   presses and across Train->Test, not just across bars. The
//   reset is keyed to is(INITRUN) so output does not depend on
//   whether the script happened to be recompiled. See
//   docs/ZORRO_LIGHTC_GOTCHAS.md section 3.
//
// Returns: Laguerre filtered price
// =============================================================

var Laguerre(var gamma) {

    // --- IIR state: previous values of each stage ---
    static var lag_L0 = 0;
    static var lag_L1 = 0;
    static var lag_L2 = 0;
    static var lag_L3 = 0;
    static int lag_init = 0;

    // --- Run-scoped reset ---------------------------------------
    // Clear the seed flag only. Prices are NOT read here: during
    // INITRUN they may not be loaded yet. Seeding happens below,
    // on the first bar that actually carries a valid price.
    if(is(INITRUN)) lag_init = 0;

    // --- Median price ---
    var lag_price = (priceHigh() + priceLow()) / 2.0;

    // No valid price yet — do not seed or advance the filter.
    if(lag_price <= 0) return 0;

    // --- Seed all stages to price on the first valid bar --------
    // Flag-based, not value-based. The old test was
    // "if(lag_L0 == 0)", which cannot fire when the statics hold
    // a leftover non-zero value from a previous run.
    if(!lag_init) {
        lag_L0 = lag_price;
        lag_L1 = lag_price;
        lag_L2 = lag_price;
        lag_L3 = lag_price;
        lag_init = 1;
    }

    // --- Four-stage Laguerre chain ---
    // L0: single-pole IIR (EMA with alpha = 1-gamma)
    // L1-L3: each peels a frequency band from the residual
    // Note: term 1 uses the NEW upstream value, term 2 the OLD.
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
