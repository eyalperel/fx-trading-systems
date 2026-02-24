//////////////////////////////////////////////////////////////
// InstantTrendline_Test.c
// Test adaptive InstantTrendline with DominantCycle
// Compares InstantTrendline vs EMA vs SmoothPrice
//////////////////////////////////////////////////////////////

#include <default.c>

#include "../../indicators/ehlers/DominantCycle.c"
#include "../../indicators/ehlers/InstantTrendline.c"

function run()
{
    BarPeriod = 1440;  // Daily bars
    LookBack = 100;
    
    asset("EUR/USD");
    
    vars Price = series(priceClose());
    
    // Get adaptive InstantTrendline (includes DominantCycle internally)
    var ITrend = InstantTrendline(Price);
    
    // Get SmoothPrice for crossover signals
    var SPrice = SmoothPrice(Price);
    
    // Standard EMA for comparison
    var ema20 = EMA(Price, 20);
    
    // Debug output every 50 bars
    if(Bar % 50 == 0) {
        printf("\n[Bar %d] Price=%.5f ITrend=%.5f SPrice=%.5f EMA20=%.5f", 
               Bar, Price[0], ITrend, SPrice, ema20);
    }
    
    // Plot everything
    plot("Price", Price[0], LINE, BLACK);
    plot("ITrend", ITrend, LINE, BLUE);
    plot("SmoothPrice", SPrice, LINE, RED);
    plot("EMA20", ema20, LINE, GREEN);
}