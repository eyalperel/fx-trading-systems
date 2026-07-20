// /zorro/strategies/tests/Test_Reflex.c
// Week 11 — Reflex indicator: full implementation + CSV export for validation
// Now also exports RoofingFilter as a phase-shift-free cross-check for the
// lag/lead test (differencing raw price introduces a quarter-cycle phase
// shift for cyclical content — RoofingFilter avoids that)
//
// Asset:    EUR/USD D1 (canonical validation pair — set via Zorro GUI)
// Period:   2015-2024 (matches Fisher/MAMA/FRAMA validation window)
// Output:   C:/zorro/Data/Reflex_EURUSD_D1.csv
//
// Standing protocol (Week 9): all indicator calls BEFORE if(is(LOOKBACK)) return;

#include <default.c>
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/Reflex.c"

void run() {
    BarPeriod = 1440;      // D1
    LookBack = 100;
    StartDate = 20150101;
    EndDate = 20241231;

    vars Price = series(priceClose());

    // Indicators called BEFORE the LOOKBACK gate — Week 9 warmup-order rule
    var reflexVal = Reflex(Price, 20);
    var roofVal   = RoofingFilter(Price, 48, 10);

    if (is(LOOKBACK)) return;

    plot("Reflex", reflexVal, NEW, RED);
    plot("Roofing", roofVal, NEW, BLUE);

    static int barCount = 0;
    barCount++;

    if (barCount == 1)
        file_append("Data/Reflex_EURUSD_D1.csv", "bar,close,reflex,roofing\n");

    file_append("Data/Reflex_EURUSD_D1.csv",
        strf("%i,%.5f,%.6f,%.6f\n", barCount, priceClose(), reflexVal, roofVal));
}