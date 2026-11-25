// NNFX_Strategy2.h - slot source for Strategy 2 variant 0 (PERF2 slot table; T3 amendment 1; PROJECT_STATE 1.2).
//
//   Baseline FRAMA (N = 32, Price (H+L)/2, High, Low), C1 MESA Stochastic (20, 48, 10) on Close vs SMA(10) of its own
//   output (two-lines cross, T3 amendment 1), C2 Laguerre RSI (gamma 0.5) on Close vs 0.5 (T3.2), ATR(14) MT4.
//   Volume ALWAYS_YES and exit NONE come from the template's modes (T1, T2), not from here. Numbers:
//   NNFX_Strategy2_Config.h.
//
// SMA (PERF2 decision 2a): our own mean of the last s2_C1SmaLen MESA outputs, from an explicit-length series (gotchas
//   9d.10), summed oldest first; C1 state 0 until that many MESA outputs exist (per-instance counter, (c)). Zorro's
//   SMA() is called on the same series every bar for the X1 cross-check only; it never sets a state.
//
// Use: the script includes, in this order (gotchas 5.2, 5.3): <default.c>, NNFX_Config.h, NNFX_Strategy2_Config.h,
//   indicators FRAMA.c, HighPassFilter.c, SuperSmoother2Pole.c, RoofingFilter.c, MESAStochastic.c, LaguerreRSI.c,
//   nnfx/ATR.c, this file, NNFX_Slots.h, NNFX_Template.h. In INITRUN: nx_config_init(), s2_config_init(), s2_ind_init().
// Every indicator call runs on every bar with no condition around it (gotchas 3.1). Each call writes one IND row to
//   s2_IndFile (values for the R2 wiring check, PERF2 W1 / X1). Read before NNFX_Template.h (single pass, gotchas 5.3):
//   own sgn, no nx_log. Prefix s2_ (gotchas 1.3).

#define NX_HAVE_STRATEGY_SLOTS

string s2_IndFile = "Data\\NNFX_Strategy2_ind.csv";

int s2_sgn(var s2_x)
{
	if(s2_x > 0) return 1;
	if(s2_x < 0) return -1;
	return 0;
}

// Fresh indicator log (INITRUN).
void s2_ind_init()
{
	file_delete(s2_IndFile);
	file_append(s2_IndFile, "kind,asset,bar,ymd,lookback,open,high,low,close,frama,dim,alpha,mesa,roof,stoc,sma,zsma,nmesa,lrsi,l0,l3,den,atr,tr\n");
}

// Fill the slot globals (nx_s*, NNFX_Config.h) for asset i on the current bar.
void nx_strategy_slots(int i)
{
	int s2_n = s2_FramaN + s2_SeriesExtra;
	if(nx_AtrLen + s2_SeriesExtra > s2_n) s2_n = nx_AtrLen + s2_SeriesExtra;
	if(s2_MesaLen + s2_SeriesExtra > s2_n) s2_n = s2_MesaLen + s2_SeriesExtra;
	vars s2_mid = series((priceHigh() + priceLow()) * s2_MidWeight, s2_n);   // (H+L)/2: FRAMA Price (a)
	vars s2_hi = series(priceHigh(), s2_n);
	vars s2_lo = series(priceLow(), s2_n);
	vars s2_cl = series(priceClose(), s2_n);                                  // MESA, LRSI input (a); ATR close

	var s2_dim = 0; var s2_alpha = 0;
	var s2_frama = FRAMACore(s2_mid, s2_hi, s2_lo, s2_FramaN, &s2_dim, &s2_alpha);
	var s2_roof = 0; var s2_stoc = 0;
	var s2_mesa = MESAStochasticCore(s2_cl, s2_MesaLen, s2_MesaHP, s2_MesaSS, &s2_roof, &s2_stoc);
	var s2_l0 = 0; var s2_l3 = 0; var s2_den = 0;
	var s2_lrsi = LaguerreRSICore(s2_cl, s2_LrsiGamma, &s2_l0, &s2_l3, &s2_den);
	var s2_tr = 0;
	var s2_atr = ATRMT4Core(s2_hi, s2_lo, s2_cl, nx_AtrLen, &s2_tr);

	// C1 second line: SMA of the MESA output (own code; Zorro SMA() for X1 only)
	vars s2_ms = series(s2_mesa, s2_C1SmaLen + s2_SeriesExtra);   // explicit length (gotchas 9d.10)
	vars s2_cnt = series(0, s2_CountLen);                                     // per-instance count of MESA outputs, starts at 0
	s2_cnt[0] = s2_cnt[1] + 1;
	var s2_sma = 0;
	int s2_k;
	for(s2_k = s2_C1SmaLen - 1; s2_k >= 0; s2_k--) s2_sma += s2_ms[s2_k];   // oldest first (model: r2_replay.sma_last)
	s2_sma /= s2_C1SmaLen;
	var s2_zsma = SMA(s2_ms, s2_C1SmaLen);                          // X1 cross-check only

	nx_sBase = s2_frama;
	nx_sC1 = 0;
	if(s2_cnt[0] >= s2_C1SmaLen) nx_sC1 = s2_sgn(s2_mesa - s2_sma);   // two-lines cross (T3 amendment 1)
	nx_sC2 = s2_sgn(s2_lrsi - s2_LrsiMid);                               // midline (T3.2)
	nx_sAtr = s2_atr;
	nx_sVol = 1;                          // replaced by the volume mode (T2)
	nx_sEx = 0;                           // replaced by the exit mode (T1)

	file_append(s2_IndFile, strf("IND,%s,%i,%i,%i,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%i,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f\n",
		Asset, Bar, ymd(ldate(EST, 0)), (int)is(LOOKBACK),
		priceOpen(0), priceHigh(0), priceLow(0), priceClose(0),
		s2_frama, s2_dim, s2_alpha, s2_mesa, s2_roof, s2_stoc, s2_sma, s2_zsma, (int)s2_cnt[0],
		s2_lrsi, s2_l0, s2_l3, s2_den, s2_atr, s2_tr));
}
