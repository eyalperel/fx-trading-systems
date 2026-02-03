// TrendFilterMA - Simple trend filter strategy
// Only trade when price above 200 SMA

function run()
{
    // Basic setup
    BarPeriod = 1440;      
    LookBack = 250;        // Need 250 bars for SMA(200)
    StartDate = 20200101;  
    EndDate = 20241231;    
    
    // Risk management
    Risk = 2;
    Stop = 2 * ATR(20);
    
    asset("EUR/USD");
    
    // Calculate indicators
    vars Price = series(priceClose());
    vars FastMA = series(SMA(Price, 20));
    vars SlowMA = series(SMA(Price, 50));
    
    // Trend filter - only trade when above 200 SMA
    var TrendFilter = SMA(Price, 200);
    
    // Entry: MA crossover AND price above trend
    if(crossOver(FastMA, SlowMA) && priceClose() > TrendFilter)
    {
        enterLong();
    }
    
    // Exit: MA crossunder
    if(crossUnder(FastMA, SlowMA))
    {
        exitLong();
    }
    
    // Plot
    plot("FastMA", FastMA[0], LINE, BLUE);
    plot("SlowMA", SlowMA[0], LINE, RED);
    plot("Trend200", TrendFilter, LINE, GREEN);
}