# DIAG1 — Does Strategy 2's slot set lose R at zero cost with random C1, and which part? — Criteria

**Status:** pre-registered 2026-11-26, before any DIAG1 run and before any code for it is written. Amendments are dated and
appended below, never edited in place (PROJECT_STATE §2.2).
**Decided:** planning chat 2026-11-26 (decision N3: B + D; G-a; J-a; R1-R5; user: as recommended / G-a). Branch
`c1s3-pooled-c1-screen`; shares only the Zorro check click with `C1S3_FiveC1_Pooled_Criteria.md` and has its own verdict.
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Purpose

(b) NULL1 read 1 (EUR/USD, 1,000 circular shifts of the C1 state, x0 = no costs): null median **-0.028** signal-R for F2
(Strategy 2's full slot set: FRAMA baseline, MESA vs SMA(10) C1, Laguerre RSI C2, bridge-too-far) vs **-0.010** for O2 (the
same C1 alone). The prediction "x0 centres within +-0.02" was not met for F2. All shifts share one price path, so the offset
spread does not contain path noise.
(c) Question: is the F2 loss at zero cost real (beyond path noise, on three pairs), and if so which slot part carries it?
**Diagnostic only:** nothing is selected, removed or tuned on this result; any template change is a new counted variant under
its own pre-registration.

## Arms (decision G-a)

All at **x0**; C1 = MSS states (MESA Stochastic(20, 48, 10) vs SMA(10), as `NNFX_Strategy2.h`) circularly shifted; baseline,
C2, ATR unshifted (as NULL1 F2). Switches existing in `analysis/template/reference_engine.py` (b): `baseline_mode`, `btf_on`;
C2 neutralised by input only (c2 := c1 state on every bar), no engine change.

| Arm | Baseline FRAMA(32) | C2 LRSI 0.5 | Bridge-too-far |
|---|---|---|---|
| A0 = F2 | on | on | on |
| A1 | on | on | off |
| A2 | on | neutral (c2 := c1) | on |
| A3 | on | neutral | off |
| A4 = O2 | off (C1-only) | unused | unused |

Contrasts: **A0 - A4** (does the slot set cost R at all), **A3 - A4** (baseline), **A0 - A1** (bridge-too-far), **A0 - A2** (C2).

## Pairs, ranges, offsets

- **EUR/USD:** PERF bars and trade range as NULL1; offsets `NULL1_offsets.csv` (sha256 `f54e5308...`, as C1S1).
- **AUD/USD, EUR/JPY:** bars, ranges, fillers as C1S2; offsets C1S2's committed files (sha256 69ffaa73... / 2a357ac8...).
- Indicator values on the new pairs (MESA, SMA, LRSI, FRAMA, ATR) must have passed C1S3's VW2 check before any DIAG1 run.
- All 15 arm x pair cells are run new (5 arms x 3 pairs x 1,000), because NULL1's stored rows hold one mean per offset and the
  statistic below needs per-year sums. **Guard G0:** the re-run EUR/USD A0 / A4 per-offset means must equal NULL1's stored F2 /
  O2 x0 rows (sha256 `201a14f9...`) on all 1,000 offsets (1e-12); a planted change (e.g. btf off in A0) must fail G0.

## Statistic and reading rule (decision J-a)

1. Per arm and pair: **x0 null mean** = total R / total signals over all 1,000 offsets; also by exit calendar year.
2. **Path noise:** blocks = calendar exit years, R and signals summed over offsets and over the three pairs (same-year blocks
   are pooled because USD / EUR moves correlate across the pairs). SE of the pooled mean by **delete-one-year jackknife** over
   the blocks; z = mean / SE.
3. **Contrasts:** the same jackknife on the per-year difference of the two arms' block means (pairing by year removes the
   shared path noise).
4. Reading (information, not acceptance):
   - "**Slot set costs R**": pooled A0 < 0 with z <= -2 **and** A0 negative on each of the three pairs.
   - "**Component X costs R**": its contrast z <= -2 pooled **and** the same sign on at least 2 of 3 pairs.
   - Otherwise: "not distinguishable from path noise".
5. **Sanity row A4:** random C1 alone at zero cost. If |z| >= 2 the report says so and flags the two candidate causes (c): a
   measurement artefact, or drift captured by the long / short share (circular shifts keep that share and move its timing).
Reported per arm and pair: signals, halves, mean, entry-kind counts, refusals; pooled table of arms and contrasts with SE, z,
per-pair signs.

## Predictions (decision R1-R5; (c), committed before any build or run)

- **R1** EUR/USD A0 mean within +-0.010 of -0.028; A4 within +-0.010 of -0.010 (NULL1 medians; the pooled mean of 1,000
  shifts should sit near their median). G0 PASS.
- **R2** Pooled A0 in [-0.04, +0.01].
- **R3** "Slot set costs R" **not met** (pooled A0 z > -2, or not negative on all three pairs): one path's -0.028 is read as
  within path noise.
- **R4** A4 pooled within +-0.02 of 0 and |z| < 2.
- **R5** No component contrast meets its rule. Which contrast is largest is not predicted.

## Run order

1. Commit with the C1S3 file (before any code).
2. Build `tools/diag1.py` (arms, per-year output, G0, jackknife, report) + tests: jackknife on a hand-built block table;
   c2 := c1 neutralisation leaves an F2 run with C2 always agreeing; G0 planted change fails; commit.
3. After C1S3's VW2 PASS on both pairs: G0, then the null runs (15 x 1,000, resumable); results sha256 recorded (appended).
4. Read: report `analysis/diag1/DIAG1_report.md`; appended below as "DIAG1 read 1".

## Count

Diagnostic arms: **5** (outside the strategy and C1 counts; no variant is chosen from them). Project-wide full-strategy
variants: 2 (unchanged).

## Amendments

### Amendment 1 (2026-11-26, before any DIAG1 code or run): NULL1's "x0" includes rollover; cost levels defined

- **Found (b)** while building, before any DIAG1 run: `tools/null1.py` `half_r(hf, day, mult)` adds `roll_price(...)` at every
  multiplier, so NULL1's x0 rows are **spread 0 with rollover**, not "no costs" as NULL1's criteria (line 52) state. The
  Purpose figures above (-0.028 F2, -0.010 O2) are those rows. C1S2's x0 rows are correct (`roll=False`); C1S1 used x2 only.
  Correction records: NULL1 Amendment 2, FINDINGS1 and PROJECT_STATE wording (same date).
- (c) Size: EUR/USD asset-list rollover is about -1.05 pips per day long / +0.50 short per 1,000 units (NULL1 constants:
  0.8947 x 0.1 / 856.1); with a balanced long / short share about -0.27 pips per day held, about -0.02 R per signal at ~10
  days against a ~120-pip stop: the order of the whole F2 effect. A hypothesis, measured by the x0r - x0 row below.
- **User decision A1-a:**
  - **Decisive level: true x0** = no spread, no rollover (net = dir x (exit - entry)), as this file's text says. The reading
    rule (J-a) and R2-R5 apply to true x0, unchanged.
  - **Information level x0r** = spread 0, asset-list rollover in (NULL1's definition), per pair constants (EUR/USD as
    `null1.py`; AUD/USD, EUR/JPY as C1S2). Reported per arm and pair with the same jackknife; never decisive.
  - **Rollover contribution** = x0r - x0 per arm and pair (and pooled), reported.
  - **G0** compares the re-run EUR/USD A0 / A4 at **x0r** with NULL1's stored F2 / O2 x0 rows (stored at 6 decimals: tolerance
    5e-7 on mean and total, exact on signals and halves, all 1,000 offsets); a planted change must fail G0.
  - **R1** is read as a statement about x0r (its values came from NULL1's rows): EUR/USD A0 x0r within +-0.010 of -0.028, A4
    x0r within +-0.010 of -0.010. Values unchanged.
- No prediction is added or changed after the finding beyond this labelling.

## Record: build (run order 2) — 2026-11-26, before any DIAG1 run

- `tools/diag1.py`: arms (A0 = `E.Params()` as NULL1 F2; A1 / A3 `btf_on = False`; A2 / A3 c2 := the shifted c1; A4
  `baseline_mode = "off"`), levels x0 (dir x (exit - entry) / (1.5 ATR)) and x0r (EUR/USD `null1.half_r(..., 0)`, others
  `c1s2.half_r(..., 0, roll=True)`), per-exit-year sums per row, resumable null runs (an offset writes all 5 arms x 2 levels
  or none), G0 (x0r vs NULL1 F2 / O2 x0 rows, 5e-7, signals / halves exact, 1,000 offsets each), read (per-pair and pooled
  means, delete-one-calendar-year jackknife, contrasts paired by year, the J-a rule, A4 sanity, x0r - x0 per arm).
- `tools/tests/test_diag1.py` (9 tests): arm configs (C2 neutral = c1, input untouched, btf / baseline switches); x0 has no
  rollover and x0r - x0 = exactly the rollover, per-pair constants; year-string round trip; blocks sum over offsets and pairs
  and exclude other arms / levels; **jackknife hand-calculated** (3 years, SE 0.0881917); a paired contrast with a constant
  shift has SE 0; G0 equal, rounding inside tolerance, **planted changes fail** (mean, one signal), true-x0 rows not compared.
- All tools tests 192 / 192 OK. No DIAG1 engine run before this commit.
