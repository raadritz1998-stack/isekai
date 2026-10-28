#!/usr/bin/env python3
"""
Chapter Linter — deterministic quality, canon, register, and style gate.

Checks:
  1. Frontmatter completeness and validity (year, pov, characters).
  2. Banned modern register words (Constitution Rule 14).
  3. Overused AI syntactic crutches ('the way [X]', ', which was', etc.).
  4. Lazy tautological placeholders ('noise it made', 'colour it goes', etc.).
  5. Chapter-specific forbidden names/locks (e.g., premature Hask in ch. 1).
  6. Word count target bounds (3,000–4,500 words).
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "canon"

BANNED_WORDS = [
    r"\befficiency\b",
    r"\boptimiz(?:e|ed|ing|ation)\b",
    r"\bsystems?\b",
    r"\bnetworks?\b",
    r"\bdata\b",
    r"\bmetrics?\b",
    r"\bprobabilit(?:y|ies)\b",
    r"\blogistics?\b",
    r"\bprotocols?\b",
    r"\bengineering\b",
    r"\bpercent(?:age)?\b",
    r"\bsoftware\b",
    r"\balgorithms?\b",
    r"\bdatabases?\b",
    r"\bcomputers?\b",
    r"\btechnolog(?:y|ies)\b",
    r"\binterfaces?\b",
    r"\bprocess(?:es)?\b",
    r"\bcapacity\b",
    r"\bbandwidth\b",
    r"\bpragmatic\b",
    r"\bCEO\b",
    r"\bAI\b",
]

AI_CLICHES = [
    (r"\bwith (?:her|his|their) whole face\b", "Cliche 'with [her/his] whole face'"),
    (r"\bspecific (?:silence|stillness) of\b", "Formulaic 'specific silence/stillness of'"),
    (r"\bthe noise (?:it|they) made\b", "Tautology: 'the noise it made'"),
    (r"\bthe colou?r (?:it goes|it went|they go)\b", "Tautology: 'the colour it goes'"),
    (r"\bdid what (?:it|mornings|days) do\b", "Tautology: 'did what [mornings/days] do'"),
    (r"\bthings that had names\b", "Vague pseudo-profound: 'things that had names'"),
    (r"\bnot,?\s+yet,?\s+untrue\b", "Clunky negative: 'not, yet, untrue'"),
    (r"\bwhat (?:a )?childhood is for\b", "Unearned pseudo-wisdom: 'what childhood is for'"),
]

# Max permitted frequency of repetitive syntactic ticks per chapter
MAX_THE_WAY_COUNT = 4
MAX_WHICH_WAS_COUNT = 4


def parse_frontmatter(text):
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
            k = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                items = [x.strip() for x in v[1:-1].split(",") if x.strip()]
                fm[k] = items
            else:
                try:
                    fm[k] = int(v)
                except ValueError:
                    fm[k] = v
    return fm, body


def lint_chapter(path: Path, forbidden_names=None):
    issues = []
    warnings = []

    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    # 1. Frontmatter checks
    for req in ["chapter", "title", "volume", "year", "pov", "characters"]:
        if req not in fm:
            issues.append(f"Missing frontmatter key: '{req}'")

    if "year" in fm and fm["year"] != 1217 and fm.get("volume") == 1:
        issues.append(f"Volume 1 year must be 1217, found {fm['year']}")

    # 2. Word count check
    words = len(re.findall(r"\b\w+\b", body))
    if words < 2500:
        issues.append(f"Word count too low: {words} words (minimum target is 3,000)")
    elif words < 3000:
        warnings.append(f"Word count slightly short: {words} words (ideal range: 3,000–4,500)")
    elif words > 4800:
        warnings.append(f"Word count long: {words} words (ideal range: 3,000–4,500)")

    # 3. Banned modern register words
    for pat in BANNED_WORDS:
        matches = re.finditer(pat, body, re.IGNORECASE)
        for m in matches:
            # Check line context
            start = max(0, body.rfind("\n", 0, m.start()))
            end = body.find("\n", m.end())
            line = body[start:end].strip() if end != -1 else body[start:].strip()
            issues.append(f"Banned register word '{m.group(0)}' found: '{line}'")

    # Check for 'company' as business
    for m in re.finditer(r"\bcompany\b", body, re.IGNORECASE):
        # Allow 'pleasant company' or 'in the company of'
        snippet = body[max(0, m.start()-20):min(len(body), m.end()+20)].strip()
        warnings.append(f"Check usage of 'company': '{snippet}' (banned if used as a business)")

    # 4. Forbidden names per chapter lock
    if forbidden_names:
        for name in forbidden_names:
            matches = list(re.finditer(rf"\b{re.escape(name)}\b", body, re.IGNORECASE))
            if matches:
                issues.append(f"Forbidden entity '{name}' mentioned {len(matches)} times (locked for this chapter)!")

    # 5. Overused syntactic ticks
    the_way_matches = list(re.finditer(r"\bthe way (?:a|the|he|she|it|men|people|\w+)\b", body, re.IGNORECASE))
    if len(the_way_matches) > MAX_THE_WAY_COUNT:
        issues.append(f"AI syntax crutch 'the way [X]' used {len(the_way_matches)} times (max allowed: {MAX_THE_WAY_COUNT})")

    which_was_matches = list(re.finditer(r",\s*which was\b", body, re.IGNORECASE))
    if len(which_was_matches) > MAX_WHICH_WAS_COUNT:
        issues.append(f"AI syntax crutch ', which was' used {len(which_was_matches)} times (max allowed: {MAX_WHICH_WAS_COUNT})")

    # 6. Specific AI clichés and tautologies
    for pat, desc in AI_CLICHES:
        for m in re.finditer(pat, body, re.IGNORECASE):
            issues.append(f"AI prose defect: {desc} -> '{m.group(0)}'")

    return issues, warnings, words, fm


def main():
    parser = argparse.ArgumentParser(description="Chapter Linter for A God in the Garden")
    parser.add_argument("chapter_path", type=str, help="Path to chapter markdown file")
    parser.add_argument("--forbid", nargs="*", default=[], help="Forbidden names for this chapter")
    args = parser.parse_args()

    path = Path(args.chapter_path)
    if not path.exists():
        print(f"Error: File '{path}' does not exist.")
        sys.exit(1)

    issues, warnings, words, fm = lint_chapter(path, forbidden_names=args.forbid)

    print("=" * 60)
    print(f"LINTER REPORT: {path.name}")
    print(f"Title: {fm.get('title', 'Unknown')} | POV: {fm.get('pov', 'Unknown')} | Words: {words}")
    print("=" * 60)

    if warnings:
        print(f"\n[WARNINGS ({len(warnings)})]:")
        for w in warnings:
            print(f"  ? {w}")

    if issues:
        print(f"\n[ERRORS / ISSUES ({len(issues)})]:")
        for i in issues:
            print(f"  X {i}")
        print("\nRESULT: FAILED")
        sys.exit(1)
    else:
        print("\nRESULT: PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
