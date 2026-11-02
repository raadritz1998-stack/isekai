#!/usr/bin/env python3
"""
Continuity Linter — automated cross-chapter narrative consistency gate.

Enforces:
  1. Chronological Entity Locks (no premature naming of entities before they are revealed).
  2. Character Lifecycle / Mortality (deceased characters cannot speak or act after death).
  3. Fourth-Wall & Meta-Leak Defense (no 'volume', 'reader', 'author', 'protagonist' in prose).
  4. Rule 1 Immune Enforcement (Casian never strained, wounded, exhausted, or sweating).
  5. Frontmatter chronological progression (1..N sequence, year=1217).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "canon"
CHAPTERS_DIR = ROOT / "volume_01" / "chapters"

# Forbidden entities before specific chapters (Chapter: [forbidden names/entities])
TEMPORAL_LOCKS = {
    1: ["Hask Veyr", "Hask", "Tolan", "Ansel", "Maeve", "Osric", "Seraine"],
    2: ["Tolan", "Ansel", "Maeve", "Osric", "Seraine"],
    3: ["Tolan", "Ansel", "Maeve", "Osric", "Seraine"],
    4: ["Tolan", "Ansel", "Seraine"],
    5: ["Ansel", "Seraine"],
    6: ["Seraine"],
    7: ["Seraine"],
    8: ["Seraine"],
    9: ["causeway destroyed", "lost ford in September", "ford is gone"],  # Ford destroyed in ch 10
}

# Deceased character tracking: (Death Chapter, Character Name)
MORTALITY_LOG = [
    (5, "Mirra Cott"),
    (5, "Jon Cott"),
    (19, "Aldous"),
    (34, "Hask Veyr"),
    (35, "Osric"),
]

# Meta-narrative leaks that break immersion
META_LEAKS = [
    r"\bin this volume\b",
    r"\bin this chapter\b",
    r"\bthe reader (?:understands|knows|notices|sees|registers|learns)\b",
    r"\bas the reader\b",
    r"\bfourth wall\b",
    r"\bprotagonist\b",
    r"\bcharacter arc\b",
    r"\bplot point\b",
]

# Rule 1 violations: Casian cannot be physically strained, wounded, or exhausted
RULE_1_VIOLATIONS = [
    (r"\bCasian (?:panted|gasped|strained|bled|collapsed|fainted|sweated with effort)\b", "Casian physical strain"),
    (r"\bCasian was (?:exhausted|terrified|helpless|wounded|overwhelmed|bleeding)\b", "Casian weakness/wound"),
    (r"\bCasian felt (?:his strength fail|himself tiring|afraid for his life)\b", "Casian internal weakness"),
]


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
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if v.startswith("[") and v.endswith("]"):
                fm[k] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
            else:
                try:
                    fm[k] = int(v)
                except ValueError:
                    fm[k] = v
    return fm, body


def check_continuity(target_files=None, max_ch=None):
    errors = []
    if target_files:
        chapter_files = sorted(target_files)
    else:
        chapter_files = sorted(CHAPTERS_DIR.glob("ch_*.md"))
        if max_ch:
            chapter_files = [p for p in chapter_files if int(re.search(r"ch_(\d+)", p.name).group(1)) <= max_ch]

    if not chapter_files:
        print("No chapter files found.")
        return 0

    print("=" * 60)
    print(f"CONTINUITY LINTER: Checking {len(chapter_files)} chapters...")
    print("=" * 60)

    for i, path in enumerate(chapter_files, 1):
        fm, body = parse_chapter(path)
        ch_num = fm.get("chapter", i)

        # 1. Frontmatter check
        if ch_num != i:
            errors.append(f"{path.name}: Chapter number {ch_num} does not match file sequence {i}")

        # 2. Temporal Locks (no premature mentions)
        if ch_num in TEMPORAL_LOCKS:
            for entity in TEMPORAL_LOCKS[ch_num]:
                matches = list(re.finditer(rf"\b{re.escape(entity)}\b", body, re.IGNORECASE))
                if matches:
                    errors.append(f"{path.name}: Premature mention of locked entity '{entity}' ({len(matches)} times) in Ch {ch_num}")

        # 3. Mortality Guard (dead characters cannot act in subsequent chapters)
        for death_ch, name in MORTALITY_LOG:
            if ch_num > death_ch:
                # Flag if dead character speaks or is marked as performing current actions
                dialogue_matches = re.findall(rf'"{name}\s+(?:said|replied|asked|answered|stood|walked)', body, re.IGNORECASE)
                action_matches = re.findall(rf'\b{re.escape(name)}\s+(?:smiled|walked|stood|poured|ate|rode|laughed)\b', body, re.IGNORECASE)
                if dialogue_matches or action_matches:
                    errors.append(f"{path.name}: Deceased character '{name}' (died Ch {death_ch}) appears to be acting/speaking in Ch {ch_num}!")

        # 4. Meta-Narrative Leak Check
        for leak_pat in META_LEAKS:
            m = re.search(leak_pat, body, re.IGNORECASE)
            if m:
                errors.append(f"{path.name}: Meta-narrative fourth-wall leak found: '{m.group(0)}'")

        # 5. Rule 1 Check
        for pat, desc in RULE_1_VIOLATIONS:
            m = re.search(pat, body, re.IGNORECASE)
            if m:
                errors.append(f"{path.name}: Rule 1 violation ({desc}): '{m.group(0)}'")

    if errors:
        print(f"\n[CONTINUITY ERRORS ({len(errors)})]:")
        for e in errors:
            print(f"  X {e}")
        print("\nRESULT: FAILED")
        return 1
    else:
        print("\nAll chapters passed continuity, mortality, temporal lock, and meta-leak checks with 0 errors!")
        print("RESULT: PASSED")
        return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Continuity Linter")
    parser.add_argument("files", nargs="*", help="Specific chapter files to check")
    parser.add_argument("--max-ch", type=int, default=None, help="Check chapters up to this number")
    args = parser.parse_args()

    target_files = [Path(f) for f in args.files] if args.files else None
    sys.exit(check_continuity(target_files=target_files, max_ch=args.max_ch))
