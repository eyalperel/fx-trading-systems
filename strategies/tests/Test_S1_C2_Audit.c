#include <default.c>

// Strategy 1 C2 audit: measure |rho| between Reflex (C2) and Fisher (C1).
// Applies criterion C-3 from docs/indicators/C2_Selection_Criteria_PreRegistered.md
// to a slot locked in Week 11 on qualitative grounds only.
// Dependency order - Light-C is single pass.
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/FisherTransform.c"
#include "../../indicators/ehlers/Reflex.c"

// LOCKED Strategy 1 parameters - do not vary.
#define REFLEX_LENGTH 20
#define FISHER_PERIOD 10

void run()
{
    StartDate = 20200101;
    EndDate   = 20241231;
    BarPeriod = 240;
    asset("BTC/USD");

    static int barCount = 0;
    barCount++;

    vars Price = series(priceClose());

    // Compute before the lookback guard. Both calls unconditional,
    // fixed order - series() allocates by call order.
    var reflexVal = Reflex(Price, REFLEX_LENGTH);
    var fisherVal = FisherTransform(FISHER_PERIOD);

    if(is(LOOKBACK)) return;

    static int hdrWritten = 0;
    if(!hdrWritten) {
        file_append("Data/S1_C2_Audit_BTCUSD_H4.csv",
            "barIndex,Price,Reflex,Fisher\n", 0);
        hdrWritten = 1;
    }

    file_append("Data/S1_C2_Audit_BTCUSD_H4.csv",
        strf("%d,%.6f,%.8f,%.8f\n",
             barCount, Price[0], reflexVal, fisherVal), 0);
}