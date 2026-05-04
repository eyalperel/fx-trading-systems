///////////////////////////////////////////////////////
// Test_HighPass.c
// Validates HighPassFilter on EUR/USD D1
// Exports output to CSV for Python analysis
// Run in Zorro Test mode
///////////////////////////////////////////////////////

#include <default.c>
#include "../../indicators/ehlers/HighPassFilter.c"

void run()
{
    // --- Settings ---
    StartDate = 20150101;
    EndDate   = 20241231;
    Asset     = "EUR/USD";
    BarPeriod = 1440;

    // --- Lookback ---
    if(is(LOOKBACK)) return;

    // --- Calculate indicator ---
    vars Price = series(priceClose());
    var hp = HighPassFilter(Price, 48);

    // --- Sequential bar counter ---
    static int barCount = 0;
    barCount++;

    // --- Export to CSV ---
    // Columns: Bar, Close, HP
    file_append("Data/HP_EURUSD_D1.csv",
        strf("%d,%.5f,%.5f\n",
            barCount,
            Price[0],
            hp));
}