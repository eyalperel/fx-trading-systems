///////////////////////////////////////////////////////
// Super Smoother - John Ehlers Two-Pole Butterworth Filter
// From: "Moving averages and smoothing filters" 
// Stocks & Commodities V. 7:3 (87-90)
//
// PURPOSE: Remove high-frequency noise while preserving cycles
// ADVANTAGE: Better noise reduction than EMA with acceptable delay
// DISADVANTAGE: ~2-3 bar delay (vs ~1 bar for EMA)
//
// PARAMETERS:
//   - Cutoff Period (Pco): Cycles shorter than this are filtered out
//
// RETURNS: Smoothed price value
///////////////////////////////////////////////////////


var SuperSmoother(vars Data, int Period)
{
    vars SS = series(0);

    if(Bar < 3)
        return Data[0];

    var A = exp(-4.44288 / Period);
    var B = 2.0 * A * cos(4.44288 / Period);
    var C = (1.0 - B + A*A) / 4.0;

    SS[0] = B * SS[1]
          - A*A * SS[2]
          + C * (Data[0] + 2.0*Data[1] + Data[2]);

    if(Bar < 12 || Bar % 50 == 0) {
        printf("\nSS Bar %d  SS0=%.8f SS1=%.8f SS2=%.8f  A=%.8f B=%.8f C=%.8f",
        Bar, SS[0], SS[1], SS[2], A, B, C);

    }

    return SS[0];
}



