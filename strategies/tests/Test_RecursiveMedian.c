#include <default.c>

// Dependency order matters - Light-C is single-pass.
// RecursiveMedian.c calls HighPassFilter, so it must come first.
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/RecursiveMedian.c"
#include "../../indicators/ehlers/AlphaBetaFilter.c"

// ---- Parameters (defaults from Ehlers TASC V.36:03) ----
#define LP_PERIOD   12    // RM low-pass critical period
#define HP_PERIOD   30    // RMO high-pass critical period
#define AB_GAIN     0.10  // alpha-beta: inside usable range [0.02, 0.20]
#define EMA_ALPHA   0.40  // comparison baseline, similar smoothing to RM

void run()
{
    // ---- Asset / timeframe: set explicitly, do not inherit ----
    StartDate = 20150101;
    EndDate   = 20241231;
    BarPeriod = 1440;              // D1
    asset("EUR/USD");
    LookBack  = 200;

    // Bar counter - (int)Now fails for bar dating in Light-C
    static int barCount = 0;
    barCount++;

    vars Price = series(priceClose());

    // ---------------------------------------------------------
    // Compute ALL indicators BEFORE the LOOKBACK guard.
    // Returning early would starve the IIR filters of warmup.
    // Every call here is unconditional: series() allocates by
    // call order, so a conditional call would corrupt state.
    // ---------------------------------------------------------
    var rm    = RecursiveMedian(Price, LP_PERIOD);
    var rmo   = RecursiveMedianOsc(Price, LP_PERIOD, HP_PERIOD);
    var ab    = AlphaBetaFilter(Price, AB_GAIN);

    // Plain EMA baseline for comparison (C-6 needs this)
    vars EMAs = series(Price[0], 2);
    EMAs[0] = EMA_ALPHA * Price[0] + (1.0 - EMA_ALPHA) * EMAs[1];

    // ---------------------------------------------------------
    // Alpha verification - print once, on the first bar.
    // Day 1 reference values:
    //   alpha1 (LP=12, NO 0.707)  = 0.422650
    //   alpha2 (HP=30, WITH 0.707)= 0.138102
    // A mismatch here means the 0.707 is in the wrong place.
    // Stop and fix before trusting any exported data.
    // ---------------------------------------------------------
    if(barCount == 1) {
        var chk_a1 = (cos(2.0*PI/LP_PERIOD) + sin(2.0*PI/LP_PERIOD) - 1.0)
                   / cos(2.0*PI/LP_PERIOD);
        var chk_a2 = (cos(0.707*2.0*PI/HP_PERIOD) + sin(0.707*2.0*PI/HP_PERIOD) - 1.0)
                   / cos(0.707*2.0*PI/HP_PERIOD);
        printf("\n=== ALPHA CHECK ===");
        printf("\nalpha1 (LP=%d, no 0.707) = %.6f  [expect 0.422650]", LP_PERIOD, chk_a1);
        printf("\nalpha2 (HP=%d, w/ 0.707) = %.6f  [expect 0.138102]", HP_PERIOD, chk_a2);
        printf("\n===================\n");
    }

    if(is(LOOKBACK)) return;

    // ---- Export ----
    if(barCount == LookBack + 1)
        file_append("Data/RecursiveMedian_EURUSD_D1.csv",
            "barIndex,Price,RM,RMO,AlphaBeta,EMA\n", 0);

    file_append("Data/RecursiveMedian_EURUSD_D1.csv",
        strf("%d,%.6f,%.6f,%.8f,%.6f,%.6f\n",
             barCount, Price[0], rm, rmo, ab, EMAs[0]), 0);
}