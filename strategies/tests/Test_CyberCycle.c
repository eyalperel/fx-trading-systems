// =============================================================================
// Test_CyberCycle.c
// Validation test script for CyberCycle oscillator
// Exports: RoofingFilter input, Cycle, Trigger to CSV for Python analysis
// Run on: EUR/USD D1 first, then BTC/USD H4
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
    BarPeriod = 1440;

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

    file_append("Data/CyberCycle_EURUSD_D1.csv",
                strf("%d,%.5f,%.5f,%.5f\n",
                    barCount,
                    filtVal,
                    cycVal,
                    Trigger));
}