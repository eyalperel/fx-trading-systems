// =============================================================
// Test_C2_LaguerreRSI.c — Laguerre RSI vs MESA Stochastic
//
// Exports both indicators on market data for the C2 screens:
//   C-3a  correlation and sign agreement with C1
//   C-4b  lag profile against C1 (Amendment 3)
//   C-5   crossings per 100 bars, both assets
//   P-LR1 saturation rate on real data
//
// C-4 (lag vs price) is measured separately by Test_LagSine.c —
// a sine input is required there, and cannot answer C-4b because
// one frequency makes any two filters look alike.
//
// C1 for Strategy 2 is MESA Stochastic (Amendment 3: the
// reference is the C1 of the strategy whose slot is being filled,
// not Fisher).
// =============================================================

#include <default.c>
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/MESAStochastic.c"
#include "../../indicators/ehlers/LaguerreRSI.c"

// ---------- CONFIG: change these together ----------
#define ASSET_NAME   "BTCUSD"
#define OUT_FILE     "Data/C2_LRSI_BTCUSD_H4.csv"
#define PRICE_MIN    1000
#define PRICE_MAX    200000
#define BAR_MINUTES  240
#define DATE_START   20200101
#define DATE_END     20241231
// ---------------------------------------------------

#define STOCH_PERIOD 20
#define HP_PERIOD    48
#define RF_SS_PERIOD 10
#define LR_GAMMA     0.5

void run() {
    AssetList = "History\\AssetsFix.csv";
    StartDate = DATE_START;
    EndDate   = DATE_END;
    BarPeriod = BAR_MINUTES;
    LookBack  = 300;

    asset(ASSET_NAME);   // return value is NOT a guard (GOTCHAS 9b.3)

    static int hdrWritten = 0;
    static int abortRun = 0;
    if(is(INITRUN)) {
        file_delete(OUT_FILE);
        hdrWritten = 0;
        abortRun = 0;
    }

    vars Close = series(priceClose());

    var mstc = MESAStochastic(Close, STOCH_PERIOD, HP_PERIOD, RF_SS_PERIOD);
    var lrsi = LaguerreRSI(Close, LR_GAMMA);

    if(is(LOOKBACK)) return;

    if(!hdrWritten) {
        file_append(OUT_FILE, "date,hour,close,mstc,lrsi\n", 0);
        hdrWritten = 1;
    }

    if(Close[0] < PRICE_MIN || Close[0] > PRICE_MAX) {
        abortRun = 1;
        quit(strf("WRONG ASSET: %s price %.4f outside [%.4f, %.4f]",
                  ASSET_NAME, Close[0], (var)PRICE_MIN, (var)PRICE_MAX));
    }
    if(abortRun) return;

    file_append(OUT_FILE,
        strf("%04d%02d%02d,%02d,%.6f,%.6f,%.6f\n",
            year(), month(), day(), hour(), Close[0], mstc, lrsi));
}
