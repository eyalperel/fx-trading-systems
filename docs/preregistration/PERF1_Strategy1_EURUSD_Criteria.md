# PERF1 — First performance read: Strategy 1 variant 0, EUR/USD D1 — Criteria

**Status:** pre-registered 2026-11-24, before any performance number is computed. Amendments are dated
and appended below, never edited in place (PROJECT_STATE §2.2).
**Decided:** planning chat 2026-11-24, one point at a time (user: accept each, decisions P-1..P-4).
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

**Lifts R-D1** (`docs/template/NNFX_TEMPLATE_DECISIONS.md`): R1 was mechanics only. Phase 1 step 5 PASS
(`e5c228c`) was the condition for reading performance.

**What is read:** Strategy 1 variant 0 (`strategies/template/NNFX_Strategy1.h`: FAMA (.5, .05) baseline,
Fisher 10 C1, Reflex 20 C2, ATR(14) MT4, T1-T11 / M-D1..M-D8 / R-D2..R-D7 defaults), EUR/USD D1 (17:00 New York
bars), trades 2007-02-01..2026-05-29, TICKS on M1 history, TR_FRC on, 100,000 EUR, 2% per signal (two 1% halves).

---

## P-1 What is reported

### R units

| Unit | 1 R = | Computed as |
|---|---|---|
| **Half-R** | that half's actual risk at entry | net profit (EUR) / (lots x stop pips x PIPCost) |
| **Signal-R** | the signal's actual risk (both halves) | (net P&L half 1 + half 2) / (risk half 1 + risk half 2) |

- (a) Stonehill counts each signal as two half-trades (C1 §1.1); VP's unit is the signal at 2% risk [M3].
- Denominator = **actual** risk after the floor rounding (M-D8.2), so lot rounding does not enter R.
- Net profit = Zorro `TradeProfit` (spread, rollover, commission included; HALF row). Risk from the SIZE row.
- (b) PIPCost is the fixed 2025-07-28 snapshot (M-D8.4); it sizes and values the trade alike, so R is unaffected.

### Report table

Every item for **all signals / standard only / continuation only** (T9.4), at **spread x1 and x2** side by side.

| # | Item | Definition |
|---|---|---|
| 1 | Signals, halves | counts |
| 2 | Total R, mean R per signal | signal-R |
| 3 | Mean R per half | half-R; TP1 half and runner half separately |
| 4 | Win rate | per signal: net signal-R > 0 = win, <= 0 = loss (breakeven exits pay the spread, so they count as losses) |
| 5 | Max drawdown | largest peak-to-trough of cumulative signal-R, stepped at each half's close (a half adds its half-R x its share of signal risk) |
| 6 | Swap | rollover summed in R; and as % of total net R |
| 7 | Spread cost | summed in R |
| 8 | Same-bar stop + TP1 | count of trades with stop and TP1 both inside one daily bar, and how Zorro resolved each (T5 amendment 3) |
| 9 | Long TP1 halves | count (M-D7) |
| 10 | Exit reasons | counts per reason (C1 flip, baseline, stop, TP1, breakeven, trail, end of history) |
| 11 | Refused signals | counts per reason (bridge-too-far, below 1 lot, margin) |
| 12 | Total R per year | calendar year of the exit, 2007-2026 |
| 13 | Longs vs shorts | count and total R per direction |

**Information only (never used in a verdict):** final equity in EUR at 2025-07-28 rates (M-D8.4); max
MarginTotal / Equity; the P-4 near-miss table.

**Limitations (c), written into the report:**
- Drawdown is on closed trades only; drawdown inside an open trade is not counted, so the real one can be deeper.
- When total net R is near 0 the swap % is large and unstable; read the swap sum in R.

### Measuring tool

`tools/perf_report.py` computes the table from the Zorro logs. Before it reads a real log it passes tests on
synthetic trade lists with hand-calculated answers (every item above), and a planted defect (e.g. target risk
used in place of actual risk) is seen to change the output (PROJECT_STATE §2.4-2.5).

---

## P-2 Data

| Level | Data | Gate before reading |
|---|---|---|
| x1 | **R1b run 1, reused**: `C:/Zorro/Data/TPL_R1b_log_run1.csv` (sha256 prefix `80873c4803b8c1c2`, recorded in `TPL_R1_Criteria.md`), indicators `TPL_R1b_ind_run1.csv` (`49309c429c06baf5`) | R1b PASS (run 1). `perf_report.py` recomputes the sha256 and refuses on a mismatch |
| x2 | **New run R1c**: same script `strategies/tests/TPL_R1_EURUSD.c`, same range, costs on, `nx_SpreadMult = 2` | R1c must first pass the R1b checks (K0-K6) at x2: every half pays exactly one doubled spread against its own fill; rollover per bar day; sizing, Equity, no MARGINCALL. Its log sha256 is recorded before `perf_report.py` reads it |
| x0 | R1a is **not used** for performance | spread cost is measured in R from the x1 log (item 7) |

- **What x2 doubles (b):** `nx_costs_apply()` sets `Spread = base x nx_SpreadMult` (`NNFX_Template.h:200`); rollover
  and commission are untouched. So x2 = spread doubled, rollover and commission at the asset-list value (T7.2).
- (b) At x2 the trades differ from x1 (a wider spread moves stop / TP trigger times, M-D7, R-D7): x2 is its own run,
  not x1 minus a cost.
- **Disclosure (b):** the outcomes of 10 R1a trades (one per exit combination, seed 20261124) were seen in Phase 1
  step 5. (c) This tells little about total R, but this read is not fully blind and is recorded as such.

---

## P-3 Verdict: continue or stop (written before looking)

(c) Purpose: triage. This read decides whether Strategy 1 variant 0 goes on to Phase 2 (T11 sensitivity, other dev
pairs, walk-forward, surrogate test). It is not acceptance; the confirmation set stays untouched.

All conditions at **spread x2** (T7.2: a result that holds only at x1 is not accepted). x1 is reported, not decisive.

| Verdict | Condition |
|---|---|
| **CONTINUE — evidence** | t >= 2 on mean signal-R **and** total R > 0 with the best year removed |
| **CONTINUE — no evidence yet** | mean signal-R > 0 **and** total R > 0 with the best year removed, t < 2. Goes to Phase 2 labelled "no evidence of an edge yet"; the Phase 2 surrogate test decides |
| **STOP** | mean signal-R <= 0, **or** total R <= 0 with the best year removed. Recorded as a failure (§2.9); Strategy 1 is not tuned on this data to rescue it; next is Strategy 2 variant 0 under its own pre-registration |

**Definitions.**
- t = mean / (sample standard deviation / sqrt(n)) over all signals, continuation included.
- Best year = the calendar year (by exit date) with the highest total R at x2; it is removed and total R recomputed.

**Notes.**
- (c) t >= 2 is a statistical convention, not an NNFX source value. The t value is always reported.
- (c) The t formula treats signals as independent; on one asset with one trade at a time this is approximate
  (a runner can overlap the next signal).
- (c) Size estimate (assumed spread of signal-R ~1 R, about 325 signals, standard error ~0.055 R): a true 0.05 R
  edge passes t >= 2 about 14% of the time and mean > 0 about 82%; a zero edge passes mean > 0 about 50%. Hence the
  middle verdict and its label.
- **Not gated:** win rate, drawdown, exit mix, longs / shorts. No sourced threshold exists; inventing one would be
  a magic number (T11).

**Variant count:** 1 (Strategy 1, variant 0, EUR/USD). Spread x1 / x2 are T7 reporting levels, not variants.
Project-wide strategy variants tested after this read: 1.

**Guard:** the verdict code in `perf_report.py` runs first on synthetic trade lists built to hit each verdict
(evidence, no evidence, STOP on mean, STOP on best year removed) and must return the expected verdict on each.

---

## P-4 One data feed (knife-edge note from step 5)

- (b) Every number comes from one feed: Zorro EUR/USD M1 history 2005-2026 (`C:/Zorro/History/EURUSD_*.t6`). Step 5
  found several outcomes hanging on < 4-pip margins; on the decisive highs / lows, two independent daily sources
  agreed within 0.4 pip (10 trades).
1. **Label:** the verdict reads "Strategy 1 v0 on this EUR/USD feed". The report lists every history file used with
   its sha256 (computed by `perf_report.py` from the files R1b / R1c read). It is not a result about EUR/USD in general.
2. **Near-miss table (information only, never gated).** For each half: the closest approach of any bar high / low to
   its stop and TP1 without crossing, and the overshoot when crossed. Count of halves whose stop / TP1 outcome would
   flip under a price shift of **0.5 / 1 / 2 pips** (0.5 near the 0.4-pip feed gap measured in step 5, (b); 1 and 2 a
   fixed band, (c), T11.3 style). (c) Counts possible flips only; R is not recomputed (a flip changes all later trades).
   Tested on a synthetic case with a known answer first.
3. **Phase 2 robustness item:** the same template on a second M1 feed (e.g. Dukascopy), own pre-registration;
   compare trade lists and verdict. Added to PROJECT_STATE "Next".
- (c) x2 partly stresses this already (triggers move by about one spread, 1.2 pips), but in one direction only;
  feed differences go both ways.

---

## Run order

1. Commit this file (before any number).
2. `tools/perf_report.py` + tests (synthetic known answers, planted defect, verdict guards); commit.
3. R1c prediction written and committed (c) (K0-K6 expected at x2); user runs R1c in Zorro; `check_r1.py` at x2 → PASS
   required; record log sha256.
4. Read: `perf_report.py` on R1b (x1) and R1c (x2); results and verdict appended below as "PERF1 read 1".

## Amendments

### Amendment 1 — 2026-11-24, before any performance number (user: accept, option A)

Reason (b): `tools/perf_report.py` (`9a202d6`, tests `9eb7bc3`, 48/48) stops on the R1b log with exit 3: two inputs
are not logged. (1) TP1 distance / level (item 8, P-4): no row holds `Tp1Atr` or the TP1 level; the template's
same-bar counter `nx_aNSameBar` is never logged. (2) Refusals (item 11): bridge-too-far skips leave no row; `ERROR`
rows (lots, risk, margin) carry no signal kind.

**A1.1 Data (replaces the P-2 table rows x1 / x2).**
- Template change, **logging only**: an `INFO` row carries `Tp1Atr=` and `RefusedLog=1`; every refused signal writes
  `REFUSED,asset,ymd,reason,kind` (reason: bridge-too-far, lots, risk, margin; kind: standard / continuation).
  Row format proposed by Claude Code, adopted.
- **x1 = new run R1d** (logging template, costs on, `nx_SpreadMult = 1`). Gate: the R1b checks (K0-K6) PASS **and**
  R1d's HALF rows equal R1b run 1's 650 HALF rows exactly (proves the change is log-only). R1b run 1 stays the reference.
- **x2 = new run R1c** (logging template, `nx_SpreadMult = 2`), gate as P-2.
- Regressions after the template change: S4, P5, P6 re-run, each equal to its last PASS.
- Both log sha256 recorded before `perf_report.py` reads them.

**A1.2 Choices left open by P-1 / P-3 / P-4, adopted as implemented (c).**
- Item 12 and the best-year removal: a signal is placed whole in the calendar year its last half closed.
- Drawdown: the peak starts at 0; halves closing on the same day are applied in log order.
- Near-miss and same-bar: a half's life includes its exit bar only for level exits (tp1, stop, be, trail);
  close-decided exits fill at the next open, so their exit bar is excluded.
- Best-year tie: the earliest year is removed.

**A1.3 Extra refusals in `perf_report.py` (guards, each seen to fire in its tests):** a group missing a half; a
profit breaking the cost identity; units not matching the SIZE lots; a SIZE row with neither ENTER nor ERROR;
REFUSED rows disagreeing with ERROR rows.

**A1.4 Disclosure (b).** In addition to the 10 step-5 trades (P-2): while inspecting the log format, Claude Code
printed 3 raw HALF rows of `TPL_R1b_log_run1.csv` (entry, exit, profit of the first signals) and row counts per
kind (325 ENTER, 650 HALF, 208 STOP). (c) The STOP count hints at the exit mix. The verdict rule (P-3) was fixed
before any of this was seen and is unchanged.
