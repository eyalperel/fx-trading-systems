// =============================================================
// RSIH.c — RSI with Hann Windowing
//
// Reference: Ehlers, John F. (2022), "(Yet Another) Improved RSI",
//   Technical Analysis of Stocks & Commodities, V.40:01, pp.26-28.
//   Transcribed from the article's EasyLanguage sidebar.
//
// TWO CHANGES FROM CLASSIC RSI:
//
// 1. Rescaled to swing -1..+1 instead of 0..100:
//      RSIH = (CU - CD) / (CU + CD)
//    All movement up -> +1, all down -> -1, balanced -> 0. The
//    numerator is a DIFFERENCE, so neutral is zero and the sign
//    alone gives direction.
//
// 2. Hann window on the accumulation. Classic RSI sums the up and
//    down moves with equal weight — a rectangular window, with the
//    same cliff the boxcar SD showed in P4 (a move enters at full
//    weight, sits 14 bars, drops out abruptly). Hann weights each
//    position by
//      w(count) = 1 - cos(2*PI*count / (Length+1))
//    which is near zero at both edges and peaks in the middle. A
//    bar ageing out was already contributing almost nothing, so
//    there is no cliff. Ehlers: the smoothing is native to the
//    computation, so no additional filtering is needed.
//
// LENGTH. Ehlers argues the correct CLASSIC RSI length is half the
//   dominant cycle period (RSI peaks over valley-to-peak, which is
//   half a cycle). Hann needs a longer window than rectangular for
//   equivalent smoothing, because the edge weights do little work.
//   Together those put RSIH at roughly the full dominant cycle
//   period — so 14 is inherited from Wilder and is not his
//   recommendation.
//
//   This implementation takes a FIXED length, defaulting to the
//   project's Week 13 convention of 20. An adaptive version driven
//   by DominantCycle.c is a registered variant to be tested against
//   this baseline — not assumed better. Precedent: fixed-period
//   InstantTrendline outperformed its adaptive version on SNR, the
//   DominantCycle mechanism costing more instability than it gained.
//
// INDEXING. Ehlers uses Close[count-1] - Close[count]: NEWER minus
//   OLDER, since [0] is the current bar. At count=1 that is
//   Close[0] - Close[1], today against yesterday. Reversing this
//   inverts the indicator while still producing plausible output.
//
// No IIR state — RSIH is a pure FIR computation over the window,
//   so there are no statics to reset (GOTCHAS 9b.1 does not apply).
//
// Locals prefixed rh_ (GOTCHAS 1.3).
//
// Parameters:
//   Close  : close series
//   Length : window length in bars (project default 20)
//
// Returns: RSIH value in [-1, +1], zero-centred
// =============================================================

var RSIH(vars Close, int Length) {

    var rh_CU = 0;
    var rh_CD = 0;
    var rh_w, rh_delta;
    int rh_count;

    for(rh_count = 1; rh_count <= Length; rh_count++) {

        // Hann weight for this position: ~0 at the edges, peak
        // in the middle. Radians — Ehlers publishes degrees.
        rh_w = 1.0 - cos(2.0 * PI * rh_count / (Length + 1));

        // Newer minus older
        rh_delta = Close[rh_count - 1] - Close[rh_count];

        // Two separate tests, matching the article — NOT if/else.
        // A bar with delta exactly 0 contributes to NEITHER sum.
        // if/else would send it to CD, which happens to add zero
        // and so is numerically identical here, but only by
        // coincidence. Flat closes are common on D1 FX.
        if(rh_delta > 0)  rh_CU += rh_w * rh_delta;
        if(rh_delta < 0)  rh_CD += rh_w * (-rh_delta);
    }

    if(rh_CU + rh_CD == 0) return 0;
    return (rh_CU - rh_CD) / (rh_CU + rh_CD);
}
