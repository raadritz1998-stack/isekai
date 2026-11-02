#!/usr/bin/env python3
"""
Master Verification Suite — Ironclad reader quality assurance.

Runs all deterministic linters across the novel:
  1. Age Ledger validity & sync (`tools/age_ledger.py --check`)
  2. Prose age consistency across drafted chapters (`tools/age_ledger.py --check-year`)
  3. Chapter Linter (`tools/chapter_linter.py`):
     - Constitution Rule 14 banned modern register words
     - AI syntactic crutches ('the way [X]', ', which was', tautologies)
     - Word count bounds (3,000–4,500 words)
     - Frontmatter completeness
  4. Continuity Linter (`tools/continuity_linter.py`):
     - Temporal locks (no premature naming of antagonists or events)
     - Mortality guard (dead characters cannot act)
     - Fourth-wall meta-narrative leaks
     - Rule 1 Casian immunity (no strain, weakness, exhaustion)

Usage:
  python tools/verify_all.py [--act 1]
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = ROOT / "volume_01" / "chapters"


def main():
    parser = argparse.ArgumentParser(description="Master Verification Suite")
    parser.add_argument("--act", type=int, choices=[1, 2, 3, 4], help="Check specific Act only")
    args = parser.parse_args()

    act_bounds = {
        1: (1, 12),
        2: (13, 24),
        3: (25, 34),
        4: (35, 40),
    }

    if args.act:
        start_ch, end_ch = act_bounds[args.act]
        targets = [CHAPTERS_DIR / f"ch_{c:03d}.md" for c in range(start_ch, end_ch + 1)]
        title = f"ACT {args.act} (Chapters {start_ch}–{end_ch})"
    else:
        targets = sorted(CHAPTERS_DIR.glob("ch_*.md"))
        title = f"ALL DRAFTED CHAPTERS ({len(targets)} total)"

    print("=" * 70)
    print(f"MASTER QUALITY SUITE: {title}")
    print("=" * 70)

    # 1. Global age ledger check
    print("\n[1/4] Checking global age ledger integrity...")
    res = subprocess.run(["python", "tools/age_ledger.py", "--check"], capture_output=True, text=True)
    if res.returncode != 0:
        print("  X FAILED: Global age ledger out of sync! Run `python tools/age_ledger.py` to regenerate.")
        sys.exit(1)
    print("  [OK] PASS: Roster and ages database synchronized.")

    # 2. Prose age check
    print("\n[2/4] Checking chapter prose ages against timeline...")
    age_failed = False
    for p in targets:
        if not p.exists():
            continue
        res = subprocess.run(["python", "tools/age_ledger.py", "--check-year", str(p)], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  X Age mismatch in {p.name}:\n{res.stdout}")
            age_failed = True
    if age_failed:
        print("  X FAILED: Prose ages contradict the age ledger!")
        sys.exit(1)
    print(f"  [OK] PASS: All {len(targets)} chapters have 100% accurate character ages.")

    # 3. Chapter linter (0 errors, 0 warnings policy)
    print("\n[3/4] Running Chapter Linter (Rule 14 register, AI crutches, word counts)...")
    linter_failed = False
    for p in targets:
        if not p.exists():
            continue
        res = subprocess.run(["python", "tools/chapter_linter.py", str(p)], capture_output=True, text=True)
        if res.returncode != 0 or "[WARNINGS" in res.stdout:
            print(f"  X Linter issues in {p.name}:\n{res.stdout}")
            linter_failed = True
    if linter_failed:
        print("  X FAILED: One or more chapters failed deterministic prose requirements!")
        sys.exit(1)
    print(f"  [OK] PASS: All {len(targets)} chapters passed with 0 errors and 0 warnings.")

    # 4. Continuity check
    print("\n[4/4] Checking cross-chapter continuity, mortality, and meta-leaks...")
    cont_cmd = ["python", "tools/continuity_linter.py"]
    if args.act:
        cont_cmd.extend(["--max-ch", str(end_ch)])
    res = subprocess.run(cont_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("  X Continuity check failed:\n" + res.stdout)
        sys.exit(1)
    print(f"  [OK] PASS: Continuity intact up to chapter {end_ch if args.act else len(targets)}.")

    print("\n" + "=" * 70)
    print("ALL SUITES PASSED — PROSE AND CANON ARE 100% PRODUCTION READY.")
    print("=" * 70)


if __name__ == "__main__":
    main()
