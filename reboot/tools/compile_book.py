#!/usr/bin/env python3
"""
Book Compiler — merges chapters into a clean, seamless single manuscript for reading.

Usage:
  python tools/compile_book.py [--up-to 12] [--output A_God_in_the_Garden_Act_1.md]
"""

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = ROOT / "volume_01" / "chapters"


def parse_chapter(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw_fm = parts[1].strip()
    body = parts[2].strip()

    fm = {}
    for line in raw_fm.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


def compile_book(up_to=None, output_path=None):
    chapter_files = sorted(CHAPTERS_DIR.glob("ch_*.md"))
    if up_to:
        chapter_files = [p for p in chapter_files if int(re.search(r"ch_(\d+)", p.name).group(1)) <= up_to]

    if not output_path:
        output_path = ROOT / (f"A_God_in_the_Garden_Act_1.md" if up_to == 12 else "A_God_in_the_Garden_Volume_1.md")
    else:
        output_path = ROOT / Path(output_path).name

    manuscript = []
    manuscript.append("# A God in the Garden")
    manuscript.append("## Volume 1: *The Gardener*")
    manuscript.append("\n---\n")

    for p in chapter_files:
        fm, body = parse_chapter(p)
        ch_num = fm.get("chapter", p.stem.replace("ch_", ""))
        title = fm.get("title", "Untitled")
        pov = fm.get("pov", "")

        manuscript.append(f"\n# Chapter {ch_num}: {title}\n")
        if pov:
            manuscript.append(f"*(POV: {pov})*\n")
        manuscript.append(body)
        manuscript.append("\n\n---\n")

    full_text = "\n".join(manuscript)
    output_path.write_text(full_text, encoding="utf-8")
    print(f"[OK] Compiled {len(chapter_files)} chapters ({len(full_text.split())} words) into '{output_path.name}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--up-to", type=int, default=40)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    out = Path(args.output) if args.output else None
    compile_book(up_to=args.up_to, output_path=out)
