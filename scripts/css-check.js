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
const SCSS_DIR = path.join(ROOT, "muckrock/assets/scss");

/** Flatten nested rules into "outer inner" selectors, as Sass does. */
/** [ids, classes, types] specificity; a function's arguments count as written. */
export function specificity(selector) {
  const plain = selector.replace(/::?[\w-]+\(/g, (m) => (m.startsWith("::") ? " " : " :x ")).replace(/[()]/g, " ");
  const ids = (plain.match(/#[\w-]+/g) ?? []).length;
  const classes = (plain.match(/\.[\w-]+|\[[^\]]*\]|(?<!:):(?!:)[\w-]+/g) ?? []).length;
  const types = (plain.match(/(?<![\w.#:-])[a-z][\w-]*|::[\w-]+/gi) ?? []).length;
  return [ids, classes, types];
}

const sameSpecificity = (selectors) =>
  new Set(selectors.map((selector) => specificity(selector).join())).size <= 1;

function joinSelectors(parents, children) {
  if (!parents.length) return children;
  // Production builds write nested rules under a selector list as :is(list),
  // which takes the list's highest specificity for every selector.
  if (!sameSpecificity(parents)) {
    throw new Error(
      `rules nested in "${parents.join(", ")}" would take their highest specificity once built; write them out`,
    );
  }
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

/** Custom properties set only on a top-level :root rule, so var() can be replaced by the value. */
function rootVariables(root) {
  const values = new Map();
  const setElsewhere = new Set();
  root.walkDecls(/^--/, (decl) => {
    const rule = decl.parent;
    const atRoot =
      rule.type === "rule" && rule.parent.type === "root" && rule.selector.trim() === ":root";
    if (atRoot) values.set(decl.prop, decl.value);
    else setElsewhere.add(decl.prop);
  });
  for (const name of setElsewhere) values.delete(name);
  return values;
}

function resolveVariables(value, variables) {
  const reference = /var\(\s*(--[\w-]+)\s*(?:,[^()]*)?\)/g;
  // Variables may refer to other variables.
  for (let depth = 0; depth < 10; depth++) {
    const resolved = value.replace(reference, (match, name) =>
      variables.has(name) ? variables.get(name) : match,
    );
    if (resolved === value) break;
    value = resolved;
  }
  return value;
}

// Sass prints at most 10 decimal places.
const formatNumber = (number) => String(Number(number.toFixed(10)));

/** Value of a calc() expression of numbers sharing one unit, or null if it has anything else. */
function evaluateExpression(expression) {
  const tokens = expression.match(/\d*\.?\d+(?:e[+-]?\d+)?[a-z%]*|[-+*/()]|\S/gi) ?? [];
  let position = 0;
  const peek = () => tokens[position];
  const fail = () => {
    throw new Error("unsupported");
  };

  function primary() {
    const token = tokens[position++];
    if (token === "(") {
      const value = sum();
      if (tokens[position++] !== ")") fail();
      return value;
    }
    if (token === "-") {
      const value = primary();
      return { number: -value.number, unit: value.unit };
    }
    const match = /^(\d*\.?\d+(?:e[+-]?\d+)?)([a-z%]*)$/i.exec(token ?? "");
    if (!match) fail();
    return { number: Number(match[1]), unit: match[2] };
  }
  function product() {
    let left = primary();
    while (peek() === "*" || peek() === "/") {
      const operator = tokens[position++];
      const right = primary();
      if (operator === "*") {
        if (left.unit && right.unit) fail();
        left = { number: left.number * right.number, unit: left.unit || right.unit };
      } else {
        if (right.unit) fail();
        left = { number: left.number / right.number, unit: left.unit };
      }
    }
    return left;
  }
  function sum() {
    let left = product();
    while (peek() === "+" || peek() === "-") {
      const operator = tokens[position++];
      const right = product();
      if (left.unit !== right.unit) fail();
      left = {
        number: operator === "+" ? left.number + right.number : left.number - right.number,
        unit: left.unit,
      };
    }
    return left;
  }

  try {
    const result = sum();
    if (position !== tokens.length) fail();
    return `${formatNumber(result.number)}${result.unit}`;
  } catch {
    return null;
  }
}

/** Replace calc() of plain numbers with its result, as Sass printed it. */
function evaluateCalc(value) {
  const innermost = /calc\(([^()]*(?:\([^()]*\)[^()]*)*)\)/g;
  for (let depth = 0; depth < 10; depth++) {
    const evaluated = value.replace(innermost, (match, expression) => {
      const result = evaluateExpression(expression);
      return result ?? match;
    });
    if (evaluated === value) break;
    value = evaluated;
  }
  return value;
}

const NAMED_COLORS = {
  aqua: "#00ffff", black: "#000000", blue: "#0000ff", fuchsia: "#ff00ff",
  gray: "#808080", green: "#008000", grey: "#808080", lime: "#00ff00",
  maroon: "#800000", navy: "#000080", olive: "#808000", orange: "#ffa500",
  purple: "#800080", red: "#ff0000", silver: "#c0c0c0", teal: "#008080",
  transparent: "#00000000", white: "#ffffff", yellow: "#ffff00",
};
const NAMED_COLOR = new RegExp(`(?<![\\w.-])(${Object.keys(NAMED_COLORS).join("|")})(?![\\w.-])`, "gi");

/**
 * Write named, hex, rgb() and rgba() colours as lowercase hex with whole-number
 * channels, the precision browsers render at.
 */
function canonicalColors(value) {
  const hex = (channels) =>
    "#" +
    channels
      .map((channel) => Math.round(Math.min(255, Math.max(0, channel))).toString(16).padStart(2, "0"))
      .join("")
      .replace(/^([0-9a-f]{6})ff$/, "$1");
  return value
    .replace(NAMED_COLOR, (name) => NAMED_COLORS[name.toLowerCase()])
    .replace(/#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})\b/gi, (match, digits) => {
      const full = digits.length <= 4 ? [...digits].map((d) => d + d).join("") : digits;
      return hex(full.match(/../g).map((pair) => parseInt(pair, 16)));
    })
    .replace(
      /rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)(%?)\s*)?\)/gi,
      (match, r, g, b, alpha = "1", percent) => {
        const a = percent ? Number(alpha) / 100 : Number(alpha);
        return hex([Number(r), Number(g), Number(b), a * 255]);
      },
    );
}

function cleanValue(value, variables = new Map()) {
  value = resolveVariables(value, variables)
    .replace(/\s+/g, " ")
    .trim()
    // Sass writes 0.5 where hand-written CSS often has .5.
    .replace(/(^|[^\w.#])\.(\d)/g, (match, before, digit) => `${before}0.${digit}`)
    .replace(/(?<![\w#.-])(\d+)\.(\d*?)0+(?!\d)/g, (match, whole, fraction) =>
      fraction ? `${whole}.${fraction}` : whole,
    );
  return canonicalColors(evaluateCalc(value));
}

// Sass drops the quotes around an attribute value that is a plain identifier.
function cleanSelector(selector) {
  return selector
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\[([\w-]+)([~|^$*]?=)(["'])(-?[A-Za-z_][\w-]*)\3\]/g, "[$1$2$4]");
}

/** Expand :is(a, b) into separate selectors when that keeps every selector's specificity. */
function expandIs(selector) {
  const match = /:is\(([^()]*)\)/.exec(selector);
  if (!match) return [selector];
  const options = match[1].split(",").map((option) => option.trim());
  if (!sameSpecificity(options)) return [selector];
  return options.flatMap((option) =>
    expandIs(selector.slice(0, match.index) + option + selector.slice(match.index + match[0].length)),
  );
}

/**
 * Turn a stylesheet into a flat list of rules, each with the at-rules that
 * wrap it, then print one block per rule.
 *
 * var() references to :root custom properties are replaced by their values.
 * With ignorePrefixes, vendor-prefixed declarations and selectors are left out.
 *
 * Throws on a declaration that follows a nested rule: CSS applies it after
 * that rule, where Sass moved it before, so flattening it would hide a change.
 */
export function normalize(css, { ignorePrefixes = false } = {}) {
  const blocks = [];
  const root = postcss.parse(css);
  const variables = rootVariables(root);

  function walk(container, selectors, atRules) {
    let decls = [];
    const flushDecls = () => {
      if (decls.length) blocks.push({ atRules, selectors, decls });
      decls = [];
    };

    const children = [];
    container.each((node) => {
      if (node.type === "decl") {
        if (variables.has(node.prop)) return;
        if (ignorePrefixes && isPrefixedDecl(node)) return;
        if (children.some((child) => child.nodes)) {
          throw new Error(
            `"${node.prop}" comes after a nested rule in "${selectors.join(", ")}"; move it above`,
          );
        }
        decls.push(
          `${node.prop}: ${cleanValue(node.value, variables)}${node.important ? " !important" : ""};`,
        );
      } else if (node.type !== "comment") {
        children.push(node);
      }
    });
    flushDecls();

    for (const node of children) {
      if (node.type === "rule") {
        let own = node.selectors.map(cleanSelector).flatMap(expandIs);
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

  walk(root, [], []);

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

/**
 * Lower each sheet for Vite's browser targets, as its minified production
 * build does, so nesting is compared as the :is() selectors browsers get.
 */
async function lowerForTargets(sheets) {
  const { resolveConfig, transformWithEsbuild } = await import("vite");
  const config = await resolveConfig({ root: ROOT, logLevel: "error" }, "build");
  const lowered = {};
  for (const [name, css] of Object.entries(sheets)) {
    const result = await transformWithEsbuild(css, `${name}.css`, {
      loader: "css",
      target: config.build.cssTarget,
    });
    lowered[name] = result.code;
  }
  return lowered;
}

/**
 * Throw if hand-written CSS uses nesting that the Vite dev server and the
 * production build would treat differently, or that browsers cannot parse.
 */
function checkSources() {
  for (const file of fs.globSync("muckrock/**/assets/{css,scss}/**/*.css", { cwd: ROOT })) {
    try {
      normalize(fs.readFileSync(path.join(ROOT, file), "utf8"));
    } catch (error) {
      throw new Error(`${file}: ${error.message}`);
    }
  }
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

/** Compile each remaining Sass partial, as Vite does, and report its warnings. */
async function recordWarnings(name) {
  const sass = await import("sass");
  const byEntry = {};
  const locations = new Map();

  const partials = fs
    .globSync("muckrock/{assets,foiamachine/assets}/**/*.scss", { cwd: ROOT })
    .filter((file) => !file.endsWith("_variables.scss"))
    .sort();
  for (const entry of partials) {
    const counts = (byEntry[entry] = {});
    const file = path.join(ROOT, entry);
    sass.compileString(`@use "base/variables" as *;\n${fs.readFileSync(file, "utf8")}`, {
      url: pathToFileURL(file),
      loadPaths: [SCSS_DIR],
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
  const warned = Object.entries(byEntry).filter(([, counts]) => Object.keys(counts).length);
  lines.push(`${Object.keys(byEntry).length} Sass files compiled, ${warned.length} with warnings`, "");
  for (const [entry, counts] of warned) {
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
  checkSources();
  const sheets = await lowerForTargets(await buildCss());

  if (command === "snapshot") {
    writeNormalized(BASELINE_DIR, sheets);
    console.log(`Wrote baseline for ${Object.keys(sheets).join(", ")}`);
    return;
  }

  // Re-processed so a change to the pipeline doesn't need a new snapshot.
  const baselineDir = path.join(WORK_DIR, "baseline");
  writeNormalized(baselineDir, await lowerForTargets(readSheets(BASELINE_DIR)), {
    ignorePrefixes,
  });
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
