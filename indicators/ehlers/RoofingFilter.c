///////////////////////////////////////////////////////
// Roofing Filter - John Ehlers
// From: "Optimal Detrending" - TASC
// Purpose: Band-pass filter isolating dominant cycle
//          = High-Pass Filter → SuperSmoother2Pole
//          HP removes trend (periods > HPPeriod)
//          SS removes noise (periods < SSPeriod)
//          Result: only dominant cycle survives
// Inputs:  Price    - price series (vars)
//          HPPeriod - high-pass cutoff (default 48)
//          SSPeriod - SuperSmoother cutoff (default 10)
// Output:  Clean cycle component, oscillates around zero
// Notes:   Standard input preprocessor for all
//          cycle oscillators (Week 8: CyberCycle, EBS)
//          HPPeriod must be >> SSPeriod to avoid
//          collapsing the passband to nothing
// Validated: EUR/USD D1, BTC/USD H4
///////////////////////////////////////////////////////


var RoofingFilter(vars Price, int HPPeriod, int SSPeriod)
{
    // Stage 1: Remove trend (everything slower than HPPeriod)
    var* hp = series(HighPassFilter(Price, HPPeriod), 3);

    // Stage 2: Remove noise (everything faster than SSPeriod)
    // SuperSmoother receives de-trended signal as input
    var roofed = SuperSmoother2Pole(hp, SSPeriod);

    return roofed;
}