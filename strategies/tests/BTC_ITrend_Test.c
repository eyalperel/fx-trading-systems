//////////////////////////////////////////////////////////////
// BTC_ITrend_Test.c
// Day 5: InstantTrendline Fixed vs Adaptive on BTC/USD H4
// Cross-asset comparison with EUR/USD D1 results from Day 4
//
// Output columns: Date,Close,ITrend_Adaptive,ITrend_Fixed,SmoothPrice,EMA20
//////////////////////////////////////////////////////////////

#include <default.c>

#include "../../indicators/ehlers/DominantCycle.c"
#include "../../indicators/ehlers/InstantTrendline.c"

#define CSV_PATH "C:/Users/eyalp/Documents/fx-trading-systems/data/crypto/BTC_USD_ITrend_FixedVsAdaptive.csv"

var InstantTrendlineFixed(vars Data, int FixedPeriod)
{
    var DC = (var)FixedPeriod;

    vars FFilt1  = series(0);
    vars FValue2 = series(0);
    vars FITrend = series(0);

    if(Bar >= 3) {
        FFilt1[0] = 0.0542*Data[0] + 0.021*Data[1] + 0.021*Data[2] + 0.0542*Data[3]
                   + 1.9733*FFilt1[1] - 1.6067*FFilt1[2] + 0.4831*FFilt1[3];
    }

    var alpha10 = 0.6;
    var Angle10 = 360.0 / 10.0 * PI / 180.0;
    if(Bar >= 2) {
        FValue2[0] = 0.8 * (FFilt1[0] - 2*cos(Angle10)*FFilt1[1] + FFilt1[2])
                    + 1.6 * cos(Angle10) * FValue2[1] - 0.6 * FValue2[2];
    }

    var alpha;
    if(DC <= 20)
        alpha = 0.8;
    else if(DC >= 40)
        alpha = 0.9;
    else
        alpha = 0.8 + 0.1 * (DC - 20.0) / 20.0;

    var AngleDC = 360.0 / DC * PI / 180.0;
    var scale = (1.0 + alpha) / 2.0;
    if(Bar >= 2) {
        FITrend[0] = scale * (FValue2[0] - 2*cos(AngleDC)*FValue2[1] + FValue2[2])
                    + (1.0 + alpha) * cos(AngleDC) * FITrend[1]
                    - alpha * FITrend[2];
    }

    return FITrend[0];
}

function run()
{
    BarPeriod = 240;   // H4 bars
    LookBack  = 100;
    StartDate = 20200101;
    EndDate   = 20240101;

    asset("BTCUSD");

    vars Price = series(priceClose());

    var ITrend_Adaptive = InstantTrendline(Price);
    var ITrend_Fixed    = InstantTrendlineFixed(Price, 20);
    var SPrice          = SmoothPrice(Price);
    var ema20           = EMA(Price, 20);

    if(Bar == 1) {
        file_delete(CSV_PATH);
        file_append(CSV_PATH, "Date,Close,ITrend_Adaptive,ITrend_Fixed,SmoothPrice,EMA20\n");
    }

    string row = strf("%s,%.2f,%.2f,%.2f,%.2f,%.2f\n",
                      strdate("%Y.%m.%d", 0),
                      Price[0],
                      ITrend_Adaptive,
                      ITrend_Fixed,
                      SPrice,
                      ema20);
    file_append(CSV_PATH, row);

    if(Bar % 200 == 0)
        printf("\n[Bar %d] Date=%s Close=%.2f Adaptive=%.2f Fixed=%.2f",
               Bar, strdate("%Y.%m.%d", 0), Price[0], ITrend_Adaptive, ITrend_Fixed);

    plot("Price",           Price[0],        LINE, BLACK);
    plot("ITrend_Adaptive", ITrend_Adaptive, LINE, BLUE);
    plot("ITrend_Fixed",    ITrend_Fixed,    LINE, RED);
    plot("EMA20",           ema20,           LINE, GREEN);
}