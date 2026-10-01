import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { parseLabel, searchEmails } from "./emailAutocomplete";

const jsonResponse = (data, { ok = true, status = 200 } = {}) => ({
  ok,
  status,
  json: () => Promise.resolve(data),
});

describe("parseLabel()", () => {
  it("reads a bare address", () => {
    expect(parseLabel("foia@fbi.gov")).toEqual({
      email: "foia@fbi.gov",
      name: "",
    });
  });

  it("splits a named address", () => {
    expect(parseLabel('"FOIA Office" <foia@fbi.gov>')).toEqual({
      email: "foia@fbi.gov",
      name: "FOIA Office",
    });
  });
});

describe("searchEmails()", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("queries the endpoint with q", async () => {
    fetch.mockResolvedValue(jsonResponse({ results: [] }));
    await searchEmails("/communication/email-autocomplete/", "fbi");
    const [url] = fetch.mock.calls[0];
    expect(url).toBe("/communication/email-autocomplete/?q=fbi");
  });

  it("maps results to addresses", async () => {
    fetch.mockResolvedValue(
      jsonResponse({
        results: [
          { id: 1, text: "foia@fbi.gov", selected_text: "foia@fbi.gov" },
          {
            id: 2,
            text: '"Records" <records@fbi.gov>',
            selected_text: '"Records" <records@fbi.gov>',
          },
        ],
        pagination: { more: false },
      }),
    );
    expect(await searchEmails("/e/", "fbi")).toEqual([
      { id: 1, email: "foia@fbi.gov", name: "" },
      { id: 2, email: "records@fbi.gov", name: "Records" },
    ]);
  });

  it("drops the create option", async () => {
    // Staff get a "Create" row; the repair form resolves a typed address on
    // submit, so creating it ahead of time is never needed
    fetch.mockResolvedValue(
      jsonResponse({
        results: [{ id: "new@fbi.gov", text: 'Create "new@fbi.gov"', create_id: true }],
      }),
    );
    expect(await searchEmails("/e/", "new@fbi.gov")).toEqual([]);
  });

  it("throws on an error response", async () => {
    fetch.mockResolvedValue(jsonResponse({}, { ok: false, status: 403 }));
    await expect(searchEmails("/e/", "fbi")).rejects.toThrow("403");
  });
});
