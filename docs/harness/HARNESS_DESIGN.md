# Reusable indicator harness — design

**Status:** design agreed 2026-11-05 (user). D1–D3 decided 2026-11-06. **Built and accepted
2026-11-07** (§5 passed; branch `harness-step2`, stages per `docs/harness/STEP2_HANDOFF.md`).
**Builds on:** H1 (`docs/preregistration/H1_SuperSmoother2Pole_Criteria.md`, results in
`analysis/harness/results/`). H1's files stay frozen as its record.
**Implements:** PROJECT_STATE §7, Phase 1 step 3 (the rest of the library).

Labels: (a) source states · (b) measured / computed here · (c) inference.

---

## 1. Two questions a harness must answer

| Question | Meaning | Where expected values come from |
|---|---|---|
| **Implementation** | Does Zorro compute what the `.c` code says? (no float, seeding, `series()` or include bugs) | The `.c` file's own coefficients |
| **Source fidelity** | Does the `.c` code say what the article says? | The article's formula, written independently of the `.c` file |

**H1 answered the implementation question only.** Its expected values were computed from the
coefficients in `SuperSmoother2Pole.c` (b). A copying error from the article into the `.c` file
would still have passed H1.

**Decision 2026-11-05:** the reusable harness takes expected values **from the article**, so it
answers both questions. A FAIL can then mean either a Zorro problem or a copying difference; the
per-check report and the H1-style implementation cross-check (§5) separate the two.

## 2. Scope (version 1)

Linear filters only, because they share one test set (flat, sines, ramp):
SuperSmoother 2-pole and 3-pole, HighPassFilter, RoofingFilter, UltimateSmootherE, Decycler.

Bounded / rescaling oscillators (stochastics, RSI-type, Fisher) are out of scope for version 1:
the ramp method fails silently on them (gotchas 9c.2). They get a second harness family later.

## 3. Components

| Part | What it is |
|---|---|
| **Indicator spec** (one per indicator, committed = its pre-registration) | Article reference and the formula with each coefficient cited (a); literal-constant replacements (D1); periods to test; inputs; expected-value table; tolerances with floor and ceiling (D2); negative controls; pass condition |
| **Reference model** (Python) | Computes the expected values from the article formula in the spec. Never reads the `.c` file |
| **Generator** (Python) | Writes one Zorro batch script from the specs: several indicators, one [Test] click. Uses H1's proven pattern: synthetic inputs from exact run-time constants (gotchas 9d.1, 9d.2), fixed unconditional call order, raw CSV, no-overwrite |
| **Checker** (Python module) | Shared input construction, measurements (least-squares sine gain, ramp lag), guards, results format |

The generator and checker are ordinary Python, tested with their own self-tests.

## 4. Rules carried from H1 (b)

- Inputs built from integers at run time; no decimal literals, no `PI` macro (9d.1, 9d.2).
- Every run: no line starting with `Error` in the Zorro window (9d.3).
- Nothing important in EXITRUN after `quit()` (9d.4).
- Each `x[n]` reaches the filters exactly once; the input guard checks it (H1 Amendment 1, A1.3).
- Results store expected, actual and |diff| in full precision or `%.3e` (CLAUDE.md §7).
- Results files get a run suffix and are never overwritten; raw CSV copied to `*_run<k>.csv`
  with its sha256 recorded.
- Negative controls in every spec; a control that passes means the harness is broken.

## 5. Acceptance of the tool itself

Before any new indicator is judged, the reusable harness must **reproduce H1 on SS2**: run with
expected values from SS2's `.c` coefficients (H1's §4 table), all 28 checks PASS and both
negative controls FAIL as required. This is rule 5 (test the measuring tool on a known answer);
H1 is now that known answer.

## 6. Decisions

**D1. Article literal constants or their intended exact values? — DECIDED 2026-11-06: (ii).**

Evidence:
(a) Ehlers' published SuperSmoother code (TASC V.32:1, 2013; TASC V.42:04, 2024) uses `1.414`
and `3.14159`; `Cosine` takes degrees, so the `·180` form carries exact π into the cosine.
V.42:04 states the filter is translated from a maximally flat Butterworth low-pass.
(b) `SuperSmoother2Pole.c` uses `sqrt(2)` and Zorro's `PI`.
(b) Measured difference, article-literal minus code, against H1's tolerances:

| Period | Largest gain diff | Gain tol | Lag diff | Lag tol |
|---|---|---|---|---|
| 10 | 1.06e-4 | 1e-4 | 3.3e-4 | 1e-3 |
| 14 | 1.08e-4 | 1e-4 | 4.7e-4 | 1e-3 |
| 20 | 1.07e-4 | 1e-4 | 6.8e-4 | 1e-3 |
| 30 | 1.03e-4 | 1e-4 | 1.02e-3 | 1e-3 |

(b) Computed 2026-11-06 (analytic steady-state gain, test periods 5–100, filter periods 10–30):
exact √2 with `3.14159` differs from the `.c` form by ~6e-7 in gain; `1.414` with `3.14159` by
~1.1e-4. Relative errors: `1.414` vs √2 = −1.5e-4; `3.14159` vs π = −8.4e-7. Assumes the `.c`
uses `PI` inside the cosine as well (not re-read this sitting).
(c) `1.414` is √2 rounded for typing (Butterworth 2-pole uses √2).
(b) 2026-11-06, stage 1 (Claude Code read of `SuperSmoother2Pole.c` lines 3–4): `PI` is used in
both the exponent and the cosine — the assumed case. Measured article vs code gain gap: 6.185e-7.

Options considered: (i) literal constants: rejected, fails a known intended rounding and either
forces a worse `.c` or trains ignoring FAILs; (iii) literal constants with widened tolerance:
rejected, mixes the two §1 questions and lowers detection for every check.

**Literal-constant rule (applies to every spec):**
1. A literal is replaced by an exact value only if it equals a named mathematical constant to
   every printed digit (`1.414`→√2, `3.14159`→π, `.707`→1/√2, `1.732`→√3).
2. Every other number is taken literally: smoothing weights (`.04`/`.96`), length factors
   (`.5*Length`), thresholds.
3. The spec records each replacement (literal, exact value, article page) and the measured
   literal-vs-exact difference. That difference is reported as information, never as PASS/FAIL.

**D1 Amendment 1 — 2026-11-15 (source's own table overrides a mistyped literal).**
Found while sourcing SS3. (a) Ehlers, *Cybernetic Analysis for Stocks and Futures* (Wiley 2004),
ch. 13: the 3-pole Super Smoother listing (Fig. 13.11, EasyLanguage; Fig. 13.12, EFS) and the
3-pole Butterworth listing (Fig. 13.6) print the pole angle as `Cosine(1.738*180/Period)`.
Table 13.4 (p. 210) gives the 3-pole Super Smoother coefficients for P = 2–40.
(b) Max |difference| from Table 13.4 at P = 4, 10, 20, 30, 40, computing the coefficients with:
`1.738` (as printed): 4.2e-3, 1.4e-3, 4.3e-4, 2.0e-4, 1.2e-4. `1.732`: ≤ 4.1e-6 (table rounding).
√3 (exact): 3.7e-5, 1.3e-5, 3.9e-6, 2.2e-6, 8.3e-7. `1.738` vs √3 in filter gain, test periods
5–100, P = 10–30: up to 3.7e-3, ~100× the SS2 gain tolerance. So the choice decides PASS/FAIL.
(c) `1.738` is a typing error for `1.732` (√3, the Butterworth 3-pole angle factor): the book's
own table was computed with `1.732`, and `1.738` matches neither the table nor a Butterworth pole.
Rule 1 as written does not cover this (1.738 ≠ √3 to every digit); rule 2 would take it literally
and target a filter the source itself does not tabulate.

**Rule 4 (added):** a literal that fails rule 1 may be replaced only when **the same source's
own numeric table** is reproduced by a rule-1 form of a named constant (here `1.732`) within the
table's rounding, and rejects the printed literal by ≥ 10× that rounding. The replacement is then
the exact constant, as rule 1 gives it (here √3). The spec records the literal, the rule-1 form,
the exact value, the table reference and all three residuals. Without such a table, rule 2 applies.
(b) SS3: table rounding ~5e-6; `1.732` ≤ 4.1e-6; `1.738` ≥ 1.2e-4 (≥ 29×). The √3-vs-table
residual (up to 3.7e-5 at P = 4) is the table's own `1.732` rounding of √3 and is information only.
(c) Gated on the source's own numbers so it cannot become "fix any literal that looks wrong".
Applied first in the SS3 spec: `1.738` → √3.

**D2. Tolerance policy — DECIDED 2026-11-06: one library-wide rule, per-quantity tolerances.**

A tolerance must sit between a **floor** (differences already accepted) and a **ceiling** (the
smallest real bug). H1 set only the ceiling side. One library-wide number was rejected: gain,
lag, near-zero high-pass outputs and (later) oscillators have different scales.

**Tolerance rule (applies to every spec):**
1. Default per-quantity tolerances: gain 1e-4 absolute, lag 1e-3 bars absolute (from H1, b).
   A new quantity gets a default when first needed, recorded here.
2. Each spec measures and records, before the run: **floor** = largest known accepted difference
   (library-`PI` gap + implementation cross-check residual); **ceiling** = smallest effect among
   its negative controls.
3. **Window condition:** floor × 10 ≤ tolerance ≤ ceiling ÷ 10. If the default fails it, the spec
   states another tolerance with its reason, as part of the pre-registration; never after a result.
4. Negative controls include a realistic copying error (e.g. one coefficient wrong in its third
   digit), so the ceiling reflects plausible bugs, not only gross ones.

(c) The 10× margins are judgement, not derived; minimum on each side. H1's 100× ceiling margin
meets it. (b) SS2 check: floor ≈ 6e-7, gain tol 1e-4, smallest H1 bug ≈ 1e-2: inside the window.

**D2 Amendment 1 — 2026-11-06 (per-control detection).** Stage 1 negative controls (b,
P = 20): NC-A (pole factor +1 in 3rd digit) gain err 9.71e-4, lag err 2.76e-4, DC 0;
NC-B (input weight +1 in 3rd digit) gain err 2.53e-3, lag err 3.97e-6, DC err 2.5e-3.
Rule 3's ceiling side as written ("tolerance ≤ ceiling ÷ 10" for every quantity) would force the
lag tolerance to ~4e-7 to "catch" NC-B, which barely moves lag by construction. Replaced by:
- **Per-control detection:** each negative control must be caught by **at least one** check
  with error ≥ 10 × that check's tolerance.
- The floor side stays per quantity: floor × 10 ≤ tolerance.
Status: NC-A is caught by gain at 9.7× (just under 10×). The gain tolerance stays 1e-4 for now
and is set in the SS2 spec once the Zorro-side floor is measured at `%.3e` (H1 stored `%.6f`, so
Zorro's residual below 1e-6 is not yet visible). (c) Likely outcome ~2e-5.

**D2 Amendment 1, correction — 2026-11-09.** (b) The NC-B "lag err 3.97e-6" above is the analytic
group delay (`reference.ramp_lag`), not what the harness lag check measures. The check (mean
(x − y)/slope over the last 100 ramp bars) also picks up a DC-gain error:
(x − y)/s = (1 − G)·x/s + G·τ. For NC-B (G = 1.00253, x ≈ 1.395, s = 1e-4) the measured lag error is
35.3 bars (ratio 3.5e4 at tol 1e-3). Found by Claude Code in the SS2F dry run (`c5e41dc`); recorded in
`SS2_ArticleFidelity.toml` Amendment 2 (`02a6fca`). "NC-B barely moves lag by construction" holds for
group delay only. The per-control rule still stands on NC-A alone: lag 2.76e-4 = 0.28× tolerance, so
only gain can catch it.

**D2 Amendment 2 — 2026-11-09 (SS2 gain tolerance set).** `SS2_ArticleFidelity.toml` (`eaba250`) sets
gain tolerance **3e-5**, lag 1e-3. (b) Floor, Zorro vs the article table: 9.8e-7 observed vs H1's 6-dp
table + 4.66e-7 table-vs-article = 1.45e-6; ×10 = 1.45e-5 ≤ 3e-5. NC-A 9.71e-4 / 3e-5 = 32× ≥ 10×.
(c) 3e-5 sits near the geometric centre of floor..NC-A (~3.8e-5), leaning to detection. The rule-1
default (1e-4) is unchanged; each spec sets its own tolerance inside its measured window.

**D3. Exact π in the library — DECIDED 2026-11-06: keep Zorro's `PI`; no library change.**

(b) Zorro's `PI` is 3.14159 (9d.2). With D1 = (ii) the reference uses true π; the library's `PI`
gap (~6e-7 in SS2 gain) is ~170× inside tolerance. Changing it would touch ~32 files and shift
every output (~1e-6 bars of lag) for no gain in detection.
Self-monitoring: under D2 every spec records the `PI` gap in its floor. If an indicator is ever
π-sensitive enough to break the window condition, that spec must fix it.
If an exact π is ever adopted: compute it at run time (`4*atan(1)`) in a shared include, never as
a decimal literal (9d.1).

**D4 (open, 2026-11-09). Lag measurement for filters whose DC gain is not 1.** (b) The ramp-lag check
assumes DC gain = 1 (D2 Amendment 1 correction). HighPassFilter and RoofingFilter have DC gain 0 by
design; (c) on a ramp the check would report roughly level/slope, not lag. Their specs need a different
phase/lag measurement (e.g. phase at the sine test periods), decided before those specs are written.

## 7. Order of work

1. [x] Decide D1–D3 (planning chat, 2026-11-06).
2. [x] Build reference model, generator and checker; self-tests (Claude Code). Stages 1–3:
   `e03b026`, `54be500`, `7224db9`; 27/27 tests on both machines (`analysis/harness/run_tests.sh`).
3. [x] Tool acceptance run (§5), 2026-11-07, `417da02`: generated `GEN_H1_SuperSmoother2Pole.c`
   gave 28/28 PASS, NC1 + NC2 FAIL as required, no guard, no `Error` line. (b) Raw output
   byte-identical to H1 run 2 (sha256 `e8ffc043…5a6f`). (b) Observed real-check |diff| vs H1's
   6-decimal table: gain ≤ 9.8e-7, lag ≤ 5.5e-6 = the `PI` gap (D1/D3) plus table rounding.
4. First article-based specs: SS2 (fidelity), SS3, HighPassFilter, RoofingFilter
   (known answer in PROJECT_STATE §5), UltimateSmootherE, Decycler — pre-registered and committed
   before the batch runs.
   SS2 status 2026-11-09: spec pre-registered `eaba250`, Amendment 1 `b941c06`, Amendment 2 `02a6fca`;
   tooling for Amendment 1/2 `c5e41dc`, `49f7fda` (40/40 tests), branch `harness-ss2f`; **run 1 PASS 2026-11-12** (`763601e`): 28/28,
   all 4 controls detected, OX 37/37 identical to H1 raw; residual = `PI` gap (gain 5.7e-7, lag 5.4e-6).
