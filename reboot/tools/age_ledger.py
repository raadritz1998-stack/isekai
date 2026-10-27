#!/usr/bin/env python3
"""
Age Ledger — single source of truth for names and ages.

The old project drifted because ages were written into prose and into
per-volume notes by hand, and nothing recomputed them when the calendar moved.
This tool makes the drift impossible:

    python tools/age_ledger.py            # regenerate canon/roster.txt + canon/ages.md
    python tools/age_ledger.py --check    # verify generated files are current (CI gate)
    python tools/age_ledger.py --check-year 1219 chapters/*.md
                                          # flag prose ages that contradict the ledger

`canon/characters.json` is the only file anyone edits. Everything else is output.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "canon"
DATA = CANON / "characters.json"

GROUP_HEADINGS = [
    ("vale",    "The Vale household"),
    ("other",   "Argius"),
    ("hollow",  "The Hollow — built by Casian, not inherited"),
    ("romance", "Romance"),
    ("wild",    "Unaffiliated"),
    ("v1_foe",  "Volume 1 — antagonists"),
    ("ash",     "The Ash — volume 2"),
    ("v3_foe",  "Volume 3"),
    ("v4_foe",  "The Court — volume 4"),
    ("crown",   "The Crown — volume 4"),
    ("v5_foe",  "Volume 5 (placeholders \u2014 confirm before planning)"),
]


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def age_in(birth, year):
    if birth is None:
        return None
    return year - birth


def alive_in(ch, year):
    return ch.get("dies") is None or year <= ch["dies"]


# ── generators ────────────────────────────────────────────────────────────────

def gen_roster(data):
    vols = data["calendar"]["volumes"]
    ref = vols[0]["year"]
    out = [
        "# Canonical names \u2014 Master Roster",
        f"# GENERATED from canon/characters.json by tools/age_ledger.py. Do not edit by hand.",
        f"# Ages shown are as of {vols[0]['id']} ({ref}). See canon/ages.md for every volume.",
        "# Any name in chapter frontmatter `characters:` must appear here, spelled exactly.",
        "",
    ]
    for group, heading in GROUP_HEADINGS:
        members = [c for c in data["characters"] if c["group"] == group]
        if not members:
            continue
        out.append(f"# \u2014 {heading} \u2014")
        width = max(len(c["name"]) for c in members) + 2
        for c in sorted(members, key=lambda c: (c["birth"] is None, -(c["birth"] or 0))):
            a = age_in(c["birth"], ref)
            age = f"born {c['birth']}, age {a}" if a is not None else "ageless"
            dies = f" \u2014 dies {c['dies']}" if c.get("dies") else ""
            note = f". {c['note']}" if c["note"] else ""
            out.append(f"{c['name'].ljust(width)}# {age} \u00b7 {c['role']}{dies}{note}")
        out.append("")
    out.append("# Names appearing in more than one group, or in no group, are an error.")
    return "\n".join(out) + "\n"


def gen_ages(data):
    vols = data["calendar"]["volumes"]
    years = [v["year"] for v in vols]

    out = [
        "# Age Ledger",
        "> **GENERATED** from `canon/characters.json` by `tools/age_ledger.py`. Do not edit by hand.",
        "> If a number here disagrees with a chapter, the chapter is wrong.",
        "",
        "## The calendar",
        "",
        "| Volume | Title | Year | Season span |",
        "|---|---|---|---|",
    ]
    for v in vols:
        out.append(f"| {v['id'][-2:].lstrip('0')} | *{v['title']}* | {v['year']} | {v['span']} |")

    out += [
        "",
        "**Rule:** every chapter's frontmatter carries `year:`. Ages are computed, never invented.",
        "A birthday is not a scene unless it is a scene. When in doubt, a character is the age in this table",
        "for the whole volume, and the next volume's table entry is the age they turn.",
        "",
        "## Ages by volume",
        "",
        "| Character | Birth | " + " | ".join(f"V{i+1}" for i in range(len(vols))) + " |",
        "|---" * (len(vols) + 2) + "|",
    ]
    for group, heading in GROUP_HEADINGS:
        members = [c for c in data["characters"] if c["group"] == group]
        if not members:
            continue
        out.append(f"| **{heading}** | | " + " | ".join("" for _ in vols) + " |")
        for c in sorted(members, key=lambda c: (c["birth"] is None, -(c["birth"] or 0))):
            cells = []
            for y in years:
                if c["birth"] is None:
                    cells.append("\u2014")
                elif not alive_in(c, y):
                    cells.append("\u2020")
                else:
                    cells.append(str(age_in(c["birth"], y)))
            out.append(f"| {c['name']} | {c['birth'] if c['birth'] else '\u2014'} | " + " | ".join(cells) + " |")

    out += [
        "",
        "\u2020 = dead by this volume. \u2014 = not applicable (ageless).",
        "",
        "## Drift traps",
        "",
        "These are the ones that broke the previous drafts. Check them every time.",
        "",
        "- **Emric** is an infant in Volume 1 and a small boy by Volume 5. He is the fastest-moving",
        "  age in the cast and the easiest to leave behind.",
        "- **Elna** is twelve when the story opens and seventeen when it ends. Her voice must change.",
        "  A twelve-year-old and a seventeen-year-old do not speak the same way.",
        "- **Casian** is sixteen at the start and twenty-one at the end. He is a boy in Volume 1 and an",
        "  adult by Volume 5, and the mask has to survive that. A twenty-one-year-old playing the",
        "  overlooked fourth son is a different performance from a sixteen-year-old doing it.",
        "- **Seraine** is three years older than him and stays three years older. Do not let the gap",
        "  drift toward zero because it reads better in a scene.",
        "- **Oswin** is seventy-one at the start. Over five years that is a real risk, and it should be",
        "  felt without ever being used as a threat.",
        "",
    ]
    return "\n".join(out) + "\n"


# ── checks ────────────────────────────────────────────────────────────────────

def check_generated(data):
    ok = True
    for name, gen in (("roster.txt", gen_roster), ("ages.md", gen_ages)):
        path = CANON / name
        if not path.exists():
            print(f"  MISSING  canon/{name}")
            ok = False
            continue
        if path.read_text(encoding="utf-8") != gen(data):
            print(f"  STALE    canon/{name} \u2014 re-run without --check")
            ok = False
    return ok


def check_validity(data):
    ok = True
    names = [c["name"] for c in data["characters"]]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        print(f"  DUPLICATE NAME  {', '.join(sorted(dupes))}")
        ok = False
    years = [v["year"] for v in data["calendar"]["volumes"]]
    if years != sorted(years):
        print(f"  CALENDAR NOT ASCENDING  {years}")
        ok = False
    for c in data["characters"]:
        if c["birth"] is None:
            continue
        if c["birth"] > years[0]:
            print(f"  BORN IN THE FUTURE  {c['name']} (birth {c['birth']})")
            ok = False
        if c.get("dies") and c["dies"] < years[0]:
            print(f"  DEAD BEFORE THE STORY STARTS  {c['name']}")
            ok = False
    return ok


AGE_RE = re.compile(r"\b(\d{1,2})[- ](?:years?[- ]old|year[- ]old)\b|\b(\d{1,2}) years old\b", re.I)
FRONT_YEAR = re.compile(r"^\s*year:\s*(\d{4})\s*$", re.M)
FRONT_CHARS = re.compile(r"^\s*characters:\s*\[(.*)\]\s*$", re.M)


def check_chapters(data, paths):
    by_name = {c["name"]: c for c in data["characters"]}
    bad = 0
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"{path}: missing")
            bad += 1
            continue
        text = path.read_text(encoding="utf-8")
        ym, cm = FRONT_YEAR.search(text), FRONT_CHARS.search(text)
        if not ym:
            print(f"{path}: no `year:` in frontmatter \u2014 ages cannot be verified")
            bad += 1
            continue
        year = int(ym.group(1))
        cast = [n.strip().strip("'\"") for n in (cm.group(1).split(",") if cm else []) if n.strip()]
        expected = {c: age_in(by_name[c]["birth"], year) for c in cast
                    if c in by_name and by_name[c]["birth"] is not None}
        for m in AGE_RE.finditer(text):
            stated = int(m.group(1) or m.group(2))
            if stated not in expected.values():
                print(f"{path}: says '{m.group(0)}' in {year}, but the ledger gives "
                      f"{expected or 'no ages for this cast'}")
                bad += 1
    return bad == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify generated files are current")
    ap.add_argument("--check-year", action="store_true", help="verify prose ages in chapter files")
    ap.add_argument("chapters", nargs="*")
    args = ap.parse_args()

    data = load()

    if args.check_year:
        print("age ledger \u2014 chapter check")
        ok = check_chapters(data, args.chapters)
        return 0 if ok else 1

    if args.check:
        print("age ledger \u2014 verification")
        ok = check_validity(data) and check_generated(data)
        print("  OK" if ok else "  FAILED \u2014 fix canon/characters.json, then regenerate")
        return 0 if ok else 1

    if not check_validity(data):
        print("refusing to generate from invalid data")
        return 1
    (CANON / "roster.txt").write_text(gen_roster(data), encoding="utf-8")
    (CANON / "ages.md").write_text(gen_ages(data), encoding="utf-8")
    print("wrote canon/roster.txt and canon/ages.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
