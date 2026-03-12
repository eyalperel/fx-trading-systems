///////////////////////////////////////////////////////
// Super Smoother Test Script
// Tests the two-pole Butterworth filter implementation
///////////////////////////////////////////////////////

#include <profile.c>
#include "../../indicators/ehlers/SuperSmoother.c"

function run()
{
    BarPeriod = 1440;
    LookBack  = 100;
    StartDate = 2021;
    EndDate   = 2022;

    Verbose = 2;
    set(LOGFILE);

    Asset = "EUR/USD";

    vars Price = series(priceClose());

    // Call once per bar (NO series() wrapper!)
    var SS10  = SuperSmoother(Price, 10);
    var EMA10 = EMA(Price, 10);

    plot("SuperSmoother(10)", SS10,  LINE, BLUE);
    plot("EMA(10)",           EMA10, LINE, RED);
    plot("Price",             Price[0], LINE, BLACK);

    if(Bar % 50 == 0)
        printf("\n[Bar %d] Price=%.5f SS10=%.5f EMA10=%.5f",
            Bar, Price[0], SS10, EMA10);
}




