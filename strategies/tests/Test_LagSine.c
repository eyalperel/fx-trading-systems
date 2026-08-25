// =============================================================
// Test_LagSine.c — lag measurement by sine input
//
// The ramp method (GOTCHAS section 8, Test_USLag.c) cannot be used
// for bounded/rescaling indicators. A stochastic asks where today
// sits between its own recent high and low; on a rising line today
// IS the high, so it reads 100 forever and never varies. Laguerre
// RSI pins at 1.0 for the same reason — all four stages stay in
// order. Registered as P-LR4b before measurement.
//
// A sine input makes both move, so lag can be read as the shift
// that best aligns output with input.
//
// SuperSmoother2Pole is included as a KNOWN ANSWER. Its analytic
// DC group delay at period 20 is 4.039 bars, confirmed by the ramp
// method at 4.0387. If this harness does not recover ~4.039 for
// SuperSmoother, the method is wrong and nothing else it reports
// can be trusted (GOTCHAS section 8 standing rule).
//
// Price data is NOT used — the asset supplies a bar clock only.
// =============================================================

#include <default.c>
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/MESAStochastic.c"
#include "../../indicators/ehlers/LaguerreRSI.c"

#define SINE_PERIOD  40      // bars per full cycle
#define SS_PERIOD    20      // SuperSmoother, known lag 4.039
#define STOCH_PERIOD 20      // MESAStochastic
#define HP_PERIOD    48
#define RF_SS_PERIOD 10
#define LR_GAMMA     0.5

void run() {
    StartDate = 20150101;
    EndDate   = 20241231;
    BarPeriod = 1440;
    LookBack  = 300;
    asset("EUR/USD");

    static int barCount = 0;
    static int hdrWritten = 0;
    if(is(INITRUN)) {
        file_delete("Data/LagSine.csv");
        barCount = 0;
        hdrWritten = 0;
    }
    barCount++;

    // Synthetic sine, offset to stay positive — a stochastic needs
    // a range to work with, and negative prices would be
    // meaningless. Amplitude 1 on a base of 100.
    // Value passed INTO series() (GOTCHAS 3.2).
    vars Sine = series(100.0 + sin(2.0 * PI * barCount / SINE_PERIOD));

    var ss    = SuperSmoother2Pole(Sine, SS_PERIOD);
    var mstc  = MESAStochastic(Sine, STOCH_PERIOD, HP_PERIOD, RF_SS_PERIOD);
    var lrsi  = LaguerreRSI(Sine, LR_GAMMA);

    if(is(LOOKBACK)) return;

    if(!hdrWritten) {
        file_append("Data/LagSine.csv", "bar,sine,ss,mstc,lrsi\n", 0);
        hdrWritten = 1;
    }

    file_append("Data/LagSine.csv",
        strf("%d,%.8f,%.8f,%.8f,%.8f\n",
            barCount, Sine[0], ss, mstc, lrsi));
}
