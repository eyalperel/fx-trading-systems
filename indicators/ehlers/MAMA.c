///////////////////////////////////////////////////////
// MESA Adaptive Moving Average (MAMA) and FAMA
// John Ehlers
// Source: "MESA Adaptive Moving Averages"
//         TASC S&C V.19:9, September 2001
// ─────────────────────────────────────────────────
// Purpose:
//   Adaptive trend indicator using the Hilbert
//   Transform to measure instantaneous phase rate
//   of change and adapt smoothing speed to the
//   current dominant market cycle.
//
// Pipeline (7 stages):
//   Price → Smooth → Detrender → I1, Q1
//   → jI, jQ → I2, Q2 (phasor addition)
//   → Homodyne Discriminator → Period
//   → DeltaPhase → alpha → MAMA, FAMA
//
// Inputs:
//   Price     - price series, typically (H+L)/2
//   FastLimit - maximum alpha (default 0.5)
//   SlowLimit - minimum alpha (default 0.05)
//   outFAMA   - pointer to receive FAMA value
//
// Outputs:
//   return    - MAMA value
//   *outFAMA  - FAMA value
//
// Signal (NNFX Baseline role):
//   MAMA crosses above FAMA → bullish / go long
//   MAMA crosses below FAMA → bearish / go short
//   Spread width = trend strength proxy
//   Requires C1/C2 confirmation before entry
//
// Parameters (validated defaults):
//   FastLimit = 0.5   (Ehlers default — keep)
//   SlowLimit = 0.05  (Ehlers default — keep)
//   Low sensitivity to parameter changes confirmed
//   in Day 5 sensitivity analysis (FL=0.3 and
//   SL=0.10 variants gave negligible difference)
//
// Implementation notes:
//   - Period initialised to 20 (not 0) to prevent
//     bound collapse on first bar
//   - barCount guard: returns Price[0] for first 5 bars
//   - atan() used in degrees via *180/PI conversion
//   - Alpha is bimodal in practice: 92.5% of bars
//     clamp at FastLimit or SlowLimit (documented
//     Ehlers behaviour, not a bug)
//   - FAMA always smoother than MAMA (half alpha)
//   - Raw crossover: 51.3% win rate, 0.92 W/L —
//     must be paired with confirmation indicator
//
// Validation status: APPROVED — Week 7
//   EUR/USD D1 : 2591 bars, 2015-2024  ✓
//   BTC/USD H4 : 7529 bars, 2020-2023  ✓
//   Lag  FX=0 bars  BTC=0 bars         ✓
//   SNR  FX=1.22x   BTC=1.19x          ✓
///////////////////////////////////////////////////////

#ifndef PI
#define PI 3.14159265358979
#endif

var MAMA(vars Price, var FastLimit, var SlowLimit, var* outFAMA)
{
    // Bar counter: formula needs 6 bars of history before computing
    static int barCount = 0;
    if(is(INITRUN)) barCount = 0;   // else the 5-bar warmup guard never fires on a stale run
    barCount++;

    // All intermediate variables declared as series
    // (series retains history bar-to-bar across calls)
    var* Smooth       = series(Price[0]);   // needs [0]..[6]
    var* Detrender    = series(0.0);        // needs [0]..[6]
    var* I1           = series(0.0);        // needs [0]..[6]
    var* Q1           = series(0.0);        // needs [0]..[6]
    var* jI           = series(0.0);
    var* jQ           = series(0.0);
    var* I2           = series(0.0);        // needs [0]..[1]
    var* Q2           = series(0.0);        // needs [0]..[1]
    var* Re           = series(0.0);        // needs [0]..[1]
    var* Im           = series(0.0);        // needs [0]..[1]
    // Period initialized to 20: prevents bound collapse on first bar
    // (published code initializes to 0 which causes 1.5*0=0 trap)
    var* Period       = series(20.0);       // needs [0]..[1]
    var* SmoothPeriod = series(20.0);       // needs [0]..[1]
    var* Phase        = series(0.0);        // needs [0]..[1]
    var* MAMAout      = series(Price[0]);   // needs [0]..[1]
    var* FAMAout      = series(Price[0]);   // needs [0]..[1]

    // Return flat until 6 bars of history accumulated
    if(barCount <= 5) {
        *outFAMA = Price[0];
        return Price[0];
    }

    // Stage 1: Smooth price
    // 4-bar weighted average, recent bars weighted more
    Smooth[0] = (4.0*Price[0] + 3.0*Price[1] + 2.0*Price[2] + Price[3]) / 10.0;

    // Stage 2: Detrender - first Hilbert Transform pass
    // Removes trend component, isolates dominant cycle
    // (.075*Period[1]+.54) = period-adaptive amplitude correction
    Detrender[0] = (0.0962*Smooth[0] + 0.5769*Smooth[2]
                   - 0.5769*Smooth[4] - 0.0962*Smooth[6])
                   * (0.075*Period[1] + 0.54);

    // Stage 3: InPhase and Quadrature components
    // Q1: second HT pass on Detrender -> 90 degree phase advance
    // I1: Detrender delayed 3 bars -> time-aligns with Q1
    Q1[0] = (0.0962*Detrender[0] + 0.5769*Detrender[2]
            - 0.5769*Detrender[4] - 0.0962*Detrender[6])
            * (0.075*Period[1] + 0.54);
    I1[0] = Detrender[3];

    // Stage 4: Advance phase of I1 and Q1 by 90 degrees
    // jI and jQ feed phasor addition in Stage 5
    jI[0] = (0.0962*I1[0] + 0.5769*I1[2]
            - 0.5769*I1[4] - 0.0962*I1[6])
            * (0.075*Period[1] + 0.54);
    jQ[0] = (0.0962*Q1[0] + 0.5769*Q1[2]
            - 0.5769*Q1[4] - 0.0962*Q1[6])
            * (0.075*Period[1] + 0.54);

    // Stage 5: Phasor addition for 3-bar averaging
    // Reinforces true cycle signal, partially cancels noise
    I2[0] = I1[0] - jQ[0];
    Q2[0] = Q1[0] + jI[0];
    // Smooth I2 and Q2 before discriminator
    I2[0] = 0.2*I2[0] + 0.8*I2[1];
    Q2[0] = 0.2*Q2[0] + 0.8*Q2[1];

    // Stage 6: Homodyne Discriminator
    // Multiplies signal by itself delayed 1 bar
    // Re ~ cos(DeltaPhase), Im ~ sin(DeltaPhase)
    Re[0] = I2[0]*I2[1] + Q2[0]*Q2[1];
    Im[0] = I2[0]*Q2[1] - Q2[0]*I2[1];
    // Smooth Re and Im
    Re[0] = 0.2*Re[0] + 0.8*Re[1];
    Im[0] = 0.2*Im[0] + 0.8*Im[1];

    // Extract dominant cycle period from phase change
    // atan() returns radians -> *180/PI converts to degrees
    // Published: Period = 360/ArcTangent(Im/Re) [degrees]
    if(Im[0] != 0.0 && Re[0] != 0.0)
        Period[0] = 360.0 / (atan(Im[0]/Re[0]) * 180.0/PI);

    // Five-layer period bounding (exact published bounds)
    if(Period[0] > 1.5*Period[1])  Period[0] = 1.5*Period[1];
    if(Period[0] < 0.67*Period[1]) Period[0] = 0.67*Period[1];
    if(Period[0] < 6.0)            Period[0] = 6.0;
    if(Period[0] > 50.0)           Period[0] = 50.0;
    Period[0] = 0.2*Period[0] + 0.8*Period[1];
    SmoothPeriod[0] = 0.33*Period[0] + 0.67*SmoothPeriod[1];

    // Stage 7: Phase measurement from Q1/I1
    // atan() returns radians -> convert to degrees
    if(I1[0] != 0.0)
        Phase[0] = atan(Q1[0]/I1[0]) * 180.0/PI;

    // DeltaPhase: reversed subtraction per Ehlers convention
    // (phase decreases forward in time in his framework)
    var DeltaPhase = Phase[1] - Phase[0];
    if(DeltaPhase < 1.0) DeltaPhase = 1.0;

    // Adaptive alpha: FastLimit/DeltaPhase, bounded both sides
    var alpha = FastLimit / DeltaPhase;
    if(alpha < SlowLimit) alpha = SlowLimit;
    if(alpha > FastLimit) alpha = FastLimit;

    // MAMA: adaptive EMA with variable alpha
    MAMAout[0] = alpha*Price[0] + (1.0 - alpha)*MAMAout[1];

    // FAMA: follows MAMA at half alpha
    // Guaranteed slower than MAMA -> crossover is meaningful
    FAMAout[0] = 0.5*alpha*MAMAout[0] + (1.0 - 0.5*alpha)*FAMAout[1];

    *outFAMA = FAMAout[0];
    return MAMAout[0];
}
