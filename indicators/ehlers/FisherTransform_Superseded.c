// =============================================================================
// FisherTransform_Superseded.c
//
// SUPERSEDED - do not use. Kept as the negative control NCS / NCT of
// FSH_ArticleFidelity (F-1 file statics and a global trigger shared by every call;
// F-3 float32 literals). Only edit vs the original (blob 259954ed): the input is a
// parameter (for synthetic inputs). Corrected file: FisherTransform.c.
//
// Edits vs the original body (b): function FisherTransform(int Period) ->
// FisherTransform_Superseded(vars Price, int Period); the input line
// `series((priceHigh() + priceLow()) * 0.5)` -> the Price parameter (kept as the
// alias `vars fto_Mid = Price;` so that every later use is unchanged); every ft_
// identifier -> fto_ (flat namespace, gotchas 1.3). Statics, literals (.33, .67, .99,
// .999), the guard, the clamp, the INITRUN resets and the trigger global are unchanged.
// =============================================================================

// Global trigger line — accessible from test script after each call
var fto_Trigger = 0;

var FisherTransform_Superseded(vars Price, int Period) {

    // --- Price input: midpoint bar (H+L)/2 ---
    // Ehlers explicitly uses midpoint, not Close, in the original EasyLanguage
    vars fto_Mid = Price;   // the ONLY behavioural edit: input is a parameter (was series((priceHigh() + priceLow()) * 0.5))

    // --- Channel: highest high and lowest low over Period bars ---
    var fto_MaxH = MaxVal(fto_Mid, Period);
    var fto_MinL = MinVal(fto_Mid, Period);

    // --- Normalize price to [-1, +1] ---
    // Maps current price position within the Period channel to [-1, +1]
    // Guard against zero range (flat price — unlikely on real data, possible in warmup)
    var fto_raw = 0;
    if(fto_MaxH - fto_MinL > 0)
        fto_raw = 2.0 * ((fto_Mid[0] - fto_MinL) / (fto_MaxH - fto_MinL) - 0.5);

    // --- Stage 1: smooth the normalized input ---
    // EMA with alpha=0.33 (0.33 + 0.67 = 1.0 — proper EMA)
    // Prevents single-bar channel spikes from contaminating the transform input
    static var fto_Value1 = 0;
    if(is(INITRUN)) fto_Value1 = 0;   // statics persist across runs
    fto_Value1 = 0.33 * fto_raw + 0.67 * fto_Value1;

    // --- Clamp to prevent log(0) or log(negative) in the transform ---
    // Check fires at ±0.99; assignment is ±0.999 — matches Ehlers' exact code
    if(fto_Value1 >  0.99) fto_Value1 =  0.999;
    if(fto_Value1 < -0.99) fto_Value1 = -0.999;

    // --- Capture previous Fisher as trigger BEFORE updating Fish ---
    // fto_Trigger holds Fish from the previous bar — this is the signal line
    static var fto_Fish = 0;
    if(is(INITRUN)) fto_Fish = 0;   // statics persist across runs
    fto_Trigger = fto_Fish;

    // --- Stage 2: Fisher transform + smooth output ---
    // 0.5 * log((1+x)/(1-x)) is arctanh(x) — the Gaussian-shaping transform
    // + 0.5 * fto_Fish is a second EMA (alpha=0.5) applied to the output
    // This light feedback smooths the output without distorting the distribution
    fto_Fish = 0.5 * log((1.0 + fto_Value1) / (1.0 - fto_Value1)) + 0.5 * fto_Fish;

    return fto_Fish;
}