function run()
{
    BarPeriod = 1440;      
    LookBack = 100;        
    StartDate = 20200101;  
    EndDate = 20241231;
    
    Risk = 2;
    Stop = 2 * ATR(20);
    
    asset("GBP/USD");
    
    vars Price = series(priceClose());
    vars FastMA = series(SMA(Price, 20));
    vars SlowMA = series(SMA(Price, 50));
    
    if(crossOver(FastMA, SlowMA))
        enterLong();
    
    if(crossUnder(FastMA, SlowMA))
        exitLong();
}