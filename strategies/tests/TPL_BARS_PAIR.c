// TPL_BARS_PAIR.c - C1S2 check P4 (V-b): Zorro's 17:00 New York daily bars and MAMA / FAMA / ATR on a new dev pair.
// Bars and indicators only: NO trades, no account figures (docs/preregistration/C1S2_MAF_OtherPairs_Criteria.md).
// One [Test] click per pair. Switch bp_Pair: 1 = AUD/USD, 2 = EUR/JPY.
// Output (deleted at INITRUN; Claude copies it after each click): Data/BARS_PAIR_log.csv -> Data/BARS_<pair>_log_run<n>.csv
//   INFO row (settings), RBAR rows (as TPL_R1: Bar, ymd, wdate, lookback, o, h, l, c), IND rows (MAMA, FAMA, period, alpha,
//   phase, ATR, TR). Checker: tools/check_bars_pair.py.
// bp_CompileOnly = 1: compiles and stops at INITRUN. Test script, not template logic: dates written here directly. Prefix bp_.

#include <default.c>
#include "../template/NNFX_Config.h"
#include "../template/NNFX_Strategy1_Config.h"
#include "../../indicators/ehlers/MAMA.c"
#include "../../indicators/nnfx/ATR.c"

int bp_CompileOnly = 0;   // compile check done 2026-11-26 (e347be0)
int bp_Pair = 1;          // 1 = AUD/USD, 2 = EUR/JPY
string bp_Log = "Data\\BARS_PAIR_log.csv";

void bp_log(string bp_s) { file_append(bp_Log, bp_s); }

void run()
{
	string bp_Asset = "AUD/USD";
	if(bp_Pair == 2) bp_Asset = "EUR/JPY";
	BarPeriod = nx_BarPeriodMin;
	BarZone = nx_BarZone;
	BarOffset = nx_BarOffsetMin;
	Fill = nx_FillMode;
	StartWeek = nx_StartWeek;
	StartDate = 20070401;   // C1S2 Range: AUD/USD as EUR/USD
	EndDate = 20260529;
	if(bp_Pair == 2) { StartDate = 20120201; EndDate = 20260115; }   // C1S2 Range: EUR/JPY

	if(is(INITRUN)) {
		nx_config_init();
		s1_config_init();
		LookBack = s1_LookBackBars;   // 520, set before the first asset call
		BarPeriod = nx_BarPeriodMin;
		BarZone = nx_BarZone;
		BarOffset = nx_BarOffsetMin;
		Fill = nx_FillMode;
		StartWeek = nx_StartWeek;
		if(bp_CompileOnly) {
			printf("\nTPL_BARS_PAIR: compile check only (bp_CompileOnly = 1), nothing run");
			quit("compile check done");
			return;
		}
		if(nx_TicksOn) set(TICKS);
		if(nx_FillUnrounded) setf(TradeMode, TR_FRC);
		file_delete(bp_Log);
		int bp_rc = assetList("C:\\Users\\eyalp\\Documents\\fx-trading-systems\\config\\assets\\AssetsNNFX_FX.csv");
		asset(bp_Asset);
		// specifiers: 1 %s + 10 %i (list .. EndDate) + 3 %.10f (PIP, PIPCost, Spread) + 4 %.6f + 1 %i (AtrLen) = 19 arguments
		bp_log(strf("INFO,%s,0,list=%i,type=%i,LookBack=%i,TICKS=%i,TradeModeFRC=%i,Fill=%i,BarOffset=%i,StartWeek=%i,StartDate=%i,EndDate=%i,PIP=%.10f,PIPCost=%.10f,Spread=%.10f,RollLong=%.6f,RollShort=%.6f,FastLimit=%.6f,SlowLimit=%.6f,AtrLen=%i\n",
			bp_Asset, bp_rc, assetType(bp_Asset), LookBack, (int)is(TICKS), (int)((TradeMode & TR_FRC) != 0), Fill, BarOffset,
			StartWeek, StartDate, EndDate, PIP, PIPCost, Spread, RollLong, RollShort, s1_FastLimit, s1_SlowLimit, nx_AtrLen));
		bp_log("kind,asset,bar,ymd,wdate,lookback,o,h,l,c,mama,fama,period,alpha,phase,atr,tr\n");
		return;   // no slot call in INITRUN (gotchas 9d.20)
	}

	if(!asset(bp_Asset)) { bp_log(strf("ASSETFAIL,%s,%i\n", bp_Asset, Bar)); return; }
	int bp_n = nx_AtrLen + s1_SeriesExtra;
	vars bp_mid = series((priceHigh() + priceLow()) * s1_MidWeight, bp_n);   // (H+L)/2: MAMA input (a)
	vars bp_hi = series(priceHigh(), bp_n);
	vars bp_lo = series(priceLow(), bp_n);
	vars bp_cl = series(priceClose(), bp_n);
	var bp_fama = 0; var bp_per = 0; var bp_alpha = 0; var bp_phase = 0;
	var bp_mama = MAMACore(bp_mid, s1_FastLimit, s1_SlowLimit, &bp_fama, &bp_per, &bp_alpha, &bp_phase);
	var bp_tr = 0;
	var bp_atr = ATRMT4Core(bp_hi, bp_lo, bp_cl, nx_AtrLen, &bp_tr);
	// specifiers: %s; %i Bar, ymd; %.10f wdate; %i lookback; %.10f o h l c (4); %.15f mama fama period alpha phase atr tr (7)
	//            = 1 %s + 3 %i + 5 %.10f + 7 %.15f = 16 arguments after the format
	bp_log(strf("RIND,%s,%i,%i,%.10f,%i,%.10f,%.10f,%.10f,%.10f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f\n",
		bp_Asset, Bar, ymd(ldate(EST, 0)), wdate(0), (int)is(LOOKBACK),
		priceOpen(0), priceHigh(0), priceLow(0), priceClose(0),
		bp_mama, bp_fama, bp_per, bp_alpha, bp_phase, bp_atr, bp_tr));
}
