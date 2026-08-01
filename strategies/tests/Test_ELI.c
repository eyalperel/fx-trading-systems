// /zorro/strategies/tests/Test_ELI.c
// Week 11 — ELI (Ehlers Leading Indicator): full implementation + CSV export
//
// Asset:    EUR/USD D1 (canonical validation pair — set via Zorro GUI)
// Period:   2015-2024 (matches Fisher/MAMA/FRAMA/Reflex/MESAStoch window)
// Output:   C:/zorro/Data/ELI_EURUSD_D1.csv
//
// Standing protocol (Week 9): all indicator calls BEFORE if(is(LOOKBACK)) return;

#include <default.c>
#include "../../indicators/ehlers/DominantCycle.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/ELI.c"

void run() {
    BarPeriod = 1440;      // D1
    LookBack = 100;
    StartDate = 20150101;
    EndDate = 20241231;

    vars Price = series(priceClose());

    // Indicators called BEFORE the LOOKBACK gate — Week 9 warmup-order rule
    var eliVal  = ELI(Price);
    var roofVal = RoofingFilter(Price, 48, 10);
    var dcVal   = DominantCycle(Price);

    if (is(LOOKBACK)) return;

    plot("ELI", eliVal, NEW, RED);
    plot("DC", dcVal, NEW, BLUE);

    static int barCount = 0;
    barCount++;

    if (barCount == 1)
        file_append("Data/ELI_EURUSD_D1.csv", "bar,close,eli,roofing,dc\n");

    file_append("Data/ELI_EURUSD_D1.csv",
        strf("%i,%.5f,%.6f,%.6f,%.2f\n", barCount, priceClose(), eliVal, roofVal, dcVal));
}