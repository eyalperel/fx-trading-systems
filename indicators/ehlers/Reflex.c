var Reflex(vars Price, int Length) {
    int rx_HalfLength = Length / 2;

    // Gentle SuperSmooth — half the cycle length, deliberately light smoothing
    var* rx_Filt = series(SuperSmoother2Pole(Price, rx_HalfLength), Length + 2);

    // Slope of the notional trend line spanning the full Length window
    var rx_Slope = (rx_Filt[Length] - rx_Filt[0]) / Length;

    // Sum deviations of Filt from the trend line, across the window
    var rx_Sum = 0;
    int rx_i;
    for (rx_i = 1; rx_i <= Length; rx_i++)
        rx_Sum += (rx_Filt[0] + rx_i * rx_Slope) - rx_Filt[rx_i];
    rx_Sum = rx_Sum / Length;

    // Normalize by running mean-square (0.04/0.96 EMA), then sqrt
    static var rx_MS = 0;
    rx_MS = 0.04 * rx_Sum * rx_Sum + 0.96 * rx_MS;

    var rx_Reflex = 0;
    if (rx_MS > 0)
        rx_Reflex = rx_Sum / sqrt(rx_MS);

    return rx_Reflex;
}