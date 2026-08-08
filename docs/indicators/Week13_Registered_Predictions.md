# Week 13 — Registered Predictions

**Registered:** 2026-08-08, Week 13 Day 1
**Status:** Written before any Week 13 implementation, backtest, or data inspection.
**Governing rules:** Predictions are registered before implementation. Values are not
revised after seeing data. Any amendment must be dated, additive, and made before the
data it governs (see `C2_Selection_Criteria_PreRegistered.md`, Amendment 1).

**Scope:** Ultimate Channels & Ultimate Bands (Ehlers, TASC V.42:05, 2024).
Tests the article's claim that the band indicator "does not differ from the channel
indicator in any major fashion."

**Fixed parameters for all predictions below:**
`Length = 20`, `STRLength = 20`, `NumSTRs = 1`, `NumSDs = 1` — the article's own settings.

**Assets:** EUR/USD D1 (2015–2024), BTC/USD H4 (2020–2024). Identical parameters, no retuning.

---

### P1 — Correlation between channel width and band width
Parameters: Length = STRLength = 20, NumSTRs = NumSDs = 1

Predicted:
  EUR/USD D1   corr(channel_width, band_width) = 0.85 – 0.90
  BTC/USD H4   corr(channel_width, band_width) = 0.60 – 0.70
  Direction:   BTC strictly lower

Reasoning: BTC's largest bars are much bigger relative to its own ordinary bars than EUR/USD's are. Because the band width squares each deviation while the channel width does not, those outsized bars push the band width up far harder than the channel width — so the two measurements disagree more often on BTC, giving a lower correlation. Note that BTC's higher raw volatility level alone does not predict this, since correlation is unaffected by scale.

Registered: Week 13 Day 1, before any implementation or data.

### P2 — Median ratio of channel width to band width
Parameters: Length = STRLength = 20, NumSTRs = NumSDs = 1

Metric: median over all bars of ( channel_width / band_width )
        where channel_width = STR, band_width = SD

Theoretical baseline: ≈ 1.6
  For a well-behaved random walk, expected bar range ≈ 1.596·sigma while SD ≈ sigma.
  This is the value expected if neither of the mechanisms below operates.

Predicted:
  EUR/USD D1   median ratio = 1.2 – 1.3
  BTC/USD H4   median ratio = 0.9 – 1.1
  Direction:   both strictly below 1.6; BTC strictly below EUR/USD

Reasoning: Two mechanisms inflate the band width (the denominator) while leaving the
channel width untouched, so both push the ratio below its 1.6 baseline.
  (a) Trend lag: the band's width is RMS deviation of Close from the LAGGING centre
      line, not from a mean. In sustained directional moves the centre trails price,
      so deviations are large and one-signed, and the band widens with no change in
      actual volatility. The channel's STR is bar-local and never references the
      centre, so it is unaffected.
  (b) Fat tails: the band squares each deviation while the channel does not, so
      outsized bars inflate the band width far more than the channel width.
Both mechanisms bite harder on BTC — its large bars are much bigger relative to its
own ordinary bars, and it lacks EUR/USD's tendency to oscillate around a level, so
price sits away from the centre line for longer stretches.

Known risk to this prediction: the median is dominated by ORDINARY bars, and on a bar
that is neither a shock nor part of a sustained move, both mechanisms are dormant and
the ratio should sit near 1.6. If inflated bars are too rare to move the middle of the
distribution, both predictions will come in too low. The BTC range was widened from an
initial 0.8–0.9 to 0.9–1.1 to straddle 1.0, so the result adjudicates whether the band
is genuinely wider than the channel on crypto.

Registered: Week 13 Day 1, before any implementation or data.

### P3 — Isolating the trend-lag effect (conditional split)
Parameters: Length = STRLength = 20, NumSTRs = NumSDs = 1

PURPOSE
P1 and P2 measure the COMBINED effect of trend lag and fat tails, so neither can
attribute a result to one mechanism. P3 isolates trend lag using a conditional split
with the channel width as a control.

SPLIT DEFINITION (fixed before data)
  trend_score = |Close − FRAMA| / STR
  Split at the MEDIAN of trend_score, computed per asset:
     above median -> trending bucket
     below median -> flat bucket

  FRAMA is used deliberately instead of the band's own centre line. Defining the split
  from |Close − Smooth| would be CIRCULAR: the band width is a rolling average of that
  exact quantity, so the band would be guaranteed wider in the trending bucket by
  arithmetic identity rather than by market behaviour. FRAMA (Week 9, validated) shares
  no term with the band width.

  Median split rather than a fixed threshold: guarantees a 50/50 bucket split on both
  assets, so cross-asset comparison is like-for-like and no threshold is tuned by hand.

METRICS (four per asset)
  B_trend / B_flat  = band width inflation in the trending bucket
  C_trend / C_flat  = channel width inflation  <- CONTROL

  The control absorbs the fact that trending bars tend to be larger bars. The GAP
  between the two ratios is the trend-lag signature: the band widening for a reason
  unrelated to volatility.

PREDICTED
  EUR/USD D1    B_trend / B_flat = 1.6 – 1.8
                C_trend / C_flat = 1.1 – 1.2
                gap              ≈ 0.5 – 0.6

  BTC/USD H4    gap strictly LARGER than EUR/USD's

  Decisive comparison: gap(BTC) > gap(EUR/USD)

REASONING
The channel width (STR) is bar-local and never references any centre line, so it cannot
detect the trend state directly; it rises in the trending bucket only because those bars
are modestly larger. The band width is built from (Close − Smooth)^2, deviation from a
LAGGING centre, so in the trending bucket it inherits the larger-bar effect AND gains a
second push from persistent one-signed deviation. BTC should show the larger gap because
it lacks EUR/USD's tendency to oscillate around a level, so price remains away from the
centre line for longer consecutive stretches and the smoother lags harder.

KNOWN LIMITATIONS
1. Fat tails contaminate the control. Large BTC bars lift C_trend as well as B_trend,
   which NARROWS the measured gap even if the underlying lag effect is unchanged. This
   biases against the BTC prediction, so a confirmed result is conservative and a
   refuted one is ambiguous.
2. trend_score divides by STR, so high-STR bars are biased toward the flat bucket. This
   affects which bars land where but does not share a term with the band width, so the
   band-side comparison remains clean.

COHERENCE NOTE
P1, P2 and P3 all rest on the same claim: BTC decouples the two width estimators more
than EUR/USD does. A BTC gap SMALLER than EUR/USD's would contradict the reasoning
behind all three predictions simultaneously, not just this one.

Registered: Week 13 Day 1, before any implementation or data.

### P4 — Boxcar echo in band width (implementation verification)
Parameters: Length = STRLength = 20, NumSTRs = NumSDs = 1

PURPOSE
Tests filter STRUCTURE rather than market behaviour. The article states that "both
averages are replaced with UltimateSmoothers." This is true of the CHANNEL, but in
the BAND only the centre line is smoothed — the width estimator remains a rectangular
FIR window (the For count = 0 to Length-1 loop). The two widths therefore belong to
different filter classes:

  STR = UltimateSmoother(TH − TL, 20)     recursive IIR, smooth decay
  SD  = sqrt( mean over exactly 20 bars ) rectangular FIR, hard cutoff

A volatility shock enters the SD window at full weight, remains at full weight for 20
bars, then drops out DISCONTINUOUSLY. That cliff is an artifact of window shape, not a
market event. STR has no equivalent — old data fades gradually and never leaves abruptly.

METRIC
  Autocorrelation of the first difference of band_width; inspect lag ≈ 20.
  Same computation on channel_width as CONTROL — no structure expected at lag 20.

PREDICTED
  Band width    shows detectable structure at lag ≈ 20 on BOTH assets
  Channel width shows NO such structure on either asset
  Visibility    STRONGER on EUR/USD D1 than on BTC/USD H4

REASONING
The lag-20 structure is close to arithmetically forced: a boxcar window of length 20
must leave a footprint at its own length. Visibility differs by asset because an echo
is a discrete event against a quiet baseline. EUR/USD produces isolated shocks with
relatively calm bars following, so each cliff is separable. BTC produces frequent,
overlapping shocks — a new one arrives before the previous has aged out of the window —
so successive cliffs superimpose and smear into the background.

Note this is the ONLY prediction in this set where EUR/USD shows the stronger effect.
P1–P3 all predict BTC as the more extreme asset; P4 tests a different property and
correctly reverses direction.

STATUS: VERIFICATION, NOT DISCOVERY
Because the result is near-forced by the arithmetic, absence of lag-20 structure in
band width indicates an IMPLEMENTATION ERROR, not a refutation of the mechanism.
Treat a null result here as a signal to audit the code before interpreting P1–P3.

PRACTICAL CONSEQUENCE
If the band is used for stop placement, the cliff causes the stop to jump inward
approximately 20 bars after a volatility event, unconnected to current conditions.
This is relevant to the Week 13 ATR/stops slot and should be recorded in the library
entry regardless of P1–P3 outcomes.

Registered: Week 13 Day 1, before any implementation or data.