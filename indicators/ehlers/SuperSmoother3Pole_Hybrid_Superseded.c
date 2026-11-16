// SuperSmoother3Pole_Hybrid_Superseded.c
// SUPERSEDED 2026-11-15. Kept as the record of a copying error and as negative control NCH
// (analysis/harness/specs/SS3_ArticleFidelity.toml). Do NOT use in strategies.
//
// (b) This was indicators/ehlers/SuperSmoother3Pole.c up to main 5821335. It cited Ehlers,
//     Cybernetic Analysis (2004) + TASC V.7:3 "Moving averages and smoothing filters", but matches neither:
//       - real pole a1 = exp(-pi/P); both sources use a1*a1 = exp(-2*pi/P)
//       - input c0*(Price[0]+Price[1]) (2-pole SuperSmoother style); book Fig. 13.11 uses coef1*Price,
//         TASC V.7:3 a (1,3,3,1)/8 Butterworth numerator
// (b) Effect at P = 20 vs book Fig. 13.11: gain error up to 0.269, ramp lag 8.59 vs 4.92 bars.
// Only change from the original: function renamed (was SuperSmoother3Pole), original header replaced.
// Original header text is in git history.

var SuperSmoother3Pole_Hybrid_Superseded(vars Price, int Period) {
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