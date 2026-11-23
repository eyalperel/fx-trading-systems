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
