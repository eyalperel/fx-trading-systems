// =============================================================================================================
// SUPERSEDED -- do not use.
// Kept as the negative controls NCS / NCS2 of analysis/harness/specs/FRAMA_ArticleFidelity.toml (D7 rule 7):
// the statics frama_prev / frama_init (here fro_prev / fro_init) are the IIR state, shared by every call (FR-3);
// half-window parameter T (FR-1); price seed on the run's first call (FR-4); `if(N3 <= 0) return prev` without an
// N1 / N2 condition (FR-5); float32 literals 4.6 / 0.01 (FR-6). Review: docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md.
// Only edits vs the original FRAMA.c (blob 3352fbe04ed691e479564bc63d46ae181334f9bb, last commit 2a5eca5):
//   FRAMA(int T) -> FRAMA_Superseded(vars Price, vars High, vars Low, int T); the input (the ONLY behavioural
//   edit): series(priceHigh()) / series(priceLow()) -> the High / Low parameters and (priceHigh() + priceLow()) / 2.0
//   -> Price[0]; prefix frama_ -> fro_ (flat namespace, gotchas 1.3); this header. Statics, INITRUN reset,
//   literals, guard and arithmetic unchanged. The original header follows, unchanged (history, not fact).
// Corrected file: FRAMA.c (FRAMACore / FRAMA).
// =============================================================================================================
// =============================================================
// FRAMA.c — Fractal Adaptive Moving Average
// Author: John Ehlers | Implementation: Week 9
// Reference: "Fractal Adaptive Moving Averages" TASC
//
// Adapts EMA speed using fractal dimension of price:
//   D → 1 (trending)  → alpha → 1.0  (fast, tracks price)
//   D → 2 (noisy)     → alpha → 0.01 (slow, ignores noise)
//
// Parameters:
//   T : half-period (full window = 2T bars, default T=16)
//
// Returns: FRAMA value (adaptive EMA of median price)
// =============================================================

var FRAMA_Superseded(vars Price, vars High, vars Low, int T) {

    // --- Run-scoped reset ---------------------------------------
    // Lite-C statics persist for the lifetime of the LOADED script
    // — across repeated [Test] presses and across Train->Test. The
    // old value-based seed below could not fire when fro_prev
    // held a leftover value from a previous run, so FRAMA would
    // begin holding the PREVIOUS asset's level.
    //
    // Editing a source file forces a recompile, which zeroes the
    // statics — so the normal edit-and-rerun workflow was safe. A
    // repeat [Test] press without an edit was not. Week 13 Day 2:
    // the May 2026 BTC baseline differs from a clean run by 1.8e-3
    // on row 1, decaying over subsequent bars — leftover EUR/USD
    // state in the baseline, not in the clean run.
    //
    // Flag is cleared here; seeding happens on the first valid bar.
    static int fro_init = 0;
    if(is(INITRUN)) fro_init = 0;


    // --- Build High/Low series for range computation ---
    vars fro_High = High;   // input edit: was series(priceHigh())
    vars fro_Low  = Low;    // input edit: was series(priceLow())

    // --- Median price ---
    var fro_price = Price[0];   // input edit: was (priceHigh() + priceLow()) / 2.0

    // --- Box 1: bars 0 to T-1 (most recent half) ---
    var fro_Hi1 = fro_High[0];
    var fro_Lo1 = fro_Low[0];
    int fro_i;
    for(fro_i = 1; fro_i < T; fro_i++) {
        if(fro_High[fro_i] > fro_Hi1) fro_Hi1 = fro_High[fro_i];
        if(fro_Low[fro_i]  < fro_Lo1) fro_Lo1 = fro_Low[fro_i];
    }
    var fro_N1 = (fro_Hi1 - fro_Lo1) / T;

    // --- Box 2: bars T to 2T-1 (older half) ---
    var fro_Hi2 = fro_High[T];
    var fro_Lo2 = fro_Low[T];
    for(fro_i = T+1; fro_i < 2*T; fro_i++) {
        if(fro_High[fro_i] > fro_Hi2) fro_Hi2 = fro_High[fro_i];
        if(fro_Low[fro_i]  < fro_Lo2) fro_Lo2 = fro_Low[fro_i];
    }
    var fro_N2 = (fro_Hi2 - fro_Lo2) / T;

    // --- Full window: bars 0 to 2T-1 ---
    var fro_Hi3 = fro_Hi1;
    var fro_Lo3 = fro_Lo1;
    for(fro_i = T; fro_i < 2*T; fro_i++) {
        if(fro_High[fro_i] > fro_Hi3) fro_Hi3 = fro_High[fro_i];
        if(fro_Low[fro_i]  < fro_Lo3) fro_Lo3 = fro_Low[fro_i];
    }
    var fro_N3 = (fro_Hi3 - fro_Lo3) / (2.0 * T);

    // --- IIR state: seed to price on the first valid bar ---
    // Flag-based, not value-based. See the INITRUN block above.
    static var fro_prev = 0;
    if(!fro_init) {
        fro_prev = fro_price;
        fro_init = 1;
    }

    // --- Guard: flat price → no update ---
    if(fro_N3 <= 0) return fro_prev;

    // --- Fractal dimension ---
    var fro_D = (log(fro_N1 + fro_N2) - log(fro_N3)) / log(2.0);

    // --- Adaptive alpha ---
    var fro_alpha = exp(-4.6 * (fro_D - 1.0));
    if(fro_alpha > 1.0)  fro_alpha = 1.0;
    if(fro_alpha < 0.01) fro_alpha = 0.01;

    // --- EMA update ---
    var fro_out = fro_alpha * fro_price + (1.0 - fro_alpha) * fro_prev;
    fro_prev = fro_out;

    return fro_out;
}