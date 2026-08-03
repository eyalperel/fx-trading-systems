# Addendum — Regime-Conditional Cycle Test

**Date:** 2026-08-03
**Extends:** `Cycle_Premise_Null_Test.md`
**Addresses:** the "persistent cycles only" limitation stated in §7 of the main document

---

## 1. The challenge being tested

The aggregate test computes one prominence value per series. If cycles appear only during specific volatility regimes, averaging across 2,000+ bars would wash them out. This was flagged in the main document as the most defensible challenge to the null result, and is tested here directly.

---

## 2. Design, and why it changed twice

### 2.1 Rejected: regime segmentation

The obvious approach — split into volatility regimes, test each separately — is not viable. Measured contiguous run lengths:

| Vol smoothing | Median run | Runs ≥200 bars (EUR/USD) |
|---|---|---|
| 20 bars | 5 | 1 |
| 60 bars | 6 | 3 |
| 120 bars | 9 | 4 |

A 10–48 bar passband cannot be measured inside a 5-bar segment, and only 1–4 segments would qualify. Concatenating same-regime segments was rejected outright: splicing introduces artificial discontinuities and manufactures spurious spectral content — precisely the artefact class this project exists to detect.

### 2.2 Rejected: max-window-prominence

First working design used rolling 250-bar windows and took the **maximum** prominence across windows. Its positive control detected a regime-localised cycle **10.8% of the time at −6 dB** — barely above the 5% false-positive floor.

Cause: a maximum over ~67 windows *and* over all passband frequencies is a double maximum, so its null distribution is heavy-tailed. Null-D's 95th percentile came out at **61.45** against a real value of 20.47. Multiple-comparison inflation.

**This failure is retained in the record rather than deleted.** It is the positive control doing exactly its job, and it is the reason the final null result can be trusted. A version of this experiment without a positive control would have reported the underpowered non-rejection as a finding.

### 2.3 Adopted: volatility contrast on window means

| Statistic | Definition |
|---|---|
| `M_hi` | mean prominence, top-tercile volatility windows |
| `M_lo` | mean prominence, bottom-tercile volatility windows |
| **`D_hilo`** | **`M_hi − M_lo`** — directly tests "cycling is associated with volatility state" |
| `M_all` | mean prominence, all windows |

Means rather than maxima give a tight null; the contrast targets the hypothesis instead of fishing across windows.

---

## 3. Results — EUR/USD D1

**Real values:** `M_hi` = 8.372, `M_lo` = 9.337, **`D_hilo` = −0.965**, `M_all` = 8.442

Two-sided rank p-values, N = 300 per null:

| Statistic | A boot | B fgn | C iaaft | D stochvol |
|---|---|---|---|---|
| M_hi | 0.487 | 0.693 | 0.800 | 0.607 |
| M_lo | 0.920 | 0.753 | 0.567 | 0.900 |
| **D_hilo** | **0.660** | **0.693** | **0.727** | **0.793** |
| M_all | 0.360 | 0.493 | 0.960 | 0.353 |

Nothing significant. `D_hilo` sits at the 33rd–40th percentile of every null.

**Direction:** `D_hilo` is *negative* — prominence is slightly **lower** in high-volatility windows. If anything, volatile periods are marginally less cycle-like, though the effect is well within noise.

---

## 4. Detection power — the honest bound

The positive control was re-run with a **block-structured** cycle (contiguous 400-bar blocks), which matches a realistic "sustained regime" hypothesis:

| Injected SNR | mean `D_hilo` | detection rate |
|---|---|---|
| −20 dB | −0.05 | 0.067 |
| −16 dB | −0.34 | 0.033 |
| −12 dB | 0.73 | 0.133 |
| **−8 dB** | **13.04** | **0.833** |
| −4 dB | 51.12 | 1.000 |

**Bound:** a cycle confined to sustained high-volatility blocks would have been detected 83% of the time at SNR ≥ −8 dB (≈15.8% of return variance) and 100% at −4 dB (≈39.8%).

This is a **materially weaker bound** than the aggregate test's −13.5 dB / 4.4%. Stated plainly: the regime-conditional test can only rule out fairly strong regime-localised cycles. Weaker ones remain possible.

---

## 5. What remains untestable, and why

The bar-level control (cycle injected at top-tercile volatility *bars* rather than in blocks) produced **no detectable signal at any SNR from −25 to −10 dB.** This is not a defect of the statistic — the block control proves the statistic works. It is a structural limit:

> Real volatility regimes on EUR/USD D1 have median run lengths of 5–9 bars. A 20-bar cycle cannot complete even one period inside a typical regime. A cycle that switches on and off with bar-level volatility is therefore **not measurable at this cycle scale**, by this or any spectral method.

Whether such a thing would even be tradable is a separate question — a cycle that never completes a period offers no phase to extrapolate.

With heavier smoothing (120-bar), 88% of high-volatility bars do fall in runs ≥60 bars, so sustained regimes exist. Those are what the block control tests, and they show nothing.

---

## 6. Conclusion

The regime-conditional challenge is **addressed but not fully closed.**

- No evidence of volatility-associated cycling on EUR/USD D1 (all p ≥ 0.36; direction slightly negative).
- Bound is weaker than the aggregate test: rules out regime-localised cycles above ~−8 dB, not ~−13.5 dB.
- Bar-level intermittent cycling remains structurally untestable at this scale, and arguably untradable by construction.

Combined with the aggregate result, the reasonable position is: **no cycle detected, aggregate or regime-conditional, above the stated bounds.** The premise remains unsupported, and the residual space where a cycle could hide is smaller than before but not empty.

---

## 7. Not yet done

**BTC/USD H4 regime test.** Not run. BTC has 5,627 usable bars versus EUR/USD's 1,936, so regimes are longer in absolute terms and the test should be better powered. This is the single most valuable remaining extension.

```bash
cd analysis/null_tests && python run_regime2.py btc
```

Runs nulls A, B and D (IAAFT omitted for runtime; it is the least informative null for a regime question since it preserves the global spectrum by construction).

---

## 8. Reproducibility

```
run_regime2.py           final design (volatility contrast)
out/regime2_*_EURUSD.csv real values, p-values, power curve
```

`WIN` = 250 bars, step 25, terciles by mean absolute return per window.
N = 300 surrogates per null, 100 per control point. Seed 20260803.

The superseded max-prominence design (`run_regime.py`) is retained in the
repository as the record of the underpowered first attempt.
