# NNFX Sources — VP rules and Stonehill indicator tests

**Compiled:** 2026-10-30 (Parts A, B) and 2026-11-01 (Part C) from 143 unique videos:
VP / No Nonsense Forex 36 (rules), Stonehill Forex 4 (method) + 103 (indicator tests).
Selected by title triage from 343 videos in 8 playlists. VP's 123 indicator-profile videos
are deferred (read per indicator when it becomes a candidate). Extraction by two agents, each
reading every file in its set in full (coverage lists in Parts A and B).
**Spot-checked** against transcripts: 2% risk, 1.5×ATR stop, trailing activation at a close
2×ATR in profit, 24h news window, dead-market threshold 7, 1×ATR baseline-distance rule,
7-candle "bridge too far", volume ignored on continuations, one-candle rule undefined here.
All confirmed.

**Status: guidelines, not rules.** Every number below is a *default* for the NNFX template,
exposed as a configurable parameter. Changing one is allowed, but under the validation gate
it is a named, counted variant. Ranges are set where the user has stated them; the rest are
fixed when the template is built.

**User decisions (2026-11-01):** risk per trade configurable over **0.3%–2%** (VP default 2%).
Dead-market mode is **optional, off by default** — undecided whether to use it.

Labels: **(a)** source states · **(b)** measurable / codeable · **(c)** inference.
Source keys `[Kn]` are numbered separately within Part A and Part B.

---

## Template defaults (summary)

Synthesis of Parts A and B. Each row cites the part where its sources are listed.

| Area | Default | Label | Part |
|---|---|---|---|
| Timeframe | Daily chart; act on closed candles only; no lower-timeframe entries/exits | (a)(b) | A §7 |
| Entry | C1 signal on last closed candle + price on correct side of baseline + C2 agrees + volume says yes | (a)(b) | A §3.1 |
| Baseline distance | No entry if close is more than 1×ATR from baseline; one-candle wait exception after a large crossing candle | (a)(b) | A §3.2–3.3 |
| Bridge too far | Skip baseline-cross entry if C1 signalled ~7+ candles earlier (two-lines-cross C1 only) | (a)(b) | A §3.5 |
| Continuation | Re-enter on new C1 signal in trade direction if price never closed back across baseline; volume and 1×ATR rule waived | (a)(b) | A §3.4 |
| ATR | ATR(14), from completed candles; value at entry used for the whole trade | (a)(b) | A §2.1, B §2 |
| Risk | 2% of account equity per trade — configurable 0.3%–2% (user) | (a)(b) | B §1 |
| Stop | 1.5×ATR from entry | (a)(b) | B §2 |
| Scale out | Half the position closes at 1×ATR; then the other half's stop moves to breakeven | (a)(b) | B §2 |
| Trailing (2nd half) | Activates after a daily close ≥2×ATR beyond entry; trails 1.5×ATR behind; moves only on new closing extreme | (a)(b) | B §2 |
| Exit | Exit indicator signal, C1 flip, close across baseline, or stop; volume never exits | (a)(b) | A §4 |
| Same-currency exposure | Never two full-risk trades on one currency; pick one or split 1%+1% | (a)(b) | B §6 |
| News | Major event on a currency within 24h: no new trades; close open trades losing or <1×ATR in profit | (a)(b) | B §4 |
| Dead market | **Optional, off by default.** Volume index below ~7 on prior close: TP1 closes whole position, skip USD pairs (VP hedges; untested by him) | (a) | B §5 |

## Open gaps that affect coding

1. **One-candle rule** — referenced in A but defined in podcast Ep 39, not in this set.
2. **Scaling Out video** — not in this set; the 1×ATR first target comes from two other videos (B).
3. **Trailing stop** — A defers it to another video; B's "Trailing Stops" video fills it (above).
4. **Acceptance criteria** — the corpus gives no win-rate / ROI thresholds for indicator tests;
   only a 3-year window for VP's profile series. Ours come from pre-registration. (c)
5. **Dead-market index** — needs a data source available in Zorro, or a stand-in. (c)
6. **News calendar** — VP's event list dates from 2019; rebuild from a current impact calendar. (c)
7. **Stonehill numeric results** — the videos give no win rates or ROI; the numbers are on the
   Stonehill blog, not reachable from this session. Fetch only for shortlisted indicators. (a)

---

## NNFX Rules — Part A: The Algorithm and Its Slots

Source extraction from 21 YouTube auto-caption transcripts (17 No Nonsense Forex / VP, 4 Stonehill Forex).
Extracted 2026-10-30. These are **guidelines / default settings**, not laws. Where the source itself expresses flexibility it is recorded.

### Labels

- **(a)** SOURCE STATES: VP or Stonehill says it (paraphrased; short quotes in "..." only where wording matters).
- **(b)** MEASURABLE: can be coded or tested directly.
- **(a)(b)**: both.
- **(c)** INFERENCE: my interpretation or a gap I filled, with the reason given.

The transcripts are auto-captions without punctuation, and indicator names are often garbled. Quotes are verbatim from the captions, so they may contain caption errors.

### Source key

| Key | Title | URL |
|---|---|---|
| V01 | Forex Indicators - By Far The Best Way To Trade | https://www.youtube.com/watch?v=7Yj0E5FRwBs |
| V03 | The ATR Indicator Is The Single Best Indicator Forex Traders Can Have Use It or Lose It | https://www.youtube.com/watch?v=086ozcHDZPw |
| V05 | Forex Trend Indicators for the No Nonsense Forex Algorithm | https://www.youtube.com/watch?v=YWNloLjXqeI |
| V11 | Forex Indicator Basics With a Bonus | https://www.youtube.com/watch?v=PfquDvN0fwI |
| V12 | Forex Volume Indicator - Our Oxygen Meter | https://www.youtube.com/watch?v=NWqbmPC3bD8 |
| V13 | Volume Indicators Part 2 And A Free Tool | https://www.youtube.com/watch?v=N8Kbk0cwIWg |
| V15 | Lower Time Frames For Entries Exits Podcast Episode 30 | https://www.youtube.com/watch?v=mr6XFnr95wc |
| V16 | Faster Ways To Test Forex Indicators Podcast Episode 32 | https://www.youtube.com/watch?v=V1VeVrHseTM |
| V18 | Putting A Moving Average on an Indicator Makes Things Happen | https://www.youtube.com/watch?v=IxZ1EdqFJcM |
| V20 | My Forex Algorithm - Part 5 Revealed | https://www.youtube.com/watch?v=JxUtee7krFc |
| V23 | Top 100 Forex Indicator - The SSL | https://www.youtube.com/watch?v=Jv6KVnxdCjQ |
| V25 | Exit Indicators - Worth A Lot More Than You Think | https://www.youtube.com/watch?v=1b3D1gNUyiw |
| V27 | Forex Baseline - We Go Deep | https://www.youtube.com/watch?v=x_8wfjTLdoY |
| V28 | Pullbacks In Forex - Don't Get Crazy Here | https://www.youtube.com/watch?v=JssEr6mopDc |
| V29 | Forex Algorithm Trading - Continuation Trades | https://www.youtube.com/watch?v=0SFM5t_XjwQ |
| V34 | Advanced Forex Strategy - NNFX Traders Only | https://www.youtube.com/watch?v=b9HE8q0tobQ |
| V139 | Changes for the Indicator Profile Series in 2025 | https://www.youtube.com/watch?v=3C7LJLFeOgI |
| SE1 | (Stonehill) Exit Indicators A miniseries Part 1 of 3 | https://www.youtube.com/watch?v=m9mQe293vUQ |
| SE2 | (Stonehill) Exit Indicators A miniseries Part 2 of 3 | https://www.youtube.com/watch?v=xGiqDtEZpKg |
| SE4 | (Stonehill) Exit Indicators Part Four | https://www.youtube.com/watch?v=V5Q_QPbEa1U |
| SV | (Stonehill) Trading With Volume | https://www.youtube.com/watch?v=YRLEbYKSYq0 |

Videos that the transcripts point to but that are **not in this corpus** (so their content is unknown here): Podcast ep. 39 "one candle rule", the moving-average-crossover video where the baseline was first revealed, the risk-profile and money-management videos, the trailing-stop video, the standalone indicator-testing podcast, the back-testing blog, the MACD video, Podcast ep. 3, and the Podcast ep. 18 on exit indicators.

---

### 1. Algorithm overview

- **(a)** An "algorithm" is a set of indicators that must all agree. All say long, go long. All say short, go short. "if even one of them is indecisive or tells me to go the other way then I do nothing". [V03; also V01]
- **(a)** NNFX trades with the trend only. No reversal trading and no top or bottom picking: "reversals are for suckers". [V01, V05]
- **(a)** No single standalone indicator is enough. You need a combination that acts as "checks and balances". [V01, V03]
- **(a)** The complete structure across the videos has six slots: ATR, Baseline, Confirmation (C1), second Confirmation (C2), Volume and Exit. VP numbers some of them himself. Baseline is "number two" [V27]. Volume is number five [V12]. C2 is "number 4 and the fifth piece" revealed [V20]. Exit was introduced earlier, in the risk video (not in corpus) [V05, V11]. The baseline was revealed last [V27], and continuation trades complete the algorithm for back-testing [V29].
- **(c)** Slot numbers 1 (ATR), 3 (C1) and 6 (Exit) are not stated explicitly. They are inferred from the remaining positions.
- **(a)** C1 is "the anchor" and "the nucleus". C2, volume and the other pieces exist to eliminate losses that C1 gives. "half of my entire algorithm is dedicated to cutting down my losses". [V12, V20]
- **(a)** "We win by not losing": removing a loss is worth as much as adding a win. [V12, V20, V34]
- **(a)** Money management and trading psychology matter more than technical analysis. The algorithm adds percentage points above a 50% coin flip. [V01, V20]
- **(a)** Final chart layout: price with the baseline on it, plus "three indicators below" (C2, volume and so on). The ATR is pulled up only to read its value and then removed. [V20, V03]

---

### 2. Slot-by-slot guidelines

#### 2.1 ATR

- **(a)(b)** Period 14, default settings: "I do 14 periods" [V03]. "the ATR 14 I can't think of anything better than that" [V16].
- **(a)** VP calls it the most important indicator. It is used for money management and position sizing, not for direction, and should be consulted on every trade. [V03]
- **(a)(b)** Position size is set as a **pip value**, scaled inversely to ATR. Worked example: EURGBP ATR 41, GBPNZD ATR 125, so about 1/3 of the pip value on GBPNZD ($6/pip vs $2/pip). [V03]
- **(a)(b)** Read the ATR from **completed** candles only. If you trade after the daily close, read the value of the last fully closed candle, not the forming one (example: 158 shown vs 162 true). [V11]
- **(a)(b)** VP's own practice is to measure about **20–30 minutes before the daily candle closes**; at the weekend, use the Friday close. [V03] He trades about 20 minutes before the daily close because spreads widen in the hour after the close. [V11]
- **(a)** Do not use the ATR line as the volume/volatility filter (see 2.5). VP uses "the figure", not the line. [V13]
- **(a)(b)** Normal risk is **2%** per trade ("a full 2% trade"). VP drops this to 1.5–1.75% when his optional EVZ check is below threshold (see 2.5). [V13]
- **(c)** Coding implication: lots = (risk% × equity) / (SL distance in pips × pip value per lot), where SL distance = 1.5 × ATR (see 4). The corpus gives only the inverse-ATR scaling idea and the 1.5×ATR stop. This formula combines the two, and the risk-profile video that probably states it is not in the corpus.

#### 2.2 Baseline

- **(a)** The baseline is an on-chart line (VP's examples use a **20-period SMA**). It is searched among "a lot of different moving averages". [V27, V28, V29, V34]
- **(a)(b)** **Entry signal:** price crosses the baseline **and the candle closes beyond it**. This is only a signal; the rest of the algorithm must also agree. [V27]
- **(a)(b)** **Exit:** if a candle closes on the opposite side of the baseline, "even if it's the very next candle", exit immediately. This often triggers before the trailing stop or the exit indicator. [V27; also V34: "once it closed back down across your baseline we always exit"]
- **(a)** It is also a **direction filter for C1 signals**: a C1 short signal with price above the baseline is not taken ("this is your baseline doing its job"). [V29, V27]
- **(a)** Scan both C1 **and** the baseline for new signals on every chart. Before the baseline was added, only C1 was scanned. [V27]
- **(a)** Placement: it must be "close but not too close" to where the rest of the algorithm signals. Too far away means it never agrees or enters too late. Too close means it always agrees and filters nothing. Fine-tune it through its settings. [V27]
- **(a)** You don't want the baseline making your C1 worse. If the baseline repeatedly enters much later than C1, retune the baseline. [V27]
- **(a)** Ignore the slope of the baseline. "in your algorithm you're going to ignore this"; "ignore where this line is tilting". [V27]
- **(a)** A good baseline should "add wins, eliminate losses altogether and then help mitigate the losses you do take". [V27]
- **(a)** The **one candle rule does not apply to the baseline**: after a baseline cross, the other indicators get "ample time to catch up". "Monitor that for the next few days." [V27] See 3.5 and Ambiguities A1–A3.
- **(a)** Do not back-test baselines until the continuation-trade video. After that, back-test the full algorithm. [V27, V29]

#### 2.3 Confirmation indicator 1 (C1)

- **(a)** Purpose: it tells you to go long, go short or do nothing. It is the "lynchpin" of entries. "if your main confirmation indicator is not telling you to take a trade then it doesn't matter what your other indicators say". [V11, V12]
- **(a)** Three acceptable types. Skip any trend indicator that is not one of them [V05]:
  1. **Zero-line cross** (oscillator flips sign).
  2. **Two lines cross** (whichever line is above gives the direction).
  3. **Chart (overlay) indicator** (on price, e.g. SuperTrend, PSAR, SSL; flips colour or side).
- **(a)** Good C1 qualities: not too early or choppy (too many signals in non-trending markets), not too late (misses most of the trend), and it avoids whipsaw / false-trend periods. [V05]
- **(a)** It must be consistent across pairs: "it might work amazing on one currency pair but then you put it on another one it falls apart that's no good". [V05]
- **(a)(b)** A signal is read only on a **closed candle**, and it must occur on the last completed candle: "we're not worried about what happened a few candles ago". [V11]
- **(a)** In VP's experience, about 9 out of 10 charts show no C1 signal on a given day. [V11]
- **(a)** You can turn a one-line indicator into a two-lines-cross C1 by applying an SMA to its data (MT4 "Apply to: First Indicator's Data"; 10-period simple in the demo). [V18]
- **(a)** A C1 that is fast can also act as an exit. C1 flipping against the trade always means exit (see 4). [V25, V29, V12]
- **(a)** Quality vs quantity of signals "really doesn't matter", "what matters is the ROI": pips at year end. [V16]

#### 2.4 Confirmation indicator 2 (C2)

- **(a)** Purpose: check C1 and eliminate more of its losses without eliminating wins. [V20]
- **(a)** C2 should be a **different type** from C1. For example, if C1 is a two-lines cross, C2 should be a zero-cross or chart indicator. The two should "accomplish the same goal but operate differently". [V20]
- **(a)(b)** Usage: C1 makes the decision. When C1 signals, check the **state** of C2 (e.g. line above or below zero / its signal line). "if they agree it's a trade if they disagree it's not a trade". A fresh C2 cross is not required. [V20]
- **(a)** VP: "I can't remember the last time my secondary confirmation indicator knocked me out of a win". [V20]
- **(a)** Candidates often come from indicators that were tested for C1 and came close. [V20]

#### 2.5 Volume (volume or volatility filter)

- **(a)** What "volume" means in NNFX: the "oxygen" or "gas in the tank" that makes price trend. VP uses the word loosely to cover volume **and** volatility. [V12, V13]
- **(a)** A volume indicator or a volatility indicator is acceptable. You need **only one**: pick the best from either category. [V13; Stonehill SV agrees: "a volatility indicator can be used in place of a volume indicator but you don't need both"]
- **(a)** Momentum indicators are excluded, because changes in momentum mean reversals. [V13]
- **(a)(b)** Function: a go / no-go gate. If volume is not there, do not trade, "I don't care if the rest of your indicator is telling you this is your green light". [V12]
- **(a)** It should **lag as little as possible**. [V12]
- **(a)** It should **adapt to the market on its own**. A fixed threshold that must be moved per pair and per regime (e.g. an ATR line at 115 pips on GBPJPY) is rejected: it gives no consistency, and back-testing becomes impractical. [V13]
- **(a)** Putting a moving average on a volume/volatility indicator instead of a fixed level makes it adapt ("the moving average adjusts to where volume already is"). [V18]
- **(a)** Expect it to occasionally block a good winner. Accept this, because the losses it removes matter more. [V12]
- **(a)** Ignore the volume indicator for **continuation trades** (see 3.4). [V29]
- **(a)** **Optional, not part of the algorithm:** VP checks the CBOE EuroCurrency volatility index ($EVZ on barchart.com) daily. Below his line (**8**, formerly 8.5) he reduces risk from 2% to 1.5–1.75%, and at "crazy low" levels he stopped trading altogether. "these are not hard rules". Drop it if it causes confusion. [V13]
- **(a)** ADX with a level at 25 is used purely as a demonstration of a **bad** volume indicator (it is in VP's "Dirty Dozen"). Even it removed 5 of 8 losses on one chart, but it also removed winners. [V12, V18]

#### 2.6 Exit indicator

- **(a)** Roles [V25]:
  1. Exit winners near the end of the move (after half has been taken off at TP1) before the trailing stop is hit.
  2. Exit losers before the stop-loss is hit. "price should almost never hit your stop-loss".
  3. Exit trades that stall ("doesn't go anywhere at all") for a small gain or loss.
- **(a)** It is used on almost every trade. It should get you out far more often than the stop or trailing stop does. [V25]
- **(a)** It can be the same as C1 (VP's C1 currently also exits him), but "don't force it just for the sake of simplicity". [V25]
- **(a)** If it is a separate indicator, it only needs to be on the chart after entry. [V25]
- **(a)** Good candidate types: **two-lines cross** ("a really good exit indicator is typically a two lines cross" [V18]), your best **reversal** indicator (used only to exit, never to enter), and Heikin Ashi colour change. [V25] SuperTrend "might work better as an exit indicator". [V05]
- **(a)** Purpose of an exit signal: momentum is probably done and the market is entering consolidation. It does not have to predict a reversal. [V25]
- **(a)(b)** Read exit signals on a **closed** candle (RVI example: the line crosses back, the candle closes, then exit). [V25]
- **(a)** The SSL Channel is used as both C1 and exit ("you're kind of tied to using both ends of this thing"). [V23]
- **(a)** If you have no exit indicator yet, use an opposite C1 signal. [V12]

---

### 3. Entry rules

#### 3.1 Standard entry: all slots agree

- **(a)(b)** Required for a standard entry: C1 signal (or baseline cross, see 3.2), price on the correct side of the baseline, C2 agrees, volume says yes, and price no more than 1×ATR from the baseline. All of these are evaluated on the **closed** daily candle. [V03, V11, V12, V20, V27, V28]
- **(a)** Daily routine: first manage open trades (close, take half off, adjust the stop). Then lock onto C1, and now also the baseline. If neither signals, move to the next chart. If one signals, "go through your progression on the rest of your structure". [V11, V27]
- **(a)** You must "wait for the candle to close first". Intrabar signals are "incorrect data". Turn indicator alerts off. VP's compromise is to act about 20 minutes before the daily close. [V11, V23]
- **(c)** In Zorro this means evaluating all rules on the completed D1 bar and entering at the next open (or at the close, emulating "20 minutes before close"). The source does not specify a fill model.
- **(a)** For flip-type chart indicators: "the first candle you see afterwards will be your entry candle" (SSL). [V23]

#### 3.2 Baseline-cross entry

- **(a)(b)** Signal: the candle closes beyond the baseline. Then check that C1 is in agreement (state), C2 agrees and volume is yes. [V27]
- **(a)** If the others have not caught up, note the pair and monitor it "for the next few days". Entry is allowed when they catch up, still subject to the 1×ATR rule (3.6). [V27, V28]
- **(a)(b)** **"Bridge too far"** (advanced, optional, test it yourself) [V34]:
  - It applies when C1 is a **two-lines cross**. VP does not know how well it works with zero-cross or chart C1s.
  - It is a classic baseline entry. If C1 gave its signal in that direction **7 or more candles** before the current candle (and never flipped since), do not take the trade: "seven is a magic number". It counted as 4 candles back = fine; 8 = skip.
  - "the one candle rule don't apply here". It happens about once a year per pair; in VP's experience these trades almost always lose.

#### 3.3 Pullback entry (only one situation)

- **(a)(b)** It applies **only** when a single candle (not a series) crosses the baseline and closes **more than 1×ATR beyond it**. Distance is measured from the candle close to the baseline. [V28]
- **(a)(b)** Do not enter that candle. Give price **one candle** to pull back. If at the next check price is within 1×ATR of the baseline and everything still agrees, enter. Otherwise there is no trade. [V28] Example: ATR 80, close 100 pips beyond the baseline means no entry. Next day 72 pips beyond means enter.
- **(a)** This is "an exception to that exception": the baseline is exempt from the one candle rule, but the pullback gets exactly one candle. [V28]
- **(a)** Nowhere else: "pullback-itis" is forbidden. If ATR = 80 and price is 79 pips away and the system says go, go. Waiting for a discount makes you miss big winners. [V28]

#### 3.4 Continuation trades

- **(a)** After you exit (by the exit indicator or a C1 flip), you cannot re-enter until a new signal. [V29]
- **(a)(b)** Continuation entry: you were in a trade in direction D and exited. Price has **never closed across the baseline against D** since. C1 gives a **new** signal in direction D. Then re-enter in D. [V29]
- **(a)** For continuation trades **only**, two rules are waived: (1) the 1×ATR distance-from-baseline rule, and (2) the volume indicator ("completely ignore your volume indicator"). [V29]
- **(a)** Money management is unchanged (ATR, risk profile). There is no baseline "safety net". [V29]
- **(a)** If any candle crosses and closes across the baseline, "deal's off" until "that whole thing resets". [V29]
- **(a)** With a C1 that is a zero-cross plus an MA, a continuation signal is both lines already beyond zero and crossing again in the trend direction (MACD-style). [V18, V29]
- **(a)** VP calls these probably the most profitable trades of your career. [V29]
- **(c)** The source does not say whether C2 must still agree on continuation trades. Because only volume and the ATR-distance rule are explicitly waived, the default reading is that C2 still applies.

#### 3.5 Signal-timing rules (summary)

| Rule | Applies to | Content | Label / source |
|---|---|---|---|
| Closed-candle rule | all indicators | read only after the candle closes (or about 20 min before) | (a)(b) V11, V23, V27 |
| Current-candle C1 | C1-triggered entries | the signal must be on the last completed candle | (a) V11 |
| One candle rule | "everything else" except the baseline | **definition not in corpus** (Podcast ep. 39) | (a) V27, V34; content: gap |
| Baseline catch-up | baseline-triggered entries | others get "ample time", "next few days" | (a) V27 |
| Pullback | single candle > 1×ATR past the baseline | exactly 1 candle to come back within 1×ATR | (a)(b) V28 |
| Bridge too far | baseline entry, two-lines-cross C1 | C1 signal ≥ 7 candles old means no trade | (a)(b) V34 |

#### 3.6 Do-not-enter conditions

- **(a)(b)** Price closes more than 1×ATR from the baseline at the moment of entry, including when the indicators catch up later. "don't even wait for a pullback". The only exception is a continuation trade. [V28, V29]
- **(a)(b)** The volume indicator says no (except continuation trades). [V12, V29]
- **(a)(b)** C2 disagrees, or the baseline is on the wrong side. [V20, V29]
- **(a)(b)** Bridge too far (see 3.2). [V34]
- **(a)** Any slot is indecisive. [V03] In a back-test, a C2 sitting right on the zero line was treated as unknown, and the loss was not removed. [V20]
- **(a)** The signal exists only intrabar. [V11, V23]
- **(a)** Lower-timeframe or weekly "confirmation" must not veto a daily setup (see 7). [V15]
- **(a)** Unusual "huge goofy candles that screw up your indicators" may be a reason not to enter. This refers to an old podcast that is not in the corpus. [V23]
- **(a)** Avoid "obvious elections" and similar known-risk events (flash-crash discussion). [V15]
- **(a)** After an exit, do not re-enter without a new signal. [V29]

---

### 4. Exit and stop/target rules

- **(a)(b)** **Stop loss = 1.5 × ATR.** "we put our stop loss at one point five times the ATR". [V25]
- **(a)(b)** **Take half off at 1 × ATR**: "take half of our profit off the table once price actually hits the ATR". [V25]
- **(a)** VP knows this looks like 1 : 1.5 "on the surface". The nuance is that the exit indicator should get you out well before the stop is hit. [V25]
- **(a)** For the remaining half, use a trailing stop "after a certain point". It protects against catastrophic opposite candles. Details were deferred to a trailing-stop video that is not in the corpus. [V25]
- **(a)** Never cap your upside with fixed R:R targets (2:1, 3:1). The money comes from big runs (500–1,500+ pips), and small wins mainly offset losses. [V15]
- **(a)(b)** Exit triggers. Any one of these closes the trade:
  - The exit indicator signals (on a closed candle). [V25]
  - The candle closes on the opposite side of the baseline. [V27, V34]
  - C1 flips against the trade. [V12, V29]
  - The stop is hit, or the trailing stop on the remainder is hit. [V25]
- **(a)** The volume indicator is never used to exit. Stonehill states it explicitly (SV: "you never use a volume indicator as an exit indicator"). VP's examples never use it to exit.
- **(a)** Do not manage or exit on lower timeframes. Let the trade "breathe" and accept giving back part of a run (e.g. 500 becomes 275 pips). [V15]
- **(a)(b)** The Indicator Profile Series 2025 uses a **1.25 × ATR** stop for gold and Bitcoin. This was Dan's choice for testing; "you can make this shift if you like". [V139]
- **(a)** Stonehill: always have hard take-profit and stop-loss levels in place as well as exit signals. Stonehill criticises fixed ratios and round-number levels because "everybody knows what your business is". [SE2]
- **(c)** Whether the exit indicator, baseline or C1 exit closes **both** halves is not stated explicitly. VP's wording ("you just exit", "immediately exit that trade") suggests the whole remaining position. The stop handling after TP1 (e.g. breakeven) is not stated in the corpus.

---

### 5. Indicator testing method

#### 5.1 VP's method

- **(a)** Test everything; you cannot judge a tool you have not tested. "Testing" means downloading the indicator and running it through a back-test. VP has tested over 2,000 indicators and seen more than 5,000. [V01, V16]
- **(a)** Test each slot in isolation, in order [V05, V12, V20, V25, V27, V29]:
  - **C1** on its own: back-test with the ATR-based risk profile so that wins and losses are real. "you need to know your stop-loss would have been". [V05]
  - **C2**: C1 + C2 only, with the ATR used just to score wins and losses. "leave everything else out of it". Record which C2 "takes away the most losses while still preserving the wins". [V20]
  - **Volume**: overlay it on existing C1 signals. Count the losses it removes **and** the wins it removes. [V12]
  - **Exit**: use a **gatekeeper** benchmark (e.g. RVI or Heikin Ashi). A new exit indicator on **default settings** must beat the gatekeeper, otherwise move on: "tweaking it is probably not going to make it that much better". Test it in different market types, including stretches with many losses. [V25]
  - **Baseline**: search now, but back-test only after the continuation-trade rule is known. Then back-test the full algorithm and forward-test it. [V27, V29]
- **(a)** Pre-filters for discarding indicators without testing [V16]:
  1. It just follows price.
  2. The creator's own screenshot shows it working poorly.
  3. It gives too many conflicting signals (buy and sell in quick succession).
  4. It draws support/resistance, including dynamic S/R.
  5. It cannot be modified (exception: ATR 14).
- **(a)** A type filter applies too: if it is not a zero-cross, two-lines-cross or chart indicator, skip it [V05]. About 70–75% of indicators "are just not the type that we're looking for" [V01]. Reversal-designed indicators can be skipped for entry slots [V01].
- **(a)** Settings: try other settings before rejecting an indicator. Example: ROC 10 → 20 removed many false signals; one of VP's own algorithm indicators "was awful" on its default. Defaults are sometimes best (ATR). [V05, V01]
- **(a)** Use common pairs and the daily chart. "we don't cherry-pick". Reuse the same chart across demos. The indicator must hold up across pairs. [V05, V20]
- **(a)** Judge on ROI (pips per year), not on signal count. [V16] VP's goal is indicators that are right "far more than 50% of the time". [V01] No numeric acceptance threshold is given in the corpus.
- **(a)** Keep testing alternatives in the background: "the Holy Grail is always out there". [V12, V13]
- **(a)** VP's funnel: about 2,000 tested; 19 in 20 unusable, leaving about 100 usable, about 50 really good, and 7 in VP's current algorithm. [V05]
- **(a)(b)** Indicator Profile Series rules from 2025 (VP + Dan) [V139]:
  - Test window **3 years** (was 1 year). Results are percentage-based.
  - No more 4H testing.
  - 1.25×ATR stop for gold and Bitcoin.
  - "Chalks" (trades that hit neither the stop nor any take-profit) are excluded from the trade count.
  - Re-test in your own system; "the real gold" is the introduction to the indicator, not the results table.
- **(a)** The standalone-test podcast and the back-testing blog are referenced for the detailed procedure, but they are not in the corpus. [V01, V12, V29]

#### 5.2 Stonehill's method (from the 4 Stonehill files)

- **(a)** Volume indicators are always tested against something: Stonehill uses an **SMA(20) baseline** as the reference signal generator. "How you decide to test volume indicators is up to you": any baseline, any C1 or any combination. [SV]
- **(a)(b)** There are three volume rules [SV]:
  1. On a long or short signal, check volume. If it does not say yes, do nothing.
  2. Once a trade is open, you no longer need the volume indicator.
  3. Never use volume as an exit.
- **(a)** Volume does not determine direction: "it only gives you a yes ... or a no". [SV]
- **(a)** Read-out examples: Normalized Volume histogram above a threshold of 100, Silence above its midline, and TTM-squeeze-type dots turning green. Thresholds are per indicator. [SV]
- **(a)** For a practice drill, mark up printed charts by hand to sharpen signal identification. This drill does not track ATR or wins/losses. Feel free to tweak settings. Beware "backwards bias" (hindsight) when judging. [SV]
- **(a)** Exit-indicator classification comes from blogs and VP's profile videos. Indicators are graded "possible" (may work with tweaked settings) or "good/yes"; those that "didn't make the cut" are omitted. Stonehill uses default settings in the images, with visual changes only. MBFX Timed was the stated exception, with its settings changed. [SE1, SE2, SE4]
- **(a)** Exit-candidate types used in the taxonomy: below-chart zero-cross, two-lines-cross, histogram, colour-change, hybrid (zero-cross or two-lines), and price-overlay colour-change or two-lines-cross. [SE1, SE2, SE4]
- **(a)** Different-looking indicator types "can help provide a higher degree of confidence". [SE4]
- **(c)** The Stonehill files contain **no quantitative testing protocol** (no pairs, period, win-rate or ROI criteria). The quantitative results live in their blogs, which are not in the corpus.

---

### 6. Numeric parameter table

| Parameter | Value | Label | Source URL |
|---|---|---|---|
| ATR period | 14 | (a)(b) | https://www.youtube.com/watch?v=086ozcHDZPw ; https://www.youtube.com/watch?v=V1VeVrHseTM |
| ATR measurement time | 20–30 min before daily close; Friday close at weekend | (a)(b) | https://www.youtube.com/watch?v=086ozcHDZPw |
| ATR measurement if after close | use last fully closed candle's value | (a)(b) | https://www.youtube.com/watch?v=PfquDvN0fwI |
| VP trade time | ~20 min before daily close (close stated as 2:00 PST in the video) | (a)(b) | https://www.youtube.com/watch?v=PfquDvN0fwI |
| Stop loss | 1.5 × ATR | (a)(b) | https://www.youtube.com/watch?v=1b3D1gNUyiw |
| Partial take-profit | 50% of position at 1 × ATR | (a)(b) | https://www.youtube.com/watch?v=1b3D1gNUyiw |
| Stop loss (gold, BTC, profile series 2025) | 1.25 × ATR | (a)(b) | https://www.youtube.com/watch?v=3C7LJLFeOgI |
| Risk per trade | 2% ("full trade") | (a)(b) | https://www.youtube.com/watch?v=N8Kbk0cwIWg |
| Reduced risk on low EVZ | 1.5–1.75% | (a)(b) | https://www.youtube.com/watch?v=N8Kbk0cwIWg |
| EVZ threshold (optional macro tool) | 8 (formerly 8.5) | (a)(b) | https://www.youtube.com/watch?v=N8Kbk0cwIWg |
| Max distance close→baseline at entry | 1 × ATR | (a)(b) | https://www.youtube.com/watch?v=JssEr6mopDc |
| Pullback wait | exactly 1 candle | (a)(b) | https://www.youtube.com/watch?v=JssEr6mopDc |
| Bridge-too-far C1 signal age | ≥ 7 candles → no trade | (a)(b) | https://www.youtube.com/watch?v=b9HE8q0tobQ |
| Example baseline | SMA 20 | (a)(b) | https://www.youtube.com/watch?v=x_8wfjTLdoY ; https://www.youtube.com/watch?v=YRLEbYKSYq0 |
| MA applied to an indicator | SMA 10 (demo, "just leave it on ten") | (a)(b) | https://www.youtube.com/watch?v=IxZ1EdqFJcM |
| ADX volume level (demo of a bad indicator) | 25 (period 14) | (a)(b) | https://www.youtube.com/watch?v=NWqbmPC3bD8 ; https://www.youtube.com/watch?v=IxZ1EdqFJcM |
| ROC demo | default 10; 20 better | (a)(b) | https://www.youtube.com/watch?v=YWNloLjXqeI |
| Aroon Up/Down default | 14 | (a)(b) | https://www.youtube.com/watch?v=YWNloLjXqeI |
| SSL Channel default | 10 | (a)(b) | https://www.youtube.com/watch?v=Jv6KVnxdCjQ |
| RVI as exit | default 10, VP prefers 8 ("default is as high as you should go") | (a)(b) | https://www.youtube.com/watch?v=1b3D1gNUyiw |
| Normalized Volume threshold (example) | 100 | (a)(b) | https://www.youtube.com/watch?v=YRLEbYKSYq0 |
| Indicators in algorithm | "four to six"; elsewhere 7 (6 shown + 1 situational) | (a) | https://www.youtube.com/watch?v=086ozcHDZPw ; https://www.youtube.com/watch?v=YWNloLjXqeI |
| Pairs traded by VP | 27 → 28 (FX + metals) | (a) | https://www.youtube.com/watch?v=PfquDvN0fwI ; https://www.youtube.com/watch?v=b9HE8q0tobQ |
| Profile-series test window | 3 years (was 1) | (a)(b) | https://www.youtube.com/watch?v=3C7LJLFeOgI |
| Timeframe | Daily (D1) only | (a)(b) | https://www.youtube.com/watch?v=YWNloLjXqeI ; https://www.youtube.com/watch?v=mr6XFnr95wc |
| Big-run size that drives P&L | 500–1,500+ pips | (a) | https://www.youtube.com/watch?v=mr6XFnr95wc |
| Share of indicators of the wrong type | 70–75% | (a) | https://www.youtube.com/watch?v=7Yj0E5FRwBs |
| Indicator funnel | ~2,000 tested → ~100 usable → ~50 good → 7 used | (a) | https://www.youtube.com/watch?v=YWNloLjXqeI |
| Charts with no C1 signal on a day | ~9 of 10 | (a) | https://www.youtube.com/watch?v=PfquDvN0fwI |
| Volume value illustration | 20 trades/month, ±100 pips, 1 win and 3 losses removed → +200 pips/month | (a) illustrative only | https://www.youtube.com/watch?v=NWqbmPC3bD8 |
| Bridge-too-far value estimate | 20 events/yr × 50 pips = 1,000 pips/yr | (a) illustrative only | https://www.youtube.com/watch?v=b9HE8q0tobQ |

---

### 7. Timeframe and lower-timeframe rules

- **(a)(b)** Trade the daily chart only: "stay on the daily chart religiously". [V15; V05: "I only use the daily timeframe"]
- **(a)** Do not use 4H or 1H to manage or exit a daily trade. That is "trading by feel" and cuts big runs short. [V15]
- **(a)** Do not use lower timeframes for better entries. The daily is "the most accurate chart", and a lower timeframe often makes the setup look like a FOMO trade, which talks you out of good trades. [V15]
- **(a)** Do not use the weekly chart for bias. VP says it is less accurate, because fundamentals can override it within a week, and long-term trends contain 500–800-pip retracements worth trading. [V15]
- **(a)** One MACD continuation illustration uses an AUDUSD 4H chart. This is an illustration only. [V29]
- **(a)** The Indicator Profile Series dropped 4H testing in 2025, implying it existed before. [V139]

---

### 8. Things VP says to avoid in the algorithm

- **(a)** Reversal and overbought/oversold logic for entries (stochastic crosses, RSI 30/70 and similar). Forex "cannot" be overbought or oversold. [V01, V05, V11]
- **(a)** Support/resistance, trend-line, Fibonacci or price-action tools, and S/R-drawing indicators. [V01, V16]
- **(a)** Indicators that just mirror price, cannot be modified, or flip-flop. [V16]
- **(a)** Fixed-threshold volume filters that need constant manual adjustment (e.g. an ATR line). [V13]
- **(a)** Lower timeframes and the weekly chart. [V15]
- **(a)** Fixed R:R take-profits that cap the upside. [V15]
- **(a)** "Pullback-itis": waiting for discounts outside the single defined case. [V28]
- **(a)** Acting on intrabar signals and alerts. [V11, V23]
- **(a)** Re-entering after an exit without a new signal. [V29]
- **(a)** Relying on one standalone "holy grail" indicator. Combining weak tools to prop each other up is also wrong; combine individually strong tools that "play well together". [V01, V20]

---

### 9. Conflicts

| # | Topic | Statement 1 | Statement 2 | Note |
|---|---|---|---|---|
| K1 | Volume gate | Never trade without volume, "doesn't matter what your other indicators are saying" (V12) | Completely ignore volume for continuation trades (V29) | The source itself makes this an exception. Code as: continuation trades skip the volume check. |
| K2 | Baseline distance | Never enter if close is > 1×ATR from the baseline (V28) | Rule waived for continuation trades (V29) | Same kind of source exception as K1. |
| K3 | Fixed targets | Never cap the upside; 2:1 or 3:1 ratios are "silly" (V15) | TP on half at 1×ATR, SL 1.5×ATR (V25); Stonehill: "always have" hard TP and SL (SE2) | (c) Consistent if only half the position has a TP and the runner is managed by trailing stop and exit signals. Stonehill's "always" TP could be read as a TP on the runner too. |
| K4 | Stop multiple | 1.5×ATR (V25) | 1.25×ATR for gold and BTC in profile tests (V139) | V139 says it is optional and only Dan's choice. |
| K5 | Volume filter form | ADX with a fixed level of 25 as the demo (V12) | Fixed lines rejected for lack of consistency (V13); MA on the indicator preferred (V18) | VP's own position changed between videos. The later videos favour adaptive thresholds. |
| K6 | Timeframe | Daily only (V05, V15) | Profile series ran 4H tests until 2025 (V139); 4H MACD example (V29) | The 4H material is for testing or illustration only. No 4H trading rules are given. |
| K7 | Indicator count | "four to six indicators" (V03) | 7 indicators in the algorithm (V05); final layout = baseline + 3 below + ATR (V20) | These are different points in time; no coding impact. |
| K8 | Scan order | Lock onto C1 only; if no C1 signal, move on (V11) | Scan both C1 and baseline (V27) | V27 is later and supersedes V11 once a baseline is in use. |
| K9 | Fresh signal vs catch-up | C1 signal must be on the latest closed candle; "not worried about ... a few candles ago" (V11) | After a baseline cross, others may "catch up" over "the next few days" (V27); Stonehill entry taken when volume crossed up "a handful of periods" after the SMA cross (SV) | These are different trigger types. Combined with V34 (C1 ≥ 7 candles old = skip), the windows overlap and are not specified precisely (see A2). |

---

### 10. Ambiguities and gaps

- **A1. One candle rule (gap).** It is referenced in V27 and V34 as applying to "everything else" but not to the baseline, and its definition is in Podcast ep. 39 (not in corpus). V27 gives one hint: a trade where C1 caught up a few candles after the baseline cross "if we were to follow the one candle rule we would have just never entered". Do not code it from this corpus; it needs the ep. 39 source.
- **A2. Baseline catch-up window.** "ample time", "next few days" (V27) gives no number. Possible codings: (i) no limit other than the 1×ATR rule and the bridge-too-far rule; (ii) a fixed N candles. Bridge-too-far (V34) limits the age of the C1 signal, not how long you wait after the baseline cross.
- **A3. Bridge-too-far counting.** "seven candles before the candle you were looking at right now"; "eight candles ago you could debate it but seven candles definitely fell into that territory" (V34). The second sentence reads inverted, possibly a misspeak or caption error. Possible codings: skip when C1-cross age ≥ 7 bars, or > 7 bars, counting the current bar as 0 or 1. It applies only to a two-lines-cross C1 (V34); its use for other C1 types is untested.
- **A4. ATR distance.** It is measured from the candle **close** to the baseline (V28, explicit). Which ATR value applies is not specified: the signal candle's, or the current one when the indicators catch up. (c) The natural reading is the ATR at the candle being evaluated.
- **A5. Pullback check moment.** "if by the same time tomorrow price is now 72 pips beyond your baseline" (V28). Since VP trades before the close, this is effectively the next candle's close vs that candle's baseline. It is not stated whether price may have closed back across the baseline in between, or whether the volume check is redone.
- **A6. Continuation trades.** Two points are not stated. (i) Whether C2 must still agree (only volume and ATR distance are waived). (ii) When the setup "resets": (c) probably a fresh baseline cross in the trade direction. Also unspecified is whether a continuation trade is allowed after a **stop-loss** exit, not only an exit-indicator or C1 exit. V29 mentions being "stopped out at the 150 mark" as a case continuation trades help with.
- **A7. Exit scope after TP1.** The source does not say whether the exit indicator, baseline or C1 exit closes the whole remaining position, or what happens to the stop after TP1 (breakeven or trail). Trailing-stop details were deferred to a video not in the corpus (V25).
- **A8. TP1 trigger.** "once price actually hits the ATR" (V25) suggests an intrabar touch (limit order) measured from entry. Close-based is the other possible reading.
- **A9. C2 or C1 reading at the zero line.** V20 treats it as indeterminate in back-testing. A coding rule for exactly 0 (or for a crossing on the same bar) is needed.
- **A10. Volume "yes" with an MA overlay.** V18 shows a volume indicator plus an MA but never states the rule. (c) The likely reading is volume above its MA = yes.
- **A11. Exit indicator state at entry.** The exit indicator is put on the chart only after entry (V25). Whether an exit signal already present at entry, or on the entry candle, blocks the entry or exits immediately is not addressed.
- **A12. Execution price.** VP trades about 20 minutes before the close (V11). A back-test on closed D1 bars approximates this. The fill model (close vs next open) is not stated.
- **A13. Slot numbering.** Only Baseline = 2, C2 = 4 and Volume = 5 are stated (V27, V20, V12).
- **A14. Garbled names (identifications are (c)).** "shaken / chicken / Chaiken money flow" = Chaikin Money Flow (V20, V27, V28, V29); "hike annachi" = Heikin Ashi (V25); "a rune / Arun up-and-down" = Aroon Up/Down; "RBI" = RVI (V34); "mags indicator" (V27) is probably "my exit indicator". Stonehill: "fer/fiser transform" = Fisher Transform, "shaft trend cycle" = Schaff Trend Cycle, "Copic curve" = Coppock Curve, "case permission stochastic" = Cynthia Case's Permission Stochastic, "Colman filter" = Kalman filter, "seop" = SSL, "trade the market squeeze/ttms" = TTM Squeeze. Other names ("dollar pile", "a cult", "Groucho percentage index", "Layman Trend") are uncertain. They are out of scope and not used for rules.
- **A15. No numeric acceptance criteria (gap).** The corpus gives no win-rate, ROI or drawdown thresholds for accepting an indicator or system. The only goals stated are "far more than 50%", maximising "pips at year end", and beating the gatekeeper. Pairs and history length are not given either, except the profile series' 3-year window (V139). Acceptance criteria must be pre-registered separately.
- **A16. "Chalks" (V139).** These are trades that never hit the stop or any take-profit. Excluding them from the trade count implies that profile tests close trades by some other means (exit signal or end of test). That mechanism is not stated.
- **A17. Daily close time.** V11 says the daily candle "closed at 2:00" Pacific. (c) This corresponds to 17:00 New York, the usual FX daily close. The broker's server time is not discussed.

---

### 11. Coverage (21/21 files read in full)

| # | File | Contribution |
|---|---|---|
| 1 | nnfx/FX_Technical_Analysis/001_7Yj0E5FRwBs_Forex_Indicators_-_By_Far_The_Best_Way_To_Trade.txt | Algorithm = all must agree; trend only; test everything; more than one indicator; 70–75% wrong type; MM > TA. |
| 2 | nnfx/FX_Technical_Analysis/003_086ozcHDZPw_The_ATR_Indicator_..._Use_It_or_Lose_It.txt | ATR 14; timing of the reading; pip-value sizing ∝ 1/ATR; "one indecisive → do nothing"; 4–6 indicators. |
| 3 | nnfx/FX_Technical_Analysis/005_YWNloLjXqeI_Forex_Trend_Indicators_for_the_No_Nonsense_Forex_Algorithm.txt | Three C1 types; C1 quality criteria; tweak settings; consistency across pairs; daily only; indicator funnel. |
| 4 | nnfx/FX_Technical_Analysis/011_PfquDvN0fwI_Forex_Indicator_Basics_With_a_Bonus.txt | Closed-candle rule; ATR from the last closed candle; trade 20 min before close; C1-first scan; manage open trades first. |
| 5 | nnfx/FX_Technical_Analysis/012_NWqbmPC3bD8_Forex_Volume_Indicator_-_Our_Oxygen_Meter.txt | Volume slot purpose; no volume = no trade; low lag; loss/win-elimination test; C1-flip as exit; ADX-25 demo. |
| 6 | nnfx/FX_Technical_Analysis/013_N8Kbk0cwIWg_Volume_Indicators_Part_2_And_A_Free_Tool.txt | Volume = volume or volatility (only one); no momentum; adaptive vs fixed thresholds; no ATR as volume; EVZ tool; 2% risk. |
| 7 | nnfx/FX_Technical_Analysis/015_mr6XFnr95wc_Lower_Time_Frames_For_Entries_Exits_Podcast_Episode_30.txt | No LTF entries or exits; no weekly bias; no fixed R:R; big runs; avoid elections. |
| 8 | nnfx/FX_Technical_Analysis/016_V1VeVrHseTM_Faster_Ways_To_Test_Forex_Indicators_Podcast_Episode_32.txt | Five pre-filter criteria; ROI over signal count; ATR 14 is best. |
| 9 | nnfx/FX_Technical_Analysis/018_IxZ1EdqFJcM_Putting_A_Moving_Average_on_an_Indicator_Makes_Things_Happen.txt | MA-on-indicator hack (SMA 10); continuation signals with zero-cross+MA; MA on volume; exit = two-lines cross. |
| 10 | nnfx/FX_Technical_Analysis/020_JxUtee7krFc_My_Forex_Algorithm_-_Part_5_Revealed.txt | C2 slot: different type, state agreement, testing method (C1+C2 only), zero-line indeterminate. |
| 11 | nnfx/FX_Technical_Analysis/023_Jv6KVnxdCjQ_Top_100_Forex_Indicator_-_The_SSL.txt | Chart-indicator C1 doubling as exit; entry candle after flip; alerts off; closed candle. |
| 12 | nnfx/FX_Technical_Analysis/025_1b3D1gNUyiw_Exit_Indicators_-_Worth_A_Lot_More_Than_You_Think.txt | SL 1.5×ATR, half off at 1×ATR, trailing stop; exit roles; exit types; gatekeeper test; RVI 8. |
| 13 | nnfx/FX_Technical_Analysis/027_x_8wfjTLdoY_Forex_Baseline_-_We_Go_Deep.txt | Baseline entry/exit on close; placement; scan baseline + C1; baseline exempt from one candle rule; ignore slope. |
| 14 | nnfx/FX_Technical_Analysis/028_JssEr6mopDc_Pullbacks_In_Forex_-_Don_t_Get_Crazy_Here.txt | 1×ATR baseline-distance rule; single-case pullback with 1-candle wait; anti pullback-itis. |
| 15 | nnfx/FX_Technical_Analysis/029_0SFM5t_XjwQ_Forex_Algorithm_Trading_-_Continuation_Trades.txt | Exit on C1/exit flip, no re-entry without signal; continuation rules; volume and ATR-distance waived. |
| 16 | nnfx/FX_Technical_Analysis/034_b9HE8q0tobQ_Advanced_Forex_Strategy_-_NNFX_Traders_Only.txt | "Bridge too far" 7-candle rule (two-lines-cross C1, baseline entries); baseline-close exit. |
| 17 | nnfx/FX_Technical_Analysis/139_3C7LJLFeOgI_Changes_for_the_Indicator_Profile_Series_in_2025.txt | Profile test protocol: 1.25×ATR gold/BTC, 3-year window, no 4H, chalks excluded. |
| 18 | stonehill/Exit_Indicators/001_V5Q_QPbEa1U_Exit_Indicators_Part_Four.txt | Exit classification (possible/yes); diverse indicator types give confidence; mostly indicator lists (out of scope). |
| 19 | stonehill/Exit_Indicators/003_xGiqDtEZpKg_Exit_Indicators_A_miniseries_Part_2_of_3.txt | Always keep hard TP and SL besides exit signals; critique of fixed ratios and round levels; default settings shown. |
| 20 | stonehill/Exit_Indicators/004_m9mQe293vUQ_Exit_Indicators_A_miniseries_Part_1_of_3.txt | Exit-indicator taxonomy and grading only; little rule content. |
| 21 | stonehill/Volume_Volatility_Indicators/003_YRLEbYKSYq0_Trading_With_Volume.txt | Three volume rules; volume ≠ direction; test vs SMA 20; threshold examples; backwards-bias warning. |


---

## NNFX Rules — Part B: Risk, Trade Management and Practice

Source set: 19 auto-caption YouTube transcripts by VP (No Nonsense Forex), folders
`Forex_Money_Management/` (7) and `FX_Trading_Strategies_Core_Concepts/` (12).
Extracted 2026-10-30. Scope: everything outside the algorithm's indicator slots.

### Labels

- **(a)**: VP states it (paraphrased; short quotes only where the exact wording matters).
- **(b)**: measurable, meaning it can be coded or tested directly.
- **(a)(b)**: both.
- **(c)**: inference or gap-fill by the extractor, with the reason given.

These are default settings, not rigid laws. Where VP himself says something is flexible, that is recorded as **Flex:**.

### Source key (cited as [Kn] below)

| Key | Video | URL |
|---|---|---|
| M1 | The Money Management Forex Traders MUST Understand | https://www.youtube.com/watch?v=aEORce6dZZI |
| M3 | Forex Risk -- A Structure You Can Follow Right Now | https://www.youtube.com/watch?v=bqWLFNpK6eg |
| M6 | Forex Risk Ratios - Should You Use Them | https://www.youtube.com/watch?v=tw_w-TfhCNM |
| M11 | Adding On To A Winning Trade (Podcast Ep 25) | https://www.youtube.com/watch?v=LWooQSrUE9M |
| M12 | Dollar Cost Averaging and Martingale (Podcast Ep 40) | https://www.youtube.com/watch?v=ITPzMOgts8A |
| M13 | Trailing Stops In Forex | https://www.youtube.com/watch?v=Bsc_1GwKINM |
| M14 | Don't Split Your Risk (Podcast Ep 72) | https://www.youtube.com/watch?v=10ihLdYPu1I |
| C1 | Trading Forex For Beginners - The No Nonsense Forex Way | https://www.youtube.com/watch?v=n9ebKwZpSw4 |
| C2 | Best FX Trading Strategies (big banks) | https://www.youtube.com/watch?v=Lvq0t0eQOG4 |
| C4 | The Best FX Trading Tip I Could Ever Give You | https://www.youtube.com/watch?v=orESKrXu6BM |
| C5 | Forex Reversal Trading vs Trend Trading | https://www.youtube.com/watch?v=EFYGtMThPis |
| C9 | Which Time Frame Gives The Best Results (Podcast Ep 3) | https://www.youtube.com/watch?v=tk2us6L3WF8 |
| C11 | How Many Currency Pairs Should You Trade (Podcast Ep 4) | https://www.youtube.com/watch?v=hETAQcmlljk |
| C12 | How Long To Demo Trade Forex (Podcast Ep 6) | https://www.youtube.com/watch?v=CaNFmubo4Jw |
| C17 | Trading Forex News - You Know Better | https://www.youtube.com/watch?v=x_q4fZcnIoA |
| C19 | Our New NNFX Volume Tool | https://www.youtube.com/watch?v=ZAVPRSa42_w |
| C20 | Trading Dead Markets In Forex | https://www.youtube.com/watch?v=_WUXh3H7U6s |
| C22 | Forex Review - How I Trade | https://www.youtube.com/watch?v=6NfU2OwuyTc |
| C32 | Forex Automation -- So Many Ways | https://www.youtube.com/watch?v=qgJ0yiaE-VM |

**Not in this source set:** several videos that VP cites for rules used here, namely the ATR video, "Scaling Out", "Exit Indicators", "Pullbacks", "Continuation trade" (MACD video), "Volume/volatility (EVZ)" (original), and podcast Ep 23 (timing alternative) and Ep 47 (backtesting). Where a rule depends on one of these, only what these 19 transcripts say about it is recorded.

---

### 1. Money management and position sizing

**1.1 Risk 2% of the account per trade.** (a)(b) [M3]
VP endorses the conventional 2% figure. Quote: "two percent is the most you can lose on a trade make sure your stop loss indicates this". The 2% is a cap set by where the stop sits. Actual losses are usually smaller because the exit indicator closes trades before the stop is hit.

**1.2 Risk is measured on current account value, including open trades.** (a)(b) [M3]
In the worked example he reads the live account figure: "yes even if i have a trade open this is the number i want right here and it's moving". That figure was $52,36x. He ignores the cents and takes 2% of it, about $1,005.

**1.3 Position sizing formula.** (a)(b) [M3]
1. Risk$ = 2% × account value.
2. Stop distance = 1.5 × ATR(14) in pips.
3. $/pip = Risk$ / stop distance in pips.

Worked example: EURUSD daily ATR = 86, so the stop is 1.5 × 86 = 129 pips, and $1,005 / 129 ≈ $7.80 per pip.
- The verbal statement says "divide it by the atr", but the calculation divides by the stop distance (1.5 × ATR). See Ambiguity A1.

**1.4 ATR definition used.** (a)(b) [M3]
ATR is the average high-to-low range of the last 14 candles (default setting 14), read on the daily chart.

**1.5 Account-currency conversion.** (a) [M3]
He lets the broker show the pip value and adjusts units until the $/pip is right. He gives no formula for non-USD quote currencies or non-USD accounts. (c) For code: units = ($/pip) / (pip value per unit in account currency). This is a standard conversion and not from the source. See Gap G1.

**1.6 Accounts split across brokers are treated as one account.** (a)(b) [M14]
If capital is split across brokers (for broker safety), compute risk on the sum of all accounts. Example: $20k split into $10k + $10k gives 2% of $20k = $400 on a trade in the $10k sub-account. On the sub-account alone that looks like 4%, which is intended. VP says to do the same thing on demo.

**1.7 Leverage.** (a)(b) [M14]
20:1 is "a set it and forget it" setting, and with NNFX risk margin is rarely an issue. Raise it to 30:1 or 40:1 only when accounts are split across brokers (sub-account margin can run thin). "it could be five hundred to one it wouldn't matter we would trade exactly the same".

**1.8 Same-currency exposure: don't trade the same currency more than once at 2%.** (a)(b) [M3]
His example: EURUSD short, AUDUSD short and USDJPY long, each at 2%, add up to 6% on USD. Allowed alternatives:
- (i) Pick one, the signal seen first: "whichever one you saw first just go with it".
- (ii) Split 1% + 1% across the two same-currency signals, e.g. EURJPY and EURAUD.
- (iii) "With caution": go 1% on the first signal when a second same-currency pair is "one candle away" from signalling.

VP warns against overusing (iii): "i don't want you going one percent on every trade" just because another signal might come, since that is "a license to go timid".
- Related [C22]: collect all of the day's signals in writing **before** entering any of them, so overlapping-currency signals can be allocated together. His example is long EURUSD and long EURNZD: full risk on both would be "overextended in one currency".

**1.9 Total open risk / number of trades.** (a)(b) [M3]
"you can have as many open as you want all at two percent risk that's fine", provided rule 1.8 is respected. No portfolio-level cap is stated. [C11] (a): "I'm usually never in more than three or four trades at one time". That is a description of what he observes, not a rule. See Gap G2.

**1.10 Risk is fixed and does not change with mood or results.** (a) [M3]
The losing "99%" vary risk with the last win or loss or with upcoming news, and "chase" losses with bigger risk. Be consistent: "take the numbers i have given you and do not deviate from them".
- **Flex:** "after you've done this and you've gotten experience with it you can adjust it how you want".

**1.11 Too little risk is also a failure.** (a) [M3]
Risk set too low makes even good trading "not worth it". His example is 4%/yr, which you can earn by parking money. No lower bound is given.

**1.12 Market volume (volatility index) influences risk per trade.** (a) [C22]
He checks the EVZ first each day. It "is going to influence the way I trade in terms of how much risk I put on every single trade... even if it's not [there] I will still often trade it but it's just a matter of how much risk". No reduced-risk number is given. See Ambiguity A6.

**1.13 Drawdown asymmetry is the reason for the cap.** (a)(b) [M3]
After a 20% drawdown (50k to 40k) you need +25% to recover. After a 50% drawdown (to 25k) you need +100%: "trading suicide". [M12] (a): never get to the point where you would "have to morph into Warren Buffett" to break even.

**1.14 Money management ranks first.** (a) [M1]
Ranking: (1) money management, (2) psychology, (3) trade entries. Illustration: a system with entries twice as good but money management half as good loses badly. [C1] repeats the ranking and allows money management and psychology to swap places.

---

### 2. Stops, targets, breakeven, trailing

**2.1 Initial stop = 1.5 × ATR from entry.** (a)(b) [M3]
"one and a half times the atr for a currency pair is where your stop loss should be". Example: ATR 80 gives a 120-pip stop. Ignore support/resistance and Fibonacci for stop placement: "ignore everything else". For a long the stop goes below entry, for a short above.

**2.2 Stops adapt to volatility; fixed-pip stops are wrong.** (a) [C4]
Example: EURGBP moves about 63 pips/day and GBPNZD about 199. The same 20- or 30-pip stop on both, or across timeframes, "makes no sense".

**2.3 Never widen a stop; don't pre-empt it either.** (a)(b) [C4]
- Never move the stop further away when a trade goes against you.
- Don't close at −20 out of −30 just because you're scared: "let the trade do what it does let your system do what it does". Exits need a concrete reason (an indicator, or a news event).
- Exceptions are given by rule elsewhere: the exit indicator (§3.5) and news (§4.4).

**2.4 No fixed risk:reward ratios; never cap the upside.** (a) [M6], [C4]
"do not use ratios in your trading". The reasons:
- (i) People pick the target from S/R first and then fit the stop to it.
- (ii) Ratios prevent scaling out.
- (iii) Ratios cap the upside and miss the 500–1500-pip trends that "happen more than once every year".
- Also: "don't take profit at major support and resistance levels".

**2.5 First take-profit (TP1) = 1 × ATR, closing half the position.** (a)(b) [C17], [M13]
- [C17]: "we use the ATR indicator to determine where we are going to take profit… for us we take it at the ATR".
- [M13]: with ATR = 100, "once i got a hundred pips up i took half off". In his WTI example the broker "automatically took half of my position off" at +187 pips (ATR 187).
- He runs the two halves as two separate trades (Oanda): "I make two separate trades because on this platform you kind of have to". See also [C22]: on entry, write down "where your stop-loss an initial take profit is going to go".
- (c) The primary "Scaling Out" video is not in this set. TP1 = 1×ATR is consistent across 2 sources here.
- The [M6] example of TP 80 pips and SL −40/−60 is explicitly "not me giving you a framework".

**2.6 Move the runner's stop to breakeven after TP1.** (a)(b) [M6], [C22], [M13]
After the first half is banked, move the stop on the remaining half to the entry price. "it's not a matter of if I'm going to win now it's just a matter of how much".

**2.7 Purpose of scale-out + breakeven.** (a) [M6], [C4]
Many small wins (TP1 half plus breakeven) are meant to cancel the losses, taking the account to about zero. The few big trends on the runner are the actual profit. [M6]: "you can probably count on two or three of those really good runs per currency pair" per year.

**2.8 Trailing stop activation: price has *closed* at least 2 × ATR beyond entry.** (a)(b) [M13]
"price has to have closed two times the ATR from where I entered". VP: "I don't have a super great reason for why this is but these are just the rules I follow". Until then, the runner stays at breakeven.

**2.9 Trailing stop distance = 1.5 × ATR behind price.** (a)(b) [M13]
"one point five times the ATR behind where price currently is". It is the same multiple as the initial stop. In his example, short WTI with ATR 187: trail = 280 pips, placed at close + 280.

**2.10 ATR value for the trade is the entry-candle ATR, frozen for the life of the trade.** (a)(b) [M13]
"I use whatever the ATR was when I entered the trade and just use that number throughout". He says it's "not the most accurate" but he prefers the consistency. This applies to TP1, the trailing activation and the trailing distance.

**2.11 Trailing stop update rule (VP calls this the most important part).** (a)(b) [M13]
- Move the trail only when a daily candle **closes** beyond the best close so far: a new closing high for a long, a new closing low for a short.
- When it moves, reset it to 1.5 × ATR(entry) behind that close.
- The trail only ever tightens; it never moves back.
- Intraday moves are ignored.
- Updates are done manually once a day. He avoids broker trailing-stop features: "I kind of relinquish control over my stop-loss that way".
- **Flex:** "you can kind of plug in your own numbers if they make more sense to you… the rule on when to move it I think is the most important".

**2.12 Trailing stops should be deep.** (a) [M13]
A trailing stop is like a regular stop, "only there in case price just goes crazy the other way". It must leave room for retracements. Ideally the exit indicator closes the trade "nine out of ten times".

**2.13 Any trailing structure beats none.** (a) [M12], [C22], [M13]
"you can put your own structure for a trailing stop in right this minute and it will still serve you a lot better than if you didn't have one".

**2.14 Illustrative early plan in [C4] (not his numbers).** (a) [C4]
GBPUSD M15: SL −30; at +50 close half and move SL to breakeven; at +100 start trailing with the stop at +50. VP: "leave the numbers blank because I don't even trade the 15-minute chart". It shows the if-then structure only. See Conflict K2.

**2.15 Write the trade-management plan down as if-then steps and follow it every time.** (a) [C4]
"something actually written down pen and paper". Deviating from it means trading by feel.

---

### 3. Trade management: adding, scaling, DCA/martingale, early close

**3.1 No adding to winners (no scaling in).** (a)(b) [M11]
Short answer "no". The system entry is the optimal point, and adding 100–150 pips later is mathematically worse and involves "a little element of greed". VP acknowledges that "some very very smart traders… will disagree with me".

**3.2 No FOMO entries.** (a)(b) [C4], [M11]
Don't enter after price has already run away from the signal (his example is 20 pips past the entry). The stop and target are then mis-placed and "the math is against you". "never enter a fear of missing out trade just let it go".

**3.3 A second signal in the same direction is not a reason to add.** (a)(b) [M11]
For your confirmation indicator to signal the same direction again, it must first have flipped the other way. An opposite confirmation signal while in a trade means **exit** ("definitely time for you to get out"). For a two-line cross indicator, an opposite cross at any time means exit.

**3.4 Use continuation trades instead of adding.** (a) [M11], [C22]
To keep taking part in a long trend after an exit, use the continuation-trade rule (defined in the MACD video, which is not in this set). [C22]: a continuation trade needs the baseline not signalling, the confirmation signalling, and the rest of the algorithm aligned "but just not the volume indicator". (c) Details are out of scope for Part B; see Part A.

**3.5 Exit indicator: obey it immediately.** (a)(b) [C22], [M3]
"if it is telling you to exit you don't ask questions you immediately go to that trade and you exit out". Its purpose is to get out before the stop is hit while letting the trade breathe. [M3]: "I rarely have my stop loss hit". A confirmation indicator can serve as the exit but "it's just typically not going to be your best option" [M11].

**3.6 Dollar-cost averaging: never.** (a)(b) [M12]
"holy no… terrible stupid reckless idea". Reason: currencies (pairs) have no intrinsic value and can trend "thousands and thousands of pips", so doubling down can wipe out an account on one pair. VP doesn't recommend it on metals either.

**3.7 Martingale: never.** (a)(b) [M12]
He describes losing his whole stake doubling up at craps. "the math in the end is so strongly against you". DCA and martingale are the only exceptions to his "any structure is better than no structure" rule.

**3.8 Exiting by feel is forbidden.** (a) [C4]
Don't exit because the move "looks overbought/oversold" or has "run its course", or to protect gains, without a concrete reason. "overbought and oversold does not exist in spot Forex" [C5].

**3.9 Rule-based early closes.** (a) [C17], [C20]
- News (§4.4).
- Dead markets: close the full position at TP1 (§5.7).

**3.10 Check the broker executed stops and targets.** (a)(b) [C22]
At the start of each session, check that any SL or TP that should have been hit actually filled. If not, find out why before doing anything else; it could be a broker fault.

---

### 4. News rules

**4.1 Never trade the news (trading the release itself).** (a) [C2], [C17]
"the best strategy by far is to stop trading the news and never do it again". Banks move price violently around releases, and spreads widen.

**4.2 Only scheduled economic releases matter. Long-horizon investor news (Bloomberg/CNBC) is ignored.** (a) [C17]

**4.3 Check the calendar daily before opening charts.** (a)(b) [C17], [C22]
His main calendar is Forex Factory, with a backup because Forex Factory under-weights NZD GDT.

**4.4 Rules around a major event on a currency within the next 24 hours.** (a)(b) [C17], [C22]

| Situation | Action |
|---|---|
| Not in a trade | Do **not** enter any pair containing that currency. "can I get at least one candle's worth of trade in before this news event comes up". [C22]: write the currency down and skip all of its pairs. |
| In a trade, losing (not yet stopped out) | **Close it** and take the loss. Avoid the risk of a spike gapping past the stop. |
| In a trade, winning but TP1 (1×ATR) not yet reached | **Close the whole trade** and take the win. |
| TP1 already taken, but current profit is now below 1×ATR | **Close the remaining position.** Even a breakeven stop is not trusted, because spreads widen. |
| Winning big: already scaled out, running well beyond 1×ATR (his example: ATR 80, trade at +200) | **Carry on** as normal with breakeven or trailing stop in place. |

VP: "I've tried every combination of this and this is what is best worked for me."

**4.5 The "major" event list for daily-chart traders, as of 17 Jan 2019.** (a)(b) [C17]
Basis: his historical spike study via newsimpact.com, 2018 data. VP notes that impact changes slowly over time.

| Currency | Events |
|---|---|
| USD | Non-Farm Payrolls ("the biggest… every month"); interest rates / anything FOMC; Fed Chair speaking; CPI |
| EUR | Interest rates; ECB President speaking |
| GBP | Interest rates (MPC vote); GDP |
| CAD | Interest rates; employment (often same time as NFP); retail sales; CPI |
| AUD | Interest rates; employment. Chinese news no longer a concern. |
| NZD | Employment; GDP; GDT (Global Dairy Trade); interest rate |
| JPY | Interest rates only |
| CHF | "LIBOR rate" only |

- (a) [C17]: on NFP day, "another reason to sit completely out the market".
- (c) The list is dated (2019) and names people (Draghi, Powell) who no longer hold office. Treat it as a template to re-derive from current impact data, not a fixed list. Gap G5.

**4.6 Elections and referendums: do not trade them.** (a) [C17]
Examples: US presidential election, Brexit vote.

**4.7 Long-running political sagas: stop trading that currency for months.** (a) [C17]
Examples: Brexit (GBP), Grexit (EUR). Wait until "the dust had settled".

**4.8 Unlisted events can still stop you out; accept it.** (a) [C17]
Have a plan for the big ones and play the odds.

**4.9 Daily-chart traders can often absorb news that goes against them.** (a) [C9], [C17]
If the technicals are right, price often recovers within a candle or so. This is a reason to trade the daily chart, not a reason to hold through major events (§4.4 still applies).

---

### 5. Timeframe, timing and market conditions

**5.1 Trade the daily chart.** (a)(b) [C9], [C11], [C22]
"the best timeframe… is the daily chart and again it is not even close". His four reasons:
- Every tool works more consistently on it.
- It takes 10–15 minutes a day.
- Fewer news events matter.
- There is less bank targeting.

The weekly chart is not used [C9] (reason given in a blog post that is not in this set).
- **Flex:** intraday traders can run a parallel daily-chart profile. "everything I tell you is going to work on every timeframe it is just going to work on the daily chart better" [C9]. [C22]: "this system works on all of them".

**5.2 Act once a day, about 20 minutes before the daily close.** (a)(b) [C22], [C9]
He acts at 1:40 pm Pacific, "20 minutes before the daily candle is about to close" (close = 2 pm Pacific). [C9]: "usually right before 2 p.m.". (c) 2 pm Pacific = 17:00 New York, the usual FX daily rollover. That conversion is the extractor's. An alternative time for people who can't be present at 1:40 is given in podcast Ep 23, which is not in this set.

**5.3 Daily routine, in order.** (a)(b) [C22]
1. At 1:40 pm PT, check the volume index (EVZ / DBC VIX).
2. Check the news calendar for the next 24 hours and list currencies to avoid.
3. Review the whiteboard: open trades, near-signals, pullback candidates.
4. **Maintenance first:**
   - Check that SL/TP fills are correct.
   - Check the exit indicator on each open trade and exit if it says so.
   - Move stops: breakeven after TP1; apply or update the trailing stop.
5. Scan all pairs for new signals and write each valid signal down without entering yet:
   - Baseline cross/close, then the ATR pullback check, then the rest of the indicators. If any says no, move on.
   - Otherwise, confirmation, then the continuation rules.
6. **Entry:** compute risk for the whole list (allocating same-currency signals per §1.8). Write down the SL and TP1 for each trade and enter with **market orders, not limit orders**. Double-check, then don't look until the same time tomorrow.

**5.4 Check once a day; don't watch open trades intraday.** (a) [C22], [M13]
"you're not going to be looking at this thing until this time tomorrow". [M13]: he looked at a chart off-hours "and it bit me".

**5.5 Dead-market detection: the volume index.** (a)(b) [C20], [C19]
- Old tool, Euro FX VIX (EVZ, via barchart):
  - Baseline 8. "my baseline used to be 8 nowadays I might just have to lower this".
  - 6 is the "floor".
  - It hit 5 in July 2014, the "deadest market I have ever seen".
- Replacement since the EVZ data stopped (early 2025): **DBC VIX USD volatility index** (CNBC).
  - Suggested levels: above **7** on the previous trading day, trade normally. Below 7, switch to the dead-markets playbook. Near **5**, "maybe just take a break".
- Read the **previous completed day's close** value; ignore intraday swings.
- **Flex/caveat:** VP has *not* tested the DBC levels himself: "use it at your own risk… set levels, but be flexible". He also says the system can be traded without a volume index.

**5.6 Dead market, option 1 (VP's "number one suggestion"): don't trade.** (a) [C20]
Use the time to test or re-evaluate the system and indicators. A good volume indicator "should be keeping you out of just about every currency pair" in a dead market. If it isn't, it needs replacing.

**5.7 Dead market, option 2: if trading, adjust three things.** (a)(b) [C20]
- (i) Avoid USD pairs entirely; trade crosses only.
- (ii) At TP1, close the **whole** position, not half. VP calls this a 1:1-type exit, "terrible money management" in normal conditions, but correct in dead markets.
- (iii) Expect to miss the first breakout move out of a dead range. This is normal, and that first move is often a false breakout anyway.

**5.8 What dead markets look like on other assets.** (a) [C20]
Slow, steady grind-up in the S&P 500 goes with dead FX. Sharp equity moves bring volume into FX. A sudden drop in a pair's ATR is another sign.

---

### 6. Pairs and correlation

**6.1 Trade 27 pairs: all 28 combinations of the 8 majors minus EURCHF.** (a)(b) [C11]
The 8 majors are EUR, GBP, USD, AUD, NZD, CAD, CHF and JPY. EURCHF is excluded because it is too tied together and doesn't trend; "it's more fundamentals driven". No exotics (MXN, TRY, ZAR, …). [M6]: "I trade 27 currency pairs".
- Reason: more opportunities ("nine times the opportunity" vs 3 pairs) and less dead time on the daily chart.

**6.2 Pairs have no unique character on the daily chart.** (a) [C11]
"currency pairs do not have their own unique movement". Don't specialise in one pair, and don't avoid illiquid crosses.

**6.3 Trade USD pairs less often than crosses.** (a) [C2], [C11], [M6]
USD pairs are the most crowded and most manipulated. "just stop trading them… or do what I do and just trade them a lot less often". EURUSD is "the last pair you should be in" if you trade only one [C11]. [M6]: "you should be trading pairs like this [GBPCHF] far more often than… dollar pairs". (c) No quantitative rule is given for "less often". Gap G3.

**6.4 Drop a currency temporarily when its correlation or politics makes it untradeable.** (a) [C17]
CHF while it was tied to EUR (he traded only 7 currencies for a while). GBP during Brexit.

**6.5 Correlation handling is by shared currency (§1.8), not by statistical correlation.** (a) [M3], [C22]
(c) No correlation coefficient or matrix is ever mentioned. Exposure is managed by counting currencies, and that is the codable form.

---

### 7. Demo / forward testing and going live

**7.1 Go live only after at least 6 months of active demo trading with at least +6% return over that window.** (a)(b) [C12]
Example: $50k demo needs to reach $53k or more. One big over-leveraged early trade "doesn't count"; you must be "actively trading for six months". Expect it to take longer: "6 to 12 to even 18 months".
- The 6% bar comes from the US stock market's ~12%/yr. Beating it annualises to that benchmark: (c) 6% in 6 months ≈ 12% a year.

**7.2 Start real money very small.** (a) [C12]
Psychology with real money is "a completely different game".

**7.3 Demo exactly as if it were real money, with the same risk profile.** (a) [C12], [M14]
Reset and retry freely while building. [M14]: run split-broker accounts on demo too.

**7.4 Don't add other markets (metals, indices, oil) until the FX system is at least in forward testing.** (a) [M14]
"inch wide mile deep".

**7.5 Backtest and forward-test results differ; don't extrapolate from backtests.** (a) [C32]

**7.6 Third-party EAs: demo first, "in my opinion for at least two months".** (a)(b) [C32]
Check that the EA is hooked up correctly, allocates capital properly, and matches the claimed results.

**7.7 Results benchmarks VP mentions.** (a) [M14], [M3]
- 10%/yr from FX alone is "really good".
- 4%/yr from risk set too low is "doing it wrong".
- (c) These are context for evaluation, not acceptance criteria.

**7.8 Dead markets are prime system-testing time.** (a) [C20]
Measure how much the system loses in them and adjust it to lose as little as possible.

---

### 8. Overall approach

**8.1 Trend trading only; reversal trading is rejected.** (a) [C5], [M6]
"trend trading and it's not even close". "Overbought/oversold does not exist in spot Forex" [C5]. Tools that pick reversals (RSI, stochastics) are rejected.

**8.2 Rationale: big banks trade against the retail majority.** (a) [C2], [C5]
Stay "under the radar":
- Avoid popular tools ("Dirty Dozen": trend lines and RSI first, S/R lines).
- Avoid popular pairs (USD).
- Avoid news trading.
(c) This is VP's causal story; it is not testable from these transcripts.

**8.3 "Best tip": eliminate what loses before adding what wins.** (a) [C4]
Removing a loss equals adding a win. Three things to cut:
- (1) Tools that don't work.
- (2) Trading by feel (FOMO, exiting on gut).
- (3) Having no written, consistent trade-management plan.
[C17], [C20]: "we win by not losing".

**8.4 Indicator-based mechanical system on the daily chart, 10–15 minutes a day, emotion removed.** (a) [C1], [C22]
VP gives the framework and the trader fills the slots. "you must have a structure and follow it… to the letter".

**8.5 Automation: no definitive answer; VP barely uses any.** (a) [C32]
Guidelines:
- Use technology to do the job **better**, not just as a shortcut.
- Test manual and automated side by side.
- Automation should supplement your trading, not replace it.
- Keep improving your own system.
- Automating backtesting of indicators and systems: "if I had to do it all over again… I would have really given this a try".
- Automating post-entry trade management (money management) is "really not a bad way to go" for traders still struggling with psychology after years. VP mentions a third-party product built for NNFX parameters.
- Note: his prop firm does not allow third-party EAs (self-coded ones are allowed).

**8.6 Patience; going slow is the method.** (a) [C1], [C12]

---

### 9. Numeric parameter table

| Parameter | Value | Label | Source URL |
|---|---|---|---|
| Risk per trade (max) | 2% of total account value (incl. open P&L) | (a)(b) | https://www.youtube.com/watch?v=bqWLFNpK6eg |
| ATR period | 14 (daily) | (a)(b) | https://www.youtube.com/watch?v=bqWLFNpK6eg |
| Initial stop | 1.5 × ATR from entry | (a)(b) | https://www.youtube.com/watch?v=bqWLFNpK6eg |
| Position size | $/pip = Risk$ / (1.5×ATR pips) | (a)(b) | https://www.youtube.com/watch?v=bqWLFNpK6eg |
| Same-currency exposure | Max one 2% trade per currency; or 1% + 1% | (a)(b) | https://www.youtube.com/watch?v=bqWLFNpK6eg |
| Number of open trades | No cap stated; he typically has 3–4 | (a) | https://www.youtube.com/watch?v=bqWLFNpK6eg ; https://www.youtube.com/watch?v=hETAQcmlljk |
| TP1 | 1 × ATR, close 50% | (a)(b) | https://www.youtube.com/watch?v=x_q4fZcnIoA ; https://www.youtube.com/watch?v=Bsc_1GwKINM |
| Runner stop after TP1 | Breakeven (entry price) | (a)(b) | https://www.youtube.com/watch?v=tw_w-TfhCNM |
| Trailing activation | Close ≥ 2 × ATR beyond entry | (a)(b) | https://www.youtube.com/watch?v=Bsc_1GwKINM |
| Trailing distance | 1.5 × ATR behind the new extreme close | (a)(b) | https://www.youtube.com/watch?v=Bsc_1GwKINM |
| ATR used in trade | ATR at entry candle, fixed for trade life | (a)(b) | https://www.youtube.com/watch?v=Bsc_1GwKINM |
| Trailing update trigger | Only on a new closing high (long) / low (short) | (a)(b) | https://www.youtube.com/watch?v=Bsc_1GwKINM |
| Exit indicator share of exits (aspiration) | ~9 out of 10 | (a) | https://www.youtube.com/watch?v=Bsc_1GwKINM |
| Big runs per pair per year | 2–3 | (a) | https://www.youtube.com/watch?v=tw_w-TfhCNM |
| FOMO example | 20 pips past intended entry = don't enter | (a) | https://www.youtube.com/watch?v=orESKrXu6BM |
| News entry blackout | Major event on currency within 24 h (≈1 daily candle) | (a)(b) | https://www.youtube.com/watch?v=x_q4fZcnIoA |
| News: close-if-below threshold | Open profit < 1 × ATR (or losing) | (a)(b) | https://www.youtube.com/watch?v=x_q4fZcnIoA |
| Timeframe | Daily (D1) | (a)(b) | https://www.youtube.com/watch?v=tk2us6L3WF8 |
| Decision time | 1:40 pm US Pacific (20 min before 2 pm PT close) | (a)(b) | https://www.youtube.com/watch?v=6NfU2OwuyTc |
| Daily time spent | 10–15 min | (a) | https://www.youtube.com/watch?v=tk2us6L3WF8 |
| Pairs traded | 27 (28 major combos minus EURCHF) | (a)(b) | https://www.youtube.com/watch?v=hETAQcmlljk |
| Major currencies | 8 | (a)(b) | https://www.youtube.com/watch?v=hETAQcmlljk |
| EVZ (old) baseline | 8 (may need lowering); floor 6; extreme low 5 (Jul 2014) | (a)(b) | https://www.youtube.com/watch?v=_WUXh3H7U6s |
| DBC VIX threshold | < 7 prev-day close → dead-market playbook; ≈5 → maybe stop (untested by VP) | (a)(b) | https://www.youtube.com/watch?v=ZAVPRSa42_w |
| Dead-market TP | Close 100% at TP1 | (a)(b) | https://www.youtube.com/watch?v=_WUXh3H7U6s |
| Leverage | 20:1 default; 30–40:1 if accounts split across brokers | (a)(b) | https://www.youtube.com/watch?v=10ihLdYPu1I |
| Split-account example | $20k total → 2% = $400 even in a $10k sub-account | (a)(b) | https://www.youtube.com/watch?v=10ihLdYPu1I |
| Demo duration | ≥ 6 months active (often 6–18) | (a)(b) | https://www.youtube.com/watch?v=CaNFmubo4Jw |
| Demo return hurdle | ≥ +6% over the 6-month window | (a)(b) | https://www.youtube.com/watch?v=CaNFmubo4Jw |
| Benchmark | US stocks ≈ 12%/yr | (a) | https://www.youtube.com/watch?v=CaNFmubo4Jw |
| EA demo period | ≥ 2 months | (a)(b) | https://www.youtube.com/watch?v=qgJ0yiaE-VM |
| "Good" annual FX return | 10% | (a) | https://www.youtube.com/watch?v=10ihLdYPu1I |
| Drawdown recovery examples | −20% needs +25%; −50% needs +100% | (a)(b) | https://www.youtube.com/watch?v=bqWLFNpK6eg |
| Illustrative-only plan (not VP's numbers) | SL −30, half off +50, BE, trail at +100 to +50 (M15) | (a), illustrative | https://www.youtube.com/watch?v=orESKrXu6BM |
| Illustrative-only ratio example | TP 80, SL −40/−60 | (a), illustrative | https://www.youtube.com/watch?v=tw_w-TfhCNM |

---

### 10. Conflicts

**K1. Number of pairs traded.**
- 27 pairs (excluding EURCHF): [C11] https://www.youtube.com/watch?v=hETAQcmlljk and [M6] https://www.youtube.com/watch?v=tw_w-TfhCNM.
- "if you're trading 28 different currency pairs like we do here": [M11] https://www.youtube.com/watch?v=LWooQSrUE9M.
- "I was only able to trade seven currencies" during the CHF peg: [C17] https://www.youtube.com/watch?v=x_q4fZcnIoA.

Probably a time-dependent universe. (c) Default to 27 and make the universe configurable.

**K2. Trailing stop rules.**
- [C4] https://www.youtube.com/watch?v=orESKrXu6BM: start trailing at +100 pips with the stop at +50 (M15, explicitly illustrative, "leave the numbers blank").
- [M13] https://www.youtube.com/watch?v=Bsc_1GwKINM: activate on a close ≥ 2×ATR; trail 1.5×ATR; move only on a new extreme close.
- [C17] (2019) says his trailing method was "a little too complex for me to explain to a mass audience". [C22] says the trailing video was not out yet and "I don't think it's gonna be a whole lot different from what you guys have going on". [M13] is the later, definitive version.

Use M13.

**K3. "Never cap your upside / no 1:1" vs dead-market full exit at TP1.**
- [M6], [C4]: never cap the upside.
- [C20] https://www.youtube.com/watch?v=_WUXh3H7U6s: close everything at TP1 in dead markets.

VP flags this himself as a deliberate situational exception. It is not a contradiction, but the code needs a regime switch.

**K4. "Don't exit early; let the stop do its job" vs news-driven early exits.**
- [C4]: don't exit early.
- [C17]: close losing trades, and winning trades below 1×ATR, ahead of major news.

[C4] itself allows a news event as a concrete reason ("I can almost get on board with"). Resolved as a rule-based exception.

**K5. Timeframe.**
- Daily exclusively, weekly not used: [C9] https://www.youtube.com/watch?v=tk2us6L3WF8.
- 2025: "I have been pretty much forced to trade the weekly chart now" because of travel, and volume matters less on the weekly: [C19] https://www.youtube.com/watch?v=ZAVPRSa42_w.

This is a personal circumstance, not a method change. Daily remains the stated default.

**K6. Volume index reference levels drift.**
- EVZ baseline 8, "might have to lower" [C20].
- DBC VIX threshold 7 [C19], on a "slightly different scale".

Different instruments and eras. Neither is VP-validated for DBC.

**K7. Volume and risk.**
- [C22]: low volume means "I will still often trade it", but with adjusted risk.
- [C20]: the number-one suggestion is not to trade at all; otherwise crosses only with a full exit at TP1. No risk reduction is mentioned.

The two playbooks differ in what they adjust: risk size vs. exit and pair selection.

---

### 11. Ambiguities / gaps

**A1. Divisor in the sizing formula.** [M3] says "take that risk and divide it by the atr", but the worked numbers divide by 129 = 1.5 × ATR(86). (c) Code it as Risk$ / stop distance in pips. The example is unambiguous; the sentence is a slip or a caption artefact.

**A2. TP1 measured from entry: the trigger is touch vs. close.**
- [M13]: the broker "automatically took half… off" at +187, which implies a resting limit order (intraday touch).
- Trailing activation is explicitly on a *close*.
- (c) TP1 = limit order at entry ± 1×ATR, filled intraday; trailing logic on daily closes only.

**A3. Stop and target reference price.** "1.5 the atr away from where the price is right now" [M3]. Entry is a market order placed just before the daily close [C22]. (c) In backtests, use the signal-candle close (or the next open) as entry and as the reference for SL and TP1. Gap-at-open handling is unspecified.

**A4. Risk split between the two halves.** He runs two separate trades [M13] with total risk 2% [M3]. (c) Each half = 1% risk with the same 1.5×ATR stop. Not stated explicitly.

**A5. Account value: balance vs equity.** [M3] uses the live, moving figure with a trade open, i.e. equity/NAV. [M14] says "the sum of those two accounts". (c) Use total equity across accounts at decision time.

**A6. Reduced risk in low volume** [C22]: no amount or rule is given. Gap.

**A7. News, "winning big" threshold** [C17]: defined by example only (scaled out, ATR 80, at +200). (c) Code it as "TP1 taken AND open profit ≥ 1×ATR → hold". This mirrors the stated close-if-below-1×ATR rule. Whether a still-at-breakeven runner at, say, +1.2×ATR is "big" is unclear.

**A8. News look-ahead window anchor.** "within 24 hours" vs "at least one candle's worth of trade in before" [C17]. (c) For a check at 1:40 pm PT, the window is the next 24 h, i.e. through the next daily close.

**A9. News event list is dated (Jan 2019)** and person-specific (Draghi, Powell). The "LIBOR rate" for CHF is likely a caption or terminology artefact for the SNB policy rate (c). Gap G5.

**A10. Same-currency rule scope.**
- [M3] covers same-direction exposure to one currency (e.g. long EUR twice).
- It does not say whether opposite-direction exposure (long EURJPY + short EURUSD) counts.
- It does not say whether three pairs sharing different currencies are fine.
- (c) Simplest compliant coding: net risk per currency, by direction, ≤ 2%.

**A11. Dead-market regime switch inputs.** The data source (CNBC DBC VIX) has no stated API, and VP does not trade it himself. (c) A coded version needs a proxy (for example a cross-pair ATR percentile). That is an inference, not from the source.

**A12. "Trade USD pairs less often"** [C2], [C11]: no rule. Gap.

**A13. Pullback rule** referenced in [C22] ("measure the distance from my baseline to where price has closed", using ATR) without its threshold. That video is not in this set. Out of scope (Part A).

**G1. Account currency:** no explicit conversion method (§1.5).

**G2. Portfolio risk cap:** none stated beyond the same-currency rule (§1.9).

**G3. Pair weighting:** nothing quantitative.

**G4. Weekend gaps / swap:** not addressed in these sources, beyond [C2] noting that weekend gaps can erase profits.

**G5. News list:** must be refreshed from current data. VP's method was historical spike size per event.

**G6. Exit-indicator, baseline and continuation definitions:** out of scope; referenced only.

---

### 12. Coverage (19 / 19 files read in full)

**Forex_Money_Management/**
1. `001_aEORce6dZZI` The Money Management Forex Traders MUST Understand: ranking MM > psychology > entries; MM-dominance illustration. Motivational, no numbers.
2. `003_bqWLFNpK6eg` Forex Risk -- A Structure You Can Follow Right Now: **core sizing**: 2%, 1.5×ATR stop, $/pip formula, worked EURUSD example, same-currency rule and alternatives, drawdown math, exit indicator role.
3. `006_tw_w-TfhCNM` Forex Risk Ratios - Should You Use Them: no R:R ratios, never cap upside, scale out + breakeven logic, small wins offset losses, 27 pairs, favour crosses.
4. `011_LWooQSrUE9M` Adding On To A Winning Trade (Ep 25): no scaling in, no FOMO, opposite confirmation signal = exit, continuation trades as the alternative.
5. `012_ITPzMOgts8A` Dollar Cost Averaging and Martingale (Ep 40): never DCA, never martingale, reasons given; any trailing structure is better than none.
6. `013_Bsc_1GwKINM` Trailing Stops In Forex: **trailing rules**: 2×ATR close activation, 1.5×ATR distance, entry ATR frozen, move only on new extreme close; TP1 at 1×ATR evidence; manual daily updates.
7. `014_10ihLdYPu1I` Don't Split Your Risk (Ep 72): risk on total capital across brokers; leverage 20:1 or 30–40:1; forward-test FX before other markets; 10%/yr benchmark.

**FX_Trading_Strategies_Core_Concepts/**
8. `001_n9ebKwZpSw4` Trading Forex For Beginners: curriculum order, MM/psychology priority, 10–15 min/day, system ethos. Little rule content.
9. `002_Lvq0t0eQOG4` Best FX Trading Strategies (big banks): rationale. Avoid popular tools and USD pairs, don't trade news, avoid exotics.
10. `004_orESKrXu6BM` The Best FX Trading Tip: eliminate losers first; no FOMO; no exiting by feel; ATR-adaptive stops; never widen a stop; never cap upside; written if-then plan (illustrative numbers).
11. `005_EFYGtMThPis` Reversal vs Trend Trading: trend only; no overbought/oversold in FX.
12. `009_tk2us6L3WF8` Which Time Frame (Ep 3): daily chart and four reasons; ~2 pm PT check; news absorbed better; weekly not used; intraday flex.
13. `011_hETAQcmlljk` How Many Currency Pairs (Ep 4): 27 pairs = 8 majors minus EURCHF; no exotics; pairs have no unique character; 3–4 trades open typically.
14. `012_CaNFmubo4Jw` How Long To Demo Trade (Ep 6): 6 months active demo with ≥6% return, 12%/yr benchmark, start live small.
15. `017_x_q4fZcnIoA` Trading Forex News: **news rules**: 24 h entry blackout, in-trade actions by P&L state, per-currency event list, elections and long sagas; TP at 1×ATR.
16. `019_ZAVPRSa42_w` Our New NNFX Volume Tool: DBC VIX replaces EVZ; threshold 7 / ~5 (untested); use previous-day close; VP now on weekly chart.
17. `020__WUXh3H7U6s` Trading Dead Markets: EVZ 8/6/5 levels; playbook: sit out, or crosses only with full exit at TP1; test the system now.
18. `022_6NfU2OwuyTc` Forex Review - How I Trade: **daily procedure**: 1:40 pm PT, EVZ, then news, then whiteboard, then maintenance, then scan and write down, then size, then market orders; volume affects risk.
19. `032_qgJ0yiaE-VM` Forex Automation: test manual vs automated; EAs demo ≥2 months; automate backtesting and post-entry management; supplement, don't replace.


---

# Part C — Stonehill Forex indicator tests

## C.0 Summary (compiled from C1 and C2 below)

**Headline (a), spot-checked:** none of the 103 videos states a win rate, ROI, profit factor or
trade count. They are chart walk-throughs; the numbers live on the Stonehill blog. Verdicts
below are Stonehill's own words, not measured results.

**Stonehill's backtest protocol (a)** — fullest statement in the Cyber Cycle video
(https://www.youtube.com/watch?v=5bOZJ16LKww); details in C1 §1.1, C2 §1.3–1.4:
- Four markets: EUR/USD, gold, Bitcoin, S&P 500; two testing horizons; daily chart, 3 years.
- $100k, 2% risk, 20:1 leverage; each signal = two half-trades; continuations excluded.
- Stop 1.5×ATR (EUR/USD, SPX), 1.25×ATR (BTC, gold); TP half at 1×ATR, then breakeven.
- Metrics: signal count, win/loss (excluding "chop"), ROI; default settings as benchmark.
- Volume filters: fixed SMA(20) baseline, direction signal first, filter strictly above threshold.

**Caveat for our validation gate (a)/(c):** Stonehill often tests several signal readings or
settings (RMO 6 modes, Ergodic TVI 3, Correlation Trend 33 price inputs, Crossroads "thousands
of iterations") and publishes the best. The number of variants behind a result is mostly not
stated, so their results are selection-biased screens, not evidence. We use them to choose
**what to test**, never as a substitute for our own test.

**Strongest stated results by role (a), qualitative:**

| Role | Indicators Stonehill rates highly | Source part |
|---|---|---|
| Baseline | GChannel (gold, BTC), McGinley Dynamic, ATR-based EMA v1 | C1 |
| C1 / confirmation | Kalman Filter, Mass Index (tweaked), Trend Intensity Index, Ehlers Correlation Trend, Forecast Oscillator, MBFX Timing, Chandelier Exit (BTC, gold) | C1, C2 |
| C2 | Kuskus Starlight, Dorsey Inertia, TopTrend, Trend Lord, Glitch Index | C1 |
| Volume / volatility | Silence, Williams VIX Fix, Market Meanness Index | C2 |
| Weak | RSI and CCI as zero-cross confirmations | C1 |
| Vendor (treat as promotional) | Crossroads, ETDI (Stonehill's own) | C1, C2 |

## C.1 Overlap with our indicator library

Stonehill tested these indicators that are already in our library, or close relatives.
"Related" = same family, not necessarily the same formula (c).

| Stonehill test | Role tested | Our library | Match |
|---|---|---|---|
| Super Smoother | Baseline | SuperSmoother2Pole | Same family (a)/(c) |
| Ehlers 3-Pole Butterworth | Baseline | SuperSmoother3Pole | Related (c) |
| FRAMA | Baseline | FRAMA | Same |
| Fisher | Confirmation | FisherTransform | Same family |
| Reflex | Confirmation | Reflex | Same |
| Cyber Cycle | Confirmation | CyberCycle | Same |
| Roofing Filter | Confirmation | RoofingFilter | Same |
| Decycler Oscillator | Confirmation | Decycler | Related (oscillator form) (c) |
| RMO | Confirmation | RMO | Same |
| Elegant Oscillator | Confirmation | Elegant Oscillator (IFT) | Same |
| Kalman Filter | Confirmation | AlphaBetaFilter | Related — ours is a fixed-gain α–β tracker (c) |
| Ehlers Correlation Trend | Confirmation | Correlation Cycle | Related (c) |
| Bandpass Filter | Confirmation | — | Not implemented |
| Ehlers Early Onset Trend, DELI, Reverse EMA, 2nd-order HP Gaussian | Confirmation | — | Not implemented (Ehlers, sources may be in our TASC set) |

Inference (c): our Week 14 finding that several "cycle" indicators are linear filters applies
here too — e.g. Roofing, Decycler and Bandpass are close in frequency terms, so Stonehill's
separate verdicts on them should not be read as independent evidence.

## C1 — Stonehill Forex indicator-profile videos: extracted test setup and results

Source set: Stonehill Forex YouTube "indicator profile / technical analysis" videos. That is 21 baseline-playlist files (14 unique videos) and confirmation-playlist files 001–047 (47 unique videos), so **61 unique videos**. Every file was read in full.

Labels: **(a)** SOURCE STATES (paraphrase, with short quotes where the wording matters) · **(b)** MEASURABLE (can be coded or tested) · **(a)(b)** both · **(c)** INFERENCE (my interpretation).

---

### 0. Headline finding: read this first

- **(a)** These videos are visual walkthroughs on a chart. Results are not in them. Nearly every video sends the viewer to the **blog** on stonehillforex.com for numbers: "check out the results we got in our testing portion in the blog" ([R Squared](https://www.youtube.com/watch?v=Sbr0x03eQGY)). The videos also say the demonstrated settings are not the tested ones: "These are not optimized settings and do not represent trades we would take" (same URL).
- **(a)(b)** **None of the 61 videos states a win rate, ROI, profit factor or trade count for an indicator.** The only numbers are (i) settings, (ii) single-trade arithmetic examples (ATR, TP and SL levels in pips) and (iii) protocol parameters (balance, risk, leverage, SL multiple).
- **(c)** The results table below therefore holds qualitative verdicts only, and its Win rate and ROI columns are "—" throughout. To get comparable numbers, you would have to pull the Stonehill blog pages for these indicators. That is a separate source, not covered here.

---

### 1. Testing method (recurring setup)

#### 1.1 Formal backtest protocol (blog results), as described in the videos

The only full statement of the protocol is in the **Cyber Cycle** video ([5bOZJ16LKww](https://www.youtube.com/watch?v=5bOZJ16LKww)). Stonehill presents it as a protocol *change* made at the start of a new year (the year is not stated).

| # | Item | Label | Detail |
|---|---|---|---|
| 1 | Timeframe | (a)(b) | Daily only, "as the premise of the system is predicated on using this particular chart" |
| 2 | History length | (a)(b) | Expanded from **1 year to 3 years**, to set "a more realistic expectation from indicators through various markets" |
| 3 | Price data | (a)(b) | "data from the open of each candle". Tick-level testing would be "time prohibitive" |
| 4 | Method | (a) | "the proper No Nonsense Forex way of testing indicators" rather than the "quick and dirty method" VP discussed in a **2018** podcast |
| 5 | Starting balance | (a)(b) | **$100,000** fictitious balance |
| 6 | Risk | (a)(b) | **2%** risk profile |
| 7 | Feed | (a) | Live-account price feed, not demo |
| 8 | Leverage | (a)(b) | **20:1** (not 50:1 or 100:1) |
| 9 | Counting | (a)(b) | They post the number of **signals**, not trades. **Each signal = two half-trades** |
| 10 | Outcomes per signal | (a)(b) | (1) both halves stopped out. (2) half 1 hits TP, half 2 stopped. (3) half 1 hits TP, half 2 profits via trailing stop. (4) "chop"/no trade: the opposite signal arrives before either SL or TP. (5) see SL row |
| 11 | Stop loss | (a)(b) | SL = **1.25 × ATR for Bitcoin and gold**, **1.5 × ATR for "the Euro and the SPX 500"** |
| 12 | Continuation trades | (a)(b) | **Not included** |
| 13 | Reported metrics | (a)(b) | Number of signals, **win/loss ratio excluding chop trades**, and **return on investment** |
| 14 | Benchmark | (a)(b) | Default settings give the benchmark. Tweaked values are compared against it, with an aim "to avoid … curve fitting or overfitting" |

**Test basket.**
- (a)(b) The four markets implied by the SL rule are a Euro pair, SPX 500, Bitcoin and gold ([Cyber Cycle](https://www.youtube.com/watch?v=5bOZJ16LKww)).
- (a) The RSI/CCI video confirms the count: "we tested both indicators on our four pairs, as we usually do" ([jKu614LPLpw](https://www.youtube.com/watch?v=jKu614LPLpw)).
- (a) Other videos name members of the basket: "Euro US dollar" default-settings testing ([R Squared](https://www.youtube.com/watch?v=Sbr0x03eQGY)); "great results in the gold and Bitcoin markets" ([GChannel](https://www.youtube.com/watch?v=2qOesDJn3nY)); "Bitcoin US dollar" ([Crossroads](https://www.youtube.com/watch?v=oOaH5tsP58k)); Bitcoin display bugs found during testing ([Momentum Candles](https://www.youtube.com/watch?v=LfkZKETnVYI)); "non forex pairs" ([Range Filter](https://www.youtube.com/watch?v=5O9x3TXSMTw)).
- (c) Most likely EURUSD, SPX500, BTCUSD and XAUUSD. "Euro" is never spelled out as EURUSD in the protocol statement itself.

**Fixed dates and pairs.**
- (a) "when we test our indicators we use the same time span the same time frame and the same pairs. The only thing we change are the dates. We change them only once for testing and only to keep them current" ([Crossroads](https://www.youtube.com/watch?v=oOaH5tsP58k)).
- (a) Same video: they warn against testers who run "78 pairs all time frames" and cherry-pick.

**Optimisation and reporting stance.**
- (a) "We post what we get and they're not even close to the best we saw" ([Lemantrend](https://www.youtube.com/watch?v=keRtpAEs0cE)).
- (a) RSI/CCI: "we published some of the best optimized results to demonstrate that we don't just choose what's profitable" ([jKu614LPLpw](https://www.youtube.com/watch?v=jKu614LPLpw)).
- (a) RMO overfitting warning: backtests do not necessarily reflect forward tests, and "be sure you can actually trade the settings" ([HwS48R7PVCE](https://www.youtube.com/watch?v=HwS48R7PVCE)).
- (a) Crossroads: on BTCUSD "the default values were the best out of the thousands of iterations" ([oOaH5tsP58k](https://www.youtube.com/watch?v=oOaH5tsP58k)).
- (a)(b) RMO: tested six usage modes (three single-line zero crosses and three two-line crosses). Only the winner was published. The other five are available by email ([HwS48R7PVCE](https://www.youtube.com/watch?v=HwS48R7PVCE)).
- (a) Ergodic TVI: three modes tested; only the winner shown ([J0PonkxmFOQ](https://www.youtube.com/watch?v=J0PonkxmFOQ)).
- (c) For variant counting: Stonehill reports the best mode or setting out of several. Their published figures are therefore post-selection numbers, and the number of variants behind them is mostly not stated.

**Testing tool.**
- (a) An "algo tester" testing string is offered for RMO ([HwS48R7PVCE](https://www.youtube.com/watch?v=HwS48R7PVCE)).
- (a) The Elegant Oscillator video thanks "the No Nonsense Forex algo tester software" people ([ot5tXDBPbPM](https://www.youtube.com/watch?v=ot5tXDBPbPM)).
- (a) The Zero Lag MACD video says the "testing settings" are on the site's settings page ([Qf6UYuQYGdU](https://www.youtube.com/watch?v=Qf6UYuQYGdU)).

#### 1.2 Money management used in the video walkthroughs (NNFX standard)

- (a)(b) **TP1 = 1 × ATR on half the position. SL = 1.5 × ATR. After TP1, SL moves to breakeven and the second half trails.** Sources:
  - RMO worked example: ATR ~81 pips, "initial take profit level is one times the ATR value" ([HwS48R7PVCE](https://www.youtube.com/watch?v=HwS48R7PVCE)).
  - Kalman worked example: ATR ~65, TP = ATR × 1 = 65 pips, SL = ATR × 1.5 ≈ 98 pips ([pAmk3-n1N7M](https://www.youtube.com/watch?v=pAmk3-n1N7M)).
  - WPR-ma worked example: ATR 72, SL 108 pips (= 1.5 × 72) ([nqYc7E69cVM](https://www.youtube.com/watch?v=nqYc7E69cVM)).
- (a)(b) The trailing stop activates only after price reaches **2 × ATR** ("double the ATR value, which is 144 points") ([WPR ma](https://www.youtube.com/watch?v=nqYc7E69cVM)).
- (a)(b) **Entry** is on the candle after the signal candle ("The next candle reflects where we would have entered", [WPR ma](https://www.youtube.com/watch?v=nqYc7E69cVM)). The order goes in at the new period's open "or just before depending on your local trading time" ([Derivative Oscillator](https://www.youtube.com/watch?v=OPMU2_X6fgA)), or "30 minutes before the close of the trading day" ([Coral](https://www.youtube.com/watch?v=g3k79uJs1FA)).
- (a)(b) **Signal validity is decided on the candle close.** A wick through the line without a close beyond it is no signal (e.g. [SMA](https://www.youtube.com/watch?v=YDYaJLZ991w), [GD](https://www.youtube.com/watch?v=3U1islu6l6E), [Geometric Mean MA](https://www.youtube.com/watch?v=DFtH0syvu7I)). "Touch and go" on the zero line is no signal ([CMO](https://www.youtube.com/watch?v=Hkv9dcV5Etk), [Disparity Index](https://www.youtube.com/watch?v=IFBPe4YXjVg)).
- (a) "we always advocate checking through 36 Forex pairs each day" ([Disparity Index](https://www.youtube.com/watch?v=IFBPe4YXjVg)).
- (a) Weekend trades are not taken in live trading. Tests are "just testing, not actually trading" ([RMO](https://www.youtube.com/watch?v=HwS48R7PVCE)).

#### 1.3 How the videos themselves are made (not the backtest)

There are two modes, and they changed over time.
- (a) **Older baseline videos: 1-minute chart, 8-hour recording sped up.** "we record price data over an eight hour period on the one minute chart usually between the Asian and European sessions and then speed it up by about 30,000 times" ([Super Smoother](https://www.youtube.com/watch?v=Zt96g49x4GQ)). Tether Line shows "the European and New York sessions price action" recorded on the day ([jQxBYfM45L0](https://www.youtube.com/watch?v=jQxBYfM45L0)).
- (a) **Later confirmation videos: daily chart, about 1 year, default settings.** "we test data on the daily chart over the last year to demonstrate that it doesn't repaint, how it reacts with price action on the default settings, and more importantly, where the signals happen". 1-minute, 8-hour, ~25,000× live tests are used "only when there's some oddity" ([LSMA RVI](https://www.youtube.com/watch?v=vnU8RV7oLwc)). Further statements:
  - Cyber Cycle: "watching just the last year in this video contrary to the extended three-year testing span in the blog" ([5bOZJ16LKww](https://www.youtube.com/watch?v=5bOZJ16LKww)).
  - Momentum Candles: "compressing a year's worth of footage into a minute and a half" ([LfkZKETnVYI](https://www.youtube.com/watch?v=LfkZKETnVYI)).
  - HACOLT: "these analysis videos are made on the open prices" ([EOPIO69off4](https://www.youtube.com/watch?v=EOPIO69off4)).
  - XMA: "normally when we record our videos we use a fast method to generate signals" ([ZX6bBv9ULKA](https://www.youtube.com/watch?v=ZX6bBv9ULKA)).
- (a) **Pair choice is deliberately varied and "not cherry-picked"** (e.g. [Derivative Oscillator](https://www.youtube.com/watch?v=OPMU2_X6fgA), [PMO](https://www.youtube.com/watch?v=xhlNKnicKms), [R Squared](https://www.youtube.com/watch?v=Sbr0x03eQGY)). The video pair is usually *not* one of the four test markets.
- (a) **Each signal is tallied as a "win" or "loss" in the indicator-testing log.** Stonehill keeps saying a full algorithm would have avoided some of these trades.
- (a) **Baselines are judged on entries only.** "Remember, this is a baseline, so we're only calling entries. Exits are handled by other tools" ([FRAMA](https://www.youtube.com/watch?v=y-vMarpaovo)). Two baseline videos use a **Chandelier Exit** on default settings as the exit ([McGinley](https://www.youtube.com/watch?v=inttDvLfJzE), [Hull](https://www.youtube.com/watch?v=HWf9cd5CmN4)).
- (a) Confirmation videos test the indicator **standalone**, without a fixed baseline. One exception: the Fisher video runs a dummy long with an unnamed baseline, C1 and C2 picked "by throwing a dart", and Fisher as the exit ([2prIL8vrIaE](https://www.youtube.com/watch?v=2prIL8vrIaE)).
- (a) **Repainting checks.** Stated as a purpose of the daily-chart video ([LSMA RVI](https://www.youtube.com/watch?v=vnU8RV7oLwc)). Done explicitly at tick level for HACOLT ([EOPIO69off4](https://www.youtube.com/watch?v=EOPIO69off4)), MBFX Timing ([LWYmnKMdSEY](https://www.youtube.com/watch?v=LWYmnKMdSEY)) and XMA ([ZX6bBv9ULKA](https://www.youtube.com/watch?v=ZX6bBv9ULKA)).

#### 1.4 Signal-type taxonomy Stonehill uses (for coding)

- (a)(b) Indicators are classified by **placement** (price overlay or below chart) and by **signal type**:
  - single-line cross (price closes beyond the line)
  - zero cross
  - midline/midpoint cross
  - two lines cross
  - colour change
  - histogram
  - dots/arrows
- (a)(b) Stonehill often re-maps an indicator to a different signal type when that tested better (RMO, Roofing Filter, Ergodic TVI, Reflex, Cyber Cycle, Fisher, Mass Index; see the table).
- (a)(b) **Mass Index:** "a midline cross provides essentially the same information" as a zero cross ([qPcFn2ct9Ic](https://www.youtube.com/watch?v=qPcFn2ct9Ic)).
- (a)(b) **Colour change with a yellow transition state:** yellow means a possible signal; act only once the new colour closes ([Coral](https://www.youtube.com/watch?v=g3k79uJs1FA), [MBFX Timing](https://www.youtube.com/watch?v=LWYmnKMdSEY), [XMA](https://www.youtube.com/watch?v=ZX6bBv9ULKA)).

---

### 2. Results table

Win rate and ROI are "—" in every row: no video states them (see §0). "Key settings" lists only settings stated in the video. "Video pair" is the demo chart, not the test basket.

| # | Indicator | Role tested | Key settings (as stated) | Win rate | ROI/return | Other metrics / stated results | Verdict (paraphrase) | URL |
|---|---|---|---|---|---|---|---|---|
| B1 | Ehlers 3-Pole Butterworth Filter | Baseline | Default; gold chart; "filter through six data sets" | — | — | 15 signal changes in ~3 months of chop (video) | "has the goods to provide you with a foundation" | https://www.youtube.com/watch?v=8EZaP7Rqw6A |
| B2 | FRAMA (Ehlers) | Baseline | Period 10 → **20**; USDJPY | — | — | — | "a bit different … we love different"; worth trying | https://www.youtube.com/watch?v=y-vMarpaovo |
| B3 | SineWMA | Baseline | Not stated | — | — | — | "looked pretty good … definitely worth exploring" | https://www.youtube.com/watch?v=1l8-QkqSNN4 |
| B4 | McGinley Dynamic | Baseline (colour change) | USDJPY daily; Chandelier Exit as exit | — | — | Results "in the blog" | "did pretty well for us … worth the revisit" | https://www.youtube.com/watch?v=inttDvLfJzE |
| B5 | Simple Moving Average | Baseline | "sma2" (period unclear); NZDSGD | — | — | Results updated "in the blog" | Neutral: good when trending, poor when flat. Used for consistency/illustration, incl. when testing volume indicators | https://www.youtube.com/watch?v=YDYaJLZ991w |
| B6 | GD (Generalized DEMA) | Baseline | "small changes … completely random settings"; NZDJPY | — | — | "The results on the blog show a better picture" | No explicit verdict; deliberately hard chart | https://www.youtube.com/watch?v=3U1islu6l6E |
| B7 | Hull Moving Average | Baseline | Period 13 → **39**, linear weighted; Chandelier Exit (default) | — | — | "current testing data" in blog | Positive (qualitative) | https://www.youtube.com/watch?v=HWf9cd5CmN4 |
| B8 | Triangle Moving Average Generalized (Ehlers) | Baseline | Default; USDCHF | — | — | — | "good Baseline indicator … worth the time to test" | https://www.youtube.com/watch?v=cQNJpPduvfU |
| B9 | Range Filter | Baseline | Default changed (values unstated); ATR multiplier tunable | — | — | Original "had some issues" on non-forex pairs; recoded | "pretty happy with this Baseline" | https://www.youtube.com/watch?v=5O9x3TXSMTw |
| B10 | ATR-Based EMA Variant 1 | Baseline | Default; USDJPY | — | — | — | "should probably take a place in your arsenal" | https://www.youtube.com/watch?v=J49G3PxDfks |
| B11 | Tether Line | Baseline (colour change) | Length shortened (value unstated); intraday session recording | — | — | Blog "had some interesting results" | "had some promise" | https://www.youtube.com/watch?v=jQxBYfM45L0 |
| B12 | Geometric Mean MA | Baseline (single-line cross) | Default + a slower setting (unstated) | — | — | — | No explicit verdict | https://www.youtube.com/watch?v=DFtH0syvu7I |
| B13 | GChannel | Baseline | Channel (SL) lines removed; default | — | — | "great results in the gold and Bitcoin markets"; other markets "not … quite as remarkable" | Positive for gold and BTC | https://www.youtube.com/watch?v=2qOesDJn3nY |
| B14 | Super Smoother (2-pole) | Baseline | Not stated; 1-min, 8-hr recording | — | — | — | "I love a good Baseline especially one that reacts quickly" | https://www.youtube.com/watch?v=Zt96g49x4GQ |
| C1 | RMO (Rahul Mohindar Oscillator) | Confirmation | 6 modes tested; **winner: green filter line as zero cross**; AUDJPY default in video | — | — | Other 5 modes' results by email only | "did fairly well right out of the box" | https://www.youtube.com/watch?v=HwS48R7PVCE |
| C2 | R Squared (auto HTF v1.1) | Confirmation (two lines cross) | Default "not great" (near-continuous signals); slowed (unstated); S&P 500 | — | — | Default on EURUSD gave "pretty good results" but too many trades | Has potential; see blog | https://www.youtube.com/watch?v=Sbr0x03eQGY |
| C3 | Normalized Finite Volume Element | Confirmation (two lines cross) | EURUSD; settings not stated | — | — | — | Quick signals; "we've got something better" than FVE. Probably not an exit on default | https://www.youtube.com/watch?v=P8Zq4-1i40g |
| C4 | Finite Volume Element (FVE) | Confirmation (below chart two lines cross; *not* volume) | 4 variables, all optimised in testing; default in video; CHFSGD | — | — | "results … were actually quite good"; "numbers that clocked in a bit higher" (elsewhere) | "two-finger grin of approval" | https://www.youtube.com/watch?v=9n9A2BNU3JI |
| C5 | Andean Oscillator | Confirmation (two lines cross; yellow line removed) | Default | — | — | One trade: best possible ~246 pips over 25 days | "solid thumbs up … decent numbers as noted in the blog"; slower C | https://www.youtube.com/watch?v=YC0EIx2QZbA |
| C6 | LSMA RVI | Confirmation (zero cross) | Default | — | — | — | "did okay"; slower indicator | https://www.youtube.com/watch?v=vnU8RV7oLwc |
| C7 | Ehlers Roofing Filter | Confirmation | Tested two lines cross vs zero cross; **zero cross better** | — | — | — | Default "a bit slow"; "some possibility" | https://www.youtube.com/watch?v=LylUVxpNF0o |
| C8 | BamsBung | Confirmation (overlay colour change + star) | EURUSD; settings not stated | — | — | — | "good numbers" as a single-indicator signal; experiment with settings | https://www.youtube.com/watch?v=io-6WI35tug |
| C9 | Decycler Oscillator (Ehlers) | Confirmation (colour change) | Default; grey line removed; EURUSD | — | — | Tweaked metrics on blog | "definitely a C1 indicator using the default settings" (wording ambiguous) | https://www.youtube.com/watch?v=2Ev18paFr8U |
| C10 | Bandpass Filter (Ehlers) | Confirmation (zero cross) | Default (they call it slow); XAUUSD | — | — | Results in blog | "properly tweaked it could prove to be a very nice C1" | https://www.youtube.com/watch?v=Qe_SSVv0xn4 |
| C11 | Ergodic TVI | Confirmation | 3 modes tested; **winner: zero cross of EMA of ETVI line**; EURJPY default | — | — | — | Chose the winning mode | https://www.youtube.com/watch?v=J0PonkxmFOQ |
| C12 | Reflex (Ehlers) | Confirmation | Zero cross vs colour change: **colour change better**; default 50; USDSGD | — | — | — | Default slow; "Does this mean it's no good? Not hardly" | https://www.youtube.com/watch?v=VHaxwQklvgk |
| C13 | Disparity Index | Confirmation (zero cross) | Default 13 → **30**; USDSGD | — | — | One run "about 15 weeks" | Fast; use with caution | https://www.youtube.com/watch?v=IFBPe4YXjVg |
| C14 | Crossroads (Stonehill in-house) | Confirmation (overlay two lines cross) | Random settings in video; GBPUSD | — | — | BTCUSD: default = best of "thousands of iterations" | Very positive (own product) | https://www.youtube.com/watch?v=oOaH5tsP58k |
| C15 | Ehlers Reverse EMA | Confirmation (zero cross) | Max bars 500 → **999999** | — | — | One trade: ~150-pip move vs ATR ~55 | Slow as an exit. Suggests a two-line (Reverse EMA + EMA) C1 with a zero-cross C2 as an experiment | https://www.youtube.com/watch?v=El_wptPo7P4 |
| C16 | Cyber Cycle (Ehlers) | Confirmation (**zero cross** better than two lines cross) | Alpha range 0.02–0.25; EURUSD | — | — | 3-yr test in blog | Positive ("pretty slick") | https://www.youtube.com/watch?v=5bOZJ16LKww |
| C17 | HLC Trend | Confirmation (two lines cross) | Default; gold; 2019 version | — | — | — | "great runs on the default settings" | https://www.youtube.com/watch?v=9Jh7TIz3iq4 |
| C18 | Coral | Confirmation (overlay colour change) | AUDJPY | — | — | Updated results in blog | VP suggested it as an exit; in exit series | https://www.youtube.com/watch?v=g3k79uJs1FA |
| C19 | Perfect Trend Line | Confirmation (overlay two lines cross, dot = signal) | Optimised settings in blog | — | — | — | Positive; dot-only display shown | https://www.youtube.com/watch?v=lccfsQXm5So |
| C20 | Trend Lord | Confirmation (overlay colour change) | Length/mode/price (= MA settings); EURUSD | — | — | — | "not … the best, fastest … can make a great C2" | https://www.youtube.com/watch?v=aX34dxEGUWA |
| C21 | Mass Index | Confirmation (midline cross) | Default "pretty much sucked"; changed (unstated); midline setup in blog | — | — | "did really well on our testing" | Positive in testing | https://www.youtube.com/watch?v=qPcFn2ct9Ic |
| C22 | Metro (RSI derivative) | Confirmation (two lines cross; RSI line removed) | CHFSGD | — | — | "did surprisingly well in our testing" | Positive | https://www.youtube.com/watch?v=t1F5Y9tHU-Q |
| C23 | Kalman Filter | Confirmation (overlay colour change) | AUDUSD | — | — | "killer results in our testing" | Positive; also a "decent exit indicator" (VP) | https://www.youtube.com/watch?v=pAmk3-n1N7M |
| C24 | Lemantrend | Confirmation (two lines cross) | Default Fibonacci values | — | — | Blog "unbiased Benchmark testing" | "definite possibilities" | https://www.youtube.com/watch?v=keRtpAEs0cE |
| C25 | Fisher (next-gen Fisher Transform) | Confirmation (zero cross, from buffer values) | EURCHF | — | — | "four wins in a row" (video tally) | Positive; VP: possible exit | https://www.youtube.com/watch?v=2prIL8vrIaE |
| C26 | HACOLT | Confirmation (colour change) | CADCHF | — | — | No repaint (tick-checked) | Positive | https://www.youtube.com/watch?v=EOPIO69off4 |
| C27 | Price Momentum Oscillator | Confirmation (two lines cross, not zero cross) | EURNZD | — | — | — | "did so well on this pair" | https://www.youtube.com/watch?v=xhlNKnicKms |
| C28 | Zero Lag MACD | Confirmation (zero cross; histogram removed) | EURNZD | — | — | One trade ~5 weeks | "decent performance" | https://www.youtube.com/watch?v=Qf6UYuQYGdU |
| C29 | JPO (JP Oscillator) | Confirmation (zero cross / histogram) | Default; USDCAD | — | — | — | "did pretty good" on default | https://www.youtube.com/watch?v=8xNshToA3ew |
| C30 | SSL | Confirmation (overlay two lines cross) | 1 period setting; CHFJPY | — | — | — | VP "top 100"; good entry and exit | https://www.youtube.com/watch?v=cODJPLxt0Uk |
| C31 | Top Bottom | Confirmation (two lines cross) | Bug-fixed; USDJPY | — | — | — | "could be a decent C2" | https://www.youtube.com/watch?v=TRvkOJkbA7Y |
| C32 | Chande Momentum Oscillator | Confirmation (zero cross) | Default 9 → **14** | — | — | Blog results updated | "good C1 or C2" | https://www.youtube.com/watch?v=Hkv9dcV5Etk |
| C33 | Glitch Index | Confirmation (colour change histogram) | Levels/colours stripped | — | — | — | "a more user-friendly C2" | https://www.youtube.com/watch?v=PCx7pui4odQ |
| C34 | TopTrend (reissue) | Confirmation (overlay colour change) | "signal" option 1 → **2**; rest default | — | — | — | "a great C2 component" | https://www.youtube.com/watch?v=nvAbeRj5kl4 |
| C35 | WPR ma | Confirmation (two lines cross) | AUDSGD | — | — | Worked ATR example (see §4) | "hidden capabilities"; needs work | https://www.youtube.com/watch?v=nqYc7E69cVM |
| C36 | MBFX Timing (= Jurik RSX) | Confirmation (colour change + yellow) | Length 7 → **14** | — | — | First loser after a streak of winners (video) | "would make a superb C1" | https://www.youtube.com/watch?v=LWYmnKMdSEY |
| C37 | Smoothed Momentum | Confirmation (midpoint cross) | Midpoint details in blog | — | — | — | Use as C2, not as an exit | https://www.youtube.com/watch?v=SQeKznDOJHE |
| C38 | RSI and CCI (zero/midline cross) | Confirmation | OB/OS levels → median/zero line | — | — | "performed worse on all tested pairs than most indicators" | Negative; prefer indicators from 1996 or later | https://www.youtube.com/watch?v=jKu614LPLpw |
| C39 | Aroon Up/Down | Confirmation (two lines cross) | 2004 MetaQuotes version; GBPUSD | — | — | Blog includes testing results | "still got legs" | https://www.youtube.com/watch?v=7xeeZ4IcVc4 |
| C40 | Derivative Oscillator | Confirmation (histogram) | NZDCAD | — | — | — | "might make for a decent C2" | https://www.youtube.com/watch?v=OPMU2_X6fgA |
| C41 | XMA | Confirmation (histogram; recoded from overlay) | 2008 version, recoded | — | — | — | Positive; many signals | https://www.youtube.com/watch?v=ZX6bBv9ULKA |
| C42 | Composite Index | Confirmation (two lines cross) | 9 variables; GBPJPY | — | — | — | Mildly positive | https://www.youtube.com/watch?v=6X4cG_COb-A |
| C43 | Elegant Oscillator (Ehlers) | Confirmation (zero line) | Default; MA(20, SMA) overlay shown as an alternative | — | — | — | "pretty good … definitely has some possibilities" | https://www.youtube.com/watch?v=ot5tXDBPbPM |
| C44 | Dorsey Inertia | Confirmation (midline cross) | Default (3 settings); GBPSGD | — | — | "testing results are actually pretty good" | "would make a decent C2" | https://www.youtube.com/watch?v=YECjCvq1Ic4 |
| C45 | Linear Regression Slope | Confirmation (histogram) | Setting 40 → **24**; USDJPY | — | — | — | "may not be suitable as your main signal (C1)"; not an exit | https://www.youtube.com/watch?v=P1hqTwLzymc |
| C46 | Kuskus Starlight | Confirmation (zero cross) | Default (colours only) | — | — | "testing numbers were consistently good" | "solid C2 … thumbs up" | https://www.youtube.com/watch?v=ApwuJlxKCc4 |
| C47 | Momentum Candles (+ companion lower-window indicator) | Confirmation (overlay colour change and two-level) | Sensitivity 2.5 → **1.3** | — | — | Fixed for Bitcoin display | Good for entry, not exit | https://www.youtube.com/watch?v=LfkZKETnVYI |

**Role vocabulary.**
- (a) Every confirmation video is titled "as a Confirmation Indicator". Stonehill adds C1/C2 suitability as an aside, not as a separately tested role.
- (a) No video in this set tests volume or exit as its primary role. Exit suitability is mentioned for Coral, Kalman and Fisher; these appear in a separate "exit indicator series" playlist that these videos refer to.

---

### 3. Per-indicator notes (only what the table cannot hold)

#### Baselines

- **3-Pole Butterworth.** (a) Ehlers. Described as a better version of the 2-pole Super Smoother profiled ~4 years earlier, and smoother than it. Also: "your baseline is not really the right tool for an exit, although it is not a crime to use it" ([8EZaP7Rqw6A](https://www.youtube.com/watch?v=8EZaP7Rqw6A)).
- **FRAMA.** (a) Ehlers, 2001, *Rocket Science for Traders*. Adapts: it hugs price in consolidation and diverges in trends ([y-vMarpaovo](https://www.youtube.com/watch?v=y-vMarpaovo)).
- **SineWMA.** (a) Weights the middle of the window more than the ends. Coded 2016 from a 1999 concept ([1l8-QkqSNN4](https://www.youtube.com/watch?v=1l8-QkqSNN4)).
- **McGinley Dynamic.** (a) John McGinley, 1997. Has a colour change (green long, orange short) ([inttDvLfJzE](https://www.youtube.com/watch?v=inttDvLfJzE)).
- **SMA.**
  - (a) Stonehill/NNFX "adopted the sma2 for the simple fact that it provides consistency with well-known indicators for both comparative and illustrative purposes". It is the MA used "when testing volume indicators".
  - (a) "VP does not use this as part of his algorithm".
  - (a) Signal is a close beyond the line; a wick through it does not count ([YDYaJLZ991w](https://www.youtube.com/watch?v=YDYaJLZ991w)).
- **GD.** (a) The settings are "completely random". (a)(b) Stonehill's baseline signal definition, stated generically: "price crosses the signal line and closes above it for a long … closes below it for a short".
  - (a) The baseline is "not a point of departure". It can serve as an emergency exit if price reverses faster than the C/exit indicators can react.
  - (a) "your volume indicator doesn't have to agree" in that case ([3U1islu6l6E](https://www.youtube.com/watch?v=3U1islu6l6E)).
- **Hull MA.**
  - (a) The default 13 is "a bit fast … way too many useful signals [sic]", so it was tripled to 39 ("no significance").
  - (a) Discusses how far after a baseline signal one may still enter. Host: "I'd give it a week or so"; others use a day or two ([HWf9cd5CmN4](https://www.youtube.com/watch?v=HWf9cd5CmN4)).
  - (c) Compare this with the NNFX "one-candle rule" and 7-candle baseline rules in the A/B source documents. The host is giving personal preference, not a protocol.
- **Triangle MA Generalized.** (a) Ehlers trend work, 1990s. Recoded from MT5 (2019) to MT4 by "Neils" ([cQNJpPduvfU](https://www.youtube.com/watch?v=cQNJpPduvfU)).
- **Range Filter.** (a) 2023, ATR-based. Fixed by Neil for non-forex pairs. The multiplier "can tighten things up for earlier signals" ([5O9x3TXSMTw](https://www.youtube.com/watch?v=5O9x3TXSMTw)).
- **Tether Line.** (a) Leaves a visible gap where the signal line crosses price: "just something in the code". (c) Check for repainting before coding; the video does not say ([jQxBYfM45L0](https://www.youtube.com/watch?v=jQxBYfM45L0)).
- **GChannel.**
  - (a) The channel lines suggest stop-loss levels. Stonehill removes them and uses NNFX stops.
  - (a) "There is no hard and fast rule that your first confirmation indicator can't be the pointy end of your stick", meaning the baseline and C1 roles are interchangeable in ordering.
  - (a) "should not be trading live for at least six months" ([2qOesDJn3nY](https://www.youtube.com/watch?v=2qOesDJn3nY)).
- **Super Smoother.** (a) Attributed to a 2014 developer (name garbled; see §4). Described as "quick acting and non-lagging" ([Zt96g49x4GQ](https://www.youtube.com/watch?v=Zt96g49x4GQ)).

#### Confirmations

- **RMO.**
  - (a) Three components: histogram (primary trend), gold signal line (EMA of RMO, slower) and green filter line (EMA of RMO, faster). The "depth" setting was added by the MT4 converter and is not Mohindar's.
  - (a)(b) Winner: **green filter line, zero cross**.
  - (a) Warns that over-fit settings can be untradeable visually ([HwS48R7PVCE](https://www.youtube.com/watch?v=HwS48R7PVCE)).
- **R Squared.** (a) Leave the MTF settings at default for daily traders ([Sbr0x03eQGY](https://www.youtube.com/watch?v=Sbr0x03eQGY)).
- **FVE.** (a) Markos Katsanos. "Even though the word volume is found in the title, it's not a volume indicator". (a) "we're just trying to prove that the indicators we talk about can do better than others" ([9n9A2BNU3JI](https://www.youtube.com/watch?v=9n9A2BNU3JI)).
- **NFVE.** (a) Normalised FVE, described as better than FVE, with quick signals. "Could it be considered as an exit indicator? … without some tweaking, probably not" ([P8Zq4-1i40g](https://www.youtube.com/watch?v=P8Zq4-1i40g)).
- **Andean Oscillator.** (a) 2022. The yellow (signal) line was removed: the author suggested it for exits and disclaimed it for entries ([YC0EIx2QZbA](https://www.youtube.com/watch?v=YC0EIx2QZbA)).
- **Roofing Filter.** (a) Three possible uses cited online. The fourth is Stonehill's own suggestion and is untested: enter on the zero cross, exit on the two-lines cross ([LylUVxpNF0o](https://www.youtube.com/watch?v=LylUVxpNF0o)).
- **Decycler Oscillator.** (a) Ehlers, *Cycle Analytics for Traders* (2013). Uses the 2017 colour-change version ([2Ev18paFr8U](https://www.youtube.com/watch?v=2Ev18paFr8U)).
- **Bandpass.** (a) Ehlers paper, 2008. Zero cross; "very forgiving and keeps you in the trade for a long time" ([Qe_SSVv0xn4](https://www.youtube.com/watch?v=Qe_SSVv0xn4)).
- **Ergodic TVI.** (a) William Blau, 1995. They chose not to publish all three modes' results to avoid confusion ([J0PonkxmFOQ](https://www.youtube.com/watch?v=J0PonkxmFOQ)).
- **Reflex.** (a) Ehlers, 2020. Uses the Super Smoother internally. Default 50 is "a pretty large number" ([VHaxwQklvgk](https://www.youtube.com/watch?v=VHaxwQklvgk)).
- **Crossroads.**
  - (a) Stonehill's own indicator. WMA and inverse-WMA variants using highest and lowest values; coded by Neil.
  - (a) "there are a couple of rules you'll need to know" (in the blog).
  - (c) It is their own product, so treat the verdict as promotional ([oOaH5tsP58k](https://www.youtube.com/watch?v=oOaH5tsP58k)).
- **Reverse EMA.** (a)(b) Set **Max bars to 999999** "to prevent any issues with backtesting" ([El_wptPo7P4](https://www.youtube.com/watch?v=El_wptPo7P4)).
- **Cyber Cycle.** (a)(b) **Alpha outside 0.02–0.25 gives "very strange … useless" results**. Ehlers 2004 article; MT4 2007 ([5bOZJ16LKww](https://www.youtube.com/watch?v=5bOZJ16LKww)).
- **HLC Trend.** (a) Looks like ASO and Lemantrend, and shares their default settings. Neil verified from the code that it is a different indicator ([9Jh7TIz3iq4](https://www.youtube.com/watch?v=9Jh7TIz3iq4)).
- **Coral.** (a) IIR filter. Yellow is a transition warning. Enter ~30 min before the daily close ([g3k79uJs1FA](https://www.youtube.com/watch?v=g3k79uJs1FA)).
- **Perfect Trend Line.** (a) The lines "kiss" without giving a signal; only the dot is the signal. The original was locked; Neil found an unlocked version and stripped code for faster backtesting ([lccfsQXm5So](https://www.youtube.com/watch?v=lccfsQXm5So)).
- **Trend Lord.** (a) Equivalent to an MT4 moving average (length, mode, price) shown as a colour change ([aX34dxEGUWA](https://www.youtube.com/watch?v=aX34dxEGUWA)). (c) It is probably a colour-coded MA slope or MA-vs-price state. Verify in code.
- **Mass Index.** (a) Midline placement "makes a difference"; the details are in the blog ([qPcFn2ct9Ic](https://www.youtube.com/watch?v=qPcFn2ct9Ic)).
- **Metro.** (a) RSI derivative, 2005. In trends the lines separate and slope; in ranges they flatten and run parallel. "Not overlapping except for the actual cross". A "more advanced version" was also posted ([t1F5Y9tHU-Q](https://www.youtube.com/watch?v=t1F5Y9tHU-Q)).
- **Kalman.** (a) Adapts to volatility. Listed first under "confirmation" in the library ([pAmk3-n1N7M](https://www.youtube.com/watch?v=pAmk3-n1N7M)).
- **Lemantrend.**
  - (a) The default values are Fibonacci numbers.
  - (a) Ignore the zero line and the upper and lower bounds; the two-line cross is the signal.
  - (a) Blog results are "not even close to the best we saw" ([keRtpAEs0cE](https://www.youtube.com/watch?v=keRtpAEs0cE)).
- **Fisher.** (a) Visually a histogram, colour change and zero cross at once. Tested as a zero cross "because technically that's what the data for the buffer values gave us" ([2prIL8vrIaE](https://www.youtube.com/watch?v=2prIL8vrIaE)).
- **HACOLT.**
  - (a) Heikin-Ashi Candle Oscillator Long Term (Sylvain Vervoort, 2012).
  - (a) Intrabar colour flashes exist, but it closes on the correct colour. "There was no repainting. We've checked both numerically and visually … at a tick level" ([EOPIO69off4](https://www.youtube.com/watch?v=EOPIO69off4)).
- **PMO.**
  - (a) Normalised ROC derivative (difference divided by the standard deviation). Used as a two-lines cross although it crosses zero.
  - (a) "will not be cherry-picking" this pair for future videos ([xhlNKnicKms](https://www.youtube.com/watch?v=xhlNKnicKms)).
- **SSL.** (a) Described as an interpolation of the Schaff Trend Cycle, with one period setting. VP "top 100"; his video has "over 200,000 views" ([cODJPLxt0Uk](https://www.youtube.com/watch?v=cODJPLxt0Uk)).
- **Top Bottom.** (a) Pine Script → MT4 (2023). Neil fixed bugs. Similar to Aroon but "not the same thing" ([TRvkOJkbA7Y](https://www.youtube.com/watch?v=TRvkOJkbA7Y)).
- **CMO.**
  - (a) Multiple signals around zero at short periods.
  - (a) A C2 "would knock out most of those false starts" ([Hkv9dcV5Etk](https://www.youtube.com/watch?v=Hkv9dcV5Etk)).
- **Glitch Index.** (a) Bars that print nothing mean no information, not an exit. MT4 2024 from a 2013 Lua / MetaStock source ([PCx7pui4odQ](https://www.youtube.com/watch?v=PCx7pui4odQ)).
- **TopTrend.**
  - (a) Bollinger-like. The `signal` option: 0 = stops only, 1 = signals and stops (default), 2 = signals only.
  - (a) "by its nature C2 … would cause us to miss a significant portion of the movement" ([nvAbeRj5kl4](https://www.youtube.com/watch?v=nvAbeRj5kl4)).
- **WPR ma.** (a) The WPR calculation affects the MA; it is not just two indicators stacked. 2023 MT4 port of a TradingView script ([nqYc7E69cVM](https://www.youtube.com/watch?v=nqYc7E69cVM)).
- **MBFX Timing = Jurik RSX.**
  - (a) Signal procedure: yellow is a warning, and a second yellow means no signal. Wait for the new colour to close, then confirm on the next candle's open.
  - (a) "would make a superb C1 … quick to react". Slower C2s would have held the whole move ([LWYmnKMdSEY](https://www.youtube.com/watch?v=LWYmnKMdSEY)).
- **Smoothed Momentum.** (a) "not as an exit … as a C2" ([SQeKznDOJHE](https://www.youtube.com/watch?v=SQeKznDOJHE)).
- **RSI/CCI.**
  - (a) VP's hypothesis: a zero/midline cross would match modern indicators. It was refuted on all four pairs.
  - (a) "the concept of overbought and oversold in the foreign exchange market does not actually exist".
  - (a) Recommends indicators from "1996 or later" ([jKu614LPLpw](https://www.youtube.com/watch?v=jKu614LPLpw)).
- **Aroon.** (a) Chande, 1995. In sideways markets the lines narrow and run parallel; this is not an exit by itself ([7xeeZ4IcVc4](https://www.youtube.com/watch?v=7xeeZ4IcVc4)).
- **Derivative Oscillator.** (a) Constance Brown, 1994: triple-smoothed RSI plus MAs ([OPMU2_X6fgA](https://www.youtube.com/watch?v=OPMU2_X6fgA)).
- **XMA.** (a) DEMA-type MA of an MA plus a comparative filter. Neil corrected "inaccurate code". Yellow bars: hold if you are in a trade; wait if you are not ([ZX6bBv9ULKA](https://www.youtube.com/watch?v=ZX6bBv9ULKA)).
- **Composite Index.** (a) Constance Brown, 1999: unbounded RSI plus a momentum component ([6X4cG_COb-A](https://www.youtube.com/watch?v=6X4cG_COb-A)).
- **Elegant Oscillator.** (a) Ehlers, 2022: inverse Fisher of price, then Super Smoother. The MA overlay was a demonstration, "not … for our testing" ([ot5tXDBPbPM](https://www.youtube.com/watch?v=ot5tXDBPbPM)).
- **Dorsey Inertia.** (a) Donald Dorsey, *S&C* Sept 1995: linear regression of the RVI ([YECjCvq1Ic4](https://www.youtube.com/watch?v=YECjCvq1Ic4)).
- **Linear Regression Slope.** (a) The exit "would eat up a significant portion of your profit". Includes a divergence-trading critique ([P1hqTwLzymc](https://www.youtube.com/watch?v=P1hqTwLzymc)).
- **Kuskus Starlight.** (a) 2007. Linear regression plus smoothing ([ApwuJlxKCc4](https://www.youtube.com/watch?v=ApwuJlxKCc4)).
- **Momentum Candles.**
  - (a) Price-only, with no MA or delay, so it gives "a huge number of signals".
  - (a) "Ghost" (empty) candles mean no signal.
  - (a) The companion indicator by Neil gives "identical signals" ([LfkZKETnVYI](https://www.youtube.com/watch?v=LfkZKETnVYI)).

---

### 4. Ambiguities

#### Results and numbers

1. **No quantitative results anywhere.** Each "did well in testing" claim refers to blog figures that are not in the transcripts.
2. **SMA "sma2".** The period is unclear. It could be SMA 2, SMA 20 or a garbled "SMA too" ([YDYaJLZ991w](https://www.youtube.com/watch?v=YDYaJLZ991w)).
3. **WPR ma worked example: the numbers do not reconcile.**
   - Stated: entry "0.978", low 0.90050, high 0.91178, close "0.910004", TP 0.90808, SL 0.88998 ("108 pips below"), trail level 0.90222.
   - (c) Back-solving from TP − 72 pips gives an entry of ≈ 0.9009. "0.978" is likely mis-transcribed.
   - Unclear ([nqYc7E69cVM](https://www.youtube.com/watch?v=nqYc7E69cVM)).
4. **Kalman example.**
   - Entry "0.651 126 or 6512", TP "6577", SL "6414", loss "98 Pips 975".
   - (c) Most likely entry 0.6512, TP 0.6577 (65 pips), SL ≈ 0.6414 (97.5 pips) ([pAmk3-n1N7M](https://www.youtube.com/watch?v=pAmk3-n1N7M)).
5. **RMO example.** TP stated as "about 94.468", entry 95.278 and ATR ~81. 95.278 − 0.81 = 94.468, which is consistent. But the text says the TP "is larger than the ATR of 80 or 81"; the meaning there is unclear ([HwS48R7PVCE](https://www.youtube.com/watch?v=HwS48R7PVCE)).
6. **Decycler: "definitely a C1 indicator using the default settings".** It is unclear whether this means "suited as C1" or "behaves like a slow C1 on default" ([2Ev18paFr8U](https://www.youtube.com/watch?v=2Ev18paFr8U)).
7. **Hull: "way too many useful signals".** Probably "useless"; it is a transcription error ([HWf9cd5CmN4](https://www.youtube.com/watch?v=HWf9cd5CmN4)).
8. **Protocol date.** The Cyber Cycle protocol (3 years, $100k, 2%, 20:1) is called new "for a new year", but no year is given. It is unclear which other videos' blog results use the old 1-year protocol and which use the new one.
9. **"the Euro and the SPX 500"** for the 1.5 × ATR SL. The exact Euro pair is not named.
10. **Tether Line timeframe.** It says the data was recorded "the day we made this video" (European and NY sessions), yet also "you're trading on the daily time frame". The video's chart timeframe is therefore unclear ([jQxBYfM45L0](https://www.youtube.com/watch?v=jQxBYfM45L0)).
11. **Fisher "four wins in a row".** This is a video tally, not a backtest metric.

#### Names (likely mis-transcriptions; corrections are (c) unless noted)

- "Ellers" / "Ellis" = John **Ehlers** (Roofing, Decycler, Bandpass, Reflex, Cyber Cycle, Triangle MA, Elegant, Fisher).
- "Colman filter from Rudolph Colman" = **Kalman** (Rudolf Kálmán).
- "Steve Nissan" = **Steve Nison**. "Muna" = Munehisa **Homma**.
- "syane verot" = Sylvain **Vervoort** (HACOLT). "hakol / hinachi" = **HACOLT / Heikin-Ashi**.
- "Carl swanland" = probably Carl **Swenlin** (PMO). "Morton baratz" (ROC origin): unclear.
- "jerk RSX / jerich / jurich" = Mark **Jurik**, Jurik RSX.
- "Layman Trend" = **Lemantrend**. "cuscus / couscous" = **Kuskus**. "dorsy" = **Dorsey**.
- "Alex Pierfu" (Andean, 2022): unclear. Possibly the TradingView author "alexgrover" (c).
- "Corel ermenko" (Super Smoother, 2014): unclear coder name.
- "Patrick laferty, ctg Trading Group" (SineWMA): unverified spelling.
- "seor signal level", "SE before … lights or Flags" = likely **Semaphore** Signal Level (c). "shaft Trend cycle" = **Schaff** Trend Cycle.
- "Ballinger" = Bollinger. "Dima" = DEMA. "MLQ5" = MQL5. "2011 advanced course" = 201 advanced course.
- "Neils / Neil / Nils" = Stonehill's in-house coder (same person, inferred).

#### Transcript quality

Several transcripts read as machine-translated rather than captioned: GD, ATR EMA, Ergodic TVI, Trend Lord, Fisher, Top Bottom, TopTrend, WPR ma, Composite Index, LinReg Slope, Momentum Candles. They contain phrases like "Xerox results", "Super overclocking" and "purchase agreement" for "long". Do not rely on their exact wording.

---

### 5. Coverage (every file in the set)

#### Baseline_Indicators (21 files, 14 unique)

| File | Status | Contribution |
|---|---|---|
| 002_8EZaP7Rqw6A_Ehlers_3_Pole_Butterworth_Filter_as_a_Baseline_Filter.txt | unique | 3-pole Butterworth baseline, gold, default; positive |
| 004_y-vMarpaovo_FRAMA_as_a_Baseline_Indicator.txt | unique | FRAMA 10→20, USDJPY; "baseline = entries only" |
| 005_1l8-QkqSNN4_SineWMA_as_a_Baseline_Indicator.txt | unique | SineWMA; positive, no settings |
| 006_inttDvLfJzE_McGinley_Dynamic_as_a_Baseline_Indicator.txt | unique | McGinley + Chandelier Exit, USDJPY; "did pretty well" |
| 007_YDYaJLZ991w_Simple_Moving_Average_SMA_as_a_Baseline_Indicator.txt | unique (read) | SMA as the NNFX reference MA; close-not-wick rule |
| 008_YDYaJLZ991w_Simple_Moving_Average_SMA_as_a_Baseline_Indicator.txt | duplicate of 007 (body identical) | — |
| 009_3U1islu6l6E_GD_as_a_Baseline_Indicator.txt | unique (read) | GD; generic baseline signal definition; baseline-as-emergency-exit |
| 010_3U1islu6l6E_GD_as_a_Baseline_Indicator.txt | duplicate of 009 (body identical) | — |
| 011_HWf9cd5CmN4_Hull_Moving_Average_as_a_Baseline_Indicator.txt | unique | Hull 13→39 LWMA + Chandelier; late-entry window ("a week or so") |
| 012_cQNJpPduvfU_Triangle_Moving_Average_Generalized_as_a_Baseline.txt | unique | Ehlers TMA Generalized, USDCHF, default; positive |
| 013_5O9x3TXSMTw_Range_Filter_as_a_Baseline_Indicator.txt | unique | Range Filter (ATR), fixed for non-forex; positive |
| 014_J49G3PxDfks_ATR_Based_EMA_Variant_1_as_a_Baseline_Indicator.txt | unique (read) | ATR-based EMA, USDJPY default; positive |
| 015_J49G3PxDfks_ATR_Based_EMA_Variant_1_as_a_Baseline_Indicator.txt | duplicate of 014 (body identical) | — |
| 016_jQxBYfM45L0_Tether_Line_as_a_Baseline_Indicator.txt | unique (read) | Tether Line; crossing gap quirk; "had some promise" |
| 017_jQxBYfM45L0_Tether_Line_as_a_Baseline_Indicator.txt | duplicate of 016 (body identical) | — |
| 018_DFtH0syvu7I_Geometric_Mean_MA_as_a_Baseline_Indicator.txt | unique (read) | Geometric Mean MA default vs slower; doji/close rule; psychology section |
| 019_DFtH0syvu7I_Geometric_Mean_MA_as_a_Baseline_Indicator.txt | duplicate of 018 (body identical) | — |
| 020_2qOesDJn3nY_GChannel_as_a_Baseline_Indicator.txt | unique (read) | GChannel; strong on gold and BTC, weaker elsewhere |
| 021_2qOesDJn3nY_GChannel_as_a_Baseline_Indicator.txt | duplicate of 020 (body identical) | — |
| 022_Zt96g49x4GQ_Super_Smoother_as_a_Baseline_Indicator.txt | unique (read) | Super Smoother; 1-min/8-hr/30,000× video method |
| 023_Zt96g49x4GQ_Super_Smoother_as_a_Baseline_Indicator.txt | duplicate of 022 (body identical) | — |

#### Confirmation_Indicators 001–047 (47 files, 47 unique; no duplicate IDs)

| File | Status | Contribution |
|---|---|---|
| 001_HwS48R7PVCE_RMO_as_a_Confirmation_Indicator.txt | unique | RMO, 6 modes, green filter zero cross wins; TP = 1×ATR example |
| 002_Sbr0x03eQGY_R_Squared_as_a_Confirmation_Indicator.txt | unique | R Squared; default too busy; EURUSD test mention; "not optimized" disclaimer |
| 003_P8Zq4-1i40g_Normalized_Finite_Volume_Element_as_a_Confirmation_Indicator.txt | unique | NFVE, EURUSD; quick; not an exit on default |
| 004_9n9A2BNU3JI_Finite_Volume_Element_FVE_as_a_Confirmation_Indicator.txt | unique | FVE two lines cross; "results quite good" |
| 005_YC0EIx2QZbA_Andean_Oscillator_as_a_Confirmation_Indicator.txt | unique | Andean two lines cross; "decent numbers" |
| 006_vnU8RV7oLwc_LSMA_RVI_as_a_Confirmation_Indicator.txt | unique | LSMA RVI zero cross; states the video method (daily, 1 yr, repaint check) |
| 007_LylUVxpNF0o_Ehlers_Roofing_Filter_as_a_Confirmation_Indicator.txt | unique | Roofing: zero cross beat two lines cross |
| 008_io-6WI35tug_BamsBung_as_a_Confirmation_Indicator.txt | unique | BamsBung overlay colour change, EURUSD |
| 009_2Ev18paFr8U_Decycler_Oscillator_as_a_Confirmation_Indicator.txt | unique | Decycler Oscillator colour change, EURUSD |
| 010_Qe_SSVv0xn4_Bandpass_Filter_as_a_Confirmation_Indicator.txt | unique | Bandpass zero cross, gold; "nice C1" if tweaked |
| 011_J0PonkxmFOQ_Ergodic_TVI_as_a_Confirmation_Indicator.txt | unique | Ergodic TVI, 3 modes; EMA-of-ETVI zero cross wins |
| 012_VHaxwQklvgk_Reflex_as_a_Confirmation_Indicator.txt | unique | Reflex: colour change beat zero cross; default 50 |
| 013_IFBPe4YXjVg_Disparity_Index_as_a_Confirmation_Indicator.txt | unique | Disparity Index 13→30; "36 pairs daily" |
| 014_oOaH5tsP58k_Cross_Roads_as_a_Confirmation_Indicator.txt | unique | Crossroads (own); fixed dates/pairs/timeframe testing statement |
| 015_El_wptPo7P4_Ehlers_Reverse_EMA_as_a_Confirmation_Indicator.txt | unique | Reverse EMA; max bars 999999 |
| 016_5bOZJ16LKww_Cyber_Cycle_as_a_Confirmation_Indicator.txt | unique | **Full backtest protocol**; Cyber Cycle zero cross; alpha range |
| 017_9Jh7TIz3iq4_HLC_Trend_as_a_Confirmation_Indicator.txt | unique | HLC Trend two lines cross, gold |
| 018_g3k79uJs1FA_Coral_as_a_Confirmation_Indicator.txt | unique | Coral colour change with yellow; exit candidate; entry 30 min before close |
| 019_lccfsQXm5So_Perfect_Trend_Line_as_a_Confirmation_Indicator.txt | unique | Perfect Trend Line; dot = signal |
| 020_aX34dxEGUWA_Trend_Lord_as_a_Confirmation_Indicator.txt | unique | Trend Lord = colour-coded MA; "great C2" |
| 021_qPcFn2ct9Ic_Mass_Index_as_a_Confirmation_Indicator.txt | unique | Mass Index midline; "did really well on our testing" |
| 022_t1F5Y9tHU-Q_Metro_as_a_Confirmation_Indicator.txt | unique | Metro (RSI derivative); "surprisingly well" |
| 023_pAmk3-n1N7M_Kalman_Filter_as_a_Confirmation_Indicator.txt | unique | Kalman; "killer results"; SL = 1.5×ATR example |
| 024_keRtpAEs0cE_Lemantrend_as_a_Confirmation_Indicator.txt | unique | Lemantrend; "post what we get" reporting stance |
| 025_2prIL8vrIaE_Fisher_as_a_Confirmation_Indicator.txt | unique | Fisher zero cross; exit demo with full stack |
| 026_EOPIO69off4_Hacolt_as_a_Confirmation_Indicator.txt | unique | HACOLT; tick-level no-repaint check |
| 027_xhlNKnicKms_Price_Momentum_Oscillator_as_a_Confirmation_Indicator.txt | unique | PMO two lines cross, EURNZD |
| 028_Qf6UYuQYGdU_Zero_Lag_MACD_as_a_Confirmation_Indicator.txt | unique | Zero Lag MACD zero cross, EURNZD |
| 029_8xNshToA3ew_JPO_as_a_Confirmation_Indicator.txt | unique | JPO zero cross, USDCAD |
| 030_cODJPLxt0Uk_SSL_as_a_Confirmation_Indicator.txt | unique | SSL two lines cross; VP top 100 |
| 031_TRvkOJkbA7Y_Top_Bottom_as_a_Confirmation_Indicator.txt | unique | Top Bottom; decent C2 |
| 032_Hkv9dcV5Etk_Chande_Momentum_Oscillator_as_a_Confirmation_Indicator.txt | unique | CMO 9→14; C1 or C2 |
| 033_PCx7pui4odQ_Glitch_Index_as_a_Confirmation_Indicator.txt | unique | Glitch Index; C2 |
| 034_nvAbeRj5kl4_TopTrend_as_a_Confirmation_Indicator_Reissue.txt | unique | TopTrend; signal option = 2; C2 |
| 035_nqYc7E69cVM_WPR_ma_as_a_Confirmation_Indicator.txt | unique | WPR ma; trailing stop at 2×ATR example |
| 036_LWYmnKMdSEY_MBFX_Timing_as_a_Confirmation_Indicator.txt | unique | MBFX = Jurik RSX; yellow-state procedure; "superb C1" |
| 037_SQeKznDOJHE_Smoothed_Momentum_as_a_Confirmation_Indicator.txt | unique | Smoothed Momentum midpoint; C2, not exit |
| 038_jKu614LPLpw_Revisiting_RSI_CCI_as_Confirmation_Indicators.txt | unique | RSI/CCI zero cross worse than most; "four pairs" |
| 039_7xeeZ4IcVc4_Aroon_Up_Down_as_a_Confirmation_Indicator.txt | unique | Aroon two lines cross, GBPUSD |
| 040_OPMU2_X6fgA_Derivative_Oscillator_as_a_Confirmation_Indicator.txt | unique | Derivative Oscillator histogram; C2; entry timing |
| 041_ZX6bBv9ULKA_XMA_as_a_Confirmation_Indicator.txt | unique | XMA recoded to histogram; yellow bars |
| 042_6X4cG_COb-A_Composite_Index_as_a_Confirmation_Indicator..txt | unique | Composite Index two lines cross, GBPJPY |
| 043_ot5tXDBPbPM_Elegant_Oscillator_as_a_Confirmation_Indicator.txt | unique | Elegant Oscillator zero line; MA-overlay how-to |
| 044_YECjCvq1Ic4_Dorsey_Inertia_as_a_Confirmation_Indicator.txt | unique | Dorsey Inertia midline; "pretty good"; C2 |
| 045_P1hqTwLzymc_Linear_Regression_Slope_as_a_Confirmation_Indicator.txt | unique | LinReg Slope 40→24; not C1, not exit |
| 046_ApwuJlxKCc4_Kuskus_Starlight_as_a_Confirmation_Indicator.txt | unique | Kuskus Starlight zero cross; "consistently good"; C2 |
| 047_LfkZKETnVYI_Momentum_Candles_as_a_Confirmation_Indicator.txt | unique | Momentum Candles 2.5→1.3; entry not exit; BTC fix |

Totals: 68 files read, 61 unique videos (14 baseline, 47 confirmation), 7 duplicates.


---

## C2 — Stonehill Forex indicator videos, part D: Confirmation 048–094, Volume/Volatility, Stonehill-created

**Scope.** Stonehill Forex YouTube transcripts (auto-captions):
- `Confirmation_Indicators/048_` to `094_`: 47 files, 34 unique videos.
- `Volume_Volatility_Indicators/`: 7 files (`003_..._Trading_With_Volume` left out as instructed), 7 unique.
- `Stonehill_Forex_Created_Indicators/`: 1 file, 1 unique.

That makes **55 files and 42 unique videos**. All 13 duplicate pairs have the same ID and were checked to have byte-identical bodies (diff after the 4-line header).

**Labels.** (a) = SOURCE STATES (Stonehill says it; paraphrased, short quotes in "…"). (b) = MEASURABLE (can be coded or tested). (a)(b) = both. (c) = INFERENCE (mine, with the reason given).

**Main caveat, read first.** These videos are *visual walk-throughs* of an indicator reacting to price. The numeric test results are almost always pushed to the companion blog ("check out the results in the blog"). Across all 42 videos, **no win rate, ROI, profit factor, trade count or with/without-filter improvement is spoken as a number for any tested indicator.** The one exception is a qualitative "100%" win/loss claim for Trend Intensity Index (057). Rankings in this document are therefore *Stonehill's qualitative remarks*, not measured results. Pulling the numbers needs the blog posts (see section 4).

---

### 1. Testing method (recurring setup)

#### 1.1 Two separate activities: the video stream and the blog test
- (a) The video is a demonstration of "how the indicator reacts to price", not the test. The test results are in the blog. Examples: 058 https://www.youtube.com/watch?v=A7b7NJi10fk, 059 https://www.youtube.com/watch?v=2Lh6bdOOr84, 070 https://www.youtube.com/watch?v=oWoOtOK51C8.
- (a) Trades in the video are counted visually as win or loss "in your journal". This is not a backtest (048 https://www.youtube.com/watch?v=BVOEdogusfQ; 052 https://www.youtube.com/watch?v=GVDoNTSjz6s).

#### 1.2 How the video data stream is made (this changes over time)
- **Phase 1: live 1-minute recording.** (a)(b) About 8 hours of live price on the **1-minute chart**, "usually between the Asian and European session", sped up about **30,000×** and paused for commentary. Viewers are told to "imagine" the daily chart. Recording forward in time is said to remove hindsight bias.
  Sources: 072 https://www.youtube.com/watch?v=g8OoMHoxIPY; 074 https://www.youtube.com/watch?v=eI2KxDu_gOA; 081 https://www.youtube.com/watch?v=rz0UQ-5RgKM; 083 https://www.youtube.com/watch?v=6BjB6I89BiA; 085 https://www.youtube.com/watch?v=SspOGGW-tq4; Choppiness 008 https://www.youtube.com/watch?v=ZQKZ-PTxdR4; Silence 007 https://www.youtube.com/watch?v=WLmOX6FY0Uk.
  Variations:
  - "about twenty thousand percent" (089 https://www.youtube.com/watch?v=jjWp_XhaZpE)
  - 25,000× (093 https://www.youtube.com/watch?v=OsNQ9-RVM0M)
  - a 15-hour stream (058)
  - a 12-hour stream around NFP (063 https://www.youtube.com/watch?v=66ZYjyq60l4)
  - the 5-minute chart compressed "120,000%" (061 https://www.youtube.com/watch?v=J8OqIsSicYU)
  - the New York session (087 https://www.youtube.com/watch?v=3elZQU3I-9k)
  - recording on different days and markets so as not to cherry-pick (062 https://www.youtube.com/watch?v=l1N4irbvYy4, 072)
- **Phase 2: replayed daily history.** (a) Stonehill announced a "change in data stream gathering methodology". They now record **a year of past daily data** from the platform at a similar pace, and used **two years** for Trend Intensity Index because its default settings are slow.
  Sources: 057 https://www.youtube.com/watch?v=Tln7U_OXScc; Williams VIX Fix 006 https://www.youtube.com/watch?v=KypvHXCRsA8.
  Later videos refer to "the last year" or "nearly 7 months" of signals: 053 https://www.youtube.com/watch?v=5LH6xgdT7eU, 055 https://www.youtube.com/watch?v=K0WNXyHKzS8, 056 https://www.youtube.com/watch?v=w-mjMnKqk4Y, ETDI https://www.youtube.com/watch?v=2JMzgt-ApSc.
  (a) Random Walk Index went **back to the 1-minute method** because the first stream was "totally unusable" (054 https://www.youtube.com/watch?v=fSYWx6Sn75s). Polarized Fractal Efficiency used a live 1-minute USD/JPY session (050 https://www.youtube.com/watch?v=fQUZGWTZvXI).
  (c) Phase order: going by playlist position, the 1-minute videos (058–094) are older and the daily-history videos (048–057) are newer. Inferred from the dates mentioned: 064 cites the "July 2023" digest, 052 says "holiday season for 2023", 049 says "welcome to 2024".
- Instruments shown in the video vary: EUR/USD (default), AUD/NZD (048, 049), CAD/CHF (051, 055), USD/JPY (050), Bitcoin (052), SGD/JPY (Chaikin 002 https://www.youtube.com/watch?v=Wk1jWNJ_XC4).

#### 1.3 The blog test (described only in passing in the videos)
- (a)(b) **Four test markets.** "the four we use" are EUR/USD, gold, Bitcoin, and S&P 500 / SPX 500.
  - 053: "did really well with Bitcoin and gold … okay with the other two markets"
  - 062: gold and Bitcoin "higher than the Euro and S&P markets"
  - 070: "the four markets we test"
  - 052: "two of the markets we tested … but gold and Bitcoin were shining"
  - 059: "all four markets and both testing horizons"
- (a)(b) **Two "testing horizons".** 059 says "both testing horizons". 057 cites EUR/USD "daily and 4-hour" and gold daily. Silence 007 cites the "4-hour SPX 500".
  (c) So the two horizons are probably **D1 and H4**. Inferred from those three mentions together; it is never stated directly.
- (a) **Default vs tweaked settings.**
  - Results are usually reported for defaults and for tweaked settings: "how this performed between default values and tweak settings" (054); "better settings are possible as indicated in the blog" (058); ETDI "tweaked settings were a lot better across all pairs".
  - The video usually runs on defaults "to give us a starting point" (058).
  - Sometimes the video uses arbitrary settings instead: "random settings we picked off the proverbial dartboard" (052), "arbitrary value" (056), "double the default values" (050).
- (a) **Bitcoin results are flagged as anomalous.** Default-setting results for Bitcoin "have deviated far off what other pairs return". Reasons given: ATR spikes (a graphic shows daily ATR from 250 to 1250), long dead periods, and gaps (062).
- (a) Any figures given are "default ROI percentages" (052). This suggests ROI% is one of the blog metrics.
  (c) ROI is the only metric named in passing. Win rate appears only as "100% win loss rates" (057).
- History length, date range, money management and trade-count thresholds for the blog test are **not stated** in any video.
  - (a) 057 says the number of trades "was a bit off from what we normally look for". This implies a minimum trade-count norm, but no figure is given.
  - (a) 061 says a "strange pattern regarding the number of operations [trades]" was fixed by adjusting settings.

#### 1.4 Volume/volatility test harness (consistent across the volume videos)
- (a)(b) **Control baseline is SMA(20).** "We've historically added a simple moving average with a 20 period" (MMI 001 https://www.youtube.com/watch?v=PgpbsJbp9Lo). Also "always employ as our control variable for signal direction" (TTMS 004 https://www.youtube.com/watch?v=9EcyIgnnWSc), and VIX Fix 006.
  Exceptions:
  - Silence 007 uses a colour-change confirmation overlay instead (indicator not named).
  - Chaikin 002 uses an unnamed "baseline" plus the **Chandelier Exit on defaults** as the exit.
  - Choppiness 008 uses an unnamed "baseline".
- (a)(b) **Order of checks.** Get the direction signal first (baseline cross and close), then check the volume/volatility filter. Enter on the open of the next candle (004, 007).
- (a)(b) **Catch-up window.** Volume may confirm one candle after the last confirmation (006). In MMI 001, "we'll usually give it up to a trading week to catch up". (c) These two windows conflict.
- (a)(b) **No exits on volume.**
  - A volume or volatility indicator is never used as an exit (002, 004, 006).
  - Volume indicators give "yes or no … not a long or a short signal" (001).
  - For testing only, the next baseline cross is used "as kind of a reset for the next trade" (001, 005).
- (a)(b) **Continuation trades do not need a volume check.** Only the first trade in a direction does (002).
- (a)(b) **Threshold rule.** The signal must be numerically *above* the threshold. Equal to the threshold is not valid. Verify with the MT4 Data Window when the values are close (Stiffness 005 https://www.youtube.com/watch?v=1T7NSW7HzG4).
- (a)(b) **NNFX Algo Tester settings shown** (001):
  - mode "BL" (baseline + volume)
  - baseline = SMA, period 20
  - volume type = "one-level cross"
  - parameter string = MMI period, file name (must match exactly), buffer value **-1**, midline value
  - Quote: "If you don't include the negative, the indicator will be treated like a confirmation indicator"
  - optimisation inputs are given as start / step / end
- (a)(b) **Market-level gate on the VIX.** "We're just looking for eight as our lower limit" (048 https://www.youtube.com/watch?v=BVOEdogusfQ). "We like to see the level of about eight or more" (006).
- **No with/without-filter improvement figure is stated in any volume video.** The benefit is shown only as a visual count of trades skipped ("saved again from entering a losing trade", 004).

#### 1.5 Other recurring practices
- (a)(b) A signal counts only when the candle **closes** across the line ("cross and close"): 063, 078 https://www.youtube.com/watch?v=bsTGZHZUaaQ, 083. For near-ties, use the Data Window: 050 (value 0.55 > 0 confirmed a cross), 065 https://www.youtube.com/watch?v=egstNlDz2ZA, 005.
- (a) Entry and exit roles should be tested separately. "Sometimes an entry makes a good exit and sometimes not so much" (081; also 078).
- (a) The video uses one indicator only. The full algorithm "would have kept you out" of whipsaws, so wins and losses in the video overstate single-indicator noise (several videos).
- (a) Repaint checks are done by forward screen recording plus a review of "manual testing" (093, 094 https://www.youtube.com/watch?v=Ju9D0KTpegM). Stonehill also started a repainting-indicators resource page (055).

---

### 2. Results table

Columns: Win rate / ROI / Other are numbers as spoken. "—" = not stated in the transcript; "unclear" = garbled. Role is Stonehill's framing (video title or "we're going to take a look at a … indicator").

| # | Indicator | Role (Stonehill's framing) | Key settings (as stated) | Win rate | ROI/return | Other metrics | Verdict (a) | URL |
|---|---|---|---|---|---|---|---|---|
| 048 | Chartmill Value (Dirk Vandycke 2013) | C1; below-chart zero-cross or midline-cross | defaults, "not slow[ed] down"; AUD/NZD | — | — | — | "definitely has promise if tuned up"; very reactive, whipsaws | https://www.youtube.com/watch?v=BVOEdogusfQ |
| 049 | DODA Stochastic (smoothed stochastic) | C1; below-chart midline cross | stock version fixed by coder Neil; AUD/NZD | — | — | — | positive ("lots of good trades"); settings tweaks suggested | https://www.youtube.com/watch?v=-AvHTYFRrKc |
| 050 | Polarized Fractal Efficiency | C1; below-chart zero cross | **2× default** values; USD/JPY 1-min | — | — | — | "did better than we initially thought"; worth experimenting | https://www.youtube.com/watch?v=fQUZGWTZvXI |
| 051 | Ehlers Early Onset Trend (quotient transform, 2014) | C1; below-chart zero cross | defaults; one of the two signal lines removed; CAD/CHF | — | — | — | "worked quite well" on defaults | https://www.youtube.com/watch?v=ZZ-OkdprpPI |
| 052 | Forecast Oscillator | C1 (fast); below-chart zero cross; also shown paired with Chandelier Exit as C2 | defaults too reactive; video: length **54**, price **4** ("randomly assigned"); Bitcoin chart | — | default ROI% "generally higher than many other indicators" | many trades; gold and BTC strong, two markets "soft" | has potential; suggested as C1 | https://www.youtube.com/watch?v=GVDoNTSjz6s |
| 053 | Chandelier Exit | C1; price-overlay colour change | ATR **22**, multiplier **3** ("alternate default", original concept) | — | — | BTC and gold "really well", other two "okay" | positive; "could definitely be worth your time" | https://www.youtube.com/watch?v=5LH6xgdT7eU |
| 054 | Random Walk Index | C1; below-chart two-lines cross | length increased from default (value not stated) | — | — | default vs tweaked results in blog | neutral; very reactive, no smoothing | https://www.youtube.com/watch?v=fSYWx6Sn75s |
| 055 | Turtle Trading Channel | C1; price-overlay colour change | defaults; EUR/USD then CAD/CHF | — | — | — | easy to use; needs a faster exit indicator | https://www.youtube.com/watch?v=K0WNXyHKzS8 |
| 056 | Trend Akkam (ATR-derived) | C1; price-overlay single-level cross | defaults "so slow"; arbitrary faster value (not stated) | — | — | video run: streak of wins | "we like this one"; results "have possibilities" | https://www.youtube.com/watch?v=w-mjMnKqk4Y |
| 057 | Trend Intensity Index (M.H. Pee, S&C Jun 2002); file says "Trading Intensity Index" | C1; below-chart midline | defaults in video; tweaked in test; 2-yr daily replay | **"100% win loss rates"** EUR/USD D1 & H4, gold D1 | — | trade count "a bit off from what we normally look for" | "very happy with the results"; "accuracy was amazing" | https://www.youtube.com/watch?v=Tln7U_OXScc |
| 058 | RSI-derived colour-change oscillator (2020 version) | C1; below-chart colour change | defaults in video | — | — | — | "appreciated this updated oldie"; better settings in blog | https://www.youtube.com/watch?v=A7b7NJi10fk |
| 059 | Ehlers Correlation Trend (S&C May 2020) | C1; below-chart two-lines cross | 33 price data sets, all tested | — | — | "excellent results through all four markets and both testing horizons" | strongly positive | https://www.youtube.com/watch?v=2Lh6bdOOr84 |
| 060 | Average Sentiment Oscillator (B.J. Nash 2012) | C1; two-lines cross or midline cross | defaults; both display modes give "the results will be the same" | — | — | "pretty good across the board", decent EUR/USD | positive, especially EUR or USD pairs | https://www.youtube.com/watch?v=u38YqPdMskQ |
| 061 | 2nd-Order High-Pass Gaussian Filter | C1; below-chart zero cross | slowed from defaults (value not stated); 5-min chart | — | — | trade-count anomaly fixed; EUR/USD comparison in blog | neutral or positive ("different") | https://www.youtube.com/watch?v=J8OqIsSicYU |
| 062 | Trend Direction (ATR-based, 2022) | C1; price-overlay single-line cross | display tweaks only | — | — | gold and esp. BTC higher than EUR/USD and S&P | "decent signals" | https://www.youtube.com/watch?v=l1N4irbvYy4 |
| 063 | Advance Trend Pressure (TP) | C1; two-lines cross or zero cross | length 14 → **36** in video | — | — | "mixed depending on the markets" | "has promise" | https://www.youtube.com/watch?v=66ZYjyq60l4 |
| 064 | Dollar Pile (vs Precision Trend Histogram) | C1 (histogram); C1/C2 or exit pairing suggested | one adjustable setting | — | — | — | "did pretty good" | https://www.youtube.com/watch?v=7nCDpdWKEss |
| 065 | IS Calculation | C1; two-lines cross | defaults | — | — | — | decent entries; could be better as exit | https://www.youtube.com/watch?v=egstNlDz2ZA |
| 067 | Ehlers DELI (Detrended Ehlers Leading Indicator) | C1; below-chart zero cross (line + histogram) | defaults | — | — | — | decent entries; exit possible | https://www.youtube.com/watch?v=ymENbEJE2f0 |
| 068 | StableFX (CCI crosses its own MA + filter) | C1; two-lines cross | modified from oscillator use (details in blog) | — | — | — | "you'll be pleasantly surprised" | https://www.youtube.com/watch?v=kggIr5ghvJU |
| 070 | Sheriff's HiLo (2023) | C1; price-overlay two-lines level | defaults | — | — | — | mixed ("some wins and some losses") | https://www.youtube.com/watch?v=oWoOtOK51C8 |
| 072 | Trigger Lines (least-squares MA) | C1; price-overlay colour change | defaults implied | — | — | — | "we really like this one" | https://www.youtube.com/watch?v=g8OoMHoxIPY |
| 074 | Prevailing Trend (MA-based, 2013) | C1; price two-lines cross | price data set selectable | — | — | — | positive ("pretty clear" signals) | https://www.youtube.com/watch?v=eI2KxDu_gOA |
| 076 | Precision Trend Histogram | C1; histogram colour change | defaults | — | — | — | "pretty happy"; good for new traders | https://www.youtube.com/watch?v=Jsovb7cx4aw |
| 078 | Jurik Volty Bands (used as zero cross) | C1; zero cross | some components removed | — | — | — | "not too bad" | https://www.youtube.com/watch?v=bsTGZHZUaaQ |
| 079 | QQE | C1; two-lines cross and midline cross (both tested) | — | — | — | — | "definitely has possibilities" | https://www.youtube.com/watch?v=Hp6SS3VYIiE |
| 081 | Detrended Price Oscillator | C1; zero-cross histogram | out of the box | — | — | — | neutral; poor exit in ranges | https://www.youtube.com/watch?v=rz0UQ-5RgKM |
| 083 | Polychromatic Momentum (Dennis Meyers 2002) | C1; zero cross | — | — | — | — | neutral; reactive in ranges | https://www.youtube.com/watch?v=6BjB6I89BiA |
| 085 | Coppock Curve (1962) | C1; zero-cross histogram | defaults 11 / 14 (months) | — | — | — | neutral | https://www.youtube.com/watch?v=SspOGGW-tq4 |
| 087 | Trendilo (modified to zero cross) | C1; zero cross | bands hidden; display only | — | — | — | neutral | https://www.youtube.com/watch?v=3elZQU3I-9k |
| 089 | Heiken Ashi Smoothed vs plain HA | C1; colour change | — | — | — | plain HA "changed colors six times while smooth remain[ed] green" | smoothed better than plain | https://www.youtube.com/watch?v=jjWp_XhaZpE |
| 091 | Kase Permission Stochastic Smoothed vs classic stochastic | C1; two-lines cross | — | — | — | — | smoothed better than classic (fewer trades and spreads) | https://www.youtube.com/watch?v=YIIeywTFZyA |
| 093 | Vulkan Profit (repaint study) | other: repaint check of an arrow indicator | 3 "non-repainting" versions tested | — | — | 8 h 1-min: **14** signals fixed, **2** painted late, about **55–60 periods** back | repaints sporadically; only usable live | https://www.youtube.com/watch?v=OsNQ9-RVM0M |
| 094 | Alaskan Pip Assassin, non-repainting version | other: repaint check / C1 two-lines cross | — | — | — | blue signal lags K-max line by **10 periods** | "would it be helpful? probably not" | https://www.youtube.com/watch?v=Ju9D0KTpegM |
| V001 | Market Meanness Index (MMI) | volume (single-level / midline cross) | level **71.3** (between about 73 and about 69); SMA20 baseline | — | — | — | "this one did a pretty good job"; VP "pretty darn good" | https://www.youtube.com/watch?v=PgpbsJbp9Lo |
| V002 | Chaikin Volatility | volume/volatility; zero cross (trade only above 0) | baseline (type not stated); Chandelier Exit on defaults as exit; SGD/JPY | — | — | — | qualitatively positive | https://www.youtube.com/watch?v=Wk1jWNJ_XC4 |
| V004 | TTM Squeeze (TTMS) | volatility; colour change (green = trade, grey = no) | defaults; SMA20 control | — | — | — | "we really like this indicator" | https://www.youtube.com/watch?v=9EcyIgnnWSc |
| V005 | Stiffness (M. Katsanos, S&C Nov 2018) | volatility; single-level cross | defaults; threshold **75** added | — | — | — | neutral or positive | https://www.youtube.com/watch?v=1T7NSW7HzG4 |
| V006 | Williams VIX Fix (2007) | volatility; single-level cross | threshold added (value not stated); SMA20 | — | — | "pretty good numbers across the board" | "useful if tweaked a bit" | https://www.youtube.com/watch?v=KypvHXCRsA8 |
| V007 | Silence (2009) | volatility; midline cross (converted from two-lines) | display modified; colour-change C1 control | — | — | "did quite well across all markets, especially on the 4-hour SPX 500" | "deserves a spot" | https://www.youtube.com/watch?v=WLmOX6FY0Uk |
| V008 | Choppiness Index (Bill Dreiss) | volatility ("tested it as a volume indicator"); below midpoint = trending | — | — | — | — | "went pretty well" | https://www.youtube.com/watch?v=ZQKZ-PTxdR4 |
| S001 | ETDI (Early Trend Detection Index), paid Stonehill indicator | C1; below-chart coloured histogram | defaults in video; Trigger Only = false (default) or true | — | — | tweaked "a lot better across all pairs" | "did pretty well" in a volatile EUR/USD year; "sparkling testing results" in blog | https://www.youtube.com/watch?v=2JMzgt-ApSc |

---

### 3. Per-indicator notes (only what the table cannot hold)

**048 Chartmill Value.** (a) Dirk Vandycke, 2013; does not use moving averages, so it has less lag. It can be read as zero cross or midline cross ("information is provided in the blog"). (a)(b) It "occasionally … will pop from one side of the zero line to the other and close before returning", so a single-bar flip counts as a signal. https://www.youtube.com/watch?v=BVOEdogusfQ

**049 DODA Stochastic.** (a) "Stock version[s] we found were not testing correctly"; coder Neil fixed it, and the fixed version is in the Stonehill library. Stonehill notes stochastics are normally "on the naughty list", but this one is smoothed and used as a midline cross. https://www.youtube.com/watch?v=-AvHTYFRrKc

**050 PFE.** (a)(b) Video settings are "double the default values". A near-zero cross was confirmed in the Data Window (value 0.55). https://www.youtube.com/watch?v=fQUZGWTZvXI

**051 Ehlers Early Onset Trend.** (a) Default settings, but one of the two signal lines was removed and the zero cross is used, which Stonehill says differs from the author's intended use. https://www.youtube.com/watch?v=ZZ-OkdprpPI

**052 Forecast Oscillator.**
- (a)(b) Video settings length 54, price 4; defaults were "just too reactive".
- (a) Second segment: Forecast Oscillator as C1 with Chandelier Exit (053) as C2. Baseline and volume are assumed to agree; the FO's opposite signals are ignored as exits.
- (a) The rationale is "indicators with different math one checks the other".
https://www.youtube.com/watch?v=GVDoNTSjz6s

**053 Chandelier Exit.** (a)(b) ATR 22 ("number of trading days in a month") and multiplier 3, chosen "to respect the original philosophy". Strict colour-change entry and exit would have turned one trade into a loss plus re-entry. https://www.youtube.com/watch?v=5LH6xgdT7eU

**054 Random Walk Index.** (a) The coder's default length makes signals "fast and furious", so Stonehill increased the length (new value not stated). The signal is the two lines crossing; the lines' own jitter is ignored. https://www.youtube.com/watch?v=fSYWx6Sn75s

**055 Turtle Trading Channel.**
- (a) Long = the red line above price flips to blue below price.
- (a) The Turtle history includes "trades book profits only 40 to 50% of the time". This is the 1980s Turtle programme, **not** a test result for this indicator.
- (a) Re-run on CAD/CHF; exits via the channel colour change gave back profit, so "better exit indicator".
https://www.youtube.com/watch?v=K0WNXyHKzS8

**057 Trend Intensity Index.**
- (a) Created by "MHP" (M.H. Pee), the same author as the Trend Continuation Factor profiled Dec 2022; published in S&C June 2002. Turned from an overbought/oversold oscillator into a midline cross.
- (a)(b) "100% win loss rates with the EUR US dollar pair on both the daily and 4-hour time frame and on the gold daily", with a low trade count.
- (c) A 100% rate on few trades is weak evidence. Stonehill itself flags the trade count.
https://www.youtube.com/watch?v=Tln7U_OXScc

**058 RSI-derived colour-change indicator.** (a) Name not given in the transcript beyond "derivative of the classic RSI", 2020 version. The filename says "Trading Oscillator". (a) "We look at 36 Forex Pairs" refers to live trading practice, not this test. https://www.youtube.com/watch?v=A7b7NJi10fk

**059 Ehlers Correlation Trend.** (a)(b) "33 available sets" (price types) for the internal calculation; "we tested through all of them". (c) That makes about 33 variants per market and horizon. Stonehill does not report a variant count against the result. https://www.youtube.com/watch?v=2Lh6bdOOr84

**060 Average Sentiment Oscillator.** (a) Two-part calculation on OHLC (detail in blog). (a) Side remark: the Tether Line indicator from the previous week "is the same as the Donchian Channel's middle signal line"; a code gap in it was fixed by Neil. https://www.youtube.com/watch?v=u38YqPdMskQ

**061 Gaussian HP filter.** (a) It looked "odd" on the 1-minute chart, so they used the 5-minute chart and slower-than-default settings. (a) "Strange pattern regarding the number of operations … remedy by making the necessary adjustments" (detail in blog). https://www.youtube.com/watch?v=J8OqIsSicYU

**062 Trend Direction.** (a) Bonus section on Bitcoin anomalies, see section 1.3. https://www.youtube.com/watch?v=l1N4irbvYy4

**063 Advance Trend Pressure.** (a)(b) Two views of the same signal: zero cross of the signal line, or green/red two-line cross. Lengthening 14 → 36 "captured" a whole trend in the video. https://www.youtube.com/watch?v=66ZYjyq60l4

**064 Dollar Pile.** (a) Run side by side with the Precision Trend Histogram (076). Exits are close to each other; Dollar Pile sometimes held longer. Stonehill suggests using one as entry and one as exit, or as C1/C2. https://www.youtube.com/watch?v=7nCDpdWKEss

**067 Ehlers DELI.** (a) Based on Ehlers' MESA; extended by "Bill Mars" (likely mis-transcribed); 2015 MT4 version. Line and histogram versions both in the library. https://www.youtube.com/watch?v=ymENbEJE2f0

**068 StableFX.** (a)(b) A CCI-based (1980) two-lines cross: "the CCI crosses a moving average already included on the indicator plus it has a filtering variable". https://www.youtube.com/watch?v=kggIr5ghvJU

**079 QQE.** (a) Tested both ways: two-lines cross, and the fast trail crossing the midline. A suggested hybrid is a two-lines-cross entry with a midline exit. Not profiled by VP "due to its widespread use". https://www.youtube.com/watch?v=Hp6SS3VYIiE

**081 DPO.** (a) Attributed in the transcript to "William Blau in 1991" with MACD roots. (c) Attribution as spoken; I have not verified it. https://www.youtube.com/watch?v=rz0UQ-5RgKM

**085 Coppock Curve.** (a) Default 11 and 14 come from the "mourning period" of 11 to 14 months that Episcopal bishops gave Coppock (transcript says "morning"). https://www.youtube.com/watch?v=SspOGGW-tq4

**087 Trendilo.** (a)(b) Display change: bands set to "none", signal line red width 4, zero level added in yellow. It is then used as a zero cross. https://www.youtube.com/watch?v=3elZQU3I-9k

**093 Vulkan Profit.** (a)(b) Three "non-repainting" versions downloaded; "all three still showed signs of sporadic repainting of the arrows … in different places". Over 8 h: 14 signals stayed fixed and 2 appeared after price had moved on, one about 55–60 periods back. Takeaway: forward testing ≠ back testing. https://www.youtube.com/watch?v=OsNQ9-RVM0M

**094 APA non-repainting.** (a) The MT4 strategy tester "indicated it was still somewhat of a repainter", but manual testing shows fixed past data. (a)(b) The blue signal lags the red K-max line by 10 periods, which makes the entry late. https://www.youtube.com/watch?v=Ju9D0KTpegM

**V001 MMI.**
- (a)(b) Overbought/oversold levels are deleted and a level of 71.3 is added, the midpoint of the observed upper (about 73) and lower (about 69) limits. Below the level = "trending zone" = trade. Above = "chop zone" = no trade. A bar "blipped just slightly above" was skipped.
- (a) Algo Tester details are in section 1.4. Mittendorf, 2010 (transcript "Jörg Mittenndorff").
- (a) A dated promo (discount until "2nd of May 2026") puts this video in about April 2026.
https://www.youtube.com/watch?v=PgpbsJbp9Lo

**V002 Chaikin Volatility.** (a)(b) Trade only when the value is above 0, for either direction. When the value is close to 0, verify in the data table. Volume is never used as an exit. The Chandelier Exit was used as the exit. https://www.youtube.com/watch?v=Wk1jWNJ_XC4

**V004 TTMS.** (a)(b) The squeeze is on (Bollinger Bands inside the Keltner Channel) = no trade, shown as grey dots. The squeeze "fired" (BB expand outside KC) = trade, shown as green (lime) dots. Default settings; "has [not] been optimized". https://www.youtube.com/watch?v=9EcyIgnnWSc

**V005 Stiffness.** (a)(b) Threshold line added at 75 (Data Window check "above 75"). Four signals where the value was *equal* to the threshold were rejected. https://www.youtube.com/watch?v=1T7NSW7HzG4

**V006 Williams VIX Fix.** (a) Synthetic MT4 VIX. (a)(b) A threshold level is added; the value is not given in the transcript. "Personal level of volatility tolerance will dictate the threshold level." Volatility may confirm within one candle after the signal. https://www.youtube.com/watch?v=KypvHXCRsA8

**V007 Silence.** (a) By Trofimov Evgeny Vitalievich, 2009. Converted from a two-lines cross to a midline cross. The rule is direction first, then volatility. https://www.youtube.com/watch?v=WLmOX6FY0Uk

**V008 Choppiness Index.** (a) "We tested it as a volume indicator but in reality it's more of a volatility tool." Closing below the midpoint = trending. Described as "our first volatility analysis". (c) Probably the first Stonehill volume/volatility video, given that remark. https://www.youtube.com/watch?v=ZQKZ-PTxdR4

**S001 ETDI.**
- (a) Stonehill's first paid indicator. MT4 only at release; licence valid on up to 3 accounts.
- (a)(b) "Trigger only" setting: false (default) prints bars for as long as the condition holds, which suits continuation trades; true prints only the first bar, so consecutive same-side signals are possible.
- (a) The video ran on defaults with a trailing stop mentioned. "141 additional free profile indicators to date."
- (c) The calculation is not disclosed (commercial). Treat the "sparkling" blog results as vendor claims until replicated.
https://www.youtube.com/watch?v=2JMzgt-ApSc

---

### 4. Ambiguities

1. **No numeric results in any video.** Win rate, ROI, profit factor and trade counts sit in the blog posts; the needed URLs are listed in section 5. The volume videos never quantify the improvement over a no-filter benchmark. Needs the blog.
2. **Test history length and dates** for the blog backtests are not stated anywhere. The "one year" or "two years" figures in 057, 006 and 053 describe the *video replay*, not the test.
3. **"Both testing horizons"** is read as D1 + H4 by inference (section 1.3); never defined explicitly.
4. **Catch-up window conflict.** One candle (006) vs "up to a trading week" (MMI 001). Possibly a later rule change; unclear.
5. **Thresholds not stated:** VIX Fix threshold (006); Chaikin's baseline type (002); the confirmation overlay used as control in Silence (007); the baseline in Choppiness (008).
6. **Changed settings not stated:** RWI new length (054); Trend Akkam faster value (056); Gaussian slower values (061); PFE actual defaults (050 says only "double").
7. **Names possibly mis-transcribed:**
   - 056 "Trend Akkam" ("trend aam" in audio)
   - 057 "Trading Intensity Index" in filename vs "trend intensity index" in audio (the audio is more plausible)
   - 058 filename "Trading Oscillator", indicator described only as an RSI derivative
   - 065 "IS Calculation"
   - 067 "Bill Mars"
   - 068 "StableFX"
   - 078 "Jurik Volty" ("jurik volte")
   - V001 "Jörg Mittenndorff"
   - V002 "Chaikin" (transcribed "Mark Chen / chin / Shen / shaken / jaken")
   - V005 "Katsanos" ("katanos")
   - V008 "Bill Dreiss" ("drice")
   - 085 "Coppock" ("Copic")
8. **081 DPO attribution** to William Blau 1991 is as spoken and not verified.
9. **057 "100% win loss rates"** is ambiguous: it may mean 100% wins, and the trade count is unstated ("a bit off").
10. **052:** the timeframe of the Bitcoin video chart is not stated.
11. **MMI midline formula.** The "simple formula" is shown on screen only. 71.3 is consistent with (≈73.x + ≈69.x)/2, but the exact limits are "some change", i.e. unclear.

---

### 5. Coverage (every file in the set)

**Confirmation_Indicators/**

| File | Status | Contribution |
|---|---|---|
| 048_BVOEdogusfQ_Chartmill_Value… | unique | Chartmill Value C1; VIX ≥ 8 gate |
| 049_-AvHTYFRrKc_Doda_Stochastic… | unique | DODA Stochastic midline C1, fixed code |
| 050_fQUZGWTZvXI_Polarized_Fractal_Efficiency… | unique | PFE zero cross at 2× defaults; Data Window check |
| 051_ZZ-OkdprpPI_Ehlers_Early_Onset_Trend… | unique | Ehlers EOT zero cross, defaults, CAD/CHF |
| 052_GVDoNTSjz6s_Forecast_Oscillator… | unique | FO settings 54/4; ROI remark; C1+C2 demo with Chandelier |
| 053_5LH6xgdT7eU_Chandelier_Exit… | unique | Chandelier ATR 22 × 3; four-market remark |
| 054_fSYWx6Sn75s_Random_Walk_Index… | unique | RWI two-lines; default vs tweaked; back to 1-min method |
| 055_K0WNXyHKzS8_Turtle_Trading_Channel… | unique | Turtle channel colour change; repaint page announced |
| 056_w-mjMnKqk4Y_Trend_Akkam… | unique | ATR-based single-level overlay; positive |
| 057_Tln7U_OXScc_Trading_Intensity_Index… | unique | TII; "100%" EUR/USD D1/H4 and gold D1; daily-replay method |
| 058_A7b7NJi10fk_Trading_Oscillator… | unique | RSI-derived colour change; 15 h stream |
| 059_2Lh6bdOOr84_Correlation_Trend… | unique | Ehlers CTI; 33 data sets; "four markets, both horizons" |
| 060_u38YqPdMskQ_Average_Sentiment_Oscillator… | unique | ASO two-line or midline; Tether Line = Donchian mid |
| 061_J8OqIsSicYU_2nd_Order_High_Pass_Gaussian_Filter… | unique | Gaussian HP zero cross; 5-min chart |
| 062_l1N4irbvYy4_Trend_Direction… | unique | ATR Trend Direction; Bitcoin anomaly explanation |
| 063_66ZYjyq60l4_Advance_Trend_Pressure… | unique | ATP; length 14 → 36; mixed results |
| 064_7nCDpdWKEss_Dollar_Pile… | unique | Dollar Pile vs Precision Trend Histogram |
| 065_egstNlDz2ZA_IS_Calculation… | unique | IS Calculation two-lines; Data Window teaching |
| 066_egstNlDz2ZA_IS_Calculation… | duplicate of 065 | none (identical body) |
| 067_ymENbEJE2f0_Ehlers_DELI… | unique | Ehlers DELI zero cross, line and histogram |
| 068_kggIr5ghvJU_StableFX… | unique | CCI-vs-MA two-lines cross with filter |
| 069_kggIr5ghvJU_StableFX… | duplicate of 068 | none |
| 070_oWoOtOK51C8_Sheriff_s_Hilo… | unique | Sheriff's HiLo overlay; "four markets we test" |
| 071_oWoOtOK51C8_Sheriff_s_Hilo… | duplicate of 070 | none |
| 072_g8OoMHoxIPY_Trigger_Lines… | unique | Trigger Lines (LSMA) colour change; 8 h 1-min method |
| 073_g8OoMHoxIPY_Trigger_Lines… | duplicate of 072 | none |
| 074_eI2KxDu_gOA_Prevailing_Trend… | unique | Prevailing Trend MA two-lines; method restated |
| 075_eI2KxDu_gOA_Prevailing_Trend… | duplicate of 074 | none |
| 076_Jsovb7cx4aw_Precision_Trend_Histogram… | unique | PTH histogram colour change |
| 077_Jsovb7cx4aw_Precision_Trend_Histogram… | duplicate of 076 | none |
| 078_bsTGZHZUaaQ_Jurik_Volty_Bands… | unique | Jurik Volty Bands as zero cross |
| 079_Hp6SS3VYIiE_QQE… | unique | QQE two-line and midline |
| 080_Hp6SS3VYIiE_QQE… | duplicate of 079 | none |
| 081_rz0UQ-5RgKM_Detrended_Price_Osciallator… | unique | DPO zero-cross histogram; 30,000× method |
| 082_rz0UQ-5RgKM_Detrended_Price_Osciallator… | duplicate of 081 | none |
| 083_6BjB6I89BiA_Polychromatic_Momentum… | unique | Polychromatic Momentum zero cross |
| 084_6BjB6I89BiA_Polychromatic_Momentum… | duplicate of 083 | none |
| 085_SspOGGW-tq4_Coppock_Curve_Indicator… | unique | Coppock 11/14 zero-cross histogram |
| 086_SspOGGW-tq4_Coppock_Curve_Indicator… | duplicate of 085 | none |
| 087_3elZQU3I-9k_Trendilo… | unique | Trendilo modified to zero cross |
| 088_3elZQU3I-9k_Trendilo… | duplicate of 087 | none |
| 089_jjWp_XhaZpE_Heiken_Ashi_Smooth… | unique | HA Smoothed vs HA ("six" flips vs none) |
| 090_jjWp_XhaZpE_Heiken_Ashi_Smooth… | duplicate of 089 | none |
| 091_YIIeywTFZyA_Kase_Permission_Stochastic_Smoothed… | unique | Kase smoothed vs classic stochastic |
| 092_YIIeywTFZyA_Kase_Permission_Stochastic_Smoothed… | duplicate of 091 | none |
| 093_OsNQ9-RVM0M_Vulkan_Profit_Indicator_Study | unique | repaint study: 14 fixed vs 2 late signals |
| 094_Ju9D0KTpegM_Alaskan_Pip_Assassin_Non-repainting… | unique | APA non-repaint; 10-period lag |

**Volume_Volatility_Indicators/**

| File | Status | Contribution |
|---|---|---|
| 001_PgpbsJbp9Lo_Market_Meanness_Index_MMI… | unique | MMI level 71.3; SMA20 harness; NNFX Algo Tester settings (buffer -1) |
| 002_Wk1jWNJ_XC4_Chaikin_Volatility… | unique | Chaikin above-zero rule; continuation needs no volume |
| 003_YRLEbYKSYq0_Trading_With_Volume | excluded per brief | not read (covered elsewhere) |
| 004_9EcyIgnnWSc_TTMS… | unique | TTM Squeeze grey/green; SMA20 control; next-open entry |
| 005_1T7NSW7HzG4_Stiffness… | unique | Stiffness threshold 75; equal ≠ valid |
| 006_KypvHXCRsA8_Williams_VIXFix… | unique | VIX Fix; VIX ≥ 8; one-candle catch-up; daily-replay method |
| 007_WLmOX6FY0Uk_Silence… | unique | Silence midline; strong on H4 SPX 500 |
| 008_ZQKZ-PTxdR4_Choppiness_Index… | unique | CI midpoint; "first volatility analysis" |

**Stonehill_Forex_Created_Indicators/**

| File | Status | Contribution |
|---|---|---|
| 001_2JMzgt-ApSc_Early_Trend_Detection_Index_ETDI… | unique | paid ETDI histogram; Trigger Only setting; tweaked > default |

Totals: 55 files read (003 in Volume excluded), 42 unique videos, 13 duplicates.
