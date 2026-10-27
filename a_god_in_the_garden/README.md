# A God in the Garden

An OP power fantasy set in Varenthos. Casian Vale, the warm fourth son of a border baron, is the most dangerous being alive. He protects and expands the eastern marches because he wants a good life there—not because he fears the world.

## Canonical Architecture

All core worldbuilding, series rules, and character definitions live in `canon/`:

1. `canon/bible.md` — Premise, crossing, First Watch, character and knowledge locks.
2. `canon/constitution.md` — Non-negotiable writer rules (Casian is never threatened, chosen mask, proactive domain building, dry Argius, medieval register).
3. `canon/series_arc.md` — High-level 6-volume series roadmap.
4. `canon/roster.txt` — Canonical roster with locked names, ages, and roles.
5. `canon/story_state.md` — Active cursor and retcon policy.

## Volume Layout

Each volume is self-contained with:
- `outline.md`: The 40-chapter beat-by-beat blueprint.
- `state_notes.md`: Start-state, continuity locks, and running bridges.
- `chapters/`: Final chapter Markdown manuscripts (`ch_001.md` – `ch_040.md`).

Volumes:
- `volume_01/` — *The Gardener* (Hask Veyr & Baron Osric)
- `volume_02/` — *The Ashfire* (Ashen Church & Inquisitor Vaunt)
- `volume_03/` — *The Iron Key* (Iron Concord & Magister Roeth)
- `volume_04/` — *The Fourth Son at Court* (Duke Lucan & Capital Charter)
- `volume_05/` — *Beyond the Hills* (Port alliance & Maritime expansion)
- `volume_06/` — *The Open Gate* (Grand Accord & Final Payoff)

## Tools & Building

- `tools/check_chapter.py`: Fast constitutional and roster linter.
- `tools/scrub_modern.py`: Scrubber for anachronistic sci-fi and research terminology.
- `epub_generator/`: Node.js EPUB builder.
