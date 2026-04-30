///////////////////////////////////////////////////////
// Test_MAMA.c
// Validates MAMA and FAMA on EUR/USD D1
// Exports Price, MAMA, FAMA
// for Python analysis
// Run in Zorro Test mode
///////////////////////////////////////////////////////
#include <default.c>
#include "../../indicators/ehlers/MAMA.c"

void run()
{
    // --- Settings ---
    StartDate = 20150101;
    EndDate   = 20241231;
    Asset     = "EUR/USD";
    BarPeriod = 1440; // D1 in minutes

    // --- Lookback ---
    if(is(LOOKBACK)) return;

    // --- Price: close, consistent with NNFX convention ---
    vars Price = series(priceClose());

    // --- Calculate MAMA and FAMA ---
    var fama = 0.0;
    var mama = MAMA(Price, 0.5, 0.05, &fama);

    // --- Sequential bar counter ---
    static int barCount = 0;
    barCount++;


    // --- Only write after warmup period (first 5 bars are flat) ---
    if(barCount <= 5) return;

    // --- Export to CSV ---
    // Columns: Bar, Price, MAMA, FAMA
    file_append("Data/MAMA_EURUSD_D1.csv",
        strf("%d,%.5f,%.5f,%.5f\n",
            barCount,
            Price[0],
            mama,
            fama));
}
