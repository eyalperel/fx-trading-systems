# DIAG1 read 1 — Strategy 2 slot set with random C1, true x0 (decisive) and x0r (information)

Criteria: `docs/preregistration/DIAG1_S2Slots_ZeroCost_Criteria.md` (+ Amendment 1). Rows sha256 `9eb5313ada48767a59cc6d86ff705ff453ecd58ba9f703c791f7f0fe94de2e91`.

## x0 (decisive)

| Arm | EUR/USD | AUD/USD | EUR/JPY | Pooled | SE (jackknife) | z | Signals pooled |
|---|---|---|---|---|---|---|---|
| A0 | -0.0206 | -0.0106 | +0.0040 | -0.0105 | 0.0120 | -0.87 | 719825 |
| A1 | -0.0211 | -0.0105 | +0.0060 | -0.0100 | 0.0113 | -0.88 | 989771 |
| A2 | -0.0135 | -0.0137 | -0.0057 | -0.0116 | 0.0077 | -1.49 | 1064046 |
| A3 | -0.0126 | -0.0117 | -0.0051 | -0.0103 | 0.0073 | -1.41 | 1519085 |
| A4 | +0.0018 | -0.0055 | -0.0004 | -0.0015 | 0.0046 | -0.33 | 1419360 |

| Contrast | EUR/USD | AUD/USD | EUR/JPY | Pooled | SE | z |
|---|---|---|---|---|---|---|
| A0-A4 | -0.0224 | -0.0052 | +0.0044 | -0.0089 | 0.0125 | -0.71 |
| A3-A4 | -0.0144 | -0.0062 | -0.0046 | -0.0088 | 0.0087 | -1.01 |
| A0-A1 | +0.0006 | -0.0002 | -0.0020 | -0.0005 | 0.0022 | -0.22 |
| A0-A2 | -0.0071 | +0.0031 | +0.0097 | +0.0011 | 0.0088 | +0.13 |

## x0r (information: spread 0, rollover in)

| Arm | EUR/USD | AUD/USD | EUR/JPY | Pooled | SE (jackknife) | z | Signals pooled |
|---|---|---|---|---|---|---|---|
| A0 | -0.0285 | -0.0117 | -0.0014 | -0.0151 | 0.0121 | -1.25 | 719825 |
| A1 | -0.0286 | -0.0115 | +0.0006 | -0.0145 | 0.0114 | -1.27 | 989771 |
| A2 | -0.0199 | -0.0147 | -0.0105 | -0.0155 | 0.0077 | -2.02 | 1064046 |
| A3 | -0.0186 | -0.0126 | -0.0099 | -0.0141 | 0.0073 | -1.94 | 1519085 |
| A4 | -0.0098 | -0.0068 | -0.0103 | -0.0088 | 0.0049 | -1.80 | 1419360 |

| Contrast | EUR/USD | AUD/USD | EUR/JPY | Pooled | SE | z |
|---|---|---|---|---|---|---|
| A0-A4 | -0.0187 | -0.0049 | +0.0089 | -0.0063 | 0.0126 | -0.50 |
| A3-A4 | -0.0088 | -0.0058 | +0.0004 | -0.0053 | 0.0087 | -0.60 |
| A0-A1 | +0.0002 | -0.0002 | -0.0019 | -0.0006 | 0.0022 | -0.29 |
| A0-A2 | -0.0086 | +0.0030 | +0.0091 | +0.0004 | 0.0089 | +0.04 |

## Reading rule (true x0)

- Slot set costs R (pooled A0 < 0, z <= -2, negative on all 3 pairs): **not met** (pooled -0.0105, z -0.87, per pair -0.0206, -0.0106, +0.0040).
- A3-A4 costs R (z <= -2 pooled, same sign on >= 2 of 3 pairs): **not met** (-0.0088, z -1.01, same sign on 3 of 3).
- A0-A1 costs R (z <= -2 pooled, same sign on >= 2 of 3 pairs): **not met** (-0.0005, z -0.22, same sign on 2 of 3).
- A0-A2 costs R (z <= -2 pooled, same sign on >= 2 of 3 pairs): **not met** (+0.0011, z +0.13, same sign on 2 of 3).
- Sanity A4 (random C1 alone, true x0): -0.0015, z -0.33.

## Rollover contribution (x0r - x0), pooled

| Arm | x0r - x0 |
|---|---|
| A0 | -0.0046 |
| A1 | -0.0045 |
| A2 | -0.0039 |
| A3 | -0.0038 |
| A4 | -0.0073 |

Limitations (c): circular shifts are correlated draws; ~19 calendar-year blocks; rollover is a 2025-07-28 snapshot; diagnostic only, nothing is selected from it.
