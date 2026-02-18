///////////////////////////////////////////////////////
// InstantTrendline Test Script
// Tests the 3-stage filter pipeline implementation
// Compares to EMA and SuperSmoother
///////////////////////////////////////////////////////

#include <profile.c>
#include "../../indicators/ehlers/InstantTrendline.c"
#include "../../indicators/ehlers/SuperSmoother.c"

function run()
{
    BarPeriod = 1440;  // Daily bars
    LookBack  = 100;
    StartDate = 2021;
    EndDate   = 2022;

    Verbose = 2;
    set(LOGFILE);

    Asset = "EUR/USD";

    vars Price = series(priceClose());

    // Fixed dominant cycle for now (will be adaptive later)
    int DC = 20;
    
   // Store results in series so we can access previous values
    vars ITrendSeries = series(InstantTrendline(Price, DC));
    vars SPriceSeries = series(SmoothPrice(Price));

   // Current values
    var ITrend = ITrendSeries[0];
    var SPrice = SPriceSeries[0];
    
    // Compare to other indicators
    var EMA20  = EMA(Price, 20);
    var SS10   = SuperSmoother(Price, 10);
    
    // Plot all for comparison
    plot("Price",           Price[0],  LINE, BLACK);
    plot("InstantTrendline", ITrend,   LINE, BLUE);
    plot("SmoothPrice",      SPrice,   LINE, RED);
    plot("EMA(20)",          EMA20,    LINE, GREEN);
    plot("SuperSmoother(10)", SS10,    LINE, ORANGE);
    
    // Trading signal detection (simple version for now)
    static int BarsSinceCross = 0;
    static int TrendMode = 0;
    
    // Detect crossover
    // Detect crossover (now we can use [1] because we have series)
    if(SPriceSeries[0] > ITrendSeries[0] && SPriceSeries[1] <= ITrendSeries[1]) {
        // Bullish cross
        BarsSinceCross = 0;
        TrendMode = 0;  // Reset trend mode
    }
    else if(SPriceSeries[0] < ITrendSeries[0] && SPriceSeries[1] >= ITrendSeries[1]) {
        // Bearish cross
        BarsSinceCross = 0;
        TrendMode = 0;  // Reset trend mode
    }
    else {
        BarsSinceCross++;
    }
    
    // Trend mode detection
    int HalfCycle = DC / 2;
    if(BarsSinceCross > HalfCycle && TrendMode == 0) {
        TrendMode = 1;
        printf("\n*** TREND MODE detected at Bar %d (BarsSinceCross=%d, HalfCycle=%d) ***",
               Bar, BarsSinceCross, HalfCycle);
    }
    
    // Periodic reporting
    if(Bar % 50 == 0) {
        printf("\n[Bar %d] Price=%.5f ITrend=%.5f SPrice=%.5f EMA20=%.5f",
               Bar, Price[0], ITrend, SPrice, EMA20);
        printf(" | BarsSinceCross=%d TrendMode=%d", BarsSinceCross, TrendMode);
    }
}