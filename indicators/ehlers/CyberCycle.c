// =============================================================================
// CLASSIFICATION: band-pass filter with characterised frequency response.
// NOT a cycle detector. Usable as a detrended momentum oscillator; do NOT use
// its measured period or phase to adapt parameters or project forward.
//
// Implementation verified against Ehlers' published formula; Zorro output
// reproduced in Python to 5.01e-06 (CSV rounding floor).
//
// The ~20-bar oscillation it reports is the filter chain's resonance, not a
// market property — pure Brownian motion through this pipeline yields 20.40
// bars. Slutsky (1937), Nelson & Kang (1981).
// See docs/research/Cycle_Premise_Null_Test.md
// =============================================================================
// CyberCycle.c
// Ehlers Cyber Cycle Oscillator
// Source: "Cybernetic Analysis for Stocks and Futures" (Ehlers, 2004)
//
// CONCEPT:
//   2nd-order IIR resonant bandpass filter. Ehlers PRESENTS this as measuring
//   the dominant cycle component of price; the Aug 2026 null test found no
//   such cycle on tested assets (see header above). Output oscillates in cycle mode,
//   flattens/drifts in trend mode. Does NOT self-suppress in trend mode —
//   requires external trend gate (MAMA/FAMA) for NNFX use.
//
// INPUTS:
//   cc_Input - vars - RoofingFilter output series (min 4 bars history)
//              DO NOT call RoofingFilter inside this function.
//              Caller computes Filt once per bar and passes series here.
//   cc_alpha - var  - resonance/damping parameter (default 0.07)
//              Controls amplitude (strong effect), not signal frequency (weak).
//              Smaller = larger oscillations. Larger = more damped.
//
// OUTPUT:
//   var - Cyber Cycle value for current bar (oscillates around zero)
//
// TRIGGER LINE (compute in caller):
//   var* Cyc     = series(CyberCycle(Filt, 0.07), 4);
//   var  Trigger = 2.0*Cyc[1] - Cyc[3];
//   BUY  when Trigger crosses above Cycle
//   SELL when Trigger crosses below Cycle
//
// VALIDATED (IMPLEMENTATION CORRECTNESS): Week 8, May 2026
//   NOTE: this validated behaviour and formula fidelity, NOT that the output
//   corresponds to a real market cycle. See null test, Aug 2026.
//   EUR/USD D1 (2015-2024): centered on zero, amplitude stable ±0.007
//   BTC/USD H4 (2020-2024): centered on zero, amplitude varies 10x
//                            AGC normalization required for BTC use
//   alpha=0.07 confirmed as optimal default for EUR/USD D1
//
// ZORRO IMPLEMENTATION NOTES:
//   - IIR state uses static vars (not series) — avoids series() collision
//   - All locals prefixed cc_ to avoid flat-namespace conflict with
//     SuperSmoother2Pole (which also uses c1, c2, Filt as local names)
//   - Warmup: ~100 bars (RF ~48 + CyberCycle IIR ~43)
//   - Trig: none used. Zorro sin/cos take RADIANS (standard C).
// =============================================================================

var CyberCycle(vars cc_Input, var cc_alpha)
{
    var cc_pole = 1.0 - cc_alpha;
    var cc_gain = (1.0 - cc_alpha/2.0) * (1.0 - cc_alpha/2.0);

    static var CycPrev1 = 0;
    static var CycPrev2 = 0;

    var cc_out = cc_gain * (cc_Input[0] - 2.0*cc_Input[1] + cc_Input[2])
               + 2.0*cc_pole     * CycPrev1
               - cc_pole*cc_pole * CycPrev2;

    CycPrev2 = CycPrev1;
    CycPrev1 = cc_out;

    return cc_out;
}