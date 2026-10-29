#!/usr/bin/env bash
# fetch_transcripts.sh — download English auto-captions (.vtt) for the NNFX and
# Stonehill Forex source playlists. Text only; no video is downloaded.
#
# Output goes OUTSIDE the repo (~/Documents/nnfx_sources) because the transcripts
# are third-party content and the repo is public. Only our own summaries, citing
# video URLs, go into the repo.
#
# Safe to rerun: --no-overwrites skips transcripts already on disk, so each rerun
# only retries the gaps (temporary failures, e.g. HTTP 429). Rerun until the
# per-folder counts stop rising; what remains are videos with no English captions.
#
# Usage:  bash tools/fetch_transcripts.sh
# Requires: yt-dlp[default] and Deno on PATH (see PROJECT_STATE / session 2026-10-21).

set -u
ROOT="$HOME/Documents/nnfx_sources"

# Source: VP / No Nonsense Forex — https://www.youtube.com/@NoNonsenseForex/playlists
NNFX_PLAYLISTS=(
  "PLPqWQo6-TXfHyC12MRHK5doA5oUeGwpkV"   # 35 videos
  "PLPqWQo6-TXfE_EEypsX7-by2qub_S09WN"   # 164 videos
  "PLPqWQo6-TXfE8G_Mmxow0znSSoWTu44e7"   # 14 videos (Forex Money Management)
)

# Source: Stonehill Forex — https://www.youtube.com/@stonehillforex7998/playlists
STONEHILL_PLAYLISTS=(
  "PL43bczXny0XqW_nb000jm3AzB1W7WWgV8"
  "PL43bczXny0XoJ2Abalbem60WA-ynCypIh"
  "PL43bczXny0XrdX0bWb7kRxC6itS8sRE8A"
  "PL43bczXny0XoOVSptL_ap-3GIDZUS2mq-"
  "PL43bczXny0XqQuiKmJUT97UxeS6H-dy17"
)

fetch() {   # $1 = output subfolder, remaining args = playlist ids
  local dest="$ROOT/$1"; shift
  mkdir -p "$dest"
  for pl in "$@"; do
    echo "=== $(date +%H:%M:%S)  $dest  playlist $pl"
    ( cd "$dest" && yt-dlp \
        --skip-download --write-auto-subs --sub-langs "en" --sub-format vtt \
        --sleep-subtitles 5 --sleep-requests 1 \
        --ignore-errors --no-overwrites --restrict-filenames \
        -o "%(playlist_title)s/%(playlist_index)03d_%(id)s_%(title)s.%(ext)s" \
        "https://www.youtube.com/playlist?list=$pl" 2>&1 \
      | grep -E "ERROR|no subtitles|Writing video subtitles|Downloading item" )
  done
}

fetch nnfx      "${NNFX_PLAYLISTS[@]}"
fetch stonehill "${STONEHILL_PLAYLISTS[@]}"

echo
echo "=== transcript count per playlist folder"
for d in "$ROOT"/nnfx/*/ "$ROOT"/stonehill/*/; do
  [ -d "$d" ] && printf "%5d  %s\n" "$(find "$d" -name '*.vtt' | wc -l)" "${d#$ROOT/}"
done
printf "%5d  TOTAL\n" "$(find "$ROOT" -name '*.vtt' | wc -l)"
