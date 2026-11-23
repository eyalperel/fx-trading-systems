# NNFX Template — Decisions (Phase 1 step 4)

Decisions taken before any template code, one at a time, in the planning chat.
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.
Each default below is variant 0 of the template; any change is a named, counted variant.

| # | Decision | Status |
|---|---|---|
| T1 | Exit slot | Decided 2026-11-22 |
| T2 | Volume slot | Decided 2026-11-22 |
| T3 | Slot interface and C1 signal type (incl. zero handling A9, bridge-too-far scope A3) | Decided 2026-11-22 |
| T4 | Fill model (entry price; SL / TP1 reference price) | Decided 2026-11-22 |
| T5 | TP1 trigger (touch vs close; same-bar SL and TP1; intrabar stop fills) | Decided 2026-11-22 |
| T6 | One-candle rule | Decided 2026-11-22 (source still to fetch: Ep 39) |
| T7 | Cost model (spread, swap, commission) | Decided 2026-11-22 |
| T8 | Sizing (half split, account-currency conversion, same-currency rule) | Decided 2026-11-22 |
| T9 | Continuation trades (C2, reset, after a stop-loss exit) | Decided 2026-11-22 |
| T10 | Baseline catch-up window; pullback details (A2, A5) | Decided 2026-11-22 |
| T11 | No magic numbers: parameters and sensitivity | Decided 2026-11-22 |
| M-D1..M-D4 | Zorro mechanics decisions (from `ZORRO_TRADE_MECHANICS.md`) | All decided 2026-11-22 |
| M-D5 | Hedge mode | Decided 2026-11-23 |
| — | News rules; dead-market mode | Off by default (no calendar G5; dead market decided 2026-11-01) |

---

## T1 — Exit slot (decided 2026-11-22, user: accept recommendation)

- (a) "If you have no exit indicator yet, use an opposite C1 signal" [V12, A §2.6].
  A C1 flip against the trade always exits, with or without an exit indicator
  (A §4; B §3.3 [M11]). Exit candidates are tested against a gatekeeper
  (RVI or Heikin Ashi) on default settings, after C1, C2 and the baseline (A §5.1).
- (b) Because the C1 flip is already an exit trigger, an empty exit slot and
  "exit = opposite C1" give identical trades. No exit candidate or gatekeeper is
  in the library.
- (c) Variant 0 will close fewer trades by exit signal than VP's aspiration of
  ~9 in 10 (B §2.12); a known property of variant 0, not a defect.

**Decision.** The template has an exit-slot interface (on a closed bar: exit long /
exit short). Default implementation `NONE` = variant 0 [V12]: trades close only on
C1 flip, close across the baseline, stop, TP1 / breakeven, or trailing stop.
A separate exit indicator, tested against a gatekeeper, comes after the engine
checks (Phase 1 step 5) as a counted variant. A11 (exit signal present at entry)
does not arise in variant 0.

## T2 — Volume slot (decided 2026-11-22, user: accept recommendation)

- (a) Volume is a go / no-go gate [V12]; volume or volatility, only one needed
  [V13; SV]; low lag [V12]; adaptive, no fixed per-pair threshold [V13]; MA on the
  indicator makes it adapt [V18]; ignored for continuation trades [V29]; never an
  exit (SV; A §4). VP tests it laid over existing signals, counting losses and wins
  removed [V12; A §5.1].
- (b) The gate only removes entries; it never changes trade management, so it can be
  added later as a test on a fixed base system. No candidate in the library (NATR,
  VolatilityRegime unreviewed; Stonehill's Silence, VIX Fix, MMI, TTM Squeeze absent).
- (c) A blocked entry can change later state (continuation, same-currency allocation),
  so "only removes trades" is exact per entry, approximate per run. Variant 0 results
  are "NNFX without the volume filter" and are labelled so.

**Decision.** Volume-slot interface (closed bar: yes / no). Default `ALWAYS_YES` =
variant 0, labelled "no volume filter". An `ALWAYS_NO` stub is a guard test only: it
must block every standard entry and no continuation entry (V29 waiver). Candidate
selection after the engine checks, by VP's method on the dev set, variants counted.

## T3 — Slot interface and C1 / C2 signal types (decided 2026-11-22, user: accept)

- (a) NNFX: C1 = zero-line cross, two-lines cross or chart indicator [V05]; no
  overbought / oversold logic [V01, V05, V11; A §8]; C2 read as a state, not a fresh
  cross, and of a different type from C1 [V20]; on the line = indeterminate [V20, A9];
  bridge-too-far defined for a two-lines-cross C1 only [V34].
  Fisher: "Fish and Fish delayed by one bar give a crossover system" (TASC V.20:11
  p. 41; `docs/harness/FISHER_SOURCE_REVIEW.md`); Stonehill tested it as a zero cross
  (C25). MESA Stochastic: .2 / .8 crossings (V.32:1). Laguerre RSI: buy after crossing
  back over .2, sell after crossing back down over .8 (*Cybernetic Analysis* p. 221).
  Reflex: no trading rule in the article; Fig. 3 plots it around 0.00; Stonehill
  preferred a colour change to a zero cross (C12), colour change undefined in our sources.
- (b) The MESA Stochastic and Laguerre RSI source rules are crossing-back reversal
  (overbought / oversold) rules, excluded by NNFX. Both outputs are 0-1 (midline 0.5);
  Stonehill treats a midline cross as a zero cross (C21).
- (c) The 0.5 midline reading of MESA Stochastic and Laguerre RSI is our adaptation,
  not a source rule. Strategy 2 (MESA C1 + Laguerre RSI C2) then has C1 and C2 of the
  same type, against V20: open strategy issue, not a template blocker.

**Decision.**
1. Interface: every slot reports a state per closed bar, +1 / -1 / 0 (0 = exactly on
   the line, indeterminate). Signal = state becomes +-1 and the last non-zero state
   was the opposite. C1 flip exit = state becomes opposite to the trade; a move to 0
   alone does not exit (c). Baseline state = sign(close - baseline).
2. Variant 0 readings: Fisher C1 = Fish vs Fish[1] two-lines cross (source);
   MESA Stochastic C1 = 0.5 midline cross (c, our adaptation); Reflex C2 = sign of
   Reflex (zero line); Laguerre RSI C2 = above / below 0.5 (c, our adaptation).
   Fisher zero cross and Reflex colour change are later counted variants.
3. Bridge-too-far on for Strategy 1 (two-lines-cross C1), off for Strategy 2 [V34];
   counting convention (A3) in T10.
4. Strategy 2 same-type C1 / C2 logged as an open strategy issue.

## T4 — Fill model (decided 2026-11-22, user: accept)

- (a) VP decides ~20 min before the daily close and enters with market orders [V11;
  B §5.3 C22]; stop "1.5 the atr away from where the price is right now" [M3].
  Stonehill walkthroughs: "The next candle reflects where we would have entered", at
  the new period's open or just before, or 30 min before the close (C1 §1.2); their
  backtests use "data from the open of each candle" (C1 §1.1). No fill model stated
  (A12; B A3); open-gap handling unspecified.
- (b) Close vs next-open fill differ by the overnight gap (small on FX D1 except the
  weekend; countable). Close fill uses the exact close the signal was computed on: a
  small look-ahead VP only approximates. Zorro's default fill / entry price and the
  D1 bar close time (A17) are NOT stated here from memory: read from the manual and
  checked by a hand-calculated trade in Phase 1 step 5.
- (c) Next-open is conservative (no look-ahead, weekend gaps charged to the trade).

**Decision.** Variant 0: signals on the closed D1 bar; market entry at the next bar's
open; stop and TP1 measured from the actual fill price with the signal bar's ATR,
frozen for the trade (B §2.10). Close fill is a later counted variant.

## T5 — TP1 trigger, stop fills, same-bar order (decided 2026-11-22, user: accept)

- (a) TP1: "once price actually hits the ATR" [V25]; the broker "automatically took
  half of my position off" at +187 [M13] (resting limit, intrabar touch; B A2). Stops
  are resting broker orders; VP checks fills each session [C22; B §3.10]. Breakeven
  after TP1 [M6, C22], applied in the daily maintenance [C22; B §5.3]. Trailing:
  activation on a close >= 2 x ATR beyond entry; moves only on a new closing extreme;
  intraday ignored [M13]. Same-bar stop and TP1: not stated.
- (b) On D1 OHLC, a bar whose range covers both stop and TP1 has an unknown order
  (countable per run). A gap through a level fills at the open (measurable extra
  loss). Close-decided exits fill at the next open (T4).
- (c) Breakeven set at the daily check: the runner keeps its original stop for the
  rest of the TP1 bar. The trailing level is a resting order once placed: fills
  intrabar on touch; its level changes only on closes.

**Decision (variant 0).**
1. Stop and TP1 are resting orders filled intrabar on touch; a gap past a level fills
   at the open.
2. Stop and TP1 inside the same bar (entry bar included): stop first (pessimistic).
   Every run reports the count of such bars; an optimistic-order run is a counted
   sensitivity check that bounds the effect.
3. Breakeven effective from the bar after the TP1 fill.
4. Trailing activates and moves on closes only [M13]; its level fills intrabar on
   touch (c).
5. C1-flip and baseline exits: decided on the close, filled at the next open (T4).
Zorro's intrabar stop handling on D1 bars: checked against the manual and a
hand-calculated trade in step 5, not assumed. Lower-timeframe resolution of the
same-bar order: later refinement.

## T6 — One-candle rule (decided 2026-11-22, user: accept)

- (a) Applies to "everything else", not the baseline [V27]; not to bridge-too-far
  [V34]; the pullback's one candle is a separate exception [V28]. Defined in Podcast
  Ep 39 ("it was episode 39 of the podcast", V27). V27 hint: where C1 caught up a few
  candles after the baseline cross, "if we were to follow the one candle rule we would
  have just never entered". Stated rules without it: C1 signal on the last closed
  candle [V11]; C2 checked when C1 signals [V20]; any indecisive slot = no trade [V03].
- (b) Checked 2026-11-22: Ep 39 is NOT among the 336 fetched videos
  (`~/Documents/nnfx_sources`, 672 files: .vtt + text). Other "one candle" mentions
  (M3, C17, VP Coral profile, Stonehill FRAMA / Geometric Mean MA / RMO) use the words
  in their plain sense; none defines the rule. A1 confirmed as a gap.
- (c) A common outside reading of the rule exists; deliberately not used.

**Decision.** Variant 0: no grace candle; a C1-triggered entry needs every slot to
agree on the signal candle [V11, V20, V03]. Baseline catch-up is separate (T10).

**Open source task (user asked for help later).** Fetch Ep 39 (linked in the V27
video description) with the existing yt-dlp workflow, read it, write the rule from
the transcript, add it as a counted variant before any run that uses it; if it is
core NNFX, decide before seeing results whether it replaces variant 0.

## T7 — Cost model (decided 2026-11-22, user: accept, x2 to start)

- (a) VP trades ~20 min before the close because spreads widen in the hour after it
  [V11]; spreads widen on news [C17]. Weekend gaps and swap not addressed (B G4).
  Stonehill: live-account feed (C1 §1.1). No cost figures in the sources.
- (b) Zorro takes spread, commission, swap and slippage per asset from its asset
  list; values to be read from the file actually used (not from memory) and checked
  in the step-5 hand-calculated trade. T4's next-open fill puts entries and
  close-decided exits at the daily open, VP's widened-spread hour: a typical spread
  understates that cost; no open-hour spread data here, so the size is unmeasured.
  Asset-list swap is fixed while real swaps changed over 2009-2023; swap's share of
  P&L is measurable per run.
- (c) One spread number would hide the T4 conflict (PROJECT_STATE §5 recurring error).

**Decision.**
1. Variant 0: spread, commission, swap from the Zorro asset list per asset; the values
   are written into every run's results header.
2. Every result reported at spread x1 and x2 side by side; x2 is a pre-set stress
   level for open-hour widening (c), not a measured value. A result that holds only at
   x1 is not accepted.
3. Swap share of P&L reported per run, labelled fixed historical swap (c).
4. Guard: costs on vs off must differ by the hand-calculable amount.
Changing the stress level: extra levels may be added any time (sensitivity); the
pass bar (x2) changes only by a dated amendment written before the run it applies
to, counted as a variant.

## T8 — Sizing (decided 2026-11-22, user: accept; sensitivity rule T11 requested)

- (a) Risk 2% of current account value incl. open trades [M3]; user range 0.3-2%
  (2026-11-01). $/pip = Risk$ / (1.5 x ATR pips) [M3; B §1.3]. Two separate trades
  [M13]; Stonehill counts each signal as two half-trades (C1 §1.1); split within the
  2% not stated (B A4). Same currency: one full-risk trade per currency, or 1% + 1%
  [M3]; scope unclear (B A10). Leverage 20:1 [M14]; Stonehill $100k at 20:1.
  Account-currency conversion not given (G1).
- (b) %-of-equity risk compounds: the $ curve depends on trade order; R (P&L /
  initial risk) does not. Lot rounding measurable at $100k. Same-currency rule acts
  only in multi-asset runs (dev set shares EUR and USD). Zorro sizing and pip-value
  conversion: from the manual, checked in step 5.
- (c) Each half 1%, same 1.5 x ATR stop, total 2% (B A4).

**Decision.**
1. Variant 0: 2% of equity at decision time, compounding; configurable 0.3-2%.
2. Two half-positions per signal, 1% each, same stop; one closes at TP1, the runner
   follows T5.
3. $100,000 start, leverage 20:1; lot-rounding error reported.
4. Every result also in R; R is the main comparison measure.
5. Same-currency rule: not applicable to single-asset runs; decided (A10) when
   portfolio runs start.

## T11 — No magic numbers: parameters and sensitivity (decided 2026-11-22, user request)

User: every number gets the sensitivity treatment; variant 0 starts each number at
its recommended (sourced) value. Risk addressed: sensitivity used to pick the best
value of ~12 parameters would be a multi-dimensional optimisation on dev (overfitting).

1. No literal numbers in template logic: every number is a named parameter in one
   config block with its source citation, or labelled (c). A pre-run lint fails on a
   number outside the block; the lint is seen to fire on a planted literal.
2. Sensitivity = robustness, not selection: one parameter at a time around variant 0,
   the rest fixed; read as plateau vs spike.
3. Levels pre-registered before the first strategy run: sourced alternatives (e.g.
   1.25 x ATR stop, V139) or a fixed band around the default (e.g. x0.75 / x1 / x1.25,
   rounded for integers). Not chosen after looking.
4. Every level is a counted variant; reported as a parameter x level table, never as
   one best number.
5. Changing a default after sensitivity results: new counted variant, dev only, dated
   amendment. The confirmation set sees only the frozen system.
6. Parameters that do not move R (starting capital: lot rounding only; leverage:
   only if margin binds, checked) are reported, not varied.

## T9 — Continuation trades (decided 2026-11-22, user: accept)

- (a) V29: no re-entry without a new signal; continuation = was in D and exited,
  price never closed across the baseline against D since, new C1 signal in D. Waived:
  1 x ATR distance and volume [V29]; money management unchanged; any close across the
  baseline = "deal's off" until reset. C2: B §3.4 [C22] states continuation needs the
  confirmation signalling and the rest of the algorithm aligned "but just not the
  volume indicator", so C2 must agree (resolves A §3.4 / A6 (i) from the source).
  After a stop-loss exit: not stated; V29 mentions being "stopped out at the 150 mark"
  as a case continuation helps. Stonehill backtests exclude continuations (C1 §1.1).
- (b) Under T3 a new C1 signal in D means C1 went against D (itself an exit) and
  came back. After a stop / trailing exit C1 may still be in D: no new signal until it
  flips against and back.
- (c) Reset = a close across the baseline against D. Continuation after a stop-loss
  exit allowed (V29 hint).

**Decision.**
1. Continuation entry in D: previous trade in D closed by any exit other than a
   baseline close (C1 flip, exit slot, stop, trailing, breakeven; stop-loss included,
   (c)); no close across the baseline against D since; new C1 signal in D; C2 agrees.
2. Volume and 1 x ATR distance waived [V29]; bridge-too-far not applied [V34].
3. A close across the baseline against D ends the chain (c).
4. Continuation trades reported separately (count, R). Excluding continuation after a
   stop is a counted variant.
5. Guards: ALWAYS_NO volume does not block continuations (T2); a planted baseline
   close kills the chain; a planted C2 disagreement blocks the entry.

## T10 — Baseline catch-up, bridge-too-far counting, ATR for distance, pullback (decided 2026-11-22, user: accept)

- (a) After a baseline cross the others get "ample time", "the next few days" [V27];
  no number (Stonehill host: "a week or so", personal preference, Hull video). The
  1 x ATR rule applies when indicators catch up later too [V28; A §3.6].
  Bridge-too-far: "seven candles before the candle you were looking at right now";
  "seven is a magic number"; 4 back fine, 8 skip; "seven candles definitely fell into
  that territory"; one sentence reads inverted [V34; A3]. Distance from close to
  baseline [V28]; which ATR not stated (A4). Pullback: single candle closes > 1 x ATR
  beyond the baseline; exactly one candle; within 1 x ATR and all agree = enter,
  otherwise no trade [V28]; volume re-check not stated (A5).
- (b) Under T3, C1 flipping into D after the cross is a C1 signal (normal entry); the
  window concerns C2 and volume catching up while C1 agrees. Extra entries per window
  length are countable against a window of 0.
- (c) "No limit except the guards" (A2 option i) is the only reading with no invented
  number.

**Decision.**
1. Catch-up, variant 0: after a baseline cross into D, enter on the first later candle
   where C2 agrees and volume says yes, provided no close back across the baseline, C1
   still in D, close within 1 x ATR. No fixed day limit (A2 option i, (c)). Windows
   N = 1 / 3 / 5 candles are pre-registered counted variants (T11).
2. Bridge-too-far (Strategy 1): skip if the C1 signal is >= 7 candles older than the
   baseline-cross candle (cross candle = 0); counting convention (c); 6 and 8 are
   sensitivity levels.
3. ATR for the distance check: the evaluated candle's ATR (A4, (c)); this is also the
   signal-bar ATR frozen for the trade (T4).
4. Pullback: only when the cross candle closes > 1 x ATR beyond the baseline. Only the
   next candle is checked, all slots re-evaluated incl. volume (c); it must still be
   on the right side and within 1 x ATR, else no trade for that cross; no later
   catch-up for that cross [V28].

## M-D1 — Daily bar close time (decided 2026-11-22, user: accept)

- (a) Daily bars "start and end at BarZone midnight plus BarOffset"; defaults UTC and
  BarOffset 940 = 15:40 UTC for daily bars; `BarZone = EST` = New York with daylight
  saving (Zorro 3.11 manual, barperiod.htm, assetzone.htm). VP's daily close: 2 pm
  Pacific = 17:00 New York (A17).
- (b) No repo script sets BarOffset / BarZone: every D1 bar used so far closed at
  15:40 UTC. Indicator verifications unaffected (synthetic inputs; ATR cross-check on
  identical bars).
- (c) 17:00 New York bars match VP's and most FX charts; the week starts cleanly at the
  Sunday open.

**Decision.** Variant 0: `BarZone = EST; BarOffset = 17*60;` as named config parameters
(T11). Probe P4 checks bar timestamps across a DST change. With T4, entries fall at
17:00 New York, VP's widened-spread hour, covered by T7's x2 check.

## M-D2 — Slippage (decided 2026-11-22, user: accept)

- (a) `Slippage`: "Simulated slippage in seconds (default = 5)", effective in [Test],
  "estimated by extrapolation of the next candle"; "recommended to test systems with and
  without slippage" (Zorro 3.11 manual, spread.htm).
- (b) Its size on daily bars is not stated; measurable by a run with and without it.
  With Slippage = 0, costs are exactly the asset-list spread and rollover
  (hand-calculable: T7 guard, probes P1 / P5).
- (c) Rough size: with ~70 pips daily movement and random-walk scaling,
  70 x sqrt(5 / 86400) ~ 0.5 pip, similar to the 0.8-pip spread and ~0.4% of a
  120-pip stop. Zorro's extrapolation formula is not given, so this is an estimate only.

**Decision.** Variant 0: `Slippage = 0` (named config parameter). The manual default
of 5 s is a T11 sensitivity level run with every result. T7's x2 spread remains the
cost stress.

## M-D3 — Breakeven due while the close is already beyond entry (decided 2026-11-22, user: accept)

- (a) VP: after TP1 the remainder's stop goes to entry, at the daily check [M6, C22].
  Zorro 3.11: "When the Stop is moved inside the price range of the current bar or tick,
  the trade will be immediately closed" (stop.htm); price and timing under Fill = 3 not
  stated.
- (b) Frequency countable per run (needs a > 1 x ATR intrabar reversal). Zorro's
  behaviour if the stop is set anyway: unknown until probe P2.
- (c) At a broker, a stop beyond the market is rejected or executes at market: the
  realistic outcome is "the runner exits now".

**Decision.** Option 1: the template detects the case at the close and exits the runner
at the next open (same handling as other close-decided exits, T5.5), without relying on
Zorro's out-of-range stop behaviour. Count of such events reported per run. The trailing
stop cannot cause it (always 1.5 x ATR behind a close).

## M-D4 — Asset list and account currency (decided 2026-11-22, user: accept)

- (a) Zorro uses `AssetsFix.csv` unless `assetList()` names another file; costs and
  PIPCost come from the loaded list (Zorro 3.11 manual, spread.htm, asset.htm).
- (b) EUR/USD row by list: AssetsFix (2026-06-01) 0.8 pip, no EUR/JPY row;
  AssetsForex (2025-07-28) 1.2 pip, all 28 FX pairs incl. EUR/JPY; AssetsOanda
  (2026-05-20) 0.5 pip; AssetsDarwinex (2020-07-04) 0.5 pip + commission 0.5. Rollover
  values differ between lists, sometimes in sign.
- (c) The default list cannot run the dev set (no EUR/JPY). Account currency inferred
  from PIPCost: EUR for AssetsFix / AssetsForex / AssetsDarwinex, USD for AssetsOanda.

**Decision.**
1. Project copy `config/assets/AssetsNNFX_FX.csv` = byte copy of AssetsForex.csv
   (provenance and sha256 in `config/assets/README.md`), loaded explicitly with
   `assetList()`; its costs are written into every results header.
2. Account currency EUR, starting capital 100,000 EUR. This amends T8's wording
   ("$100,000"), not its substance; comparisons are in R (T8.4).
3. A cheaper list (Oanda / Darwinex spreads) is a later T11 sensitivity level.
BTC/USD is not in the list; crypto handled separately later (no daily NNFX BTC run planned;
BTC data also missing, ZORRO_TRADE_MECHANICS §9).

## T5 amendment — Zorro TICKS mode and the same-bar order (2026-11-22, user: accept)

- (a) Zorro 3.11 mode.htm: without `TICKS` "an intra-bar approximation is used ... a stop
  loss is always triggered earlier than a profit target"; "TICKS should be used when trades
  enter and exit at the same bar"; with TICKS "the price curve inside any bar is evaluated".
- (b) TPL_Probe run 3: without TICKS, entries filled on a bar whose range crossed stop and
  target, and neither fired (gotchas 9d.12). Real history is M1 (ZORRO_TRADE_MECHANICS §6).
- (c) Without TICKS every entry-day stop-out or TP1 is missed: an optimistic bias that breaks
  T5 (the entry bar is checked).

**Decision.**
1. The template sets `TICKS` (`nx_TicksOn = 1`). On M1 history the intrabar order comes from
   the data; Zorro's stop-first rule then applies only inside one history record.
2. T5.2 (stop first when both levels lie inside one daily bar) stays the reference engine's
   rule, since the engine sees daily OHLC only. Equivalence scenarios use intraday paths with
   a stated order; scenario A3 is run low-first (Zorro = T5.2) and high-first (A3HF: Zorro
   takes TP1 on half 1, then stops the runner; documented difference, not a failure).
3. Every real-data run reports the number of trades with stop and TP1 both inside one daily
   bar, so the effect of the order is visible.

## M-D5 — Hedge mode (decided 2026-11-23, user: accept)

- (a) `Hedge` 0: opening a position closes opposite positions of the same asset (default for
  NFA accounts); 1: same, per algo (default for non-NFA accounts); 2: full hedging, "Entering a
  trade will not automatically close opposite positions" (Zorro 3.11 hedge.htm). "Opening a
  trade automatically closes opposite trades when Hedge is 0 or 1" (buylong.htm). Which
  default a backtest gets is not stated.
- (b) Correct template code sends the exit before an opposite entry, so modes 0, 1 and 2 give
  the same trades on correct code.
- (c) With 0 or 1 a missing exit in the template is closed by Zorro and the equivalence
  comparison still passes; with 2 it shows as overlapping long and short trades, which the
  engine never produces, so S4 fails. Mode 2 holds both directions if the template errs, which
  NFA brokers forbid: a live-trading concern, not a backtest one.

**Decision.** Variant 0: `Hedge = 2` as a named config value (`nx_HedgeMode`). Every exit comes
from template code or a trade's own stop / target. Revisit before any demo or live run (NFA
compliance: mode 0 or 4).
