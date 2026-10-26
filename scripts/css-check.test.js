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

  it("keeps bodyless at-rules and !important", () => {
    expect(normalize('@charset "UTF-8"; a { color: red !important; }')).toBe(
      '@charset "UTF-8";\n\na {\n  color: red !important;\n}\n',
    );
  });
});
