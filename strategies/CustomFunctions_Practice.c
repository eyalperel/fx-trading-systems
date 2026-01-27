// Custom Functions Practice
// Week 3 Day 2 - Exercise 1


int isTrending(int adxPeriod, var adxThreshold)
{
    return ADX(adxPeriod) > adxThreshold;
}



// Test function - DO NOT MODIFY
function run()
{
    BarPeriod = 1440;
    LookBack = 100;
    StartDate = 20200101;
    EndDate = 20241231;
    
    asset("EUR/USD");
    
    // Test your function
    if(isTrending(14, 25.0)) {
        printf("\nBar %d: Market is TRENDING (ADX > 25)", Bar);
    } else {
        printf("\nBar %d: Market is RANGING (ADX <= 25)", Bar);
    }
}