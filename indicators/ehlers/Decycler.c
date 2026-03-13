///////////////////////////////////////////////////////
// Decycler - John Ehlers
// From: "Decyclers" - TASC
// Purpose: Low-lag trend isolation
//          = Price - HighPassFilter(Price)
//          HP removes cycles, subtraction leaves trend
//          Lower lag than SuperSmoother for trend tracking
// Inputs:  Price    - price series (vars)
//          HPPeriod - high-pass cutoff (default 48)
// Output:  Trend component of price, tracks price closely
// Notes:   Complement of HighPassFilter —
//          Decycler + HighPassFilter = raw Price
//          Use when lag reduction is more important
//          than smoothness
// Validated: EUR/USD D1, BTC/USD H4
///////////////////////////////////////////////////////

var Decycler(vars Price, int HPPeriod)
{
    // Remove cycle component via high-pass filter
    // What remains is the trend component
    var hp = HighPassFilter(Price, HPPeriod);

    // Decycler = Price - Cycles = Trend
    return Price[0] - hp;
}