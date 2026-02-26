//////////////////////////////////////////////////////////////
// InstantTrendline_Test.c
// Test adaptive InstantTrendline with DominantCycle
// Compares InstantTrendline vs EMA vs SmoothPrice
// Exports results to CSV for Python/Jupyter validation
//////////////////////////////////////////////////////////////

#include <default.c>

#include "../../indicators/ehlers/DominantCycle.c"
#include "../../indicators/ehlers/InstantTrendline.c"

// Output file path — relative to Zorro's working directory
// This lands in: fx-trading-systems/data/fx/
#define CSV_PATH "C:/Users/eyalp/Documents/fx-trading-systems/data/fx/EUR_USD_ITrend_export.csv"

function run()
{
    BarPeriod = 1440;  // Daily bars
    LookBack = 100;
    StartDate = 20150101;  // Export from 2015 onwards
    EndDate   = 20240101;

    asset("EUR/USD");

    vars Price = series(priceClose());

    // Get adaptive InstantTrendline (includes DominantCycle internally)
    var ITrend = InstantTrendline(Price);

    // Get SmoothPrice for crossover signals
    var SPrice = SmoothPrice(Price);

    // Standard EMA for comparison
    var ema20 = EMA(Price, 20);

    // --- CSV Export ---
    // Write header on the very first bar
    // Bar == 1 is the first bar Zorro processes after LookBack warmup
    if(Bar == 1) {
        file_delete(CSV_PATH);
        file_append(CSV_PATH, "Date,Close,ITrend,SmoothPrice,EMA20\n");
    }

    // Write one row per bar
    // strdate() converts Zorro's internal bar timestamp to YYYY.MM.DD string
    string row = strf("%s,%.5f,%.5f,%.5f,%.5f\n",
                      strdate("%Y.%m.%d", 0),
                      Price[0],
                      ITrend,
                      SPrice,
                      ema20);
    file_append(CSV_PATH, row);

    // --- Debug output every 50 bars (unchanged) ---
    if(Bar % 50 == 0) {
        printf("\n[Bar %d] Price=%.5f ITrend=%.5f SPrice=%.5f EMA20=%.5f",
               Bar, Price[0], ITrend, SPrice, ema20);
    }

    // --- Plot everything (unchanged) ---
    plot("Price",       Price[0], LINE, BLACK);
    plot("ITrend",      ITrend,   LINE, BLUE);
    plot("SmoothPrice", SPrice,   LINE, RED);
    plot("EMA20",       ema20,    LINE, GREEN);
}