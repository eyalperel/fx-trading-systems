// =============================================================================
// SUPERSEDED -- do not use. Kept as the negative control NCS of
// MESA_ArticleFidelity (M-1 window StochPeriod + 1, M-2 scale 0-100,
// fallback 50). Corrected file: MESAStochastic.c.
//
// This is the earlier MESAStochastic.c body verbatim (git blob
// a8c51bacf951cd1aa7a0d1c2f39347824ca1d6bf), with the function renamed
// MESAStochastic -> MESAStochastic_Superseded and every mstc_ identifier
// renamed mstco_ (flat namespace, gotchas 1.3). Nothing else is changed.
// Review: docs/harness/MESASTOCHASTIC_SOURCE_REVIEW.md.
// Include after RoofingFilter.c and SuperSmoother2Pole.c.
// =============================================================================

var MESAStochastic_Superseded(vars Price, int StochPeriod, int HPPeriod, int SSPeriod) {
    // Stage 1: RoofingFilter — band-pass preprocessor (already in library)
    var* mstco_Roof = series(RoofingFilter(Price, HPPeriod, SSPeriod), StochPeriod + 1);

    // Stage 2: ordinary Stochastic, computed on RoofingFilter output (not raw price)
    var mstco_HH = mstco_Roof[0];
    var mstco_LL = mstco_Roof[0];
    int mstco_i;
    for (mstco_i = 1; mstco_i <= StochPeriod; mstco_i++) {
        if (mstco_Roof[mstco_i] > mstco_HH) mstco_HH = mstco_Roof[mstco_i];
        if (mstco_Roof[mstco_i] < mstco_LL) mstco_LL = mstco_Roof[mstco_i];
    }

    var mstco_RawStoch = 50;  // neutral fallback if range is zero
    if (mstco_HH != mstco_LL)
        mstco_RawStoch = 100.0 * (mstco_Roof[0] - mstco_LL) / (mstco_HH - mstco_LL);

    // Stage 3: final SuperSmooth pass — same SSPeriod as RoofingFilter's internal smoothing
    var* mstco_RS = series(mstco_RawStoch, 3);
    var mstco_Final = SuperSmoother2Pole(mstco_RS, SSPeriod);

    return mstco_Final;
}