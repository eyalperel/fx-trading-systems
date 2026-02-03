// Arrays vs Series Practice
// Week 3 Day 3 - Exercise 3

// Method 1: Using series (Zorro way)
var highestHighSeries(int period)
{
    vars High = series(priceHigh());
    
    var highest = High[0];
    
    int i;
    for(i = 1; i < period; i++)
    {
        if(High[i] > highest) {
            highest = High[i];
        }
    }
    
    return highest;
}

// Method 2: Using manual array (for comparison)
var highestHighArray(int period)
{
    static var highs[100];  // Static = persists between bars
    
    // Shift array to make room for new value
    int i;
    for(i = 99; i > 0; i--) {
        highs[i] = highs[i-1];
    }
    
    // Store current high
    highs[0] = priceHigh();
    
    // Find maximum in first 'period' elements
    var highest = highs[0];
    for(i = 1; i < period; i++) {
        if(highs[i] > highest) {
            highest = highs[i];
        }
    }
    
    return highest;
}

// Test function
function run()
{
    Verbose = 2;      // Enable detailed logging
    set(LOGFILE);     // Write to log file
    
    BarPeriod = 1440;
    LookBack = 100;
    StartDate = 20240101;
    EndDate = 20240131;
    
    asset("EUR/USD");
    
    int lookback = 20;
    
    var seriesResult = highestHighSeries(lookback);
    var arrayResult = highestHighArray(lookback);
    
    printf("\nBar %d: Series = %.5f, Array = %.5f", 
           Bar, seriesResult, arrayResult);
    
    if(seriesResult == arrayResult) {
        printf(" ✓ MATCH");
    } else {
        printf(" ✗ DIFF");
    }
}