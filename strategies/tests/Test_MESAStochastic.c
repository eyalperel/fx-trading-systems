// /zorro/strategies/tests/Test_MESAStochastic.c
// Week 11 — MESA Stochastic: full implementation + CSV export for validation
//
// Asset:    EUR/USD D1 (canonical validation pair — set via Zorro GUI)
// Period:   2015-2024 (matches Fisher/MAMA/FRAMA/Reflex validation window)
// Output:   C:/zorro/Data/MESAStochastic_EURUSD_D1.csv
//
// Standing protocol (Week 9): all indicator calls BEFORE if(is(LOOKBACK)) return;

#include <default.c>
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/MESAStochastic.c"

void run() {
    BarPeriod = 1440;      // D1
    LookBack = 100;
    StartDate = 20150101;
    EndDate = 20241231;

    vars Price = series(priceClose());

    // Indicators called BEFORE the LOOKBACK gate — Week 9 warmup-order rule
    var mesaStoch = MESAStochastic(Price, 20, 48, 10);
    var roofVal   = RoofingFilter(Price, 48, 10);

    if (is(LOOKBACK)) return;

    plot("MESAStoch", mesaStoch, NEW, RED);

    static int barCount = 0;
    barCount++;

    if (barCount == 1)
        file_append("Data/MESAStochastic_EURUSD_D1.csv", "bar,close,mesastoch,roofing\n");

    file_append("Data/MESAStochastic_EURUSD_D1.csv",
        strf("%i,%.5f,%.6f,%.6f\n", barCount, priceClose(), mesaStoch, roofVal));
}