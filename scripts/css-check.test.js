import { describe, it, expect } from "vitest";
import * as sass from "sass";

import { normalize } from "./css-check";

const compileScss = (scss) => sass.compileString(scss).css;

describe("normalize()", () => {
  it("treats native CSS nesting as equal to the Sass it replaces", () => {
    const scss = `
      .card, .panel {
        color: #FFF;
        > .title { font-weight: bold; }
        &:hover, &.active { color: red; }
        @media (min-width: 40em) {
          padding: 1rem;
          .title { font-size: 2rem; }
        }
      }
    `;
    const nativeCss = `
      .panel, .card {
        color: #fff;
        > .title { font-weight: bold; }
        &.active, &:hover { color: red; }
        @media (min-width: 40em) {
          padding: 1rem;
          .title { font-size: 2rem; }
        }
      }
    `;
    expect(normalize(nativeCss)).toBe(normalize(compileScss(scss)));
  });

  it("refuses a BEM selector built from &, which native nesting cannot express", () => {
    expect(() => normalize(".block { &__item { color: red; } }")).toThrow(/&__item/);
    expect(() => normalize(".block { &--active { color: red; } }")).toThrow(/&--active/);
  });

  it("ignores comments and whitespace", () => {
    expect(normalize("/* note */ a   b{color:red/* inline */}")).toBe(
      normalize("a b {\n  color: red;\n}"),
    );
  });

  it("ignores how rules are grouped into the same at-rule", () => {
    expect(normalize("@media print { a { color: red; } b { color: blue; } }")).toBe(
      normalize("@media print { a { color: red; } } @media print { b { color: blue; } }"),
    );
  });

  it("keeps the order of declarations, since later ones win", () => {
    expect(normalize("a { color: red; color: blue; }")).not.toBe(
      normalize("a { color: blue; color: red; }"),
    );
  });

  it("keeps the order of rules", () => {
    expect(normalize("a { color: red; } b { color: blue; }")).not.toBe(
      normalize("b { color: blue; } a { color: red; }"),
    );
  });

  it("shows removed vendor prefixes as a difference", () => {
    expect(normalize("a { display: -webkit-flex; display: flex; }")).not.toBe(
      normalize("a { display: flex; }"),
    );
  });

  it("leaves out vendor prefixes and 2009 flexbox properties when asked", () => {
    const prefixed = `
      a {
        display: -webkit-box; display: -ms-flexbox; display: box; display: flex;
        -webkit-box-pack: justify; box-pack: justify; justify-content: space-between;
        -webkit-transition: -webkit-transform .2s; transition: transform .2s;
        box-sizing: border-box; box-shadow: none;
      }
      input::-webkit-input-placeholder, input::-moz-placeholder { color: red; }
    `;
    const plain = `
      a {
        display: flex; justify-content: space-between; transition: transform .2s;
        box-sizing: border-box; box-shadow: none;
      }
    `;
    expect(normalize(prefixed, { ignorePrefixes: true })).toBe(normalize(plain));
  });

  it("gives the same result when run on its own output", () => {
    const once = normalize(compileScss(".a { b, c > d { color: red; } @media print { e: f; } }"));
    expect(normalize(once)).toBe(once);
  });

  it("replaces :root variables with their values", () => {
    const withVariables = `
      :root { --ink: #362522; --line: 1px solid var(--ink); }
      a { color: var(--ink); border: var(--line); }
    `;
    expect(normalize(withVariables)).toBe(
      normalize("a { color: #362522; border: 1px solid #362522; }"),
    );
  });

  it("keeps variables that are also set outside :root, since their value depends on scope", () => {
    const scoped = ":root { --ink: red; } .dark { --ink: white; } a { color: var(--ink); }";
    expect(normalize(scoped)).toContain("color: var(--ink);");
    expect(normalize(scoped)).toContain("--ink: #ff0000;");
  });

  it("refuses a declaration after a nested rule, which CSS and Sass order differently", () => {
    expect(() => normalize(".a { b { color: red; } color: blue; }")).toThrow(/"color" comes after/);
  });

  it("treats Sass's number and attribute-selector formatting as equal to the source's", () => {
    expect(normalize('a[href^="http"], input[type="text"] { margin: .5em -.25em; }')).toBe(
      normalize("a[href^=http], input[type=text] { margin: 0.5em -0.25em; }"),
    );
    expect(normalize('input[value="two words"] { color: red; }')).toContain('"two words"');
  });

  it("evaluates calc() of one unit to the number Sass would have printed", () => {
    const calc = `
      :root { --vr: 1.1875rem; }
      a { margin: calc(var(--vr) * 0.5) calc(var(--vr) / 3) calc(var(--vr) * -1) calc(2 * var(--vr)); }
    `;
    expect(normalize(calc)).toBe(
      normalize("a { margin: 0.59375rem 0.3958333333rem -1.1875rem 2.375rem; }"),
    );
  });

  it("leaves calc() alone when it mixes units", () => {
    expect(normalize("a { width: calc(100% - 2rem); }")).toContain("calc(100% - 2rem)");
  });

  it("compares colours at the whole-number precision browsers render", () => {
    expect(normalize("a { color: rgb(249.4494382022, 192.2359550562, 184.5505617978); }")).toBe(
      normalize("a { color: #F9C0B9; }"),
    );
    expect(normalize("a { color: rgba(51, 60, 71, 0.8); border-color: #fff; }")).toBe(
      normalize("a { color: #333c47cc; border-color: #ffffff; }"),
    );
    expect(normalize("a { color: #f9c0b9; }")).not.toBe(normalize("a { color: #f9c0ba; }"));
    expect(normalize("a { color: white; background: transparent; }")).toBe(
      normalize("a { color: #FFFFFF; background: rgba(0, 0, 0, 0); }"),
    );
    expect(normalize(".x { grid-area: red-zone; }")).toContain("red-zone");
  });

  it("treats :is() of equally specific selectors as the separate selectors", () => {
    expect(normalize(":is(ul, ol).inline li { margin: 0; }")).toBe(
      normalize("ul.inline li, ol.inline li { margin: 0; }"),
    );
    expect(normalize(":is(a, .link):hover { color: red; }")).toContain(":is(a, .link):hover");
  });

  it("refuses rules nested under selectors of different specificity, which :is() would change", () => {
    expect(() => normalize("a, .link { &:hover { color: red; } }")).toThrow(/highest specificity/);
    expect(() => normalize("ul, ol { &.inline { margin: 0; } }")).not.toThrow();
  });

  it("ignores trailing zeros in numbers", () => {
    expect(normalize("a { transition-timing-function: cubic-bezier(0.230, 0.635, 0.320, 1.0); }")).toBe(
      normalize("a { transition-timing-function: cubic-bezier(0.23, 0.635, 0.32, 1); }"),
    );
    expect(normalize("a { width: 100px; color: #100; }")).toContain("100px");
  });

  it("keeps bodyless at-rules and !important", () => {
    expect(normalize('@charset "UTF-8"; a { color: red !important; }')).toBe(
      '@charset "UTF-8";\n\na {\n  color: #ff0000 !important;\n}\n',
    );
  });
});
