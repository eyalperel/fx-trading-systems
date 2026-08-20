# Strategy 2 C2 Slot — Pre-Registered Selection Criteria

**Written:** 2026-08-05, Week 12 Day 2
**Status:** REGISTERED BEFORE ANY VALIDATION DATA EXISTS
**Committed:** before implementation (Day 3) and validation (Day 4)

---

## 1. Purpose and binding status

Strategy 2 has one open slot:

| Slot | Component | Status |
|---|---|---|
| Baseline | FRAMA | Locked |
| C1 | MESA Stochastic | Locked |
| **C2** | **OPEN** | **This document governs the decision** |

Three candidates arrive in Week 12. Criteria written after inspecting validation output
would be a rationalisation of a choice already made. These are therefore registered
before implementation, and committed to a public remote so the timestamp is verifiable.

> **Binding rule.** These thresholds are not to be revised after seeing data. If a
> candidate fails, the correct response is to record the failure and evaluate
> alternatives — not to adjust the threshold. Any revision must be a separate, dated
> commit stating the justification, made *before* the data it affects is examined.

---

## 2. Candidates

| # | Candidate | Mechanism | Prior assessment |
|---|---|---|---|
| 22b | **Recursive Median Oscillator (RMO)** | Non-linear median → EMA → 2nd-order high-pass | **Primary candidate.** Only Week 12 indicator with oscillator shape. |
| 21 | Alpha-Beta Filter | Position+velocity tracker | Unlikely — outputs a price level, and leads by 1 bar (forecast, not confirmation) |
| 23 | Correlation Cycle | Autocorrelation | Unlikely — cycle-justified, subject to Principle 6 null gate |

Fallback if all three fail: **Laguerre RSI** (indicator #26, Week 13), already listed in
the indicator plan as a C2 hypothesis.

---

## 3. Criteria

All seven must pass. Ordered by decisiveness, not importance.

### C-1 — Directional signal (binary)
Produces an unambiguous directional state via zero-crossing or fixed threshold.
**Fail ⇒ eliminated.** Not a confirmation indicator by definition.

### C-2 — Mechanistic distinctness from C1 (argued, not measured)
Must differ from MESA Stochastic in filter class, not merely in parameters. Argued from
theory and stated in the library entry.
**Fail ⇒ eliminated.** Two parameterisations of one mechanism are not two confirmations.

### C-3 — Signal correlation with C1 — **DECISIVE**
Pearson |ρ| between candidate output and MESA Stochastic output, measured on **both**
EUR/USD D1 and BTC/USD H4, full available history, contemporaneous (zero lag).

| |ρ| (worse of the two assets) | Outcome |
|---|---|---|
| ≤ 0.50 | **PASS** |
| 0.50 – 0.65 | **CONDITIONAL** — permitted only if C-4/C-5/C-6 all pass cleanly and the reason for correlation is understood and documented |
| > 0.65 | **FAIL — eliminated** |

**Rationale.** NNFX combines *uncorrelated* confirmations. A C2 tracking C1 adds no
information while adding the appearance of agreement — worse than no C2 at all, because
it manufactures false confidence.

**Registered prediction (RMO): |ρ| in 0.40–0.65.** Straddles the threshold deliberately;
the outcome is not known in advance.

### C-4 — Lag
Measured by cross-correlation peak against price, both assets. Must not exceed
**Fisher Transform's measured lag + 2.0 bars** at comparable smoothing.
**Fail ⇒ conditional** — documented, permitted only if C-3 passes clearly (≤ 0.40).

### C-5 — Cross-asset stability
Identical parameters must work on EUR/USD D1 and BTC/USD H4 with no retuning. Signal
frequency (crossings per 100 bars) must not differ by more than **2×** between assets.
**Fail ⇒ conditional** — a documented per-asset parameter set is permitted but counts
against the candidate; the library standard set by HP=48/SS=10 and Fisher P=10 is
cross-asset generalisation without retuning.

### C-6 — Outlier resistance (sanity check, weak evidence)
2020-03 BTC/USD H4 crash. Candidate must not produce a signal state persisting more than
**5 bars** beyond what a plain EMA of equivalent smoothing produces.

> **Stated limitation.** This is one event, not a distribution. It cannot distinguish
> genuine outlier robustness from having handled this particular outlier. For RM the
> expected result is a pass *by construction* — the median stage guarantees it. This
> criterion therefore functions primarily as an **implementation bug-detector**: failure
> indicates the median stage is wrong, rather than that the design is unsound. It is
> recorded as weak evidence and weighted accordingly.

**Fail ⇒ investigate implementation before treating as a design failure.**

### C-7 — Mechanism survives the Week 11 null finding (Principle 7)
Justification must not depend on a market cycle existing. If the candidate is
cycle-justified, Principle 6's null gate applies and it must be surrogate-tested before
entering as C2.
**Fail ⇒ eliminated for C2**, though it may still enter the library classified as a filter.

---

## 4. Decision procedure

1. Evaluate C-1, C-2, C-7 from theory before validation. Eliminated candidates do not proceed.
2. Measure C-3, C-4, C-5, C-6 on Day 4, both assets.
3. Apply the table. Record every candidate's result, including failures.
4. If exactly one passes → **lock as Strategy 2 C2**, with the honest caveat that this is
   an indicator-level decision, provisional until Phase 3 backtesting.
5. If several pass → prefer the lowest C-3 |ρ|.
6. If none pass → **leave C2 open**, document why, defer to Laguerre RSI in Week 13. An
   empty slot is a valid outcome and is preferable to a C2 that duplicates C1.

---

## 5. Registered predictions (before data)

| Prediction | Value |
|---|---|
| RMO lag | ≈ 3.4 bars (2.0 median + 1.37 EMA at P=12) |
| RMO vs MESA Stochastic \|ρ\| | 0.40 – 0.65 |
| RMO C-6 | Pass, by construction |
| RMO AGC | **Concern** — no automatic gain control; may fail C-5 on BTC/USD H4 given ~10× regime amplitude variation |
| Alpha-Beta as C2 | Fails C-1 (outputs a price level, not an oscillator) |
| Correlation Cycle null test | Non-rejection expected (H(returns) ≈ 0.5 on both assets is close to incompatible with a recurring correlogram) |
| **Most likely overall outcome** | RMO takes the slot, with a normalisation wrapper required for crypto |

---

## 6. References

- `docs/indicators/RecursiveMedian_Theory.md` — RMO theory, Day 1
- `docs/research/Cycle_Premise_Conclusions_and_Impact.md` — Week 11 null test
- `docs/roadmap/FX_Roadmap_v2026.08.03.md` v4.3 — Phase 2 Principles 6–7
---
---

# AMENDMENT 1 — C-3 replaced by a two-stage test

**Date:** 2026-08-06, Week 12 Day 6
**Status:** REGISTERED BEFORE THE DATA IT GOVERNS. No Week 13 candidate (Laguerre RSI)
has been implemented or measured at the time of writing.
**Everything above this line is preserved unedited** — it is the criterion under which
RMO was eliminated on Day 4, and that decision stands.

## A1.1 Why C-3 is being revised

C-3 measures *correlation*. The question that matters is *conditional information gain*:
does C2 add anything beyond C1? These come apart, and the Week 12 Strategy 1 audit
demonstrates it directly.

Reflex vs Fisher, |ρ| ≈ 0.60 on both assets. Signed forward return following C1's
direction:

| Asset | C1 & C2 agree | C1 alone | C2 filter effect |
|---|---|---|---|
| EUR/USD D1 (5-bar fwd) | −5.19 bp | −12.09 bp | **+6.90 bp — adds edge** |
| BTC/USD H4 (6-bar fwd) | +6.83 bp | +21.75 bp | **−14.93 bp — destroys edge** |

**Near-identical correlation, opposite value.** Correlation cannot distinguish these
cases. A criterion that rejects on ρ alone rejects the wrong candidates and accepts the
wrong ones.

The underlying reason: 74% sign agreement leaves 26% of bars where C2 disagrees. Whether
C2 earns its slot depends entirely on whether *those* bars are informative — which ρ
does not measure.

## A1.2 The revised test

**C-3a — Correlation screen (retained, demoted to a warning)**

|ρ| between candidate and C1, both assets, contemporaneous.

| \|ρ\| | Action |
|---|---|
| ≤ 0.50 | Clean |
| 0.50 – 0.65 | Flagged — investigate and document the source of correlation |
| > 0.65 | **Flagged strongly** — high redundancy risk; C-3b must pass decisively |

**No longer eliminates on its own.** Correlation is a warning, not a verdict.

**C-3b — Conditional information gain (new, DECISIVE)**

Does C1 + C2 outperform C1 alone, out of sample, on **both** assets?

- Measured at strategy level: entry rules, transaction costs, walk-forward
- Metric: risk-adjusted return (Sharpe or equivalent) of C1+C2 vs C1 alone
- **Pass requires improvement on both assets.** Improvement on one and degradation on
  the other is a fail — that is parameter luck, not a confirmation indicator.

**This is a stricter test than C-3, not a looser one.** It would have eliminated RMO
regardless, and it places Reflex genuinely in question.

## A1.3 Consequences

**RMO (Week 12):** elimination stands. Decided under C-3 as originally written, before
this amendment. Not reopened here. If reconsidered later it must be measured fresh under
C-3b, with the original decision left standing in the record.

**Reflex (Strategy 1 C2, locked Week 11):** **FLAGGED, NOT UNLOCKED.**
- C-3a: |ρ| = 0.597 (FX) / 0.595 (BTC) → conditional band on both assets
- C-3b preliminary: **fails on BTC** (−14.93 bp)
- The preliminary figure is a crude proxy — no entry rules, no costs, arbitrary horizon,
  a single unvalidated statistic. Per the Day 3 instrument-validation rule, a rough proxy
  does not unlock a locked slot.
- **Formal C-3b resolution deferred to Phase 2.5 / Phase 3**, where the strategy-level
  machinery exists.
- Until then, Strategy 1's C2 carries an explicit open question in the README.

**Structural consequence:** C-3b is a strategy-level test. **C2 selection cannot be
completed at indicator level.** Phase 2 can screen candidates (C-1, C-2, C-3a, C-4, C-5,
C-6, C-7) and shortlist them; the decisive test belongs to Phase 3. Week 13's Laguerre
RSI is therefore evaluated as a *shortlisted candidate*, not locked.

## A1.4 Note on multi-asset validation

A proposal was raised to defer these questions to broad testing across many FX pairs.
Recorded, with the objection that motivates C-3b's both-assets requirement:

**FX majors are not independent tests.** EUR/USD, GBP/USD, AUD/USD and NZD/USD share the
USD leg, with pairwise correlations typically 0.6–0.9. Twenty pairs yield perhaps three
to five effective independent samples, while multiple-comparison inflation prices as if
there were twenty. Run enough pairs and something passes WFO and Monte Carlo on noise.

This project has already measured that effect: the Week 11 regime addendum found a
max-statistic null 95th percentile of 61.45 against a real value of 20.47.

Broad multi-pair testing remains valuable — as *confirmation* after a candidate passes on
pre-specified assets, not as a search over pairs for one that works.
---
---

# AMENDMENT 2 — C-7 withdrawn

**Date:** 2026-08-10, Week 13
**Status:** REGISTERED BEFORE THE DATA IT GOVERNS. No Week 13 C2 candidate (Laguerre RSI,
RSIH, Laguerre oscillator) has been implemented or measured at the time of writing.
**Everything above this line is preserved unedited**, including C-7 itself and Amendment 1.
**Governed by:** `docs/research/Scope_Correction_2026-08-10.md`

## A2.1 What is withdrawn

**C-7 — "Mechanism survives the Week 11 null finding" — is withdrawn.** It no longer
eliminates a candidate, conditions one, or requires a surrogate test.

Criteria are now **C-1 through C-6**. Numbering is deliberately not compacted; C-7 remains
visible above so the criterion under which Week 12 candidates were assessed stays legible.

## A2.2 Why

C-7 made a candidate's eligibility depend on whether its *source author's motivation*
survived a bounded empirical result. That result — three linear-projection mechanisms, two
assets, one parameterisation, a 10–48 bar passband — does not carry the weight of an
eligibility gate.

What matters for a confirmation indicator is whether it produces a directional signal that
adds information beyond C1. That is C-1 and C-3b. An indicator's frequency response, lag and
bandwidth are measurable properties of the filter, and they are sufficient grounds for
inclusion regardless of what phenomenon its author invoked to motivate the design.

C-7 was also partly redundant. A cycle-justified candidate that duplicates C1's mechanism is
already caught by C-2 (mechanistic distinctness) and C-3a (correlation screen) — on measured
behaviour rather than on provenance.

## A2.3 Consequences

**Decision procedure, step 1** now reads: *"Evaluate C-1 and C-2 from theory before
validation. Eliminated candidates do not proceed."*

**Correlation Cycle** is no longer excluded *a priori* as a C2 candidate. It was never
assessed on merit — Week 12 deferred it under C-7 rather than measuring it against C-3.
It becomes eligible, subject to every remaining criterion. As a normalised single-bin DFT it
is expected to correlate highly with MESA Stochastic's roofing-filtered band-pass, so C-3a
is the likely binding constraint. **That is a prediction, not a decision.** Registered here,
before measurement.

**RMO's elimination stands.** Decided under C-3 on measured correlation (|ρ| = 0.799),
not under C-7. Not reopened.

**Reflex remains FLAGGED, not unlocked.** Amendment 1's disposition is unchanged. Its C-3b
resolution still belongs to Phase 2.5/3.

**Week 12's deferral of Correlation Cycle is not retroactively reversed.** It was decided
under the criterion as written at the time. If reconsidered, it is measured fresh under
C-1–C-6, with the original deferral left standing in the record.

## A2.4 What is not weakened

C-3b — conditional information gain, decisive, requiring improvement on **both** development
assets — is unchanged and remains the binding test. Amendment 1's structural finding also
stands: **C2 selection cannot be completed at indicator level.** Phase 2 shortlists;
Phase 2.5/3 decides.

The withdrawal removes a criterion that screened on *provenance*. It does not remove any
criterion that screens on *measured behaviour*.

## A2.5 Development set extended

Criteria C-3, C-3a, C-4 and C-5 specify measurement on "both assets," meaning EUR/USD D1 and
BTC/USD H4. The development set is now four instruments: **EUR/USD D1, BTC/USD H4,
EUR/JPY D1, AUD/USD D1** (see `Scope_Correction_2026-08-10.md` §5).

Where a criterion says "both assets," read **"all development-set instruments for which data
is available at the time of measurement."** Cross-asset stability (C-5) and correlation
(C-3a) are measured on every available development instrument; the worse case governs, as
before.

> **Stated limitation.** EUR/JPY and AUD/USD are not yet set up in Zorro and were not used
> for any Week 5–12 validation. Until they are, measurements remain two-asset, and any
> criterion applied on two assets is recorded as such rather than presented as four-asset
> evidence.

---

# Amendment 3 — C-4 reference and method

**Date:** 2026-08-13, Week 13 Day 3
**Status:** Registered BEFORE Laguerre RSI is implemented or measured.
**Type:** Additive. Original C-4 text stands above, unmodified.

## A3.1 C-4 referenced the wrong strategy

C-4 as written measures the candidate's lag against **Fisher Transform's** measured
lag + 2.0 bars. Fisher is Strategy 1's C1. This document governs **Strategy 2's** C2
slot, whose C1 is MESA Stochastic.

No reason is given in the original text. (Inference, labelled as such: Fisher had a
measured lag figure available in Week 10 and MESA Stochastic may not have, making
Fisher the available reference rather than the correct one.)

The threshold also does not generalise. Five strategies are planned; "Fisher + 2.0"
is meaningless for four of them.

**Revised:** C-4 measures against the **C1 of the strategy whose slot is being
filled**, + 2.0 bars, at comparable smoothing. For Strategy 2 that is MESA
Stochastic. If that C1's lag has not been measured, it is measured first — the
reference cannot be substituted for convenience.

## A3.2 Lag against price does not answer the question C-4 asks

C-4 measures lag against **price**, then treats that number as explaining the
relationship between C1 and C2. It does not follow.

Two candidates can share the same lag-vs-price and mean opposite things:

    C1:  -0.2   +0.4   +0.6   +0.5
    X:   -0.4   -0.3   -0.1   +0.2     turns up 2 bars after C1
    Y:   -0.4   -0.3   -0.5   -0.6     never turns up

X is a delayed copy of C1 — it postpones entries without filtering anything. Y is
measuring something else and keeps disagreeing. Same lag figure, opposite value as
a confirmation indicator.

**Added — C-4b, lag profile against C1.** Cross-correlate the candidate's output
against C1's output at shifts 0 to 10 bars, both assets. Record where the
correlation peaks.

| Peak location | Reading |
|---|---|
| Shift 0, low correlation | Genuinely different quantity — the wanted case |
| Shift 0, high correlation | Duplicate of C1; C-3a already flags this |
| Shift >= 1, high correlation | **Delayed copy.** Disagreements are latency, not information |

The peak's LOCATION is the diagnostic, not a fixed cutoff. A candidate whose
correlation with C1 peaks at a non-zero shift with a high value is a lagged
duplicate: given enough bars it agrees, so it delays entries rather than filtering
them.

**Fail (high correlation at non-zero shift) => conditional**, on the same footing as
C-4. Recorded, weighted against the candidate, and C-3b must pass decisively.

This is a diagnostic, not an elimination criterion. C-3b remains the decisive test.

## A3.3 "At comparable smoothing" is undefined

C-4 requires the lag comparison to be made "at comparable smoothing" but gives no
procedure for establishing it. The intent is clear — lag and smoothness trade off,
so any indicator can be made to look fast by turning its smoothing down, and a
comparison at mismatched smoothing is not a comparison at all.

    Period 5:   lag 1.2 bars    output wiggles a lot
    Period 40:  lag 9.5 bars    output very smooth

Without a matching rule, a candidate could be set to a short period, measured at 2
bars of lag, and declared a pass against a C1 measured at 4 — while doing far less
smoothing.

**Method adopted, ours not the document's:** match variance reduction (output sd
divided by input sd), then measure lag at the matched setting. Recorded as our
choice so it is not later read as part of the original criteria.

## A3.4 What is not changed

C-1, C-2, C-3a, C-3b, C-5 and C-6 are unchanged. C-7 remains withdrawn per
Amendment 2. The C-4 numeric margin (+2.0 bars) is unchanged; only its reference
point moves.

Decisions already made under C-4 as originally written are not revisited.
