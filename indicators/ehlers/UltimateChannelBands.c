// =============================================================
// UltimateChannelBands.c — Ultimate Channel & Ultimate Bands
//
// Reference: Ehlers, John F. (2024), "Ultimate Channels And
//   Ultimate Bands", Technical Analysis of Stocks & Commodities,
//   V.42:05. Both replace the moving averages of Keltner channels
//   and Bollinger Bands with UltimateSmoothers to remove lag.
//
// STRUCTURAL NOTE (this is what P4 tests): the article states
//   "both averages are replaced with UltimateSmoothers". True of
//   the CHANNEL. In the BAND only the CENTRE line is smoothed —
//   the width estimator remains a rectangular window over exactly
//   Length bars. The two widths are therefore different filter
//   classes:
//     STR = UltimateSmootherE(TR, STRLength)  recursive IIR
//     SD  = sqrt(mean over exactly Length)    rectangular FIR
//   A shock enters the SD window at full weight, stays 20 bars,
//   then drops out discontinuously. STR has no such cliff.
//
// True range is Wilder's, in Ehlers' cheaper form:
//   TH = max(High, Close[1]); TL = min(Low, Close[1]); TR = TH-TL
//   Verified equivalent to max(H-L, |H-C1|, |L-C1|) in all cases.
//
// CALL ORDER IS LOAD-BEARING (GOTCHAS 3.1). UltimateSmootherE uses
//   series(), which allocates by call order. The three calls below
//   are unconditional and fixed in sequence. Do not reorder them,
//   and do not place any of them inside an if().
//
// Requires: UltimateSmootherE.c included first.
// Locals prefixed uc_ (GOTCHAS 1.3).
//
// Parameters:
//   Close     : close series
//   Length    : centre-line period, and SD window (article: 20)
//   STRLength : smooth-true-range period (article: 20)
//   NumSTRs   : channel width multiplier (article: 1)
//   NumSDs    : band width multiplier (article: 1)
//
// Out-parameters (GOTCHAS 7 — no tuples in lite-C):
//   pCentre, pChUp, pChDn, pSTR   channel
//   pBdUp, pBdDn, pSD             band (same centre)
// =============================================================

void UltimateChannelBands(vars Close, int Length, int STRLength,
                          var NumSTRs, var NumSDs,
                          var* pCentre, var* pChUp, var* pChDn, var* pSTR,
                          var* pBdUp, var* pBdDn, var* pSD,
                          var* pTRBox, var* pDevSm)
{
    vars uc_High = series(priceHigh());   // GOTCHAS 6.1
    vars uc_Low  = series(priceLow());

    // --- True range (Wilder, Ehlers' form) ---
    // Bar-local: current bar plus one previous close. No window,
    // no memory. This independence is why the channel serves as
    // the control in P3 — TR cannot see the trend state.
    var uc_th = max(uc_High[0], Close[1]);
    var uc_tl = min(uc_Low[0],  Close[1]);
    vars uc_TR = series(uc_th - uc_tl);   // value passed IN (3.2)

    // --- CALL 1: smooth true range = channel width ---
    var uc_str = UltimateSmootherE(uc_TR, STRLength);

    // --- CALL 2: centre line, shared by channel and band ---
    var uc_centre = UltimateSmootherE(Close, Length);

    // --- Channel ---
    *pSTR    = uc_str;
    *pCentre = uc_centre;
    *pChUp   = uc_centre + NumSTRs * uc_str;
    *pChDn   = uc_centre - NumSTRs * uc_str;

    // --- Band: RMS deviation from the centre line ---
    // Rectangular window over exactly Length bars — every bar in
    // the window counts at full weight, then leaves abruptly.
    // Deviations are squared, so one outsized bar counts far more
    // heavily here than it does in the channel's plain average.
    vars uc_Dev = series(Close[0] - uc_centre);
    var uc_sumsq = 0;
    int uc_i;
    for(uc_i = 0; uc_i < Length; uc_i++)
        uc_sumsq += uc_Dev[uc_i] * uc_Dev[uc_i];

    var uc_sd = sqrt(uc_sumsq / Length);

    *pSD   = uc_sd;
    *pBdUp = uc_centre + NumSDs * uc_sd;
    *pBdDn = uc_centre - NumSDs * uc_sd;

    // --- Diagnostic corners (Week 13 Day 2) --------------------
    // STR and SD differ in TWO ways at once: what is fed in (bar
    // range vs distance from centre) and how it is averaged
    // (recursive smoother vs hard 20-bar window). Comparing STR to
    // SD changes both, so it cannot attribute the low correlation
    // to either. These two fill the missing corners of the 2x2.
    //
    // Corner 3: bar range, hard window (STR's input, SD's averaging)
    var uc_trsum = 0;
    for(uc_i = 0; uc_i < Length; uc_i++)
        uc_trsum += uc_TR[uc_i];
    *pTRBox = uc_trsum / Length;

    // Corner 4: distance from centre, smoothed (SD's input, STR's
    // averaging). CAVEAT: uses ABSOLUTE deviation, not squared —
    // squaring inside a recursive filter is not well defined the
    // way it is over a fixed window. So this differs from SD in
    // two ways (averaging AND squaring), not one. Its comparison
    // to SD is therefore muddier than corner 3's.
    //
    // CALL 3 to UltimateSmootherE — unconditional, fixed position
    // in the sequence (GOTCHAS 3.1).
    vars uc_AbsDev = series(abs(uc_Dev[0]));
    *pDevSm = UltimateSmootherE(uc_AbsDev, Length);
}
