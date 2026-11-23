// TPL_Equivalence.c - NNFX template, stage S4: engine equivalence batch (one [Test] click).
//
// Runs the Light-C template (strategies/template/NNFX_Template.h) on 64 synthetic scenarios,
// one asset each: 30 long scenarios of the reference-engine tests, their 30 short mirrors and
// 4 planted-bug controls (S4 decisions 3 and 4, 2026-11-23). Slots are SCRIPTED from each
// scenario's states CSV, so every slot value is known exactly. Expected trades: the reference
// engine on the same float32 inputs (analysis/template/equivalence/expected/).
// Criteria: docs/preregistration/TPL_Equivalence_Criteria.md, committed before the run.
// Inputs: History/SYN_*.t6 + SYN_*_states.csv and TPL_Equivalence_Scenarios.h, all written by
//   python tools/make_scenarios.py --zorro C:/Zorro --out analysis/template/equivalence/expected
//          --start 2024-03-06 --header strategies/tests/TPL_Equivalence_Scenarios.h ALL
// Output: Data/NNFX_Template_log.csv (deleted at INITRUN). After the run copy it to
//   Data/TPL_Equivalence_log_run<n>.csv. Expect no line starting with "Error" in the window.
// tpe_CompileOnly = 1: compiles and stops at INITRUN before any asset is loaded or any trade
// is made (a compile check that shows no result). Set 0 for the real run.
// This is a test batch, not template logic: dates and the synthetic asset parameters are
// written here directly (as TPL_Probe.c).

#include <default.c>
#include "../template/NNFX_Config.h"
#include "../template/NNFX_Slots.h"
#include "../template/NNFX_Template.h"
#include "TPL_Equivalence_Scenarios.h"

int tpe_CompileOnly = 0;   // run 2 (Amendment 1 committed before the run)

void run()
{
	BarPeriod = nx_BarPeriodMin;
	BarZone = nx_BarZone;
	BarOffset = nx_BarOffsetMin;
	Fill = nx_FillMode;
	Slippage = nx_SlippageSec;
	Hedge = nx_HedgeMode;
	StartWeek = nx_StartWeek;   // M-D6; must precede the first asset call (barmode.htm)
	LookBack = 0;
	StartDate = 20240228;   // 5 warm-up bars before the scenarios (make_scenarios PAD_BARS)
	EndDate = 20240329;     // after the last scenario day 2024-03-26
	set(LOGFILE);

	int tpe_i;
	if(is(INITRUN)) {
		nx_config_init();
		BarPeriod = nx_BarPeriodMin;
		BarZone = nx_BarZone;
		BarOffset = nx_BarOffsetMin;
		Fill = nx_FillMode;
		Slippage = nx_SlippageSec;
		Hedge = nx_HedgeMode;
		StartWeek = nx_StartWeek;
		if(tpe_CompileOnly) {
			printf("\nTPL_Equivalence: compile check only (tpe_CompileOnly = 1), nothing run");
			quit("compile check done");
			return;
		}
		nx_SlotSource = NX_SRC_SCRIPTED;
		nx_FixedLots = 1;
		nx_template_init();
		int tpe_rcList = assetList("C:\\Users\\eyalp\\Documents\\fx-trading-systems\\config\\assets\\AssetsNNFX_FX.csv");
		var tpe_pip = 1; tpe_pip /= 10000;
		var tpe_pipCost = 1; tpe_pipCost /= 10;
		if(nx_TicksOn) set(TICKS);   // T5 amendment; set in INITRUN (mode.htm)
		for(tpe_i = 0; tpe_i < tple_N(); tpe_i++) {
			string tpe_n = tple_name(tpe_i);
			assetAdd(tpe_n, 1, 0, 0, 0, tpe_pip, tpe_pipCost, 0, nx_Leverage, 1000, 0, tpe_n);
			int tpe_rows = nx_slots_load(tpe_i, strf("History\\%s_states.csv", tpe_n));
			nx_aVolMode[tpe_i] = tple_volume_mode(tpe_i);
			nx_aBtfOn[tpe_i] = tple_btf_on(tpe_i);
			nx_aContStop[tpe_i] = tple_cont_after_stop(tpe_i);
			nx_aMut[tpe_i] = tple_mutation(tpe_i);
			nx_log(strf("INFO,%s,%i,rows=%i,vol=%i,btf=%i,cont=%i,mut=%i,list=%i,Fill=%i,Hedge=%i,TICKS=%i,BarOffset=%i,StartWeek=%i",
				tpe_n, tpe_i, tpe_rows, nx_aVolMode[tpe_i], nx_aBtfOn[tpe_i], nx_aContStop[tpe_i],
				nx_aMut[tpe_i], tpe_rcList, Fill, Hedge, (int)is(TICKS), BarOffset, StartWeek));
		}
	}

	for(tpe_i = 0; tpe_i < tple_N(); tpe_i++) {
		string tpe_name = tple_name(tpe_i);
		if(!asset(tpe_name)) { nx_log(strf("ASSETFAIL,%s,%i", tpe_name, Bar)); continue; }
		Spread = 0;   // assetAdd(..., 0, ...) leaves a spread (TPL_Probe run 4); costs are P5
		nx_slots_update(tpe_i);
		nx_bar(tpe_i, tpe_name);
		nx_log(strf("CNT,%s,%i,%i,%i", tpe_name, Bar, nx_aNSameBar[tpe_i], nx_aNBeAdv[tpe_i]));
	}
	for(open_trades)
		nx_log(strf("OPEN,%s,%i,%i,%i,%i,%.15f,%.15f", Asset, Bar, TradeInt[NX_TI_GROUP],
			TradeInt[NX_TI_HALF], (int)TradeIsPending, TradePriceOpen, (var)TradeStopLimit));
}
