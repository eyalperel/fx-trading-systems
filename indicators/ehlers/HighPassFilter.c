///////////////////////////////////////////////////////
// High-Pass Filter - John Ehlers 2-Pole IIR
// Source (a): "Predictive And Successful Indicators", TASC (S&C V.32:1, 2014),
//          roofing-filter sidebar HP lines; same HP lines in "Decyclers"
//          (S&C V.33:09, 2015) with HPPeriod. Not the 1-pole HP (V.34:09)
//          or the $HighPass of "The Ultimate Smoother" (V.42:04).
// Purpose: Remove trend component, isolate cycles
//          Output oscillates around zero
//          Use as input preprocessor for oscillators
// Inputs:  Price - price series (vars)
//          HPPeriod - cutoff period (default 48)
// Output:  De-trended price (oscillates around zero)
// Notes:   Trig args are RADIANS (standard C math library).
//          Ehlers' published EasyLanguage uses DEGREES - all
//          formulas converted: 360/P -> 2*PI/P. Corrected May 2026.
//          Source constant .707 = 1/sqrt(2) (HARNESS_DESIGN D1 rule 1),
//          computed at run time as sqrt(2.0)/2.0: a decimal literal 0.707
//          is float32 in Zorro (gotchas 9d.1). Corrected 2026-11-17.
//          HP history starts at 0, as in the source (EasyLanguage HP(0)).
//          Was series(Price[0], 3), which started HP at the price level
//          and gave a start-up transient (GAP-1.26). Corrected 2026-11-17.
//          (b) alpha1: HPPeriod=30 -> 0.138121; HPPeriod=48 -> 0.088526
//          (the earlier 0.138102 is the 0.707 form).
//          Reusable on any input series - RMO uses this directly
//          as its second stage. Callers must invoke unconditionally
//          every bar: series() allocates by call order.
//          Pair with SuperSmoother2Pole to form
//          the Roofing Filter (band-pass)
// Verification: analysis/harness/specs/HP_ArticleFidelity.toml
//          (pre-registered 2069d86). Not verified until that run passes.
///////////////////////////////////////////////////////


var HighPassFilter(vars Price, int HPPeriod)
{
    // Alpha controls the cutoff frequency
    // Smaller HPPeriod = larger alpha = more aggressive trend removal
    // hp_k = 1/sqrt(2): two-pole cascade compensation (source: .707)
    var hp_k = sqrt(2.0) / 2.0;
    var alpha1 = (cos(hp_k*2.0*PI / HPPeriod) + sin(hp_k*2.0*PI / HPPeriod) - 1.0)
           / cos(hp_k*2.0*PI / HPPeriod);
    // Persistent storage - needs 3 bars of history
    // History starts at 0, as the source (no price-level seed)
    var* HP = series(0, 3);
    // 2-pole high-pass filter
    // Input term: second difference of price (blocks trend, passes cycles)
    // Feedback term: IIR memory (sharp frequency cutoff)
    HP[0] = (1.0 - alpha1/2.0) * (1.0 - alpha1/2.0)
            * (Price[0] - 2.0*Price[1] + Price[2])
            + 2.0*(1.0 - alpha1) * HP[1]
            - (1.0 - alpha1) * (1.0 - alpha1) * HP[2];
    return HP[0];
}