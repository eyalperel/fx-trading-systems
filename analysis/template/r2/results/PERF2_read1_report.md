# PERF2 read 1 — Strategy 2 v0 on this EUR/USD feed

Criteria: `docs/preregistration/PERF2_Strategy2_EURUSD_Criteria.md` (P-1 table, P-3 verdict, P-4). Not a result about EUR/USD in general (P-4.1).

## What ran

- Variants counted: **1** (Strategy 2, variant 0, EUR/USD); project-wide strategy variants tested: **2** after this read (1 before). x1 / x2 are reporting levels, not variants (P-3).
- Computed by `tools/perf_report.py` from two template logs; half-R and signal-R use the ACTUAL risk (lots x stop pips x PIPCost, SIZE row).

- x1 log: `/sessions/rcw-013lzkyej3cgbeeogpd6ljv8/mnt/zorro/Data/TPL_R2b_log_run1.csv`, sha256 `431922aad1bbfe4917ab0f2551b7e8d26eeb828b115f523f3b21ef3c0c4d984f`
- x2 log: `/sessions/rcw-013lzkyej3cgbeeogpd6ljv8/mnt/zorro/Data/TPL_R2c_log_run1.csv`, sha256 `9c26d615bd8db7492bd4e469e67440bd4bc75de282c1aecc7e1edd5a160a2734`

## Verdict (spread x2, P-3)

**STOP**

- signals n = 282, mean signal-R = -0.047949, sample sd = 0.680204, **t = -1.1838** (rule t >= 2, (c) a convention)
- total R = -13.5217; best year (exit year) = 2008 with +2.4852; total R with the best year removed = -16.0069
- x1 for reading only (not decisive): t = -1.0218, mean = -0.041269, total R without best year = -14.1812 (would read: STOP)

## Items 1-13 (all signals / standard only / continuation only; x1 and x2)

| Item | all x1 | all x2 | standard x1 | standard x2 | continuation x1 | continuation x2 |
|---|---|---|---|---|---|---|
| 1 signals | 282 | 282 | 262 | 262 | 20 | 20 |
| 1 halves | 564 | 564 | 524 | 524 | 40 | 40 |
| 2 total R (signal-R) | -11.6379 | -13.5217 | -11.2770 | -12.9437 | -0.3609 | -0.5780 |
| 2 mean R per signal | -0.0413 | -0.0479 | -0.0430 | -0.0494 | -0.0180 | -0.0289 |
| 3 mean R per half (all) | -0.0413 | -0.0479 | -0.0430 | -0.0494 | -0.0180 | -0.0289 |
| 3 mean R, TP1 half | -0.0588 | -0.0677 | -0.0609 | -0.0697 | -0.0305 | -0.0412 |
| 3 mean R, runner half | -0.0238 | -0.0282 | -0.0251 | -0.0291 | -0.0056 | -0.0166 |
| 4 win rate (signals, net R > 0) | 39.4% (111/282) | 39.4% (111/282) | 38.9% (102/262) | 38.9% (102/262) | 45.0% (9/20) | 45.0% (9/20) |
| 5 max drawdown, closed halves (signal-R) | 15.5114 | 17.3175 | 16.7267 | 18.8284 | 3.8889 | 3.9491 |
| 6 swap, summed (R) | -3.1133 | -3.1887 | -2.5951 | -2.6706 | -0.5182 | -0.5182 |
| 6 swap, % of total net R | +26.75% | +23.58% | +23.01% | +20.63% | +143.56% | +89.65% |
| 7 spread cost, summed (R, cost positive) | 2.5889 | 5.1779 | 2.3686 | 4.7373 | 0.2203 | 0.4406 |
| 8 same-bar stop + TP1, signals | 0 | 0 | 0 | 0 | 0 | 0 |
| 8 ... resolved by half-1 exit | none | none | none | none | none | none |
| 9 long TP1 halves | 53 | 53 | 50 | 50 | 3 | 3 |
| 10 exit reason: c1_flip | 92 | 93 | 77 | 78 | 15 | 15 |
| 10 exit reason: baseline | 284 | 284 | 273 | 273 | 11 | 11 |
| 10 exit reason: stop | 38 | 38 | 34 | 34 | 4 | 4 |
| 10 exit reason: tp1 | 101 | 101 | 93 | 93 | 8 | 8 |
| 10 exit reason: be | 36 | 35 | 35 | 34 | 1 | 1 |
| 10 exit reason: trail | 11 | 11 | 11 | 11 | 0 | 0 |
| 10 exit reason: exit_ind | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 exit reason: be_adverse | 2 | 2 | 1 | 1 | 1 | 1 |
| 10 exit reason: end | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 exit reason: other | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 refused: bridge-too-far | 158 | 158 | 158 | 158 | 0 | 0 |
| 11 refused: below 1 lot | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 refused: margin | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 refused: risk above configured | 0 | 0 | 0 | 0 | 0 | 0 |
| 12 total R, exit year 2007 | -1.2264 | -1.2921 | -1.2264 | -1.2921 | 0 (no signal) | 0 (no signal) |
| 12 total R, exit year 2008 | +2.5432 | +2.4852 | +3.5833 | +3.5303 | -1.0400 | -1.0451 |
| 12 total R, exit year 2009 | +0.2078 | +0.1239 | +0.3400 | +0.2630 | -0.1322 | -0.1390 |
| 12 total R, exit year 2010 | -4.7272 | -4.7862 | -4.7272 | -4.7862 | 0 (no signal) | 0 (no signal) |
| 12 total R, exit year 2011 | -1.9032 | -1.9466 | -1.9032 | -1.9466 | 0 (no signal) | 0 (no signal) |
| 12 total R, exit year 2012 | -3.1370 | -3.2418 | -2.5692 | -2.6646 | -0.5677 | -0.5771 |
| 12 total R, exit year 2013 | +2.2685 | +2.1584 | +2.2685 | +2.1584 | 0 (no signal) | 0 (no signal) |
| 12 total R, exit year 2014 | +1.1285 | +0.9861 | +1.8559 | +1.7244 | -0.7274 | -0.7383 |
| 12 total R, exit year 2015 | +2.1740 | +2.0665 | +2.1740 | +2.0665 | 0 (no signal) | 0 (no signal) |
| 12 total R, exit year 2016 | +0.8920 | +0.7610 | +0.8920 | +0.7610 | 0 (no signal) | 0 (no signal) |
| 12 total R, exit year 2017 | -1.6826 | -1.7755 | -0.8178 | -0.8917 | -0.8648 | -0.8839 |
| 12 total R, exit year 2018 | -6.0405 | -6.2319 | -6.0405 | -6.2319 | 0 (no signal) | 0 (no signal) |
| 12 total R, exit year 2019 | +0.4125 | +0.2121 | +0.3376 | +0.1626 | +0.0749 | +0.0495 |
| 12 total R, exit year 2020 | -2.4473 | -2.6827 | -3.5048 | -3.7101 | +1.0574 | +1.0274 |
| 12 total R, exit year 2021 | +2.0769 | +1.8412 | +1.6227 | +1.4126 | +0.4542 | +0.4286 |
| 12 total R, exit year 2022 | -0.6915 | -0.8135 | -1.0306 | -1.1449 | +0.3392 | +0.3313 |
| 12 total R, exit year 2023 | +1.2231 | +1.0953 | +0.0124 | -0.0949 | +1.2107 | +1.1902 |
| 12 total R, exit year 2024 | +0.4741 | +0.3079 | +1.2148 | +1.0796 | -0.7407 | -0.7717 |
| 12 total R, exit year 2025 | -4.0667 | -3.6249 | -4.6421 | -4.1750 | +0.5755 | +0.5501 |
| 12 total R, exit year 2026 | +0.8837 | +0.8358 | +0.8837 | +0.8358 | 0 (no signal) | 0 (no signal) |
| 13 longs: count, total R | 149, -11.9524 | 149, -12.6115 | 136, -9.4228 | 136, -9.9466 | 13, -2.5296 | 13, -2.6650 |
| 13 shorts: count, total R | 133, +0.3144 | 133, -0.9102 | 126, -1.8542 | 126, -2.9971 | 7, +2.1686 | 7, +2.0870 |

Item 10 counts halves. Item 12: calendar year of the signal's last exit (c: the criteria say 'year of the exit'; a signal is placed whole in the year its last half closed). Item 5: the running sum of half-R x its share of signal risk, in log order within a day, peak starts at 0 (c).

## Information only (never used in a verdict)

| | x1 | x2 |
|---|---|---|
| final equity (EUR, 2025-07-28 rates, M-D8.4), last ACCT row | 77496.93 | 74616.99 |
| max MarginTotal / Equity | 0.0373 | 0.0374 |

## P-4 near-miss table (information only; counts possible flips, R is not recomputed)

Daily bars from the M1 history (r1_data, bar rule of R1). Margin = pips between a bar's extreme and the level, over the half's life (entry bar to exit bar; the exit bar only for level exits). A half 'could flip' under a shift of s pips when some bar stayed within s of a level without crossing it, or crossed it by less than s.

| level | halves | flip at 0.5 pip: stop / TP1 / either | flip at 1 pip: stop / TP1 / either | flip at 2 pip: stop / TP1 / either | closest uncrossed (stop / TP1, pips) | crossed halves (stop / TP1) | smallest overshoot (stop / TP1, pips) |
|---|---|---|---|---|---|---|---|
| x1 | 564 | 5 / 2 / 7 | 6 / 4 / 10 | 9 / 10 / 19 | 0.12 / 0.16 | 85 / 101 | 0.40 / 0.41 |
| x2 | 564 | 5 / 2 / 7 | 6 / 4 / 10 | 8 / 10 / 18 | 0.12 / 0.16 | 84 / 101 | 0.40 / 0.41 |

## History files used (P-4.1)

| file | sha256 |
|---|---|
| `EURUSD_2005.t6` | `e9bf0c7f9de70842056be7e1608f8c7cb5859f4ce5c8decff70aacbcb0997340` |
| `EURUSD_2006.t6` | `1fbd5f6736635c48c0984b8eaf16607a04ce545e4533c531c0106210cf8e7c8f` |
| `EURUSD_2007.t6` | `347f2bf5321b9f4827805503d62c990cc73530da9c15e8450899640c3c773bf9` |
| `EURUSD_2008.t6` | `30d93c82fbd20399845ec088d15ec9d8842a2a3bae515e8129c26b734cd7326d` |
| `EURUSD_2009.t6` | `9d789f389a8017a17f75aa6c33f40cc6eff595a343f526ea8a3d890ab129249b` |
| `EURUSD_2010.t6` | `d037f40b3ebbbf70be82e7ac9e42af8e277b1d080461cad19cd726a44a0e935e` |
| `EURUSD_2011.t6` | `d77b8928bb42c5cd217843cd2fbb454a08e4ab32f9cb3a07101075722b875a9a` |
| `EURUSD_2012.t6` | `fddade644a594ecd54351a6434e05719c0b36842d6b22c01c00ac361eadb30fe` |
| `EURUSD_2013.t6` | `ffe3689d55ee5ce2ae7f2f6e2183aeff9c02944609a8ba46eabffdc19e8d3996` |
| `EURUSD_2014.t6` | `e242a325fe4062fca38ca9757136ddb20eb37888c739d6c1e26adb8b0ca1696a` |
| `EURUSD_2015.t6` | `6f78a6c1fdd1e6b9f407cc0d1ad588c03f1c7508f29a45d033c018d223e8f7a4` |
| `EURUSD_2016.t6` | `d775bf7223e621505aaba06de87dc622e1a40e7f7ad54a2095c75d2fa8c6e2b3` |
| `EURUSD_2017.t6` | `13384ffecd79326393acb84be356d3b862fd3ca904e2d54891a5899fb90bda72` |
| `EURUSD_2018.t6` | `0d2af41d15487c873f0b24ef1a86553e9d43c65ea069ec94bc07d0da85266e34` |
| `EURUSD_2019.t6` | `10ac41d95b658b34582635d175c9d8dc5462dc1464b8c439da1c6c2db8377335` |
| `EURUSD_2020.t6` | `a8a6202d32c959eb8236d467b50bf706a2b342c1edbdb2a60edc5d1062ce8cbd` |
| `EURUSD_2021.t6` | `664df4948d2d53e19da67b3d1c831fc9345b20fa9c8e830d090d895b260a27a8` |
| `EURUSD_2022.t6` | `860313ad683338ab91dd58c73bad9663f817c60c1953e4ef27a5bd7d560e0b53` |
| `EURUSD_2023.t6` | `bfa83aad0f17fb5102759a7068cbebeb76f9a25482d08258b97ce6c71daa140b` |
| `EURUSD_2024.t6` | `4821817fc9ae074a783faa23aa8e1ab3f66b2c8bfd98f7b60f2edb157298aeb8` |
| `EURUSD_2025.t6` | `f8fce62ef32f3e451a29b256fbe3193ad1aa5e37db943778220b08f817ea9a20` |
| `EURUSD_2026.t6` | `983ad63565b39403da4e24ec130b818acbd3a0de42053bf19bf7566f3d5b0a86` |

## Limitations (c)

- Drawdown is on closed trades only; drawdown inside an open trade is not counted, so the real one can be deeper.
- When total net R is near 0 the swap % is large and unstable; read the swap sum in R.
- The t formula treats signals as independent; a runner can overlap the next signal.
- Disclosure (P-2): no Strategy 2 trade outcome was hand-checked before this read.
