//////////////////////////////////////////////////////////////
// InstantTrendline.c
// Adaptive trendline using 3-stage filter pipeline with dynamic cycle detection
//
// Based on: "The Instantaneous Trendline"
// John F. Ehlers, Stocks & Commodities V.20:2 (February 2002)
//
// Enhancement: Uses adaptive dominant cycle instead of fixed period
//
// Usage: var trend = InstantTrendline(series(price()));
// Returns: Smooth trendline with minimal lag
//
// Theory: Three-stage pipeline removes cycles while preserving trend:
// Stage 1: Elliptic lowpass (removes high-freq noise)
// Stage 2: Fixed 10-bar notch (removes elliptic filter's weak spot)
// Stage 3: Adaptive DC notch (removes measured dominant cycle)
//////////////////////////////////////////////////////////////


//////////////////////////////////////////////////////////////
// SmoothPrice - 4-bar weighted moving average for crossover signals
//////////////////////////////////////////////////////////////
var SmoothPrice(vars Data)
{
    if(Bar >= 3)
        return (4*Data[0] + 3*Data[1] + 2*Data[2] + Data[3]) / 10.0;
    else
        return Data[0];
}

//////////////////////////////////////////////////////////////
// InstantTrendline - Main function
//
// Three-stage filter pipeline:
// 1. Elliptic lowpass: Remove frequencies >5 bars
// 2. 10-bar notch: Remove 10-bar cycle (elliptic's weakness)
// 3. Adaptive DC notch: Remove measured dominant cycle
//
// Result: Clean trend with 33-59% less lag than SMA
//////////////////////////////////////////////////////////////
var InstantTrendline(vars Data)
{
    // Measure the current dominant cycle (adaptive)
    var DC = DominantCycle(Data);
    
    // Series for 3-stage filter pipeline
    vars Filt1 = series(0);   // Stage 1 output
    vars Value2 = series(0);  // Stage 2 output
    vars ITrend = series(0);  // Stage 3 output (final)
    
    // STAGE 1: 3-pole Elliptic Lowpass Filter
    // Removes high-frequency noise (cycles <5 bars)
    // Coefficients: 0.8dB ripple, 30dB attenuation
    if(Bar >= 3) {
        Filt1[0] = 0.0542*Data[0] + 0.021*Data[1] + 0.021*Data[2] + 0.0542*Data[3]
                  + 1.9733*Filt1[1] - 1.6067*Filt1[2] + 0.4831*Filt1[3];
    }
    
    // STAGE 2: Fixed 10-bar Notch Filter
    // Removes 10-bar cycle where elliptic has high lag
    // Alpha = 0.6 controls notch width
    var alpha10 = 0.6;
    var Angle10 = 360.0 / 10.0 * PI / 180.0;  // Convert to radians
    
    if(Bar >= 2) {
        Value2[0] = 0.8 * (Filt1[0] - 2*cos(Angle10)*Filt1[1] + Filt1[2])
                   + 1.6 * cos(Angle10) * Value2[1] - 0.6 * Value2[2];
    }
    
    // STAGE 3: Adaptive Dominant Cycle Notch Filter
    // Removes the measured dominant cycle
    // Alpha adapts: 0.8 for DC=20, 0.9 for DC=40, linear between
    var alpha;
    if(DC <= 20)
        alpha = 0.8;
    else if(DC >= 40)
        alpha = 0.9;
    else
        alpha = 0.8 + 0.1 * (DC - 20.0) / 20.0;  // Linear interpolation
    
    var AngleDC = 360.0 / DC * PI / 180.0;  // Convert to radians
    
    // Notch filter with proper amplitude scaling
    var scale = (1.0 + alpha) / 2.0;
    
    if(Bar >= 2) {
        ITrend[0] = scale * (Value2[0] - 2*cos(AngleDC)*Value2[1] + Value2[2])
                   + (1.0 + alpha) * cos(AngleDC) * ITrend[1] 
                   - alpha * ITrend[2];
    }
    
    return ITrend[0];
}
