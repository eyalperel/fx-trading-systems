///////////////////////////////////////////////////////
// Test_RoofingFilter.c
// Validates RoofingFilter on EUR/USD D1
// Exports Price, HP, and Roofing Filter output
// for three-panel Python analysis
// Run in Zorro Test mode
///////////////////////////////////////////////////////

#include <default.c>
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/RoofingFilter.c"

void run()
{
    // --- Settings ---
    StartDate = 20200101;
    EndDate   = 20241231;
    Asset     = "BTC/USD";
    BarPeriod = 240; // H4 in minutes

    // --- Lookback ---
    if(is(LOOKBACK)) return;

    // --- Calculate indicators ---
    vars Price = series(priceClose());
    var hp      = HighPassFilter(Price, 48);
    var roofed  = RoofingFilter(Price, 48, 10);

    // --- Sequential bar counter ---
    static int barCount = 0;
    barCount++;

    // --- Export to CSV ---
    // Columns: Bar, Close, HP, Roofing
    file_append("Data/RoofingFilter_BTCUSD_H4.csv",
        strf("%d,%.5f,%.5f,%.5f\n",
            barCount,
            Price[0],
            hp,
            roofed));
}