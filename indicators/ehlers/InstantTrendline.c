///////////////////////////////////////////////////////
// InstantTrendline - John Ehlers Low-Lag Trendline
// From: "The Instantaneous Trendline" 
// Stocks & Commodities V. 20:2 (28-32)
//
// PURPOSE: Extract trend component with minimal lag
// METHOD: 3-stage filter pipeline
//   Stage 1: Elliptic lowpass (remove high-freq noise)
//   Stage 2: 10-bar notch (remove problematic frequency)
//   Stage 3: Dominant cycle notch (remove main cycle)
//
// ADVANTAGE: Much lower lag than SMA
//   - 21-bar cycle: 6.7 bars lag (vs 10 bars for SMA)
//   - 40-bar cycle: 8.2 bars lag (vs 20 bars for SMA)
//
// PARAMETERS:
//   - Data: Price series (typically priceClose())
//   - DC: Dominant cycle period (fixed for now, will be adaptive later)
//
// RETURNS: Trendline value with minimal lag
///////////////////////////////////////////////////////

var InstantTrendline(vars Data, int DC)
{
    // Series for each filter stage
    vars Filt1 = series(0);  // Stage 1: Elliptic lowpass
    vars Value2 = series(0); // Stage 2: 10-bar notch
    vars ITrend = series(0); // Stage 3: Dominant cycle notch
    
    // Need at least 3 bars for filters
    if(Bar < 3)
        return Data[0];
    
    // STAGE 1: Elliptic Lowpass Filter
    // Removes cycles shorter than 5 bars
    // Coefficients: 0.0542, 0.021, 0.021, 0.0542 (input)
    //               1.9733, -1.6067, 0.4831 (feedback)
    Filt1[0] = 0.0542*Data[0] + 0.021*Data[1] + 0.021*Data[2] + 0.0542*Data[3]
             + 1.9733*Filt1[1] - 1.6067*Filt1[2] + 0.4831*Filt1[3];
    
    // STAGE 2: 10-Bar Notch Filter
    // Removes the 10-bar cycle component (where elliptic has high lag)
    // Alpha = 0.6 for this notch
    // CRITICAL: cos() expects RADIANS!
    var Angle10 = 360.0 / 10.0 * PI / 180.0;  // Convert to radians
    
    Value2[0] = 0.8*(Filt1[0] - 2*cos(Angle10)*Filt1[1] + Filt1[2])
              + 1.6*cos(Angle10)*Value2[1] - 0.6*Value2[2];
    
    // STAGE 3: Dominant Cycle Notch Filter
    // Removes the measured dominant cycle
    // Alpha adapts based on DC length (0.8 for short, 0.9 for long)
    var alpha;
    if(DC <= 20)
        alpha = 0.8;
    else if(DC >= 40)
        alpha = 0.9;
    else
        alpha = 0.8 + 0.1 * (DC - 20.0) / 20.0;  // Linear interpolation

    // CRITICAL: cos() expects RADIANS!
    var AngleDC = 360.0 / DC * PI / 180.0;  // Convert to radians

    // Notch filter formula from Ehlers
    // The (1+alpha)/2 scaling preserves signal amplitude
    var scale = (1.0 + alpha) / 2.0;
    ITrend[0] = scale * (Value2[0] - 2*cos(AngleDC)*Value2[1] + Value2[2])
            + (1.0 + alpha) * cos(AngleDC) * ITrend[1] 
            - alpha * ITrend[2];
    
    // Debug output (first 12 bars + every 50th bar)
    if(Bar < 12 || Bar % 50 == 0) {
        printf("\n[IT Bar %d] DC=%d alpha=%.2f Filt1=%.5f V2=%.5f ITrend=%.5f",
               Bar, DC, alpha, Filt1[0], Value2[0], ITrend[0]);
    }
    
    return ITrend[0];
}

// Helper function: Smoothed Price (4-bar WMA)
// Used for crossover signals with InstantTrendline
// Lag: ~1 bar (very responsive)
var SmoothPrice(vars Data)
{
    if(Bar < 3)
        return Data[0];
    
    // Weighted: 4-3-2-1, divide by 10
    return (4*Data[0] + 3*Data[1] + 2*Data[2] + Data[3]) / 10.0;
}