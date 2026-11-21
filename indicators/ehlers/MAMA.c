// =============================================================================================================
// MAMA.c -- MESA Adaptive Moving Average (MAMA) and its FAMA
// =============================================================================================================
// SOURCE (a): Ehlers, J. F., "MESA Adaptive Moving Averages", Technical Analysis of Stocks & Commodities V.19:9
//   (2001), pp. 30-35, Sidebar Figure 1 (TradeStation code for MAMA and FAMA), PDF p. 5.
// FORMULA (a), in plain terms:
//   4-bar weighted Smooth of Price -> Hilbert-transform Detrender, I1 / Q1, jI / jQ (weights .0962 / .5769, times
//   .075*Period[1] + .54) -> phasor sums I2 / Q2 (.2 / .8 smoothed) -> homodyne Re / Im (.2 / .8 smoothed) ->
//   Period = 360 / ArcTangent(Im / Re) in degrees, bounded to .67x..1.5x the previous Period, then to 6..50, then
//   blended .2 / .8 with the previous Period -> Phase = ArcTangent(Q1 / I1) in degrees -> DeltaPhase = Phase[1] -
//   Phase, floored at 1 -> alpha = FastLimit / DeltaPhase clamped to [SlowLimit, FastLimit] -> MAMA = alpha*Price +
//   (1 - alpha)*MAMA[1]; FAMA = .5*alpha*MAMA + (1 - .5*alpha)*FAMA[1].
//   Defaults (a): Price (H+L)/2, FastLimit .5, SlowLimit .05. SmoothPeriod (.33 / .67) is computed and unused, as in
//   the source.
// USE (a): the source suggests the MAMA / FAMA crossover as a trend signal. Not implemented here; the NNFX baseline
//   rule is a template decision (PROJECT_STATE step 4).
//
// DEVIATIONS FIXED (b), review docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md (MA-1..MA-9, appendix C-1..C-3, S1..S5):
//   MA-1 start-up as the source: every state starts at 0 and the body is computed from this instance's 6th call
//        (the old file seeded with the price, returned Price for 5 calls and started Period at 20).
//   MA-2 Period / Phase keep their value on a bar where Im or Re = 0 / I1 = 0 (the old file set 20 / 0).
//   MA-3 per-instance state and call counter (the old `static barCount` was shared by every call).
//   MA-4 every constant built from integers at run time (decimal literals are float32 in Zorro, gotchas 9d.1).
//   S1   exact pi built at run time (4*atan(1)) for the degree conversion: the old PI = 3.14159 moved Phase by up to
//        7.3e-5 degrees, more than the float32 literals did (D3 exception, review appendix S1). The old #ifndef PI
//        fallback (MA-5) never applied and is removed.
//   MA-7 MAMACore exports FAMA, Period, alpha and Phase; MAMA() is a thin wrapper with the old signature.
//   MA-8 this header. The old header's "APPROVED", lag, SNR, win-rate and 92.5% claims are dropped (unsourced or not
//        reproducible); its "1.5*0 = 0 trap" does not occur (b): the source's 6-bar floor acts.
//
// BEHAVIOUR (b) (review section 3 and appendix; MAMA_ArticleFidelity.toml observations):
//   * Zero start: MAMA / FAMA start at 0 and need about 500 bars to forget it (sines: start-up differences gone by
//     row ~520). (c) A strategy's LookBack must cover this.
//   * alpha is in [SlowLimit, FastLimit]; on short cycles it switches between the two limits (T = 10 / 20 bars:
//     FastLimit on 20% / 10% of bars, SlowLimit otherwise). Period follows the cycle within ~0.5% for T = 10..40 and
//     sits on its bounds outside 6..50.
//   * Ill-conditioned inputs: on a flat line (during start-up), a steady ramp and cycles shorter than 6 bars the
//     output depends on rounding (one ulp of input moved FAMA by up to 3.2e-2 / 2.8e-4 / 1.7e-2): the phase wrap at
//     +-90 degrees flips alpha between its limits. On a ramp Period wanders 36..48 and the lags are about 2.2 bars
//     (MAMA) / 7.0 bars (FAMA) at (.5, .05) (model, not exact).
//
// CALLER REQUIREMENTS: Price series of at least 4 values; call unconditionally on every bar (gotchas 3.1); build
//   FastLimit / SlowLimit from integers (var sl = 1; sl = sl/20; for .05, gotchas 9d.1). Use your own local
//   prefix: ma_ and maw_ belong to this file (gotchas 1.3).
// STATE: no statics; every series() call is unconditional and first; each instance has its own state. No includes
//   needed.
// VERIFICATION: analysis/harness/specs/MAMA_ArticleFidelity.toml (pre-registered 7713f5b). Not verified until that
//   run passes.
// =============================================================================================================

var MAMACore(vars Price, var FastLimit, var SlowLimit, var* pFama, var* pPeriod, var* pAlpha, var* pPhase)
{
    vars ma_n  = series(0, 2);     // per-instance CurrentBar (9d.9)
    vars ma_S  = series(0, 7);
    vars ma_De = series(0, 7);
    vars ma_I1 = series(0, 7);
    vars ma_Q1 = series(0, 7);
    vars ma_jI = series(0, 2);
    vars ma_jQ = series(0, 2);
    vars ma_I2 = series(0, 2);
    vars ma_Q2 = series(0, 2);
    vars ma_Re = series(0, 2);
    vars ma_Im = series(0, 2);
    vars ma_P  = series(0, 2);
    vars ma_SP = series(0, 2);
    vars ma_Ph = series(0, 2);
    vars ma_A  = series(0, 2);
    vars ma_M  = series(0, 2);
    vars ma_F  = series(0, 2);
    ma_n[0] = ma_n[1] + 1;
    // EasyLanguage: a var keeps its value on a bar where it is not assigned (MA-2)
    ma_S[0] = ma_S[1];   ma_De[0] = ma_De[1]; ma_I1[0] = ma_I1[1]; ma_Q1[0] = ma_Q1[1];
    ma_jI[0] = ma_jI[1]; ma_jQ[0] = ma_jQ[1]; ma_I2[0] = ma_I2[1]; ma_Q2[0] = ma_Q2[1];
    ma_Re[0] = ma_Re[1]; ma_Im[0] = ma_Im[1]; ma_P[0] = ma_P[1];   ma_SP[0] = ma_SP[1];
    ma_Ph[0] = ma_Ph[1]; ma_A[0] = ma_A[1];   ma_M[0] = ma_M[1];   ma_F[0] = ma_F[1];
    var ma_w1 = 962;  ma_w1 = ma_w1/10000;
    var ma_w2 = 5769; ma_w2 = ma_w2/10000;
    var ma_ka = 75;   ma_ka = ma_ka/1000;
    var ma_kb = 54;   ma_kb = ma_kb/100;
    var ma_a2 = 2;    ma_a2 = ma_a2/10;
    var ma_a8 = 8;    ma_a8 = ma_a8/10;
    var ma_c33 = 33;  ma_c33 = ma_c33/100;
    var ma_c67 = 67;  ma_c67 = ma_c67/100;
    var ma_up = 15;   ma_up = ma_up/10;
    var ma_dn = 67;   ma_dn = ma_dn/100;
    var ma_pi = 4;    ma_pi = ma_pi*atan(1);       // S1: exact pi at run time (D3)
    var ma_deg = 180; ma_deg = ma_deg/ma_pi;
    var ma_h = 1;     ma_h = ma_h/2;
    var ma_u = 1;
    var ma_pf = 0;
    var ma_p1 = 0;
    var ma_dp = 0;
    var ma_ah = 0;
    if(ma_n[0] > 5) {
        ma_S[0] = 4*Price[0] + 3*Price[1] + 2*Price[2] + Price[3];
        ma_S[0] = ma_S[0]/10;
        ma_pf = ma_ka*ma_P[1] + ma_kb;
        ma_De[0] = (ma_w1*ma_S[0] + ma_w2*ma_S[2] - ma_w2*ma_S[4] - ma_w1*ma_S[6])*ma_pf;
        ma_Q1[0] = (ma_w1*ma_De[0] + ma_w2*ma_De[2] - ma_w2*ma_De[4] - ma_w1*ma_De[6])*ma_pf;
        ma_I1[0] = ma_De[3];
        ma_jI[0] = (ma_w1*ma_I1[0] + ma_w2*ma_I1[2] - ma_w2*ma_I1[4] - ma_w1*ma_I1[6])*ma_pf;
        ma_jQ[0] = (ma_w1*ma_Q1[0] + ma_w2*ma_Q1[2] - ma_w2*ma_Q1[4] - ma_w1*ma_Q1[6])*ma_pf;
        ma_I2[0] = ma_I1[0] - ma_jQ[0];
        ma_Q2[0] = ma_Q1[0] + ma_jI[0];
        ma_I2[0] = ma_a2*ma_I2[0] + ma_a8*ma_I2[1];
        ma_Q2[0] = ma_a2*ma_Q2[0] + ma_a8*ma_Q2[1];
        ma_Re[0] = ma_I2[0]*ma_I2[1] + ma_Q2[0]*ma_Q2[1];
        ma_Im[0] = ma_I2[0]*ma_Q2[1] - ma_Q2[0]*ma_I2[1];
        ma_Re[0] = ma_a2*ma_Re[0] + ma_a8*ma_Re[1];
        ma_Im[0] = ma_a2*ma_Im[0] + ma_a8*ma_Im[1];
        if(ma_Im[0] != 0 && ma_Re[0] != 0) {
            ma_P[0] = atan(ma_Im[0]/ma_Re[0]);
            ma_P[0] = ma_P[0]*ma_deg;
            ma_P[0] = 360/ma_P[0];
        }
        ma_p1 = ma_P[1];
        if(ma_P[0] > ma_up*ma_p1) ma_P[0] = ma_up*ma_p1;
        if(ma_P[0] < ma_dn*ma_p1) ma_P[0] = ma_dn*ma_p1;
        if(ma_P[0] < 6)  ma_P[0] = 6;
        if(ma_P[0] > 50) ma_P[0] = 50;
        ma_P[0] = ma_a2*ma_P[0] + ma_a8*ma_p1;
        ma_SP[0] = ma_c33*ma_P[0] + ma_c67*ma_SP[1];
        if(ma_I1[0] != 0) {
            ma_Ph[0] = atan(ma_Q1[0]/ma_I1[0]);
            ma_Ph[0] = ma_Ph[0]*ma_deg;
        }
        ma_dp = ma_Ph[1] - ma_Ph[0];
        if(ma_dp < 1) ma_dp = 1;
        ma_A[0] = FastLimit/ma_dp;
        if(ma_A[0] < SlowLimit) ma_A[0] = SlowLimit;
        if(ma_A[0] > FastLimit) ma_A[0] = FastLimit;
        ma_M[0] = ma_A[0]*Price[0] + (ma_u - ma_A[0])*ma_M[1];
        ma_ah = ma_h*ma_A[0];
        ma_F[0] = ma_ah*ma_M[0] + (ma_u - ma_ah)*ma_F[1];
    }
    *pFama   = ma_F[0];
    *pPeriod = ma_P[0];
    *pAlpha  = ma_A[0];
    *pPhase  = ma_Ph[0];
    return ma_M[0];
}

var MAMA(vars Price, var FastLimit, var SlowLimit, var* outFAMA)
{
    var maw_1;
    var maw_2;
    var maw_3;
    return MAMACore(Price, FastLimit, SlowLimit, outFAMA, &maw_1, &maw_2, &maw_3);
}
