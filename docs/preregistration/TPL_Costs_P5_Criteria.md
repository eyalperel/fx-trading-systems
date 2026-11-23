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

---

## Run 1 — 2026-11-23 10:13 — FAIL (Q1 guard fired: assets not Forex); data read at a known scale

Commit `4c10fec`. Log `C:/Zorro/Data/TPL_Costs_log_run1.csv` (sha256 `c7c647d96eab08c8…`); checker
output `analysis/template/costs/results/TPL_Costs_run1.csv` (36 FAIL rows). Zorro: `Trades 32`, no Error line.

- (b) **Q1 FAIL on all 16 assets: `assetType("EUR_A10_USD")` = 0**, not Forex. The manual's rule ("begins
  and ends with the 3-letter abbreviation of a currency", asset.htm) did not apply to this name shape.
  Zorro then charged commission and rollover per contract instead of per 10000 units: commission 1000.0
  per half (planned 0.1), rollover -1000 / +500 per day (planned -0.1 / +0.05). The guard did its job.
- Read at that known scale (x 10000 on commission and rollover; inference only in the scaling, the
  ratios are measured), the run answers the three open questions:
  - (b) **Rollover days: H_BAR fits every half, H_UTC and H_NY do not.** C1 and C1M: 4 days (H_BAR 4,
    midnights 3); A2 / A2M runners 3, B1 / B1M runners 6, all others 0 (equal under all rules). The
    prediction (a midnight rule) was wrong: the rollover day changes at the bar boundary (17:00 New York).
  - (b) **Short levels: S_ASK.** Every short half lost exactly one spread (0.2) against K0, on stop, TP1,
    breakeven, trail and C1-flip exits alike; prediction met.
  - (b) **Not anticipated: long TP1 halves pay no spread.** A2 / B1 half 1 (TP1): K1 exit recorded 1.01020
    (ask; the bid was 1.01000), profit K0 - K1 = commission only. Every other long exit (stop, breakeven,
    trail, C1 flip) lost exactly one spread. So a long's take-profit fills when the bid reaches the level,
    while a long's stop triggers when the ask reaches it ((a) stop.htm says both use the ask). Effect per
    long TP1 half: + one spread versus the engine's "one spread per half"; the ask must also travel one
    spread further before the TP fills (timing).
  - (b) Commission was charged once per half (TradeCommission field = the Commission value), at the close.
- Consequence for the criteria: Q5 ("one spread on every long half") does not describe Zorro. Not tuned
  here: the next step is a decision on how the template's cost model treats this (M-D7) and a fix for the
  asset names, then Amendment 1 and run 2.

## Amendment 1 — 2026-11-23 (after run 1, before run 2)

1. **Asset names (user decision):** the 16 assets carry real pair names, not dev-set pairs, 0.0001 pip:
   AUD/CAD, AUD/CHF, AUD/NZD, CAD/CHF, EUR/AUD, EUR/CAD, EUR/CHF, EUR/GBP, EUR/NZD, GBP/AUD, GBP/CAD,
   GBP/CHF, GBP/NZD, NZD/CAD, NZD/CHF, USD/CAD (K0 / K1 of A1, A2, B1, C1, A1M, A2M, B1M, C1M in that
   order; `tools/make_scenarios.py` COSTED). Files `<PAIR>syn.t6` / `<PAIR>syn_states.csv`, loaded with
   `History = "*syn.t6"` set before any asset call. (b) PROBE_AssetType: only real pair names give
   assetType 1 (gotchas 9d.18). Q1 unchanged (assetType 1 on all 16).
2. **M-D7 (user decision):** Q5 becomes: long halves closed at TP1 pay no spread (recorded exit one spread
   above the K0 exit; profit K0 - K1 = commission - rollover); every other long half as before (same
   prices, 0.3 - rollover). Q2-Q4, Q6, Q7 unchanged.
3. Prediction for run 2 (from run 1, read at the known scale): PASS; assetType 1 on all 16; Zorro loads
   the syn files (states rows 20, no Error 047); day rule **H_BAR** only (C1 / C1M 4 days); short rule
   **S_ASK** only; commission 0.1 per half; rollover -0.1 / +0.05 per day.
4. Old run-1 files (`History/EUR_*_USD*`, `analysis/template/costs/expected/expected_EUR_*`) are unused
   from now on.
