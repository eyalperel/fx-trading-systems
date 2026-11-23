// NNFX_Config.h — every number used by the generic NNFX template (decision T11).
//
// Rules (enforced by tools/lint_literals.py, config mode):
//   - every line holding a number carries its source label: (a) source states,
//     (b) measured, (c) inference, a decision id (T<n>, M-D<n>) or a source key [..];
//   - no decimal literals (Light-C reads them as float32, gotchas 9d.1): non-integers
//     are built from integers at run time, e.g. 1.5 = 3 / 2.
// Values are variant 0 (docs/template/NNFX_TEMPLATE_DECISIONS.md). Changing one is a
// named, counted variant (T11). Source keys: docs/sources/NNFX_Sources.md.
// Strategy-specific indicator settings live in a separate per-strategy config, not here.
// Globals are prefixed nx_ (flat namespace across includes, CLAUDE.md §6).

// ---- bars and fills ----------------------------------------------------------
int    nx_BarPeriodMin;      // daily bars
int    nx_BarZone;           // bar time zone
int    nx_BarOffsetMin;      // bar end offset from BarZone midnight
int    nx_FillMode;          // Zorro Fill mode
int    nx_TicksOn;           // 1 = set(TICKS): intrabar path evaluated, entry-bar exits possible
int    nx_StartWeek;         // Zorro StartWeek (dhhmm in BarZone): start of the trading week
var    nx_SlippageSec;       // Zorro Slippage

// ---- trade management (all in multiples of the entry-bar ATR, frozen per trade) --
int    nx_AtrLen;
var    nx_StopAtr;           // initial stop distance
var    nx_Tp1Atr;            // first target distance
var    nx_Tp1Fraction;       // share of the position closed at TP1
var    nx_BeOffsetAtr;       // breakeven stop offset from entry
var    nx_TrailStartAtr;     // close beyond entry that activates the trail
var    nx_TrailDistAtr;      // trail distance behind the best close

// ---- entry rules ---------------------------------------------------------------
var    nx_BaselineMaxDistAtr;   // max |close - baseline| at entry
int    nx_PullbackWaitBars;     // candles allowed for the one pullback case
int    nx_BtfMaxAgeBars;        // bridge-too-far: skip if C1 signal age >= this
int    nx_CatchupLimitOn;       // 0 = no day limit on baseline catch-up
int    nx_CatchupMaxBars;       // used only if nx_CatchupLimitOn
int    nx_ContAfterStop;        // continuation allowed after a stop-loss exit

// ---- money and costs ------------------------------------------------------------
var    nx_RiskPct;           // % of equity per signal (both halves together)
var    nx_RiskPctMin;        // user range, lower end
var    nx_RiskPctMax;        // user range, upper end
var    nx_Capital;           // starting capital, account currency (EUR, M-D4)
var    nx_Leverage;          // target leverage; see ZORRO_TRADE_MECHANICS (MarginCost check pending)
var    nx_SpreadMult;        // spread multiplier (1 = asset list)
string nx_AssetList;         // asset list file

// ---- engine switches (S3 template, 2026-11-23) -------------------------------------
int    nx_HedgeMode;         // Zorro Hedge
int    nx_FixedLots;         // > 0: fixed lots per half (S4 equivalence); 0: risk sizing T8 (stage P6)
int    nx_BtfOn;             // bridge-too-far rule on / off (per strategy, T3.3)
int    nx_SlotSource;        // where slot states come from (codes below)
int    nx_CtlMutation;       // planted-bug control id; 0 in every real run (codes below)

// ---- codes: identifiers, not parameters (never varied, not sensitivity levels) ------
#define NX_MAXA        64    // max assets per script: S4 batch 60 + 4 controls [capacity]
#define NX_SRC_STRATEGY 0    // slots from the strategy's indicator file [code]
#define NX_SRC_SCRIPTED 1    // slots from a states CSV per asset (S4 scenarios) [code]
#define NX_VOL_YES     0     // volume ALWAYS_YES, T2 [code]
#define NX_VOL_NO      1     // volume ALWAYS_NO guard stub, T2 [code]
#define NX_VOL_IND     2     // volume indicator state [code]
#define NX_EXIT_NONE   0     // exit slot NONE, T1 [code]
#define NX_EXIT_IND    1     // exit indicator state, T1 [code]
#define NX_MUT_NONE    0     // no planted bug [code]
#define NX_MUT_M3      1     // control: breakeven placed without the M-D3 check [code]
#define NX_MUT_MF      2     // control: entry only when no trade is open [code]
#define NX_R_NONE      0     // exit reasons [code]
#define NX_R_STOP      1     // [code]
#define NX_R_TP1       2     // [code]
#define NX_R_BE        3     // [code]
#define NX_R_TRAIL     4     // [code]
#define NX_R_C1FLIP    5     // [code]
#define NX_R_EXITIND   6     // [code]
#define NX_R_BASELINE  7     // [code]
#define NX_R_BEADV     8     // M-D3 runner exit [code]
#define NX_R_END       9     // closed at market by Zorro, not by the template (end of history, gotchas 9d.15) [code]
#define NX_R_OTHER     10    // any other close: never expected [code]
#define NX_K_C1        1     // entry kinds [code]
#define NX_K_CONT      2     // [code]
#define NX_K_BASELINE  3     // [code]
#define NX_K_PULLBACK  4     // [code]
#define NX_TI_ASSET    0     // TradeInt slots carried by each half: asset index + 1 [code]
#define NX_TI_GROUP    1     // trade number within the asset [code]
#define NX_TI_HALF     2     // 1 = TP1 half, 2 = runner [code]
#define NX_TI_KIND     3     // entry kind [code]
#define NX_TI_STOPR    4     // reason if its stop fires: stop / be / trail [code]
#define NX_TI_EXITR    5     // reason of a template exit order, 0 if none [code]
#define NX_TI_LOGGED   6     // 1 once its HALF row is written [code]
#define NX_TI_ENTYMD   7     // YYYYMMDD of the bar it filled in (New York date) [code]
#define NX_HALF_TP1    1     // half closed at TP1 [code]
#define NX_HALF_RUNNER 2     // half that runs to breakeven / trail [code]
#define NX_SC_C1       1     // states CSV columns after the %w timestamp (tools/make_scenarios.py) [code]
#define NX_SC_C2       2     // [code]
#define NX_SC_BASE     3     // [code]
#define NX_SC_ATR      4     // [code]
#define NX_SC_VOL      5     // [code]
#define NX_SC_EX       6     // [code]

// ---- slot switches ----------------------------------------------------------------
int    nx_ExitMode;          // 0 = NONE (exit only by C1 flip, baseline, stops)
int    nx_VolumeMode;        // 0 = ALWAYS_YES, 1 = ALWAYS_NO (guard test only), 2 = indicator
int    nx_NewsOn;            // news rules
int    nx_DeadMarketOn;      // dead-market mode

void nx_config_init()
{
	nx_BarPeriodMin = 1440;              // (a) daily chart [V05, V15]
	nx_BarZone = EST;                     // M-D1 New York, DST-aware
	nx_BarOffsetMin = 17; nx_BarOffsetMin *= 60; // M-D1 bars close 17:00 New York (A17)
	nx_FillMode = 3;                      // T4 next-bar open (Zorro 3.11 fill.htm)
	nx_TicksOn = 1;                       // T5 amendment 2026-11-22 (mode.htm TICKS; gotchas 9d.12)
	nx_StartWeek = 71700;                 // Sunday 17:00 New York, M-D6; (b) EURUSD 2024 first quote Sun 17:01-17:09 NY
	nx_SlippageSec = 0;                   // M-D2 (sensitivity level: 5)

	nx_AtrLen = 14;                       // (a) [V03, V16]
	nx_StopAtr = 3; nx_StopAtr /= 2;      // 1.5 (a) [V25, M3]
	nx_Tp1Atr = 1;                        // (a) [V25, C17, M13]
	nx_Tp1Fraction = 1; nx_Tp1Fraction /= 2; // one half (a) [V25]; T8
	nx_BeOffsetAtr = 0;                   // stop exactly at entry (a) [M6]
	nx_TrailStartAtr = 2;                 // on a close (a) [M13]
	nx_TrailDistAtr = 3; nx_TrailDistAtr /= 2; // 1.5 behind best close (a) [M13]

	nx_BaselineMaxDistAtr = 1;            // (a) [V28]
	nx_PullbackWaitBars = 1;              // (a) [V28]
	nx_BtfMaxAgeBars = 7;                 // skip if age >= 7 (a) [V34]; T10
	nx_CatchupLimitOn = 0;                // no day limit (c) T10
	nx_CatchupMaxBars = 3;                // sensitivity level only (c) T10, T11
	nx_ContAfterStop = 1;                 // (c) T9

	nx_RiskPct = 2;                       // (a) [M3]
	nx_RiskPctMin = 3; nx_RiskPctMin /= 10; // 0.3, user range 2026-11-01 [NNFX_Sources]
	nx_RiskPctMax = 2;                    // user range 2026-11-01 [NNFX_Sources]
	nx_Capital = 100000;                  // EUR, M-D4
	nx_Leverage = 20;                     // (a) [M14]
	nx_SpreadMult = 1;                    // T7 (stress level: 2)
	nx_AssetList = "AssetsNNFX_FX";       // M-D4; load path checked in S3

	nx_HedgeMode = 2;                     // full hedging: Zorro closes nothing itself, M-D5
	nx_FixedLots = 0;                     // risk sizing T8 (P6); S4 batch sets 1 (c)
	nx_BtfOn = 1;                         // Strategy 1, two-lines-cross C1 [V34]; T3.3 (Strategy 2: 0)
	nx_SlotSource = NX_SRC_STRATEGY;      // T3 slot interface
	nx_CtlMutation = NX_MUT_NONE;         // S4 decision 4, 2026-11-23: controls only

	nx_ExitMode = 0;                      // NONE, T1
	nx_VolumeMode = 0;                    // ALWAYS_YES, T2
	nx_NewsOn = 0;                        // off, no current calendar [B G5]
	nx_DeadMarketOn = 0;                  // off (user 2026-11-01) [NNFX_Sources]
}
