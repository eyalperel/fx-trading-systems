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

// --- MAMA parameters (Ehlers defaults .5 / .05): built from integers at run time in run() (gotchas 9d.1:
//     a decimal literal such as 0.05 would be float32 at the call) ---

// --- FRAMA parameter ---
#define FRAMA_N     32     // full window (source N); was T = 16 (half window) = the same 32 bars

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

    // --- MAMA limits from integers: FastLimit 1/2, SlowLimit 1/20 ---
    var fvm_fl = 1;  fvm_fl = fvm_fl/2;
    var fvm_sl = 1;  fvm_sl = fvm_sl/20;

    // --- FRAMA inputs as the source (Price = (H+L)/2, High, Low); own prefix, unconditional, >= FRAMA_N values ---
    vars fvm_mid = series((priceHigh() + priceLow())/2, FRAMA_N);
    vars fvm_hi  = series(priceHigh(), FRAMA_N);
    vars fvm_lo  = series(priceLow(), FRAMA_N);

    // --- Compute indicators on every bar including lookback ---
    var mama_val = MAMA(Price, fvm_fl, fvm_sl, &fama_val);
    var frama_val = FRAMA(fvm_mid, fvm_hi, fvm_lo, FRAMA_N);

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