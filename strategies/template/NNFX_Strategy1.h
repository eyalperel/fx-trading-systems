// NNFX_Strategy1.h - slot source for Strategy 1 (decisions R-D2, R-D3; PROJECT_STATE §1.2).
//
//   Baseline FAMA (MAMA's second output), C1 Fisher (Fish vs its one-bar-delayed trigger, T3),
//   C2 Reflex (sign, T3), ATR(14) MT4 for stops and distances. Volume ALWAYS_YES and exit NONE come
//   from the template's modes (T1, T2), not from here. Numbers: NNFX_Strategy1_Config.h.
//
// Use: the script includes, in this order (gotchas 5.2, 5.3: includes in the script, dependency order):
//   <default.c>, NNFX_Config.h, NNFX_Strategy1_Config.h, indicators MAMA.c, FisherTransform.c, Reflex.c,
//   nnfx/ATR.c, this file, NNFX_Slots.h, NNFX_Template.h. In INITRUN it calls nx_config_init(),
//   s1_config_init(), then s1_ind_init().
// Every indicator call runs on every bar with no condition around it (gotchas 3.1): nx_slots_update()
// calls nx_strategy_slots() unconditionally, also during LOOKBACK.
// Each call writes one IND row to s1_IndFile (indicator values for the R1 wiring check, R-D6). This file is
// read before NNFX_Template.h (single pass, gotchas 5.3), so it cannot call nx_log / nx_sgn: it has its own.
// Prefix s1_ (gotchas 1.3).

#define NX_HAVE_STRATEGY_SLOTS

string s1_IndFile = "Data\\NNFX_Strategy1_ind.csv";

int s1_sgn(var s1_x)
{
	if(s1_x > 0) return 1;
	if(s1_x < 0) return -1;
	return 0;
}

// Fresh indicator log (INITRUN).
void s1_ind_init()
{
	file_delete(s1_IndFile);
	file_append(s1_IndFile, "kind,asset,bar,ymd,lookback,open,high,low,close,mama,fama,period,alpha,phase,fish,trig,raw,v1,rng,reflex,sum,ms,atr,tr\n");
}

// Fill the slot globals (nx_s*, NNFX_Slots.h) for asset i on the current bar.
void nx_strategy_slots(int i)
{
	int s1_n = s1_FisherLen + s1_SeriesExtra;
	if(s1_ReflexLen + s1_SeriesExtra > s1_n) s1_n = s1_ReflexLen + s1_SeriesExtra;
	if(nx_AtrLen + s1_SeriesExtra > s1_n) s1_n = nx_AtrLen + s1_SeriesExtra;
	vars s1_mid = series((priceHigh() + priceLow()) * s1_MidWeight, s1_n);   // (H+L)/2: MAMA / Fisher input (a)
	vars s1_cl = series(priceClose(), s1_n);                                  // Reflex input (a); ATR close
	vars s1_hi = series(priceHigh(), s1_n);
	vars s1_lo = series(priceLow(), s1_n);

	var s1_fama = 0; var s1_per = 0; var s1_alpha = 0; var s1_phase = 0;
	var s1_mama = MAMACore(s1_mid, s1_FastLimit, s1_SlowLimit, &s1_fama, &s1_per, &s1_alpha, &s1_phase);
	var s1_raw = 0; var s1_v1 = 0; var s1_rng = 0; var s1_trig = 0;
	var s1_fish = FisherCore(s1_mid, s1_FisherLen, &s1_raw, &s1_v1, &s1_rng, &s1_trig);
	var s1_sum = 0; var s1_ms = 0;
	var s1_rfx = ReflexCore(s1_cl, s1_ReflexLen, &s1_sum, &s1_ms);
	var s1_tr = 0;
	var s1_atr = ATRMT4Core(s1_hi, s1_lo, s1_cl, nx_AtrLen, &s1_tr);

	nx_sBase = s1_fama;
	nx_sC1 = s1_sgn(s1_fish - s1_trig);   // two-lines cross: Fish vs Fish[1] (T3.2)
	nx_sC2 = s1_sgn(s1_rfx);              // zero line (T3.2)
	nx_sAtr = s1_atr;
	nx_sVol = 1;                          // replaced by the volume mode (T2)
	nx_sEx = 0;                           // replaced by the exit mode (T1)

	file_append(s1_IndFile, strf("IND,%s,%i,%i,%i,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f\n",
		Asset, Bar, ymd(ldate(EST, 0)), (int)is(LOOKBACK),
		priceOpen(0), priceHigh(0), priceLow(0), priceClose(0),
		s1_mama, s1_fama, s1_per, s1_alpha, s1_phase,
		s1_fish, s1_trig, s1_raw, s1_v1, s1_rng,
		s1_rfx, s1_sum, s1_ms, s1_atr, s1_tr));
}
