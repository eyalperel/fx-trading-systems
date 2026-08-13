// =============================================================
// Test_USLag.c — ramp steady-state lag measurement
//
// Feeds a synthetic ramp (slope = 1 per bar) to both
// UltimateSmoother implementations and exports input vs output.
// Price data is NOT used — the asset only supplies a bar clock.
//
// Method (GOTCHAS section 8): a filter with unity DC gain tracks
// a ramp with a constant offset once settled. With slope 1, that
// offset in value IS the lag in bars. Early bars are startup
// transient and must be discarded.
// =============================================================

#include <default.c>
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/UltimateSmoother.c"
#include "../../indicators/ehlers/UltimateSmootherE.c"

#define PERIOD 20

void run() {
    StartDate = 20150101;
    EndDate   = 20241231;
    BarPeriod = 1440;
    // Series length cannot exceed LookBack. With LookBack = 0 all
    // series are allocated with NO history — Warning 041 "series
    // with no size" — and every [1]/[2] access returns 0, silently
    // feeding all filters (barCount, 0, 0) instead of a ramp.
    LookBack  = 100;
    asset("EUR/USD");

    static int barCount = 0;
    static int hdrWritten = 0;
    if(is(INITRUN)) {
        file_delete("Data/US_Lag.csv");
        barCount = 0;
        hdrWritten = 0;
    }

    barCount++;

    // Synthetic ramp: slope exactly 1 per bar.
    // Value must be passed INTO series() — series(0) followed by
    // an overwrite of [0] shifts the ZERO into [1] next bar, so
    // history stays permanently 0 (GOTCHAS 3.2).
    vars Ramp = series(barCount);

    var usE = UltimateSmootherE(Ramp, PERIOD);
    var usW5 = UltimateSmoother(Ramp, PERIOD);
    var ss  = SuperSmoother2Pole(Ramp, PERIOD);

    if(!hdrWritten) {
        file_append("Data/US_Lag.csv", "bar,ramp,r1,r2,usE,usW5,ss\n", 0);
        hdrWritten = 1;
    }

    file_append("Data/US_Lag.csv",
        strf("%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
            barCount, Ramp[0], Ramp[1], Ramp[2], usE, usW5, ss));
}
