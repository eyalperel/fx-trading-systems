#!/usr/bin/env bash
# fetch_binance_klines.sh - download Binance spot monthly klines + CHECKSUM files and verify them (PREM2 data, decision B-a).
# Source (b): https://data.binance.vision (Binance public data; monthly spot kline files from 2017-08, one .CHECKSUM per zip).
# Usage (Git Bash, repo root):  bash tools/fetch_binance_klines.sh [SYMBOL] [INTERVAL] [FIRST_YYYY-MM] [LAST_YYYY-MM]
# Defaults: BTCUSDT 4h 2017-08 2026-10.  Output: data/crypto/binance_<symbol>_<interval>/ (git-ignored by the data/ rule).
# Idempotent: a month whose zip already verifies is skipped. Nothing is overwritten unless it fails its checksum.
# Writes download_log.txt (one line per month: OK / SKIP / MISSING / BADSUM) and exits non-zero if any month is not OK/SKIP.
set -u
SYM="${1:-BTCUSDT}"; IV="${2:-4h}"; FIRST="${3:-2017-08}"; LAST="${4:-2026-10}"
BASE="https://data.binance.vision/data/spot/monthly/klines/${SYM}/${IV}"
OUT="data/crypto/binance_$(echo "$SYM" | tr 'A-Z' 'a-z')_${IV}"
mkdir -p "$OUT"
LOG="$OUT/download_log.txt"
: > "$LOG"
bad=0
y=${FIRST%-*}; m=$((10#${FIRST#*-}))
ly=${LAST%-*}; lm=$((10#${LAST#*-}))
while [ "$y" -lt "$ly" ] || { [ "$y" -eq "$ly" ] && [ "$m" -le "$lm" ]; }; do
  mm=$(printf "%02d" "$m")
  f="${SYM}-${IV}-${y}-${mm}.zip"
  verify() { (cd "$OUT" && sha256sum -c "$f.CHECKSUM" >/dev/null 2>&1); }
  if [ -f "$OUT/$f" ] && [ -f "$OUT/$f.CHECKSUM" ] && verify; then
    echo "$y-$mm SKIP" >> "$LOG"
  else
    curl -sf "$BASE/$f" -o "$OUT/$f.part" && curl -sf "$BASE/$f.CHECKSUM" -o "$OUT/$f.CHECKSUM"
    if [ $? -ne 0 ]; then
      echo "$y-$mm MISSING" >> "$LOG"; rm -f "$OUT/$f.part"; bad=$((bad+1))
    else
      mv -f "$OUT/$f.part" "$OUT/$f"
      if verify; then echo "$y-$mm OK" >> "$LOG"; else echo "$y-$mm BADSUM" >> "$LOG"; bad=$((bad+1)); fi
    fi
  fi
  m=$((m+1)); if [ "$m" -gt 12 ]; then m=1; y=$((y+1)); fi
done
echo "months: $(wc -l < "$LOG"), not OK: $bad  ->  $LOG"
grep -v -E " (OK|SKIP)$" "$LOG" || true
[ "$bad" -eq 0 ]
