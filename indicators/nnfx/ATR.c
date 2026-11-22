// ATR.c -- Average True Range, MetaTrader 4 definition (NNFX "ATR 14, default settings")
//
// Source (a): MetaQuotes ATR.mq4 (MetaTrader 4, MQL4/Indicators; installed copies sha256 134da529e0382b89... / c5c680c466e7d87f...,
//   code identical; docs/harness/ATR_SOURCE_REVIEW.md section 2):
//   TR = max(High, Close[1]) - min(Low, Close[1]); ATR = simple Length-bar mean of TR, kept as a running sum;
//   row 0 TR = 0; ATR = 0 on the instance's rows 0..Length-1; row Length = mean of TR[1..Length]. Default Length 14.
//   This is NNFX's "ATR 14, default settings" (docs/sources/NNFX_Sources.md A section 2.1, B section 1.4; VP's charts are MT4)
//   (c: the MT4 identification is the review's inference, review section 2).
// (a) Not Zorro's ATR() (Wilder's recursive form, manual ta.htm). Equal in definition to Zorro's ATRS() (SMA of TrueRange), which
//   reads the asset's own prices and cannot take caller series.
// (b) Behaviour (review section 3, spec observations): exact known answers (flat 0; constant-range bars 2h; close-only ramp = slope);
//   a 14- vs 15-bar window differs by 2-8% of the ATR level; Wilder vs this differs by up to 2-4% on band sines (0 when TR is constant);
//   the first Length bars are 0, so a strategy's LookBack must cover Length + 1 bars (c).
// (a) NNFX use (template, step 4): stop 1.5 x ATR, TP1 1 x ATR, trailing after a close 2 x ATR beyond entry, trail 1.5 x ATR,
//   size = risk / (1.5 x ATR), entry only within 1 x ATR of the baseline; the entry bar's ATR is frozen for the trade.
//   Not implemented here.
// Caller requirements (b, by construction): High / Low / Close series of at least 2 values (the core reads Close[1] only);
//   call unconditionally every bar (gotchas 3.1); Length >= 1 integer.
// STATE: no statics; every series() call unconditional and first; per-instance state and counter (gotchas 9d.9); explicit
//   series lengths (9d.10; series(0, Length + 2)).
// Verification line: analysis/harness/specs/ATR_MT4Fidelity.toml (pre-registered bd62493). NOT VERIFIED until that run passes.
// Prefixes: at_ (ATRMT4Core), atw_ (ATRMT4 wrapper).

var ATRMT4Core(vars High, vars Low, vars Close, int Length, var* pTR)
{
    vars at_n  = series(0, 2);            // per-instance CurrentBar (9d.9); row r = at_n[0] - 1
    vars at_TR = series(0, Length + 2);   // explicit length (9d.10): reads at_TR[Length]
    vars at_A  = series(0, 2);
    var at_th = 0;
    var at_tl = 0;
    var at_s  = 0;
    int at_i;
    at_n[0] = at_n[1] + 1;
    at_TR[0] = 0;                         // row 0: no previous close (ATR.mq4 line 76)
    at_A[0] = 0;                          // rows 0..Length-1: 0 (lines 77, 85)
    if(at_n[0] > 1) {
        at_th = High[0];
        if(Close[1] > at_th) at_th = Close[1];
        at_tl = Low[0];
        if(Close[1] < at_tl) at_tl = Close[1];
        at_TR[0] = at_th - at_tl;         // line 80 / 98
    }
    if(at_n[0] == Length + 1) {           // row Length: mean of TR[1..Length] (lines 83-90)
        for(at_i = 0; at_i < Length; at_i++)
            at_s = at_s + at_TR[at_i];
        at_A[0] = at_s/Length;
    }
    if(at_n[0] > Length + 1)              // line 99, running form kept (AT-4)
        at_A[0] = at_A[1] + (at_TR[0] - at_TR[Length])/Length;
    *pTR = at_TR[0];
    return at_A[0];
}

var ATRMT4(vars High, vars Low, vars Close, int Length)
{
    var atw_1;
    return ATRMT4Core(High, Low, Close, Length, &atw_1);
}
