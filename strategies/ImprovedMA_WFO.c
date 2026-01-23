function run()
{
    BarPeriod = 1440;      
    LookBack = 100;
    StartDate = 20220101;  // ← OUT-OF-SAMPLE PERIOD!
    EndDate = 20241231;
    
    Risk = 2;
    Stop = 2 * ATR(20);
    asset("EUR/USD");
    
    // USE THE "OPTIMAL" PARAMETERS FROM TRAINING
    int FastPeriod = 20;  // ← Winner from training
    int SlowPeriod = 50;  // ← Winner from training
    
    vars Price = series(priceClose());
    vars FastMA = series(SMA(Price, FastPeriod));
    vars SlowMA = series(SMA(Price, SlowPeriod));
    
    if(crossOver(FastMA, SlowMA))
        enterLong();
    
    if(crossUnder(FastMA, SlowMA))
        exitLong();
}