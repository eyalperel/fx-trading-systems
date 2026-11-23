# P6 — Lot sizing probe: pre-registered criteria

**Written 2026-11-23, before the run** (Phase 1 step 4, stage P6; decisions T8, M-D8). Commit this file
before the [Test] click with `tsz_CompileOnly = 0`. Changes after the commit are dated amendments appended
below, never in place. Labels: (a) source states, (b) measured, (c) inference.

## What is tested

The template's risk sizing (`nx_size()` in `strategies/template/NNFX_Template.h`, M-D8):
per half `Lots = floor(Equity x 1% / ((1.5 x ATR / PIP) x PIPCost))`, `Capital = 100000`, `MarginCost =
close x PIPCost / PIP / 20` at entry, and three refusals in this order: below 1 lot; actual risk above the
configured 1% per half; `MarginTotal` + both halves' margin above `Equity`.

- **Inputs:** 15 synthetic assets, `tools/make_scenarios.py ... SIZING` (start 2024-03-06; commit `1cc7f3e`),
  real pair names (assetType Forex, gotchas 9d.18), files `History/<PAIR>sz.t6` loaded with
  `History = "*sz.t6"`. Spread, commission, rollover 0. LotAmount 1000. ATR = float32(0.01) on every bar.
  Loop order and parameters:

| # | Asset | Scenario | PIPCost | PIP | Role |
|---|---|---|---|---|---|
| 0 | EUR/USD | R1 | 0.1 | 0.0001 | second signal sized after the first trade's result |
| 1 | GBP/USD | R1M | 0.1 | 0.0001 | same, short |
| 2 | AUD/USD | E1 | 0.08561 | 0.0001 | list value (USD quote); continuation sized later |
| 3 | NZD/USD | E1M | 0.08561 | 0.0001 | same, short |
| 4 | USD/JPY | B1 | 0.058102 | 0.01 | JPY-style pip |
| 5 | EUR/JPY | B1M | 0.058102 | 0.01 | same, short |
| 6-11 | USD/CHF, USD/CAD, EUR/GBP, EUR/CHF, AUD/CAD, EUR/CAD | A2, A2M, A5, C1, A1, A1M | 0.08561 / 0.1 | 0.0001 | open or closed trades in the Equity of later signals |
| 12 | EUR/AUD | A1_CMR | 0.1 | 0.0001 | **control:** planted bug NX_MUT_R2 (2% per half) |
| 13 | GBP/CHF | A1_GLOT | 1000 | 0.0001 | **guard:** below 1 lot |
| 14 | GBP/CAD | A1_GMRG | 0.1 | 0.0001 | **guard:** price + 19 (~20): margin 132,000 > equity |

- **Script:** `strategies/tests/TPL_Sizing.c`. Compile check (flag 1) done 2026-11-23: no Error line.
- **Checker:** `python tools/check_sizing.py C:/Zorro/Data/TPL_Sizing_log_run1.csv
  analysis/template/sizing/results/TPL_Sizing_run1.csv` (8 tests in `tools/tests/test_check_sizing.py`;
  each planted defect - lots, Equity, missing guard error, undetected mutant, MARGINCALL, half units - fails it).
  Model predictions: `python tools/check_sizing.py --predict`.

## Hand calculation (first signals, decision 2024-03-07, Equity = Capital = 100,000; no trade before)

ATR = float32(0.01) = 0.009999999776; stop = 1.5 x ATR = 0.014999999665.

| Asset | Stop pips | Risk per lot (EUR) | Raw lots = 1000 / risk per lot | Lots | Actual risk | Rounding |
|---|---|---|---|---|---|---|
| PIPCost 0.1, PIP 0.0001 | 149.99999665 | 14.999999665 | 66.6666682 | **66** | 990.00 | -1.00% |
| PIPCost 0.08561, PIP 0.0001 | 149.99999665 | 12.84149971 | 77.8725 | **77** | 988.80 | -1.12% |
| PIPCost 0.058102, PIP 0.01 | 1.4999999665 | 0.0871530 | 11474.07 | **11474** | 999.99 | -0.0006% |
| A1_CMR (2% per half) | 149.99999665 | 14.999999665 | 133.333336 | 133 | 1995.00 > cap 1000 | refused: risk |
| A1_GLOT (PIPCost 1000) | 149.99999665 | 149999.99665 | 0.0066667 | 0 | - | refused: lots |
| A1_GMRG (price 20) | 149.99999665 | 14.999999665 | 66.6666682 | 66 | 990.00 | refused: margin (2 x 66 x 1000 = 132,000 > 100,000) |

MarginCost at price 1.0: 1.0 x 0.1 / 0.0001 / 20 = 50.0 EUR per lot (PIPCost 0.08561: 42.805; PIP 0.01:
0.29051). Margin per signal 6,592-6,667 EUR = 6.6-6.7% of equity on every trading asset.

## Criteria

| # | Criterion | Pass condition |
|---|---|---|
| C0 | Zorro window | No line starting with `Error`; no ASSETFAIL row |
| K0 | Setup | 15 INFO rows: assetType 1, FixedLots 0, Capital 100000, RiskPct 2, Leverage 20, StopAtr 1.5, Fill 3, Hedge 2, TICKS 1 |
| K1 | Formula | Every SIZE row (except A1_CMR) recomputes from its own logged inputs within 1e-8 relative; lots = floor(raw); MarginCost = logged close x PIPCost / PIP / 20 |
| K1c | Control | A1_CMR's SIZE row does NOT satisfy the correct rule (DETECTED) |
| K2 | Refusals | ERROR rows exactly: A1_GLOT `lots`, A1_CMR `risk`, A1_GMRG `margin`; those 3 assets have no HALF row; every other asset has the engine's number of halves (32 in all); no ACCT row with MARGINCALL |
| K3 | Model | Every SIZE row's Equity within 0.05 EUR and lots equal to the from-scratch model under ONE timing alternative for the whole run (TA or TB, below); every ACCT row's Equity within 0.05 EUR of the model at the bar close |
| K4 | Halves | Each HALF row's lots (TradeUnits / (PIPCost / PIP)) equal its signal's SIZE lots |

**Run verdict:** PASS only if C0 and K0-K4 hold and K1c is DETECTED. Anything else is FAIL, investigated and
recorded; the template's sizing is not used for any strategy result until a run passes.

## Open question answered by the run (alternatives fixed before the run)

When asset j decides at bar t, what state of the other assets does `Equity` contain?
- **TA:** every asset as of this bar's close (Zorro processes all assets' ticks of the bar, then calls `run()`).
- **TB:** assets later in the loop than j as of the previous bar's close.
Model values (`--predict`), signals after the first day (2024-03-07 rows: Equity 100,000 under both):

| Signal (decision) | TA: Equity / lots | TB: Equity / lots |
|---|---|---|
| R1 EUR/USD (2024-03-11) | 102,217.06 / **68** | 100,814.58 / **67** |
| R1M GBP/USD (2024-03-11) | 102,217.06 / **68** | 99,626.59 / **66** |
| E1 AUD/USD (2024-03-13) | 105,200.55 / **81** | 105,811.71 / **82** |
| E1M NZD/USD (2024-03-13) | 105,200.55 / **81** | 105,811.71 / **82** |

**Prediction (c): TA.** Either alternative passes K3; a run matching neither is a FAIL.

## Prediction (before the run)

- (c) RUN PASS. 19 SIZE rows (15 on 2024-03-07, 4 later); 3 ERROR rows (lots, risk, margin); 32 HALF rows
  (Zorro `Trades 32`); K1c DETECTED; no MARGINCALL; timing **TA** with the lots above.
- Observations, not criteria: `MarginTotal` at the 2024-03-11 / 03-13 decisions vs the sum of open halves'
  lots x MarginCost at their entry decision (which MarginCost Zorro keeps for an open trade is not stated);
  max `MarginTotal / Equity` over the ACCT rows (predicted ~0.5 at the 2024-03-08 close: 16 halves of
  ~3,300 EUR still open after A1 / A1M stops and the A2 / B1 TP1s on the entry day); rounding error per signal (-1.00% / -1.12% / -0.0006% on the first day).

## Variants counted

- Template configurations: **1** (variant 0 sizing: 2% per signal, two 1% halves, floor, leverage 20).
- Controls and plants: 1 mutant (NX_MUT_R2, 1 asset); 2 planted inputs (PIPCost 1000, price 20).
- Runs: this is run 1 of P6. Every rerun is counted and recorded with its cause.

## Not tested here

Costs together with sizing (spread / rollover in Equity: P5 tested them at 1 lot); PIPCost conversion
(M-D8.4 option B, later); the same-currency rule (portfolio runs, T8.5); real bars (EUR/USD run next).

## Run 1 — 2026-11-23 15:58 — PASS, all predictions met; timing TA

Commit `f315f77` (criteria). Log `C:/Zorro/Data/TPL_Sizing_log_run1.csv` (sha256 `e91ad59edca18c92…`); checker
output `analysis/template/sizing/results/TPL_Sizing_run1.csv`: 86 rows, 0 FAIL, 1 DETECTED; timing fits: TA only.
Zorro: `Test: TPL_Sizing (TICKS) 2024`, `Trades 32`, no Error line. (The window's Win / Capital / CAGR figures
are the synthetic batch's statistics and have no meaning.)

| # | Result (b) |
|---|---|
| C0, K0 | No Error line, no ASSETFAIL; 15 INFO rows with the required settings |
| K1 | 18 SIZE rows recompute from their own inputs within 1e-8; first-day lots 66 / 77 / 11474 as hand-calculated |
| K1c | A1_CMR DETECTED (pct 2, 133 lots) |
| K2 | ERROR rows exactly: EUR/AUD `risk` (actual 1994.999955 above 1000), GBP/CHF `lots` (raw 0.0066666668), GBP/CAD `margin` (0 + 132000 above 100000); no HALF row for them; 32 halves on the 12 trading assets; no MARGINCALL |
| K3 | All 19 SIZE rows match model **TA** (TB fails): R1 / R1M at 2024-03-11 Equity 102,217.057465, **68** lots; E1 / E1M at 2024-03-13 Equity 105,200.549728, **81** lots. Every ACCT row equals the model at the bar close |
| K4 | Every HALF row's lots equal its signal's SIZE lots |

Observations:
- (b) **Equity timing = TA:** when an asset decides, `Equity` already holds every asset's state at this bar's
  close, including assets later in the loop. (c) Zorro processes all assets' ticks of a bar before calling `run()`.
- (b) Max `MarginTotal / Equity` = 0.518 (2024-03-08 close, 52,875.53 of 102,002.58), as predicted (~0.5).
- (b) `MarginTotal` vs the two models of which MarginCost an open trade keeps:

  | Close | Logged | At entry decision (ours) | At current close |
  |---|---|---|---|
  | 2024-03-08 | 52,875.534 | 52,842.533 | 52,875.534 |
  | 2024-03-11 | 42,970.364 | 42,950.563 | 43,009.963 |
  | 2024-03-12 | 23,579.823 | 23,566.623 | 23,612.824 |
  | 2024-03-13 | 16,779.823 | 16,766.623 | 16,812.824 |

  Neither model fits every row; the differences are <= 0.2% of `MarginTotal` (<= 0.04% of Equity). (c) Mechanism
  not identified (a mix of per-asset MarginCost update times is likely). Effect: the margin guard's threshold is
  uncertain by that much; at <= 52% use it does not bind. Open item, recorded, not a criterion.
- (b) Rounding error per signal: -1.00% (PIPCost 0.1), -1.12% (0.08561), -0.0006% (PIP 0.01) on the first day;
  later signals -0.21% (R1: 1020.00 for 1022.17) and -1.13% (E1).

**Verdict: P6 sizing PASS** (1 run). Variants: 1 sizing configuration; 1 mutant; 2 planted inputs.

## Amendment 1 — 2026-11-23 (regression run 2, R1 template changes; before the run)

**Why:** branch `eurusd-r1` changed the template: `nx_FillUnrounded = 1` sets TradeMode `TR_FRC` in
`nx_template_init()` (R-D5: stops, limits and fills no longer rounded to the PIP; (a) `include/trading.h:276`
"don't round to 1 PIP"), and the slot values `nx_s*` moved from `NNFX_Slots.h` to `NNFX_Config.h` (declaration
only). Inputs unchanged (generator output byte-identical, checked 2026-11-23).

**Prediction (c):** same verdict and counts as run 1 (RUN PASS, timing TA, 19 SIZE rows, 3 ERROR rows, 32 halves, mutant DETECTED, same lots). Logs need **not** be byte-identical: a level
that is not on the pip grid (stop = fill - 1.5 x float32 ATR) now fills unrounded. Recorded as an observation (b):
the largest change of any logged fill price vs run 1; > 0 shows that Zorro rounded before (R-D5), 0 that it did
not on these paths. Every price change must stay within the existing tolerances. Runs so far: 1; this is run 2.

