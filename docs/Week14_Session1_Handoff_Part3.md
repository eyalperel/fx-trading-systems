# Week 14 — Session 1 Handoff (part 3)

**Date:** 2026-09-10
**Covered:** family status-table rewrite, HighPass (full recall → probe → read →
gap check → fix cycle)
**Not covered:** RoofingFilter, Decycler
**Repo:** `4a67e83` → `ec12066`, pushed to origin/main

Read parts 1 and 2 first (`docs/Week14_Session1_Handoff.md`,
`docs/Week14_Session1_Handoff_Part2.md`). This continues part 2's section 7.

> **Numbering.** Part 1 is headed "part 1 of 2" and part 2 "part 2 of 3". Both
> totals were wrong when written. This file carries no total.

---

## 1. Order changed at the start of the sitting

The scope list ran the status-table rewrite first. It was moved to the end, for
three reasons: the rewrite covers `UltimateSmootherE`, whose row depends on what
the high-pass does on non-straight-line input (GAP-1.16), so writing it first
would repeat the move that deferred it twice already; plan §2.1 puts fixes at the
end of a session and the rewrite is a fix; and recall is the expensive work and
belongs at the start.

It paid. Two of the rewrite's changes (GAP-1.26 seeding, the Key Finding 5
addendum on damping) came out of the HighPass review and would not have existed
in a rewrite done first.

## 2. What reconstructed cleanly

- **What a high-pass does.** "Attenuates slow, passes fast" — correct on first
  statement, unprompted.
- **The design use.** `Price − HighPass(Price)` recalled without prompting,
  including that it is the route to smoothing with less lag than a moving
  average. This is the design derived unaided in part 2, retained.
- **Sign handling under a flip.** After the tent, the valley case was answered
  correctly on all three parts — sign of the second difference, direction of the
  US offset, and which direction the filter resists — with no worked example.
- **Feedback structure.** Given the numerator was feeding zeros, correctly
  predicted the output would not snap back, and wrote the recursion in the right
  shape from memory.
- **Extending a sequence.** Continued the ring sequence three bars past what was
  asked, which is what surfaced its sign flips.
- **Discriminant work.** Computed correctly three times, including on the broken
  filter, and correctly read complex roots as oscillation.

## 3. What did not reconstruct

- **"Passes noise" as the framing.** The opening answer described the high-pass
  as passing noise. It responds to **curvature**; noise passes because jitter
  bends the series constantly, not because the filter identifies noise. A clean
  noiseless turn passes just as readily. Corrected in session via the tent.
- **The repeated-root case.** Discriminant = 0 was not a case previously met.
  Reconstructed via the quadratic formula rather than supplied.
- **Decay shape.** Predicted exponential decay for the feedback tail. Correct for
  real poles, wrong for complex ones — the teaching example rang. The general
  principle (real → fade, complex → ring) was new material.

## 4. Findings

### 4.1 The filter is correct; nothing that claims to have checked it is

`HighPassFilter.c` is a sound implementation. Its coefficients were verified
against the header's own reference (HPPeriod=30 → alpha1 = 0.138102, recomputed
to six significant figures). Its feedback polynomial is `(z − b)²` with
`b = 1 − alpha1`, so the discriminant is zero at every HPPeriod: a repeated real
pole, **critically damped by construction, no ringing**.

Everything offered as evidence for it is not:

- `Test_HighPass.c` has **no pass criterion** — it computes the indicator and
  appends to a CSV. It cannot fail (GAP-1.19).
- The notebook's four criteria cannot fail (GAP-1.22, GAP-1.23).
- The cross-asset verdict is a **hardcoded string** with typed-literal figures
  beneath it (GAP-1.25).
- The `.c` header's "Validated: EUR/USD D1, BTC/USD H4" rests on the above.

**These are separate facts and the second does not impugn the first.**

### 4.2 A one-factor typo changes the filter completely

Dropping one `(1 − alpha1)` gives `z² − 1.8z + 0.9` at b=0.9, discriminant
**−0.36**, complex poles, a **ringing** filter. Critically damped and ringing are
entirely different behaviours — and on real price **both look like a squiggle
around zero**. Market-data validation is structurally blind to the difference.
A tent (11 bars, one kink, no data) separates them immediately, as does computing
the discriminant.

This is the same shape as part 1 §4.1: a check that runs on messy input, where
messy output is expected either way.

### 4.3 Settling and superposition

At HPPeriod=48: alpha1 = 0.088513, b = 0.911487.

| residue | bars |
|---|---|
| 10% | 24.8 |
| **1%** | **49.7** |
| 0.1% | 74.5 |

~25 bars per decade. Rule of thumb at two periods (48 → 49.7, 20 → 20.6):
**1% settling ≈ HPPeriod**. Two points, not a proof.

The filter is linear, so by **superposition** its output is exactly the sum of
the responses to every past bend. With bends arriving every few bars and ~50-bar
memory, any single output value is an accumulation and cannot be read as a
statement about current conditions.

**This is the substance behind GAP-1.16.** `UltimateSmootherE` measured 0.0000
bars on a ramp because a ramp has no bends — the high-pass contributes nothing
and the subtraction is a no-op. Zero lag was measured in the one regime where the
mechanism is switched off. The carry-forward question from part 2 is answered at
the mechanism level; the quantitative question (how much lag on a curve) remains
open and needs a measurement.

### 4.4 One root cause behind four reproducibility findings

`.gitignore` excludes `data/` deliberately, reason given as size. Consequently
every market-data validation in the library depends on files a fresh clone cannot
obtain. `Test_HighPass.c` writes to `Data/` in the Zorro install directory; the
notebook reads `<repo>/data/fx/`; **no tracked file records the copy step between
them.**

Week 5, Week 9, `Test_USLag.c` and Week 6 are not four defects. They are one
policy decision with four symptoms. Resolved by **D-14.1** below.

### 4.5 One scalar standing in for a trade-off — instances 6 and 7

Part 1 logged three, part 2 two more. Added here:

- HP mean used as a correctness gate, where the quantity is driven to zero by N
- MAD from price used as a lag measure, where the optimum is the identity filter

**Seven instances across three sittings.** This remains the review's principal
recurring finding.

### 4.6 One working instance of backward propagation exists

`HighPass_RoofingFilter_Notes.md` §7 carries a dated correction marker that
states what the line previously said and names where the original bug came from.
It is the only instance in the review of a correction reaching the document that
made the original claim. **GAP-1.15 asks for a mechanism that does this
routinely; this is the template.** Note it did not reach §3's formula block four
sections above, which kept the wrong form until today.

## 5. Decision taken

### D-14.1 — Validation data policy

Supersedes the open decision carried in part 1 §8 and part 2 §7.

**The split.** Validation answers two questions and they get different
instruments:

- **Correctness** — synthetic inputs generated inside the test file (ramp, tent,
  step, sine). No market data. Analytically known answers, bit-identical from any
  clone, zero storage.
- **Behaviour** — three small committed EUR/USD D1 slices, ~250 bars each,
  chosen **named-by-event** with the reason recorded before any filter output is
  examined.

**Slices are separate and contiguous, not stitched.** A splice is a step
discontinuity; at HPPeriod=48 each join contaminates ~50 bars, which would make
~38% of a three-regime stitched file artifact. Bar index, date, OHLC. Committed
to a new tracked directory distinct from the gitignored `data/`, and regenerated
by a tracked export script so the path from clone to CSV is runnable and
recorded.

**`.gitignore` unchanged.** The size reason holds for multi-year history and does
not bind at ~7 KB per slice.

**The past is not re-accounted.** The Week 6 notebook keeps its inputs, outputs
and numbers, and gets a header noting its data is unobtainable and its criteria
superseded. Slices and synthetic tests apply going forward only. Consistent with
part 2 §6.

**Crypto deferred.** BTC/USD H4 slices are a later decision.

**Closes** GAP-1.20 as a policy question and the root cause behind the Week 5,
Week 9, `Test_USLag.c` and Week 6 findings. **Does not close** implementation: no
slices, no export script, no synthetic test file exist yet.

## 6. Gaps

| ref | finding | status |
|---|---|---|
| GAP-1.17 | No stated tolerance for "sufficiently damped" | deferred — Phase 2.5, via parameter sensitivity |
| GAP-1.18 | `.c` header claims BTC/USD H4 validation; no BTC test script exists. BTC data *was* processed in the notebook, from an uncommitted export, producing an unconditional verdict | open |
| GAP-1.19 | `Test_HighPass.c` has no pass criterion — an exporter, not a test | open |
| GAP-1.20 | Validation artifacts unreproducible **by policy**, not accident; one root cause behind four findings | **resolved as a decision — D-14.1.** Implementation open |
| GAP-1.21 | Naming: file is `HighPassFilter.c`; docs say "HighPass" | open — minor, recorded in the notes |
| GAP-1.22 | Cell 8 criterion 1 (`\|mean\| < 0.0001`) cannot fail — second differences telescope, mean → 0 as 1/N for any coefficients; blind to all feedback terms | open — documented |
| GAP-1.23 | MAD-from-price used as lag measurement; optimum is the identity filter. Decycler wins by construction. Same metric that produced the false UltimateSmoother zero-lag claim | open — documented |
| GAP-1.24 | Cell 18 omits the 0.707 (alpha1 0.123024 vs 0.088513, 39% error) so it sweeps a filter the library does not contain; its "Smooth Ratio" column reduces algebraically to a constant; its conclusion is printed unconditionally. Cell 19 unaffected in structure | open |
| GAP-1.25 | Cross-asset verdict is a hardcoded string; "key findings" figures are typed literals, not the computed variables | open |
| GAP-1.26 | `WARMUP = 30` is short of ~50-bar settling; `series(Price[0], 3)` seeds a zero-mean filter at price level, leaving ~0.068 of transient in retained data. The `.c` comment is backwards for a high-pass | open — **not fixed**, changes all downstream output |
| GAP-1.27 | `HighPass_RoofingFilter_Notes.md`: six defects (a) wrong formula (b) trend explanation (c) unfalsifiable criteria restated as fact (d) BTC mean 365× its own gate marked ✅ (e) SSPeriod 2.6x vs 10.9x contradiction (f) VALIDATED header | (a)(b)(c)(d)(f) FIXED — `ec12066`; (e) open |
| GAP-1.28 | SS2 sensitivity SNR column non-monotonic (17.53 / 19.86 / **14.18** / 18.99); the Period=20 value duplicates the EUR/USD table entry exactly, suggesting a copied cell. Period=20 is used throughout the library | open — needs the Week 5 notebook re-run, blocked by GAP-1.10 |

## 7. Commits

| commit | what |
|---|---|
| `eb30662` | `SuperSmoother_Notes.md` — per-indicator status with named evidence; caveats relocated to the tables they describe; Key Finding 3 withdrawn, 4 narrowed; GAP-1.28 recorded; changelog added |
| `ec12066` | `HighPass_RoofingFilter_Notes.md` — §3 formula corrected (radians + 0.707); curvature correction; damping, settling and superposition added; §5 retitled superseded with all four criteria caveated; warmup and seeding defects recorded |

No measured value was changed in either file. All numbers written into the notes
were independently recomputed before commit, which caught two of them.

**Pending commit:** `docs/learning/HighPass_Explained.md` and this handoff.

## 8. Corrections to material produced in session

Claude produced seven errors, all caught by later verification. Recorded because
the failure mode is the one under review — figures stated to several significant
places inside an otherwise correct argument.

- Called bar 6 "the peak of the tent." Bar 5 is the peak.
- alpha1 at HPPeriod=48 given as 0.087749. Correct: **0.088513**.
- alpha1 at HPPeriod=20 given as 0.19814, 1% at 21 bars. Correct: **0.200653**,
  **20.6 bars**.
- Cell 18's alpha given as 0.1248, error 41%. Correct: **0.123024**, **39%**.
- MAD counterexample: distance given as 0.8 where |99 − 100.2| = **1.2**; mean
  1.100 → **1.200**.
- Teaching coefficients `0.5 / 1.0 / −0.5` were chosen for clean arithmetic and
  happen to have **complex** poles, so the ringing demonstration described a case
  the real filter does not exhibit. Corrected in session and labelled in the
  notes.
- GAP-1.20 was first asserted as equivalent to Week 5's finding without checking
  the notebook's read path, then over-corrected toward charity. The `.gitignore`
  check settled it.

Four of the seven were numbers quoted without computing. The habit, not the
magnitude, is the finding.

## 9. Next sitting starts here

**Chat title:** `Week 14 Session 1 (part 4) — Foundation Filters`

1. **RoofingFilter** — HP → SuperSmoother. Both stages now reviewed
   individually. Expect the same header/criteria pattern; the notebook and notes
   are shared with HighPass and have already been corrected, so the scope is the
   `.c` file, `Test_RoofingFilter.c`, and the SSPeriod contradiction (GAP-1.27e).
2. **Decycler** — `Price − HighPass`, i.e. `UltimateSmootherE` under another
   name. Worth establishing whether the two files are the same filter, given part
   2's `UltimateSmoother` finding. GAP-1.23 applies directly: its "4.5x closer to
   price" claim is not a lag result.
3. **`CyberCycle.c` statics missing the `cc_` prefix** (GOTCHAS 1.3) — plan §4.1
   suggests session 6; still unconfirmed after three sittings.

**Deliberately not done tonight, all unblocked:**

- `HighPassFilter.c` header line "Validated: EUR/USD D1, BTC/USD H4" — live code,
  six dependent files, needs before/after verification discipline
- The seeding fix (GAP-1.26) — changes every downstream output
- The synthetic test file — replaces five unfalsifiable criteria; the tent built
  in this sitting is the instrument
- D-14.1 implementation — three slices, export script, tracked directory

**New in the repo:** `docs/learning/` — plain-language explanations of mechanisms,
distinct from `docs/indicators/` which records library status and evidence.
Revised freely as understanding improves.
