///////////////////////////////////////////////////////
// Test_Decycler.c
// Validates Decycler on EUR/USD D1
// Exports Price, Decycler, and SuperSmoother2Pole
// for lag comparison in Python analysis
// Run in Zorro Test mode
///////////////////////////////////////////////////////

#include <default.c>
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/Decycler.c"

void run()
{
    // --- Settings ---
    StartDate = 20150101;
    EndDate   = 20241231;
    Asset     = "EUR/USD";
    BarPeriod = 1440; // D1 in minutes

    // --- Lookback ---
    if(is(LOOKBACK)) return;

    // --- Calculate indicators ---
    vars Price = series(priceClose());
    var dc     = Decycler(Price, 48);
    var ss     = SuperSmoother2Pole(Price, 20);

    // --- Sequential bar counter ---
    static int barCount = 0;
    barCount++;

    // --- Export to CSV ---
    // Columns: Bar, Close, Decycler, SuperSmoother
    file_append("Data/Decycler_EURUSD_D1.csv",
        strf("%d,%.5f,%.5f,%.5f\n",
            barCount,
            Price[0],
            dc,
            ss));
}