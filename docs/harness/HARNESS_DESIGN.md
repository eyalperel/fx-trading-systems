# Reusable indicator harness — design

**Status:** design agreed 2026-11-05 (user). Not built yet. D1–D3 decided 2026-11-06.
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

**D3. Exact π in the library — DECIDED 2026-11-06: keep Zorro's `PI`; no library change.**

(b) Zorro's `PI` is 3.14159 (9d.2). With D1 = (ii) the reference uses true π; the library's `PI`
gap (~6e-7 in SS2 gain) is ~170× inside tolerance. Changing it would touch ~32 files and shift
every output (~1e-6 bars of lag) for no gain in detection.
Self-monitoring: under D2 every spec records the `PI` gap in its floor. If an indicator is ever
π-sensitive enough to break the window condition, that spec must fix it.
If an exact π is ever adopted: compute it at run time (`4*atan(1)`) in a shared include, never as
a decimal literal (9d.1).

## 7. Order of work

1. [x] Decide D1–D3 (planning chat, 2026-11-06).
2. Build reference model, generator and checker; self-tests (Claude Code).
3. Tool acceptance run: reproduce H1 on SS2 (§5).
4. First article-based specs: SS2 (fidelity), SS3, HighPassFilter, RoofingFilter
   (known answer in PROJECT_STATE §5), UltimateSmootherE, Decycler — pre-registered and committed
   before the batch runs.
