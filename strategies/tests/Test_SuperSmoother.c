// Test_SuperSmoother.c
// Purpose: Verify SuperSmoother 2-pole, 3-pole, and Ultimate Smoother
//          run without errors, produce reasonable output,
//          and export to CSV for Python analysis
// Run on:  BTC/USD H4

#include <default.c>
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/SuperSmoother3Pole.c"
#include "../../indicators/ehlers/UltimateSmoother.c"

void run() {
    // --- Setup ---
    BarPeriod = 240;        // H4 bars (240 minutes)
    StartDate = 20200101;
    EndDate   = 20240101;
    LookBack  = 300;        // warmup bars

    // --- Price series ---
    vars Close = series(priceClose(), 300);

    // --- Indicators ---
    var ss2 = SuperSmoother2Pole(Close, 20);
    var ss3 = SuperSmoother3Pole(Close, 20);
    var us  = UltimateSmoother(Close, 20);

    // --- Skip warmup bars ---
    if(is(LOOKBACK)) return;

    // --- Export for Python validation ---
    string line = strf("%d,%f,%f,%f,%f\n", Bar, priceClose(), ss2, ss3, us);
    file_append("Data/SuperSmoother_BTCUSD_H4.csv", line);
}