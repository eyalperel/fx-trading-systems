# Dev-set data: BTC/USD H4 = Binance spot BTCUSDT 4h (2026-11-27)

**Decision:** N5 (2026-11-27, user: as recommended): a PREM1-style premise test on BTC H4 first (PREM2); data source **B-a**.
Labels: (a) source states, (b) measurable, (c) inference.

## Source

- (a) Binance public data, https://data.binance.vision: spot monthly kline files, one `.CHECKSUM` (sha256) per zip; monthly spot
  candlestick files from 2017-08-15 (Binance FAQ "How to Download Historical Market Data"); spot timestamps from 2025-01-01 in
  microseconds (binance-public-data README).
- Symbol **BTCUSDT**, interval **4h**, months 2017-08 .. 2026-10. (c) The quote currency is USDT, not USD; the USDT/USD basis is
  small but not zero. From here on the dev-set entry "BTC/USD H4" (PROJECT_STATE §2.1) means Binance BTCUSDT H4.
- Replaces the August 2026 Kaggle-CSV BTC/USD H4 file (2020-01 .. 2024-12, 7,534 bars; `Data_Availability_2026-08-12.md`),
  which is no longer on disk and whose provenance was unknown.

## Download and guards

- `tools/fetch_binance_klines.sh` (Git Bash, user's machine; the VM shell has no internet): 111 months, every zip verified
  against its `.CHECKSUM`; log `download_log.txt`; files in `data/crypto/binance_btcusdt_4h/` (git-ignored by `data/`).
- Run 1: `months: 111, not OK: 0`.
- Guards seen to fire (b): **MISSING** (2017-07, before the source starts: `MISSING`, exit 1); **BADSUM / repair** (one byte
  appended to `BTCUSDT-4h-2021-05.zip`: its CHECKSUM rejected it; the re-run re-downloaded that month only (110 SKIP + 1 OK) and
  the hash returned to the original `6fe459a0c90e5712...`).
- Manifest: `docs/research/Data_BTCUSDT_H4_Binance_manifest.csv` (sha256 of all 111 zips; equal to their `.CHECKSUM` files).

## Bar check (b), all 111 files

| Check | Result |
|---|---|
| Bars | 20,160 |
| Span (UTC, bar open times) | 2017-08-17 04:00 .. 2026-10-31 20:00 |
| Timestamp units | ms 16,146 bars (to 2024-12), us 4,014 (2025 on) |
| Header rows / duplicates / non-increasing / off the 4h UTC grid / outside the file month | 0 / 0 / 0 / 0 / 0 |
| OHLC violations (low <= min(open, close), high >= max(open, close), low > 0) | 0 |
| Gaps > 4h | 9 (17 bars missing), all before 2020-03: 2017-09-06 12:00 (8h), **2018-02-08 00:00 (32h)**, 2018-06-26 (12h), 2018-07-04 (8h), 2018-11-14 (8h), 2019-03-12 (8h), 2019-05-15 (12h), 2019-08-15 (8h), 2020-02-19 08:00 (8h) |

(c) Gaps are probably exchange downtime; no cause is claimed. How returns across them are treated is a PREM2 decision.
