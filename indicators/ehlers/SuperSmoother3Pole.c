// SuperSmoother3Pole.c
// Based on: Ehlers, "Cybernetic Analysis for Stocks and Futures"
//           + TASC "Moving Averages and Smoothing Filters"
// Purpose:  Low-lag smoothing filter — 3-pole Butterworth IIR design
//           More smoothing than 2-pole at cost of slightly more lag
// Inputs:   Price — vars pointer to price series (e.g. closing prices)
//           Period — cutoff period in bars (recommended: FX 14-20, Crypto 8-14)
// Output:   Smoothed price value
// Notes:    Needs ~2x Period bars warmup before output is reliable
//           cos() uses radians — standard C math library
//           3-pole combines one real pole (a1) + one complex conjugate pair (b1)

var SuperSmoother3Pole(vars Price, int Period) {
    // --- Coefficients (Butterworth 3-pole design) ---
    var a1 = exp(-PI / Period);
    var b1 = 2.0 * a1 * cos(sqrt(3.0) * PI / Period);

    // Three feedback coefficients derived from pole combination
    var c1 = b1 + a1;           // SS[1]: complex pair + real pole
    var c2 = -(b1 * a1 + a1 * a1); // SS[2]: cross terms
    var c3 = a1 * a1 * a1;      // SS[3]: real pole cubed

    // Input gain — ensures unity DC gain
    var c0 = (1.0 - c1 - c2 - c3) / 2.0;

    // --- Filter state: needs 4 elements (current + 3 feedback bars) ---
    var* Filt = series(Price[0], 4);

    // --- During warmup: return price directly ---
    if(Init) {
        Filt[0] = Price[0];
        return Filt[0];
    }

    // --- Output equation ---
    Filt[0] = c0 * (Price[0] + Price[1])
            + c1 * Filt[1]
            + c2 * Filt[2]
            + c3 * Filt[3];

    return Filt[0];
}