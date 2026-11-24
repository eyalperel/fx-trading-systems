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

## Run 2 — 2026-11-23 10:51 — FAIL (2 rows: fill position of long TP1 by one path step; costs exact)

Commit `8f5d947` (Amendment 1). Log `C:/Zorro/Data/TPL_Costs_log_run2.csv` (sha256 `478edbae14d2cacc…`);
checker output `analysis/template/costs/results/TPL_Costs_run2.csv`. Zorro: `Trades 32`, no Error line.

- (b) Q0, Q1 met: assetType 1 on all 16 assets, syn files loaded (states rows 20, no Error 047).
- (b) Q2-Q4, Q6, Q7 met: timing equal K0 vs K1; K0 cost-free; rollover an integer number of days on every
  half; **day rule H_BAR only** (C1 / C1M 4 days) and **short rule S_ASK only**, both as predicted in
  Amendment 1; commission 0.1 per half; rollover -0.1 / +0.05 per day.
- (b) **Q5 FAIL on 2 rows:** A2 and B1 half 1 (long TP1, CAD/CHF and EUR/CAD): profit K0 - K1 = 0.10998, Q5
  expects 0.1 within 1e-4. The K1 TP filled at 1.01019 (ask, 09:36:01 Fri), one 1e-5 path step before the
  1.01020 of run 1: 0.01 = 1e-5 x 1000 units.
- (b) Cost identity against the actual fills, all 32 halves: profit = direction x (exit - entry) x units
  - spread x units - commission + rollover, largest deviation 5.5e-7 (float32). **Every half, long TP1
  included, pays exactly one spread relative to its recorded (ask) fill**; the long TP1 difference is in
  where it triggers (about bid = level), not in what is charged. M-D7's wording "pays no spread" describes
  the result against the level, not the accounting.
- Cause of the FAIL (c, criteria-side): Q5's money tolerance (1e-4) was set from float32 precision only and
  left out the fill-position tolerance of one path step (1e-5 in price, S4 C3, = 0.01 at 1000 units) for a
  long TP1 whose trigger depends on the bid. Not tuned here.

## Amendment 2 — 2026-11-23 (after run 2, before run 3; user decision)

**Written after seeing run 2.** The change separates the two questions P5 mixes; it does not loosen the
cost question.

1. **Costs (replaces Q5 and Q6's cost part):** for every half of both copies, profit = direction x (exit -
   entry) x units - spread x units - commission + rollover, against that half's own recorded fills,
   within 1e-4 (float32). Spread 0.0002 / commission 0.1 on K1, 0 on K0. `TradeCommission` = 1 (the
   Commission setting; run 2: 1.0) on every K1 half.
2. **Fill position (new, separate):** K1 vs K0 within one path step, 1e-5, the S4 C3 tolerance and its
   reason (fills land within one 0.1-pip record of a level): entries equal; exits equal, except long TP1
   exits one spread higher on the ask (M-D7); shorts must fit S_ASK (exits equal) or S_BID (entry-derived
   level exits one spread lower) consistently.
3. Q0-Q4, Q7 unchanged. M-D7's wording is corrected in its record: every half pays one spread against
   its recorded fill; a long TP1 *triggers* at about bid = level.

Known before run 3 (from run 2's data; disclosed, not hidden): the cost identity holds on all 32 halves
(largest deviation 5.5e-7), and the long TP1 position offset was +1.998e-4 vs +2e-4 expected
(|diff| 9.98e-6, inside 1e-5 by 2e-8: the narrowest margin of the run). The path and the script are
unchanged, so run 3 is expected to reproduce run 2's log exactly (same sha256); a different log would
itself be a finding.

Prediction for run 3: PASS; log identical to run 2 (sha256 `478edbae14d2cacc…`); day rule H_BAR; short
rule S_ASK. Runs: 3 (2 FAIL recorded).

## Run 3 — 2026-11-23 11:10 — PASS, all predictions met

Commit `4156cf6` (Amendment 2). Log `C:/Zorro/Data/TPL_Costs_log_run3.csv`, **byte-identical to run 2**
(sha256 `478edbae14d2cacc…`, as predicted: the run is deterministic). Checker output
`analysis/template/costs/results/TPL_Costs_run3.csv`: 0 FAIL rows. Zorro: `Trades 32`, no Error line.

- (b) Costs: profit = price move - spread - commission + rollover on all 32 halves (<= 5.5e-7);
  commission 0.1 per half; rollover -0.1 / +0.05 per day, whole days only.
- (b) Fill positions within one path step; long TP1 one spread higher on the ask (M-D7).
- (b) Day rule **H_BAR** (rollover day = bar day, 17:00 New York with M-D1, weekend days included);
  short rule **S_ASK**.
- **Verdict: P5 PASS** (3 runs: run 1 FAIL, assets not Forex, Q1 guard; run 2 FAIL, criteria tolerance;
  run 3 PASS after Amendment 2, which was written after seeing run 2 and disclosed as such).

## Amendment 3 — 2026-11-23 (regression run 4, after P6; before the run)

**Why:** the template changed after run 3 (commit `1cc7f3e`, P6): `nx_template_init()` sets `Capital = 100000`,
and the entry block calls `nx_size()` only when `nx_FixedLots <= 0`. This batch sets `nx_FixedLots = 1`, so
(c) sizing is bypassed and no logged value changes (`Capital` affects Equity and margin-call simulation only;
1 lot per half uses < 0.1% of the margin). The generator edits change no input: all History files and expected
folders regenerate byte-identical (checked 2026-11-23, 160 files).

**Prediction (c):** `C:/Zorro/Data/TPL_Costs_run4.csv` **byte-identical** to `TPL_Costs_run3.csv` (sha256 `478edbae14d2cacc…`);
hence the checker output is identical and the verdict PASS. Zorro `Trades 32`, no Error line. Runs so far: 3; this is
run 4, a regression run. Variants unchanged.

## Run 4 — 2026-11-23 16:03 — PASS, prediction met (regression after P6)

Commit `2b22994` (Amendment 3). Log `C:/Zorro/Data/TPL_Costs_log_run4.csv` **byte-identical to run 3**
(sha256 `478edbae14d2cacc…`, `cmp`); checker output identical to run 3's: RUN PASS, 0 FAIL rows, day rule
H_BAR, short rule S_ASK. Zorro: `Trades 32`, no Error line.

**Verdict: P5 still PASS after P6.** Runs of P5: 4 (runs 1-2 FAIL, recorded; runs 3-4 PASS).

## Amendment 4 — 2026-11-23 (regression run 5, R1 template changes; before the run)

**Why:** branch `eurusd-r1` changed the template: `nx_FillUnrounded = 1` sets TradeMode `TR_FRC` in
`nx_template_init()` (R-D5: stops, limits and fills no longer rounded to the PIP; (a) `include/trading.h:276`
"don't round to 1 PIP"), and the slot values `nx_s*` moved from `NNFX_Slots.h` to `NNFX_Config.h` (declaration
only). Inputs unchanged (generator output byte-identical, checked 2026-11-23).

**Prediction (c):** same verdict and counts as run 4 (RUN PASS, 0 FAIL rows, day rule H_BAR, short rule S_ASK, Trades 32). Logs need **not** be byte-identical: a level
that is not on the pip grid (stop = fill - 1.5 x float32 ATR) now fills unrounded. Recorded as an observation (b):
the largest change of any logged fill price vs run 4; > 0 shows that Zorro rounded before (R-D5), 0 that it did
not on these paths. Every price change must stay within the existing tolerances. Runs so far: 4; this is run 5.


## Run 5 — 2026-11-23 19:46 — PASS, prediction met (regression after the R1 template changes)

Commit `12aa643` (Amendment 4). Log `C:/Zorro/Data/TPL_Costs_log_run5.csv` (sha256 `6dfbe788941bde8f…`); checker: RUN PASS, 0 FAIL
rows, day rule H_BAR, short rule S_ASK. Zorro: `Trades 32`, no Error line. Not byte-identical to run 4 (allowed by Amendment 4):
(b) 2 of 761 rows differ, the long TP1 exits of CAD/CHF and EUR/CAD (costs on): exit 1.010190725 (run 5) vs 1.010190010 =
float32(1.01019) (run 4), change 7.2e-7; profit change 7.2e-4. **So without TR_FRC Zorro rounded this fill to the 0.1-pip grid
(1e-5)**, as stop.htm states ("next 1/10 pip for currencies"), not to 1 PIP as the trading.h comment says. R-D5 (TR_FRC on) is
confirmed as the right setting for exact replays.

**Verdict: P5 still PASS after R1.** Runs of P5: 5.

## Amendment 5 — 2026-11-24 (regression run 6, PERF1 logging change; before the run)

**Why:** PERF1 Amendment 1 (A1.1), commit `d49c581`: logging-only template change. Every refused signal writes a
`REFUSED,asset,ymd,reason,kind` row (bridge-too-far in the baseline-cross skip branch; lots / risk / margin after the
existing ERROR row in `nx_size`); `nx_size` gains a kind argument (plumbing only). No condition, order, size or level
changed (diff read in the planning chat, 2026-11-24). (b) This checker ignores row types it does not read, so REFUSED
rows cannot change its verdict. Compare in Git Bash:
`diff <(grep -v '^REFUSED,' NEW | tr -d '\r') <(tr -d '\r' < OLD) && echo IDENTICAL`.

**Prediction (c):** same verdict and counts as run 5 (RUN PASS, 0 FAIL rows, day rule H_BAR, short rule S_ASK); Zorro
`Trades 32`, no Error line. Log `TPL_Costs_log_run6.csv` with REFUSED rows removed is identical to run 5's log (sha256
`6dfbe788941bde8f…`) up to line endings. REFUSED rows: `bridge-too-far` / `standard` only; 0 lots / risk / margin rows
(`nx_FixedLots` > 0). Count recorded as an observation (b). Runs so far: 5; this is run 6.
