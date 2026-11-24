# PERF1 read 1 — Strategy 1 v0 on this EUR/USD feed

Criteria: `docs/preregistration/PERF1_Strategy1_EURUSD_Criteria.md` (P-1 table, P-3 verdict, P-4). Not a result about EUR/USD in general (P-4.1).

## What ran

- Variants counted: **1** (Strategy 1, variant 0, EUR/USD). x1 / x2 are reporting levels, not variants (P-3).
- Computed by `tools/perf_report.py` from two template logs; half-R and signal-R use the ACTUAL risk (lots x stop pips x PIPCost, SIZE row).

- x1 log: `C:/Zorro/Data/TPL_R1d_log_run1.csv`, sha256 `0590f0b9c9671c329cd9cc3e4f943e96ae72a4976f746303739b9b79bfccdcc1`
- x2 log: `C:/Zorro/Data/TPL_R1c_log_run1.csv`, sha256 `640f8fb4743178afbb2fe7e44958debd14ea626360fee2dc7ca7ca40e75ffede`

## Verdict (spread x2, P-3)

**STOP**

- signals n = 325, mean signal-R = -0.030378, sample sd = 0.628967, **t = -0.8707** (rule t >= 2, (c) a convention)
- total R = -9.8728; best year (exit year) = 2007 with +2.9946; total R with the best year removed = -12.8674
- x1 for reading only (not decisive): t = -0.6761, mean = -0.023511, total R without best year = -10.7840 (would read: STOP)

## Items 1-13 (all signals / standard only / continuation only; x1 and x2)

| Item | all x1 | all x2 | standard x1 | standard x2 | continuation x1 | continuation x2 |
|---|---|---|---|---|---|---|
| 1 signals | 325 | 325 | 256 | 256 | 69 | 69 |
| 1 halves | 650 | 650 | 512 | 512 | 138 | 138 |
| 2 total R (signal-R) | -7.6412 | -9.8728 | -3.6810 | -5.2744 | -3.9602 | -4.5984 |
| 2 mean R per signal | -0.0235 | -0.0304 | -0.0144 | -0.0206 | -0.0574 | -0.0666 |
| 3 mean R per half (all) | -0.0235 | -0.0304 | -0.0144 | -0.0206 | -0.0574 | -0.0666 |
| 3 mean R, TP1 half | -0.0127 | -0.0214 | -0.0064 | -0.0151 | -0.0360 | -0.0449 |
| 3 mean R, runner half | -0.0343 | -0.0394 | -0.0223 | -0.0262 | -0.0788 | -0.0884 |
| 4 win rate (signals, net R > 0) | 44.6% (145/325) | 44.6% (145/325) | 44.1% (113/256) | 44.1% (113/256) | 46.4% (32/69) | 46.4% (32/69) |
| 5 max drawdown, closed halves (signal-R) | 16.9231 | 18.1819 | 10.6312 | 11.6102 | 8.9642 | 9.4604 |
| 6 swap, summed (R) | -3.4829 | -3.5701 | -2.5934 | -2.6806 | -0.8895 | -0.8895 |
| 6 swap, % of total net R | +45.58% | +36.16% | +70.45% | +50.82% | +22.46% | +19.34% |
| 7 spread cost, summed (R, cost positive) | 2.9836 | 5.9672 | 2.3235 | 4.6471 | 0.6601 | 1.3202 |
| 8 same-bar stop + TP1, signals | 2 | 2 | 2 | 2 | 0 | 0 |
| 8 ... resolved by half-1 exit | stop 1, tp1 1 | stop 1, tp1 1 | stop 1, tp1 1 | stop 1, tp1 1 | none | none |
| 9 long TP1 halves | 65 | 65 | 51 | 51 | 14 | 14 |
| 10 exit reason: c1_flip | 267 | 268 | 172 | 173 | 95 | 95 |
| 10 exit reason: baseline | 161 | 161 | 161 | 161 | 0 | 0 |
| 10 exit reason: stop | 43 | 43 | 37 | 37 | 6 | 6 |
| 10 exit reason: tp1 | 125 | 125 | 101 | 101 | 24 | 24 |
| 10 exit reason: be | 46 | 45 | 36 | 35 | 10 | 10 |
| 10 exit reason: trail | 7 | 7 | 4 | 4 | 3 | 3 |
| 10 exit reason: exit_ind | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 exit reason: be_adverse | 1 | 1 | 1 | 1 | 0 | 0 |
| 10 exit reason: end | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 exit reason: other | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 refused: bridge-too-far | 35 | 35 | 35 | 35 | 0 | 0 |
| 11 refused: below 1 lot | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 refused: margin | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 refused: risk above configured | 0 | 0 | 0 | 0 | 0 | 0 |
| 12 total R, exit year 2007 | +3.1428 | +2.9946 | +1.2280 | +1.1238 | +1.9148 | +1.8708 |
| 12 total R, exit year 2008 | +1.6287 | +1.5625 | +1.6942 | +1.6340 | -0.0655 | -0.0714 |
| 12 total R, exit year 2009 | +0.9450 | +0.8536 | +2.1714 | +2.1014 | -1.2264 | -1.2478 |
| 12 total R, exit year 2010 | +0.7888 | +0.7235 | -0.9791 | -1.0305 | +1.7679 | +1.7540 |
| 12 total R, exit year 2011 | -4.9010 | -5.0024 | -2.2514 | -2.3259 | -2.6496 | -2.6766 |
| 12 total R, exit year 2012 | -1.3279 | -1.4300 | -1.2806 | -1.3667 | -0.0473 | -0.0633 |
| 12 total R, exit year 2013 | +1.7278 | +1.6263 | +2.4721 | +2.3998 | -0.7443 | -0.7735 |
| 12 total R, exit year 2014 | -2.7675 | -2.9796 | -2.2443 | -2.3858 | -0.5233 | -0.5938 |
| 12 total R, exit year 2015 | -1.5754 | -1.6605 | -0.3889 | -0.4577 | -1.1865 | -1.2028 |
| 12 total R, exit year 2016 | +2.2264 | +2.0363 | +2.5848 | +2.4184 | -0.3584 | -0.3821 |
| 12 total R, exit year 2017 | -0.2788 | -0.3783 | +0.0013 | -0.0801 | -0.2801 | -0.2981 |
| 12 total R, exit year 2018 | -3.9367 | -4.1380 | -3.0204 | -3.2144 | -0.9163 | -0.9236 |
| 12 total R, exit year 2019 | -4.4711 | -4.0207 | -3.6964 | -3.2287 | -0.7747 | -0.7920 |
| 12 total R, exit year 2020 | +1.9689 | +1.7509 | -0.4454 | -0.6142 | +2.4142 | +2.3651 |
| 12 total R, exit year 2021 | -0.5248 | -0.7267 | +0.5744 | +0.4100 | -1.0991 | -1.1367 |
| 12 total R, exit year 2022 | +0.3819 | +0.2510 | +0.8975 | +0.7746 | -0.5156 | -0.5236 |
| 12 total R, exit year 2023 | -1.9667 | -2.1396 | -2.3346 | -2.4458 | +0.3679 | +0.3062 |
| 12 total R, exit year 2024 | +1.6859 | +1.4580 | +3.0489 | +2.9169 | -1.3630 | -1.4589 |
| 12 total R, exit year 2025 | -0.9703 | -1.1445 | -1.6239 | -1.7508 | +0.6536 | +0.6062 |
| 12 total R, exit year 2026 | +0.5828 | +0.4908 | -0.0887 | -0.1527 | +0.6714 | +0.6435 |
| 13 longs: count, total R | 180, -11.2552 | 180, -12.1578 | 138, -7.4278 | 138, -7.9607 | 42, -3.8274 | 42, -4.1971 |
| 13 shorts: count, total R | 145, +3.6140 | 145, +2.2851 | 118, +3.7468 | 118, +2.6864 | 27, -0.1328 | 27, -0.4013 |

Item 10 counts halves. Item 12: calendar year of the signal's last exit (c: the criteria say 'year of the exit'; a signal is placed whole in the year its last half closed). Item 5: the running sum of half-R x its share of signal risk, in log order within a day, peak starts at 0 (c).

## Information only (never used in a verdict)

| | x1 | x2 |
|---|---|---|
| final equity (EUR, 2025-07-28 rates, M-D8.4), last ACCT row | 83791.81 | 80268.37 |
| max MarginTotal / Equity | 0.0403 | 0.0404 |

## P-4 near-miss table (information only; counts possible flips, R is not recomputed)

Daily bars from the M1 history (r1_data, bar rule of R1). Margin = pips between a bar's extreme and the level, over the half's life (entry bar to exit bar; the exit bar only for level exits). A half 'could flip' under a shift of s pips when some bar stayed within s of a level without crossing it, or crossed it by less than s.

| level | halves | flip at 0.5 pip: stop / TP1 / either | flip at 1 pip: stop / TP1 / either | flip at 2 pip: stop / TP1 / either | closest uncrossed (stop / TP1, pips) | crossed halves (stop / TP1) | smallest overshoot (stop / TP1, pips) |
|---|---|---|---|---|---|---|---|
| x1 | 650 | 3 / 5 / 8 | 3 / 9 / 12 | 9 / 19 / 28 | 0.40 / 0.08 | 97 / 127 | 0.40 / 0.10 |
| x2 | 650 | 3 / 5 / 8 | 3 / 9 / 12 | 9 / 19 / 28 | 0.40 / 0.08 | 96 / 127 | 0.40 / 0.10 |

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
- Disclosure (P-2): the outcomes of 10 R1a trades were seen in Phase 1 step 5; this read is not fully blind.
