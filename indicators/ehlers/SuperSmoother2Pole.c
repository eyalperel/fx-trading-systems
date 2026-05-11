var SuperSmoother2Pole(vars Price, int Period) {
    // --- Coefficients (Butterworth 2-pole design) ---
    var c1 = exp(-sqrt(2.0) * PI / Period);
    var b1 = 2.0 * c1 * cos(sqrt(2.0) * PI / Period);
    var c2 = b1;
    var c3 = -c1 * c1;
    var c0 = (1.0 - b1 + c1 * c1) / 2.0;

    // --- Filter state ---
    // Initialize to current price so feedback terms start at price level
    var* Filt = series(Price[0], 3);

    // --- First bar: all history is init value, output = price ---
    if(Init) {
        Filt[0] = Price[0];
        return Filt[0];
    }

    // --- Output equation ---
    Filt[0] = c0 * (Price[0] + Price[1])
            + c2 * Filt[1]
            + c3 * Filt[2];

    return Filt[0];
}