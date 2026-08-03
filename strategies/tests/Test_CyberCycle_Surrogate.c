// =============================================================================
// Test_CyberCycle_Surrogate.c
// Exports Price + RoofingFilter + Cycle + Trigger for surrogate-data testing
// Purpose: null-hypothesis validation of the cycle premise (Week 11 experiment)
// Derived from Test_CyberCycle.c — parameters and warmup deliberately UNCHANGED
//   so output cols 3-5 reproduce Test_CyberCycle.c cols 2-4 exactly.
// Config: EUR/USD D1, 2015-2024
// =============================================================================

#include <default.c>
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/CyberCycle.c"

#define HP_PERIOD   48
#define SS_PERIOD   10
#define CC_ALPHA    0.07
#define WARMUP_BARS 100

void run()
{
    StartDate = 20150101;
    EndDate   = 20240101;
    Asset     = "EUR/USD";
    BarPeriod = 1440;      // D1 = 1440 minutes

    if(is(LOOKBACK)) return;

    vars Price = series(priceClose());

    // Stage 1: RoofingFilter — called ONCE per bar
    var filtVal = RoofingFilter(Price, HP_PERIOD, SS_PERIOD);
    var* Filt   = series(filtVal, 4);

    // Stage 2: CyberCycle
    var cycVal = CyberCycle(Filt, CC_ALPHA);
    var* Cyc   = series(cycVal, 4);

    // Stage 3: Trigger
    var Trigger = 2.0*Cyc[1] - Cyc[3];

    // Skip warmup bars
    static int barCount = 0;
    barCount++;
    if(barCount <= WARMUP_BARS) return;

    // Price exported at FULL precision (%.6f) — surrogate generation is
    // sensitive to return-series rounding; 5dp would quantise EUR/USD returns.
    file_append("Data/CyberCycle_Surrogate_EURUSD_D1.csv",
                strf("%d,%.6f,%.5f,%.5f,%.5f\n",
                    barCount,
                    Price[0],
                    filtVal,
                    cycVal,
                    Trigger));
}