// Multi-Timeframe Practice
// Week 3 Day 2 - Exercise 2

function run()
{
    BarPeriod = 1440;  // Daily bars
    LookBack = 100;
    StartDate = 20200101;
    EndDate = 20241231;

    asset("EUR/USD");

    // Create daily price series (main timeframe)
    vars PriceDaily = series(priceClose());

     // Create weekly price series
    TimeFrame = 7;  // 7 days = 1 week (since BarPeriod is daily)
    vars PriceWeekly = series(priceClose());
    TimeFrame = 1;  // Reset to daily

     // Compare current daily close to current weekly close
    if(PriceDaily[0] > PriceWeekly[0]) {
        printf("\nBar %d: Daily close (%.5f) ABOVE weekly close (%.5f)", 
               Bar, PriceDaily[0], PriceWeekly[0]);
    } else {
        printf("\nBar %d: Daily close (%.5f) BELOW weekly close (%.5f)", 
               Bar, PriceDaily[0], PriceWeekly[0]);
    }

}