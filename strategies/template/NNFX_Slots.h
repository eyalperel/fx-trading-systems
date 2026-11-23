// NNFX_Slots.h - slot interface of the generic NNFX template (decision T3).
//
// Every slot reports one value per closed bar for the asset being processed:
//   C1, C2, exit : state +1 / -1 / 0 (0 = exactly on the line, indeterminate; T3.1)
//   baseline     : the baseline value (its state is sign(close - baseline), computed by the template)
//   ATR          : the ATR value used for stops, targets and distances (T4, T10.3)
//   volume       : 1 = go, 0 = no-go (T2)
// The template reads only these globals (nx_s*), so a strategy changes by its slot source,
// never by editing NNFX_Template.h.
//
// Sources (nx_SlotSource, NNFX_Config.h):
//   NX_SRC_SCRIPTED  states read from a CSV per asset (S4 scenarios: tools/make_scenarios.py
//                    writes History/SYN_<name>_states.csv, columns %w,c1,c2,baseline,atr,vol,ex,
//                    one row per bar stamped one hour before the bar's 17:00 New York close).
//   NX_SRC_STRATEGY  a strategy file defines NX_HAVE_STRATEGY_SLOTS and the function
//                    nx_strategy_slots(int i), included BEFORE this file. Its indicator calls
//                    must run on every bar with no condition around them (gotcha 3.1).
// Volume and exit modes then filter the raw states (T1, T2): NONE / ALWAYS_YES / ALWAYS_NO.
//
// Requires: NNFX_Config.h. Globals and locals prefixed nx_ / nxs_ (flat namespace, gotcha 1.3).

int nx_sC1;       // C1 state
int nx_sC2;       // C2 state
int nx_sEx;       // exit-slot state after the exit mode
int nx_sVol;      // volume go / no-go after the volume mode
var nx_sBase;     // baseline value
var nx_sAtr;      // ATR value
int nx_sOK;       // 1 = every slot delivered a value for this bar

int nx_aVolMode[NX_MAXA];     // per-asset volume mode (NX_VOL_*), set by nx_slots_init / batch
int nx_aExitMode[NX_MAXA];    // per-asset exit mode (NX_EXIT_*)

// Load the states CSV of asset i into dataset handle i + 1 (handles 1..1000, data.htm).
// Returns the number of rows read (0 = file missing or wrong format).
int nx_slots_load(int i, string nxs_file)
{
	dataNew(i + 1, 0, 0);
	return dataParse(i + 1, "%w,f1,f2,f3,f4,f5,f6", nxs_file);
}

// Scripted states for the current bar: the row whose timestamp lies in the last day before
// the bar's close (TPL_Probe runs 3-6: same lookup, dd in [0, 1) day).
void nxs_scripted(int i)
{
	int nxs_r = dataFind(i + 1, wdate(0));
	if(nxs_r < 0) return;
	var nxs_dd = wdate(0) - dataVar(i + 1, nxs_r, 0);
	if(nxs_dd < 0 || nxs_dd >= 1) return;
	nx_sC1 = dataVar(i + 1, nxs_r, NX_SC_C1);
	nx_sC2 = dataVar(i + 1, nxs_r, NX_SC_C2);
	nx_sBase = dataVar(i + 1, nxs_r, NX_SC_BASE);
	nx_sAtr = dataVar(i + 1, nxs_r, NX_SC_ATR);
	nx_sVol = dataVar(i + 1, nxs_r, NX_SC_VOL);
	nx_sEx = dataVar(i + 1, nxs_r, NX_SC_EX);
	nx_sOK = 1;
}

// Fill nx_s* for asset i on the current bar. Called once per asset per bar, unconditionally.
void nx_slots_update(int i)
{
	nx_sOK = 0;
	nx_sC1 = 0; nx_sC2 = 0; nx_sEx = 0; nx_sVol = 0;
	nx_sBase = 0; nx_sAtr = 0;
#ifdef NX_HAVE_STRATEGY_SLOTS
	nx_strategy_slots(i);      // always called: its series() must not depend on the source switch
	if(nx_SlotSource == NX_SRC_STRATEGY) nx_sOK = 1;
#endif
	if(nx_SlotSource == NX_SRC_SCRIPTED) nxs_scripted(i);
	if(nx_sAtr <= 0) nx_sOK = 0;   // no stop can be placed without a positive ATR

	// volume mode (T2): ALWAYS_YES variant 0, ALWAYS_NO guard stub, or the slot's state
	if(nx_aVolMode[i] == NX_VOL_YES) nx_sVol = 1;
	if(nx_aVolMode[i] == NX_VOL_NO) nx_sVol = 0;
	// exit mode (T1): NONE = variant 0, no exit signal ever
	if(nx_aExitMode[i] == NX_EXIT_NONE) nx_sEx = 0;
}
