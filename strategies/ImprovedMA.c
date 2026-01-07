// Improved MA Strategy with Trend Filter
// Now only trades in trending markets!

function run()
{
    // Basic setup
    BarPeriod = 1440;      
    LookBack = 100;        
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
    
    // NEW: Trend filter - only trade when ADX > 25
    var TrendStrength = ADX(14);
    
    // Entry: MA crossover AND strong trend
    if(crossOver(FastMA, SlowMA) && TrendStrength > 25)
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
    plot("ADX", TrendStrength, LINE, GREEN);
}