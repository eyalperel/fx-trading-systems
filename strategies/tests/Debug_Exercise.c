// Debug Exercise - FIXED VERSION
// Week 3 Day 4 - Exercise 5

var BuggyRSI(vars Price, int period)
{
    // Declare static series
    static vars Gains;
    static vars Losses;
    
    // Initialize series ONCE (inside function!)
    if(!Gains) Gains = series(0);
    if(!Losses) Losses = series(0);
    
    // FIX BUG 5: Skip early bars
    if(Bar < period) return 50;
    
    // Calculate gain/loss
    var change = Price[0] - Price[1];
    
    if(change > 0) {
        Gains[0] = change;
        Losses[0] = 0;
    } else {
        Gains[0] = 0;
        Losses[0] = -change;  // FIX BUG 1: Store as positive
    }
    
    // Calculate average gain/loss
    var avgGain = SMA(Gains, period);
    var avgLoss = SMA(Losses, period);
    
    // FIX BUG 4: Declare rs before if statement
    var rs = 0;
    if (avgLoss != 0) {
        rs = avgGain / avgLoss;
    } else {
        rs = 999;  // Very high RS if no losses
    }
    
    // Calculate RSI
    var rsi = 100 - (100 / (1 + rs));
    
    return rsi;
}

function run()
{
    Verbose = 2;
    set(LOGFILE);
    
    BarPeriod = 1440;
    LookBack = 50;  // FIX BUG 3: Increase to 50 for safety
    StartDate = 20240101;
    EndDate = 20240131;
    
    asset("EUR/USD");
    
    vars Price = series(priceClose());
    
    var myRSI = BuggyRSI(Price, 14);
    var zorroRSI = RSI(Price, 14);
    
    printf("\nBar %d: MyRSI=%.2f, ZorroRSI=%.2f", 
           Bar, myRSI, zorroRSI);
    
    if(abs(myRSI - zorroRSI) < 1.0) {
        printf(" ✓");
    } else {
        printf(" ✗ DIFF=%.2f", abs(myRSI - zorroRSI));
    }
}