# NULL1 read 1 — the template's null distribution on EUR/USD D1

Criteria: `docs/preregistration/NULL1_TemplateNull_Criteria.md`. Statistic: mean signal-R per run. Null runs sha256 `201a14f904d5e559fe0163bb73cd56ba71e6d1d3b2d68dba4a46686e8a78ad40`, positive control `8efe5c9890a6e8faa4741d470c613dcbb0af27cca9629a281ed2e93fdd5faa83`.

## Null distributions (1,000 circular shifts each)

| Set | Level | signals (median) | mean | sd | 2.5% | 5% | 50% | 95% | 97.5% |
|---|---|---|---|---|---|---|---|---|---|
| F1 | x2 | 260 | -0.0248 | 0.0310 | -0.0833 | -0.0743 | -0.0247 | +0.0261 | +0.0376 |
| F1 | x0 | 260 | -0.0062 | 0.0310 | -0.0647 | -0.0558 | -0.0060 | +0.0449 | +0.0566 |
| F2 | x2 | 260 | -0.0464 | 0.0347 | -0.1137 | -0.1045 | -0.0464 | +0.0094 | +0.0198 |
| F2 | x0 | 260 | -0.0285 | 0.0347 | -0.0955 | -0.0863 | -0.0284 | +0.0274 | +0.0372 |
| O1 | x2 | 914 | -0.0255 | 0.0245 | -0.0742 | -0.0644 | -0.0257 | +0.0132 | +0.0228 |
| O1 | x0 | 914 | -0.0071 | 0.0245 | -0.0557 | -0.0462 | -0.0073 | +0.0315 | +0.0412 |
| O2 | x2 | 506 | -0.0282 | 0.0371 | -0.1025 | -0.0923 | -0.0279 | +0.0318 | +0.0412 |
| O2 | x0 | 506 | -0.0098 | 0.0371 | -0.0842 | -0.0740 | -0.0096 | +0.0501 | +0.0599 |

## F1 / F2: where the real PERF results sit (describe only; PERF1 / PERF2 verdicts unchanged)

| Set | Real mean signal-R x2 (Zorro, PERF) | Percentile in null x2 | Engine's own real x2 (V1) | Percentile |
|---|---|---|---|---|
| F1 | -0.0304 | 42.7% | -0.0315 | 41.9% |
| F2 | -0.0479 | 47.5% | -0.0498 | 45.8% |

## Positive control (C5; Q1 rule: detected if the carrier >= the null's 95th percentile)

| Set | mu (x ATR / bar) | Carrier mean signal-R | Null 95% | Carrier percentile | Detected |
|---|---|---|---|---|---|
| O1 | 0.01 | +0.0139 | +0.0137 | 95.0% | YES |
| O1 | 0.02 | +0.0360 | +0.0144 | 99.5% | YES |
| O1 | 0.05 | +0.1044 | +0.0158 | 100.0% | YES |
| O2 | 0.01 | -0.0413 | +0.0313 | 35.8% | no |
| O2 | 0.02 | -0.0076 | +0.0279 | 70.8% | no |
| O2 | 0.05 | +0.0763 | +0.0335 | 99.9% | YES |

## Predictions (c) against results

- F1 / F2 null centre x2 in [-0.06, -0.01]: F1 -0.0247, F2 -0.0464 -> met
- real PERF results between the 5th and 95th percentile: met ({'F1': True, 'F2': True})
- x0 null centres within +-0.02 of 0: F1 -0.0060, F2 -0.0284, O1 -0.0073, O2 -0.0096 -> NOT met
- mu 0.05 detected in O1 and O2: met
- mu 0.01 not detected in at least one: met
- mu 0.02: not predicted

## Limitations (c)

- Circular shifts of one series: neighbouring offsets are correlated; 1,000 runs are fewer independent draws.
- The engine's cost model differs from Zorro on a few halves (V1: M-D7 trigger shifts); medians match exactly.
- One asset, one feed; the positive control's drift is a construct (C5), its R is measured, not a market property.
