// =============================================================
// LaguerreRSI.c — Laguerre RSI
//
// Reference: Ehlers, John F. (2004), "Cybernetic Analysis for
//   Stocks and Futures", Wiley. Chapter 14, Figure 14.8, p.221.
//   Transcribed from the book on 2026-08-13, verified against the
//   source text — not reconstructed from memory.
//
// WHAT IT DOES. Classic RSI sorts N raw price changes into "up"
// and "down" piles and takes the ratio. This sorts THREE filtered
// differences into the same two piles:
//
//     L0 vs L1,   L1 vs L2,   L2 vs L3
//
// Each pair asks "is the newer stage above the older one?" — if
// yes the gap goes to CU, if no to CD. The four L values already
// contain the history, so three comparisons stand in for fourteen.
// Ehlers calls this a time warp: a long effective memory held in
// four numbers rather than a stored window.
//
// THREE POINTS EASY TO GET WRONG, all verified against Fig 14.8:
//   1. Comparisons are ADJACENT pairs, not L0 against L3.
//   2. Input is Close. The Laguerre FILTER on p.216 takes (H+L)/2;
//      this does not. Same author, adjacent pages, different input.
//   3. Output is 0..1 with neutral at 0.5 — NOT the -1..+1 of
//      RSIH. Ehlers plots the 0.2 and 0.8 levels.
//
// SATURATION IS EXPECTED, not a defect. With only three
//   comparisons, the four stages fall into order whenever price
//   trends, so CD (or CU) reaches zero and the output pins at
//   EXACTLY 1.0 or 0.0. Ehlers describes the excursions as "lock
//   to lock" and Figure 14.10 shows long flat stretches. The
//   consequence: during a trend the indicator reports THAT it is
//   trending but stops reporting how strongly. Registered
//   prediction P-LR1 puts this at 35-55% of bars.
//
// EHLERS' TRADING RULES ARE NOT IMPLEMENTED HERE. He suggests
//   buying when the line crosses back above 0.2 and selling when
//   it crosses back below 0.8 — trading the exits from saturation
//   rather than the levels. Those fire on a CROSSING, so they give
//   no answer between crossings, which a C2 confirmation must.
//   The caller decides state; see the registered predictions file
//   for the C-1 interpretation (>= 0.5 up) and for the
//   crossing-window variant deferred to strategy level.
//
// STATE: four series(), not statics, because each stage needs both
//   its current and previous value in the same bar. The
//   series()-then-write pattern is required here — the value
//   depends on the series' own history, so it cannot be passed
//   into series() (contrast GOTCHAS 3.2, where it could).
//   Allocation is by call order and every call is unconditional
//   (GOTCHAS 3.1).
//
// Locals prefixed lr_ (GOTCHAS 1.3).
//
// Parameters:
//   Close : close series
//   gamma : damping factor, book default 0.5. Higher = each stage
//           trails further behind, so more smoothing and more lag.
//
// Returns: 0..1, neutral 0.5. Returns 0.5 when CU+CD is zero
//   (all four stages equal — flat price).
// =============================================================

var LaguerreRSI(vars Close, var gamma) {

    vars lr_L0 = series(0, 2);
    vars lr_L1 = series(0, 2);
    vars lr_L2 = series(0, 2);
    vars lr_L3 = series(0, 2);

    // Seed all stages to price on the first valid bar. Without
    // this the stages ramp from zero to price level over the
    // warmup (GOTCHAS 3.3). Flag-based, not value-based, and
    // cleared at INITRUN so it cannot be defeated by leftover
    // state from a previous run (GOTCHAS 9b.1, 9b.2).
    static int lr_init = 0;
    if(is(INITRUN)) lr_init = 0;
    if(!lr_init && Close[0] > 0) {
        lr_L0[0] = Close[0]; lr_L0[1] = Close[0];
        lr_L1[0] = Close[0]; lr_L1[1] = Close[0];
        lr_L2[0] = Close[0]; lr_L2[1] = Close[0];
        lr_L3[0] = Close[0]; lr_L3[1] = Close[0];
        lr_init = 1;
        return 0.5;
    }

    // --- Four-stage Laguerre chain (Fig 14.8) ---
    // L0 is a plain EMA. L1-L3 are allpass delays: note each uses
    // the CURRENT upstream value in the first term and the
    // PREVIOUS in the second. Reversing that turns the allpass
    // into a lowpass — which is what the 2025 TASC article's code
    // does. See LaguerreOsc_Notes.md.
    lr_L0[0] = (1.0 - gamma) * Close[0] + gamma * lr_L0[1];
    lr_L1[0] = -gamma * lr_L0[0] + lr_L0[1] + gamma * lr_L1[1];
    lr_L2[0] = -gamma * lr_L1[0] + lr_L1[1] + gamma * lr_L2[1];
    lr_L3[0] = -gamma * lr_L2[0] + lr_L2[1] + gamma * lr_L3[1];

    // --- Three adjacent comparisons ---
    var lr_CU = 0;
    var lr_CD = 0;

    if(lr_L0[0] >= lr_L1[0]) lr_CU = lr_L0[0] - lr_L1[0];
    else                     lr_CD = lr_L1[0] - lr_L0[0];

    if(lr_L1[0] >= lr_L2[0]) lr_CU += lr_L1[0] - lr_L2[0];
    else                     lr_CD += lr_L2[0] - lr_L1[0];

    if(lr_L2[0] >= lr_L3[0]) lr_CU += lr_L2[0] - lr_L3[0];
    else                     lr_CD += lr_L3[0] - lr_L2[0];

    // Both piles empty means all four stages are exactly equal —
    // genuinely flat price. Fig 14.8 reads
    //     If CU + CD <> 0 then RSI = CU / (CU + CD);
    // with no else, so RSI keeps its previous value. Implemented
    // as published: if nothing changed, the reading does not
    // change. Returning a neutral 0.5 instead would invent a
    // state change from a non-event, which for a C2 would flip
    // the vote on a bar where nothing happened.
    //
    // Holding a value makes the RSI itself persistent state, so
    // it gets an INITRUN reset like any other static
    // (GOTCHAS 9b.1). Seeded neutral.
    //
    // In practice this branch is near-dead: on floating-point
    // price data the four stages differ in the seventh decimal
    // even on an unchanged close.
    static var lr_prevRSI = 0.5;
    if(is(INITRUN)) lr_prevRSI = 0.5;

    if(lr_CU + lr_CD == 0) return lr_prevRSI;

    lr_prevRSI = lr_CU / (lr_CU + lr_CD);
    return lr_prevRSI;
}
