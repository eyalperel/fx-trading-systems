//////////////////////////////////////////////////////////////
// InstantTrendline_Test.c
// Day 4: Fixed vs Adaptive InstantTrendline comparison
//
// Exports both versions to CSV for Python/Jupyter analysis
// Fixed version: hardcoded DC=20 (bypasses DominantCycle)
// Adaptive version: uses DominantCycle measurement
//
// Output columns: Date,Close,ITrend_Adaptive,ITrend_Fixed,SmoothPrice,EMA20
//////////////////////////////////////////////////////////////

#include <default.c>

#include "../../indicators/ehlers/DominantCycle.c"
#include "../../indicators/ehlers/InstantTrendline.c"

#define CSV_PATH "C:/Users/eyalp/Documents/fx-trading-systems/data/fx/EUR_USD_ITrend_FixedVsAdaptive.csv"

//////////////////////////////////////////////////////////////
// InstantTrendlineFixed
// Identical 3-stage pipeline to InstantTrendline.c
// but uses a hardcoded period instead of DominantCycle
//
// This lets us isolate the effect of the adaptive DC measurement:
// any difference between this and InstantTrendline() is purely
// due to DominantCycle adapting vs staying fixed at FixedPeriod
//////////////////////////////////////////////////////////////
var InstantTrendlineFixed(vars Data, int FixedPeriod)
{
    // Use hardcoded period — no DominantCycle call
    var DC = (var)FixedPeriod;

    // Same series names with "F" suffix to avoid collision with adaptive version
    vars FFilt1  = series(0);
    vars FValue2 = series(0);
    vars FITrend = series(0);

    // STAGE 1: 3-pole Elliptic Lowpass (identical to adaptive version)
    if(Bar >= 3) {
        FFilt1[0] = 0.0542*Data[0] + 0.021*Data[1] + 0.021*Data[2] + 0.0542*Data[3]
                   + 1.9733*FFilt1[1] - 1.6067*FFilt1[2] + 0.4831*FFilt1[3];
    }

    // STAGE 2: Fixed 10-bar Notch (identical to adaptive version)
    var alpha10 = 0.6;
    var Angle10 = 360.0 / 10.0 * PI / 180.0;
    if(Bar >= 2) {
        FValue2[0] = 0.8 * (FFilt1[0] - 2*cos(Angle10)*FFilt1[1] + FFilt1[2])
                    + 1.6 * cos(Angle10) * FValue2[1] - 0.6 * FValue2[2];
    }

    // STAGE 3: Fixed DC Notch — DC is hardcoded, not measured
    // Alpha calculation identical to adaptive version
    var alpha;
    if(DC <= 20)
        alpha = 0.8;
    else if(DC >= 40)
        alpha = 0.9;
    else
        alpha = 0.8 + 0.1 * (DC - 20.0) / 20.0;

    var AngleDC = 360.0 / DC * PI / 180.0;
    var scale = (1.0 + alpha) / 2.0;
    if(Bar >= 2) {
        FITrend[0] = scale * (FValue2[0] - 2*cos(AngleDC)*FValue2[1] + FValue2[2])
                    + (1.0 + alpha) * cos(AngleDC) * FITrend[1]
                    - alpha * FITrend[2];
    }

    return FITrend[0];
}

function run()
{
    BarPeriod = 1440;  // Daily bars
    LookBack  = 100;
    StartDate = 20150101;
    EndDate   = 20240101;

    asset("EUR/USD");

    vars Price = series(priceClose());

    // --- Adaptive version (uses DominantCycle internally) ---
    var ITrend_Adaptive = InstantTrendline(Price);

    // --- Fixed version (hardcoded DC=20) ---
    // 20 bars is Ehlers' typical default for daily FX
    var ITrend_Fixed = InstantTrendlineFixed(Price, 20);

    // --- Supporting indicators ---
    var SPrice = SmoothPrice(Price);
    var ema20  = EMA(Price, 20);

    // --- CSV Export ---
    if(Bar == 1) {
        file_delete(CSV_PATH);
        file_append(CSV_PATH, "Date,Close,ITrend_Adaptive,ITrend_Fixed,SmoothPrice,EMA20\n");
    }

    string row = strf("%s,%.5f,%.5f,%.5f,%.5f,%.5f\n",
                      strdate("%Y.%m.%d", 0),
                      Price[0],
                      ITrend_Adaptive,
                      ITrend_Fixed,
                      SPrice,
                      ema20);
    file_append(CSV_PATH, row);

    // --- Debug output every 50 bars ---
    if(Bar % 50 == 0) {
        printf("\n[Bar %d] Price=%.5f Adaptive=%.5f Fixed=%.5f",
               Bar, Price[0], ITrend_Adaptive, ITrend_Fixed);
    }

    // --- Plot all versions ---
    plot("Price",          Price[0],        LINE, BLACK);
    plot("ITrend_Adaptive",ITrend_Adaptive, LINE, BLUE);
    plot("ITrend_Fixed",   ITrend_Fixed,    LINE, RED);
    plot("EMA20",          ema20,           LINE, GREEN);
}