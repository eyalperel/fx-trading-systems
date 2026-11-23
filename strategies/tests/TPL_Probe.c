// TPL_Probe.c — NNFX template, stage S3 probe batch (one [Test] click).
//
// Purpose: confirm the Zorro 3.11 mechanics the template will rely on, before the template
// is written (docs/template/ZORRO_TRADE_MECHANICS.md §10):
//   P1  Fill = 3: an order placed at a bar's close fills at the next bar's open;
//   P3  a bar touching both Stop and TakeProfit closes at the Stop;
//   P4  BarZone = EST, BarOffset = 17*60: daily bars close 17:00 New York, across the
//       2024-03-10 DST change (synthetic bars here; EUR/USD in a later EUR/USD-only run);
//   plus: assetList() of the project list, assetAdd() of synthetic assets, synthetic
//   .t6 history, dataset load of scripted states (dataParse "%w"), and breakeven set by
//   TradeStopLimit at a close (first half of P2).
// Prediction: docs/template/TPL_Probe_Prediction.md, committed before the run.
// Inputs: History/SYN_A2.t6, SYN_A3.t6, SYN_A2_states.csv, SYN_A3_states.csv
//         (tools/make_scenarios.py --start 2024-03-06 A2 A3).
// Output: Data/TPL_Probe_raw.csv (deleted at INITRUN). After the run copy it to
//         TPL_Probe_raw_run1.csv. Expect no line starting with "Error" in the window.
// This is a probe, not template logic: it uses raw Zorro calls, and its dates and the
// synthetic asset parameters are written here directly.

#include <default.c>
#include "../template/NNFX_Config.h"

string tp_Out = "Data\\TPL_Probe_raw.csv";

void tp_line(string s)
{
	file_append(tp_Out, s);
	file_append(tp_Out, "\n");
}

// One synthetic scenario on the current bar. Handle = dataset with its states.
void tp_scen(string name, int handle)
{
	if(!asset(name)) { tp_line(strf("ASSETFAIL,%s,%i", name, Bar)); return; }
	int r = dataFind(handle, wdate(0));
	var c1 = 0;
	var c1prev = 0;
	var atr = 0;
	var dd = -1;
	if(r >= 0) {
		dd = wdate(0) - dataVar(handle, r, 0);
		if(dd >= 0 && dd < 1) {
			c1 = dataVar(handle, r, 1);
			atr = dataVar(handle, r, 4);
			if(r + 1 < dataFind(handle, 0)) c1prev = dataVar(handle, r + 1, 1);
		}
	}
	tp_line(strf("BAR,%s,%i,%.8f,%.8f,%.15f,%.15f,%.15f,%.15f,%i,%.8f,%.0f,%.0f,%i,%i",
		name, Bar, wdate(0), ldate(EST, 0), priceOpen(), priceHigh(), priceLow(), priceClose(),
		r, dd, c1, c1prev, NumOpenLong, NumPendingLong));

	// breakeven for the remaining runner (half 1 closed at TP1), set at this close
	if(NumOpenLong == 1) {
		for(open_trades)
			if(0 == strcmp(Asset, name) && TradeIsLong && TradePriceOpen > TradeStopLimit)
				TradeStopLimit = TradePriceOpen;
		asset(name);
	}

	// C1 signal (+1 after -1): two halves, half 1 with TP1, half 2 without
	if(c1 == 1 && c1prev == -1 && NumOpenLong == 0 && NumPendingLong == 0) {
		Lots = 1;
		Stop = nx_StopAtr * atr;
		TakeProfit = nx_Tp1Atr * atr;
		enterLong();
		TakeProfit = 0;
		enterLong();
		tp_line(strf("ENTER,%s,%i,%.15f,%.15f", name, Bar, nx_StopAtr * atr, nx_Tp1Atr * atr));
	}
}

function run()
{
	BarPeriod = nx_BarPeriodMin;
	BarZone = nx_BarZone;
	BarOffset = nx_BarOffsetMin;
	Fill = nx_FillMode;
	Slippage = nx_SlippageSec;
	LookBack = 0;
	StartDate = 20240228;   // 5 warm-up bars before the scenario (Amendment 1)
	EndDate = 20240315;
	set(LOGFILE);

	if(is(INITRUN)) {
		nx_config_init();
		BarPeriod = nx_BarPeriodMin;
		BarZone = nx_BarZone;
		BarOffset = nx_BarOffsetMin;
		Fill = nx_FillMode;
		Slippage = nx_SlippageSec;
		file_delete(tp_Out);
		tp_line("kind,asset,bar,wdate_utc,ldate_est,open,high,low,close,row,dd,c1,c1prev,num_open_long,num_pending_long");
		int rcList = assetList("C:\\Users\\eyalp\\Documents\\fx-trading-systems\\config\\assets\\AssetsNNFX_FX.csv");
		var pip = 1; pip /= 10000;
		var pipCost = 1; pipCost /= 10;
		assetAdd("SYN_A2", 1, 0, 0, 0, pip, pipCost, 0, nx_Leverage, 1000, 0, "SYN_A2");
		assetAdd("SYN_A3", 1, 0, 0, 0, pip, pipCost, 0, nx_Leverage, 1000, 0, "SYN_A3");
		dataNew(2, 0, 0);
		int n2 = dataParse(2, "%w,f1,f2,f3,f4,f5,f6", "History\\SYN_A2_states.csv");
		dataNew(3, 0, 0);
		int n3 = dataParse(3, "%w,f1,f2,f3,f4,f5,f6", "History\\SYN_A3_states.csv");
		tp_line(strf("INFO,assetList_rc=%i,rows_A2=%i,rows_A3=%i,BarOffset=%i,Fill=%i", rcList, n2, n3, BarOffset, Fill));
	}

	tp_scen("SYN_A2", 2);
	tp_scen("SYN_A3", 3);

	// EUR/USD removed (Amendment 2): no year-split M1 history in a synthetic-asset script.

	for(all_trades)
		tp_line(strf("TRD,%s,%i,%i,%i,%i,%i,%.15f,%.15f,%.15f,%.15f,%.15f",
			Asset, Bar, TradeID, (int)TradeIsOpen, TradeBarOpen, TradeBarClose,
			TradePriceOpen, TradePriceClose, TradeStopLimit, TradeProfitLimit, TradeProfit));
}
