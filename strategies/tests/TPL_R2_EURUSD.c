// TPL_R2_EURUSD.c - real-data runs of the NNFX template for Strategy 2 variant 0 on EUR/USD D1 (PERF2 P-2).
// One [Test] click per run. Copy of TPL_R1_EURUSD.c pointed at NNFX_Strategy2.h; TPL_R1_EURUSD.c is not touched.
//
// Runs (criteria: docs/preregistration/PERF2_Strategy2_EURUSD_Criteria.md, predictions committed before each click):
//   r2_SpreadLevel = 0 -> R2a: spread, commission, rollover 0 (bars, wiring, X1, states, exact M1 replay; mechanics only)
//   r2_SpreadLevel = 1 -> R2b: asset-list costs x1        (read by tools/perf_report.py as x1)
//   r2_SpreadLevel = 2 -> R2c: asset-list costs, spread x2 (read by tools/perf_report.py as x2)
// Outputs (both deleted at INITRUN; copy after each run):
//   Data/NNFX_Template_log.csv   -> Data/TPL_R2<a|b|c>_log_run<n>.csv
//   Data/NNFX_Strategy2_ind.csv  -> Data/TPL_R2<a|b|c>_ind_run<n>.csv
// After a click only Error lines and the trade count are reported, as text (PERF2 P-5.1).
// r2_CompileOnly = 1: compiles and stops at INITRUN, nothing run.
// This is a test script, not template logic: dates and modes are written here directly. Prefix r2_.

#include <default.c>
#include "../template/NNFX_Config.h"
#include "../template/NNFX_Strategy2_Config.h"
#include "../../indicators/ehlers/FRAMA.c"
#include "../../indicators/ehlers/HighPassFilter.c"
#include "../../indicators/ehlers/SuperSmoother2Pole.c"
#include "../../indicators/ehlers/RoofingFilter.c"
#include "../../indicators/ehlers/MESAStochastic.c"
#include "../../indicators/ehlers/LaguerreRSI.c"
#include "../../indicators/nnfx/ATR.c"
#include "../template/NNFX_Strategy2.h"
#include "../template/NNFX_Slots.h"
#include "../template/NNFX_Template.h"

int r2_CompileOnly = 0;   // compile check 2026-11-25 clean; run (PERF2 Amendment 2: R2a prediction committed first)
int r2_SpreadLevel = 1;   // 0 = R2a (costs off), 1 = R2b (x1), 2 = R2c (x2); PERF2 P-2. R2a run 3 PASS; set to 1 for R2b
string r2_Asset = "EUR/USD";

void run()
{
	BarPeriod = nx_BarPeriodMin;
	BarZone = nx_BarZone;
	BarOffset = nx_BarOffsetMin;
	Fill = nx_FillMode;
	Slippage = nx_SlippageSec;
	Hedge = nx_HedgeMode;
	StartWeek = nx_StartWeek;
	StartDate = 20070401;   // PERF2 Range: same bars as PERF1 (R1 Amendment 1)
	EndDate = 20260529;     // R-D4: last history day (b)

	if(is(INITRUN)) {
		nx_config_init();
		s2_config_init();
		nx_BtfOn = 1;                      // bridge-too-far on: two-lines-cross C1 [V34]; T3 amendment 1.2
		if(r2_SpreadLevel > 0) nx_SpreadMult = r2_SpreadLevel;   // T7 level x1 / x2 (config default 1)
		LookBack = s2_LookBackBars;        // set before the first asset call
		BarPeriod = nx_BarPeriodMin;
		BarZone = nx_BarZone;
		BarOffset = nx_BarOffsetMin;
		Fill = nx_FillMode;
		Slippage = nx_SlippageSec;
		Hedge = nx_HedgeMode;
		StartWeek = nx_StartWeek;
		if(r2_CompileOnly) {
			printf("\nTPL_R2_EURUSD: compile check only (r2_CompileOnly = 1), nothing run");
			quit("compile check done");
			return;
		}
		nx_SlotSource = NX_SRC_STRATEGY;   // Strategy 2's indicators
		nx_template_init();                // also Capital and TR_FRC (M-D8.3, R-D5)
		s2_ind_init();
		int r2_rcList = assetList("C:\\Users\\eyalp\\Documents\\fx-trading-systems\\config\\assets\\AssetsNNFX_FX.csv");
		if(nx_TicksOn) set(TICKS);
		asset(r2_Asset);
		int r2_Costs = 0;
		if(r2_SpreadLevel > 0) r2_Costs = 1;
		nx_log(strf("INFO,%s,0,costs=%i,type=%i,list=%i,FixedLots=%i,Capital=%.2f,RiskPct=%.6f,Leverage=%.6f,LookBack=%i,TradeModeFRC=%i,Fill=%i,Hedge=%i,TICKS=%i,BarOffset=%i,StartWeek=%i,PIP=%.10f,PIPCost=%.10f,LotAmount=%i,Spread=%.10f,RollLong=%.6f,RollShort=%.6f,Commission=%.6f,FramaN=%i,MesaLen=%i,MesaHP=%i,MesaSS=%i,C1SmaLen=%i,LrsiGamma=%.6f,AtrLen=%i,BtfOn=%i,SpreadMult=%.6f,Tp1Atr=%.6f,RefusedLog=%i",
			r2_Asset, r2_Costs, assetType(r2_Asset), r2_rcList, nx_FixedLots, Capital, nx_RiskPct, nx_Leverage,
			LookBack, (int)((TradeMode & TR_FRC) != 0), Fill, Hedge, (int)is(TICKS), BarOffset, StartWeek,
			PIP, PIPCost, (int)LotAmount, Spread, RollLong, RollShort, Commission,
			s2_FramaN, s2_MesaLen, s2_MesaHP, s2_MesaSS, s2_C1SmaLen, s2_LrsiGamma, nx_AtrLen, nx_BtfOn,
			nx_SpreadMult, nx_Tp1Atr, nx_RefusedLog));
		return;   // R1 Amendment 1: no slot call in INITRUN; Zorro discards series state from that call
	}

	if(!asset(r2_Asset)) { nx_log(strf("ASSETFAIL,%s,%i", r2_Asset, Bar)); return; }
	if(r2_SpreadLevel > 0) {
		nx_costs_apply(0);   // T7 spread level from the asset list x nx_SpreadMult
	} else {
		Spread = 0; Commission = 0; RollLong = 0; RollShort = 0;   // R2a: no costs (spread.htm)
	}
	nx_slots_update(0);   // every bar, LOOKBACK included: indicators warm up (gotchas 3.1)
	nx_log(strf("RBAR,%s,%i,%i,%.10f,%i,%.10f,%.10f,%.10f,%.10f", r2_Asset, Bar, ymd(ldate(EST, 0)), wdate(0),
		(int)is(LOOKBACK), priceOpen(0), priceHigh(0), priceLow(0), priceClose(0)));
	if(!is(LOOKBACK)) {
		nx_bar(0, r2_Asset);   // decisions only after the warm-up (engine replay starts here too)
		nx_account_row();
	}
}
