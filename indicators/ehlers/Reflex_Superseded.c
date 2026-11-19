// SUPERSEDED -- do not use. Kept as the negative control NCS / NCT
// of RFX_ArticleFidelity (R-1 shared static MS, R-2 int half length,
// R-3 float32 weights). Corrected file: Reflex.c.
// Body = the Reflex.c of blob 7c6b235c00f053faef6f70dff71d9e09b99c440d
// verbatim; only the function name and rx_ -> rxo_ (flat namespace,
// gotchas 1.3) changed.
var Reflex_Superseded(vars Price, int Length) {
    int rxo_HalfLength = Length / 2;

    // Gentle SuperSmooth — half the cycle length, deliberately light smoothing
    var* rxo_Filt = series(SuperSmoother2Pole(Price, rxo_HalfLength), Length + 2);

    // Slope of the notional trend line spanning the full Length window
    var rxo_Slope = (rxo_Filt[Length] - rxo_Filt[0]) / Length;

    // Sum deviations of Filt from the trend line, across the window
    var rxo_Sum = 0;
    int rxo_i;
    for (rxo_i = 1; rxo_i <= Length; rxo_i++)
        rxo_Sum += (rxo_Filt[0] + rxo_i * rxo_Slope) - rxo_Filt[rxo_i];
    rxo_Sum = rxo_Sum / Length;

    // Normalize by running mean-square (0.04/0.96 EMA), then sqrt
    static var rxo_MS = 0;
    if(is(INITRUN)) rxo_MS = 0;   // statics persist across runs
    rxo_MS = 0.04 * rxo_Sum * rxo_Sum + 0.96 * rxo_MS;

    var rxo_Reflex = 0;
    if (rxo_MS > 0)
        rxo_Reflex = rxo_Sum / sqrt(rxo_MS);

    return rxo_Reflex;
}