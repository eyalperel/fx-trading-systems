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