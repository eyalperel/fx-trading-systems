// =============================================================================
// NAMING CAUTION: "MESA" here is Ehlers' naming only. This implementation does
// NOT perform maximum-entropy spectral analysis and does NOT measure or adapt
// to a dominant cycle. It takes three FIXED periods (StochPeriod, HPPeriod,
// SSPeriod) and is a normalised band-pass oscillator:
//     RoofingFilter -> rolling min/max normalisation -> SuperSmoother2Pole
//
// Consequence: UNAFFECTED by the Aug 2026 cycle-premise null test, which found
// no detectable cycle in EUR/USD D1 or BTC/USD H4. Its justification is
// "normalised position within a band-passed series", not "cycle position".
//
// Additional advantage: the stochastic stage rescales by rolling range, i.e.
// automatic gain control. This matters on BTC/USD H4 where raw oscillator
// amplitude varies ~10x across regimes. Raw CyberCycle has no AGC.
//
// See docs/research/Cycle_Premise_Conclusions_and_Impact.md
// =============================================================================

var MESAStochastic(vars Price, int StochPeriod, int HPPeriod, int SSPeriod) {
    // Stage 1: RoofingFilter — band-pass preprocessor (already in library)
    var* mstc_Roof = series(RoofingFilter(Price, HPPeriod, SSPeriod), StochPeriod + 1);

    // Stage 2: ordinary Stochastic, computed on RoofingFilter output (not raw price)
    var mstc_HH = mstc_Roof[0];
    var mstc_LL = mstc_Roof[0];
    int mstc_i;
    for (mstc_i = 1; mstc_i <= StochPeriod; mstc_i++) {
        if (mstc_Roof[mstc_i] > mstc_HH) mstc_HH = mstc_Roof[mstc_i];
        if (mstc_Roof[mstc_i] < mstc_LL) mstc_LL = mstc_Roof[mstc_i];
    }

    var mstc_RawStoch = 50;  // neutral fallback if range is zero
    if (mstc_HH != mstc_LL)
        mstc_RawStoch = 100.0 * (mstc_Roof[0] - mstc_LL) / (mstc_HH - mstc_LL);

    // Stage 3: final SuperSmooth pass — same SSPeriod as RoofingFilter's internal smoothing
    var* mstc_RS = series(mstc_RawStoch, 3);
    var mstc_Final = SuperSmoother2Pole(mstc_RS, SSPeriod);

    return mstc_Final;
}