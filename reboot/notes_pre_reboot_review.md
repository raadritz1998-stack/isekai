# Reading Notes — `isekai / a_god_in_the_garden`

Reviewed at commit `fa778aa` ("Story base line", 2026-10-27). Nothing changed in the repo — this is read-only notes for discussion.

---

## What the folder actually is

Not a code project. It's a **planning-and-continuity repo for a 6-volume OP power-fantasy web serial**, with a small tooling layer bolted on.

```
a_god_in_the_garden/
  canon/            bible, constitution, series arc, roster, story state   ← the source of truth
  volume_01..06/    outline.md (40 chapters each) + state_notes.md
  README.md
tools/              check_chapter.py (linter) + scrub_modern.py (rewriter)
.agents/agents/     three LLM agent prompts: chapter-reviewer, prose_reviewer, prose_expander
epub_generator/     Node EPUB builder (marked + epub-gen-memory), 16 MB of character art
```

**Premise.** Casian Vale, 16, fourth son of a border baron, is the reloaded consciousness of a strategic-class weapon from another world. Argius, its damaged military interface, lives in his head and gives him the Current (total, cost-free remote power). Centuries before his birth, the autonomous **First Watch** built the **Hollow** — a hidden territorial order that already owns the eastern marches. He doesn't hide out of fear; he likes the garden, likes being underestimated, and is quietly building a private kingdom in everything but name.

The core design decision is a good one: **the power is not the story's problem.** There's no "can he win" tension anywhere. The stakes are entirely *what he chooses to take and who gets hurt before he decides*. `constitution.md` makes this explicit and enforceable.

---

## What's strong

**1. The canon layer is unusually disciplined for a hobby project.** Five files with clean separation of concerns — *premise* (bible), *law* (constitution), *roadmap* (series arc), *facts* (roster), *cursor* (story state). Most projects at this stage have one sprawling worldbuilding doc. The knowledge-lock table in `bible.md` (who may know what, per character) is the single best artifact in the repo — it's the thing that stops a long serial from collapsing into people learning things they shouldn't.

**2. `constitution.md` rule 5 and the "First Watch" framing.** You pre-empted the two standard failure modes of this genre: the backstory becoming a mystery-investigation that stalls the plot, and the ancient-power reveal cheapening the protagonist. "Seasoning, never the plot meal" is the right instruction and it's repeated where it needs to be.

**3. Structural consistency.** All six outlines have exactly 40 chapters, no gaps, no duplicates. Act boundaries, epilogue placement, and the "one volume = one escalation of scale, not of threat" rule all hold across the 240-chapter span. That's real discipline.

**4. The volume-4 pivot is the smartest single choice in the arc.** After three volumes where the answer is "he erases them," volume 4 replaces erasure with a *caper* and lets Lucan survive, disgraced. Then volume 5 replaces the antagonist with *choice* (he goes to sea because he wants to). That's how you keep an OP protagonist from becoming boring — you stop escalating power and start escalating the kind of game he plays. Volumes 4–6 read like they were designed by someone who noticed the problem in volumes 1–3.

---

## The problems, in priority order

### 1. There are no chapters. None. Zero.

`find . -name "ch_*.md"` returns nothing. There is no `chapters/` directory in any of the six volumes.

But:

- `volume_01/state_notes.md` → *"Next chapter: COMPLETE — Volume 1 v3 regenerated 40/40."*
- `volume_02/state_notes.md` → *"COMPLETE — Volume 2 v3 regenerated 40/40."*
- `volume_03/state_notes.md` → *"COMPLETE — Volume 3 v3 regenerated 40/40. **Series 120/120 complete per new canon.**"*
- `bible.md` → *"Existing Volume 1–3 manuscripts are preserved as legacy drafts."*
- `story_state.md` → *"Existing chapter manuscripts and earlier volume state notes are preserved as legacy drafts."*

Five documents agree that 120 chapters exist. The repo contains 0. And the volume-1 "continuity log" goes chapter by chapter — ch_001 through ch_040 — describing what each one contains in enough detail that someone wrote them, or generated them, and then either never committed them (`.gitignore` is empty, so that's not it) or deleted them before the "Story base line" commit.

**This is the thing to resolve first**, because everything else downstream depends on the answer:

- If they exist somewhere → they need to come into the repo before anything else is discussed.
- If they were generated and deleted → say so, and decide whether regeneration is the plan.
- If those state notes are *aspirational* (written as though the volume were done, as a target) → then the state-notes format is currently lying to you, and it will lie to you again at volume 2. `story_state.md` should say what's actually true.

The inconsistent *shape* across the six volumes is a tell. Volumes 1–3 have long "end state" + "continuity log" sections. Volumes 4–6 are bare scaffolds ending in "`Next chapter: blocked until Volume X v3 is complete.`" Three volumes are written as if finished; three are written as if not started. That's a session artifact, not a design.

### 2. `Ferrand` is two different people

- `canon/roster.txt`: `Ferrand  # merchant liaison` — a recurring minor support character.
- `volume_02/outline.md` ch.15: *"Ferrand, the Church's cruelest field leader"* → ch.18 *The Warden Who Vanished* → erased.

Same name, merchant vs. Church Warden, and the Warden dies. If both are meant to exist you need two names; if the roster entry is stale you need to delete it. This is the only outright factual contradiction I found in the canon layer, but it's the kind that a linter can't catch and a reader will.

### 3. `epub_generator/assets/vol1/character_sheet.md` contradicts canon outright

It's a v1/v2 survivor and it disagrees with `roster.txt` on nearly every field:

| | character_sheet.md | canon v3 |
|---|---|---|
| Casian | **15** | **16** |
| Edric | **45** | **49** |
| Maren | **41** | **45** |
| Elna | **11** | **12** |
| Casian's character | *"runs the barony from the shadows with **cold, modern efficiency**"* | *"warm, dry, amused, decisive, and thoroughly human"* |

That last row is the serious one. "Cold" and "efficiency" are the exact two things `constitution.md` was written to forbid, and `efficiency` is on the linter's WARN list. The art file `Sera_Vale.jpg` is wired to Elna but there is no Sera anywhere in canon — probably a renamed draft of Elna. Since this ship's in the EPUB front matter, it will end up printed in the book.

### 4. The linter is checking the wrong story

`tools/check_chapter.py` bans `the Quiet` and `the Ledger` as ERROR-level "secret-org" leaks. **Neither exists in this story.** The order is `the Hollow`. So the one leak you'd actually want caught — a POV character naming the Hollow on the page — is not checked at all. The rules were carried over from a previous project and never updated.

Other issues in the same file:

- Docstring and usage examples reference `story/writers_constitution.md`, `story/canon/roster.txt`, `story/volume_01/...`. The real paths are `a_god_in_the_garden/canon/...`. The code paths are correct; only the docs are stale, so it works but reads as broken.
- `(re.compile(r"\bcompan(y|ies)\b"), "register")` will fire on *"a company of riders"* — a completely ordinary medieval phrase. Same for `networks`, which is legitimately usable of tunnels/roads.
- `\bAI\b` case-sensitive will miss `Ai`/`ai` and fire on nothing useful.
- `\bIndia\b` as a past-life marker is a very odd survivor of the old project.
- Roster matching is exact-string, so frontmatter must say `Hask Veyr`, not `Hask`, or you get a false ERROR. Nothing documents that.

### 5. `scrub_modern.py` is a loaded gun pointed at your manuscripts

It opens every chapter, regex-replaces, and **writes back in place** — no dry-run, no diff, no backup, no confirmation. Given that point 1 means there are currently no files to destroy, this hasn't bitten yet. It will.

Specific defects:

- Duplicate dict key: `\bgeometric proofs\b` appears twice. Harmless, but it means the dict was never reviewed.
- `\bdata\b → knowledge` is a global noun swap. Any legitimate use becomes nonsense.
- `\binterface\b → connection` will fire on nothing in Varenthos (good) but also can't tell Argius's interface from a metaphorical one.
- Dict ordering means longer phrases must precede shorter ones — currently correct, but fragile and undocumented.

The linter (read-only, reports line numbers, you judge) is the right design. The scrubber (silent mutation) is the wrong design for prose. If it stays, it needs `--dry-run` as the default and a `git diff` gate.

### 6. Two of the three agent prompts fight the canon

- All three reference `story/writers_constitution.md`, a path that doesn't exist, and `chapter-reviewer` is still told it works on **'The Cost of Quiet'** — the previous project.
- `prose_expander` is instructed to *"reset Argius to a cold tone."* `constitution.md` rule 8 says Argius is **dry** — "terse military precision, occasional flat humour." Cold is the v2 Argius. That agent will actively walk your protagonist's only companion back to a characterization you retired.
- `chapter-reviewer` hardcodes a 2,500-word minimum, which is a real constraint but appears nowhere in canon. If it's law, put it in `constitution.md`; if it's not, the agents shouldn't enforce it.

### 7. Small stale references

- `story_state.md`: *"Draft Volume 1 v3 from `volume_01/outline_v3.md`"* — the file is `volume_01/outline.md`.
- `epub_generator/README.md`: every example uses `../story/volume_01` and title `"The Cost of Quiet"`.
- `epub_generator/epub.example.json`: title `"The Cost of Quiet"`, description describes a different book entirely.
- `requirements.txt` pulls `qdrant-client[fastembed]` and `python-frontmatter` for a RAG indexer that **isn't in the repo**. The linter needs neither. You have dependencies with no consumer.
- `canon/roster.txt` is missing every name volumes 5–6 need (`Mira`, `Nemea`, `Voss`, `Severin`, `Ivara`, `Tarek`). The volume state notes flag this honestly ("add to roster before drafting"), but it means roster.txt is not yet a master list, which is the one job it has.

---

## The thing I'd actually want to argue about

Everything above is cleanup. This is the substantive question.

**Volumes 1, 2, and 3 are the same book three times.**

Put the three outlines side by side and the beat skeleton is nearly identical:

| Beat | Vol 1 | Vol 2 | Vol 3 |
|---|---|---|---|
| Ch. 1–2: villain arrives certain; Casian receives the news while planting / gardening | Hask Veyr | Inquisitor Vaunt | Magister Roeth |
| Ch. 3–5: villain commits an atrocity on ordinary people, proving teeth | burned border holding | Warden burns a healer | Concord kills Hollow operatives |
| Ch. 5–7: the sharp noblewoman arrives to observe, notices he's *never surprised* | Seraine | Seraine | Seraine |
| Ch. 13–15: the field girl challenges him about an old mark answering to him | Vesna | Vesna | Vesna |
| Ch. 21–22: the villain strikes *near* home and nearly takes people he cares about | ch.22 | ch.22 | ch.21 |
| Ch. 26–28: Casian engineers a trap that the enemy walks into believing they're cornering *him* | ch.28–30 | ch.28–30 | ch.28–30 |
| Ch. 31–33: the enemy's command structure vanishes in stages; certainty → terror; erased | Hask | Ferrand + Vaunt's hunt | Roeth |
| Ch. 34–36: the ally confronts him with what she can prove, which is nothing | Seraine | Seraine | Seraine |
| Ch. 37: an old mark does something unexplained; atmosphere only | ch.37 | ch.37 | ch.37 |
| Ch. 38–39: the victory is converted into permanent infrastructure/leverage | ch.38–39 | ch.38–39 | ch.37–39 |
| Ch. 40: he is back in the garden, content, planning the next improvement | "Three Buds" | "Summer Roads" | "The Horizon Is His" |

The near-miss always lands on an *adjacent* person (never Casian, per rule 1) — in all three volumes at almost the same chapter number. The confrontation-without-proof always happens in ch. 36. The mark does something unexplained in ch. 37, in all three.

Now: some of this is *deliberate form*, and it can work — serialized genre fiction runs on reliable rhythm, and the conclusion of each volume landing in the garden is thematically correct (it's called *A God in the Garden*). A reader who loves the loop will be happy.

But the risk is real and specific: **by the midpoint of volume 2, the reader knows the shape of the trick before the villain does.** The aura depends on surprise — the reader seeing the gap between the harmless boy and the force shaping the board. If the reader can predict the gap, you're not showing them aura anymore, you're showing them a process. And volumes 4–6 show you already know how to fix this: change *what kind of game* he's playing, not how big the enemy is.

Worth deciding now, before 120 chapters are written:

- Is the repeated skeleton intentional ritual (comfort reading), or drift?
- If ritual: what varies *inside* the skeleton per volume so it doesn't read as a copy? Right now the variation is mostly the villain's ideology, which is the least interesting variable.
- If drift: volume 2 is where to break it. It's the one where the *institution* (the Church, with a Synod, an archive, and a doctrinal fear of the Marches) is far more interesting than its field commander. The outline knows this — ch. 24 and ch. 33 are Selwyn writing reports about an ancient terror — but Selwyn stays a witness rather than becoming the engine. A volume where the antagonist's *institution* adapts to Casian instead of the antagonist being erased would break the pattern with material you already have.

Second, smaller version of the same worry: **`constitution.md` says every act needs "at least two unmistakable Casian-aura payoffs."** That's 6+ per volume, 36+ across three volumes, and they're all variations on *things vanish and nobody can explain it*. Aura degrades with repetition faster than any other element of this genre. It might be worth asking what a payoff looks like that isn't an erasure — volume 4's caper answer (social dominance, exposure, letting a rival live diminished) is the template.

---

## Suggested order of operations

1. **Resolve the missing manscripts.** Everything else is decoration until you know whether 120 chapters exist.
2. **Fix the canon contradictions** — Ferrand, and the `character_sheet.md` ages/characterization (or delete the sheet).
3. **Update the tooling to this story** — retarget the linter's secret-org rules to `Hollow`, fix the agent prompts' project name / path / Argius-tone instruction, add `--dry-run` to the scrubber, drop the unused `requirements.txt` deps.
4. **Decide roster completeness** — add Vol 5–6 names or explicitly mark the roster as "volumes 1–4".
5. **Have the volume 1–3 sameness conversation** while it's still cheap.

Items 2–4 are an afternoon of work and I'm happy to do them. Item 5 is the one worth the conversation.
