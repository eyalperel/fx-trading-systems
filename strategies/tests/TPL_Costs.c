// TPL_Costs.c - NNFX template, probe P5: transaction costs (one [Test] click).
//
// Purpose (decision T7 guard; docs/template/ZORRO_TRADE_MECHANICS.md §7): the same 8 scenarios
// (A1, A2, B1, C1 and their short mirrors) run twice in one click, costs off (K0) and costs on
// (K1), through the unchanged template. Per half, the K0 - K1 profit difference must equal the
// hand-calculated spread + commission - rollover. Criteria and prediction:
// docs/preregistration/TPL_Costs_P5_Criteria.md, committed before the run.
// Inputs: History/<PAIR>syn.t6 + <PAIR>syn_states.csv and TPL_Costs_Scenarios.h, written by
//   python tools/make_scenarios.py --zorro C:/Zorro --out analysis/template/costs/expected
//          --start 2024-03-06 --header strategies/tests/TPL_Costs_Scenarios.h COSTS
// Assets carry real pair names (only those are Forex for assetType(), PROBE_AssetType 2026-11-23); the
// INFO row logs assetType(), which must be 1. Their files carry a "syn" suffix and are loaded with
// History = "*syn.t6" (history.htm), so no real-pair run can load them.
// Output: Data/NNFX_Template_log.csv (deleted at INITRUN); copy to Data/TPL_Costs_log_run<n>.csv.
// K1 costs (built from integers, gotchas 9d.1): Spread 2 pips; Commission 1 per 10000 units;
// RollLong -1, RollShort +0.5 per 10000 units per day. With PIPCost 0.1 per pip and LotAmount
// 1000: spread 0.2, commission 0.1 per round turn, rollover -0.1 / +0.05 per day, per lot.
// This is a probe, not template logic: dates and costs are written here directly.

#include <default.c>
#include "../template/NNFX_Config.h"
#include "../template/NNFX_Slots.h"
#include "../template/NNFX_Template.h"
#include "TPL_Costs_Scenarios.h"

int tpc_CompileOnly = 0;   // run 2 (Amendment 1 committed before the run; compile check with 1 done)

void run()
{
	BarPeriod = nx_BarPeriodMin;
	BarZone = nx_BarZone;
	BarOffset = nx_BarOffsetMin;
	Fill = nx_FillMode;
	Slippage = nx_SlippageSec;
	Hedge = nx_HedgeMode;
	StartWeek = nx_StartWeek;
	History = "*syn.t6";   // synthetic files only (P5 Amendment 1); set before any asset call
	LookBack = 0;
	StartDate = 20240228;
	EndDate = 20240329;
	set(LOGFILE);

	var tpc_pip = 1; tpc_pip /= 10000;
	var tpc_spread1 = 2; tpc_spread1 *= tpc_pip;
	var tpc_comm1 = 1;
	var tpc_rollL1 = -1;
	var tpc_rollS1 = 1; tpc_rollS1 /= 2;
	int tpc_i;
	if(is(INITRUN)) {
		nx_config_init();
		BarPeriod = nx_BarPeriodMin;
		BarZone = nx_BarZone;
		BarOffset = nx_BarOffsetMin;
		Fill = nx_FillMode;
		Slippage = nx_SlippageSec;
		Hedge = nx_HedgeMode;
		StartWeek = nx_StartWeek;
		if(tpc_CompileOnly) {
			printf("\nTPL_Costs: compile check only (tpc_CompileOnly = 1), nothing run");
			quit("compile check done");
			return;
		}
		nx_SlotSource = NX_SRC_SCRIPTED;
		nx_FixedLots = 1;
		nx_template_init();
		int tpc_rcList = assetList("C:\\Users\\eyalp\\Documents\\fx-trading-systems\\config\\assets\\AssetsNNFX_FX.csv");
		var tpc_pipCost = 1; tpc_pipCost /= 10;
		if(nx_TicksOn) set(TICKS);
		for(tpc_i = 0; tpc_i < tple_N(); tpc_i++) {
			string tpc_n = tple_name(tpc_i);
			assetAdd(tpc_n, 1, 0, 0, 0, tpc_pip, tpc_pipCost, 0, nx_Leverage, 1000, 0, tpc_n);
			int tpc_rows = nx_slots_load(tpc_i, strf("History\\%s_states.csv", tple_stem(tpc_i)));
			nx_aVolMode[tpc_i] = tple_volume_mode(tpc_i);
			nx_aBtfOn[tpc_i] = tple_btf_on(tpc_i);
			nx_aContStop[tpc_i] = tple_cont_after_stop(tpc_i);
			nx_aMut[tpc_i] = tple_mutation(tpc_i);
			nx_log(strf("INFO,%s,%i,rows=%i,costed=%i,type=%i,list=%i,Fill=%i,Hedge=%i,TICKS=%i,BarOffset=%i,StartWeek=%i,SpreadMult=%.6f",
				tpc_n, tpc_i, tpc_rows, tple_costed(tpc_i), assetType(tpc_n), tpc_rcList, Fill, Hedge,
				(int)is(TICKS), BarOffset, StartWeek, nx_SpreadMult));
		}
	}

	for(tpc_i = 0; tpc_i < tple_N(); tpc_i++) {
		string tpc_name = tple_name(tpc_i);
		if(!asset(tpc_name)) {
			nx_log(strf("ASSETFAIL,%s,%i", tpc_name, Bar));
		} else {
			Spread = 0; Commission = 0; RollLong = 0; RollShort = 0;   // K0: no costs (spread.htm)
			if(tple_costed(tpc_i)) {
				Spread = tpc_spread1;
				Commission = tpc_comm1;
				RollLong = tpc_rollL1;
				RollShort = tpc_rollS1;
			}
			nx_costs_apply(tpc_i);   // T7 multiplier (x1 here) from the stored base
			nx_slots_update(tpc_i);
			nx_bar(tpc_i, tpc_name);
			nx_log(strf("COST,%s,%i,%i,%.10f,%.6f,%.6f,%.6f", tpc_name, Bar, ymd(ldate(EST, 0)),
				Spread, Commission, RollLong, RollShort));
		}
	}
	for(open_trades)
		nx_log(strf("OPEN,%s,%i,%i,%i,%i,%.15f,%.15f,%.8f,%.8f", Asset, Bar, TradeInt[NX_TI_GROUP],
			TradeInt[NX_TI_HALF], (int)TradeIsPending, TradePriceOpen, (var)TradeStopLimit,
			(var)TradeRoll, (var)TradeProfit));
}
