// Test_SuperSmoother.c
// Purpose: Parameter sensitivity sweep — periods 10, 14, 20, 30
// Run on:  EUR/USD D1 and BTC/USD H4

#include <default.c>
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/SuperSmoother3Pole.c"
#include "../../indicators/ehlers/UltimateSmoother.c"

void run() {
    // --- Setup ---
    BarPeriod = 1440;       // D1 — change to 240 for H4
    StartDate = 20150101;
    EndDate   = 20240101;
    LookBack  = 300;

    // --- Price series ---
    vars Close = series(priceClose(), 300);

    // --- Four periods ---
    var ss2_10 = SuperSmoother2Pole(Close, 10);
    var ss2_14 = SuperSmoother2Pole(Close, 14);
    var ss2_20 = SuperSmoother2Pole(Close, 20);
    var ss2_30 = SuperSmoother2Pole(Close, 30);

    if(is(LOOKBACK)) return;

    string line = strf("%d,%f,%f,%f,%f,%f\n",
        Bar, priceClose(), ss2_10, ss2_14, ss2_20, ss2_30);
    file_append("Data/SuperSmoother_Sensitivity_EURUSD.csv", line);
}