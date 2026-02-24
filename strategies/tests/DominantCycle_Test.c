//////////////////////////////////////////////////////////////
// DominantCycle_Test.c
// Test script to visualize how the dominant cycle changes over time
//////////////////////////////////////////////////////////////

#include <default.c>
#include "../../indicators/ehlers/DominantCycle.c"

function run()
{
    BarPeriod = 1440;  // Daily bars
    LookBack = 100;
    
    asset("EUR/USD");
    
    vars Price = series(priceClose());
    var dc = DominantCycle(Price);
    
    // Debug output every 50 bars
    if(Bar % 50 == 0) {
        printf("\n[Bar %d] Price=%.5f  DominantCycle=%.1f", Bar, Price[0], dc);
    }
    
    // Plot the measured dominant cycle
    plot("DC", dc, LINE, BLUE);
    plot("FixedDC20", 20, DOT, RED);
    plot("LowerBound", 18, DOT, GREEN);
    plot("UpperBound", 40, DOT, GREEN);
}