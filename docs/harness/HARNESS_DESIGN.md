# Reusable indicator harness — design

**Status:** design agreed 2026-11-05 (user). Not built yet.
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
| **Indicator spec** (one per indicator, committed = its pre-registration) | Article reference and the formula with each coefficient cited (a); periods to test; inputs; expected-value table; tolerances; negative controls; pass condition |
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

## 6. Open decisions — settle before the first article-based spec is written

**D1. Article literal constants or their intended exact values?**
(a) Ehlers' published SuperSmoother code (TASC V.32:1, 2013; TASC V.42:04, 2024) uses `1.414`
and `3.14159`. (b) `SuperSmoother2Pole.c` uses `sqrt(2)` and Zorro's `PI`.
(b) Measured difference, article-literal minus code, against H1's tolerances:

| Period | Largest gain diff | Gain tol | Lag diff | Lag tol |
|---|---|---|---|---|
| 10 | 1.06e-4 | 1e-4 | 3.3e-4 | 1e-3 |
| 14 | 1.08e-4 | 1e-4 | 4.7e-4 | 1e-3 |
| 20 | 1.07e-4 | 1e-4 | 6.8e-4 | 1e-3 |
| 30 | 1.03e-4 | 1e-4 | 1.02e-3 | 1e-3 |

With article-literal expected values, SS2 would fail 4–5 checks narrowly.
(c) `1.414` is very likely √2 rounded for EasyLanguage (the article describes a Butterworth
design, which uses √2). Options: (i) literal constants, (ii) intended exact values with the
rounding documented, (iii) literal constants with a tolerance that admits the rounding. The
choice is a method rule for all indicators, not a per-indicator fix.

**D2. Tolerance policy.** H1's tolerances (gain 1e-4, lag 1e-3) were set ~100x tighter than the
smallest bug seen in its negative controls. Keep that rule per spec, or set one library-wide
tolerance?

**D3. Exact π in the library.** Zorro's `PI` is 3.14159 (9d.2). Defining an exact π for the
indicator files changes every indicator's output slightly (~1e-6 bars of lag). Deferred; decide
together with D1.

## 7. Order of work (proposed)

1. Decide D1–D3 (planning chat).
2. Build reference model, generator and checker; self-tests (Claude Code).
3. Tool acceptance run: reproduce H1 on SS2 (§5).
4. First article-based specs: SS2 (fidelity), SS3, HighPassFilter, RoofingFilter
   (known answer in PROJECT_STATE §5), UltimateSmootherE, Decycler — pre-registered and committed
   before the batch runs.
