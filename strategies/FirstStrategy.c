// Simple Moving Average Crossover Strategy
// Your first complete trading system!

function run()
{
    // Basic setup
    BarPeriod = 1440;      // Daily bars
    LookBack = 100;        // Need 100 bars for indicators
    StartDate = 20200101;  // Backtest from 2020
    EndDate = 20241231;    // To end of 2024
    
    // Asset to trade
    asset("EUR/USD");
    
    // Calculate two moving averages as SERIES
    vars Price = series(priceClose());
    vars FastMA = series(SMA(Price, 20));  // 20-day MA as series
    vars SlowMA = series(SMA(Price, 50));  // 50-day MA as series
    
    // Trading logic - now using series
    if(crossOver(FastMA, SlowMA))  // Fast crosses above slow = buy
        enterLong();
    
    if(crossUnder(FastMA, SlowMA))  // Fast crosses below slow = exit
        exitLong();
    
    // Plot the moving averages on chart
    plot("FastMA", FastMA[0], LINE, BLUE);
    plot("SlowMA", SlowMA[0], LINE, RED);
}