# PREM1 read 1 — directional predictability at 2-60 days, D1 FX (EUR/USD, AUD/USD, EUR/JPY)

Criteria: `docs/preregistration/PREM1_D1FX_Predictability_Criteria.md`.

**Random-sign null (decisive):** bar (95th pct of max|z|) **2.406**; pooled null sd of VR(2) - 1 0.0122. Real M = **1.327**. Flagged horizons: **none**.

| q | VR EUR/USD | VR AUD/USD | VR EUR/JPY | pooled D | null 5th / 50th / 95th | pct | z |
|---|---|---|---|---|---|---|---|
| 2 | 1.0075 | 0.9747 | 0.9920 | -0.0086 | -0.0201 / -0.0008 / +0.0199 | 25.5% | -0.66 |
| 5 | 0.9869 | 0.9573 | 0.9451 | -0.0369 | -0.0432 / -0.0023 / +0.0432 | 8.7% | -1.33 |
| 10 | 0.9802 | 0.9270 | 0.9278 | -0.0550 | -0.0636 / -0.0055 / +0.0696 | 7.9% | -1.30 |
| 20 | 0.9829 | 0.9117 | 0.9031 | -0.0674 | -0.0924 / -0.0090 / +0.0933 | 13.8% | -1.07 |
| 40 | 0.9980 | 0.9184 | 0.8625 | -0.0737 | -0.1289 / -0.0129 / +0.1457 | 21.2% | -0.79 |
| 60 | 0.9949 | 0.9590 | 0.8657 | -0.0602 | -0.1554 / -0.0179 / +0.1723 | 32.2% | -0.51 |

**Stochvol null (information):** bar 2.459; real M 1.519; flagged: none.

**Positive control (detection rate, flagged with the planted sign):**

| kind | level | rate (+) | rate (-) |
|---|---|---|---|
| ar1 | 0.01 | 0.130 | 0.115 |
| ar1 | 0.02 | 0.325 | 0.280 |
| ar1 | 0.03 | 0.615 | 0.550 |
| ar1 | 0.05 | 0.975 | 0.945 |
| mom | 0.02 | 0.115 | 0.030 |
| mom | 0.05 | 0.150 | 0.050 |
| mom | 0.10 | 0.415 | 0.240 |
| mom | 0.20 | 0.955 | 0.715 |
| mom | 0.30 | 1.000 | 0.980 |
| mom | 0.40 | 1.000 | 1.000 |

**Detection bounds (>= 90%, both signs):** AR(1) phi = 0.05, momentum kappa = 0.3 (pre-registered rule). Information (Amendment 1): sign-specific kappa_90 trend side (+) 0.2, reversal side (-) 0.3; phi_90 (+) 0.05, (-) 0.05.

Limitations (c): one history per pair; equal-weight pooling; the random-sign null assumes sign symmetry; slow momentum below the kappa bound is invisible to this test.
