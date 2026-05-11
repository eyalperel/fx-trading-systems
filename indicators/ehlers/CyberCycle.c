// =============================================================================
// CyberCycle.c
// Ehlers Cyber Cycle Oscillator
// Source: "Cybernetic Analysis for Stocks and Futures" (Ehlers, 2004)
//
// Takes pre-filtered input (RoofingFilter output) — do NOT call RoofingFilter
// inside this function. Caller computes Filt once and passes the series here.
// This prevents double-shifting of RoofingFilter's internal series().
//
// Inputs:
//   Filt   - vars (series pointer) - RoofingFilter output, min 3 bars history
//   alpha  - var  - filter resonance parameter (default 0.07)
//
// Returns:
//   var - Cyber Cycle oscillator value for current bar
//
// Usage (in test script):
//   var  filtVal = RoofingFilter(Price, 48, 10);
//   var* Filt    = series(filtVal, 4);
//   var  cycVal  = CyberCycle(Filt, 0.07);
//   var* Cyc     = series(cycVal, 4);
//   var  Trigger = 2.0*Cyc[1] - Cyc[3];
//
// Warmup: ~100 bars minimum (RoofingFilter ~48 + CyberCycle IIR ~43)
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