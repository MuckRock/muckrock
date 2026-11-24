// @vitest-environment jsdom
import { readFileSync } from "node:fs";
import $ from "jquery";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { initDatepickers } from "./datepicker";

// A Monday, so June 2026 opens with no leading days from May when weeks start on Monday.
const TODAY = new Date(2026, 5, 15, 12);

function mount(html) {
  document.body.innerHTML = html;
  initDatepickers();
}

function open(selector) {
  $(selector).trigger("focus");
  return $("#ui-datepicker-div");
}

function dayCell($dp, day) {
  return $dp
    .find("td")
    .not(".ui-datepicker-other-month")
    .filter((_, td) => $(td).text().trim() === String(day));
}

function isSelectable($cell) {
  return (
    $cell.find("a").length === 1 &&
    !$cell.hasClass("ui-datepicker-unselectable")
  );
}

function pick($dp, day) {
  dayCell($dp, day).find("a").trigger("click");
}

function setDate(selector, date) {
  $(selector).datepicker("setDate", date);
  return $(selector).val();
}

beforeEach(() => {
  $.fx.off = true;
  // jsdom has no layout, so jQuery treats every element as hidden and the
  // datepicker cannot position itself next to its input.
  vi.spyOn(Element.prototype, "getClientRects").mockReturnValue([{}]);
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(TODAY);
});

afterEach(() => {
  $(".hasDatepicker").datepicker("hide").datepicker("destroy");
  document.body.innerHTML = "";
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("date filter picker (.datepicker)", () => {
  beforeEach(() => {
    mount('<input class="datepicker" id="filter">');
  });

  it("offers month and year dropdowns spanning 2010 through next year", () => {
    const $dp = open("#filter");

    expect($dp.find("select.ui-datepicker-month")).toHaveLength(1);
    const years = $dp
      .find("select.ui-datepicker-year option")
      .map((_, o) => o.value)
      .get();
    expect(years[0]).toBe("2010");
    expect(years.at(-1)).toBe("2027");
  });

  it("writes the picked day as MM/DD/YYYY", () => {
    pick(open("#filter"), 20);

    expect($("#filter").val()).toBe("06/20/2026");
  });

  it("keeps dates between 2010 and a year from today", () => {
    expect(setDate("#filter", new Date(2009, 5, 1))).toBe("01/01/2010");
    expect(setDate("#filter", new Date(2028, 0, 1))).toBe("06/15/2027");
  });
});

describe("embargo expiration picker", () => {
  const form = (attrs = "") =>
    `<form id="embargo-form"${attrs}><input class="datepicker" id="id_date_embargo"></form>`;

  it("starts the week on Monday", () => {
    mount(form());

    expect(open("#id_date_embargo").find("thead th").first().text()).toBe("Mo");
  });

  it("has no month or year dropdowns", () => {
    mount(form());

    expect(open("#id_date_embargo").find("select")).toHaveLength(0);
  });

  it("only offers today through 30 days from today", () => {
    mount(form());
    const $dp = open("#id_date_embargo");

    expect(isSelectable(dayCell($dp, 14))).toBe(false);
    expect(isSelectable(dayCell($dp, 15))).toBe(true);
    expect($dp.find(".ui-datepicker-prev").hasClass("ui-state-disabled")).toBe(
      true,
    );

    $dp.find(".ui-datepicker-next").trigger("click");

    expect($dp.find(".ui-datepicker-month").text()).toBe("July");
    expect(isSelectable(dayCell($dp, 15))).toBe(true);
    expect(isSelectable(dayCell($dp, 16))).toBe(false);
    expect($dp.find(".ui-datepicker-next").hasClass("ui-state-disabled")).toBe(
      true,
    );
  });

  it("keeps the 30-day limit even though the input also has the filter class", () => {
    mount(form());

    expect(setDate("#id_date_embargo", new Date(2026, 8, 1))).toBe(
      "07/15/2026",
    );
  });

  it("writes the picked day as MM/DD/YYYY", () => {
    mount(form());
    pick(open("#id_date_embargo"), 20);

    expect($("#id_date_embargo").val()).toBe("06/20/2026");
  });

  it("opens on the existing embargo date", () => {
    mount(form(' data-default-date="07/04/2026"'));
    const $dp = open("#id_date_embargo");

    expect($dp.find(".ui-datepicker-month").text()).toBe("July");
    expect(dayCell($dp, 4).hasClass("ui-datepicker-days-cell-over")).toBe(true);
  });

  it("opens on the current month when there is no embargo date", () => {
    mount(form());

    expect(open("#id_date_embargo").find(".ui-datepicker-month").text()).toBe(
      "June",
    );
  });
});

describe("estimated completion picker", () => {
  beforeEach(() => {
    mount('<form class="change-date"><input id="id_date_estimate"></form>');
  });

  it("offers month and year dropdowns", () => {
    const $dp = open("#id_date_estimate");

    expect($dp.find("select.ui-datepicker-month")).toHaveLength(1);
    expect($dp.find("select.ui-datepicker-year")).toHaveLength(1);
  });

  it("writes the picked day as YYYY-MM-DD", () => {
    pick(open("#id_date_estimate"), 20);

    expect($("#id_date_estimate").val()).toBe("2026-06-20");
  });

  it("blocks past days but not distant future ones", () => {
    expect(isSelectable(dayCell(open("#id_date_estimate"), 14))).toBe(false);
    expect(setDate("#id_date_estimate", new Date(2030, 0, 1))).toBe(
      "2030-01-01",
    );
  });
});

it("leaves estimate fields outside the request sidebar as plain inputs", () => {
  mount('<form class="task"><input id="id_date_estimate"></form>');

  expect($("#id_date_estimate").hasClass("hasDatepicker")).toBe(false);
});

it("renders every class the datepicker stylesheet targets", () => {
  const css = readFileSync(
    "muckrock/assets/css/component/datepicker.css",
    "utf8",
  );
  const classes = [...new Set(css.match(/(?<=\.)ui-[\w-]+/g))];
  mount(
    '<form id="embargo-form"><input class="datepicker" id="id_date_embargo"></form>',
  );
  setDate("#id_date_embargo", new Date(2026, 5, 20));
  const $dp = open("#id_date_embargo");

  const missing = classes.filter(
    (c) => !$dp.is(`.${c}`) && $dp.find(`.${c}`).length === 0,
  );

  expect(classes.length).toBeGreaterThan(10);
  expect(missing).toEqual([]);
});
