/**
 * Build the site's CSS, normalise it, and compare it with the committed
 * baseline in scripts/css-baseline/.
 *
 *   npm run css:diff       exit 1 and print a unified diff if the CSS changed
 *   npm run css:diff -- --ignore-prefixes
 *                          the same, leaving out vendor-prefixed CSS on both sides
 *   npm run css:snapshot   overwrite the baseline with the current build
 *   npm run css:warnings -- step-N
 *                          record Sass deprecation warnings in
 *                          scripts/sass-warnings/step-N.txt
 *
 * Normalising removes differences that cannot change how a page renders
 * (comments, whitespace, nesting, how rules are grouped into at-rule blocks,
 * selector order within a list, hex colour case), so Sass output and its
 * hand-written CSS replacement compare equal.
 */
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import postcss from "postcss";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BASELINE_DIR = path.join(ROOT, "scripts/css-baseline");
const WORK_DIR = path.join(ROOT, "node_modules/.cache/css-check");
const BUILD_DIR = path.join(WORK_DIR, "build");
const CURRENT_DIR = path.join(WORK_DIR, "current");
const WARNINGS_DIR = path.join(ROOT, "scripts/sass-warnings");
const SASS_ENTRIES = [
  "muckrock/assets/scss/style.scss",
  "muckrock/assets/scss/docViewer.scss",
  "muckrock/assets/scss/print.scss",
  "muckrock/foiamachine/assets/scss/style.scss",
];

/** Flatten nested rules into "outer inner" selectors, as Sass does. */
function joinSelectors(parents, children) {
  if (!parents.length) return children;
  const joined = [];
  for (const parent of parents) {
    for (const child of children) {
      if (!child.includes("&")) {
        joined.push(`${parent} ${child}`);
        continue;
      }
      // Native nesting cannot build a name from `&` (&__item, &--active);
      // joining it here would make broken CSS compare equal to Sass.
      if (/&[\w-]/.test(child)) {
        throw new Error(
          `"${child}" builds a selector name from &, which native CSS nesting does not support`,
        );
      }
      joined.push(child.replaceAll("&", parent));
    }
  }
  return joined;
}

const VENDOR_PREFIX = /^-(webkit|moz|ms|o)-/;
// Unprefixed properties from the 2009 flexbox draft; no browser applies them.
const LEGACY_FLEXBOX = /^box-(flex|flex-group|pack|align|orient|lines|direction|ordinal-group)$/;

function isPrefixedDecl({ prop, value }) {
  return (
    VENDOR_PREFIX.test(prop) ||
    VENDOR_PREFIX.test(value) ||
    LEGACY_FLEXBOX.test(prop) ||
    (prop === "display" && /^(inline-)?box$/.test(value))
  );
}

const isPrefixedSelector = (selector) => /::?-(webkit|moz|ms|o)-/.test(selector);

function cleanValue(value) {
  return value
    .replace(/\s+/g, " ")
    .trim()
    .replace(/#[0-9a-f]{3,8}\b/gi, (hex) => hex.toLowerCase());
}

/**
 * Turn a stylesheet into a flat list of rules, each with the at-rules that
 * wrap it, then print one block per rule.
 *
 * With ignorePrefixes, vendor-prefixed declarations and selectors are left out.
 */
export function normalize(css, { ignorePrefixes = false } = {}) {
  const blocks = [];

  function walk(container, selectors, atRules) {
    let decls = [];
    const flushDecls = () => {
      if (decls.length) blocks.push({ atRules, selectors, decls });
      decls = [];
    };

    // Declarations after a nested rule still belong to the parent's block in
    // Sass output, so collect them all before emitting children.
    const children = [];
    container.each((node) => {
      if (node.type === "decl") {
        if (ignorePrefixes && isPrefixedDecl(node)) return;
        decls.push(
          `${node.prop}: ${cleanValue(node.value)}${node.important ? " !important" : ""};`,
        );
      } else if (node.type !== "comment") {
        children.push(node);
      }
    });
    flushDecls();

    for (const node of children) {
      if (node.type === "rule") {
        let own = node.selectors.map((s) => s.replace(/\s+/g, " ").trim());
        if (ignorePrefixes) own = own.filter((s) => !isPrefixedSelector(s));
        if (!own.length) continue;
        walk(node, joinSelectors(selectors, own), atRules);
      } else if (node.type === "atrule") {
        const header = `@${node.name} ${cleanValue(node.params)}`.trim();
        if (node.nodes) {
          walk(node, selectors, [...atRules, header]);
        } else {
          blocks.push({ atRules: [...atRules, header], selectors: [], decls: [] });
        }
      }
    }
  }

  walk(postcss.parse(css), [], []);

  return blocks
    .map(({ atRules, selectors, decls }) => {
      const lines = [];
      let depth = 0;
      const open = (header) => lines.push(`${"  ".repeat(depth++)}${header} {`);
      const bodyless = !decls.length && !selectors.length;
      atRules.forEach((header, i) =>
        bodyless && i === atRules.length - 1
          ? lines.push(`${"  ".repeat(depth)}${header};`)
          : open(header),
      );
      if (selectors.length) open([...selectors].sort().join(",\n" + "  ".repeat(depth)));
      for (const decl of decls) lines.push(`${"  ".repeat(depth)}${decl}`);
      const closes = depth;
      for (let i = 0; i < closes; i++) lines.push(`${"  ".repeat(--depth)}}`);
      return lines.join("\n");
    })
    .join("\n\n")
    .concat("\n");
}

/** Build with Vite and return { entryName: css } from the manifest. */
async function buildCss() {
  const { build } = await import("vite");
  await build({
    root: ROOT,
    logLevel: "error",
    build: { outDir: BUILD_DIR, emptyOutDir: true, minify: false },
    // Sass deprecation warnings would bury the diff.
    css: { preprocessorOptions: { scss: { logger: { warn() {} } } } },
  });
  const manifest = JSON.parse(
    fs.readFileSync(path.join(BUILD_DIR, "manifest.json"), "utf8"),
  );

  const cssFor = (key, seen = new Set()) => {
    if (seen.has(key)) return [];
    seen.add(key);
    const chunk = manifest[key];
    return [
      ...(chunk.imports || []).flatMap((imported) => cssFor(imported, seen)),
      ...(chunk.css || []),
    ];
  };

  const result = {};
  for (const [key, chunk] of Object.entries(manifest)) {
    if (!chunk.isEntry) continue;
    const files = [...new Set(cssFor(key))];
    if (!files.length) continue;
    result[chunk.name] = files
      .map((file) => fs.readFileSync(path.join(BUILD_DIR, file), "utf8"))
      .join("\n");
  }
  return result;
}

/** Compile each Sass entry and report its warnings by type and location. */
async function recordWarnings(name) {
  const sass = await import("sass");
  const byEntry = {};
  const locations = new Map();

  for (const entry of SASS_ENTRIES) {
    const counts = (byEntry[entry] = {});
    sass.compile(path.join(ROOT, entry), {
      // Without verbose, Sass stops repeating a warning after five.
      verbose: true,
      logger: {
        warn(message, { deprecationType, span }) {
          const type = deprecationType?.id ?? "warn";
          counts[type] = (counts[type] ?? 0) + 1;
          const where = span?.url
            ? `${path.relative(ROOT, fileURLToPath(span.url))}:${span.start.line + 1}`
            : "(unknown)";
          const key = `${type.padEnd(16)} ${where}`;
          locations.set(key, (locations.get(key) ?? 0) + 1);
        },
      },
    });
  }

  const lines = [`# Sass warnings: ${name}`, "", "## Count by entry and type", ""];
  for (const [entry, counts] of Object.entries(byEntry)) {
    const total = Object.values(counts).reduce((sum, n) => sum + n, 0);
    lines.push(`${entry}: ${total}`);
    for (const [type, n] of Object.entries(counts).sort()) {
      lines.push(`  ${type.padEnd(16)} ${n}`);
    }
  }
  lines.push(
    "",
    `## Locations (${locations.size}), with how often each fires across all entries`,
    "",
  );
  for (const [key, n] of [...locations].sort(([a], [b]) => a.localeCompare(b))) {
    lines.push(`${key}  x${n}`);
  }

  fs.mkdirSync(WARNINGS_DIR, { recursive: true });
  const file = path.join(WARNINGS_DIR, `${name}.txt`);
  fs.writeFileSync(file, lines.join("\n") + "\n");
  console.log(`Wrote ${path.relative(ROOT, file)}: ${locations.size} locations`);
}

function writeNormalized(dir, sheets, options) {
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  for (const [name, css] of Object.entries(sheets)) {
    fs.writeFileSync(path.join(dir, `${name}.css`), normalize(css, options));
  }
}

function readSheets(dir) {
  return Object.fromEntries(
    fs
      .readdirSync(dir)
      .filter((file) => file.endsWith(".css"))
      .map((file) => [path.basename(file, ".css"), fs.readFileSync(path.join(dir, file), "utf8")]),
  );
}

async function main(command, ...args) {
  const [arg] = args;
  const ignorePrefixes = args.includes("--ignore-prefixes");
  if (command === "warnings" && arg) {
    await recordWarnings(arg);
    return;
  }
  if (command !== "snapshot" && command !== "diff") {
    console.error("usage: node scripts/css-check.js snapshot|diff|warnings <step-name>");
    process.exit(2);
  }
  const sheets = await buildCss();

  if (command === "snapshot") {
    writeNormalized(BASELINE_DIR, sheets);
    console.log(`Wrote baseline for ${Object.keys(sheets).join(", ")}`);
    return;
  }

  let baselineDir = BASELINE_DIR;
  if (ignorePrefixes) {
    baselineDir = path.join(WORK_DIR, "baseline");
    writeNormalized(baselineDir, readSheets(BASELINE_DIR), { ignorePrefixes });
  }
  writeNormalized(CURRENT_DIR, sheets, { ignorePrefixes });
  try {
    execFileSync(
      "diff",
      ["-ruN", path.relative(ROOT, baselineDir), path.relative(ROOT, CURRENT_DIR)],
      { cwd: ROOT, stdio: "inherit" },
    );
    console.log("CSS matches the baseline.");
  } catch (error) {
    if (error.status !== 1) throw error;
    process.exit(1);
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main(...process.argv.slice(2));
}
