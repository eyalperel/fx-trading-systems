// =============================================================
// LaguerreOsc.c — Laguerre Oscillator
//
// Reference: Ehlers, John F. (2025), "Laguerre Filters",
//   Technical Analysis of Stocks & Commodities, V.43:07, pp.8-12.
//   Transcribed from the article's "Laguerre Oscillator, In
//   EasyLanguage Code" sidebar.
//
// STRUCTURE — only two terms:
//   L0  = UltimateSmoother(Close, Length)
//   L1  = delayed version of L0
//   Osc = (L0 - L1) / RMS(L0 - L1, 100)
//
// L1 is L0 pushed later in time, so subtracting removes whatever
// the two have in common — the trend — and leaves what changed
// between them, oscillating around zero. Same principle as the
// Decycler (Week 6).
//
// The RMS division makes it scale-free. L0 - L1 is in price units:
// ~0.005 on EUR/USD, ~50 on BTC. Dividing by its own recent RMS
// puts the output in standard deviations, which is Ehlers' stated
// intent ("scaled in standard deviations to assist in swing
// trading decisions"). Same normalisation problem NATR has, solved
// differently — NATR divides by price, this divides by its own
// recent spread.
//
// PARAMETERS ARE THE ARTICLE'S, NOT THE WEEK 13 CONVENTION.
//   gamma = 0.5, Length = 30, RMS window = 100.
//   Every other Week 13 component uses 20 (UltimateSmoother, the
//   channel, the band, the SD window, RSIH). This file deliberately
//   does not, because the article publishes 0.5/30 for the
//   oscillator specifically and no measurement here suggests
//   otherwise. Matching the source beats house consistency when
//   there is no evidence either way. If a sweep later shows 20 is
//   better, that is a measured change with a reason.
//
// ARTICLE DISCREPANCY — text vs code, documented not corrected.
//   Ehlers writes that each term is "the allpass filter delay of
//   the previous term". An allpass filter passes every frequency
//   at unchanged amplitude and only shifts phase. The published
//   code is
//     L1 = -gama*L0[1] + L0[1] + gama*L1[1]
//   which uses the PREVIOUS L0 in both terms and collapses to
//     L1 = (1-gama)*L0[1] + gama*L1[1]
//   — a lowpass, not an allpass. Measured amplitude at gamma 0.5:
//   0.45 at period 4, 0.75 at period 10, 0.91 at period 20, 1.00
//   only asymptotically. A true allpass measures 1.0000 at every
//   period. The book version (Cybernetic Analysis, Fig 14.5, and
//   our Laguerre.c) uses the CURRENT L0 in the first term and is
//   a genuine allpass.
//
//   FOR THIS OSCILLATOR THE DIFFERENCE IS EXACTLY NIL. Algebra:
//     1 - H_allpass   = (1+gamma)(1 - z^-1) / (1 - gamma*z^-1)
//     1 - H_published =         (1 - z^-1) / (1 - gamma*z^-1)
//   so the allpass form gives exactly (1+gamma) times the
//   published form — a constant, at every frequency. The RMS
//   division cancels it: the factor appears in both numerator and
//   denominator. Verified numerically, max difference 8.9e-16.
//
//   THIS DOES NOT CARRY OVER to the five-term Laguerre FILTER in
//   the same article. That chains four such delays and combines
//   them with binomial weights 1-4-6-4-1, with no normalisation.
//   Constant factors do not cancel in a weighted sum, so there the
//   choice would change the output. Check before extending.
//
// The published code is implemented as published.
//
// Requires: UltimateSmootherE.c included first.
// Locals prefixed lo_ (GOTCHAS 1.3).
//
// Parameters:
//   Close  : close series
//   gamma  : delay depth, article default 0.5
//   Length : UltimateSmoother period, article default 30
//   RMSLen : RMS normalisation window, article default 100
//
// Returns: oscillator in standard deviations, centred on zero
// =============================================================

var LaguerreOsc(vars Close, var gamma, int Length, int RMSLen) {

    // L0: UltimateSmoother of price. CALL ORDER matters — this
    // uses series() internally (GOTCHAS 3.1). Unconditional.
    vars lo_L0 = series(UltimateSmootherE(Close, Length));

    // L1: the published recursion, using PREVIOUS L0 in both terms
    vars lo_L1 = series(0, 2);
    lo_L1[0] = -gamma * lo_L0[1] + lo_L0[1] + gamma * lo_L1[1];

    // The oscillator's raw quantity, kept as a series for the RMS
    vars lo_D = series(lo_L0[0] - lo_L1[0]);

    // RMS over RMSLen bars: square each value, average, take the
    // root. The article publishes an $RMS function and uses it
    // here; it gives no reason, and none is inferred.
    //
    // What is checkable: RMS measures spread around ZERO, while a
    // standard deviation measures spread around the data's own
    // mean. On values centred near zero the two agree; on values
    // sitting away from zero they diverge sharply. Example —
    // (10,12,14,12,10): sd = 1.50, rms = 11.70. Same shape shifted
    // to (-2,0,2,0,-2): sd = 1.55, rms = 1.55.
    //
    // L0-L1 is a difference between two similar quantities, so it
    // hovers near zero and the two measures should agree here. If
    // it ever develops a persistent offset, RMS returns a larger
    // number than sd would and the oscillator reads smaller than
    // its standard-deviation interpretation implies. Measurable:
    // compare mean(L0-L1) against rms(L0-L1) on real data.
    var lo_sumsq = 0;
    int lo_i;
    for(lo_i = 0; lo_i < RMSLen; lo_i++)
        lo_sumsq += lo_D[lo_i] * lo_D[lo_i];

    var lo_rms = sqrt(lo_sumsq / RMSLen);

    if(lo_rms == 0) return 0;
    return lo_D[0] / lo_rms;
}
