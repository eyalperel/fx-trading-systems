// Test_SuperSmoother.c
// Purpose: Verify SuperSmoother 2-pole and 3-pole run without errors,
//          produce reasonable output, and export to CSV for Python analysis
// Run on:  EUR/USD D1

#include <default.c>
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/SuperSmoother3Pole.c"

void run() {
    // --- Setup ---
    BarPeriod = 1440;       // D1 bars (1440 minutes)
    StartDate = 20150101;
    EndDate   = 20240101;
    LookBack  = 300;        // warmup bars — comfortably above 2x Period

    // --- Price series ---
    vars Close = series(priceClose(), 300);

    // --- Indicators ---
    var ss2 = SuperSmoother2Pole(Close, 20);
    var ss3 = SuperSmoother3Pole(Close, 20);

    // --- Skip warmup bars ---
    if(is(LOOKBACK)) return;

    // --- Export for Python validation ---
    string line = strf("%d,%f,%f,%f\n", Bar, priceClose(), ss2, ss3);
    file_append("Data/SuperSmoother_EURUSD_D1.csv", line);
}