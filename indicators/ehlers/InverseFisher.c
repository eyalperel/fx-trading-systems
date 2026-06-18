// =============================================================================
// InverseFisher.c
// Ehlers, TASC 2004 + Redux 2022 — "Inverse Fisher Transform Redux"
//
// Two functions in one file:
//
//   1. InverseFisher(x)       — simple IFT wrapper (tanh)
//      Compresses any input to (-1, +1) via a smooth soft-limiting curve.
//      Input MUST be RMS-normalized to standard deviations before calling.
//      Use this to sharpen any oscillator signal in the library.
//
//   2. ElegantOscillator(n)   — full Redux pipeline (Ehlers 2022)
//      Derivative → RMS normalize → IFT soft-limit → SuperSmoother integrate.
//      Produces a near-zero-lag oscillator from raw Close prices.
//
// NNFX Role: signal sharpener / C1 candidate (Elegant Oscillator)
//
// Inputs (ElegantOscillator):
//   BandEdge  — SuperSmoother cutoff period (default: 20)
//
// Outputs (ElegantOscillator):
//   return value — smoothed IFT oscillator, oscillates near ±1
//
// Usage in test script:
//   #include "SuperSmoother2Pole.c"    // MUST come before this file
//   #include "InverseFisher.c"
//
//   var eo = ElegantOscillator(20);
//
//   // Or wrap any existing oscillator:
//   var rms_scaled_signal = some_oscillator / its_rms;
//   var sharpened = InverseFisher(rms_scaled_signal);
//
// Dependencies: SuperSmoother2Pole.c (for ElegantOscillator only)
//
// Zorro gotchas observed:
//   - SuperSmoother2Pole expects vars (series), not var (scalar)
//     Promote eo_IFish to series before passing: series(eo_IFish)
//   - RMS loop uses a series of squared derivatives — Zorro shifts it each bar
//     No static accumulator needed; just sum 50 elements of the series
//   - eo_RMS guard: avoid divide-by-zero on first bars before series fills
//   - Zorro trig uses RADIANS — SuperSmoother internally uses cos(1.414*PI/n)
//     This is already correct in SuperSmoother.c (fixed in Week 8 audit)
// =============================================================================


// -----------------------------------------------------------------------------
// InverseFisher(x)
// Simple IFT: tanh(x) = (e^2x - 1) / (e^2x + 1)
// Output is always in (-1, +1) — hard bounded regardless of input magnitude
//
// Properties:
//   - Near zero: nearly linear (small signals pass through undistorted)
//   - Away from zero: saturates toward ±1 (large signals get compressed)
//   - Zero crossing: preserved exactly (no timing shift)
//   - Soft limiter: smoother than hard clipping, no high-frequency noise injection
// -----------------------------------------------------------------------------
var InverseFisher(var x) {
    var ift_e = exp(2.0 * x);
    return (ift_e - 1.0) / (ift_e + 1.0);
}


// -----------------------------------------------------------------------------
// ElegantOscillator(BandEdge)
// Full Redux pipeline — Ehlers TASC 2022
//
// Pipeline:
//   Step 1 — 2-bar price derivative
//             Deriv = Close - Close[2]
//             Why 2-bar (not 1-bar): also zeros out the Nyquist frequency,
//             reducing high-frequency noise before normalization
//
//   Step 2 — RMS normalization over 50 bars
//             NDeriv = Deriv / RMS
//             Puts derivative in standard deviation units so IFT compression
//             is applied in the correct region of the tanh curve
//
//   Step 3 — IFT soft-limiting
//             IFish = InverseFisher(NDeriv)
//             Compresses amplitude extremes without distorting zero crossings
//
//   Step 4 — SuperSmoother integration
//             SS = SuperSmoother2Pole(IFish, BandEdge)
//             Integrates (smooths) the amplitude-limited derivative back into
//             a coherent oscillator waveform; removes residual noise
// -----------------------------------------------------------------------------
var ElegantOscillator(int BandEdge) {

    // --- Step 1: 2-bar price derivative ---
    // Close series needed for 2-bar lookback (Close[2])
    vars eo_Close = series(priceClose());
    var  eo_Deriv = eo_Close[0] - eo_Close[2];

    // --- Step 2: RMS normalization over 50 bars ---
    // Build a series of squared derivative values — Zorro shifts each bar
    // Sum the last 50 elements to get mean squared value, then take sqrt
    vars eo_DerivSq = series(eo_Deriv * eo_Deriv);
    var  eo_RMS     = 0;
    int  eo_i;
    for(eo_i = 0; eo_i < 50; eo_i++)
        eo_RMS += eo_DerivSq[eo_i];
    if(eo_RMS > 0) eo_RMS = sqrt(eo_RMS / 50.0);

    // Normalize derivative to standard deviations
    // Guard: skip normalization if RMS not yet meaningful (early warmup bars)
    var eo_NDeriv = 0;
    if(eo_RMS > 0) eo_NDeriv = eo_Deriv / eo_RMS;

    // --- Step 3: IFT soft-limiting ---
    var eo_IFish = InverseFisher(eo_NDeriv);

    // --- Step 4: SuperSmoother integration ---
    // SuperSmoother2Pole expects vars (series), not var (scalar)
    // series(eo_IFish) promotes the scalar to a series for the SS input
    var eo_result = SuperSmoother2Pole(series(eo_IFish), BandEdge);

    return eo_result;
}