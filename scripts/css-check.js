/**
 * Build the site's CSS, normalise it, and compare it with the committed
 * baseline in scripts/css-baseline/.
 *
 *   npm run css:diff       exit 1 and print a unified diff if the CSS changed
 *   npm run css:snapshot   overwrite the baseline with the current build
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

function cleanValue(value) {
  return value
    .replace(/\s+/g, " ")
    .trim()
    .replace(/#[0-9a-f]{3,8}\b/gi, (hex) => hex.toLowerCase());
}

/**
 * Turn a stylesheet into a flat list of rules, each with the at-rules that
 * wrap it, then print one block per rule.
 */
export function normalize(css) {
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
        const own = node.selectors.map((s) => s.replace(/\s+/g, " ").trim());
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

function writeNormalized(dir, sheets) {
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  for (const [name, css] of Object.entries(sheets)) {
    fs.writeFileSync(path.join(dir, `${name}.css`), normalize(css));
  }
}

async function main(command) {
  if (command !== "snapshot" && command !== "diff") {
    console.error("usage: node scripts/css-check.js snapshot|diff");
    process.exit(2);
  }
  const sheets = await buildCss();

  if (command === "snapshot") {
    writeNormalized(BASELINE_DIR, sheets);
    console.log(`Wrote baseline for ${Object.keys(sheets).join(", ")}`);
    return;
  }

  writeNormalized(CURRENT_DIR, sheets);
  try {
    execFileSync(
      "diff",
      ["-ruN", path.relative(ROOT, BASELINE_DIR), path.relative(ROOT, CURRENT_DIR)],
      { cwd: ROOT, stdio: "inherit" },
    );
    console.log("CSS matches the baseline.");
  } catch (error) {
    if (error.status !== 1) throw error;
    process.exit(1);
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main(process.argv[2]);
}
