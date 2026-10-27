"""
Chapter Linter — Writer's Constitution enforcement (the fast, dumb layer)
=========================================================================
Scans chapter .md files for mechanical rule breaks and reports them with
line numbers. This is the cheap check that runs after every chapter. It
catches the OBVIOUS violations (modern words, the secret orgs named on the
page, past-life leaks, unknown character names). It cannot catch the subtle
ones (Casian bypassing his father, Argius being too warm, a system appearing
from thin air) — those are for the reviewer-agent pass. See
story/writers_constitution.md.

Two tiers:
  ERROR — a hard break. Unambiguously modern / a named secret org / a past-life
          leak. Exit code is non-zero if any ERROR is found (so a pipeline can
          gate on it).
  WARN  — a modern-register word that is a break in dialogue/narration but is
          ALLOWED in an Argius line or Casian's private internal thought. The
          linter can't tell which, so it shows the line and you judge.

Usage:
    python check_chapter.py                                   # all chapters, all volumes
    python check_chapter.py --volume 1                        # only volume 1
    python check_chapter.py story/volume_01/chapters/ch_005.md  # one file (or several)

Entity check:
    If story/canon/roster.txt exists (one canonical name per line, '#' comments
    allowed), any name in a chapter's `characters:` frontmatter that is not in
    the roster is reported as an ERROR. If the file is missing, the entity check
    is skipped with a note. (The roster is the "continuity anchor" step.)

No external dependencies — plain file reading + regex, runs anywhere.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORY_DIR = ROOT / "a_god_in_the_garden"
ROSTER_FILE = STORY_DIR / "canon" / "roster.txt"

# ─── Rule sets ────────────────────────────────────────────────────────────────

# ERROR: unambiguously modern, or a secret-org name, or a past-life leak.
# Each entry: (compiled regex, label). Case-sensitive where noted.
ERROR_PATTERNS = [
    # Secret organisations named on the page (proper-noun form: capital Q / L).
    (re.compile(r"\bthe Quiet\b"),      "secret-org"),
    (re.compile(r"\bThe Quiet\b"),      "secret-org"),
    (re.compile(r"\bthe Ledger\b"),     "secret-org"),
    (re.compile(r"\bThe Ledger\b"),     "secret-org"),
    # Past-life / reincarnation leaks.
    (re.compile(r"reincarnat\w*", re.I),          "past-life"),
    (re.compile(r"\bpast life\b", re.I),          "past-life"),
    (re.compile(r"\bprevious life\b", re.I),      "past-life"),
    (re.compile(r"\bformer life\b", re.I),        "past-life"),
    (re.compile(r"\bIndia\b"),                    "past-life"),
    (re.compile(r"\b2[01]st[- ]century\b", re.I), "past-life"),
    (re.compile(r"\btwenty[- ]?first century\b", re.I), "past-life"),
    # Unambiguously modern nouns (too modern even for internal thought).
    (re.compile(r"\bsoftware\b", re.I),      "anachronism"),
    (re.compile(r"\balgorithm\w*", re.I),    "anachronism"),
    (re.compile(r"\bdatabase\w*", re.I),     "anachronism"),
    (re.compile(r"\bcomputers?\b", re.I),    "anachronism"),
    (re.compile(r"\btechnolog\w*", re.I),    "anachronism"),
    (re.compile(r"\bCEO\b"),                 "anachronism"),
    (re.compile(r"\bAI\b"),                  "anachronism"),
]

# WARN: modern-register words. A break in dialogue/narration, but fine in an
# Argius line or Casian's internal thought — you judge each.
WARN_PATTERNS = [
    (re.compile(r"\befficien\w*", re.I),   "register"),
    (re.compile(r"\boptimi[sz]\w*", re.I), "register"),
    (re.compile(r"\bsystems?\b", re.I),    "register"),
    (re.compile(r"\bnetworks?\b", re.I),   "register"),
    (re.compile(r"\bdata\b", re.I),        "register"),
    (re.compile(r"\bmetrics?\b", re.I),    "register"),
    (re.compile(r"\bprobabilit\w*", re.I), "register"),
    (re.compile(r"\blogistics?\b", re.I),  "register"),
    (re.compile(r"\bprotocols?\b", re.I),  "register"),
    (re.compile(r"\bengineer\w*", re.I),   "register"),
    (re.compile(r"\bcompan(y|ies)\b", re.I), "register"),
    (re.compile(r"\bpercent\b", re.I),     "register"),
    (re.compile(r"%"),                     "register"),
]

# ─── File handling ────────────────────────────────────────────────────────────

def body_start_line(lines: list[str]) -> int:
    """Return the 1-based line number where the prose body begins (after any
    YAML frontmatter block delimited by --- ... ---)."""
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return i + 2  # first line after the closing ---
    return 1


def frontmatter_characters(lines: list[str]) -> list[str]:
    """Pull the `characters:` list from frontmatter, if present. Handles the
    inline form `characters: [A, B]` (the format the RAG indexer expects)."""
    if not (lines and lines[0].strip() == "---"):
        return []
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            break
        m = re.match(r"\s*characters:\s*\[(.*)\]\s*$", lines[i])
        if m:
            return [n.strip().strip("'\"") for n in m.group(1).split(",") if n.strip()]
    return []


def load_roster() -> set[str] | None:
    if not ROSTER_FILE.exists():
        return None
    names = set()
    for line in ROSTER_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.add(line)
    return names


def collect_files(paths: list[str], volume: int | None) -> list[Path]:
    if paths:
        return [Path(p) for p in paths]
    files = sorted(STORY_DIR.glob("volume_*/chapters/ch_*.md"))
    if volume is not None:
        files = [f for f in files if f"volume_{volume:02d}" in str(f)]
    return files

# ─── Checking ─────────────────────────────────────────────────────────────────

def check_file(path: Path, roster: set[str] | None) -> tuple[list, list]:
    """Return (errors, warns), each a list of (line_no, label, text)."""
    errors, warns = [], []
    if not path.exists():
        errors.append((0, "missing-file", f"{path} does not exist"))
        return errors, warns

    lines = path.read_text(encoding="utf-8").splitlines()
    start = body_start_line(lines)

    # Entity check (frontmatter, whole file).
    if roster is not None:
        for name in frontmatter_characters(lines):
            if name not in roster:
                errors.append((1, "unknown-character",
                               f"'{name}' is not in the roster (typo? new character? wrong relationship?)"))

    # Prose checks (body only).
    for idx in range(start - 1, len(lines)):
        text = lines[idx]
        if not text.strip():
            continue
        line_no = idx + 1
        for rx, label in ERROR_PATTERNS:
            if rx.search(text):
                errors.append((line_no, label, text.strip()))
        for rx, label in WARN_PATTERNS:
            if rx.search(text):
                warns.append((line_no, label, text.strip()))
    return errors, warns


def fmt(items: list, kind: str) -> list[str]:
    out = []
    for line_no, label, text in items:
        snippet = text if len(text) <= 100 else text[:97] + "..."
        loc = f"line {line_no}" if line_no else "frontmatter"
        out.append(f"  {kind:5}  {loc:>10}  [{label}]  {snippet}")
    return out

# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Lint chapters against the Writer's Constitution.")
    ap.add_argument("paths", nargs="*", help="Specific chapter files (default: all).")
    ap.add_argument("--volume", type=int, help="Only this volume number.")
    args = ap.parse_args()

    roster = load_roster()
    files = collect_files(args.paths, args.volume)

    if not files:
        print("No chapter files found. (Nothing written yet — that's fine.)")
        return 0

    if roster is None:
        print(f"[note] No roster at {ROSTER_FILE.relative_to(ROOT)} - entity check skipped.\n")

    total_err = total_warn = 0
    for path in files:
        errors, warns = check_file(path, roster)
        total_err += len(errors)
        total_warn += len(warns)
        if errors or warns:
            try:
                shown = path.relative_to(ROOT)
            except ValueError:
                shown = path
            print(str(shown))
            for line in fmt(errors, "ERROR"):
                print(line)
            for line in fmt(warns, "WARN"):
                print(line)
            print()

    print(f"- {len(files)} file(s) checked: {total_err} error(s), {total_warn} warning(s).")
    if total_warn:
        print("  (WARN items inside an Argius line or Casian's internal thought are allowed - judge each.)")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
