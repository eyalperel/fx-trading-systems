// TPL_R1_EURUSD.c - first real-data run of the NNFX template: Strategy 1, variant 0, EUR/USD D1
// (decisions R-D1..R-D7, docs/template/NNFX_TEMPLATE_DECISIONS.md). One [Test] click per mode.
//
// Purpose: MECHANICS ONLY (R-D1). Bars, indicator wiring, the trade replay against the Python engine,
// sizing, costs and Equity are checked by tools/check_r1.py. No performance figure is computed or
// recorded; the Zorro window's summary line is not used.
// Modes (R-D7): r1_Costs = 0 -> R1a (spread, commission, rollover 0: exact M1 replay);
//               r1_Costs = 1 -> R1b (asset-list costs x1: cost identity, sizing, Equity).
// Criteria: docs/preregistration/TPL_R1_Criteria.md, committed before each run.
// Inputs: C:/Zorro/History/EURUSD_2005..2026.t6 (M1, real), config/assets/AssetsNNFX_FX.csv (M-D4).
// Outputs (copy after each run, both are deleted at INITRUN):
//   Data/NNFX_Template_log.csv   -> Data/TPL_R1<a|b>_log_run<n>.csv   (template rows, BAR rows)
//   Data/NNFX_Strategy1_ind.csv  -> Data/TPL_R1<a|b>_ind_run<n>.csv   (indicator values per bar)
// r1_CompileOnly = 1: compiles and stops at INITRUN, nothing run.
// This is a test script, not template logic: dates and modes are written here directly. Prefix r1_.

#include <default.c>
#include "../template/NNFX_Config.h"
#include "../template/NNFX_Strategy1_Config.h"
#include "../../indicators/ehlers/MAMA.c"
#include "../../indicators/ehlers/FisherTransform.c"
#include "../../indicators/ehlers/Reflex.c"
#include "../../indicators/nnfx/ATR.c"
#include "../template/NNFX_Strategy1.h"
#include "../template/NNFX_Slots.h"
#include "../template/NNFX_Template.h"

int r1_CompileOnly = 0;   // run (compile checks 2026-11-23 clean); criteria committed before each run
int r1_Costs = 0;         // 0 = R1a, 1 = R1b (R-D7)
string r1_Asset = "EUR/USD";

void run()
{
	BarPeriod = nx_BarPeriodMin;
	BarZone = nx_BarZone;
	BarOffset = nx_BarOffsetMin;
	Fill = nx_FillMode;
	Slippage = nx_SlippageSec;
	Hedge = nx_HedgeMode;
	StartWeek = nx_StartWeek;
	StartDate = 20070201;   // R-D4 amended 2026-11-23: 539 bars before it cover LookBack 520
	EndDate = 20260529;     // R-D4: last history day (b)

	if(is(INITRUN)) {
		nx_config_init();
		s1_config_init();
		LookBack = s1_LookBackBars;   // R-D4; set before the first asset call
		BarPeriod = nx_BarPeriodMin;
		BarZone = nx_BarZone;
		BarOffset = nx_BarOffsetMin;
		Fill = nx_FillMode;
		Slippage = nx_SlippageSec;
		Hedge = nx_HedgeMode;
		StartWeek = nx_StartWeek;
		if(r1_CompileOnly) {
			printf("\nTPL_R1_EURUSD: compile check only (r1_CompileOnly = 1), nothing run");
			quit("compile check done");
			return;
		}
		nx_SlotSource = NX_SRC_STRATEGY;   // R-D2: Strategy 1's indicators
		nx_template_init();                // also Capital and TR_FRC (M-D8.3, R-D5)
		s1_ind_init();
		int r1_rcList = assetList("C:\\Users\\eyalp\\Documents\\fx-trading-systems\\config\\assets\\AssetsNNFX_FX.csv");
		if(nx_TicksOn) set(TICKS);
		asset(r1_Asset);
		nx_log(strf("INFO,%s,0,costs=%i,type=%i,list=%i,FixedLots=%i,Capital=%.2f,RiskPct=%.6f,Leverage=%.6f,LookBack=%i,TradeModeFRC=%i,Fill=%i,Hedge=%i,TICKS=%i,BarOffset=%i,StartWeek=%i,PIP=%.10f,PIPCost=%.10f,LotAmount=%i,Spread=%.10f,RollLong=%.6f,RollShort=%.6f,Commission=%.6f,FastLimit=%.6f,SlowLimit=%.6f,FisherLen=%i,ReflexLen=%i,AtrLen=%i",
			r1_Asset, r1_Costs, assetType(r1_Asset), r1_rcList, nx_FixedLots, Capital, nx_RiskPct, nx_Leverage,
			LookBack, (int)((TradeMode & TR_FRC) != 0), Fill, Hedge, (int)is(TICKS), BarOffset, StartWeek,
			PIP, PIPCost, (int)LotAmount, Spread, RollLong, RollShort, Commission,
			s1_FastLimit, s1_SlowLimit, s1_FisherLen, s1_ReflexLen, nx_AtrLen));
	}

	if(!asset(r1_Asset)) { nx_log(strf("ASSETFAIL,%s,%i", r1_Asset, Bar)); return; }
	if(r1_Costs) {
		nx_costs_apply(0);   // T7 spread level from the asset list (x1)
	} else {
		Spread = 0; Commission = 0; RollLong = 0; RollShort = 0;   // R1a: no costs (spread.htm)
	}
	nx_slots_update(0);   // every bar, LOOKBACK included: indicators warm up (gotchas 3.1)
	nx_log(strf("RBAR,%s,%i,%i,%.10f,%i,%.10f,%.10f,%.10f,%.10f", r1_Asset, Bar, ymd(ldate(EST, 0)), wdate(0),
		(int)is(LOOKBACK), priceOpen(0), priceHigh(0), priceLow(0), priceClose(0)));
	if(!is(LOOKBACK)) {
		nx_bar(0, r1_Asset);   // decisions only after the warm-up (engine replay starts here too)
		nx_account_row();
	}
}
