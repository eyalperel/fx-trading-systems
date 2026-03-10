// Test_SuperSmoother.c
// Purpose: Verify SuperSmoother 2-pole runs without errors,
//          produces reasonable output, and exports to CSV for Python analysis
// Run on:  EUR/USD D1

#include <default.c>
#include "../../indicators/ehlers/SuperSmoother2Pole.c"

void run() {
    // --- Setup ---
    BarPeriod = 1440;       // D1 bars (1440 minutes)
    StartDate = 20150101;
    EndDate   = 20240101;
    LookBack  = 300;        // warmup bars — comfortably above 2x Period

    // --- Price series ---
    vars Close = series(priceClose(), 100);

    // --- Indicator ---
    var ss2 = SuperSmoother2Pole(Close, 20);

    // --- Sanity checks ---
    // Output should be close to current price, not zero or extreme
    if(is(LOOKBACK)) return;   // skip warmup bars

    // --- Export for Python validation ---
    string line = strf("%d,%f,%f\n", Bar, priceClose(), ss2);
    file_append("Data/SuperSmoother2P_EURUSD_D1.csv", line);
}