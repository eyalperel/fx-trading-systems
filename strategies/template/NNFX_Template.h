// NNFX_Template.h - generic NNFX template engine (Phase 1 step 4, stage S3).
//
// Architecture A (planning chat 2026-11-22): Zorro executes every order and every intrabar fill;
// this file only decides, at each bar close, what to send. It is a port of the reference engine
// (analysis/template/reference_engine.py, run(), step 3), statement for statement, so that S4
// can compare the two trade lists. Rules: docs/template/NNFX_TEMPLATE_DECISIONS.md (T1-T11,
// M-D1..M-D5); Zorro behaviour relied on: docs/template/ZORRO_TRADE_MECHANICS.md.
//
// Engine bar t                          Here
//  1. open: pending exit, then entry      Zorro fills orders sent at the close of t-1 (Fill = 3)
//  2. intrabar: stop before TP1           Zorro's resting Stop / TakeProfit, tick by tick (TICKS)
//  3. close: breakeven / M-D3, trailing,  nx_bar(): observe what Zorro did in bar t, then decide in
//     close-decided exits, entries        the engine's order and send exits / entries / stop moves
//
// Each half carries its own labels in TradeInt[] (codes NX_TI_*, NNFX_Config.h): TradeID is 0
// while a trade is pending (trade.htm), so halves are matched by these tags, never by ID.
// Exit reasons come from Zorro's trade flags (TR_STOPPED / TR_PROFIT / TR_SOLD, trading.h) plus
// the tag of a template exit order; an exit at market not sent by the template is NX_R_END
// (end of history, gotchas 9d.15).
//
// Requires: NNFX_Config.h, NNFX_Slots.h; Hedge = nx_HedgeMode (M-D5: Zorro closes nothing itself).
// No statics: all state is per asset in nx_a* arrays, reset by nx_template_init() at INITRUN
// (gotcha 9b.1). Globals nx_, locals nxt_ (flat namespace, gotcha 1.3).

string nx_LogFile = "Data\\NNFX_Template_log.csv";

int nx_RefusedLog = 1;   // 1: every refused signal writes a REFUSED row; scripts print it in their INFO row (PERF1 Amendment 1, A1.1)

// ---- per-asset settings (copied from the config at init; a batch may override per asset) ----
int nx_aBtfOn[NX_MAXA];
int nx_aContStop[NX_MAXA];
int nx_aMut[NX_MAXA];

// ---- per-asset state: the reference engine's run() locals, one copy per asset ----
int nx_aBar[NX_MAXA];        // t: calls so far for this asset
int nx_aLastC1[NX_MAXA];     // last_c1
int nx_aLastB[NX_MAXA];      // last_b
int nx_aSigL[NX_MAXA];       // c1_sig_bar[LONG], -1 = none
int nx_aSigS[NX_MAXA];       // c1_sig_bar[SHORT], -1 = none
int nx_aWin[NX_MAXA];        // window active
int nx_aWinDir[NX_MAXA];
int nx_aWinStart[NX_MAXA];
int nx_aWinPull[NX_MAXA];
int nx_aChainL[NX_MAXA];     // chain[LONG]
int nx_aChainS[NX_MAXA];     // chain[SHORT]
int nx_aGroup[NX_MAXA];      // number of the last trade (= last_trade); 0 = none yet
int nx_aDir[NX_MAXA];        // last_trade["dir"]
int nx_aReason[NX_MAXA];     // last_trade["reason"]; NX_R_NONE while any half is open
int nx_aKind[NX_MAXA];
var nx_aAtr[NX_MAXA];        // signal-bar ATR, frozen for the trade (T4)
var nx_aEntry[NX_MAXA];      // fill price, read from Zorro
int nx_aFilled[NX_MAXA];
var nx_aStop1[NX_MAXA];      // half 1 stop (never moves)
var nx_aStop2[NX_MAXA];      // runner stop as the template set it
var nx_aTp[NX_MAXA];
int nx_aStopR2[NX_MAXA];     // runner stop_reason
int nx_aTp1Bar[NX_MAXA];     // tp1_bar, -1 = none
int nx_aTrail[NX_MAXA];
var nx_aBest[NX_MAXA];
int nx_aNSameBar[NX_MAXA];   // same_bar_conflicts (T5.2 count)
int nx_aNBeAdv[NX_MAXA];     // be_adverse_exits (M-D3 count)
int nx_aCostInit[NX_MAXA];   // 1 once the asset's base spread is stored
var nx_aSpread0[NX_MAXA];    // base spread of the asset (asset list or script), before the T7 multiplier

int nx_sgn(var nxt_x)
{
	if(nxt_x > 0) return 1;
	if(nxt_x < 0) return -1;
	return 0;
}

string nx_rname(int nxt_r)
{
	if(nxt_r == NX_R_STOP) return "stop";
	if(nxt_r == NX_R_TP1) return "tp1";
	if(nxt_r == NX_R_BE) return "be";
	if(nxt_r == NX_R_TRAIL) return "trail";
	if(nxt_r == NX_R_C1FLIP) return "c1_flip";
	if(nxt_r == NX_R_EXITIND) return "exit_ind";
	if(nxt_r == NX_R_BASELINE) return "baseline";
	if(nxt_r == NX_R_BEADV) return "be_adverse";
	if(nxt_r == NX_R_END) return "end";
	if(nxt_r == NX_R_OTHER) return "other";
	return "none";
}

string nx_kname(int nxt_k)
{
	if(nxt_k == NX_K_C1) return "c1";
	if(nxt_k == NX_K_CONT) return "continuation";
	if(nxt_k == NX_K_BASELINE) return "baseline";
	if(nxt_k == NX_K_PULLBACK) return "pullback";
	return "none";
}

void nx_log(string nxt_s)
{
	file_append(nx_LogFile, nxt_s);
	file_append(nx_LogFile, "\n");
}

// Kind of a refused signal for the REFUSED row (PERF1 A1.1): continuation or standard (every other kind).
string nx_refkind(int nxt_k)
{
	if(nxt_k == NX_K_CONT) return "continuation";
	return "standard";
}

// Reset every per-asset array (INITRUN). Settings start from the config (variant 0).
void nx_template_init()
{
	int nxt_i;
	for(nxt_i = 0; nxt_i < NX_MAXA; nxt_i++) {
		nx_aVolMode[nxt_i] = nx_VolumeMode;
		nx_aExitMode[nxt_i] = nx_ExitMode;
		nx_aBtfOn[nxt_i] = nx_BtfOn;
		nx_aContStop[nxt_i] = nx_ContAfterStop;
		nx_aMut[nxt_i] = nx_CtlMutation;
		nx_aBar[nxt_i] = 0;
		nx_aLastC1[nxt_i] = 0;
		nx_aLastB[nxt_i] = 0;
		nx_aSigL[nxt_i] = -1;
		nx_aSigS[nxt_i] = -1;
		nx_aWin[nxt_i] = 0;
		nx_aWinDir[nxt_i] = 0;
		nx_aWinStart[nxt_i] = 0;
		nx_aWinPull[nxt_i] = 0;
		nx_aChainL[nxt_i] = 0;
		nx_aChainS[nxt_i] = 0;
		nx_aGroup[nxt_i] = 0;
		nx_aDir[nxt_i] = 0;
		nx_aReason[nxt_i] = NX_R_NONE;
		nx_aKind[nxt_i] = 0;
		nx_aAtr[nxt_i] = 0;
		nx_aEntry[nxt_i] = 0;
		nx_aFilled[nxt_i] = 0;
		nx_aStop1[nxt_i] = 0;
		nx_aStop2[nxt_i] = 0;
		nx_aTp[nxt_i] = 0;
		nx_aStopR2[nxt_i] = NX_R_STOP;
		nx_aTp1Bar[nxt_i] = -1;
		nx_aTrail[nxt_i] = 0;
		nx_aBest[nxt_i] = 0;
		nx_aNSameBar[nxt_i] = 0;
		nx_aNBeAdv[nxt_i] = 0;
		nx_aCostInit[nxt_i] = 0;
		nx_aSpread0[nxt_i] = 0;
	}
	Capital = nx_Capital;   // M-D8.3: Equity = Capital + closed + open results (balance.htm)
	if(nx_FillUnrounded) setf(TradeMode, TR_FRC);   // R-D5: no rounding of stops, limits, fills (trademode.htm)
	file_delete(nx_LogFile);
	nx_log("kind,asset,a,b,c,d,e,f,g,h,i,j,k,l,m,n");
}

// Risk sizing per signal (T8, M-D8), asset nxi selected, at the decision close. Returns the lots
// per half (both halves get the same lots), or 0 when the signal is refused; every call writes a
// SIZE row, a refusal also an ERROR row. Order of checks: below 1 lot, configured risk exceeded,
// margin. Locals use the nxz_ prefix (gotchas 1.3).
int nx_size(int nxi, string nxn, int nxz_ymd, var nxz_atr, int nxz_kind)
{
	var nxz_eq = Equity;                                   // M-D8.3, incl. open trades (a) balance.htm
	var nxz_pct = nx_RiskPct / NX_NHALVES;                 // % of equity per half, T8.2
	if(nx_aMut[nxi] == NX_MUT_R2) nxz_pct = nx_RiskPct;    // planted bug (control assets only)
	var nxz_target = nxz_eq * nxz_pct / NX_PCT;            // EUR at risk per half
	var nxz_stopPips = nx_StopAtr * nxz_atr / PIP;
	var nxz_riskLot = nxz_stopPips * PIPCost;              // risk of 1 lot (a) lots.htm; no spread, M-D8.1
	var nxz_raw = nxz_target / nxz_riskLot;
	int nxz_lots = floor(nxz_raw);                         // round down, M-D8.2
	var nxz_actual = nxz_lots * nxz_riskLot;
	var nxz_cap = nxz_eq * nx_RiskPct / NX_NHALVES / NX_PCT;   // configured risk per half: runtime guard
	MarginCost = priceClose(0) * PIPCost / PIP / nx_Leverage;  // M-D8.5 (a) pip.htm
	var nxz_margin = NX_NHALVES * nxz_lots * MarginCost;   // both halves
	nx_log(strf("SIZE,%s,%i,%.6f,%.6f,%.6f,%.15f,%.15f,%.15f,%i,%.6f,%.6f,%.12f,%.15f,%.10f,%i,%.6f,%.10f,%.6f",
		nxn, nxz_ymd, nxz_eq, Balance, MarginTotal, nxz_atr, PIP, PIPCost, (int)LotAmount, nxz_pct,
		nxz_target, nxz_stopPips, nxz_riskLot, nxz_raw, nxz_lots, nxz_actual, MarginCost, nxz_margin));
	if(nxz_lots < 1) {
		nx_log(strf("ERROR,%s,%i,lots,below 1 lot: raw %.10f", nxn, nxz_ymd, nxz_raw));
		nx_log(strf("REFUSED,%s,%i,lots,%s", nxn, nxz_ymd, nx_refkind(nxz_kind)));
		return 0;
	}
	if(nxz_actual > nxz_cap) {
		nx_log(strf("ERROR,%s,%i,risk,actual %.6f above configured %.6f", nxn, nxz_ymd, nxz_actual, nxz_cap));
		nx_log(strf("REFUSED,%s,%i,risk,%s", nxn, nxz_ymd, nx_refkind(nxz_kind)));
		return 0;
	}
	if(MarginTotal + nxz_margin > nxz_eq) {
		nx_log(strf("ERROR,%s,%i,margin,%.6f + %.6f above equity %.6f", nxn, nxz_ymd, MarginTotal, nxz_margin, nxz_eq));
		nx_log(strf("REFUSED,%s,%i,margin,%s", nxn, nxz_ymd, nx_refkind(nxz_kind)));
		return 0;
	}
	return nxz_lots;
}

// One ACCT row per bar, called by the script after its asset loop: account state for the margin
// report (M-D8.5) and the Equity checks of the sizing probe.
void nx_account_row()
{
	nx_log(strf("ACCT,,%i,%i,%.6f,%.6f,%.6f,%i", Bar, ymd(ldate(EST, 0)), Equity, Balance, MarginTotal,
		(int)is(MARGINCALL)));
}

// T7 spread level for asset i (selected): Spread = base x nx_SpreadMult. The base is the asset's
// Spread at its first call (asset list, or a value the script set before this call); recomputing
// from the stored base every bar keeps the multiplier from compounding. Call after asset() and after
// any script cost settings, before nx_bar().
void nx_costs_apply(int i)
{
	if(!nx_aCostInit[i]) {
		nx_aSpread0[i] = Spread;
		nx_aCostInit[i] = 1;
	}
	Spread = nx_aSpread0[i] * nx_SpreadMult;
}

// Exit reason of a closed half (ThisTrade): template order tag first, then Zorro's flags.
int nx_classify()
{
	if(TradeInt[NX_TI_EXITR] != NX_R_NONE) return TradeInt[NX_TI_EXITR];
	if(TradeFlag(TR_PROFIT)) return NX_R_TP1;
	if(TradeFlag(TR_STOPPED)) return TradeInt[NX_TI_STOPR];
	if(TradeFlag(TR_SOLD)) return NX_R_END;
	return NX_R_OTHER;
}

// Tag the trade just returned by enterLong / enterShort (ThisTrade).
void nx_tag(int nxi, int nxt_half)
{
	TradeInt[NX_TI_ASSET] = nxi + 1;
	TradeInt[NX_TI_GROUP] = nx_aGroup[nxi];
	TradeInt[NX_TI_HALF] = nxt_half;
	TradeInt[NX_TI_KIND] = nx_aKind[nxi];
	TradeInt[NX_TI_STOPR] = NX_R_STOP;
	TradeInt[NX_TI_EXITR] = NX_R_NONE;
	TradeInt[NX_TI_LOGGED] = 0;
	TradeInt[NX_TI_ENTYMD] = 0;
}

// One closed bar of asset i (selected by the caller, name = its asset name). Slots must already
// be updated (nx_slots_update). Called once per asset per bar, unconditionally.
void nx_bar(int nxi, string nxn)
{
	int nxt_t = nx_aBar[nxi];
	nx_aBar[nxi] = nxt_t + 1;
	int nxt_ymd = ymd(ldate(EST, 0));
	var nxt_o = priceOpen();
	var nxt_h = priceHigh();
	var nxt_l = priceLow();
	var nxt_c = priceClose();
	int nxt_g = nx_aGroup[nxi];
	int nxt_d = nx_aDir[nxi];

	// ---- observe bar nxt_t (engine steps 1-2 happened inside Zorro) ----
	int nxt_o1 = 0;           // half 1 of the current trade open at this close
	int nxt_o2 = 0;           // runner open at this close
	int nxt_h1Active = 0;     // half 1 was in the market during the bar (same-bar count)
	int nxt_closedNow = 0;    // nxt_a half of the current trade closed in this bar
	int nxt_lastR = NX_R_NONE;
	for(all_trades) {
		if(TradeInt[NX_TI_ASSET] == nxi + 1 && !TradeIsPending) {
			if(TradeInt[NX_TI_ENTYMD] == 0) TradeInt[NX_TI_ENTYMD] = nxt_ymd;   // filled in this bar
			if(TradeInt[NX_TI_GROUP] == nxt_g && !nx_aFilled[nxi]) {
				nx_aEntry[nxi] = TradePriceOpen;
				nx_aFilled[nxi] = 1;
			}
			if(TradeInt[NX_TI_GROUP] == nxt_g && TradeIsOpen) {
				if(TradeInt[NX_TI_HALF] == NX_HALF_TP1) { nxt_o1 = 1; nxt_h1Active = 1; }
				if(TradeInt[NX_TI_HALF] == NX_HALF_RUNNER) nxt_o2 = 1;
			}
			if(TradeIsClosed && TradeInt[NX_TI_LOGGED] == 0) {
				int nxt_r = nx_classify();
				int nxt_td = 1;
				if(!TradeIsLong) nxt_td = -1;
				nx_log(strf("HALF,%s,%i,%i,%i,%s,%i,%.15f,%i,%.15f,%s,%i,%i,%i,%.8f,%.8f,%.8f,%.10f,%.8f",
					nxn, TradeInt[NX_TI_GROUP], TradeInt[NX_TI_HALF], nxt_td,
					nx_kname(TradeInt[NX_TI_KIND]), TradeInt[NX_TI_ENTYMD], TradePriceOpen,
					nxt_ymd, TradePriceClose, nx_rname(nxt_r), g->tr->flags, TradeBarOpen, TradeBarClose,
					(var)TradeProfit, (var)TradeRoll, (var)TradeCommission, TradeSpread, TradeUnits));
				TradeInt[NX_TI_LOGGED] = 1;
				if(TradeInt[NX_TI_GROUP] == nxt_g) {
					nxt_closedNow = 1;
					nxt_lastR = nxt_r;
					if(TradeInt[NX_TI_HALF] == NX_HALF_TP1 && (nxt_r == NX_R_TP1 || nxt_r == NX_R_STOP)) nxt_h1Active = 1;
					if(TradeInt[NX_TI_HALF] == NX_HALF_TP1 && nxt_r == NX_R_TP1) nx_aTp1Bar[nxi] = nxt_t;
				}
			}
		}
	}
	asset(nxn);

	// levels of the current trade from its fill (T4: from the fill price, signal-bar ATR)
	var nxt_a0 = nx_aAtr[nxi];
	if(nxt_g > 0 && nx_aFilled[nxi] && nx_aStop1[nxi] == 0) {
		nx_aStop1[nxi] = nx_aEntry[nxi] - nxt_d * nx_StopAtr * nxt_a0;
		nx_aStop2[nxi] = nx_aStop1[nxi];
		nx_aTp[nxi] = nx_aEntry[nxi] + nxt_d * nx_Tp1Atr * nxt_a0;
	}
	int nxt_open = nxt_o1 || nxt_o2;
	if(nxt_g > 0 && nxt_closedNow && !nxt_open) nx_aReason[nxi] = nxt_lastR;   // last_trade["reason"]

	// same-bar stop and TP1 count (T5.2): half 1 in the market and both levels inside the bar
	if(nxt_h1Active) {
		int nxt_sh = 0;
		int nxt_th = 0;
		if(nxt_d == 1) { nxt_sh = (nxt_l <= nx_aStop1[nxi]); nxt_th = (nxt_h >= nx_aTp[nxi]); }
		if(nxt_d == -1) { nxt_sh = (nxt_h >= nx_aStop1[nxi]); nxt_th = (nxt_l <= nx_aTp[nxi]); }
		if(nxt_sh && nxt_th) nx_aNSameBar[nxi] += 1;
	}

	if(!nx_sOK) {   // no slot values for this bar: observe only, decide nothing
		nx_log(strf("BAR,%s,%i,%i,%i,%i", nxn, Bar, nxt_t, nxt_ymd, nx_sOK));
		return;
	}

	// ---- engine step 3: at the close ----
	int nxt_c1 = nx_sC1;
	int nxt_c2 = nx_sC2;
	int nxt_b = nx_sgn(nxt_c - nx_sBase);
	int nxt_c1sig = 0;
	if(nxt_c1 != 0 && nx_aLastC1[nxi] == -nxt_c1) nxt_c1sig = nxt_c1;
	if(nxt_c1sig == 1) nx_aSigL[nxi] = nxt_t;
	if(nxt_c1sig == -1) nx_aSigS[nxi] = nxt_t;
	if(nxt_c1 != 0) nx_aLastC1[nxi] = nxt_c1;
	int nxt_bcross = 0;
	if(nxt_b != 0 && nx_aLastB[nxi] == -nxt_b) nxt_bcross = nxt_b;
	if(nxt_b != 0) {
		nx_aLastB[nxi] = nxt_b;
		if(nxt_b == 1) nx_aChainS[nxi] = 0;    // chain[-nxt_b] = False
		if(nxt_b == -1) nx_aChainL[nxi] = 0;
	}
	nx_log(strf("BAR,%s,%i,%i,%i,%i,%.15f,%.15f,%.15f,%.15f,%i,%i,%.15f,%.15f,%i,%i",
		nxn, Bar, nxt_t, nxt_ymd, nx_sOK, nxt_o, nxt_h, nxt_l, nxt_c, nxt_c1, nxt_c2, nx_sBase, nx_sAtr, nx_sVol, nx_sEx));

	int nxt_pexit = NX_R_NONE;
	int nxt_stopMoved = 0;

	// breakeven (M-D3) and trailing on the runner, only after TP1
	if(nxt_o2 && nx_aTp1Bar[nxi] >= 0) {
		int nxt_skipTrail = 0;
		if(nx_aTp1Bar[nxi] == nxt_t) {
			if(nxt_d * (nxt_c - nx_aEntry[nxi]) < 0 && nx_aMut[nxi] != NX_MUT_M3) {
				nxt_pexit = NX_R_BEADV;
				nx_aNBeAdv[nxi] += 1;
				nxt_skipTrail = 1;
			} else {
				var nxt_be = nx_aEntry[nxi] + nxt_d * nx_BeOffsetAtr * nxt_a0;
				if(nxt_d * (nxt_be - nx_aStop2[nxi]) > 0) {
					nx_aStop2[nxi] = nxt_be;
					nx_aStopR2[nxi] = NX_R_BE;
					nxt_stopMoved = 1;
				}
			}
		}
		if(!nxt_skipTrail) {
			if(!nx_aTrail[nxi] && nxt_d * (nxt_c - nx_aEntry[nxi]) >= nx_TrailStartAtr * nxt_a0) {
				nx_aTrail[nxi] = 1;
				nx_aBest[nxi] = nxt_c;
			} else {
				if(nx_aTrail[nxi] && nxt_d * (nxt_c - nx_aBest[nxi]) > 0) nx_aBest[nxi] = nxt_c;
			}
			if(nx_aTrail[nxi]) {
				var nxt_nw = nx_aBest[nxi] - nxt_d * nx_TrailDistAtr * nxt_a0;
				if(nxt_d * (nxt_nw - nx_aStop2[nxi]) > 0) {
					nx_aStop2[nxi] = nxt_nw;
					nx_aStopR2[nxi] = NX_R_TRAIL;
					nxt_stopMoved = 1;
				}
			}
		}
	}
	if(nxt_stopMoved) {
		for(open_trades)
			if(TradeInt[NX_TI_ASSET] == nxi + 1 && TradeInt[NX_TI_GROUP] == nxt_g && TradeInt[NX_TI_HALF] == NX_HALF_RUNNER) {
				TradeStopLimit = nx_aStop2[nxi];
				TradeInt[NX_TI_STOPR] = nx_aStopR2[nxi];
			}
		asset(nxn);
		nx_log(strf("STOP,%s,%i,%i,%.15f,%s", nxn, nxt_ymd, nxt_g, nx_aStop2[nxi], nx_rname(nx_aStopR2[nxi])));
	}

	// close-decided exits (T1, T3, T5.5)
	if(nxt_open && nxt_pexit == NX_R_NONE) {
		if(nxt_c1 == -nxt_d) nxt_pexit = NX_R_C1FLIP;
		else if(nx_aExitMode[nxi] == NX_EXIT_IND && nx_sEx == -nxt_d) nxt_pexit = NX_R_EXITIND;
		else if(nxt_b == -nxt_d) nxt_pexit = NX_R_BASELINE;
	}
	if(nxt_pexit != NX_R_NONE) {
		for(open_trades)
			if(TradeInt[NX_TI_ASSET] == nxi + 1 && TradeInt[NX_TI_GROUP] == nxt_g) {
				TradeInt[NX_TI_EXITR] = nxt_pexit;
				exitTrade(ThisTrade);
			}
		asset(nxn);
		nx_log(strf("EXIT,%s,%i,%i,%s", nxn, nxt_ymd, nxt_g, nx_rname(nxt_pexit)));
	}

	// entries (only when nxt_flat after any pending exit)
	int nxt_flat = !nxt_open || nxt_pexit != NX_R_NONE;
	if(nx_aMut[nxi] == NX_MUT_MF) nxt_flat = !nxt_open;
	if(!nxt_flat) return;
	var nxt_a = nx_sAtr;
	int nxt_distOk = abs(nxt_c - nx_sBase) <= nx_BaselineMaxDistAtr * nxt_a;
	int nxt_volOk = nx_sVol;
	int nxt_dec = 0;          // direction of the decided entry, 0 = none
	int nxt_kind = 0;
	int nxt_dd;
	if(nxt_c1sig != 0) {
		nxt_dd = nxt_c1sig;
		int nxt_chainD = nx_aChainS[nxi];
		if(nxt_dd == 1) nxt_chainD = nx_aChainL[nxi];
		int nxt_cont = (!nxt_open && nxt_g > 0 && nx_aDir[nxi] == nxt_dd
			&& nx_aReason[nxi] != NX_R_NONE && nx_aReason[nxi] != NX_R_BASELINE && nxt_chainD
			&& (nx_aContStop[nxi] || nx_aReason[nxi] != NX_R_STOP));
		if(nxt_cont) {
			if(nxt_c2 == nxt_dd && nxt_b != -nxt_dd) { nxt_dec = nxt_dd; nxt_kind = NX_K_CONT; }
		} else {
			if(nxt_b == nxt_dd && nxt_c2 == nxt_dd && nxt_volOk && nxt_distOk) { nxt_dec = nxt_dd; nxt_kind = NX_K_C1; }
		}
	}
	if(nxt_dec == 0 && nxt_bcross != 0) {
		nxt_dd = nxt_bcross;
		int nxt_sig = nx_aSigS[nxi];
		if(nxt_dd == 1) nxt_sig = nx_aSigL[nxi];
		if(nx_aBtfOn[nxi] && nxt_c1 == nxt_dd && nxt_sig >= 0 && nxt_t - nxt_sig >= nx_BtfMaxAgeBars) {
			nx_log(strf("REFUSED,%s,%i,bridge-too-far,standard", nxn, nxt_ymd));
			nx_aWin[nxi] = 0;
		} else {
			nx_aWin[nxi] = 1;
			nx_aWinDir[nxi] = nxt_dd;
			nx_aWinStart[nxi] = nxt_t;
			nx_aWinPull[nxi] = !nxt_distOk;
		}
	}
	if(nxt_dec == 0 && nx_aWin[nxi]) {
		nxt_dd = nx_aWinDir[nxi];
		int nxt_k = nxt_t - nx_aWinStart[nxi];
		int nxt_alive = (nxt_b != -nxt_dd && nxt_c1 != -nxt_dd);
		if(nx_aWinPull[nxi] && nxt_k > nx_PullbackWaitBars) nxt_alive = 0;
		if(nx_CatchupLimitOn && nxt_k > nx_CatchupMaxBars) nxt_alive = 0;
		if(!nxt_alive) {
			nx_aWin[nxi] = 0;
		} else {
			if(nxt_b == nxt_dd && nxt_c1 == nxt_dd && nxt_c2 == nxt_dd && nxt_volOk && nxt_distOk) {
				nxt_dec = nxt_dd;
				nxt_kind = NX_K_BASELINE;
				if(nx_aWinPull[nxi]) nxt_kind = NX_K_PULLBACK;
				nx_aWin[nxi] = 0;
			}
		}
	}
	if(nxt_dec == 0) return;

	// send the entry: two halves, filled at the next open (Fill 3), Stop / TP1 from the fill
	int nxt_lots = nx_FixedLots;   // > 0 only in the S4 / P5 batches
	if(nx_FixedLots <= 0) {
		nxt_lots = nx_size(nxi, nxn, nxt_ymd, nxt_a, nxt_kind);   // T8 / M-D8
		if(nxt_lots < 1) return;   // refused: ERROR row written, signal skipped (c: as if no entry)
	}
	nx_aGroup[nxi] = nxt_g + 1;
	nx_aDir[nxi] = nxt_dec;
	nx_aReason[nxi] = NX_R_NONE;
	nx_aKind[nxi] = nxt_kind;
	nx_aAtr[nxi] = nxt_a;
	nx_aFilled[nxi] = 0;
	nx_aStop1[nxi] = 0;
	nx_aStop2[nxi] = 0;
	nx_aTp[nxi] = 0;
	nx_aStopR2[nxi] = NX_R_STOP;
	nx_aTp1Bar[nxi] = -1;
	nx_aTrail[nxi] = 0;
	nx_aBest[nxi] = 0;
	if(nxt_dec == 1) { nx_aChainL[nxi] = 1; nx_aChainS[nxi] = 0; }
	if(nxt_dec == -1) { nx_aChainS[nxi] = 1; nx_aChainL[nxi] = 0; }
	Lots = nxt_lots;
	Stop = nx_StopAtr * nxt_a;
	TakeProfit = nx_Tp1Atr * nxt_a;
	if(nxt_dec == 1) ThisTrade = enterLong(); else ThisTrade = enterShort();
	if(ThisTrade) nx_tag(nxi, NX_HALF_TP1);
	TakeProfit = 0;
	if(nxt_dec == 1) ThisTrade = enterLong(); else ThisTrade = enterShort();
	if(ThisTrade) nx_tag(nxi, NX_HALF_RUNNER);
	Stop = 0;
	nx_log(strf("ENTER,%s,%i,%i,%i,%s,%.15f", nxn, nxt_ymd, nx_aGroup[nxi], nxt_dec, nx_kname(nxt_kind), nxt_a));
}
