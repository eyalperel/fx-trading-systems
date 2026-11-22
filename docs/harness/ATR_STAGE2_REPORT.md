# ATR stage 2 report: ATR.c, series-length probe, cross-check script, pre-run records (Amendment 1), generated script

Written for: the planning chat and the user, who reviews before committing. Claude Code (Sonnet), 2026-11-22, branch `harness-atr`, base `bd62493`.
Brief: `docs/harness/ATR_STAGE2_PROMPT.md`. Nothing is committed and Zorro was not run. Labels: (a) source states, (b) measured here, (c) inference.

## 1. Summary

- Written: `indicators/nnfx/ATR.c` (new folder), `strategies/tests/PROBE_SeriesExprLen.c` + `analysis/harness/tools/check_probe_series_len.py`,
  `strategies/tests/XCHK_ATRMT4_vs_ATRS.c` + `analysis/harness/tools/check_xchk_atr.py`, `analysis/harness/tests/test_atr_corrected_code.py`,
  `analysis/harness/tests/test_atr_tools.py`, the gotchas 1.3 prefixes, `[amendment_1]` + `[prerun]` in the spec, the generated script
  `strategies/tests/GEN_ATR_MT4.c`.
- Generator: **not changed** (section 7). One stage 1 test was updated (section 7), not a criterion.
- Pre-run i, ii, iii, iv, v, vii PASS. **vi is pending** the probe click (`cond_vi` holds the literal text the brief asks for).
- Suite: TOTAL 926 PASS 926 before; TOTAL 950 PASS 950 FAIL 0 ERROR 0 after (section 9).
- Nothing in the Zorro window has been seen: none of the three Zorro scripts (probe, main, cross-check) has been compiled. Everything about them is read-through only.

## 2. Click order for the user (restart Zorro before each; Zorro's script folder = repo `strategies/tests/`)

1. `PROBE_SeriesExprLen` (one [Test] click) -> `python analysis/harness/tools/check_probe_series_len.py` (default path `C:/Zorro/Data/PROBE_SeriesExprLen.csv`),
   tell the planning chat; it records `[prerun].cond_vi`. A compile `Error` line or a PASS-less checker = STOP, switch to the fixed `series(0, 64)` fallback by amendment.
2. Commit (the one command at the end of this report, after the planning chat has recorded cond_vi).
3. Planning-chat prediction committed.
4. `GEN_ATR_MT4` (the main run, one click). Raw file `C:/Zorro/Data/GEN_ATR_raw.csv`; copy it to `GEN_ATR_raw_run1.csv` afterwards and record the sha256 (CLAUDE.md 7).
5. `XCHK_ATRMT4_vs_ATRS` (one click, read after the main run) -> `python analysis/harness/tools/check_xchk_atr.py`.
Every run card: expect no line starting with `Error` in the Zorro window (Warning 047 on EUR/USD D1 is harmless, gotchas 9d.7).

## 3. `indicators/nnfx/ATR.c` (full text)


```c
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
```

Function bodies are the spec's `[corrected_code].lines` and `.wrapper_lines`, verbatim (asserted by test, section 6). The header is comments only, each statement labelled (a) / (b) / (c).

## 4. Pre-run (vi) probe

### 4.1 `strategies/tests/PROBE_SeriesExprLen.c` (full text)


```c
// PROBE_SeriesExprLen.c -- ATR stage 2, pre-run (vi): does series(0, L + 2), a length that is a parameter EXPRESSION, compile in
// Zorro 3.11 Light-C, and does every CALL of the same function get its own series slot?
// Pre-registration: analysis/harness/specs/ATR_MT4Fidelity.toml [prerun].cond_vi / pass_condition (vi); brief docs/harness/ATR_STAGE2_PROMPT.md section 2.
// Not an indicator test: a probe. The checker analysis/harness/tools/check_probe_series_len.py gives PASS / FAIL.
// Clock: EUR/USD D1, StartDate 20080101 / EndDate 20240101 as the generated script (Warning 047 expected, gotchas 9d.7). Inputs: per-script bar counter pse_bar (integer, from 1). Call 1: pse_f(14, bar); call 2: pse_f(20, 1000 + bar); unconditional, fixed order.
// pse_f writes x into slot 0 of series(0, L + 2) and returns the OLDEST slot [L + 1].
// Output: Data/PROBE_SeriesExprLen.csv: header "bar,r14,r20", one row per bar, 60 rows, %.15e; written before quit() (gotchas 9d.4).
//   The file is never overwritten: if it exists at INITRUN, the script refuses (prints REFUSED, writes nothing). Delete it by hand to rerun.
// Expected (b, by construction; pre-registered in the brief): r14 = bar - 15 for bar > 15; r20 = 1000 + bar - 21 for bar > 21;
//   earlier rows 0 (series(0, n) starts at 0, gotchas 9d.6). Padding other than 0 is a finding to report, not a failure.
// Run card: pick PROBE_SeriesExprLen in the Script dropdown (folder: repo strategies/tests/), restart Zorro first, ONE [Test] click.
//   Expect no line starting with `Error` in the Zorro window; the last message is "PROBE_SeriesExprLen: 60 rows written".
#include <default.c>

#define PSE_FILE "Data/PROBE_SeriesExprLen.csv"
#define PSE_NBARS 60

static int pse_bar = 0;
static int pse_done = 0;
static int pse_refuse = 0;

var pse_f(int L, var x)
{
    vars pse_s = series(0, L + 2);
    pse_s[0] = x;
    return pse_s[L + 1];
}

void run()
{
    BarPeriod = 1440;
    StartDate = 20080101;
    EndDate   = 20240101;
    LookBack  = 0;
    asset("EUR/USD");

    if(is(INITRUN)) {
        pse_bar = 0; pse_done = 0; pse_refuse = 0;      // declared initialisers (9b)
        if(file_length(PSE_FILE) > 0) {                 // no-overwrite guard
            pse_refuse = 1;
            printf("\nPROBE_SeriesExprLen REFUSED: %s exists; delete it to rerun", PSE_FILE);
        }
        return;
    }
    if(is(EXITRUN)) return;
    if(pse_refuse || pse_done) return;

    pse_bar = pse_bar + 1;
    var bar = pse_bar;                                  // integer-built (no literal)
    var r14 = pse_f(14, bar);                           // call 1
    var r20 = pse_f(20, 1000 + bar);                    // call 2
    if(pse_bar == 1)
        file_append(PSE_FILE, "bar,r14,r20\n", 0);
    file_append(PSE_FILE, strf("%d,%.15e,%.15e\n", pse_bar, r14, r20), 0);
    if(pse_bar >= PSE_NBARS) {
        pse_done = 1;
        printf("\nPROBE_SeriesExprLen: %d rows written", pse_bar);
        quit("PROBE_SeriesExprLen done");
    }
}
```

Read-through: `pse_f(int L, var x)` allocates `series(0, L + 2)` and returns the oldest slot `[L + 1]`; per bar two unconditional calls in fixed order (call 1 `pse_f(14, bar)`,
call 2 `pse_f(20, 1000 + bar)`), `bar` an integer counter from 1; INITRUN returns before any `series()` call; CSV `bar,r14,r20` with `%.15e`; rows are written before `quit()`; 60 bars.
Expected (pre-registered in the brief): r14 = bar - 15 for bar > 15, r20 = 1000 + bar - 21 for bar > 21, earlier rows 0.

### 4.2 `analysis/harness/tools/check_probe_series_len.py` (full text)


```python
"""Checker for strategies/tests/PROBE_SeriesExprLen.c (ATR stage 2, pre-run (vi)).

  python analysis/harness/tools/check_probe_series_len.py [Data/PROBE_SeriesExprLen.csv]

Expected (b, by construction; brief docs/harness/ATR_STAGE2_PROMPT.md section 2): columns bar,r14,r20; bar = 1..60 contiguous;
r14 = bar - 15 for bar > 15, r20 = 1000 + bar - 21 for bar > 21; earlier rows 0. A padding value other than 0 is INFO (a finding),
not a failure. Prints PASS / FAIL with the first mismatching row; exit code 0 = PASS, 1 = FAIL.
"""
import csv
import sys

TOL = 1e-9
NBARS = 60


def expected(bar):
    e14 = bar - 15 if bar > 15 else 0
    e20 = 1000 + bar - 21 if bar > 21 else 0
    return e14, e20


def check(rows):
    """rows: list of (bar, r14, r20) floats. Returns (result, message, infos)."""
    infos = []
    if len(rows) != NBARS:
        return "FAIL", "expected %d rows, got %d" % (NBARS, len(rows)), infos
    for k, (bar, r14, r20) in enumerate(rows):
        if bar != k + 1:
            return "FAIL", "row %d: bar %r, expected %d (not contiguous from 1)" % (k, bar, k + 1), infos
        e14, e20 = expected(k + 1)
        for name, got, want in (("r14", r14, e14), ("r20", r20, e20)):
            if not abs(got - want) <= TOL:                   # NaN fails too
                pad = (name == "r14" and bar <= 15) or (name == "r20" and bar <= 21)
                if pad:
                    infos.append("INFO padding row bar=%d %s = %r (expected 0)" % (bar, name, got))
                    continue
                return "FAIL", "first mismatch: row bar=%d %s = %r, expected %r" % (bar, name, got, want), infos
    return "PASS", "r14 = bar - 15 (bar > 15) and r20 = 1000 + bar - 21 (bar > 21) on all %d rows; separate slots per call" % NBARS, infos


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.reader(fh)
        header = next(r)
        if header != ["bar", "r14", "r20"]:
            raise ValueError("unexpected header %r" % header)
        return [(int(a), float(b), float(c)) for a, b, c in r]


def main(argv):
    path = argv[1] if len(argv) > 1 else "C:/Zorro/Data/PROBE_SeriesExprLen.csv"
    try:
        rows = read(path)
    except (OSError, ValueError) as e:
        print("FAIL: cannot read %s: %s" % (path, e))
        return 1
    res, msg, infos = check(rows)
    for i in infos:
        print(i)
    print("%s: %s" % (res, msg))
    return 0 if res == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

Evidence (`test_atr_tools.py`, TestProbeChecker, 6 tests, all pass; the `[fire]` lines are printed by the tests):
- good synthetic file: PASS, 0 INFO;
- calls swapped (r14 and r20 exchanged): `FAIL: first mismatch: row bar=16 r14 = 0.0, expected 1`;
- one value off at bar 41: `FAIL: first mismatch: row bar=41 r14 = 27.0, expected 26`;
- padding 7 instead of 0 in r14, rows 1..15: PASS with 15 INFO lines (`INFO padding row bar=1 r14 = 7.0 (expected 0)`), as the brief says (a padding other than 0 is reported, not a failure);
- NaN, 59 rows, a non-contiguous bar column: each FAIL;
- command line on a good file (exit 0, PASS), a swapped file (exit 1, FAIL) and a missing file (exit 1).

## 5. Cross-check (S8, AT-5)

### 5.1 `strategies/tests/XCHK_ATRMT4_vs_ATRS.c` (full text)


```c
// XCHK_ATRMT4_vs_ATRS.c -- ATR stage 2, real-data cross-check S8 / AT-5: ATRMT4 (indicators/nnfx/ATR.c) against Zorro's ATRS(14).
// Pre-registration: analysis/harness/specs/ATR_MT4Fidelity.toml [cross_check] (criterion: on rows >= 100, max relative |diff| <= 1e-9, (c));
//   brief docs/harness/ATR_STAGE2_PROMPT.md section 3.
// Inputs: EUR/USD D1 (dev set), Zorro history, StartDate 20100101, EndDate 20240101, LookBack = 100 (c: >= 100 per the spec).
// Per bar, unconditionally and BEFORE the lookback return (gotchas 4.1): series(priceHigh/Low/Close(), 16), ATRMT4(.., 14), ATRS(14).
// Output: Data/XCHK_ATR_raw.csv: every bar incl. lookback bars (flag): date,bar,lookback,atrmt4,atrs,absdiff,reldiff,close ; %.15e.
//   reldiff = absdiff / atrs, 0 when atrs = 0. `close` is the (b) magnitude guard column for the checker (wrong asset): 0.8 .. 1.7.
//   Never overwritten: if the file exists at INITRUN the script refuses (prints REFUSED, writes nothing). Rows are written bar by bar.
// Checker: analysis/harness/tools/check_xchk_atr.py. Not run in stage 2.
// Run card: after the main run (GEN_ATR_MT4); pick XCHK_ATRMT4_vs_ATRS (folder: repo strategies/tests/), restart Zorro first, ONE [Test] click.
//   Expect no line starting with `Error` in the Zorro window.
#include <default.c>
#include "../../indicators/nnfx/ATR.c"

#define XA_FILE "Data/XCHK_ATR_raw.csv"

static int xa_bar = 0;
static int xa_hdr = 0;
static int xa_refuse = 0;

void run()
{
    BarPeriod = 1440;
    StartDate = 20100101;
    EndDate   = 20240101;
    LookBack  = 100;
    asset("EUR/USD");

    if(is(INITRUN)) {
        xa_bar = 0; xa_hdr = 0; xa_refuse = 0;          // declared initialisers (9b)
        if(file_length(XA_FILE) > 0) {                  // no-overwrite guard
            xa_refuse = 1;
            printf("\nXCHK_ATR REFUSED: %s exists; move or delete it to rerun", XA_FILE);
        }
        return;
    }
    if(is(EXITRUN)) return;
    if(xa_refuse) return;

    vars xa_h = series(priceHigh(), 16);
    vars xa_l = series(priceLow(), 16);
    vars xa_c = series(priceClose(), 16);
    var xa_m = ATRMT4(xa_h, xa_l, xa_c, 14);
    var xa_z = ATRS(14);

    int xa_lb = 0;
    if(is(LOOKBACK)) xa_lb = 1;
    var xa_d = abs(xa_m - xa_z);
    var xa_r = 0;
    if(xa_z != 0) xa_r = xa_d / xa_z;

    if(!xa_hdr) {
        file_append(XA_FILE, "date,bar,lookback,atrmt4,atrs,absdiff,reldiff,close\n", 0);
        xa_hdr = 1;
    }
    file_append(XA_FILE, strf("%d,%d,%d,%.15e,%.15e,%.15e,%.15e,%.15e\n",
        ymd(wdate()), xa_bar, xa_lb, xa_m, xa_z, xa_d, xa_r, xa_c[0]), 0);
    xa_bar = xa_bar + 1;
}
```

Read-through: the three `series(price(), 16)` calls, `ATRMT4(..., 14)` and `ATRS(14)` come before any return and are unconditional (gotchas 4.1); the lookback bars are exported too (flag column);
`LookBack = 100` and the exporter does not need the usual `if(is(LOOKBACK)) return;`, because every bar is a row. Header once (`xa_hdr`), no-overwrite guard at INITRUN, statics reset at INITRUN.

### 5.2 `analysis/harness/tools/check_xchk_atr.py` (full text)


```python
"""Checker for strategies/tests/XCHK_ATRMT4_vs_ATRS.c (ATR stage 2, S8 / AT-5).

  python analysis/harness/tools/check_xchk_atr.py [Data/XCHK_ATR_raw.csv]

Criterion (spec [cross_check], (c)): on rows with bar index >= 100, max relative |ATRMT4 - ATRS| <= 1e-9. Relative = |diff| / ATRS, recomputed here
from the two exported values (0 when ATRS = 0); the exported reldiff column is cross-read. Prints PASS / FAIL, the max row, and
the number of rows > 1e-12 relative (INFO). Also FAIL: header mismatch, bar index not contiguous from 0, fewer than 101 rows, a
NaN / infinite value, a close outside 0.8 .. 1.7 (wrong-asset guard, (b) h1_check CLOCK_LO / CLOCK_HI). Exit code 0 = PASS, 1 = FAIL.
"""
import csv
import math
import sys

HEADER = ["date", "bar", "lookback", "atrmt4", "atrs", "absdiff", "reldiff", "close"]
FROM_ROW = 100
LIMIT = 1e-9
INFO_LIMIT = 1e-12
CLOCK_LO, CLOCK_HI = 0.8, 1.7


def check(rows):
    """rows: list of dicts (date, bar int; the rest float). Returns (result, message, info)."""
    info = {}
    if len(rows) <= FROM_ROW:
        return "FAIL", "only %d rows; need more than %d" % (len(rows), FROM_ROW), info
    for k, r in enumerate(rows):
        if r["bar"] != k:
            return "FAIL", "row %d: bar index %r, expected %d" % (k, r["bar"], k), info
        for key in ("atrmt4", "atrs", "absdiff", "reldiff", "close"):
            if not math.isfinite(r[key]):
                return "FAIL", "row %d: %s is not finite (%r)" % (k, key, r[key]), info
        if not (CLOCK_LO <= r["close"] <= CLOCK_HI):
            return "FAIL", "row %d (date %d): close %r outside %s .. %s (wrong asset?)" % (k, r["date"], r["close"], CLOCK_LO, CLOCK_HI), info
    worst, worst_row, n_info = -1.0, None, 0
    for r in rows[FROM_ROW:]:
        rel = 0.0 if r["atrs"] == 0 else abs(r["atrmt4"] - r["atrs"]) / abs(r["atrs"])
        if rel > INFO_LIMIT:
            n_info += 1
        if rel > worst:
            worst, worst_row = rel, r
    info = {"max_rel": worst, "max_row": worst_row, "n_gt_1e-12": n_info, "n_rows_checked": len(rows) - FROM_ROW}
    if worst <= LIMIT:
        return "PASS", "max relative |diff| %.3e <= %.0e on %d rows (bar >= %d)" % (worst, LIMIT, len(rows) - FROM_ROW, FROM_ROW), info
    return "FAIL", "max relative |diff| %.3e > %.0e at bar %d (date %d)" % (worst, LIMIT, worst_row["bar"], worst_row["date"]), info


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.reader(fh)
        header = next(r)
        if header != HEADER:
            raise ValueError("unexpected header %r" % header)
        out = []
        for a in r:
            out.append(dict(date=int(a[0]), bar=int(a[1]), lookback=int(a[2]), atrmt4=float(a[3]), atrs=float(a[4]),
                            absdiff=float(a[5]), reldiff=float(a[6]), close=float(a[7])))
        return out


def main(argv):
    path = argv[1] if len(argv) > 1 else "C:/Zorro/Data/XCHK_ATR_raw.csv"
    try:
        rows = read(path)
    except (OSError, ValueError) as e:
        print("FAIL: cannot read %s: %s" % (path, e))
        return 1
    res, msg, info = check(rows)
    if info:
        w = info["max_row"]
        print("INFO max row: bar %d date %d atrmt4 %r atrs %r" % (w["bar"], w["date"], w["atrmt4"], w["atrs"]))
        print("INFO rows with relative |diff| > 1e-12: %d of %d" % (info["n_gt_1e-12"], info["n_rows_checked"]))
    print("%s: %s" % (res, msg))
    return 0 if res == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

Evidence (`test_atr_tools.py`, TestXchkChecker, 6 tests, all pass):
- pass: a synthetic file with one row 1e-11 relative off -> PASS, INFO count of rows > 1e-12 = 1;
- fail by one row: row 250 off by 1e-8 relative -> `FAIL: max relative |diff| 1.000e-08 > 1e-09 at bar 250 (date 20100351)`, max row reported = 250;
- rows < 100 are excluded: a row-50 error of a factor 2 still PASSes;
- ATRS = 0 row: relative defined 0, no division error, PASS (also with ATRMT4 non-zero on that row: the brief defines reldiff = 0 there; see deviation 5);
- guards seen to fire: close 150 (wrong asset) `FAIL: row 10 ... close 150.0 outside 0.8 .. 1.7`; NaN `FAIL: row 120: atrmt4 is not finite`; bar index 99 at row 30 `FAIL: row 30: bar index 99, expected 30`; 100 rows `FAIL: only 100 rows; need more than 100`;
- command line: good file exit 0 PASS, bad file exit 1 FAIL.

## 6. Gotchas 1.3 diff (`docs/ZORRO_LIGHTC_GOTCHAS.md`, `git diff --stat --ignore-cr-at-eol`: 5 insertions, 2 deletions; plain `--stat` identical, no line-ending churn)

Table 1.3 row, "Prefixes in use" block and one change-log row: added `at_` (ATRMT4Core), `atw_` (ATRMT4 wrapper), `ats_` (ATR NCS body), `ax0_` / `axi_` / `axr_` / `axz_` (ATR control bodies NC0 / NCWi / NCR / NCZ),
`pse_` (PROBE_SeriesExprLen), `xa_` (XCHK_ATRMT4_vs_ATRS). Nothing else. A repo grep for these prefixes in `*.c` / `*.h` before writing found no existing use.

## 7. Tests and guard-fire evidence

`test_atr_corrected_code.py` (11 tests, all pass), run output:
```
[i] indicators/nnfx/ATR.c: core: verbatim (body == pre-registered lines); wrapper: verbatim (body == pre-registered lines)
[fire] ATR.c static before vars at_n:                          ok=False (core: body differs from the pre-registered lines)
[fire] ATR.c at_n[0] == Length + 1 -> at_n[0] == Length:       ok=False (core: body differs)
[fire] ATR.c Close[1] -> Close[0] (every occurrence):          ok=False (core: body differs)
[fire] ATR.c at_TR[Length] -> at_TR[Length - 1]:               ok=False (core: body differs)
[fire] ATR.c series(0, Length + 2) -> series(0, Length):       ok=False (core: body differs)
[fire] ATR.c the if(at_n[0] > 1) guard removed:                ok=False (core: body differs)
[fire] ATR.c vars at_A = series(0, 2) moved inside the if:     ok=False (core: body differs)
[fire] ATR.c wrapper does not call the core:                   ok=False (wrapper: body differs)
[fire] scans: static, decimal literal, literal product, global var, PI, priceHigh each reported on a broken copy
[fire] caller scan reports ATRMT4( in a code line; ignores comments and ATRMT4Core(
[ii] git log bd62493 -- indicators/nnfx/ATR.c: '' (no old blob)
[ii] files calling ATRMT4(: ['strategies/tests/XCHK_ATRMT4_vs_ATRS.c']
[v] ATR.c: 0 hits; spec NCS body: [(1, 'ats_prev')]
```
Each broken copy goes through a real temp file, as in the MAF tests. The "Close[1] -> Close[0]" copy replaces every occurrence (also the ones in comments, which the comparison ignores).
Also asserted: no `static`, `INITRUN`, `Period`, `#include`, `PI`, global var, decimal literal, product of literals, `priceHigh` / `priceLow` / `priceClose` in ATR.c; 3 `series()` calls, all before the first statement, each with an explicit length.

## 8. Generator change

None (expected none). The generated layout is the stage 1 layout: 148 calls per bar, 304 columns, 670 lines, sha256 identical when regenerated into a temp folder after the amendment was appended.
One stage 1 **test** changed (not a criterion, not the generator): `test_generator_atr.test_lint_issues_are_exactly_the_two_stage2_ones` asserted that lint reports `L_INCLUDE` and `L_NO_STATIC` because `ATR.c` did not exist.
With `ATR.c` present that assertion is false (it was the one FAIL in the first full run, section 9). It is replaced by `test_lint_is_clean_now_that_atr_c_exists` (lint issues == [] and the file exists) and a new
`test_lint_fires_when_atr_c_is_missing` (the include resolved from an empty folder and the no-static lookup in an empty root give exactly `L_INCLUDE` and `L_NO_STATIC`, so both rules are still seen to fire). Recorded in A1.1.

## 9. Pre-run conditions (spec pass_condition) and suite

| Item | Result | Evidence |
|---|---|---|
| (i) corrected code verbatim | PASS | test_atr_corrected_code, 8 guards fire (section 7) |
| (ii) new file, callers, Zorro include grep | PASS | no commit up to `bd62493` has the file; only `XCHK_ATRMT4_vs_ATRS.c` calls `ATRMT4(`; `grep -rl ATRMT4 C:/Zorro/include`: no hit (stage 1: no hit; repeated) |
| (iii) reference reproduces the spec | PASS | test_reference_atr_spec 8 tests; largest deviation 0.000e+00 in every section (conditioning 72 values, findings 678 values) |
| (iv) `generator.py <spec> --lint-only` | PASS | `lint clean; nothing written`, exit 0; include resolves; INFO: floors trace 8.882e-16, equivariance 1.776e-15, known_value 4.407e-17; control margins all >= 10x on every required kind (thinnest: NC0 trace 2.74e+08x; the sub-10x kinds NCWi and NCZ known_value, 4.41e-05x, are not required); `INFO L_NO_STATIC indicators/nnfx/ATR.c: 0 static tokens: PASS` |
| (v) no-static lint | PASS | 0 hits on ATR.c; 1 hit (`ats_prev`) on the NCS body |
| (vi) series-length probe | **PENDING** | `cond_vi = "pending: PROBE_SeriesExprLen.c, run by the user before the main run"` |
| (vii) conditioning recomputed | PASS | `checker.conditioning_mismatches = []`, 0 INFO (test_01b) |

Suite (`bash analysis/harness/run_tests.sh`, Claude Code shell, Python 3.12):

| Run | TOTAL | PASS | FAIL | ERROR | SKIP |
|---|---|---|---|---|---|
| before (at `bd62493`, nothing of stage 2 present) | 926 | 926 | 0 | 0 | 0 |
| after, first run (stage 2 files in, stale stage 1 lint test not yet updated) | 949 | 948 | 1 | 0 | 0 |
| after, second run (final test files, amendment appended) | 950 | 950 | 0 | 0 | 0 |

The first run's single FAIL was `test_generator_atr.GeneratedScript.test_lint_issues_are_exactly_the_two_stage2_ones`: `AssertionError: Lists differ: [] != ['L_INCLUDE', 'L_NO_STATIC']`, i.e. lint is now clean
because `ATR.c` exists (section 8). It was reported, the test updated, and the full suite rerun green. After that run I changed two things that no test reads for content: a one-line comment in `PROBE_SeriesExprLen.c` and its StartDate (deviation 2),
and the sha256 recorded in the spec; I reran `test_reference_atr_spec` and `test_generator_atr` (green) and re-parsed the spec, but did not rerun the full suite a third time.
The known intermittent `test_checker_amend1.test_cli` MemoryError did not appear. New tests: 11 + 12 + 1 net = 24 (926 + 24 = 950). The commit-message count must come from the user's Git Bash run.

## 10. Scripts, hashes, read-through

| File | sha256 / blob |
|---|---|
| `indicators/nnfx/ATR.c` | git blob `976af2849785b3bef5303e511293b01a07ab26b0` |
| `strategies/tests/GEN_ATR_MT4.c` | `02b6a63635d2a7dc4302bd135c168859870ac58f7b4bc54ad717305bb47bc4eb` |
| `strategies/tests/PROBE_SeriesExprLen.c` | `9058aa2fd29cf53521043c26124fac351d3b8e8eada7189e4b0a0c5675f74d6d` |
| `strategies/tests/XCHK_ATRMT4_vs_ATRS.c` | `5179dcce3d22f5db53218c1f2f1d4509da321308e6bc16c29fa7726d86cf8ecd` |

All four are recorded in `[prerun]` of the spec. Generated script path: `strategies/tests/GEN_ATR_MT4.c` (670 lines, 35345 bytes), the generator's default output folder.
Read-through of `GEN_ATR_MT4.c` (each item of brief section 8):
- one include, `#include "../../indicators/nnfx/ATR.c"` (after `<default.c>`): yes;
- input series: 18 price inputs and 10 band High / Low pairs are built from integers (lvl 11/10, amp 1/100, slp 1/10000, `pi_x = 4 * atan(1)`, h = `atr_hb` = 2/10000, `atr_k_sc` 10/1, `atr_c_sc` (0 - 99)/10, `atr_k_of` 1/1, `atr_c_of` 11/10), all before the 38 `series(X, 22)` calls and before any indicator call; every one of them has length 22. The sc / of High / Low copies are mapped from XH[6] / XL[6] with the same k and c. No decimal literal in the harness part or the control bodies (grep for digit-dot-digit outside comments: none), no `PI` / `Period` token outside comments. Every generated static (`atr_n`, `atr_done`, `atr_hdr`, `atr_rows`) is reset at INITRUN. `ats_prev` (NCS body) is not, by design (spec [run_notes]): restart Zorro before a rerun;
- calls: all unconditional, fixed variant-major order, 148 per bar (counted by regex: `ATRMT4Core` 52 = AT14 18 + AT20 18 + NCW 16 with Length 14 / 20 / 15; `atr_nc0`, `atr_ncwi`, `atr_ncr`, `atr_ncz` 16 each; `atr_ncs` 32); no call sits in an `if` or loop;
- NCS order: NCS on `flat, s5, s10, s20, s40, s100, ramp, rampdn, flatB, rampB, rampdnB, s5B, s10B, s20B, s40B, s100B`, then NCS2 on the same 16 in the same order: **identical to the order stage 1's replay parsed, no STOP**;
- out-parameters: `atr_o_tr` (a local scalar) receives `pTR`, copied to `Y[]` on the next line before the next call; NCS calls return the value only;
- raw file `Data/GEN_ATR_raw.csv`: 304 columns (304 unique names counted from the header `file_append` strings), header and 3000 rows written before `quit()` with `atr_done` latched first (gotchas 9d.4); see deviation 1 for the guard;
- `C:/Zorro/Data/` holds none of `GEN_ATR_raw.csv`, `PROBE_SeriesExprLen.csv`, `XCHK_ATR_raw.csv` (and no `GEN_ATR_exit_marker.txt`): confirmed with `ls` just before writing this report.

## 11. Deviations from the brief and points to check

1. **Raw-file guard of the generated script.** The brief (section 8) lists "no-overwrite guard" for `Data/GEN_ATR_raw.csv`. The generator (unchanged, as section 6 of the brief requires) deletes the raw file at INITRUN, as it does for every GEN script (FRAMA: same). So the main run overwrites a stale raw file instead of refusing. Copy the raw CSV to `*_run1.csv` after the run (CLAUDE.md 7); a generator change would have been needed otherwise. The probe and the cross-check script do have the refuse-if-exists guard (`file_length(...) > 0` at INITRUN). (c) `file_length` returns 0 for a missing file (declared `size_t file_length(const char*)` in `C:/Zorro/include/functions.h:166`; the 0-for-missing behaviour is from memory of the manual and unprobed): if it did not, the probe would print `REFUSED` on the first click and write nothing, which the user would see.
2. **Probe clock.** The brief says "StartDate / EndDate / BarPeriod / asset as the generated script": StartDate 20080101, EndDate 20240101 (I first wrote 20100101 and corrected it). The cross-check uses 20100101 as its own brief says.
3. **`ymd()` needs an argument.** `C:/Zorro/include/functions.h:546` declares `int ymd(var Date)`; the brief wrote `ymd()`. The cross-check calls `ymd(wdate())` (`wdate()` is the one-argument-less overload, `functions.h:136`). Compile-unverified.
4. **Extra `close` column** (8th) in `XCHK_ATR_raw.csv`, not in the brief's column list: it carries the CLAUDE.md 6 magnitude guard against a wrong asset (`asset()` is not a validity guard); the checker FAILs on a close outside 0.8 .. 1.7 (seen to fire). Delete it if you want the brief's exact seven columns; the guard then goes.
5. **ATRS = 0.** The brief defines relative |diff| as 0 when ATRS = 0, the checker does that, so a row where ATRS is 0 but ATRMT4 is not would be invisible to the criterion. The raw `absdiff` column still shows it; on rows >= 100 of EUR/USD D1 ATRS should never be 0 (c).
6. **New folder** `analysis/harness/tools/` for the two checkers (the brief allowed "or an existing tools module"; no such module exists). Their tests are in `analysis/harness/tests/test_atr_tools.py` (the suite discovers only the tests folder).
7. **Spec bookkeeping:** `[amendment_1]` has A1.1 only (no generator change, so no A1.2); the `# (none)` comment line above it is left unchanged. The probe sha256 was updated once after a comment/StartDate edit (final value in section 10).
8. Compile status: nothing was compiled. Light-C specifics assumed from the existing scripts and `functions.h`: `file_length`, `strf` with `%d` and `%.15e`, `series(0, L + 2)` (the probe's question), `ymd(wdate())`, `abs(var)` (declared in `default.c:41`).

## 12. Git

`git diff --stat` and the one suggested commit command follow in the terminal message (new files are untracked, so they are in `git status`, not in `git diff --stat`).
