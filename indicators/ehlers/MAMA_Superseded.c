// =============================================================================================================
// SUPERSEDED -- do not use.
// Kept as the negative controls NCS / NCS2 of analysis/harness/specs/MAMA_ArticleFidelity.toml (D7 rule 7):
// the static barCount is shared by every call (MA-3); price-seeded start-up returning Price for the run's first
// 5 calls and Period / SmoothPeriod starting at 20 (MA-1); Period / Phase reset to 20 / 0 on unassigned bars (MA-2);
// float32 literals (MA-4); PI = 3.14159 (MA-5). Review: docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md.
// Only edits vs the original MAMA.c (blob bab4cbbb5961be5720bce82fc6e487e283f7f00e, last commit 2a5eca5):
//   function MAMA -> MAMA_Superseded; every local / static identifier prefixed mao_ in code (barCount, Smooth,
//   Detrender, I1, Q1, jI, jQ, I2, Q2, Re, Im, Period, SmoothPeriod, Phase, MAMAout, FAMAout, DeltaPhase, alpha;
//   flat namespace, gotchas 1.3); an explicit length 7 on each of the 15 series() calls (the original had none, so
//   each took LookBack's length: zorro.chm, series; the generated scripts set LookBack = 0, the original ran with
//   LookBack >= 7; 7 > the largest index read, [6]; Amendment 1 A1.2); this header. The parameters Price, FastLimit,
//   SlowLimit, outFAMA keep their names (the generated script passes them positionally). NO other edit: the #ifndef
//   PI block, the literals, the static and its INITRUN reset are unchanged. The original header follows, unchanged (history, not fact).
// Corrected file: MAMA.c (MAMACore / MAMA).
// =============================================================================================================
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

var MAMA_Superseded(vars Price, var FastLimit, var SlowLimit, var* outFAMA)
{
    // Bar counter: formula needs 6 bars of history before computing
    static int mao_barCount = 0;
    if(is(INITRUN)) mao_barCount = 0;   // else the 5-bar warmup guard never fires on a stale run
    mao_barCount++;

    // All intermediate variables declared as series
    // (series retains history bar-to-bar across calls)
    var* mao_Smooth       = series(Price[0], 7);   // needs [0]..[6]
    var* mao_Detrender    = series(0.0, 7);        // needs [0]..[6]
    var* mao_I1           = series(0.0, 7);        // needs [0]..[6]
    var* mao_Q1           = series(0.0, 7);        // needs [0]..[6]
    var* mao_jI           = series(0.0, 7);
    var* mao_jQ           = series(0.0, 7);
    var* mao_I2           = series(0.0, 7);        // needs [0]..[1]
    var* mao_Q2           = series(0.0, 7);        // needs [0]..[1]
    var* mao_Re           = series(0.0, 7);        // needs [0]..[1]
    var* mao_Im           = series(0.0, 7);        // needs [0]..[1]
    // Period initialized to 20: prevents bound collapse on first bar
    // (published code initializes to 0 which causes 1.5*0=0 trap)
    var* mao_Period       = series(20.0, 7);       // needs [0]..[1]
    var* mao_SmoothPeriod = series(20.0, 7);       // needs [0]..[1]
    var* mao_Phase        = series(0.0, 7);        // needs [0]..[1]
    var* mao_MAMAout      = series(Price[0], 7);   // needs [0]..[1]
    var* mao_FAMAout      = series(Price[0], 7);   // needs [0]..[1]

    // Return flat until 6 bars of history accumulated
    if(mao_barCount <= 5) {
        *outFAMA = Price[0];
        return Price[0];
    }

    // Stage 1: Smooth price
    // 4-bar weighted average, recent bars weighted more
    mao_Smooth[0] = (4.0*Price[0] + 3.0*Price[1] + 2.0*Price[2] + Price[3]) / 10.0;

    // Stage 2: Detrender - first Hilbert Transform pass
    // Removes trend component, isolates dominant cycle
    // (.075*Period[1]+.54) = period-adaptive amplitude correction
    mao_Detrender[0] = (0.0962*mao_Smooth[0] + 0.5769*mao_Smooth[2]
                   - 0.5769*mao_Smooth[4] - 0.0962*mao_Smooth[6])
                   * (0.075*mao_Period[1] + 0.54);

    // Stage 3: InPhase and Quadrature components
    // Q1: second HT pass on Detrender -> 90 degree phase advance
    // I1: Detrender delayed 3 bars -> time-aligns with Q1
    mao_Q1[0] = (0.0962*mao_Detrender[0] + 0.5769*mao_Detrender[2]
            - 0.5769*mao_Detrender[4] - 0.0962*mao_Detrender[6])
            * (0.075*mao_Period[1] + 0.54);
    mao_I1[0] = mao_Detrender[3];

    // Stage 4: Advance phase of I1 and Q1 by 90 degrees
    // jI and jQ feed phasor addition in Stage 5
    mao_jI[0] = (0.0962*mao_I1[0] + 0.5769*mao_I1[2]
            - 0.5769*mao_I1[4] - 0.0962*mao_I1[6])
            * (0.075*mao_Period[1] + 0.54);
    mao_jQ[0] = (0.0962*mao_Q1[0] + 0.5769*mao_Q1[2]
            - 0.5769*mao_Q1[4] - 0.0962*mao_Q1[6])
            * (0.075*mao_Period[1] + 0.54);

    // Stage 5: Phasor addition for 3-bar averaging
    // Reinforces true cycle signal, partially cancels noise
    mao_I2[0] = mao_I1[0] - mao_jQ[0];
    mao_Q2[0] = mao_Q1[0] + mao_jI[0];
    // Smooth I2 and Q2 before discriminator
    mao_I2[0] = 0.2*mao_I2[0] + 0.8*mao_I2[1];
    mao_Q2[0] = 0.2*mao_Q2[0] + 0.8*mao_Q2[1];

    // Stage 6: Homodyne Discriminator
    // Multiplies signal by itself delayed 1 bar
    // Re ~ cos(DeltaPhase), Im ~ sin(DeltaPhase)
    mao_Re[0] = mao_I2[0]*mao_I2[1] + mao_Q2[0]*mao_Q2[1];
    mao_Im[0] = mao_I2[0]*mao_Q2[1] - mao_Q2[0]*mao_I2[1];
    // Smooth Re and Im
    mao_Re[0] = 0.2*mao_Re[0] + 0.8*mao_Re[1];
    mao_Im[0] = 0.2*mao_Im[0] + 0.8*mao_Im[1];

    // Extract dominant cycle period from phase change
    // atan() returns radians -> *180/PI converts to degrees
    // Published: Period = 360/ArcTangent(Im/Re) [degrees]
    if(mao_Im[0] != 0.0 && mao_Re[0] != 0.0)
        mao_Period[0] = 360.0 / (atan(mao_Im[0]/mao_Re[0]) * 180.0/PI);

    // Five-layer period bounding (exact published bounds)
    if(mao_Period[0] > 1.5*mao_Period[1])  mao_Period[0] = 1.5*mao_Period[1];
    if(mao_Period[0] < 0.67*mao_Period[1]) mao_Period[0] = 0.67*mao_Period[1];
    if(mao_Period[0] < 6.0)            mao_Period[0] = 6.0;
    if(mao_Period[0] > 50.0)           mao_Period[0] = 50.0;
    mao_Period[0] = 0.2*mao_Period[0] + 0.8*mao_Period[1];
    mao_SmoothPeriod[0] = 0.33*mao_Period[0] + 0.67*mao_SmoothPeriod[1];

    // Stage 7: Phase measurement from Q1/I1
    // atan() returns radians -> convert to degrees
    if(mao_I1[0] != 0.0)
        mao_Phase[0] = atan(mao_Q1[0]/mao_I1[0]) * 180.0/PI;

    // DeltaPhase: reversed subtraction per Ehlers convention
    // (phase decreases forward in time in his framework)
    var mao_DeltaPhase = mao_Phase[1] - mao_Phase[0];
    if(mao_DeltaPhase < 1.0) mao_DeltaPhase = 1.0;

    // Adaptive alpha: FastLimit/DeltaPhase, bounded both sides
    var mao_alpha = FastLimit / mao_DeltaPhase;
    if(mao_alpha < SlowLimit) mao_alpha = SlowLimit;
    if(mao_alpha > FastLimit) mao_alpha = FastLimit;

    // MAMA: adaptive EMA with variable alpha
    mao_MAMAout[0] = mao_alpha*Price[0] + (1.0 - mao_alpha)*mao_MAMAout[1];

    // FAMA: follows MAMA at half alpha
    // Guaranteed slower than MAMA -> crossover is meaningful
    mao_FAMAout[0] = 0.5*mao_alpha*mao_MAMAout[0] + (1.0 - 0.5*mao_alpha)*mao_FAMAout[1];

    *outFAMA = mao_FAMAout[0];
    return mao_MAMAout[0];
}
