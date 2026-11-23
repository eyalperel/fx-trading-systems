# P5 — Transaction costs probe: pre-registered criteria

**Written 2026-11-23, before the run** (Phase 1 step 4; T7 guard "costs on vs off must differ by the
hand-calculable amount"). Commit before the [Test] click with `tpc_CompileOnly = 0`. Changes after
the commit are dated amendments below. Labels: (a) source states, (b) measured, (c) inference.

## Setup

- Script `strategies/tests/TPL_Costs.c` through the unchanged template (S4 PASS, `cda6836`; since then
  only the HALF row gained cost columns and `nx_costs_apply()` was added). Compile check done 2026-11-23.
- 8 scenarios (A1, A2, B1, C1 and mirrors A1M, A2M, B1M, C1M), each twice on identical price / states
  files: K0 costs off, K1 costs on. Names `EUR_<scenario><k>_USD`, so Zorro identifies them as Forex
  ((a) asset.htm: "If the name begins and ends with the 3-letter abbreviation of a currency, it is
  identified as Forex"); costs are per 10000 units for currencies (spread.htm).
- K1, set by script after every `asset()`: Spread 2 pips; Commission 1 (per 10000 units); RollLong -1,
  RollShort +0.5 (per 10000 units per day). LotAmount 1000, PIPCost 0.1 per pip, 1 lot per half: per
  half **spread 0.2, commission 0.1 per round turn, rollover -0.1 (long) / +0.05 (short) per day**.
  K0: all four 0. Spread multiplier x1 (`nx_SpreadMult`).
- Checker: `python tools/check_costs.py C:/Zorro/Data/TPL_Costs_log_run1.csv
  analysis/template/costs/results/TPL_Costs_run1.csv` (7 tests; planted errors seen to fail).

## Sources for the expectations

(a) spread.htm: profit reduced by the spread; commission charged when the position closes, round-turn
cost Lots x Commission x LotAmount / 10000; rollover "per 10000 contracts for currencies", added "for any
trade that was longer open than 12 hours at any new day, including Saturday and Sunday". stop.htm: "all
prices are given as ask prices"; a trade is closed "when the ask price reaches the given ... limit"; longs
fill at the ask and close at the bid, shorts fill at the bid and close at the ask. trading.h: the exit
price field is "sell price per unit, without spread".

## Two open questions, candidates fixed now

- **Day rule** for rollover (manual: "new day", time zone not stated): H_UTC (00:00 UTC), H_NY
  (00:00 New York), H_BAR (17:00 New York = our bar close).
- **Short levels** with a spread: S_ASK (stop / TP1 / breakeven measured from the ask-quoted entry, as
  the engine) or S_BID (from the bid fill: those levels one spread lower, so the K1 short gains the spread
  back on such exits). The trailing stop comes from closes and is the same under both.

Rollover days per half from the S4 run 2 trade times (entries Thu 2024-03-07 23:00 UTC; `--predict`):

| Half | Close (UTC) | H_UTC | H_NY | H_BAR |
|---|---|---|---|---|
| A1, A1M (both); A2, A2M, B1, B1M half 1 | Fri 03-08 09:30-09:43 | 0 | 0 | 0 |
| A2, A2M runner | Mon 03-11 08:08 | 3 | 3 | 3 |
| B1, B1M runner | Thu 03-14 08:30 | 6 | 6 | 6 |
| C1, C1M (both) | Mon 03-11 22:00 | 3 | 3 | **4** |

H_UTC and H_NY are not distinguished by these trades; C1 / C1M distinguish H_BAR from both.

## Criteria (run PASS only if all hold)

| # | Criterion |
|---|---|
| Q0 | No `Error` line in the Zorro window; no ERROR / ASSETFAIL row |
| Q1 | All 16 INFO rows: `assetType` 1 (Forex), `costed` = k |
| Q2 | Per pair: 2 halves each; half, direction, kind, entry day, exit day, exit reason equal K0 vs K1 |
| Q3 | K0 guard: rollover 0, commission 0, profit = direction x (exit - entry) x units within 1e-4 |
| Q4 | Rollover of every K1 half = an integer number of days x the direction's daily rate (within 1e-3 day) |
| Q5 | Longs: entry and exit price equal K0 vs K1 within 1e-5; profit(K0) - profit(K1) = 0.2 + 0.1 - rollover(K1) within 1e-4 |
| Q6 | Shorts: profit(K0) - profit(K1) = 0.3 - rollover (S_ASK) or, on stop / TP1 / breakeven exits, 0.1 - rollover (S_BID), within 1e-4; one of S_ASK / S_BID fits every short half |
| Q7 | One of H_UTC / H_NY / H_BAR fits every half's day count |

Tolerances: prices 1e-5 (as S4 C3); money 1e-4 (TradeProfit and TradeRoll are 4-byte floats, values
<= 16, float32 spacing <= 2e-6).

## Prediction (before the run)

- (c) PASS. Day rule: H_UTC or H_NY (Zorro's dates are UTC; C1 / C1M 3 days, not 4), reported as
  "midnight, UTC vs New York not distinguished". Short rule: S_ASK (c, weak: the manual states every
  level is an ask price, but not from which entry price a short's Stop distance is measured).
- Recorded, not predicted: the K1 short entry price (`TradePriceOpen`, bid or ask); `TradeCommission`
  field value; the bar on which each rollover charge appears (OPEN rows).
- If the day rule or short rule found differs from the engine's assumptions, it is recorded and decided
  (M-D7), not tuned away. A FAIL of Q2-Q5 is a cost-model defect and blocks P6.

## Variants

Cost levels: K0 (off) and K1 (made-up round values, not the asset list). Template variant 0, 1 run.
