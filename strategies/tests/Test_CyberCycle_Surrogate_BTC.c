// =============================================================================
// Test_CyberCycle_Surrogate_BTC.c
// Exports Price + RoofingFilter + Cycle + Trigger for surrogate-data testing
// Purpose: null-hypothesis validation of the cycle premise — CRYPTO ARM
// Companion to Test_CyberCycle_Surrogate.c (EUR/USD D1)
//
// Parameters deliberately IDENTICAL to the FX arm so that any cross-asset
// difference is a property of the market, not of the tuning.
// Config: BTC/USD H4, 2020-2024 (matches original Week 8 BTC test)
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
    StartDate = 20200101;
    EndDate   = 20240101;
    Asset     = "BTC/USD";
    BarPeriod = 240;       // H4 = 240 minutes

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

    // BTC trades near 5-digit levels, so %.2f already gives ~1e-7 relative
    // precision — finer than the EUR/USD arm's %.6f on a ~1.10 price.
    // Oscillator outputs are in PRICE units here (hundreds/thousands), not
    // the ~0.01 of EUR/USD; %.5f is ample.
    file_append("Data/CyberCycle_Surrogate_BTCUSD_H4.csv",
                strf("%d,%.2f,%.5f,%.5f,%.5f\n",
                    barCount,
                    Price[0],
                    filtVal,
                    cycVal,
                    Trigger));
}