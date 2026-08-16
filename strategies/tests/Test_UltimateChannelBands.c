// =============================================================
// Test_UltimateChannelBands.c — Week 13 Tier 1
//
// Exports channel and band widths for P1-P4 analysis.
// Article settings: Length = STRLength = 20, NumSTRs = NumSDs = 1.
//
// Include order matters — lite-C is single-pass (GOTCHAS 5.3).
// UltimateSmootherE must precede UltimateChannelBands.
// =============================================================

#include <default.c>
#include "../../indicators/ehlers/UltimateSmootherE.c"
#include "../../indicators/ehlers/UltimateChannelBands.c"
#include "../../indicators/ehlers/FRAMA.c"
#include "../../indicators/ehlers/VolatilityRegime.c"

// ---------- CONFIG: change these together ----------
#define ASSET_NAME   "EUR/USD"
#define OUT_FILE     "Data/UCB_EURUSD_D1.csv"
#define PRICE_MIN    0.5
#define PRICE_MAX    2.0
#define BAR_MINUTES  1440
#define DATE_START   20150101
#define DATE_END     20241231
// ---------------------------------------------------

#define UCB_LENGTH    20
#define UCB_STRLEN    20
#define UCB_NUMSTRS   1.0
#define UCB_NUMSDS    1.0

// Regime classifier — parameters chosen before results, not swept
#define VR_WINDOW     250
#define VR_LO         30.0
#define VR_HI         70.0

void run() {
    AssetList = "History\\AssetsFix.csv";
    StartDate = DATE_START;
    EndDate   = DATE_END;
    BarPeriod = BAR_MINUTES;
    // 250-bar regime window + smoother warmup. Too small and the
    // rank is computed against a partially filled window, silently.
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

    var centre, chUp, chDn, str, bdUp, bdDn, sd, trBox, devSm, natr;
    UltimateChannelBands(Close, UCB_LENGTH, UCB_STRLEN,
                         UCB_NUMSTRS, UCB_NUMSDS,
                         &centre, &chUp, &chDn, &str,
                         &bdUp, &bdDn, &sd,
                         &trBox, &devSm, &natr);

    // P3 split variable. FRAMA deliberately, not the centre line:
    // the band width IS built from (Close - centre), so splitting
    // on that would be circular. FRAMA shares no term with either
    // width. T=16 per Week 9.
    var frama = FRAMA(16);

    // NATR must be a series for the regime window. Value passed
    // INTO series() — writing [0] afterward shifts the wrong value
    // into [1] next bar (GOTCHAS 3.2).
    vars NATRs = series(natr);
    var rank;
    var regime = VolatilityRegime(NATRs, VR_WINDOW, VR_LO, VR_HI, &rank);

    if(is(LOOKBACK)) return;

    if(!hdrWritten) {
        file_append(OUT_FILE,
            "date,hour,close,centre,str,sd,ch_up,ch_dn,bd_up,bd_dn,tr_box,dev_sm,frama,natr,rank,regime\n", 0);
        hdrWritten = 1;
    }

    // Price-range assertion — checks the data, not the asset name.
    // quit() completes the bar, so the latch gates the write.
    if(Close[0] < PRICE_MIN || Close[0] > PRICE_MAX) {
        abortRun = 1;
        quit(strf("WRONG ASSET: %s price %.4f outside [%.4f, %.4f]",
                  ASSET_NAME, Close[0], (var)PRICE_MIN, (var)PRICE_MAX));
    }
    if(abortRun) return;

    file_append(OUT_FILE,
        strf("%04d%02d%02d,%02d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.4f,%.0f\n",
            year(), month(), day(), hour(),
            Close[0], centre, str, sd, chUp, chDn, bdUp, bdDn,
            trBox, devSm, frama, natr, rank, regime));
}
