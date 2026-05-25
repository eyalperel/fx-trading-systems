// =============================================================
// Test_FRAMA_Laguerre_DSMA.c
// Week 9 validation — EUR/USD D1 (2015-2024)
//
// Outputs all three adaptive trend indicators to CSV for
// Python validation analysis.
//
// Include order (dependency chain):
//   SuperSmoother2Pole → RoofingFilter → DSMA
//   FRAMA and Laguerre are standalone
//
// RoofingFilter is computed ONCE per bar here and passed
// to DSMA — avoids double-call state corruption (Week 8).
// =============================================================

#include <default.c>
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/FRAMA.c"
#include "../../indicators/ehlers/Laguerre.c"
#include "../../indicators/ehlers/DSMA.c"

// --- Parameters ---
#define FRAMA_T      16    // half-period: full window = 32 bars
#define LAG_GAMMA    0.5   // Laguerre memory depth
#define DSMA_PERIOD  20    // StdDev + SuperSmoother lookback
#define HP_PERIOD    48    // RoofingFilter highpass cutoff
#define SS_PERIOD    10    // RoofingFilter supersmoother period

void run() {

    StartDate = 20200101;
    EndDate   = 20241231;
    BarPeriod = 240;            // H4 = 240 minutes
    Asset     = "BTC/USD";
    LookBack  = 100;

    // Build price series
    vars Close = series(priceClose());

    // Compute indicators on EVERY bar including lookback
    // so internal state is fully warmed up before output starts
    var rf_value  = RoofingFilter(Close, HP_PERIOD, SS_PERIOD);
    var frama_val = FRAMA(FRAMA_T);
    var lag_val   = Laguerre(LAG_GAMMA);
    var dsma_val  = DSMA(rf_value, DSMA_PERIOD);

    // Skip output during warmup — indicators still ran above
    if(is(LOOKBACK)) return;

    var med_price = (priceHigh() + priceLow()) / 2.0;

    file_append("Data/FRAMA_Laguerre_DSMA_BTCUSD_H4.csv",
        strf("%04d%02d%02d,%.6f,%.6f,%.6f,%.6f,%.6f\n",
            year(), month(), day(),
            med_price, frama_val, lag_val, dsma_val, rf_value));
}
