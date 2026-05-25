// =============================================================
// Test_FRAMA_vs_MAMA.c
// Week 9 — Direct FRAMA vs MAMA/FAMA comparison
// Baseline selection for Phase 3 strategy development
//
// Output columns:
//   Date, Price, FRAMA, MAMA, FAMA
// =============================================================

#include <default.c>
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/MAMA.c"
#include "../../indicators/ehlers/FRAMA.c"

// --- MAMA parameters (Ehlers defaults) ---
#define FAST_LIMIT  0.5
#define SLOW_LIMIT  0.05

// --- FRAMA parameter ---
#define FRAMA_T     16     // half-period, full window = 32 bars

void run() {

    StartDate = 20150101;
    EndDate   = 20241231;
    BarPeriod = 1440;          // D1
    Asset     = "EUR/USD";
    LookBack  = 100;

    // --- Price series ---
    vars Price = series((priceHigh() + priceLow()) / 2.0);

    // --- FAMA output pointer ---
    var fama_val = 0;

    // --- Compute indicators on every bar including lookback ---
    var mama_val = MAMA(Price, FAST_LIMIT, SLOW_LIMIT, &fama_val);
    var frama_val = FRAMA(FRAMA_T);

    if(is(LOOKBACK)) return;

    // --- Median price ---
    var med_price = (priceHigh() + priceLow()) / 2.0;

    file_append("Data/FRAMA_vs_MAMA_EURUSD_D1.csv",
        strf("%04d%02d%02d,%.6f,%.6f,%.6f,%.6f\n",
            year(), month(), day(),
            med_price,
            frama_val,
            mama_val,
            fama_val));
}