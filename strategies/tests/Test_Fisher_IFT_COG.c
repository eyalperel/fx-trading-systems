// =============================================================================
// Test_Fisher_IFT_COG.c
// Week 10 — Combined test script: Fisher Transform, Elegant Oscillator, COG
//
// Asset:    EUR/USD D1 (canonical validation pair — set via Zorro GUI)
//           Switch to BTC/USD H4 via GUI for cross-asset validation (Day 5)
// Period:   2015-01-01 to 2024-12-31 (~2596 bars EUR/USD D1)
// Output:   C:/zorro/Data/Fisher_IFT_COG_EURUSD_D1.csv
//
// CSV columns:
//   bar, close, midprice, fisher, fisher_trig, elegant_osc, cog, cog_trig
//
// Validation goals (Day 4-5):
//   Fisher:  do ±2.5 extremes align with price turning points?
//   EO:      near-zero lag confirmed vs price peaks/troughs?
//   COG:     zero-lag claim — verify via cross-correlation in Python
//
// Include order is mandatory:
//   SuperSmoother.c must come before InverseFisher.c
//   (ElegantOscillator calls SuperSmoother2Pole internally)
//
// Standing protocol (Week 9):
//   All indicator calls BEFORE if(is(LOOKBACK)) return;
//   Output gated AFTER the LOOKBACK guard only
// =============================================================================

// --- Includes: dependency order is critical ---
// Adjust paths relative to your Zorro Strategy folder location
#include <default.c>
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/FisherTransform.c"
#include "../../indicators/ehlers/InverseFisher.c"
#include "../../indicators/ehlers/COG.c"

void run() {

    // --- Script configuration ---
    BarPeriod  = 1440;         // D1 — 1440 minutes per bar
    LookBack   = 100;         // generous warmup: covers Fisher(10) + EO RMS(50) + SS(20)
    StartDate  = 20150101;
    EndDate    = 20241231;

    // =========================================================================
    // INDICATOR COMPUTATION — mandatory before LOOKBACK guard
    // All indicators must receive warmup bars to initialize IIR state
    // correctly. Calling them after the guard causes silent cold-start failure.
    // =========================================================================

    // --- Fisher Transform (Period=10) ---
    // Returns current bar Fisher value; ft_Trigger = previous bar (signal line)
    var fisher = FisherTransform(10);
    var f_trig = ft_Trigger;

    // --- Elegant Oscillator (BandEdge=20) ---
    // IFT Redux pipeline: derivative → RMS normalize → soft-limit → SuperSmoother
    var eo = ElegantOscillator(20);

    // --- Center of Gravity (Period=10) ---
    // Returns current bar COG; cog_Trigger = previous bar (signal line)
    var cog    = COG(10);
    var c_trig = cog_Trigger;

    // =========================================================================
    // LOOKBACK GUARD — gate output only, never indicator computation
    // =========================================================================
    if(is(LOOKBACK)) return;

    // --- Bar counter (integer Now unreliable in Zorro — use static counter) ---
    static int barCount = 0;
    barCount++;

    // --- Reference prices ---
    var mid   = (priceHigh() + priceLow()) * 0.5;  // midpoint — Fisher/COG input
    var close = priceClose();                        // close — EO input

    // --- Write header on first bar ---
    if(barCount == 1)
        file_append("Data/Fisher_IFT_COG_EURUSD_D1.csv",
            "bar,close,midprice,fisher,fisher_trig,elegant_osc,cog,cog_trig\n");

    // --- Append data row ---
    file_append("Data/Fisher_IFT_COG_EURUSD_D1.csv",
        strf("%i,%.5f,%.5f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
            barCount,
            close,
            mid,
            fisher, f_trig,
            eo,
            cog,    c_trig));
}