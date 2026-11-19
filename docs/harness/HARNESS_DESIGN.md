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
**Oscillator family: D6 (decided 2026-11-18), first indicator Reflex.**

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
- Every run is read twice (adopted 2026-11-17, HP runs 1-2): after the [Test] click and BEFORE the checker, the
  planning chat back-checks the raw file with its own code (models from `reference.py`, measurements written
  independently of `checker.py`) and writes a row-level prediction; then Claude Code runs the checker; the two are
  compared row by row. A disagreement is a finding to explain before the result is accepted. (b) HP run 1: both readers
  found the same single FAIL; run 2: same PASS.
- Every number a pre-run condition compares is stored at full precision in the spec (HP Amendment 1, A1.2: values kept
  as 4-digit text could only be compared at their digits).
- Corrected code starts expressions with a variable, never with a product of literals (gotchas 9d.8: such products are
  folded at compile time to an unpredictable float32).

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

**D4 - DECIDED 2026-11-16 (planning chat, user): sine phase + ramp residual; ramp lag only at DC gain 1.**

Worked example (b): first difference y = x - x[1] (DC gain 0). Ramp x = 5 + 2n gives y = 2 on every bar, so
(x - y)/s = 2.5, 3.5, 4.5, ... grows by 1 per bar: the ramp-lag check measures position on the ramp, not lag.
Sine T = 4 (x = sin(pi*n/2)): the least-squares fit y = a*sin + b*cos gives a = b = 1, gain sqrt(2), phase
pi/4 rad, delay = -phase/omega = -0.5 bars (the output leads). Matches H(e^jw) = 1 - e^-jw = 1 + j at w = pi/2.
(b) Found while reading `checker.py`: `m_flat` also assumes DC gain 1 (it measures |y - level|).

Rules (apply to every spec from HighPassFilter on):
1. **Ramp lag** (existing check): only when the spec's reference DC gain = 1.
2. **Flat:** expected output = reference DC gain x level (0 for DC gain 0). `m_flat` is generalised accordingly.
3. **Sine phase** (new quantity): phase = atan2 of the existing least-squares fit (sin, cos, constant columns,
   `checker.m_gain`), compared with arg H(e^jw) from the reference model; the difference is wrapped to (-pi, pi];
   tolerance in **radians**; checked only at test periods where the reference gain >= a gate the spec
   pre-registers (phase is undefined at gain 0, e.g. RoofingFilter at T = 2).
4. **Ramp residual** (specs with DC gain 0): steady-state output on the ramp vs the reference model's value
   (-s * sum k*h_k; 0 when the numerator has a double zero at DC). A known-answer check, not a lag.
5. The phase tolerance default is set in the first spec that uses it (HighPassFilter) from its measured floor
   and recorded here (D2 rule 1). D2 per-control detection (Amendment 1) is unchanged.

Why radians (b): a phase error d_phi is d_phi * T/(2*pi) bars, so one tolerance in bars would be loose at long
periods and strict at short ones. Rejected: group delay from phases at two nearby periods (differences two noisy
estimates; a high-pass has no meaningful group delay near DC); gain only (a pole-angle error barely moves gain,
and timing is what the NNFX slots depend on).
Sourcing note (a)/(b), 2026-11-16: Ehlers published three different high-pass filters: 2-pole with `.707`
(TASC V.32:1 2014; also V.33:09, V.36:03), 1-pole (V.34:09 2016), 2-pole Butterworth-type with zero start-up
(V.42:04 2024). `HighPassFilter.c` implements the first (read 2026-11-16); details in the HighPassFilter spec.

**D4 rule 5 applied, 2026-11-17 (HP_ArticleFidelity, 2069d86).** Defaults recorded under D2 rule 1:
**phase 3e-5 rad** (HP floor 8.1e-7 = the `PI` gap; NCA 37x), **ramp residual 1e-9** (floor 2.8e-16), **start-up 1e-6**
(floor 1.2e-9). Phase gate 0.05 (judgement (c); binds first in RoofingFilter, gain 0 at T = 2: (b) RFF run 1, alt phase
SKIP in all 11 variants; a period-2 sine is impossible, sin(pi*n) = 0, so T = 2 uses an alternating input). Each later spec checks
them against its own measured window (D2 rule 3) and states another value with its reason if the window requires it.

**D5 - DECIDED 2026-11-17: how an amendment changes a pre-registered value.** The pre-registered text is never edited.
A dated amendment adds a correction section that the tooling applies on a copy and reports as an INFO line in the
results header: `[effect_corrections.<id>]` (SS2 Amendment 2, tooling 49f7fda) and `[imp_corrections.<id>]` (HP
Amendment 2, tooling edfa8d5). An `[imp_corrections]` entry must name its list (`must_pass` | `must_fail`), quote the
model it `replaces` verbatim (validation refuses a mismatch), name a registered model, its amendment and a labelled
source. Rejected: editing in place (breaks the record), a checker-side override outside the spec (criterion not
traceable to the pre-registration), a new spec for a one-model change (re-runs everything for nothing).
(b) First use: HP run 1 FAILED one row because the NCH model did not know Zorro's compile-time fold of `0.707*2.0*PI`
(gotchas 9d.8). The fold was measured by a probe (ba54022), the model corrected by Amendment 2 (e29febd), and run 2
(same script, byte-identical raw) PASSED (512781c). Run 1 stays recorded as FAIL. The planning chat had first fitted
the value from run 1's data; the probe measured it independently; disclosed in the amendment.

**D6 - DECIDED 2026-11-18 (planning chat, user): check set for the oscillator family (normalised / bounded outputs).**
First indicator: Reflex (TASC V.38:02; source review `docs/harness/REFLEX_SOURCE_REVIEW.md`, `05be788`). Order within the
family: Reflex, then MESAStochastic (C1).

Evidence (b), planning chat, independent float64 model of the article Reflex (L = 20; inputs as SS2F: level 1.1, sine
amplitude 0.01, ramp slope 1e-4; 3000 bars; price seed):
- Reflex = Sum/sqrt(MS) is scale-invariant, so it also normalises rounding noise. On the ramp, Sum falls to ~3e-17 by row
  200 while sqrt(MS) keeps decaying (1.3e-10 at row 700, 1.4e-16 at row 1500): **the article model itself** gives
  max |Reflex| = 2.86 over rows >= 700 (-1.39 at row 1500). "Flat -> 0, ramp -> 0" is not a valid known answer for the
  normalised output. Flat gave exactly 0 here only because every bar rounds identically (c: not to be relied on in Zorro).
- Sines are well conditioned: max |Reflex| over rows >= 700 is 1.397 (T = 20) / 1.400 (T = 40), near sqrt(2) for a pure sine.
- Zorro `PI` gap (float32(3.14159) vs pi) on Reflex, max |diff| over rows >= 700, sines T = 5/10/20/40/100: <= 1.6e-6
  for L = 14/20/21/30 (largest 1.57e-6, L = 20, T = 10).
- Start-up memory: MS decays as 0.96^n, below 1e-12 after ln(1e-12)/ln(0.96) = 676.87 bars.

Rules (apply to every oscillator spec; each spec states how they map to its indicator):
1. **Expose the linear stage.** Where the indicator has a linear front end, the corrected code exports it through a
   core function with out-parameters (Reflex: `ReflexCore(Price, Length, &sum, &ms)`; `Reflex(Price, Length)` is a thin
   wrapper, so callers do not change). The linear stage gets the existing v1 checks unchanged (flat, gains, phases,
   alternating input, ramp residual; D4). (b) Reflex Sum = FIR on Filt with weights (L-1)/(2L) at lags 0 and L, -1/L at
   lags 1..L-1: DC gain 0 and a double zero at DC (ramp residual 0).
2. **Trace replay (new quantity).** The normalised output is compared row by row with the article model, rows >= W
   (W pre-registered, >= the start-up memory of every state, e.g. 677 for Reflex), on well-conditioned inputs only
   (sines). A conditioning gate, pre-registered per spec (Reflex: sqrt(MS) / input amplitude >= g), excludes rows where
   the denominator is near zero; gated rows are counted and reported. Flat and ramp rows of the normalised output are
   INFO, never PASS/FAIL. Tolerance per D2 (floor = `PI` gap + IMP residual).
3. **Structural bound.** Every row of every input satisfies the indicator's exact bound (Reflex: MS >= 0.04 Sum^2, so
   |Reflex| <= 5). No model needed; it also covers the ill-conditioned rows.
4. **Invariance.** The same sine scaled (x k) and offset (other level) must give the same normalised output within
   tolerance (Zorro-internal comparison, no model). Catches a missing / wrong normalisation and DC leakage. Needs extra
   input copies in the generator.
5. **Multiple instances.** Several instances run every bar in the standard layout; a shared-state control (Reflex: the
   superseded `static rx_MS` body, called as two instances) must fail trace replay.
6. **Start-up** where the source states no rule: INFO only (Reflex R-4).
D2 per-control detection (Amendment 1) and the D5 amendment mechanism are unchanged.

Rejected: trace replay on every input (fails on rounding noise, finding above); checking only the normalised output
without exporting the linear stage (linear-stage fidelity hidden inside a nonlinear comparison; floor harder to read).
(c) MESAStochastic reuses rules 2-4 and adds a gate on its min/max range (HH - LL).

**D6 defaults recorded under D2 rule 1 (2026-11-18, RFX_ArticleFidelity spec).** New quantities, first set in the Reflex spec:
**trace 3e-5** (absolute, normalised output; Reflex floor 1.57e-6 = the `PI` gap, floor x10 = 1.57e-5: inside the window but
with only ~1.9x margin, the thinnest so far; floor guard tol/10 = 3e-6), **bound: relative allowance 1e-12** on the exact bound
(Reflex |r| <= 5, attained on the first non-zero Sum row), **invariance 1e-9** (float64 floor ~1.2e-12 to 2.2e-12), **trace gate
g = 0.01** (judgement (c); smallest margin on a correct variant 0.037, L14), **W = 700** (Reflex MS memory). The gate is evaluated
on the MODEL's MS, never on the run's, so a broken variant cannot gate away its own rows; a sine with every row gated is an ERROR.
(b) Back-check of the spec draft (planning chat, independent code): NCS / NCT effects with ONE static MS shared by all 16 calls per
bar (8 inputs x 2 instances, variant-major) reproduced 1.347901 / 1.878025, the same for three input orders; the old float32 weights
give |r| = 1/sqrt(float32(0.04)) = 5.000000055879 on the first superseded call, so the bound check also fires on NCS (not required).

**Open items (2026-11-17).**
- The `L_FLOAT32` exemption INFO line appears in lint output and pre-run records but not in the results header; the
  run record should carry every pre-registered exception (small tooling task).
- Intermittent test errors: `test_checker_amend1.test_cli` MemoryError twice in Claude Code's shell; once 4/144
  ERRORs in the user's Git Bash, cause not captured (CLAUDE.md §8 now requires tracebacks and a rerun).
- Cascade seeds (RFF Amendment 2, A2.2): the checker applies a variant's declared `seed = "price"` to a cascaded model as
  ONE filter with output history = x[0], a start state no code has (b: NCO must_fail measured 1.9138e-2; per-stage price
  seeding gives 9.07e-5; zero seeds 1.10 = the pre-registered value). Verdict unaffected (row needs > 1e-9). Fix before a
  cascade must_pass row depends on a non-zero seed: declare seeds per stage.

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
   SS3 status 2026-11-16: source = Cybernetic Analysis Fig. 13.11; D1 Amendment 1 (rule 4) `9789fb5`; spec + tooling
   (ss3 reference models, IMP replay check, floor guard; 57/57 tests) `867f952`; existing `.c` found to be a hybrid,
   corrected `.c` + hybrid kept as `SuperSmoother3Pole_Hybrid_Superseded.c` `172fb4e`; Amendment 1 (pre-run records)
   `a1dbce5` (65/65 tests); **run 1 PASS 2026-11-16** (`09c05ad`): 28/28, all 6 controls detected (incl. NCH = the
   real hybrid, NCL = the book as printed), IMP <= 3.4e-14 (fire test 4.1e-3), Zorro vs book = `PI` gap (gain 9.0e-7,
   lag 7.7e-6); 10 variants. First spec to answer both §1 questions in one run (IMP replaces an H1-style run).
   HP status 2026-11-17: D4 decided `032d766`; tooling `14395a0`, `a2999c4`, `f2e80c2`; spec `2069d86` (HP-A, TASC
   V.32:1; corrections D-1 `0.707` -> sqrt(2)/2 and D-2 zero seed; 56 real checks, 8 controls, IMP own-model replay for
   all 12 variants); corrected `.c` `d22ef57`; Amendment 1 `c998bf8`. **Run 1 FAIL** (`a361e4b`): item 6 only, NCH
   own-model replay 2.24e-7 (Zorro literal fold, probe `ba54022`). Amendment 2 `e29febd` (tooling `edfa8d5`,
   `3434866`). **Run 2 PASS** (`512781c`): 56/56, 8/8 controls, 14/14 IMP (<= 1.3e-11 except fire rows), 16/16 floor;
   Zorro vs article = `PI` gap (gain 4.0e-7, phase 8.1e-7 rad). 24 variant-runs (12 x 2) on one byte-identical raw file.
   RFF status 2026-11-17: source TASC V.32:1 Roofing sidebar; code structure already matched (only GAP-1.31 header and local
   renames, `b249142`). Tooling `f9f3561` (params list, include list, alternating input, gated alt phase SKIP, cascade models);
   spec `b6b5c5d` (4 real x 16 checks, 7 controls incl. NCO = the pre-HP-fix pipeline; planning-chat back-check of tables,
   floors, effects agreed <= 2e-9 rel.); Amendment 1 + script `a7b7262`. **Run 1 PASS** (`d1395d3`): 64/64, 7/7 controls, 13/13 IMP
   (must_pass <= 3.5e-12), 16/16 floor, 11 alt-phase SKIP; Zorro vs article = `PI` gap (gain 5.6e-7, phase 1.6e-6 rad).
   Amendment 2: post-run record (cascade-seed note, open items; `1.0/1000` residual INFO, gotchas 9d.8).
   USE status 2026-11-18: source TASC V.42:04 UltimateSmoother sidebar; DC gain 1, so D4 rule 1 (ramp lag, expected 0 exactly:
   the HP numerator has a double zero at DC). Two deviations: D-1 folded `1.414 * PI` (9d.8), D-2 global `Bar < 4` start-up. Tooling
   `baa74a9` (seed mode `pass<n>`, `one_minus`, `us_article`, role `info`); spec `ca4454b` (4 real x 16, 6 controls + NCL info; NCL at
   3.6x / 4.8x could not meet the 10x rule and is information only under D1 rule 3); corrected .c + test `ad8eae5`; Amendment 1 +
   script `1aa5d21`. **Run 1 PASS** (`41c8d76`): 64/64, 6/6 controls, 13/13 IMP (must_pass <= 8.0e-15), 16/16 floor, 11 alt-phase
   SKIP; Zorro vs article = `PI` gap (gain 6.5e-7, phase 7.6e-7 rad). (b) The ramp check is structural only for this family: no
   control moved DC gain or ramp lag; detection came from gain, phase, alt gain and start-up. (b) A 3- vs 4-bar seed is invisible on
   flat and ramp; only a sine start-up sees it. Amendment 2: post-run record.
   RFX status 2026-11-18 (first oscillator spec, D6): source TASC V.38:02 Reflex sidebar; review `05be788` (R-1 shared static MS, R-2
   int half length, R-3 float32 weights, R-4 no start-up rule, R-5 header); D6 `5087c39`; tooling `853dc20` (multi-output calls,
   trace / bound / invariance, shared-state replay); spec `960ae09` (4 real x 21 checks, 8 controls incl. the real superseded file as
   NCS/NCT, NCL info); corrected .c + superseded control + test `5840f20`; generator out-parameters via local scalars `62b4e97`
   (A1.2); Amendment 1 + script `353c94f`. Prediction committed before the checker `901b3a0`. **Run 1 PASS** (`ad487b7`): 84/84,
   8/8 controls (76 FAIL rows, as predicted row by row), IMP 13/13 must_pass (<= 2.8e-12) + 2/2 must_fail, floor 20/20 (tightest
   trace 1.570e-6 <= 3e-6, = the pre-run `PI` gap), 0 gated rows, 11 alt-phase SKIP. (b) NCK (Sum divisor) was seen only by the Sum
   gain checks (trace at the floor): D6 rule 1 confirmed in a run. (b) The old float32 weights showed up only as NCS's bound row
   (5.000000055879), not in trace. (b) Raw values are `%.15f` (absolute resolution 1e-15): adequate here; a quantity near 1e-14 would
   need `%.17g`. Amendment 2: post-run record.
