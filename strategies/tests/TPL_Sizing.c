// TPL_Sizing.c - NNFX template, probe P6: lot sizing (one [Test] click).
//
// Purpose (T8, M-D8): the template sizes every signal itself: per half
//   Lots = floor(Equity x (nx_RiskPct / 2) % / ((nx_StopAtr x ATR / PIP) x PIPCost)),
// Capital = nx_Capital, MarginCost from nx_Leverage at entry, and three refusals (below 1 lot,
// actual risk above the configured risk, margin above equity). Each signal writes a SIZE row; each
// bar an ACCT row. Checked against hand / model values by tools/check_sizing.py.
// Criteria and prediction: docs/preregistration/TPL_Sizing_Criteria.md, committed before the run.
// Inputs: History/<PAIR>sz.t6 + <PAIR>sz_states.csv and TPL_Sizing_Scenarios.h, written by
//   python tools/make_scenarios.py --zorro C:/Zorro --out analysis/template/sizing/expected
//          --start 2024-03-06 --header strategies/tests/TPL_Sizing_Scenarios.h SIZING
// Assets carry real pair names (assetType = Forex, gotchas 9d.18); files carry an "sz" suffix and are
// loaded with History = "*sz.t6", so neither real runs nor the P5 batch see them. PIP and PIPCost come
// from integer ratios in the generated header (gotchas 9d.1). No costs: spread, commission, rollover 0,
// so Equity is checkable from the trades alone.
// Output: Data/NNFX_Template_log.csv (deleted at INITRUN); copy to Data/TPL_Sizing_log_run<n>.csv.
// This is a probe, not template logic: dates and asset parameters are written here directly.

#include <default.c>
#include "../template/NNFX_Config.h"
#include "../template/NNFX_Slots.h"
#include "../template/NNFX_Template.h"
#include "TPL_Sizing_Scenarios.h"

int tsz_CompileOnly = 1;   // 1: compile check; set 0 for run 1 after the criteria commit

void run()
{
	BarPeriod = nx_BarPeriodMin;
	BarZone = nx_BarZone;
	BarOffset = nx_BarOffsetMin;
	Fill = nx_FillMode;
	Slippage = nx_SlippageSec;
	Hedge = nx_HedgeMode;
	StartWeek = nx_StartWeek;
	History = "*sz.t6";   // P6 synthetic files only; set before any asset call
	LookBack = 0;
	StartDate = 20240228;
	EndDate = 20240329;
	set(LOGFILE);

	int tsz_i;
	if(is(INITRUN)) {
		nx_config_init();
		BarPeriod = nx_BarPeriodMin;
		BarZone = nx_BarZone;
		BarOffset = nx_BarOffsetMin;
		Fill = nx_FillMode;
		Slippage = nx_SlippageSec;
		Hedge = nx_HedgeMode;
		StartWeek = nx_StartWeek;
		if(tsz_CompileOnly) {
			printf("\nTPL_Sizing: compile check only (tsz_CompileOnly = 1), nothing run");
			quit("compile check done");
			return;
		}
		nx_SlotSource = NX_SRC_SCRIPTED;
		// nx_FixedLots stays at its config value 0: risk sizing (M-D8) is what is tested
		nx_template_init();   // also sets Capital = nx_Capital
		int tsz_rcList = assetList("C:\\Users\\eyalp\\Documents\\fx-trading-systems\\config\\assets\\AssetsNNFX_FX.csv");
		if(nx_TicksOn) set(TICKS);
		for(tsz_i = 0; tsz_i < tple_N(); tsz_i++) {
			string tsz_n = tple_name(tsz_i);
			var tsz_pip = 1; tsz_pip /= tple_pip_den(tsz_i);
			var tsz_pc = tple_pipcost_num(tsz_i); tsz_pc /= tple_pipcost_den(tsz_i);
			assetAdd(tsz_n, 1, 0, 0, 0, tsz_pip, tsz_pc, 0, nx_Leverage, 1000, 0, tsz_n);
			int tsz_rows = nx_slots_load(tsz_i, strf("History\\%s_states.csv", tple_stem(tsz_i)));
			nx_aVolMode[tsz_i] = tple_volume_mode(tsz_i);
			nx_aBtfOn[tsz_i] = tple_btf_on(tsz_i);
			nx_aContStop[tsz_i] = tple_cont_after_stop(tsz_i);
			nx_aMut[tsz_i] = tple_mutation(tsz_i);
			nx_log(strf("INFO,%s,%i,rows=%i,mut=%i,type=%i,list=%i,FixedLots=%i,Capital=%.2f,RiskPct=%.6f,Leverage=%.6f,StopAtr=%.6f,Fill=%i,Hedge=%i,TICKS=%i,BarOffset=%i,StartWeek=%i",
				tsz_n, tsz_i, tsz_rows, nx_aMut[tsz_i], assetType(tsz_n), tsz_rcList, nx_FixedLots, Capital,
				nx_RiskPct, nx_Leverage, nx_StopAtr, Fill, Hedge, (int)is(TICKS), BarOffset, StartWeek));
		}
	}

	for(tsz_i = 0; tsz_i < tple_N(); tsz_i++) {
		string tsz_name = tple_name(tsz_i);
		if(!asset(tsz_name)) {
			nx_log(strf("ASSETFAIL,%s,%i", tsz_name, Bar));
		} else {
			Spread = 0; Commission = 0; RollLong = 0; RollShort = 0;   // no costs in this probe
			nx_slots_update(tsz_i);
			nx_bar(tsz_i, tsz_name);
			nx_log(strf("ASSET,%s,%i,%i,%.10f,%.10f,%.10f,%i", tsz_name, Bar, ymd(ldate(EST, 0)),
				priceClose(0), PIP, PIPCost, (int)LotAmount));
		}
	}
	nx_account_row();
	for(open_trades)
		nx_log(strf("OPEN,%s,%i,%i,%i,%i,%.15f,%.15f,%.8f,%.4f", Asset, Bar, TradeInt[NX_TI_GROUP],
			TradeInt[NX_TI_HALF], (int)TradeIsPending, TradePriceOpen, (var)TradeStopLimit,
			(var)TradeProfit, TradeLots));
}
