// =============================================================================
// MESAStochastic.c -- MESA Stochastic (Ehlers' published form)
//
// Source (a): Ehlers, John F., "Predictive And Successful Indicators",
//   Technical Analysis of Stocks & Commodities V.32:1 (2014), pp. 16-25,
//   sidebar "EasyLanguage Code To Compute The MESA Stochastic Indicator"
//   (PDF p. 8). Formula in Light-C terms:
//     Roof = RoofingFilter(48, 10)
//     Stoc = (Roof - LowestRoof) / (HighestRoof - LowestRoof), over the
//            last Length Roof values (count = 0 .. Length - 1)
//     MESAStochastic = SuperSmoother(10) applied to (Stoc + Stoc[1]) / 2
//   (a) Source default Length = 20; 48 and 10 are fixed in the source.
//   (c) StochPeriod / HPPeriod / SSPeriod are this library's generalisation
//   (review M-7); SSPeriod is used for BOTH SuperSmoother passes, as the
//   source reuses the same coefficients.
//
// Deviations from the earlier file, fixed (b); review
//   docs/harness/MESASTOCHASTIC_SOURCE_REVIEW.md (3f0de96):
//   M-1 the window is StochPeriod bars (was StochPeriod + 1).
//   M-2 the output scale is 0-1 as in the source (was 0-100).
//       Exports made before this fix are x100.
//   M-6 the zero-range fallback is 0.5 (was 50).
//   M-9 MESAStochasticCore exports the Roofing Filter and the raw
//       stochastic; MESAStochastic is a thin wrapper, callers unchanged.
//   M-8 this header.
//
// Zero range (b/c): the source has no guard (it divides 0/0 when the window
//   high equals the low). The fallback 0.5 is a library choice (mid-range:
//   a flat market cannot produce a 0.2 / 0.8 crossing). It fires on the
//   first bar and on flat input.
//
// Start-up (a): the source states no rule. (b) Roof starts at 0
//   (HighPassFilter zero seed, GAP-1.26 fixed upstream); the final
//   SuperSmoother starts at the first stochastic value (series seeding),
//   where the source starts at 0: the difference is gone after row 59
//   (spec finding 7). Treat the first ~60 bars as warm-up (the harness
//   uses W = 700).
//
// Bounds (b): the raw stochastic lies in [0, 1] exactly; the final output
//   does NOT (it overshoots, about -0.03 to 1.03 on a long-period sine:
//   spec finding 5). Thresholds such as the source's .2 / .8 apply to the
//   final output.
//
// Window (b): the window length matters only for cycles longer than the
//   window (spec O_WINDOW: 21 vs 20 bars differs by <= 8e-14 at T <= 20,
//   by 6e-2 to 8e-2 at T = 40 / 100).
//
// What it is (c): three fixed periods; it does not measure or adapt to a
//   dominant cycle despite the "MESA" name. The stochastic stage rescales
//   by the rolling range of the band-passed series. Whether that matters
//   for the cycle premise: docs/research/Cycle_Premise_Conclusions_and_Impact.md
//   (not asserted here).
//
// STATE: no statics. Both series() calls are unconditional and precede any
//   use (gotchas 3.1); every instance has its own window and final-smoother
//   state. Callers invoke unconditionally every bar. Include order:
//   HighPassFilter.c, SuperSmoother2Pole.c, RoofingFilter.c,
//   MESAStochastic.c (gotchas 5.3).
//
// Verification: analysis/harness/specs/MESA_ArticleFidelity.toml
//   (pre-registered 0fd34ee). Not verified until that run passes.
// =============================================================================

var MESAStochasticCore(vars Price, int StochPeriod, int HPPeriod, int SSPeriod, var* pRoof, var* pStoc)
{
    vars mstc_Roof = series(RoofingFilter(Price, HPPeriod, SSPeriod), StochPeriod);
    var mstc_HH = mstc_Roof[0];
    var mstc_LL = mstc_Roof[0];
    int mstc_i;
    for(mstc_i = 1; mstc_i < StochPeriod; mstc_i++) {
        if(mstc_Roof[mstc_i] > mstc_HH) mstc_HH = mstc_Roof[mstc_i];
        if(mstc_Roof[mstc_i] < mstc_LL) mstc_LL = mstc_Roof[mstc_i];
    }
    var mstc_Stoc = 1;
    mstc_Stoc = mstc_Stoc/2;
    if(mstc_HH != mstc_LL)
        mstc_Stoc = (mstc_Roof[0] - mstc_LL)/(mstc_HH - mstc_LL);
    vars mstc_S = series(mstc_Stoc, 3);
    var mstc_Out = SuperSmoother2Pole(mstc_S, SSPeriod);
    *pRoof = mstc_Roof[0];
    *pStoc = mstc_Stoc;
    return mstc_Out;
}

var MESAStochastic(vars Price, int StochPeriod, int HPPeriod, int SSPeriod)
{
    var mstc_r;
    var mstc_s;
    return MESAStochasticCore(Price, StochPeriod, HPPeriod, SSPeriod, &mstc_r, &mstc_s);
}
