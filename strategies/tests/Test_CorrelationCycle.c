#include <default.c>

// No dependencies - CorrelationCycle is self-contained (no IIR state,
// full window recomputation each bar).
#include "../../indicators/ehlers/CorrelationCycle.c"

#define CC_PERIOD 20   // Ehlers' stated default

void run()
{
    StartDate = 20200101;
    EndDate   = 20241231;
    BarPeriod = 240;
    asset("BTC/USD");

    static int barCount = 0;
    barCount++;

    vars Price = series(priceClose());

    // Compute BEFORE the lookback guard.
    var ccReal, ccImag, ccAngleRaw, ccAngle, ccState;
    CorrelationCycle(Price, CC_PERIOD,
                     &ccReal, &ccImag, &ccAngleRaw, &ccAngle, &ccState);

    if(is(LOOKBACK)) return;

    static int hdrWritten = 0;
    if(!hdrWritten) {
        file_append("Data/CorrCycle_BTCUSD_H4.csv",
            "barIndex,Price,Real,Imag,AngleRaw,Angle,State\n", 0);
        hdrWritten = 1;
    }

    file_append("Data/CorrCycle_BTCUSD_H4.csv",
        strf("%d,%.6f,%.8f,%.8f,%.6f,%.6f,%.0f\n",
             barCount, Price[0], ccReal, ccImag, ccAngleRaw, ccAngle, ccState), 0);
}