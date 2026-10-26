# Plan: move off Sass

Proposed as a series of small PRs, each one checked before the next starts.

## What's there now

- **Three Sass entry points:**
  - `muckrock/assets/scss/style.scss`: the main site, about 9,100 lines across 75 partials. `docViewer.scss` reuses part of it.
  - `muckrock/foiamachine/assets/scss/style.scss`: 627 lines, standalone. It uses only variables, nesting and one `@extend`.
  - `muckrock/assets/scss/print.scss`: standalone, almost plain CSS already.
- **Where the warnings come from:** most are in two old vendored libraries, Bourbon and Neat, under `muckrock/assets/vendor/`. Our own code adds the `@import`s, `$vr/2`-style division (about 170 places) and `darken()`/`lighten()` (38 places).
- **Sass features our code depends on:**
  - **Bourbon prefix mixins**, roughly 450 calls (`display(flex)`, `flex`, `justify-content`, …). They add about 2,000 vendor-prefixed lines to `main.css`, mostly for browsers that no longer exist.
  - **Neat:** only `media($medium-bp)` (33 calls) and `row` (1). There's no grid usage.
  - **Our own mixins:** 20. Our `border-radius`, `box-shadow` and `border` mixins have the same names as Bourbon's and override them. Easy to get wrong when removing Bourbon.
  - **Other:** 6 `@extend`s, one `@if`, and `#{$all-text-inputs}` from Bourbon.
  - **42 nested `&__x` / `&--x` selectors.** Native CSS nesting does not support these (BEM name joining), so they have to be written out in full during the CSS conversion. This is the easiest place to introduce a silent bug.
- **Build:** Vite already runs PostCSS and bundles plain-CSS `@import`, so we don't need a new build tool. (`AGENTS.md` still says Webpack, which is out of date.)

## How we check each step

The site has no visual tests, so the main check compares built CSS: build the CSS, normalise it (format it, strip comments), and diff it against a baseline from `main`. Every step says up front which diff it expects. Anything else in the diff is a bug.

Some steps also need a quick look at a fixed list of pages: home, request detail, new request, task list, doc viewer embed, FOIAMachine and the print view.

## Steps (one small PR each)

**Phase 0: safety net**

0. **Add the CSS diff script** with a baseline snapshot. Expected diff: none (it only adds tooling).

**Phase 1: stay on Sass and remove every deprecated feature. Built CSS stays identical except where noted.**

1. **Fix division:** `$vr/2` → `math.div` via `sass-migrator division`. Expected diff: none.
2. **Fix colours:** `darken()`/`lighten()` → `color.adjust($lightness: …)`, which gives exactly the same colours. Expected diff: none.
3. **Drop Neat:** a local `media` mixin with the 3 breakpoints, write out `row`, remove the Neat import. Expected diff: none.
4. **Replace Bourbon's helpers that don't add prefixes:** `$all-text-inputs`, `placeholder`, `appearance`, `columns`, and so on. Rename our overriding mixins first so nothing changes meaning. Expected diff: none.
5. **Replace Bourbon's prefix mixins with plain properties, then delete Bourbon.** Expected diff: only vendor-prefixed lines removed. The `if-function`, `elseif` and `global-builtin` warnings are gone after this.

After Phase 1, the only warning left is `@import`.

**Phase 2: Sass → plain CSS**

6. **Pilot on the two easy files:** `print.scss` and FOIAMachine. This tests the Vite plain-CSS path and the nesting decision on low-risk files.
7. **Turn colours and spacing into CSS variables** (`tokens.css` with `:root { --color-… }`). Work out the derived colours as fixed hex values first, because CSS variables can't go through Sass colour functions. The diff script swaps the variables back for their values so the comparison stays exact.
8. **Remove the remaining Sass-only features:** write out the 20 mixins and 6 `@extend`s. Expected diff: none.
9. **Convert the partials to `.css`, one folder per PR:** `base` → `component` → `pattern` → `view/*` → `docViewer`. Write out every `&__`/`&--`. Each PR's CSS diff must be empty after normalising.
10. **Clean up:** remove the `sass` dependency and its options in `vite.config.js`, and update `AGENTS.md`.

## Open decisions

1. **Vendor prefixes (step 5):** recommend dropping them outright, since `display: flex` without prefixes works in every browser we'd still support. The alternative is adding `autoprefixer` with a target browser list (`browserslist`), which keeps any prefixes that are still needed.
2. **The end state:** plain CSS, or PostCSS plugins that mimic Sass (`postcss-mixins`, `postcss-simple-vars`)? Recommend plain CSS: those plugins are basically Sass again with less tooling. The only exception would be `postcss-custom-media`, because CSS variables don't work inside `@media` queries.
3. **Nesting (from step 6):** keep native CSS nesting (supported by all major browsers since 2023), or flatten everything? Recommend native nesting with `&__x` written out. Flattening is safer for very old browsers, but the files get much harder to read.
4. **The `@import` warning during Phase 2:** turn it off temporarily (`silenceDeprecations: ['import']`) rather than migrating to `@use`. That migration would be thrown away once the files are plain CSS.

---

_Generated by [Claude Code](https://claude.ai/code)_
