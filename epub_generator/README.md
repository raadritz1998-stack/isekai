# epub_generator

Builds an EPUB from a **story volume folder**. Point it at a volume directory;
it reads `chapters/*.md`, strips YAML front-matter, converts the Markdown, adds
optional image pages before the table of contents, and writes a `.epub`.

---

## Install

```bash
cd epub_generator
pnpm install     # or npm install
```

Node 18.3+ (uses `util.parseArgs`). On this machine, Node is via NVS — prepend
the 22.17.1 dir to `PATH` before running (`.../AppData/Local/nvs/node/22.17.1/x64`).

---

## Usage

```bash
node index.js <volume-folder> [options]
```

`<volume-folder>` is any directory that contains a `chapters/` subfolder — e.g.
`../story/volume_01`. Path is absolute or relative to the current directory.

```bash
# simplest — everything inferred
node index.js ../story/volume_01

# override bits from the terminal
node index.js ../story/volume_01 --title "The Cost of Quiet" --subtitle "Volume One" -o dist/vol1.epub

# via the package script
pnpm build ../story/volume_01
```

### Options

| Flag | Meaning | Default |
|------|---------|---------|
| `-o, --out <file>` | Output `.epub` path | `output/<slug-of-title>.epub` |
| `--title <text>` | Book title | `epub.json` → H1 of `outline.md` → folder name |
| `--subtitle <text>` | Appended as `"Title: Subtitle"` | — |
| `--author <text>` | Author | `epub.json` → built-in default |
| `--publisher <text>` | Publisher | `epub.json` → built-in default |
| `--cover <file>` | Cover image (resolved against the volume folder) | `epub.json` cover, else none |
| `--assets <dir>` | Asset search directory | `<volume-folder>/assets` |
| `--no-frontmatter` | Skip the front-matter image pages | off |
| `-h, --help` | Usage | — |

**Precedence for every setting:** CLI flag → `<volume-folder>/epub.json` →
`outline.md` (title only) → built-in default.

---

## Chapters

- Every `*.md` in `<volume-folder>/chapters/` is a chapter. `README.md` is ignored.
- Order is by the **first number in the filename** (`ch_001.md`, `ch_002.md`, …).
- **YAML front-matter is stripped** before conversion. The chapter title is the
  front-matter `title:` if present, otherwise the prettified filename, and it is
  prefixed with the chapter number (`3. Substitutions`).

```markdown
---
title: Substitutions
characters: [Casian, Argius]
---

Prose starts here...
```

---

## Assets & front matter

Front-matter image pages appear before the table of contents. Each entry is
`{ title, file, alt }`. For every `file`, the generator looks:

1. in the volume's asset dir — `<volume-folder>/assets/` (or `--assets <dir>`),
2. then in this generator's built-in `epub_generator/assets/`.

`file` may also be a path with a slash (resolved against the volume folder) or an
absolute path. Supported: `.png .jpg .jpeg .gif .webp .svg`.

**A missing image is a warning, not an error** — the page is skipped and the
build continues. So you can declare the pages you *intend* to have now and drop
the real art in later without touching any code.

### Right now (no config)

With no `epub.json`, the build uses the three placeholder images in
`epub_generator/assets/` (`Core.png`, `npc.png`, `asset_1.png`). Fine for a
draft build.

### Later (custom art per volume)

1. Copy [`epub.example.json`](epub.example.json) to `<volume-folder>/epub.json`.
2. Put your art in `<volume-folder>/assets/`.
3. Edit `epub.json` — set `title`/`subtitle`, `cover`, and the `frontMatter`
   list to your real filenames.

```jsonc
// story/volume_01/epub.json
{
  "title": "The Cost of Quiet",
  "subtitle": "Volume One",
  "cover": "assets/cover.png",
  "frontMatter": [
    { "title": "Core Cast", "file": "assets/core-cast.png", "alt": "Core cast" },
    { "title": "Map of the Eastern Marches", "file": "assets/map.png", "alt": "Map" }
  ]
}
```

Nothing else changes — `node index.js ../story/volume_01` now picks it all up.
Each volume carries its own `epub.json` + `assets/`, so volumes stay independent.

---

## Output

Default: `epub_generator/output/<slug>.epub`. `output/` and `*.epub` are
git-ignored. Override with `-o`.

---

## Files

| Path | Purpose |
|------|---------|
| `index.js` | the generator |
| `epub.example.json` | template to copy into a volume folder as `epub.json` |
| `assets/` | built-in placeholder images (fallback when a volume has none) |
| `output/` | build output (git-ignored) |

## Notes / limitations

- Front-matter parsing captures only simple `key: value` scalars — enough for
  `title`. List and multi-line values are ignored (they're metadata for other
  tools, not the EPUB).
- Images are embedded from local files via `file://` URLs by `epub-gen-memory`.
  Remote URLs in chapter Markdown would also be fetched at build time.
- No EPUB validation step. Run the result through an external checker if you need
  store-grade output.
