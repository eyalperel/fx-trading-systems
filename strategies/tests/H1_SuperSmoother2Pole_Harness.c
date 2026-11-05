// H1_SuperSmoother2Pole_Harness.c
//
// PURPOSE:  Batch harness H1. Feeds synthetic inputs through SuperSmoother2Pole
//           (4 periods + 2 negative controls) and writes the RAW outputs. It does NOT judge
//           anything. Python (analysis/harness/h1_check.py) measures and writes PASS/FAIL.
// PREREG:   docs/preregistration/H1_SuperSmoother2Pole_Criteria.md (incl. Amendment 1).
// INPUTS:   Synthetic only, from the bar counter n (criteria S2):
//             flat 1.1 | 1.1+0.01*sin(2*PI*n/T), T=5,10,20,40,100 | ramp 1.1+0.0001*n
//           EUR/USD D1 is used only as a bar clock. clock_close is exported so Python can
//           check by magnitude that the clock really is EUR/USD (gotchas 9b.3).
// OUTPUT:   C:/Zorro/Data/H1_SS2P_raw.csv  (3000 rows n=0..2999 + header; 50 columns;
//           values printed with 15 decimals - %f's 6 decimals cannot resolve the 1e-9 / 1e-4 tolerances)
// VARIANTS: 6 x 7 inputs = 42 filter calls per bar: P=10,14,20,30 | NC1 = P 21 |
//           NC2 = local copy with the cos argument in degrees (h1_ss_deg, below).
//           Call order is fixed and unconditional (gotchas 3.1).
// FEEDING:  (b by design, verified by Python) every x[n], n=0..2999, reaches the filters
//           exactly once. The INITRUN and EXITRUN calls feed NOTHING and write NOTHING:
//           they return before any series() call. The first bar after INITRUN is n=0.
// NO LOOKBACK GUARD: LookBack = 0 and there is no is(LOOKBACK) return, because warmup
//           bars (n<500) must be exported too. If Zorro still runs lookback bars, they are
//           fed and written like any other; Python requires n = 0..2999 contiguous.
// SOURCES:  (a) Criteria file for inputs/tolerances. (c) series() seeding in Zorro is
//           unverified here; observations O1-O3 in the checker report it.
// Generated layout; edit with care: Y[] index = variant*7 + input.

#include <default.c>
#include "../../indicators/ehlers/SuperSmoother2Pole.c"

#define H1_RAW "Data/H1_SS2P_raw.csv"
#define H1_NBARS 3000

static int h1_n = 0;
static int h1_done = 0;
static int h1_hdr = 0;
static int h1_rows = 0;

// NC2: negative control. Identical to SuperSmoother2Pole.c except the cos argument is
// in degrees (sqrt(2)*180/P instead of sqrt(2)*PI/P). Defined here only.
var h1_ss_deg(vars Price, int P)
{
	var c1 = exp(-sqrt(2.0) * PI / P);
	var b1 = 2.0 * c1 * cos(sqrt(2.0) * 180.0 / P);
	var c2 = b1;
	var c3 = -c1 * c1;
	var c0 = (1.0 - b1 + c1 * c1) / 2.0;
	var* Filt = series(Price[0], 3);
	if(Init) {
		Filt[0] = Price[0];
		return Filt[0];
	}
	Filt[0] = c0 * (Price[0] + Price[1]) + c2 * Filt[1] + c3 * Filt[2];
	return Filt[0];
}

void run()
{
	// Settings must be assigned on every call, including INITRUN, or Zorro never sees them.
	BarPeriod = 1440;
	StartDate = 20080101;	// history check: see run card (>= 3000 D1 bars needed)
	EndDate   = 20240101;
	LookBack  = 0;
	asset("EUR/USD");

	if(is(INITRUN)) {
		h1_n = 0; h1_done = 0; h1_hdr = 0; h1_rows = 0;	// declared initialisers
		file_delete(H1_RAW);
		return;
	}
	if(is(EXITRUN)) {
		printf("\nH1 EXIT: rows written = %d, done = %d  (expected 3000 and 1)", h1_rows, h1_done);
		return;
	}

	int n;
	var X[7];
	var Y[42];
	n = h1_n;

	// --- inputs from the bar counter (radians) ---
	X[0] = 1.1;
	X[1] = 1.1 + 0.01 * sin(2.0 * PI * n / 5.0);
	X[2] = 1.1 + 0.01 * sin(2.0 * PI * n / 10.0);
	X[3] = 1.1 + 0.01 * sin(2.0 * PI * n / 20.0);
	X[4] = 1.1 + 0.01 * sin(2.0 * PI * n / 40.0);
	X[5] = 1.1 + 0.01 * sin(2.0 * PI * n / 100.0);
	X[6] = 1.1 + 0.0001 * n;

	// --- input series: 7 unconditional calls, fixed order ---
	vars S0 = series(X[0], 3);
	vars S1 = series(X[1], 3);
	vars S2 = series(X[2], 3);
	vars S3 = series(X[3], 3);
	vars S4 = series(X[4], 3);
	vars S5 = series(X[5], 3);
	vars S6 = series(X[6], 3);

	// --- 42 filter calls, variant-major, unconditional, fixed order ---
	Y[0] = SuperSmoother2Pole(S0, 10);	// P10 flat
	Y[1] = SuperSmoother2Pole(S1, 10);	// P10 s5
	Y[2] = SuperSmoother2Pole(S2, 10);	// P10 s10
	Y[3] = SuperSmoother2Pole(S3, 10);	// P10 s20
	Y[4] = SuperSmoother2Pole(S4, 10);	// P10 s40
	Y[5] = SuperSmoother2Pole(S5, 10);	// P10 s100
	Y[6] = SuperSmoother2Pole(S6, 10);	// P10 ramp
	Y[7] = SuperSmoother2Pole(S0, 14);	// P14 flat
	Y[8] = SuperSmoother2Pole(S1, 14);	// P14 s5
	Y[9] = SuperSmoother2Pole(S2, 14);	// P14 s10
	Y[10] = SuperSmoother2Pole(S3, 14);	// P14 s20
	Y[11] = SuperSmoother2Pole(S4, 14);	// P14 s40
	Y[12] = SuperSmoother2Pole(S5, 14);	// P14 s100
	Y[13] = SuperSmoother2Pole(S6, 14);	// P14 ramp
	Y[14] = SuperSmoother2Pole(S0, 20);	// P20 flat
	Y[15] = SuperSmoother2Pole(S1, 20);	// P20 s5
	Y[16] = SuperSmoother2Pole(S2, 20);	// P20 s10
	Y[17] = SuperSmoother2Pole(S3, 20);	// P20 s20
	Y[18] = SuperSmoother2Pole(S4, 20);	// P20 s40
	Y[19] = SuperSmoother2Pole(S5, 20);	// P20 s100
	Y[20] = SuperSmoother2Pole(S6, 20);	// P20 ramp
	Y[21] = SuperSmoother2Pole(S0, 30);	// P30 flat
	Y[22] = SuperSmoother2Pole(S1, 30);	// P30 s5
	Y[23] = SuperSmoother2Pole(S2, 30);	// P30 s10
	Y[24] = SuperSmoother2Pole(S3, 30);	// P30 s20
	Y[25] = SuperSmoother2Pole(S4, 30);	// P30 s40
	Y[26] = SuperSmoother2Pole(S5, 30);	// P30 s100
	Y[27] = SuperSmoother2Pole(S6, 30);	// P30 ramp
	Y[28] = SuperSmoother2Pole(S0, 21);	// NC1 flat
	Y[29] = SuperSmoother2Pole(S1, 21);	// NC1 s5
	Y[30] = SuperSmoother2Pole(S2, 21);	// NC1 s10
	Y[31] = SuperSmoother2Pole(S3, 21);	// NC1 s20
	Y[32] = SuperSmoother2Pole(S4, 21);	// NC1 s40
	Y[33] = SuperSmoother2Pole(S5, 21);	// NC1 s100
	Y[34] = SuperSmoother2Pole(S6, 21);	// NC1 ramp
	Y[35] = h1_ss_deg(S0, 20);	// NC2 flat
	Y[36] = h1_ss_deg(S1, 20);	// NC2 s5
	Y[37] = h1_ss_deg(S2, 20);	// NC2 s10
	Y[38] = h1_ss_deg(S3, 20);	// NC2 s20
	Y[39] = h1_ss_deg(S4, 20);	// NC2 s40
	Y[40] = h1_ss_deg(S5, 20);	// NC2 s100
	Y[41] = h1_ss_deg(S6, 20);	// NC2 ramp

	// --- write one row per fed bar ---
	if(!h1_done) {
		if(!h1_hdr) {
		file_append(H1_RAW, "n,clock_close,x_flat,x_s5,x_s10,x_s20,x_s40,x_s100,x_ramp", 0);
		file_append(H1_RAW, ",y_P10_flat,y_P10_s5,y_P10_s10,y_P10_s20,y_P10_s40,y_P10_s100,y_P10_ramp", 0);
		file_append(H1_RAW, ",y_P14_flat,y_P14_s5,y_P14_s10,y_P14_s20,y_P14_s40,y_P14_s100,y_P14_ramp", 0);
		file_append(H1_RAW, ",y_P20_flat,y_P20_s5,y_P20_s10,y_P20_s20,y_P20_s40,y_P20_s100,y_P20_ramp", 0);
		file_append(H1_RAW, ",y_P30_flat,y_P30_s5,y_P30_s10,y_P30_s20,y_P30_s40,y_P30_s100,y_P30_ramp", 0);
		file_append(H1_RAW, ",y_NC1_flat,y_NC1_s5,y_NC1_s10,y_NC1_s20,y_NC1_s40,y_NC1_s100,y_NC1_ramp", 0);
		file_append(H1_RAW, ",y_NC2_flat,y_NC2_s5,y_NC2_s10,y_NC2_s20,y_NC2_s40,y_NC2_s100,y_NC2_ramp", 0);
		file_append(H1_RAW, "\n", 0);
			h1_hdr = 1;
		}
		file_append(H1_RAW, strf("%d,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f",
			n, priceClose(), X[0], X[1], X[2], X[3], X[4], X[5], X[6]), 0);
		file_append(H1_RAW, strf(",%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f", Y[0],Y[1],Y[2],Y[3],Y[4],Y[5],Y[6]), 0);
		file_append(H1_RAW, strf(",%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f", Y[7],Y[8],Y[9],Y[10],Y[11],Y[12],Y[13]), 0);
		file_append(H1_RAW, strf(",%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f", Y[14],Y[15],Y[16],Y[17],Y[18],Y[19],Y[20]), 0);
		file_append(H1_RAW, strf(",%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f", Y[21],Y[22],Y[23],Y[24],Y[25],Y[26],Y[27]), 0);
		file_append(H1_RAW, strf(",%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f", Y[28],Y[29],Y[30],Y[31],Y[32],Y[33],Y[34]), 0);
		file_append(H1_RAW, strf(",%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f", Y[35],Y[36],Y[37],Y[38],Y[39],Y[40],Y[41]), 0);
		file_append(H1_RAW, "\n", 0);
		h1_rows += 1;
		if(n == H1_NBARS - 1) {
			h1_done = 1;	// latch first; nothing is written after this row
			quit("H1 batch complete: 3000 rows written");
		} else {
			h1_n += 1;
		}
	}
}
