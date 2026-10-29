"""
vtt_to_text.py — convert YouTube auto-caption .vtt files to plain readable text.

Why: YouTube auto-captions repeat each phrase ~3 times (once with per-word
timing tags, then as plain text while the caption scrolls). Agents read the
cleaned text faster and more accurately, and it is ~10x smaller.

Method:
  1. Drop the header, timestamp lines and blank lines.
  2. Strip inline tags such as <00:00:01.040> and <c>...</c>.
  3. Drop a line if it equals the previous kept line (removes the scroll repeats).
  4. Join into paragraphs of ~12 lines for readability.

Usage:
  python tools/vtt_to_text.py <input_folder> <output_folder>
Walks <input_folder> recursively and mirrors its subfolders (one per playlist).
File names are [NNN_]<id>_<title>.en.vtt, where NNN is the playlist position
(optional) and <id> is the 11-character YouTube id. Each becomes a .txt with a
header giving title, playlist position, id and URL, so every summary can cite
its source video.
"""
import re
import sys
from pathlib import Path

TAG = re.compile(r"<[^>]+>")                 # <00:00:01.040>, <c>, </c>
TIMESTAMP = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ")
HEADER = ("WEBVTT", "Kind:", "Language:")
# [NNN_]<11-char id>_<title>  — playlist position is optional
NAME = re.compile(r"^(?:(\d{3})_)?([A-Za-z0-9_-]{11})_(.*)$")


def clean_vtt(text: str) -> list[str]:
    """Return the caption text as a list of unique consecutive lines."""
    kept: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(HEADER) or TIMESTAMP.match(line):
            continue
        line = TAG.sub("", line).strip()
        line = re.sub(r"\s+", " ", line)
        if line and (not kept or line != kept[-1]):
            kept.append(line)
    return kept


def to_paragraphs(lines: list[str], per_para: int = 12) -> str:
    chunks = [" ".join(lines[i:i + per_para]) for i in range(0, len(lines), per_para)]
    return "\n\n".join(chunks)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: python vtt_to_text.py <input_folder> <output_folder>")
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    files = sorted(src.rglob("*.vtt"))
    if not files:
        sys.exit(f"no .vtt files found in {src}")
    skipped = 0
    for f in files:
        stem = f.name.rsplit(".", 2)[0]            # drop ".en.vtt"
        m = NAME.match(stem)
        if not m:
            print(f"SKIP (unrecognised name): {f}")
            skipped += 1
            continue
        position, video_id, title = m.group(1), m.group(2), m.group(3).replace("_", " ")
        body = to_paragraphs(clean_vtt(f.read_text(encoding="utf-8")))
        header = (f"VIDEO: {title}\n"
                  + (f"PLAYLIST POSITION: {int(position)}\n" if position else "")
                  + f"ID: {video_id}\nURL: https://www.youtube.com/watch?v={video_id}\n\n")
        out = dst / f.parent.relative_to(src) / (stem + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(header + body + "\n", encoding="utf-8")
        print(f"{f.stat().st_size:>8} -> {out.stat().st_size:>7} bytes  {out.relative_to(dst)}")
    print(f"done: {len(files) - skipped} converted, {skipped} skipped")


if __name__ == "__main__":
    main()
