const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { parseArgs } = require("util");
const { marked } = require("marked");
const Epub = require("epub-gen-memory").default;

// ─── Defaults ────────────────────────────────────────────────────────────────
// These are used when the volume folder has no `epub.json` and no CLI flag
// overrides them. Anything here can be replaced per-volume later without
// touching this file — see the README.

const SCRIPT_DIR = __dirname;
const BUILTIN_ASSETS_DIR = path.join(SCRIPT_DIR, "assets");
const DEFAULT_OUTPUT_DIR = path.join(SCRIPT_DIR, "output");
const SUPPORTED_IMAGE_EXT = new Set([".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]);
const MIME_BY_EXT = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
};

const DEFAULTS = {
  title: "The Fourth Son's Ledger",
  author: "Raadritz",
  publisher: "unknown traveller",
  lang: "en",
  // Image pages inserted before the table of contents. Each `file` is looked
  // for in the volume's asset dir first, then this generator's built-in
  // assets/ folder. Missing images are skipped with a warning, not fatal —
  frontMatter: [
    { title: "Casian Vale", file: "../../epub_generator/assets/vol1/Casian_Vale.jpg", alt: "Casian Vale" },
    { title: "Lord Edric Vale", file: "../../epub_generator/assets/vol1/Edric_Vale.jpg", alt: "Lord Edric Vale" },
    { title: "Lady Maren Vale", file: "../../epub_generator/assets/vol1/Maren_Vale.jpg", alt: "Lady Maren Vale" },
    { title: "Sera Vale", file: "../../epub_generator/assets/vol1/Sera_Vale.jpg", alt: "Sera Vale" },
    { title: "Baroness Calla of Fenwick", file: "../../epub_generator/assets/vol1/Baroness_Calla.jpg", alt: "Baroness Calla" },
    { title: "Lady Seraine Varyn", file: "../../epub_generator/assets/vol1/Lady_Seraine.jpg", alt: "Lady Seraine" },
    { title: "Baron Osric of Thornwall", file: "../../epub_generator/assets/vol1/Baron_Osric.jpg", alt: "Baron Osric" },
  ],
  cover: null, // e.g. "assets/cover.png" (relative to the volume folder)
};

// ─── CLI ─────────────────────────────────────────────────────────────────────

function parseCli(argv) {
  const { values, positionals } = parseArgs({
    args: argv,
    allowPositionals: true,
    options: {
      out: { type: "string", short: "o" },
      title: { type: "string" },
      subtitle: { type: "string" },
      author: { type: "string" },
      publisher: { type: "string" },
      cover: { type: "string" },
      assets: { type: "string" },
      "no-frontmatter": { type: "boolean", default: false },
      help: { type: "boolean", short: "h", default: false },
    },
  });
  return { opts: values, volumeArg: positionals[0] };
}

function printUsage() {
  console.log(`
Build an EPUB from a volume folder.

Usage:
  node index.js <volume-folder> [options]

Arguments:
  <volume-folder>   Path to a volume dir that contains a chapters/ subfolder
                    (e.g. ../story/volume_01). Absolute or relative to cwd.

Options:
  -o, --out <file>       Output .epub path. Default: output/<slug>.epub
      --title <text>      Book title. Default: epub.json > outline.md > folder name
      --subtitle <text>   Appended as "Title: Subtitle"
      --author <text>     Default: epub.json > built-in default
      --publisher <text>  Default: epub.json > built-in default
      --cover <file>      Cover image, resolved against the volume folder
      --assets <dir>      Asset search dir. Default: <volume-folder>/assets
      --no-frontmatter    Skip the front-matter image pages
  -h, --help

Per-volume config (all optional): put an epub.json in the volume folder. See README.
`);
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function slugify(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "book";
}

/**
 * Strip a leading `--- ... ---` YAML front-matter block and return { data, body }.
 * `data` only captures simple `key: value` scalars (enough for `title`);
 * list values and folded/multi-line values are ignored on purpose.
 */
function splitFrontMatter(md) {
  const withoutBom = md.charCodeAt(0) === 0xfeff ? md.slice(1) : md;
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(withoutBom);
  if (!match) return { data: {}, body: withoutBom };

  const data = {};
  for (const line of match[1].split(/\r?\n/)) {
    const kv = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line);
    if (!kv) continue;
    const value = kv[2].trim();
    if (value === "" || value.startsWith(">") || value.startsWith("|") || value.startsWith("[")) continue;
    data[kv[1]] = value.replace(/^["']|["']$/g, "");
  }
  return { data, body: withoutBom.slice(match[0].length) };
}

function prettifyFilename(file) {
  return file
    .replace(/\.md$/i, "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function firstNumber(str) {
  const m = str.match(/\d+/);
  return m ? parseInt(m[0], 10) : Number.MAX_SAFE_INTEGER;
}

/**
 * Resolve an asset reference to an absolute path, or return null.
 * - absolute path            -> used as-is
 * - contains a slash         -> resolved relative to `baseDir` (the volume folder)
 * - bare filename            -> searched in each of `searchDirs` in order
 */
function resolveAsset(file, { searchDirs, baseDir }) {
  if (!file) return null;
  if (path.isAbsolute(file)) return fs.existsSync(file) ? file : null;
  if (file.includes("/") || file.includes("\\")) {
    const p = path.resolve(baseDir, file);
    return fs.existsSync(p) ? p : null;
  }
  for (const dir of searchDirs) {
    const p = path.join(dir, file);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function imageFileUrl(absPath) {
  const ext = path.extname(absPath).toLowerCase();
  if (!MIME_BY_EXT[ext]) {
    throw new Error(`Unsupported image type "${ext}": ${absPath}`);
  }
  return pathToFileURL(absPath).href;
}

function createImagePage(entry, resolveOpts) {
  const abs = resolveAsset(entry.file, resolveOpts);
  if (!abs) {
    console.warn(`  ! front-matter image not found, skipping: ${entry.file}`);
    return null;
  }
  const safeTitle = escapeHtml(entry.title ?? "");
  const safeAlt = escapeHtml(entry.alt ?? entry.title ?? "");
  return {
    title: entry.title ?? "Illustration",
    beforeToc: true,
    content: `
      <section style="margin:0; padding:0; text-align:center;">
        ${safeTitle ? `<h1 style="font-size:1.4em; margin:0 0 1em 0;">${safeTitle}</h1>` : ""}
        <img
          src="${imageFileUrl(abs)}"
          alt="${safeAlt}"
          style="display:block; width:100%; max-width:100%; height:auto; margin:0 auto;"
        />
      </section>
    `,
  };
}

function titleFromOutline(volumeDir) {
  const p = path.join(volumeDir, "outline.md");
  if (!fs.existsSync(p)) return null;
  const heading = fs
    .readFileSync(p, "utf-8")
    .split(/\r?\n/)
    .find((l) => /^#\s+/.test(l));
  if (!heading) return null;
  return heading
    .replace(/^#\s+/, "")
    .replace(/[*_`]/g, "")
    .replace(/^[^\p{L}\p{N}]+/u, "") // strip leading emoji / decoration
    .trim();
}

function loadVolumeConfig(volumeDir) {
  for (const name of ["epub.json", "book.json"]) {
    const p = path.join(volumeDir, name);
    if (fs.existsSync(p)) {
      try {
        return JSON.parse(fs.readFileSync(p, "utf-8"));
      } catch (e) {
        throw new Error(`Failed to parse ${p}: ${e.message}`);
      }
    }
  }
  return {};
}

// ─── Build ───────────────────────────────────────────────────────────────────

async function generateEpub({ opts, volumeArg }) {
  const volumeDir = path.resolve(volumeArg);
  if (!fs.existsSync(volumeDir) || !fs.statSync(volumeDir).isDirectory()) {
    throw new Error(`Volume folder not found: ${volumeDir}`);
  }

  const chapterDir = path.join(volumeDir, "chapters");
  if (!fs.existsSync(chapterDir)) {
    throw new Error(`No chapters/ folder inside: ${volumeDir}`);
  }

  const cfg = loadVolumeConfig(volumeDir);

  // Resolution order for every setting: CLI flag > epub.json > outline.md > built-in default.
  const baseTitle =
    opts.title || cfg.title || DEFAULTS.title || titleFromOutline(volumeDir) || path.basename(volumeDir);
  const subtitle = opts.subtitle || cfg.subtitle || "";
  const title = subtitle ? `${baseTitle}: ${subtitle}` : baseTitle;
  const author = opts.author || cfg.author || DEFAULTS.author;
  const publisher = opts.publisher || cfg.publisher || DEFAULTS.publisher;
  const lang = cfg.lang || DEFAULTS.lang;

  const volumeAssetsDir = path.resolve(volumeDir, opts.assets || cfg.assets || "assets");
  const searchDirs = [volumeAssetsDir, BUILTIN_ASSETS_DIR].filter((d) => fs.existsSync(d));
  const resolveOpts = { searchDirs, baseDir: volumeDir };

  // Chapters
  const files = fs
    .readdirSync(chapterDir)
    .filter((f) => /\.md$/i.test(f) && f.toLowerCase() !== "readme.md")
    .sort((a, b) => firstNumber(a) - firstNumber(b));

  if (files.length === 0) {
    throw new Error(`No chapter .md files in: ${chapterDir}`);
  }

  const chapters = files.map((file) => {
    const raw = fs.readFileSync(path.join(chapterDir, file), "utf-8");
    const { data, body } = splitFrontMatter(raw);
    const n = firstNumber(file);
    const name = data.title || prettifyFilename(file);
    const chapterTitle = n === Number.MAX_SAFE_INTEGER ? name : `${n}. ${name}`;
    return { title: chapterTitle, content: marked.parse(body) };
  });

  // Front matter
  let frontMatter = [];
  if (!opts["no-frontmatter"]) {
    const entries = Array.isArray(cfg.frontMatter) ? cfg.frontMatter : DEFAULTS.frontMatter;
    frontMatter = entries.map((e) => createImagePage(e, resolveOpts)).filter(Boolean);
  }

  // Cover
  const coverRef = opts.cover || cfg.cover || DEFAULTS.cover;
  let cover;
  if (coverRef) {
    const abs = resolveAsset(coverRef, resolveOpts);
    if (abs) cover = imageFileUrl(abs);
    else console.warn(`  ! cover image not found, skipping: ${coverRef}`);
  }

  // Output path
  const outFile = path.resolve(
    opts.out || path.join(DEFAULT_OUTPUT_DIR, `${slugify(title)}.epub`),
  );
  fs.mkdirSync(path.dirname(outFile), { recursive: true });

  const options = {
    title,
    author,
    publisher,
    lang,
    ...(cover ? { cover } : {}),
    ...(cfg.description ? { description: cfg.description } : {}),
  };

  console.log(`Volume folder : ${volumeDir}`);
  console.log(`Chapters      : ${files.length}`);
  console.log(`Front matter  : ${frontMatter.length} image page(s)`);
  console.log(`Title         : ${title}`);
  console.log(`Output        : ${outFile}`);
  console.log("Generating EPUB...");

  const epubBuffer = await Epub(options, [...frontMatter, ...chapters]);
  fs.writeFileSync(outFile, epubBuffer);
  console.log(`Success! Saved ${outFile}`);
}

// ─── Entry ───────────────────────────────────────────────────────────────────

(async () => {
  const parsed = parseCli(process.argv.slice(2));
  if (parsed.opts.help || !parsed.volumeArg) {
    printUsage();
    process.exit(parsed.volumeArg ? 0 : 1);
  }
  try {
    await generateEpub(parsed);
  } catch (e) {
    console.error("Error building the book:");
    console.error(e.message || e);
    process.exit(1);
  }
})();
