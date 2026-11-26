// TPL_IND_PAIR.c - C1S3 check V-a (and DIAG1 inputs): Zorro's 17:00 New York daily bars and the indicators of the five
// C1S3 readings (FSH, MSS, RFX, ROF, LRS) plus FRAMA and ATR on a new dev pair.
// Bars and indicators only: NO trades, no account figures (docs/preregistration/C1S3_FiveC1_Pooled_Criteria.md,
// "Zorro checks before any read"). TPL_BARS_PAIR.c (C1S2) is unchanged; bar settings here are copied from it.
// One [Test] click per pair. Switch ip_Pair: 1 = AUD/USD, 2 = EUR/JPY.
// Output (deleted at INITRUN; Claude copies it after each click): Data/IND_PAIR_log.csv -> Data/IND_<pair>_log_run<n>.csv
//   INFO row (settings), RIND rows (Bar, ymd, wdate, lookback, o, h, l, c, then the indicator values). Checker:
//   tools/check_ind_pair.py. Indicator calls as NNFX_Strategy1.h (Fisher, Reflex) and NNFX_Strategy2.h (FRAMA, MESA,
//   own SMA + Zorro SMA for X1, LRSI), ATR as both. Every call runs on every bar, no condition around it (gotchas 3.1).
// ip_CompileOnly = 1: compiles and stops at INITRUN. Test script, not template logic: dates written here directly. Prefix ip_.

#include <default.c>
#include "../template/NNFX_Config.h"
#include "../template/NNFX_Strategy1_Config.h"
#include "../template/NNFX_Strategy2_Config.h"
#include "../../indicators/ehlers/FisherTransform.c"
#include "../../indicators/ehlers/Reflex.c"
#include "../../indicators/ehlers/FRAMA.c"
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/MESAStochastic.c"
#include "../../indicators/ehlers/LaguerreRSI.c"
#include "../../indicators/nnfx/ATR.c"

int ip_CompileOnly = 0;   // compile check done 2026-11-26 (530eec1)
int ip_Pair = 2;          // 1 = AUD/USD, 2 = EUR/JPY
string ip_Log = "Data\\IND_PAIR_log.csv";

void ip_log(string ip_s) { file_append(ip_Log, ip_s); }

void run()
{
	string ip_Asset = "AUD/USD";
	if(ip_Pair == 2) ip_Asset = "EUR/JPY";
	BarPeriod = nx_BarPeriodMin;
	BarZone = nx_BarZone;
	BarOffset = nx_BarOffsetMin;
	Fill = nx_FillMode;
	StartWeek = nx_StartWeek;
	StartDate = 20070401;   // C1S2 Range, carried by C1S3: AUD/USD as EUR/USD
	EndDate = 20260529;
	if(ip_Pair == 2) { StartDate = 20120201; EndDate = 20260115; }   // C1S2 Range: EUR/JPY

	if(is(INITRUN)) {
		nx_config_init();
		s1_config_init();
		s2_config_init();
		LookBack = s1_LookBackBars;   // 520 (s2_LookBackBars is also 520; logged), set before the first asset call
		BarPeriod = nx_BarPeriodMin;
		BarZone = nx_BarZone;
		BarOffset = nx_BarOffsetMin;
		Fill = nx_FillMode;
		StartWeek = nx_StartWeek;
		if(ip_CompileOnly) {
			printf("\nTPL_IND_PAIR: compile check only (ip_CompileOnly = 1), nothing run");
			quit("compile check done");
			return;
		}
		if(nx_TicksOn) set(TICKS);
		if(nx_FillUnrounded) setf(TradeMode, TR_FRC);
		file_delete(ip_Log);
		int ip_rc = assetList("C:\\Users\\eyalp\\Documents\\fx-trading-systems\\config\\assets\\AssetsNNFX_FX.csv");
		asset(ip_Asset);
		// specifiers: 1 %s + 11 %i (list .. LookBack2) + 3 %.10f (PIP, PIPCost, Spread) + 2 %.6f (rolls)
		//            + 7 %i (FisherLen, ReflexLen, FramaN, MesaLen, MesaHP, MesaSS, SmaLen) + 1 %.6f (gamma) + 1 %i (AtrLen)
		//            = 26 arguments after the format
		ip_log(strf("INFO,%s,0,list=%i,type=%i,LookBack=%i,TICKS=%i,TradeModeFRC=%i,Fill=%i,BarOffset=%i,StartWeek=%i,StartDate=%i,EndDate=%i,LookBack2=%i,PIP=%.10f,PIPCost=%.10f,Spread=%.10f,RollLong=%.6f,RollShort=%.6f,FisherLen=%i,ReflexLen=%i,FramaN=%i,MesaLen=%i,MesaHP=%i,MesaSS=%i,SmaLen=%i,LrsiGamma=%.6f,AtrLen=%i\n",
			ip_Asset, ip_rc, assetType(ip_Asset), LookBack, (int)is(TICKS), (int)((TradeMode & TR_FRC) != 0), Fill, BarOffset,
			StartWeek, StartDate, EndDate, s2_LookBackBars, PIP, PIPCost, Spread, RollLong, RollShort,
			s1_FisherLen, s1_ReflexLen, s2_FramaN, s2_MesaLen, s2_MesaHP, s2_MesaSS, s2_C1SmaLen, s2_LrsiGamma, nx_AtrLen));
		ip_log("kind,asset,bar,ymd,wdate,lookback,o,h,l,c,fish,trig,mesa,roof,sma,zsma,nmesa,reflex,lrsi,frama,atr,tr\n");
		return;   // no indicator call in INITRUN (gotchas 9d.20)
	}

	if(!asset(ip_Asset)) { ip_log(strf("ASSETFAIL,%s,%i\n", ip_Asset, Bar)); return; }
	int ip_n = s2_FramaN + s2_SeriesExtra;
	if(nx_AtrLen + s2_SeriesExtra > ip_n) ip_n = nx_AtrLen + s2_SeriesExtra;
	if(s2_MesaLen + s2_SeriesExtra > ip_n) ip_n = s2_MesaLen + s2_SeriesExtra;
	if(s1_FisherLen + s1_SeriesExtra > ip_n) ip_n = s1_FisherLen + s1_SeriesExtra;
	if(s1_ReflexLen + s1_SeriesExtra > ip_n) ip_n = s1_ReflexLen + s1_SeriesExtra;
	vars ip_mid = series((priceHigh() + priceLow()) * s1_MidWeight, ip_n);   // (H+L)/2: Fisher, FRAMA Price (a); s1 = s2 weight
	vars ip_hi = series(priceHigh(), ip_n);
	vars ip_lo = series(priceLow(), ip_n);
	vars ip_cl = series(priceClose(), ip_n);                                  // Reflex, MESA, LRSI input (a); ATR close

	var ip_raw = 0; var ip_v1 = 0; var ip_rng = 0; var ip_trig = 0;
	var ip_fish = FisherCore(ip_mid, s1_FisherLen, &ip_raw, &ip_v1, &ip_rng, &ip_trig);
	var ip_sum = 0; var ip_ms1 = 0;
	var ip_rfx = ReflexCore(ip_cl, s1_ReflexLen, &ip_sum, &ip_ms1);
	var ip_dim = 0; var ip_alpha = 0;
	var ip_frama = FRAMACore(ip_mid, ip_hi, ip_lo, s2_FramaN, &ip_dim, &ip_alpha);
	var ip_roof = 0; var ip_stoc = 0;
	var ip_mesa = MESAStochasticCore(ip_cl, s2_MesaLen, s2_MesaHP, s2_MesaSS, &ip_roof, &ip_stoc);
	var ip_l0 = 0; var ip_l3 = 0; var ip_den = 0;
	var ip_lrsi = LaguerreRSICore(ip_cl, s2_LrsiGamma, &ip_l0, &ip_l3, &ip_den);
	var ip_tr = 0;
	var ip_atr = ATRMT4Core(ip_hi, ip_lo, ip_cl, nx_AtrLen, &ip_tr);

	// MSS second line, as NNFX_Strategy2.h: own SMA of the last s2_C1SmaLen MESA outputs, oldest first; Zorro SMA() for X1
	vars ip_ms = series(ip_mesa, s2_C1SmaLen + s2_SeriesExtra);   // explicit length (gotchas 9d.10)
	vars ip_cnt = series(0, s2_CountLen);                          // per-instance count of MESA outputs, starts at 0
	ip_cnt[0] = ip_cnt[1] + 1;
	var ip_sma = 0;
	int ip_k;
	for(ip_k = s2_C1SmaLen - 1; ip_k >= 0; ip_k--) ip_sma += ip_ms[ip_k];
	ip_sma /= s2_C1SmaLen;
	var ip_zsma = SMA(ip_ms, s2_C1SmaLen);                          // X1 cross-check only

	// specifiers: %s; %i Bar, ymd; %.10f wdate; %i lookback; %.10f o h l c (4);
	//            %.15f fish trig mesa roof sma zsma nmesa reflex lrsi frama atr tr (12)
	//            = 1 %s + 3 %i + 5 %.10f + 12 %.15f = 21 arguments after the format (22 fields with the kind)
	ip_log(strf("RIND,%s,%i,%i,%.10f,%i,%.10f,%.10f,%.10f,%.10f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f\n",
		ip_Asset, Bar, ymd(ldate(EST, 0)), wdate(0), (int)is(LOOKBACK),
		priceOpen(0), priceHigh(0), priceLow(0), priceClose(0),
		ip_fish, ip_trig, ip_mesa, ip_roof, ip_sma, ip_zsma, ip_cnt[0], ip_rfx, ip_lrsi, ip_frama, ip_atr, ip_tr));
}
