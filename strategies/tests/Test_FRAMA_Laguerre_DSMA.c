// =============================================================
// Test_FRAMA_Laguerre_DSMA.c
// Week 9 validation harness — rewritten Week 13 Day 2
//
// Outputs FRAMA, Laguerre and DSMA to CSV for Python validation.
//
// ASSET SWITCHING: change the three defines in the CONFIG block
// below as a UNIT. Asset name, output filename, bar period and
// date range must agree. They are adjacent deliberately — a
// previous version kept them apart and produced five months of
// EUR/USD data under a BTC filename.
//
// ASSET NAMING IS INCONSISTENT in AssetsFix.csv:
//   FX uses a slash      -> "EUR/USD"
//   Crypto does NOT      -> "BTCUSD"
// Writing "BTC/USD" by analogy silently falls back to the
// default asset. The asset() guard below makes that fatal.
//
// Include order (dependency chain):
//   SuperSmoother2Pole -> RoofingFilter -> DSMA
//   FRAMA and Laguerre are standalone
//
// RoofingFilter is computed ONCE per bar here and passed to
// DSMA — avoids double-call state corruption (Week 8).
// =============================================================

#include <default.c>
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/FRAMA.c"
#include "../../indicators/ehlers/Laguerre.c"
#include "../../indicators/ehlers/DSMA.c"

// ---------- CONFIG: change these together ----------
#define ASSET_NAME   "BTCUSD"
#define OUT_FILE     "Data/FRAMA_Laguerre_DSMA_BTCUSD_H4.csv"
#define PRICE_MIN    1000     // sanity bounds — BTC, not FX
#define PRICE_MAX    200000
#define BAR_MINUTES  240
#define DATE_START   20200101
#define DATE_END     20241231
// ---------------------------------------------------

// --- Indicator parameters ---
#define FRAMA_T      16    // half-period: full window = 32 bars
#define LAG_GAMMA    0.5   // Laguerre memory depth
#define DSMA_PERIOD  20    // StdDev + SuperSmoother lookback
#define HP_PERIOD    48    // RoofingFilter highpass cutoff
#define SS_PERIOD    10    // RoofingFilter supersmoother period

void run() {

    // Pin the asset list so the UI dropdown cannot change which
    // list the asset name resolves against.
    AssetList = "History\\AssetsFix.csv";

    StartDate = DATE_START;
    EndDate   = DATE_END;
    BarPeriod = BAR_MINUTES;
    LookBack  = 100;

    // --- Asset selection ------------------------------------
    // NOTE: asset() return value is NOT a usable guard. Zorro 2.70
    // emits "Warning 034: <name> not in asset list" and then runs
    // anyway with an auto-created dummy asset, returning non-zero.
    // Verified Week 13 Day 2 with a deliberately bogus name.
    asset(ASSET_NAME);

    // --- Run-scoped file reset ------------------------------
    // file_append appends. Without this, re-running stacks a
    // second pass under the first. Statics are reset here too:
    // they persist across [Test] presses, so hdrWritten would
    // stay 1 and the header would be lost on the second run.
    static int hdrWritten = 0;
    if(is(INITRUN)) {
        file_delete(OUT_FILE);
        hdrWritten = 0;
    }

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

    if(!hdrWritten) {
        file_append(OUT_FILE,
            "date,hour,med_price,frama,laguerre,dsma,roofing\n", 0);
        hdrWritten = 1;
    }

    var med_price = (priceHigh() + priceLow()) / 2.0;

    // --- Price-range assertion ------------------------------
    // Checks the DATA, not the asset registration. A wrong asset
    // is detectable by price magnitude: EUR/USD at ~1.12 fails a
    // BTC bound by three orders of magnitude. This is the guard
    // that would have caught the Week 9 mislabelling on bar one.
    // quit() does NOT abort at the point of call — it completes the
    // current bar first. Verified Week 13 Day 2: a bare quit() here
    // still let one mislabelled row reach the CSV. The latch below
    // gates the write independently of quit()'s timing.
    static int abortRun = 0;
    if(is(INITRUN)) abortRun = 0;
    if(med_price < PRICE_MIN || med_price > PRICE_MAX) {
        abortRun = 1;
        quit(strf("WRONG ASSET: %s price %.4f outside [%d, %d]",
                  ASSET_NAME, med_price, PRICE_MIN, PRICE_MAX));
    }
    if(abortRun) return;

    // hour() is required: on H4 bars a date alone repeats six
    // times per day and cannot key a join.
    file_append(OUT_FILE,
        strf("%04d%02d%02d,%02d,%.6f,%.6f,%.6f,%.6f,%.6f\n",
            year(), month(), day(), hour(),
            med_price, frama_val, lag_val, dsma_val, rf_value));
}
