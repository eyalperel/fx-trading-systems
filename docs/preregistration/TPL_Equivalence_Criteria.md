# S4 — Template equivalence: pre-registered criteria

**Written 2026-11-23, before the run** (Phase 1 step 4, stage S4). Commit this file before the
[Test] click with `tpe_CompileOnly = 0`. Changes after the commit are dated amendments appended
below, never in place. Labels: (a) source states, (b) measured, (c) inference.

## What is tested

The Light-C template (`strategies/template/NNFX_Template.h`, architecture A: Zorro executes, the
template decides at each close) must produce the same trades as the Python reference engine
(`analysis/template/reference_engine.py`, 32 hand-calculated tests) on the same inputs.

- **Inputs:** 64 synthetic assets written by `tools/make_scenarios.py ... ALL` (start 2024-03-06):
  30 long scenarios (A1-A6, A3HF, P1, B1, B2, C1-C3, D1a, D1b, D1d, D2, D5, D6, D7a-c, D8, D9, E1-E3,
  E4a, E4b, R1), their 30 short mirrors (`<name>M`), and 4 planted-bug controls. Slots SCRIPTED
  from each scenario's states file; intraday paths of 0.1-pip records; spread 0, slippage 0,
  1 lot per half. (b) Generator padding guard passed: warm-up / tail bars change no trade, except
  D6 / D6M, whose tail entry from a decision on the scenario's last bar is reported and kept.
- **Expected:** `analysis/template/equivalence/expected/` (engine trades per scenario + counts).
- **Script:** `strategies/tests/TPL_Equivalence.c`, `tpe_CompileOnly = 0`. Compile check (flag 1)
  done 2026-11-23: no Error line, no result seen.
- **Checker:** `python tools/compare_equivalence.py C:/Zorro/Data/TPL_Equivalence_log_run1.csv
  analysis/template/equivalence/expected analysis/template/equivalence/results/TPL_Equivalence_run1.csv`
  (18 tests, each planted defect seen to flip the verdict).

## Criteria

| # | Criterion | Pass condition |
|---|---|---|
| C0 | Zorro window | No line starting with `Error`; no `ERROR` or `ASSETFAIL` row in the log |
| C1 | Setup, per asset | INFO row present; states rows = scenario bars; Fill 3, Hedge 2, TICKS 1, BarOffset 1020 |
| C2 | Trades, per scenario | Same number of halves as the engine; per half (in trade order): half, direction, kind, entry day equal |
| C3 | Prices | Entry and exit within **1e-5** of the engine (fills overshoot a level by <= one 0.1-pip path step, Amendment 4 of the probe; float32 inputs on both sides) |
| C4 | Exits | Exit reason and exit day equal; halves the engine closes as `end` (still open when the history ends, gotchas 9d.15) are compared on entry only |
| C5 | Documented difference | A3HF and A3HFM (high-first / mirrored path): Zorro takes TP1 on half 1, then stops the runner on the same bar (A3HF: tp1 1.0100 / stop 0.9850; A3HFM: tp1 0.9900 / stop 1.0150). The engine stops both (T5.2). Pass = Zorro shows exactly these trades. Reported as DOC, not as PASS |
| C6 | Counts | Template's same-bar stop/TP1 count (T5.2) and M-D3 runner-exit count equal the engine's per scenario; no half with reason `other`; no trade open after the last bar |
| C7 | Controls | Each of the 4 control assets (A6_CM3, A6M_CM3: breakeven placed without the M-D3 check; R1_CMF, R1M_CMF: entry only when no trade is open) shows **at least one FAIL row** |

**Run verdict:** PASS only if C0 holds and all 60 real scenarios meet C1-C6 (DOC and ENTRY_ONLY
rows allowed) and all 4 controls meet C7. Anything else is FAIL, investigated and recorded; the
template is not used for any strategy result until a run passes.

## Prediction (before the run)

- (c) All 60 real scenarios PASS; 4 DOC rows (A3HF, A3HFM halves); **40 ENTRY_ONLY rows**, one per
  engine `end` half, in A5, C3, D5, D6 (tail entry), D7b, D7c, D8, E1, E4a, P1, R1 and their mirrors
  (counted from the expected files, not from memory).
- **Open item, first evidence in this run:** an exit sent with `exitTrade` at a close under
  `Fill = 3` fills at the next bar's open (ZORRO_TRADE_MECHANICS §12 R1, (c), unprobed). Scenarios
  C1, C2, R1, A6, E1, E4a and mirrors depend on it. If it fills elsewhere, those fail on exit day or
  price; the cause is recorded and decided, not tuned away.
- Controls: MF (R1_CMF, R1M_CMF) predicted to miss the reversal entry (2 halves instead of 4).
  M3 (A6_CM3, A6M_CM3) sets the runner's stop above the close; Zorro's reaction is not stated in
  the manual ("immediately closed", stop.htm; price and timing under Fill 3 unknown, M-D3), so
  only "differs from the engine" is predicted. Its actual exit is recorded (it answers P2's
  second half as an observation).

## Variants counted

- Template configurations exercised: **5** — variant 0 (48 assets), volume ALWAYS_NO (D2, D2M),
  volume indicator states (E1-E4b and mirrors, 10), bridge-too-far off (D7c, D7cM), no continuation
  after a stop (E4b, E4bM). Controls are planted bugs, not system variants: 2 mutants, 4 assets.
- Runs: this is run 1 of S4. Every rerun is counted and recorded with its cause.

## Not tested here (later stages)

Costs (spread, swap, commission: P5), lot sizing and PIPCost (P6), real bars and real indicators
(P4 on EUR/USD), fill rounding to 1 pip on 5-decimal quotes (`TR_FRC`, ZORRO_TRADE_MECHANICS §12 R5),
the optimistic same-bar order (engine only).

---

## Run 1 — 2026-11-23 09:43 — FAIL (two setup causes found; template logic not implicated)

Commit `356315a` (criteria + code). Log `C:/Zorro/Data/TPL_Equivalence_log_run1.csv` (sha256
`162400b83510ecac…`); checker output `analysis/template/equivalence/results/TPL_Equivalence_run1.csv`.
Zorro: `Test: TPL_Equivalence (TICKS) 2024`, `Trades 112`, no Error line.

- (b) C0 met (no Error / ERROR / ASSETFAIL). C7 met: 4/4 controls detected (A6_CM3 and A6M_CM3 3 FAIL
  rows each, R1_CMF and R1M_CMF 1 each). 4 DOC rows as predicted (A3HF / A3HFM match C5).
- (b) **50/60 real scenarios PASS; FAIL: A4, A4M, A5, A5M, A6, A6M, D7b, D7bM, D7c, D7cM.** ENTRY_ONLY
  rows 36 (predicted 40; the missing 4 are D7c / D7cM).
- **Cause 1 (b): Zorro's trading week.** Every failing fill is a Monday fill at 03:00:00 UTC (Zorro
  trade log): A4 stops at 0.97801 (gap open 0.9800 expected), A5 TP1 at 1.01201 (1.0130), A6 M-D3
  exit at 0.99651 (0.9975), D7b entry at 0.99800 (0.9990), mirrors alike. On the synthetic Monday
  path that time is the day's low (high for mirrors). (a) `StartWeek` default 72300 = "Sunday 23:00"
  in local time of the BarZone; with `BR_WEEKEND` (default) Zorro does not "trade ... between
  EndWeek and StartWeek in the bar time zone, even when they contain price quotes" (date.htm,
  barmode.htm). BarZone = EST (M-D1) puts the week start at Sunday 23:00 New York = Monday 03:00
  UTC; the synthetic Monday starts Sunday 18:00 New York. (b) Real EUR/USD 2024 (`EURUSD_2024.t6`,
  53 weekly gaps): last quote Friday 16:47-17:00 New York, first quote Sunday 17:01-17:09 New York.
  So on real data too, Monday-open fills would be taken up to 6 h after the weekly open.
- **Cause 2 (b): bar creation follows the first asset.** All 64 assets' last BAR row is 2024-03-18,
  the last history day of SYN_A2 (asset 0). (a) "If that flag [BR_FLAT] is not set, bars are only
  created where the first asset has valid prices" (barmode.htm). D7c / D7cM decided their entry
  at the 03-18 close and never got another bar (0 halves); D7b / D7bM entered at 03-18 and were
  closed by the end of the test. The generator gave scenarios different lengths (13-20 days).
- (c) Neither cause involves the template's decisions: every non-Monday fill, every reason, kind and
  day outside these cases matched; the controls failed as planted.
- Not interpreted further while the setup is wrong. Next: decision on the trading week (M-D6),
  generator fix for a common last day, Amendment 1, run 2.

## Amendment 1 — 2026-11-23 (after run 1, before run 2)

Changes (setup only; criteria C0-C7, tolerance, documented differences and the template's decision
logic unchanged):
1. **M-D6 (user decision 2026-11-23):** `StartWeek = 71700` (Sunday 17:00 New York, BarZone EST),
   named config value `nx_StartWeek`, set before the first asset call. `EndWeek` stays at Zorro's
   default (Friday 20:00 New York; the last real quote is Friday ~17:00, run 1 cause 1).
   C1 gains `StartWeek = 71700` (INFO row), checked by the comparator.
2. **Common last day:** every scenario's tail is extended so all 64 end on 2024-03-26
   (`tools/make_scenarios.py`; the generator refuses to write if last days differ). Checked: the
   regenerated expected trades differ from run 1's only in the exits of `end` halves; 40 real
   `end` halves, as before.
3. Run 2 uses `tpe_CompileOnly = 0` unchanged in purpose.

Prediction for run 2 (unchanged from the original, now with both causes removed): C0 met; 60/60 real
scenarios PASS; 4 DOC rows (A3HF, A3HFM); 40 ENTRY_ONLY rows; 4/4 controls detected; every Monday
fill at the Monday open (first record, Sunday 18:00 New York on the synthetic path); last BAR row
2024-03-26 for every asset. Runs so far: 1 (FAIL, setup). Variants unchanged (5 configurations).

## Run 2 — 2026-11-23 09:49 — PASS, all predictions met

Commit `b3f31f9` (Amendment 1). Log `C:/Zorro/Data/TPL_Equivalence_log_run2.csv` (sha256
`d6492c5ce83aa9ff…`); checker output `analysis/template/equivalence/results/TPL_Equivalence_run2.csv`.
Zorro: `Test: TPL_Equivalence (TICKS) 2024`, `Trades 116` (120 expected halves minus the 4 the MF
controls lose), no Error line.

| # | Result (b) |
|---|---|
| C0 | No Error line; no ERROR / ASSETFAIL row |
| C1 | 64 INFO rows: Fill 3, Hedge 2, TICKS 1, BarOffset 1020, StartWeek 71700, all states rows loaded; last BAR row 2024-03-26 on all 64 assets |
| C2-C4, C6 | **60/60 real scenarios PASS**; 40 ENTRY_ONLY rows (predicted 40); counts equal the engine's; no `other` reason; nothing open after the last bar. Largest price difference on any compared fill 1.4e-8 (A3, half 1 exit), tolerance 1e-5 |
| C5 | 4 DOC rows as predicted: A3HF tp1 1.0100 then stop 0.9850; A3HFM tp1 0.9900 then stop 1.0150 |
| C7 | 4/4 controls detected: A6_CM3 / A6M_CM3 2 FAIL rows each (runner reason `be` for `be_adverse`, M-D3 count 0 for 1); R1_CMF / R1M_CMF 2 halves for 4 (the reversal's short never entered), as predicted |

Observations:
- (b) Monday-open fills now on the first record of the week (e.g. A6 runner "Sell 1@0.997500 at
  22:00:00 Sun" UTC = Sunday 18:00 New York): M-D6 confirmed.
- (b) **Exits sent at a close (exitTrade) fill at the next bar's open under Fill 3** (ZORRO_TRADE_MECHANICS
  §12 R1, open until now): C1, C2, R1, A6, E1, E4a and mirrors all matched the engine's next-open exits.
- (b) **Stop moved beyond the price at a close (probe P2, second half):** control A6_CM3 set the runner's
  stop to 1.0000 at the 0.9980 close; Zorro did not close the trade at that close but at the next tick,
  the next open 0.9975 ("Stop 1@0.997500", A6_CM3 log), the same price as the M-D3 exit at the next open.
  M-D3's explicit exit therefore changes the label and the count, not the fill (on this path).

**Verdict: S4 engine equivalence PASS** (2 runs; run 1 FAIL from setup, recorded above).
Variants: 5 template configurations, 2 planted mutants on 4 assets.
