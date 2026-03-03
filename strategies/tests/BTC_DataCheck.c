#include <default.c>

function run()
{
    BarPeriod = 240;  // H4 bars
    LookBack  = 10;
    StartDate = 20200101;
    EndDate   = 20240101;

    asset("BTCUSD");

    if(Bar % 100 == 0)
        printf("\n[Bar %d] Date=%s Close=%.2f",
               Bar, strdate("%Y.%m.%d", 0), priceClose());
}