# Plan: move off Sass

Proposed as a series of small PRs, each one checked before the next starts.

**Status:** Phases 0 and 1 are done (steps 0–5, PR #2312). Phase 2 is in progress on `2220-css-phase-2`, stacked on it.

## What's there now

- **Three Sass entry points:**
  - `muckrock/assets/scss/style.scss`: the main site, about 9,100 lines across 75 partials. `docViewer.scss` reuses part of it.
  - `muckrock/foiamachine/assets/scss/style.scss`: 627 lines, standalone. It uses only variables, nesting and one `@extend`.
  - `muckrock/assets/scss/print.scss`: standalone, almost plain CSS already.
- **Where the warnings come from:** most are in two old vendored libraries, Bourbon and Neat, under `muckrock/assets/vendor/`. Our own code adds the `@import`s, `$vr/2`-style division (about 170 places) and `darken()`/`lighten()` (38 places).
- **Sass features our code depends on:**
  - **Bourbon prefix mixins**, roughly 450 calls (`display(flex)`, `flex`, `justify-content`, …). They add about 2,000 vendor-prefixed lines to `main.css`, mostly for browsers that no longer exist.
  - **Neat:** only `media($medium-bp)` (33 calls) and `row` (1). There's no grid usage.
  - **Our own mixins:** 20. Only `padding` and `button` share a name with a Bourbon mixin, and both were already overriding Bourbon's everywhere they're used.
  - **Other:** 6 `@extend`s, one `@if`, and `#{$all-text-inputs}` from Bourbon.
  - **42 nested `&__x` / `&--x` selectors.** Native CSS nesting does not support these (BEM name joining), so they have to be written out in full during the CSS conversion. This is the easiest place to introduce a silent bug.
- **Build:** Vite already runs PostCSS and bundles plain-CSS `@import`, so we don't need a new build tool.

## How we check each step

The site has no visual tests, so the main check compares built CSS: build the CSS, normalise it (format it, strip comments), and diff it against a baseline from `main`. Every step says up front which diff it expects. Anything else in the diff is a bug.

Some steps also need a quick look at a fixed list of pages: home, request detail, new request, task list, doc viewer embed, FOIAMachine and the print view.

From step 7, Playwright also compares the computed styles of every element (and hover states) on those pages before and after the change, and checks with `CSS.supports` that every declaration using `var()` is still valid. This catches what the CSS diff can't, such as an invalid declaration that browsers used to ignore becoming an override once it holds `var()`.

## Steps (one small PR each)

**Phase 0: safety net**

0. ✅ **Add the CSS diff script** with a baseline snapshot. Expected diff: none (it only adds tooling).
   - `npm run css:diff` / `css:snapshot` (`scripts/css-check.js`), baseline in `scripts/css-baseline/`.
   - `npm run css:warnings -- step-N` records Sass warnings per step in `scripts/sass-warnings/`.

**Phase 1: stay on Sass and remove every deprecated feature. Built CSS stays identical except where noted.**

1. ✅ **Fix division:** `$vr/2` → `math.div` via `sass-migrator division`. Expected diff: none.
   - The migrator uses multiplication for constant divisors (`$vr*0.5`) and `math.div` only for 3 and 6.
2. ✅ **Fix colours:** `darken()`/`lighten()` → `color.adjust($lightness: …)`, which gives exactly the same colours. Expected diff: none.
   - Not quite exact: `color.adjust` doesn't clamp at 100% lightness. The one overshoot (disabled input background) is clipped with `color.to-gamut`.
3. ✅ **Drop Neat:** a local `media` mixin with the 3 breakpoints, write out `row`, remove the Neat import. Expected diff: none.
   - Neat also emitted the global `* { box-sizing: border-box }`; it now lives in `base/_box-sizing.scss`.
4. ✅ **Replace Bourbon's helpers that don't add prefixes:** `$all-text-inputs`, `placeholder`, `appearance`, `columns`, and so on. Rename our overriding mixins first so nothing changes meaning. Expected diff: none.
   - Covered `$all-text-inputs`, `clearfix` and `border-*-radius`. `placeholder`, `appearance` and `columns` do add prefixes, so they moved to step 5. No renames were needed.
5. ✅ **Replace Bourbon's prefix mixins with plain properties, then delete Bourbon.** Expected diff: only vendor-prefixed lines removed. The `if-function`, `elseif` and `global-builtin` warnings are gone after this.
   - Also removed the non-standard 2009 flexbox properties (`box-pack`, `display: box`, …). Bourbon's `placeholder` only emitted prefixed selectors, so its 4 rules became `::placeholder`.
   - `main.css` went from 220 KB to 167 KB minified. The baseline was re-snapshotted.
   - Also fixed `transition: opacity, .5s, linear` in `pattern/_task.scss`, which the commas made three transitions.
   - `sass` now requires `^1.79.0`, the first release with `color.adjust($space: …)` and `color.to-gamut`.

After Phase 1, the only warning left is `@import`. ✅ Confirmed: 90 in `style.scss`, 11 in `docViewer.scss`.

**Phase 2: Sass → plain CSS**

6. ✅ **Pilot on the two easy files:** `print.scss` and FOIAMachine. This tests the Vite plain-CSS path and the nesting decision on low-risk files.
   - Now `muckrock/assets/css/print.css` and `muckrock/foiamachine/assets/css/style.css`; FOIAMachine's variables are `:root` custom properties.
   - Vite's targets (Chrome 107, Safari 16) can't parse nesting; the production build lowers it, writing multi-selector parents as `:is(…)`, whose specificity can differ from Sass's expansion. `css:diff` now lowers both sides the same way, so it compares what production ships.
   - esbuild moves a declaration that follows a nested rule above it, but the dev server serves raw nesting, where it applies after. `css:diff` checks the `.css` sources and refuses those, and `&__x` / `&--x`.
7. ✅ **Turn colours and spacing into CSS variables** (`tokens.css` with `:root { --color-… }`). Work out the derived colours as fixed hex values first, because CSS variables can't go through Sass colour functions. The diff script swaps the variables back for their values so the comparison stays exact.
   - ✅ 7a, colours: `muckrock/assets/css/tokens.css`, with derived shades named for their origin (`--color-red-lighten-40`). Sass colour variables point at the tokens; page-local shades are fixed hex. `css:diff` evaluates `calc()` and compares colours at whole-channel precision.
   - A declaration that was invalid, and so ignored, becomes an override once it holds `var()` (`.button`'s `text-shadow: inset …` blanked grey buttons' shadow). `css:diff` can't see this; a Playwright comparison of computed styles and a `CSS.supports` check of every `var()` declaration caught it.
   - ✅ 7b, spacing and type: fonts, weights, sizes, `--lh`, `--vr` and borders are tokens; 211 calculations are `calc(var(--vr) * N)`. Found a second ignored declaration the same way: `.foia-log__request-id { font-family: $size-1 }`, removed (probably meant `font-size`).
   - Breakpoints stay Sass strings until step 9, since `var()` can't be used in `@media`.
8. ✅ **Remove the remaining Sass-only features:** write out the 20 mixins and 6 `@extend`s. Expected diff: none.
   - It was 21 mixins and 5 `@extend`s (FOIAMachine's was step 6). Mixins are inlined at each `@include`; `media()` writes its query literally.
   - Writing out `@extend dfn` puts its selectors in the `dfn` rules. Sass had also woven them into four descendant rules, as 48 selectors no template can match; those are dropped.
9. ✅ **Convert the partials to `.css`, one folder per PR:** `base` → `component` → `pattern` → `view/*` → `docViewer`. Write out every `&__`/`&--`. Each PR's CSS diff must be empty after normalising.
   - ✅ Entries and index files are plain-CSS `@import` lists, so Sass compiles each remaining partial on its own (with the variables from `additionalData`) and never sees converted CSS. Sass inlining a `.css` file moved its nested `@media` after the rule. No Sass warnings remain.
   - ✅ `base/`. Fixes three Fine Uploader images whose URLs Sass had rebased to a 404.
   - Production lowers rules nested under a selector list to `:is(list)`, which takes the list's highest specificity; `css:diff` refuses mixed-specificity parents in source, and they're written out flat.
   - ✅ `component/`, `pattern/`, `view/` and its subfolders, the doc viewer's rules and the vendored normalize and loader. Sass evaluated every variable expression and the result is inlined; BEM joins are written out; where Sass emitted declarations after a nested rule, the rule is split in two so the order holds. Every step's built CSS matched, and Playwright showed no change.
   - `style.css` declares `@charset "UTF-8"`, which Sass had added for the sortable-table arrows.
   - Only `base/_variables.scss` remains, unused; step 11 removes it with Sass.
10. **Remove unused and dead CSS, one folder per PR.** Unlike steps 6–9, the CSS diff is expected to change: only the removed rules.
    - A selector is dead when nothing MuckRock renders can match it. Search every place a class or ID can come from: Django templates, Python (form widget `attrs`, template tags, `mark_safe` HTML), JS/JSX/Svelte (`className`, `classList`, `addClass`, string building), third-party widgets (select2, jQuery UI, tooltipster, Fine Uploader, Tabulator) and HTML in agency and user content (communications, markdown).
    - Classes built at runtime (`"status-" + value`) can't be found by search; review those by hand and keep them unless the full set of values is known.
    - Also delete commented-out code blocks (for example in `view/_project.scss` and the banner's `@supports` block).
    - Candidates found so far: `.create/.update/.activate.organization` and `.account.plans` (those pages moved to Squarelet), `.form.search`, `.crowdfund__widget … .sharing`, and the `.browse` block in `pattern/_foia-log.scss`.
    - Check: `css:diff` shows only the removed rules, and the Playwright comparison of the page list shows no change.
11. **Clean up:** remove the `sass` dependency and its options in `vite.config.js`, and update `AGENTS.md`.

## Open decisions

1. ✅ **Decided: drop them.** **Vendor prefixes (step 5):** recommend dropping them outright, since `display: flex` without prefixes works in every browser we'd still support. The alternative is adding `autoprefixer` with a target browser list (`browserslist`), which keeps any prefixes that are still needed.
2. ✅ **Decided: plain CSS.** **The end state:** plain CSS, or PostCSS plugins that mimic Sass (`postcss-mixins`, `postcss-simple-vars`)? Recommend plain CSS: those plugins are basically Sass again with less tooling. The only exception would be `postcss-custom-media`, because CSS variables don't work inside `@media` queries.
3. ✅ **Decided: native nesting.** **Nesting (from step 6):** keep native CSS nesting (supported by all major browsers since 2023; Vite's targets predate it, so production builds lower it), or flatten everything? Recommend native nesting with `&__x` written out. Flattening is safer for very old browsers, but the files get much harder to read.
4. **The `@import` warning during Phase 2:** turn it off temporarily (`silenceDeprecations: ['import']`) rather than migrating to `@use`. That migration would be thrown away once the files are plain CSS.

---

_Generated by [Claude Code](https://claude.ai/code)_
