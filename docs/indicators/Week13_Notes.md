# Week 13 — Volatility Indicators, Bands, and a C2 Candidate

**Dates:** 2026-08-12 to 2026-08-13 (Days 2-3)
**Branch:** `main`, 15 commits
**Assets:** EUR/USD D1 2015-2024 (2,596 bars), BTC/USD H4 2020-2024 (7,534 bars)

## Deliverables

| # | Item | File | Status |
|---|---|---|---|
| 24 | Normalized ATR | `UltimateChannelBands.c` | Complete |
| 25 | Ultimate Channels & Bands | `UltimateChannelBands.c` | Complete, P1-P4 measured |
| — | Volatility regime classifier | `VolatilityRegime.c` | Complete |
| — | RSIH (Hann-windowed RSI) | `RSIH.c` | Complete |
| — | Laguerre Oscillator (2025 TASC) | `LaguerreOsc.c` | Complete |
| 26 | Laguerre RSI (book) | `LaguerreRSI.c` | **Shortlisted for Strategy 2 C2** |

Two items were not in the plan and are recorded in `Week13_Plan_Amendment.md`: RSIH
(the plan listed the article but assigned no indicator number to it) and the Laguerre
Oscillator (absent entirely).

## What the week actually produced

Beyond the six deliverables, most of the time went to things the brief did not
anticipate:

- A **five-month data-labelling bug** — `Asset = "BTC/USD"` silently resolved to
  EUR/USD, writing FX data into a BTC-named file since May
- A **library-wide state-reset sweep** — nine indicator files whose statics persisted
  across runs
- **Two indicators that do not match their cited source** — `UltimateSmoother.c`, and
  the 2025 TASC Laguerre oscillator code contradicting its own article text
- **Two amendments to the C2 criteria**, both from gaps found while applying them
- **Two new GOTCHAS sections** (9b, 9c) covering eight failure modes
- A finding that **Week 9's validation is not reproducible** from the repo

## Predictions: ten registered, six hit

| | Predicted | Result | |
|---|---|---|---|
| P1 corr(str,sd) | 0.85-0.90 / 0.60-0.70, BTC lower | 0.666 / 0.786 | **MISS, reversed** |
| P2 median str/sd | 1.2-1.3, BTC lower | 1.509 / 1.459 | MISS, direction right |
| P3 trend-lag gap | 0.5-0.6, BTC larger | 0.026 / 0.008 | **MISS, reversed** |
| P4 lag-20 in band | present / absent | 8.82x / 1.16x | HIT |
| RSIH mean | positive both, BTC larger | -0.022 / +0.039 | MISS on EUR/USD |
| P-LR1 saturation | 35-55% | 37.8% / 37.4% | HIT |
| P-LR2 rho with C1 | 0.45-0.65 | 0.576 / 0.562 | HIT |
| P-LR3 crossing ratio | under 1.5x | 1.10x | HIT |
| P-LR4a lag | 1.5-4.0 bars LAG | 4.595 bars LEAD | **MISS, reversed** |
| P-LR4b ramp fails | yes | confirmed | HIT |

Four misses, three of them reversals. Every miss has a recorded mechanism; none was
revised after the fact.

---

# 1. Core theory

## 1.1 Channel vs Band — the same centre, two ways to measure width

Both draw an envelope around price. Both use the same centre line, an
UltimateSmoother of price. They differ only in how the width is measured.

**The channel measures bar size.** For each bar it takes the true range, then
smooths that sequence:

    channel_width = UltimateSmootherE(TrueRange, 20)

It never looks at the centre line. A bar's range is what it is regardless of where
the smoothed line sits.

**The band measures distance from the centre.** It takes how far each close sits from
the centre line, squares it, averages over 20 bars, and takes the root:

    band_width = sqrt(mean((Close - Centre)^2 over 20 bars))

Two consequences follow, and P1-P3 were built on them.

**Trend lag.** If the centre line trails price during a sustained move, `Close -
Centre` is large and one-signed bar after bar, so the band widens with no change in
actual volatility. Formally, splitting the deviation into a systematic part `d` and a
fluctuating part `e`:

    mean((d+e)^2) = d^2 + 2d*mean(e) + mean(e^2) = d^2 + sigma^2

so `band_width = sqrt(d^2 + sigma^2)` — actual spread PLUS how far off-centre the
line sits. It cannot tell them apart.

**Squaring.** The band squares each deviation, the channel does not, so one outsized
bar counts far more heavily in the band.

## 1.2 True range is Wilder's, in a cheaper form

Ehlers writes:

    TH = max(High, Close[1])
    TL = min(Low,  Close[1])
    TR = TH - TL

Wilder writes: the largest of `High-Low`, `|High-Close[1]|`, `|Low-Close[1]|`.

These are the same quantity. Checked across three cases:

    No gap    C1=105, bar 100-110:  Wilder max(10,5,5)   = 10   Ehlers 110-100 = 10
    Gap up    C1=100, bar 110-112:  Wilder max(2,12,10)  = 12   Ehlers 112-100 = 12
    Gap down  C1=120, bar 100-105:  Wilder max(5,15,20)  = 20   Ehlers 120-100 = 20

Wilder takes the max of three distances; Ehlers stretches the bar to include the
previous close and takes its span. Ehlers' form is one max, one min, one subtraction.

Earlier notes in this session described TH/TL as "not Wilder's true range". That was
wrong and is corrected here.

## 1.3 The Hann window (RSIH)

Classic RSI sums the up-moves and down-moves with equal weight — a rectangular
window, with the same cliff the boxcar band width shows in P4. A move enters at full
weight, sits 14 bars, then drops out abruptly.

RSIH weights each position instead:

    w(count) = 1 - cos(2*PI*count / (Length+1))

For Length 6:

    count:   1      2      3      4      5      6
    weight: 0.38   1.22   1.90   1.90   1.22   0.38

Near zero at both edges, peaking in the middle. A bar ageing out was already
contributing almost nothing, so there is no cliff.

**On length.** Ehlers gives two separate arguments, often collapsed into one. First,
the correct CLASSIC RSI length is half the dominant cycle, because RSI maxes over the
valley-to-peak stretch which is half a cycle. Second, Hann needs a LONGER window than
rectangular for equivalent smoothing, since the edge weights do little work — a Hann
6 smooths about as much as a rectangular 4. Together those put RSIH at roughly the
full dominant cycle period. So 14 is inherited from Wilder and is not his
recommendation.

Implemented at 20 (project convention). An adaptive variant driven by
`DominantCycle.c` is registered for later comparison, not assumed better — precedent
is fixed-period InstantTrendline outperforming its adaptive version on SNR.

## 1.4 Why huge drift produces a tiny offset

RSIH outputs `(CU-CD)/(CU+CD)`. Take a 20-bar stretch where up-moves total 520 and
down-moves 480:

    net move  = 520 - 480 =   40
    total move= 520 + 480 = 1000
    RSIH      = 40 / 1000 = 0.04

Price moved 1000 points in total; only 40 was net direction. The other 960 cancelled.
The indicator asks what FRACTION of movement was directional, and over a 20-bar
window noise dominates trend.

Measured: BTC rose 1,212% over its sample against EUR/USD's -13.9% — 87x more in
percentage terms — yet BTC's RSIH mean is only 1.8x larger in magnitude.

**Consequence:** RSIH thresholds transfer across assets without recalibration. NATR's
do not. Two indicators, same week, opposite behaviour on the same question.

## 1.5 Percentile rank, and why the classifier needed it

Measured NATR distributions barely overlap:

    EUR/USD D1   p10 0.42%   median 0.67%   p90 1.15%
    BTC/USD H4   p10 0.94%   median 1.83%   p90 3.71%

BTC's tenth percentile sits ABOVE EUR/USD's median. So no fixed NATR threshold can
label both assets: at 1.5% EUR/USD is never volatile, at 0.8% it flips constantly.

Percentile rank solves this by construction — it is 0-100 on any distribution, so one
threshold means the same thing everywhere. It is also distribution-free, which
matters because volatility has a hard floor at zero and a long right tail, breaking
the assumptions behind both a z-score (symmetric spread) and a ratio-to-mean (the
mean as a meaningful centre).

**The null for run length.** With independent labels at 30/40/30, two consecutive
bars match with probability

    0.3^2 + 0.4^2 + 0.3^2 = 0.09 + 0.16 + 0.09 = 0.34

so 66% of bars start a new run and the expected run length is 1/0.66 = **1.52**.
Confirmed by simulation over 2M bars (1.5158). Both assets measured near 3x that.

## 1.6 Group delay is not phase delay

Two different quantities, and the measurement method decides which one you get.

**Group delay** is what a ramp measures. A straight line is pure zero frequency, so
the ramp gives the DC figure.

**Phase delay** is what a sine cross-correlation measures, at that sine's frequency.

They converge at DC and diverge elsewhere. SuperSmoother P=20:

    at DC        group 4.0394   phase 4.0393
    at period 40 group 4.8340   phase 4.3505

The sine harness measured 4.349, matching phase delay to 0.03%. Compared against the
ramp's 4.039 it looked 7% wrong. Both numbers were correct; the comparison was not.

## 1.7 Differencing leads by a quarter cycle

    bar:        0     5    10    15    20    25    30    35
    sine:      0.0  +0.7  +1.0  +0.7   0.0  -0.7  -1.0  -0.7

Where is it highest? Bar 10. Where is it rising fastest? Look at the steps: 0->5
rises 0.7, 5->10 rises 0.3. Fastest rise is near bar 0 — at the peak it is not rising
at all.

So rate-of-change peaks a quarter cycle before level peaks. At period 40 that is 10
bars.

Laguerre RSI is built from differences between stages, so it inherits that lead:

    differencing        +10.0 bars lead
    four L stages        -5.2 bars lag
                        -----
    net                  +4.8 bars lead     measured 4.595

This is why P-LR4a missed in direction. The derivation accounted for the stages and
forgot the differencing.

---

# 2. Measured results

## 2.1 Ultimate Channels and Bands — P1 to P4

Article settings, no retuning: Length = STRLength = 20, NumSTRs = NumSDs = 1.

| | Predicted | EUR/USD | BTC | Verdict |
|---|---|---|---|---|
| P1 corr(str, sd) | 0.85-0.90 / 0.60-0.70, BTC lower | 0.666 | 0.786 | Miss, **reversed** |
| P2 median str/sd | 1.2-1.3 / 0.9-1.1, BTC lower | 1.509 | 1.459 | Miss, direction right |
| P3 gap | 0.5-0.6, BTC larger | 0.026 | 0.008 | Miss, **reversed** |
| P4 lag-20 in d(sd) | present / absent | 8.82x | 1.16x | **HIT** |

**P4 first — it is a verification, not a discovery.** Band width first-differenced
autocorrelation at lag 20 is **-0.4686**, 8.82x its neighbours at lags 15-25. The
channel shows 1.16x. The negative sign is the confirmation: a bar enters the 20-bar
window, lifts the width, then drops out abruptly 20 bars later. Lags 19 and 21 show
the expected smearing (-0.17, -0.20). Implementation verified, so P1-P3 are real
results rather than bugs.

**P2 missed as predicted the day before.** UltimateSmoother's lag measures **exactly
0.0000 bars** by algebraic cancellation, so the trend-lag inflation P2 assumed cannot
occur. Measured 1.509 against a 1.6 random-walk baseline: 6% inflation, not the 25%
predicted. Registered before the data.

**P1 reversed, and the premise is refuted.** BTC correlates HIGHER, in all eight
cells of the diagnostic grid. P1 reasoned that fatter tails hit the squared measure
harder so the widths disagree more. The premise is true; the inference is not. A
large shock enlarges the bar range AND pushes price from the centre — it moves both
widths together, and shared signal RAISES correlation. What lowers correlation is
disagreement on ordinary bars.

**Fat tails synchronise the two estimators rather than decoupling them.**

**The 2x2 that explains P1's level.** STR and SD differ in two ways at once — input
and filter class. Two extra columns filled the missing corners:

| corr | EUR/USD | BTC |
|---|---|---|
| same input, different averaging (str~tr_box) | 0.746 | 0.832 |
| same input, different averaging (dev_sm~sd) | 0.581 | 0.734 |
| same averaging, different input (str~dev_sm) | 0.696 | 0.825 |
| **same averaging, different input (tr_box~sd)** | **0.867** | 0.939 |
| both different (P1's comparison) | 0.666 | 0.786 |

`tr_box~sd` = 0.867 lands INSIDE P1's predicted range. So the input reasoning was
sound; P1 missed because it did not account for the filter-class difference.

Not clean: `str~dev_sm` = 0.696 despite matched averaging. Corner 4 uses absolute
rather than squared deviation, so it differs from SD in two ways. Not pursued.

**P3's split variable inverted the test.** Both ratios came in below 1; both were
predicted well above 1. `trend_score = |Close - FRAMA| / STR` divides by STR, so
high-volatility bars get a smaller score and land in the FLAT bucket. The
pre-registration identified this (Known Limitation 2) and judged it survivable
because it shares no term with the band width. That reasoning was about circularity
and holds. The severity was underestimated: the bias is strong enough to invert both
ratios, leaving no headroom for the effect being tested.

**Coherence.** P1, P2 and P3 were registered as resting on one claim: that BTC
decouples the two estimators more than EUR/USD. The document states a reversal would
contradict all three at once. P1 and P3 both reversed. **The shared premise is
refuted.**

**Practical consequence.** P4's cliff is real and matters for the ATR slot. A stop
placed on the band jumps inward roughly 20 bars after a volatility event, unrelated
to conditions at that moment. The channel has no such artifact. **For stop placement,
prefer the channel.**

## 2.2 NATR

    raw STR   EUR/USD 0.008172   BTC 800.72     factor 98,000
    NATR %    EUR/USD 0.7342     BTC 2.1945     factor 3.0

Price scale removed — five orders of magnitude down to three-fold. But the residual
gap matters: volatility scales as sqrt(time), so BTC's H4 median scaled to a D1
equivalent is 4.49% against EUR/USD's 0.67% — roughly **6.7x more volatile per unit
time**, not 3x.

Computed from STR (zero-lag smoother) rather than a boxcar or Wilder ATR, so it
inherits zero lag and the smoother's known overshoot.

## 2.3 Volatility regime classifier

250-bar percentile window, cut at 30/70. Parameters chosen before results, not swept.

| | EUR/USD D1 | BTC/USD H4 |
|---|---|---|
| avg run length | 5.41 | 4.51 |
| Calm run | 7.09 | 5.36 |
| **Normal run** | **3.42** | **3.43** |
| Volatile run | 7.76 | 5.80 |
| Calm -> Volatile | 1.0% | 1.5% |

Against a null of 1.52, both assets sit near 3x. Normal's run length matches to two
decimals across a D1 FX pair and an H4 crypto series — the no-retuning requirement
holds about as cleanly as it could.

**Two structural findings, neither imposed by the design.** Regimes step rather than
jump: Calm->Volatile is ~1% of transitions on both assets, so volatility passes
through Normal. And Normal is the least stable state (3.4 bars against 5-8 for the
extremes) — a transit corridor rather than somewhere the market sits.

**Not tested:** whether these labels predict anything. Run length shows the labels are
stable, not that trading differs across them. That is a strategy-level question under
Principle 7.

## 2.4 RSIH

| | EUR/USD D1 | BTC/USD H4 |
|---|---|---|
| mean | -0.0222 | +0.0393 |
| median | -0.0142 | +0.0334 |
| p5 / p95 | -0.555 / +0.517 | -0.545 / +0.656 |
| % above zero | 48.2 | 53.4 |
| price over sample | -13.9% | +1212.5% |

Prediction was positive on both, larger on BTC, magnitude under 0.1. Sign follows
drift on both and both magnitudes are under 0.1 — but **EUR/USD is negative**. The
prediction applied an equities intuition to a currency pair without checking the
sample. A sloppy prediction, not a surprising result.

## 2.5 Laguerre Oscillator

Article defaults gamma 0.5, Length 30, RMS 100.

| | EUR/USD D1 | BTC/USD H4 |
|---|---|---|
| mean | -0.049 | +0.078 |
| sd | 1.016 | 1.076 |
| p1 / p99 | -2.47 / +2.17 | -2.80 / +3.07 |
| min / max | -3.69 / +3.96 | -5.59 / +5.56 |

**sd near 1 is close to automatic** — divide numbers by their own typical size and you
get typical size 1. It is not a discovery about markets. What it does show is that
the 100-bar window tracks the changing scale well on both assets.

**The tails do not match.** Both have typical size ~1, but BTC reaches +/-5.6 while
EUR/USD stops near +/-3.9. So "scaled in standard deviations" transfers as a SCALE but
not as a PROBABILITY: reading +/-2 as "roughly the top 5%" holds on EUR/USD and
understates how often BTC goes further.

**Observed, not investigated:** `dev_sm` reached -0.000472 on an all-positive input.
The UltimateSmoother overshoots — Ehlers' own caveat that it is less smooth than
SuperSmoother, appearing in our data.

## 2.6 Laguerre RSI — C2 screening

**SHORTLISTED. Not locked.** Full record in `C2_Decision_Week13_LaguerreRSI.md`.

| | Result |
|---|---|
| C-1 directional state | PASS |
| C-2 mechanistic distinctness | PASS |
| C-3a correlation | **FLAG** — 0.576 / 0.562 |
| C-3b information gain | **PENDING** — decisive, needs a backtest |
| C-4 lag | PASS — 1.138 bars later than C1 |
| C-4b lag profile | PASS — leads C1, not a delayed copy |
| C-5 cross-asset | PASS — crossing ratio 1.10x |
| C-6 outlier | PASS — 12 bars faster than the reference |

Sign agreement 73.1% / 70.9%, against RMO's 84.7% when RMO was eliminated in Week 12.
Laguerre RSI disagrees with C1 on 27-29% of bars against RMO's 15% — roughly double
the potential filtering. Whether those bars are informative is exactly what C-3a
cannot measure and C-3b decides.

C-6 on the 2020-03-12 crash (-20.5% in one H4 bar, 6,037 -> 4,800): Laguerre RSI stuck
14 bars against EMA(20)'s 26.

---

# 3. Source discrepancies

Three files where code and citation disagreed. All three surfaced from checking
against the source rather than from a failing test.

## 3.1 UltimateSmoother.c does not implement its cited article

Ehlers' published filter (TASC V.42:04, 2024) is one recursion:

    c1 = (1 + c2 - c3) / 4
    US = (1-c1)*Price + (2*c1-c2)*Price[1] - (c1+c3)*Price[2] + c2*US[1] + c3*US[2]

The Week 5 file computes SuperSmoother first, then adds a residual scaled by an
invented `gamma = (1-c2-c3)/2`. Different sign, different divisor, different
structure. Not a transcription slip — a different filter.

**Measured lag, ramp steady-state at Period 20:**

    UltimateSmootherE (published)   0.0000 bars
    UltimateSmoother  (Week 5)      3.8725 bars
    SuperSmoother2Pole              4.0387 bars

Zero is exact, not approximate: the numerator and denominator group delays are
algebraically identical and cancel, for every period. Method validated against
theory — SuperSmoother's analytic DC group delay at P=20 is 4.039.

**Week 5 recorded the file as VALIDATED, "near-zero-lag".** At 3.87 against
SuperSmoother's 4.04 that claim is refuted — it is SuperSmoother with 4% less lag.
The Week 5 check used detrended cross-correlation, which GOTCHAS section 8 later
found reports 0.00 bars for an EMA with true lag 1.50. **The method could not have
detected the discrepancy.**

Both files retained: `UltimateSmootherE.c` is the published form, the original is
unchanged and still referenced by `Test_SuperSmoother.c`.

## 3.2 The 2025 TASC Laguerre code contradicts its own article text

Ehlers writes that each term is "the allpass filter delay of the previous term". An
allpass passes every frequency at unchanged amplitude, shifting only phase. The
published code uses the PREVIOUS L0 in both terms, collapsing to a lowpass:

    published:  L1 = -gama*L0[1] + L0[1] + gama*L1[1]  =  (1-gama)*L0[1] + gama*L1[1]
    allpass:    L1 = -gamma*L0[0] + L0[1] + gamma*L1[1]

Measured amplitude at gamma 0.5:

    period:      4      10     20     40     100
    published:  0.45   0.75   0.91   0.98   0.996
    allpass:    1.00   1.00   1.00   1.00   1.00

**For the oscillator the difference is exactly nil.** The allpass form gives exactly
(1+gamma) times the published form at every frequency — verified at gamma
0.2/0.5/0.8/0.95, ratios 1.200000/1.500000/1.800000/1.950000. The RMS division
cancels a constant factor. Max difference between the two oscillators: 8.9e-16.

Implemented as published. **This does not carry over to the five-term Laguerre
FILTER** in the same article, which combines four such delays with binomial weights
and no normalisation — constant factors do not cancel in a weighted sum.

The book (Fig 14.5, and our `Laguerre.c`) uses the current L0 and is a genuine
allpass. The book text states this explicitly.

## 3.3 Laguerre.c cited the wrong source, and used the wrong default

Header cited the TASC article; the code implements the book algorithm (Fig 14.5,
(H+L)/2 input, EMA-seeded L0, four stages, 1-2-2-1 weights). Corrected.

Separately, the header presented gamma 0.5 as the default. **Fig 14.5 declares
gamma(.8) for the filter**; 0.5 is the Laguerre RSI's default from Fig 14.8, a
different indicator on a later page. 0.5 is a legitimate choice but was not the
book's value for that filter. No reason for the Week 9 choice is recorded and none is
inferred.

---

# 4. Process findings

## 4.1 The asset name bug — five months of mislabelled data

`Test_FRAMA_Laguerre_DSMA.c` set `Asset = "BTC/USD"`. That symbol does not exist:
`AssetsFix.csv` names crypto without a slash (`BTCUSD`) while FX uses one
(`EUR/USD`). Zorro did not fail — it substituted the default asset and ran to
completion, writing EUR/USD data into a BTC-named file.

The May 2026 baseline is 15,063 rows: 7,534 genuine BTC followed by 7,529 appended
EUR/USD. `file_append` appends and nothing deleted the file between runs.

**`asset()` is not a usable guard.** Zorro 2.70 emits `Warning 034: <name> not in
asset list` and then runs anyway with an auto-created dummy asset, returning
non-zero. Verified with a deliberately bogus name.

Replaced with a **price-range assertion** — checking the DATA rather than the
registration. EUR/USD at ~1.12 fails a BTC bound by three orders of magnitude.
Verified to fire on exactly the Week 9 failure mode.

**`quit()` completes the current bar before stopping.** A bare `quit()` in the guard
still let one mislabelled row reach the CSV. The write is now gated behind a latch.

**Standing rule adopted: a guard that has never been seen to fire is not a guard.**
Both guards added this week were tested by deliberately breaking the input first. The
`asset()` check failed that test.

## 4.2 Library-wide state reset

Lite-C statics persist for the lifetime of the LOADED script, not the run. Editing a
source forces a recompile and zeroes them, so the usual edit-and-rerun workflow was
safe — but a repeat [Test] press, or Train->Test, was not. **Output depended on
whether a recompile happened: an invariant neither controlled nor observable from the
CSV.**

Audited all nine indicator files carrying statics. FRAMA used a value-based seed that
cannot fire on leftover state; the other seven had no seeding guard at all. All now
reset on `is(INITRUN)`.

Resets restore the DECLARED initialisers, not zero — DominantCycle's `Peak = 0.1` and
`SmoothCycle = 20` are chosen values. Only genuinely persistent state is reset:
`Mu`, `XX[]` and `Pwr[]` are write-before-read every bar and do not leak.

**Verification:** regenerated both CSVs and compared against the May baselines.
Laguerre, DSMA and RoofingFilter byte-identical across the full file. FRAMA differs on
rows 1-29 only, max 1.77e-3 absolute (2.5e-7 relative), converging by row 30 — that is
leftover EUR/USD state in the BASELINE, not in the new run. EUR/USD differs on zero
rows, because that run was the first after a compile.

## 4.3 Two amendments to the C2 criteria

Both found while applying the criteria, both registered before the data they govern.

**Amendment 3** — C-4 referenced Fisher Transform, which is Strategy 1's C1, while
governing Strategy 2. Revised to reference the C1 of the strategy whose slot is being
filled. Added C-4b, a lag profile against C1, because lag against PRICE cannot
distinguish a delayed copy of C1 from a genuine disagreement. Recorded that "at
comparable smoothing" had no procedure, and adopted variance-reduction matching as
ours rather than the document's.

**Amendment 4** — C-4b's table had no row for a LEADING candidate; it assumed a
candidate would lag its C1, and the assumption was unstated. Added the row. Also
recorded that C-4 does not predict C-4b: the sine implied Laguerre RSI would lag MESA
by 1.14 bars, market data shows it leads by 0.55-0.85. Opposite sign, because a sine
is one frequency and markets contain many.

## 4.4 Week 9's validation is not reproducible

No tracked file in the repo reads `FRAMA_Laguerre_DSMA_*.csv` — no notebook, no
script, no document. Week 9 has no notebook while Weeks 8, 10 and 11 each have one.

This does not establish that validation never happened. It does establish that three
indicators are recorded as VALIDATED with no artifact showing how. Week 14 item.

---

# 5. NNFX component mapping

| Slot | Component | Notes |
|---|---|---|
| ATR / stops | **Ultimate Channel** | Preferred over the band — no lag-20 cliff (P4) |
| Volatility measure | **NATR** | Cross-asset comparable, but thresholds do not transfer |
| Regime filter | **Volatility regime classifier** | Not an NNFX slot; a filter above the system |
| C1/C2 candidate | RSIH | Zero-centred, thresholds transfer across assets |
| C1/C2 candidate | Laguerre Oscillator | Scale transfers, probability does not |
| **Strategy 2 C2** | **Laguerre RSI** | **Shortlisted**, C-3b pending |

---

# 6. Files committed

| File | Path | Description |
|---|---|---|
| `UltimateChannelBands.c` | `indicators/ehlers/` | Channels, bands, NATR, 2x2 diagnostics |
| `VolatilityRegime.c` | `indicators/ehlers/` | Percentile-rank regime classifier |
| `RSIH.c` | `indicators/ehlers/` | Hann-windowed RSI |
| `LaguerreOsc.c` | `indicators/ehlers/` | 2025 TASC oscillator |
| `LaguerreRSI.c` | `indicators/ehlers/` | Book Fig 14.8, C2 candidate |
| `UltimateSmootherE.c` | `indicators/ehlers/` | Ehlers' published form |
| `Test_UltimateChannelBands.c` | `strategies/tests/` | Tier 1-3 export harness |
| `Test_C2_LaguerreRSI.c` | `strategies/tests/` | C2 screening export |
| `Test_LagSine.c` | `strategies/tests/` | Sine-input lag harness |
| `Test_USLag.c` | `strategies/tests/` | Ramp-input lag harness |

Documentation: `Week13_P1_P4_Results.md`, `LaguerreOsc_Notes.md`,
`UltimateSmoother_Lag_2026-08-12.md`, `C2_Decision_Week13_LaguerreRSI.md`,
`LaguerreRSI_Registered_Predictions.md`, `Week13_Plan_Amendment.md`,
`Data_Integrity_Correction_2026-08-12.md`, `Data_Availability_2026-08-12.md`,
`Swap_Cost_Modelling_Open.md`, `Week9_Validation_Not_Reproducible.md`,
`C2_Criteria_Review_and_Explanation.md`, GOTCHAS sections 9b and 9c.

---

# 7. Retrospective

## What went well

- **Registering predictions before measuring worked, including when it hurt.** Four
  of ten missed, three reversed. Each miss has a mechanism, and none was revised
  after the fact. P2's miss was predicted a day in advance from the lag measurement,
  which is the strongest form the practice takes.
- **Checking sources rather than working from memory caught three discrepancies.**
  The Laguerre RSI algorithm in particular: the assumption before reading the book
  was that it compares L0 against L3. It compares adjacent pairs. Building on the
  assumption would have produced a plausible indicator that was not Laguerre RSI.
- **Testing guards by deliberately breaking the input.** The `asset()` check looked
  correct and failed the test. The price-range assertion and the write latch both
  passed.
- **The 2x2 diagnostic.** Comparing STR to SD changes two things at once, so it
  cannot attribute the result to either. Filling the missing corners recovered P1's
  predicted range and located the miss.

## What was harder than expected

- **Two days of six were unplanned work.** The state sweep, the asset bug, and the
  data downloads all preceded any Week 13 deliverable.
- **Silent failures dominated.** `asset()` returning non-zero for an unknown symbol,
  `quit()` completing the bar, `LookBack = 0` allocating series with no history, the
  ramp method returning a constant for bounded indicators. None errored; all produced
  plausible output.
- **My own reasoning errors needed catching.** The 2x2 was under-specified until
  challenged. An intent was attributed to Ehlers he never stated. A lag prediction was
  registered against an unmeasured reference, making it unfalsifiable. Each was caught
  in review, not by a test.

## Heading into Week 14

Week 14 is consolidation, and the README is the primary deliverable. Open items:

- Week 9 validation — reconstruct or amend the status
- CSVs and `AssetsDarwinex.csv` live outside version control
- `CyberCycle.c` statics lack the `cc_` prefix (GOTCHAS 1.3)
- `DominantCycle.c` STEP 5 omits Ehlers' EMA smoothing term
- RSIH adaptive-length variant against the fixed-20 baseline
- Swap cost modelling before C-3b (`Swap_Cost_Modelling_Open.md`)
- Two-project attribution separation for the CV
