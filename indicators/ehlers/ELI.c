// /zorro/indicators/ehlers/ELI.c
// Based on: Ehlers, "Moving Averages Part 2: Ehlers Leading Indicator (ELI)"
//           S&C V.6:7 (1988)
// Purpose: EMA-cascade leading indicator. Only meaningful when a genuine
//          dominant cycle is present in the data (Ehlers' own caveat).
// Upgrade vs 1988 original: DC (dominant cycle length) is measured live via
//          DominantCycle.c (Week 4), not typed in by hand as a fixed guess.
// Inputs:  Price series
// Output:  ELI value (unbounded, roughly price-scale — no normalization,
//          unlike Reflex or MESA Stochastic)

var ELI(vars Price) {
    var eli_DC = DominantCycle(Price);

    // EMA1: alpha = 4/DC  (length = DC/2, "long" EMA)
    // EMA2: alpha = 2x EMA1's alpha = 8/DC  (length = DC/4, "short" EMA)
    var eli_Alpha1 = 4.0 / eli_DC;
    var eli_Alpha2 = 2.0 * eli_Alpha1;

    var* eli_EMA1 = series(Price[0], 2);
    var* eli_EMA2 = series(Price[0], 2);
    eli_EMA1[0] = eli_Alpha1 * Price[0] + (1.0 - eli_Alpha1) * eli_EMA1[1];
    eli_EMA2[0] = eli_Alpha2 * Price[0] + (1.0 - eli_Alpha2) * eli_EMA2[1];

    // Synthetic price = difference of the two EMAs (detrends, isolates cycle)
    var eli_Synthetic = eli_EMA1[0] - eli_EMA2[0];

    // EMA3: EMA of the synthetic price itself, same alpha as EMA2
    var* eli_EMA3 = series(eli_Synthetic, 2);
    eli_EMA3[0] = eli_Alpha2 * eli_Synthetic + (1.0 - eli_Alpha2) * eli_EMA3[1];

    // ELI = synthetic price minus its own (more-lagged) EMA
    var eli_Result = eli_Synthetic - eli_EMA3[0];
    return eli_Result;
}