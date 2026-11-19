// =============================================================================
// LaguerreRSI.c -- Laguerre RSI (corrected 2026-11-19; the earlier file is kept as LaguerreRSI_Superseded.c)
//
// Source (a): Ehlers, J. F., "Cybernetic Analysis for Stocks and Futures" (Wiley 2004), ch. 14
//   "Time Warp - Without Space Travel", Fig. 14.8 (EasyLanguage), p. 221; Fig. 14.9 (EFS) agrees.
//   In Light-C terms: L0 = EMA with alpha 1 - gamma; L1..L3 = allpass stages; CU / CD = the sums of the
//   positive / negative differences over the three ADJACENT pairs (L0,L1), (L1,L2), (L2,L3);
//   RSI = CU / (CU + CD), range 0..1; book default gamma 0.5; reference lines .2 / .8.
//   Input: Close. (The companion Laguerre FILTER, Fig. 14.5 / Laguerre.c, uses (H+L)/2 -- not this indicator.)
//
// Deviations from the previous file, now fixed (b) -- review docs/harness/LAGUERRERSI_SOURCE_REVIEW.md (6382607):
//   L-1  zero start as the source (was: every stage seeded to the first Close, that bar skipped, 0.5 returned).
//   L-2  hold the previous value when CU + CD = 0, initial 0, per instance (was a static starting at 0.5).
//   L-3  no statics (the old lr_init / lr_prevRSI were shared by every call: a second instance or asset
//        started differently and could return another instance's value).
//   L-5  LaguerreRSICore exports L0, L3 and CU + CD.
//   L-6  this header.
//   (b) Outputs before this fix differ in the first ~60 / 120 / 196 bars (gamma 0.5 / 0.7 / 0.8); after that
//   they are identical (review section 3).
//
// Start-up (a/b): the source starts every stage at 0 and computes from the first bar; this file does the same
//   (each series(0, 2) history starts at 0 on the instance's first call). Treat the first ~200 bars as warm-up
//   (the harness uses W = 700).
//
// Behaviour (b): the output lies in [0, 1] exactly. On a steadily rising (falling) price it is exactly 1 (0) once the
//   four stages are ordered ("lock to lock"; saturation by design, not a defect: it then reports THAT the price trends,
//   not how strongly). The share of bars pinned at 0 or 1 grows with the cycle length (spec observation O_PIN).
//   On a flat price the result is a held value or rounding noise.
//
// Use stated by the source (a), p. 221 / 225: buy after the line crosses back above .2, sell after it crosses back below
//   .8 (the book's sell sentence says "price"; (c) probably the line). Not implemented here.
//
// Callers (b): gamma 0.5 is exact in float32; 0.7 / 0.8 are not (gotchas 9d.1) -- build them at run time from
//   integers (var g = 7; g = g/10;). Same output range and scale (0..1) as MESAStochastic.
//
// Notes: (c) the old claim "P-LR1: 35-55% of bars pinned" is a prediction, see the registered predictions file, not a
//   measurement. (b) The 2025 TASC article's code has L1 use L0[1] in the first term, which makes that stage a delayed
//   EMA rather than an allpass (review L-6); this file follows the 2004 book.
//
// STATE: no statics. All five series() calls are unconditional and come before any use (gotchas 3.1); each instance
//   has its own state. Callers invoke unconditionally every bar. No includes needed (no dependency).
//   Locals prefixed lr_ (gotchas 1.3).
//
// Verification: analysis/harness/specs/LRSI_ArticleFidelity.toml (pre-registered 824a3cc). NOT verified until that
//   run passes.
// =============================================================================

var LaguerreRSICore(vars Close, var gamma, var* pL0, var* pL3, var* pDen) {
    vars lr_L0 = series(0, 2);
    vars lr_L1 = series(0, 2);
    vars lr_L2 = series(0, 2);
    vars lr_L3 = series(0, 2);
    vars lr_R  = series(0, 2);
    var lr_k = 1;
    lr_k = lr_k - gamma;
    lr_L0[0] = lr_k*Close[0] + gamma*lr_L0[1];
    lr_L1[0] = lr_L0[1] - gamma*lr_L0[0] + gamma*lr_L1[1];
    lr_L2[0] = lr_L1[1] - gamma*lr_L1[0] + gamma*lr_L2[1];
    lr_L3[0] = lr_L2[1] - gamma*lr_L2[0] + gamma*lr_L3[1];
    var lr_CU = 0;
    var lr_CD = 0;
    if(lr_L0[0] >= lr_L1[0]) lr_CU = lr_L0[0] - lr_L1[0];
    else                     lr_CD = lr_L1[0] - lr_L0[0];
    if(lr_L1[0] >= lr_L2[0]) lr_CU = lr_CU + lr_L1[0] - lr_L2[0];
    else                     lr_CD = lr_CD + lr_L2[0] - lr_L1[0];
    if(lr_L2[0] >= lr_L3[0]) lr_CU = lr_CU + lr_L2[0] - lr_L3[0];
    else                     lr_CD = lr_CD + lr_L3[0] - lr_L2[0];
    lr_R[0] = lr_R[1];
    if(lr_CU + lr_CD != 0) lr_R[0] = lr_CU/(lr_CU + lr_CD);
    *pL0 = lr_L0[0];
    *pL3 = lr_L3[0];
    *pDen = lr_CU + lr_CD;
    return lr_R[0];
}

var LaguerreRSI(vars Close, var gamma) {
    var lr_w0;
    var lr_w3;
    var lr_wd;
    return LaguerreRSICore(Close, gamma, &lr_w0, &lr_w3, &lr_wd);
}
