///////////////////////////////////////////////////////
// High-Pass Filter - John Ehlers 2-Pole IIR
// // From: "Decyclers" - TASC (S&C V.33:09)
// Purpose: Remove trend component, isolate cycles
//          Output oscillates around zero
//          Use as input preprocessor for oscillators
// Inputs:  Price - price series (vars)
//          HPPeriod - cutoff period (default 48)
// Output:  De-trended price (oscillates around zero)
// Notes:   Trig args are RADIANS (standard C math library).
//          Ehlers' published EasyLanguage uses DEGREES - all
//          formulas converted: 360/P -> 2*PI/P. Corrected May 2026.
//          alpha1 carries 0.707 (two-pole cascade compensation).
//          Reference: HPPeriod=30 -> alpha1 = 0.138102
//          Reusable on any input series - RMO uses this directly
//          as its second stage. Callers must invoke unconditionally
//          every bar: series() allocates by call order.
//          Pair with SuperSmoother2Pole to form
//          the Roofing Filter (band-pass)
// Validated: EUR/USD D1, BTC/USD H4
///////////////////////////////////////////////////////


var HighPassFilter(vars Price, int HPPeriod)
{
    // Alpha controls the cutoff frequency
    // Smaller HPPeriod = larger alpha = more aggressive trend removal
    // Formula derived from bilinear transform of continuous-time HP prototype
    var alpha1 = (cos(0.707*2.0*PI / HPPeriod) + sin(0.707*2.0*PI / HPPeriod) - 1.0)
           / cos(0.707*2.0*PI / HPPeriod);
    // Persistent storage - needs 3 bars of history
    // Initialize at Price[0] level to avoid startup transient
    var* HP = series(Price[0], 3);
    // 2-pole high-pass filter
    // Input term: second difference of price (blocks trend, passes cycles)
    // Feedback term: IIR memory (sharp frequency cutoff)
    HP[0] = (1.0 - alpha1/2.0) * (1.0 - alpha1/2.0)
            * (Price[0] - 2.0*Price[1] + Price[2])
            + 2.0*(1.0 - alpha1) * HP[1]
            - (1.0 - alpha1) * (1.0 - alpha1) * HP[2];
    return HP[0];
}