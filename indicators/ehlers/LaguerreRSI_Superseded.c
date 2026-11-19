// =============================================================================
// LaguerreRSI_Superseded.c
// SUPERSEDED -- do not use. Kept as the negative control NCS / NCT of LRSI_ArticleFidelity
// (L-1 price seed, L-2 hold starting at 0.5, L-3 file statics shared by every call).
// Corrected file: LaguerreRSI.c. Body = the earlier LaguerreRSI.c verbatim (git blob
// b05f725176eff59b4ba1b68f299395c1c774ddff), function renamed LaguerreRSI -> LaguerreRSI_Superseded,
// every lr_ identifier renamed lro_ (flat namespace, gotchas 1.3). Nothing else is changed.
// Review: docs/harness/LAGUERRERSI_SOURCE_REVIEW.md.
// =============================================================================

var LaguerreRSI_Superseded(vars Close, var gamma) {

    vars lro_L0 = series(0, 2);
    vars lro_L1 = series(0, 2);
    vars lro_L2 = series(0, 2);
    vars lro_L3 = series(0, 2);

    // Seed all stages to price on the first valid bar. Without
    // this the stages ramp from zero to price level over the
    // warmup (GOTCHAS 3.3). Flag-based, not value-based, and
    // cleared at INITRUN so it cannot be defeated by leftover
    // state from a previous run (GOTCHAS 9b.1, 9b.2).
    static int lro_init = 0;
    if(is(INITRUN)) lro_init = 0;
    if(!lro_init && Close[0] > 0) {
        lro_L0[0] = Close[0]; lro_L0[1] = Close[0];
        lro_L1[0] = Close[0]; lro_L1[1] = Close[0];
        lro_L2[0] = Close[0]; lro_L2[1] = Close[0];
        lro_L3[0] = Close[0]; lro_L3[1] = Close[0];
        lro_init = 1;
        return 0.5;
    }

    // --- Four-stage Laguerre chain (Fig 14.8) ---
    // L0 is a plain EMA. L1-L3 are allpass delays: note each uses
    // the CURRENT upstream value in the first term and the
    // PREVIOUS in the second. Reversing that turns the allpass
    // into a lowpass — which is what the 2025 TASC article's code
    // does. See LaguerreOsc_Notes.md.
    lro_L0[0] = (1.0 - gamma) * Close[0] + gamma * lro_L0[1];
    lro_L1[0] = -gamma * lro_L0[0] + lro_L0[1] + gamma * lro_L1[1];
    lro_L2[0] = -gamma * lro_L1[0] + lro_L1[1] + gamma * lro_L2[1];
    lro_L3[0] = -gamma * lro_L2[0] + lro_L2[1] + gamma * lro_L3[1];

    // --- Three adjacent comparisons ---
    var lro_CU = 0;
    var lro_CD = 0;

    if(lro_L0[0] >= lro_L1[0]) lro_CU = lro_L0[0] - lro_L1[0];
    else                     lro_CD = lro_L1[0] - lro_L0[0];

    if(lro_L1[0] >= lro_L2[0]) lro_CU += lro_L1[0] - lro_L2[0];
    else                     lro_CD += lro_L2[0] - lro_L1[0];

    if(lro_L2[0] >= lro_L3[0]) lro_CU += lro_L2[0] - lro_L3[0];
    else                     lro_CD += lro_L3[0] - lro_L2[0];

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
    static var lro_prevRSI = 0.5;
    if(is(INITRUN)) lro_prevRSI = 0.5;

    if(lro_CU + lro_CD == 0) return lro_prevRSI;

    lro_prevRSI = lro_CU / (lro_CU + lro_CD);
    return lro_prevRSI;
}
