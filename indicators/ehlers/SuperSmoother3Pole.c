// SuperSmoother3Pole.c
// Source (a): Ehlers, Cybernetic Analysis for Stocks and Futures (Wiley 2004), ch. 13,
//             Fig. 13.11 "Three-Pole Super Smoother" (EasyLanguage); coefficients in Table 13.4.
// Pre-registered: analysis/harness/specs/SS3_ArticleFidelity.toml [corrected_code] (867f952).
//             The code lines below must equal that block; change both only via a spec amendment.
// Purpose:    3-pole low-pass smoother: Butterworth 3-pole poles, numerator replaced by one
//             constant coef1 that gives unity gain at zero frequency (book p. 205, paraphrase).
// Inputs:     Price  - vars pointer to the price series
//             Period - critical (cutoff) period in bars
// Output:     smoothed price
// Notes:
//  (a) The book prints Cosine(1.738*180/Period) (degrees). Here sqrt(3) is used, per
//      HARNESS_DESIGN D1 Amendment 1 (rule 4, 9789fb5): Table 13.4 is reproduced by 1.732
//      (<= 4.4e-6) and rejects 1.738 (>= 1.2e-4).
//  (a) cos() takes radians: Cosine(x*180/P) degrees = cos(x*PI/P).
//  (b) PI is Zorro's macro (3.14159, float32), kept per HARNESS_DESIGN D3.
//  (b) Pole layout: complex pair radius a1 = exp(-PI/P), angle sqrt(3)*PI/P; real pole c1 = a1*a1.
//  (b) Passband overshoot: gain up to 1.0046 at P = 10, T = 20 (spec O_PEAK); not 2-pole-flat.
//  (b) Seeding: Filt = Price on the INITRUN call only; the book seeds Filt3 = Price for
//      CurrentBar < 4. Start-up transient only (< 1e-9 after ~200 bars at P = 30); not verified.
//  Superseded version (hybrid, wrong real pole and input): SuperSmoother3Pole_Hybrid_Superseded.c

var SuperSmoother3Pole(vars Price, int Period)
{
	var a1 = exp(-PI / Period);
	var b1 = 2.0 * a1 * cos(sqrt(3.0) * PI / Period);
	var c1 = a1 * a1;
	var coef2 = b1 + c1;
	var coef3 = -(c1 + b1 * c1);
	var coef4 = c1 * c1;
	var coef1 = 1.0 - coef2 - coef3 - coef4;
	var* Filt = series(Price[0], 4);
	if(Init) {
		Filt[0] = Price[0];
		return Filt[0];
	}
	Filt[0] = coef1 * Price[0] + coef2 * Filt[1] + coef3 * Filt[2] + coef4 * Filt[3];
	return Filt[0];
}
