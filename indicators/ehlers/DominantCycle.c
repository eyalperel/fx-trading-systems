//////////////////////////////////////////////////////////////
// DominantCycle.c
// Measures the dominant cycle period in price data using Griffiths method
//
// Based on: "Linear Predictive Filters And Instantaneous Frequency"
// John F. Ehlers, Stocks & Commodities V.43:01 (January 2025)
//
// Usage: var dc = DominantCycle(series(price()));
// Returns: Dominant cycle period (18-40 bars)
//
// Theory: Uses adaptive linear predictive filter coefficients to
// measure spectral power across frequencies. The period with maximum
// power is the dominant cycle.
//////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////
// Internal helper: HighPass filter for DominantCycle
//////////////////////////////////////////////////////////////
var HighPass_DC(vars Data, int Period)
{
    vars HP = series(0);
    
    // 2-pole Butterworth highpass coefficients
    var a1 = exp(-1.414 * PI / Period);
    var b1 = 2 * a1 * cos(1.414 * 180 / Period * PI/180);
    var c2 = b1;
    var c3 = -a1 * a1;
    var c1 = (1 + c2 - c3) / 4;
    
    if(Bar >= 3)
        HP[0] = c1*(Data[0] - 2*Data[1] + Data[2]) + c2*HP[1] + c3*HP[2];
    else
        HP[0] = 0;
    
    return HP[0];
}

//////////////////////////////////////////////////////////////
// Internal helper: SuperSmoother filter for DominantCycle
//////////////////////////////////////////////////////////////
var SuperSmoother_DC(vars Data, int Period)
{
    vars SS = series(0);
    
    // 2-pole Butterworth lowpass coefficients
    var a1 = exp(-1.414 * PI / Period);
    var b1 = 2 * a1 * cos(1.414 * 180 / Period * PI/180);
    var c2 = b1;
    var c3 = -a1 * a1;
    var c1 = 1 - c2 - c3;
    
    if(Bar >= 2)
        SS[0] = c1*(Data[0] + Data[1])/2 + c2*SS[1] + c3*SS[2];
    else
        SS[0] = Data[0];
    
    return SS[0];
}

//////////////////////////////////////////////////////////////
// DominantCycle - Main function
//
// Algorithm:
// 1. Band-limit data (remove very long trends and short noise)
// 2. Normalize to [-1, +1] using AGC
// 3. Compute adaptive linear predictive filter coefficients
// 4. Extract spectrum by testing each period (18-40)
// 5. Find period with maximum power
// 6. Smooth result to prevent jumps
//////////////////////////////////////////////////////////////
var DominantCycle(vars Data)
{
    // Configuration
    int LowerBound = 18;   // Shortest detectable cycle
    int UpperBound = 40;   // Longest detectable cycle
    int Length = 40;       // Data history length for coefficient calculation
    
    // Persistent state variables
    static var Mu = 0;           // Convergence factor
    static var Peak = 0.1;       // AGC peak tracker
    vars HP = series(0);         // Highpass filtered data
    vars LP = series(0);         // Lowpass filtered data
    vars Signal = series(0);     // Normalized signal
    
    // Arrays for linear predictive filter
    static var XX[100];          // Data array
    static var coef[100];        // Adaptive coefficients
    static var Pwr[100];         // Power at each period
    
    // Working variables
    var XBar;
    int count, Period;
    var Real, Imag, Denom;
    var MaxPwr, Cycle;
    
    // --- Run-scoped reset ---------------------------------------
    // Lite-C statics persist for the lifetime of the LOADED script.
    // Only the three genuinely persistent ones are reset here:
    //   Peak        AGC tracker, decays 0.991/bar across bars
    //   coef[]      Griffiths adaptive coefficients, accumulate
    //   SmoothCycle rate limiter, carries forward (reset at decl.)
    // Mu, XX[] and Pwr[] are write-before-read every bar and do
    // not leak. Values below restore the DECLARED initialisers, so
    // behaviour matches a freshly compiled run exactly.
    if(is(INITRUN)) {
        Peak = 0.1;
        for(count = 0; count < 100; count++) coef[count] = 0;
    }

    // Initialize convergence factor
    Mu = 1.0 / Length;
    
    // STEP 1: Band-limit the data
    // Remove trends longer than UpperBound and noise shorter than LowerBound
    HP[0] = HighPass_DC(Data, UpperBound);
    LP[0] = SuperSmoother_DC(HP, LowerBound);
    
    // STEP 2: AGC normalization
    // Fast attack (immediate if larger), slow decay (0.991 per bar)
    Peak = 0.991 * Peak;
    if(abs(LP[0]) > Peak) 
        Peak = abs(LP[0]);
    
    if(Peak != 0) 
        Signal[0] = LP[0] / Peak;
    else
        Signal[0] = 0;
    
    // STEP 3: Load data into array (reverse order for easier indexing)
    for(count = 0; count < Length; count++) {
        XX[count] = Signal[Length - 1 - count];
    }
    
    // STEP 4: Compute adaptive filter coefficients (Griffiths method)
    // Predict current value from past values
    XBar = 0;
    for(count = 0; count < Length; count++) {
        XBar = XBar + XX[Length - 1 - count] * coef[count];
    }
    
    // Update coefficients to minimize prediction error
    for(count = 0; count < Length; count++) {
        coef[count] = coef[count] + Mu * (XX[Length - 1] - XBar) * XX[Length - 1 - count];
    }
    
    // STEP 5: Extract spectrum from coefficients
    // Test each period by applying complex frequency probe
    for(Period = LowerBound; Period <= UpperBound; Period++) 
    {
        Real = 0;  // In-phase component
        Imag = 0;  // Quadrature component
        
        // Evaluate transfer function at this frequency
        for(count = 0; count < Length; count++) {
            Real = Real + coef[count] * cos(2 * PI * count / Period);
            Imag = Imag + coef[count] * sin(2 * PI * count / Period);
        }
        
        // Power = 1 / |H(w)|^2
        Denom = (1 - Real) * (1 - Real) + Imag * Imag;
        Pwr[Period] = 0.1 / Denom;  // 0.1 = EMA smoothing alpha
    }
    
    // STEP 6: Find period with maximum power (dominant cycle)
    MaxPwr = 0;
    Cycle = 20;  // Default fallback
    
    for(Period = LowerBound; Period <= UpperBound; Period++) 
    {
        if(Pwr[Period] > MaxPwr) {
            MaxPwr = Pwr[Period];
            Cycle = Period;
        }
    }
    
    // STEP 7: Smooth output to prevent sudden jumps
    // Limit change to ±2 bars per update
    static var SmoothCycle = 20;
    if(is(INITRUN)) SmoothCycle = 20;   // restores declared initialiser
    if(Cycle > SmoothCycle + 2) Cycle = SmoothCycle + 2;
    if(Cycle < SmoothCycle - 2) Cycle = SmoothCycle - 2;
    SmoothCycle = Cycle;
    
    return Cycle;
}
