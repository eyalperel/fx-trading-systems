// =============================================================================================================
// FRAMA.c -- Fractal Adaptive Moving Average
// =============================================================================================================
// SOURCE (a): Ehlers, J. F., "Fractal Adaptive Moving Averages", Technical Analysis of Stocks & Commodities V.23:10
//   (2005), pp. 81-82, "FRAMA EasyLanguage code" sidebar, PDF p. 3.
// FORMULA (a): N = the FULL window, even (default 16). From High / Low:
//   N1 = (HH - LL)/(N/2) over bars 0..N/2-1; N2 the same over bars N/2..N-1; N3 = (HH - LL)/N over bars 0..N-1.
//   Dimen = (ln(N1 + N2) - ln(N3))/ln 2, computed only when N1, N2 and N3 are all > 0 (otherwise held; initial 0).
//   alpha = exp(-4.6*(Dimen - 1)) clamped to [.01, 1]; Filt = alpha*Price + (1 - alpha)*Filt[1];
//   Filt = Price for the first N bars. Price default (H+L)/2.
//
// DEVIATIONS FIXED (b), review docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md (FR-1..FR-8, appendix C-1..C-3, S1..S5):
//   FR-1 the parameter is the source's N (full window). The old `T` was HALF the window, and every caller passed 16,
//        i.e. a 32-bar window: callers now pass N = 32 to keep that configuration (the source default is 16).
//   FR-2 Price, High and Low are parameters (the old file read priceHigh() / priceLow() itself).
//   FR-3 per-instance state (the old `static frama_prev` / `frama_init` were shared by every call: a second instance
//        or an asset loop was silently wrong, by up to 3.3e-2 on a random walk).
//   FR-4 start-up as the source (Filt = Price while CurrentBar < N + 1; the old file seeded on its first call).
//   FR-5 the source's guard: Dimen only when N1, N2, N3 > 0, otherwise held, and Filt always updated (the old file
//        returned without update when N3 <= 0 and could take log(0)).
//   FR-6 every constant built from integers at run time (4.6 and .01 were float32 literals, gotchas 9d.1).
//   FR-7 FRAMACore exports Dimen and alpha; FRAMA() is a thin wrapper.
//   FR-8 this header (the old "default T=16", "alpha -> 0.01" and "Week 9" statements are replaced).
//
// BEHAVIOUR (b) (review section 3 and appendix; FRAMA_ArticleFidelity.toml observations):
//   * Dimen <= 2 always (N1 + N2 <= 4*N3), so alpha >= exp(-4.6) = 0.01005 and the .01 floor never binds; the
//     article's "alpha = .01 at D = 2" is rounded.
//   * With overlapping bars (H > L) Dimen >= 1 (c). With H = L (close-only data) Dimen can fall below 1 and alpha
//     clamps to 1: FRAMA = price (a steady ramp gives out = price exactly).
//   * On a steady ramp with bars of constant range, Dimen and alpha are constant and FRAMA lags by (1 - alpha)/alpha:
//     34.05 bars at N = 16, 17.27 at N = 32 (range 0.004 around a slope of 1e-4 per bar).
//   * Start-up memory is long: where alpha sits near .01 (Dimen near 2, short cycles), differences from the start
//     fall as .99^n (about 2750 bars to 1e-12).
//
// CALLER REQUIREMENTS: N even (the source's rule; not checked in code); Price, High and Low series of at least N
//   values; call unconditionally on every bar (gotchas 3.1). For the source's inputs pass
//   series((priceHigh() + priceLow())/2, n), series(priceHigh(), n), series(priceLow(), n) with n >= N. Use your own
//   local prefix: fr_ and frw_ belong to this file (gotchas 1.3).
// STATE: no statics; every series() call is unconditional and first; each instance has its own state. No includes
//   needed.
// VERIFICATION: analysis/harness/specs/FRAMA_ArticleFidelity.toml (pre-registered 7713f5b). Not verified until that
//   run passes.
// =============================================================================================================

var FRAMACore(vars Price, vars High, vars Low, int N, var* pDim, var* pAlpha)
{
    vars fr_n = series(0, 2);      // per-instance CurrentBar (9d.9)
    vars fr_F = series(0, 2);
    vars fr_D = series(0, 2);
    vars fr_A = series(0, 2);
    fr_n[0] = fr_n[1] + 1;
    fr_F[0] = fr_F[1];  fr_D[0] = fr_D[1];  fr_A[0] = fr_A[1];   // EasyLanguage hold (FR-5: Dimen held)
    var fr_k  = 46;  fr_k  = fr_k/10;
    var fr_lo = 1;   fr_lo = fr_lo/100;
    var fr_u  = 1;
    var fr_l2 = 2;   fr_l2 = log(fr_l2);
    int fr_h = N/2;
    int fr_i;
    var fr_HH = High[0];
    var fr_LL = Low[0];
    for(fr_i = 1; fr_i < N; fr_i++) {
        if(High[fr_i] > fr_HH) fr_HH = High[fr_i];
        if(Low[fr_i]  < fr_LL) fr_LL = Low[fr_i];
    }
    var fr_N3 = fr_HH - fr_LL;  fr_N3 = fr_N3/N;
    fr_HH = High[0];  fr_LL = Low[0];
    for(fr_i = 0; fr_i < fr_h; fr_i++) {
        if(High[fr_i] > fr_HH) fr_HH = High[fr_i];
        if(Low[fr_i]  < fr_LL) fr_LL = Low[fr_i];
    }
    var fr_N1 = fr_HH - fr_LL;  fr_N1 = fr_N1/fr_h;
    fr_HH = High[fr_h];  fr_LL = Low[fr_h];
    for(fr_i = fr_h; fr_i < N; fr_i++) {
        if(High[fr_i] > fr_HH) fr_HH = High[fr_i];
        if(Low[fr_i]  < fr_LL) fr_LL = Low[fr_i];
    }
    var fr_N2 = fr_HH - fr_LL;  fr_N2 = fr_N2/fr_h;
    if(fr_N1 > 0 && fr_N2 > 0 && fr_N3 > 0) {
        fr_D[0] = log(fr_N1 + fr_N2) - log(fr_N3);
        fr_D[0] = fr_D[0]/fr_l2;
    }
    var fr_e = fr_D[0] - fr_u;
    fr_e = fr_k*fr_e;
    fr_A[0] = exp(-fr_e);
    if(fr_A[0] < fr_lo) fr_A[0] = fr_lo;
    if(fr_A[0] > fr_u)  fr_A[0] = fr_u;
    fr_F[0] = fr_A[0]*Price[0] + (fr_u - fr_A[0])*fr_F[1];
    if(fr_n[0] < N + 1) fr_F[0] = Price[0];
    *pDim   = fr_D[0];
    *pAlpha = fr_A[0];
    return fr_F[0];
}

var FRAMA(vars Price, vars High, vars Low, int N)
{
    var frw_1;
    var frw_2;
    return FRAMACore(Price, High, Low, N, &frw_1, &frw_2);
}
