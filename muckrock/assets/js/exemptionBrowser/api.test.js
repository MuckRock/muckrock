import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("js-cookie", () => ({
  default: { get: vi.fn() },
}));

import Cookie from "js-cookie";
import api, { rootDomain } from "./api";

const jsonResponse = (data, { ok = true, status = 200 } = {}) => ({
  ok,
  status,
  json: () => Promise.resolve(data),
});

describe("api transport", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    Cookie.get.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("rootDomain", () => {
    it("defaults to dev.muckrock.com when not in staging or production", () => {
      // process.env.NODE_ENV is unset (or "test") in vitest, so we get the default branch.
      expect(rootDomain).toBe("https://dev.muckrock.com");
    });
  });

  describe("get()", () => {
    it("requests baseURL + path with no query string when no params given", async () => {
      fetch.mockResolvedValue(jsonResponse({ results: [] }));
      await api.get("exemption/");
      expect(fetch).toHaveBeenCalledTimes(1);
      const [url] = fetch.mock.calls[0];
      expect(String(url)).toBe("https://dev.muckrock.com/api_v1/exemption/");
    });

    it("appends params as a URL-encoded query string", async () => {
      fetch.mockResolvedValue(jsonResponse({ results: [] }));
      await api.get("exemption/", {
        params: { q: "foo bar", jurisdiction: 1 },
      });
      const [url] = fetch.mock.calls[0];
      expect(String(url)).toBe(
        "https://dev.muckrock.com/api_v1/exemption/?q=foo+bar&jurisdiction=1",
      );
    });

    it("uses GET and does not set Content-Type or X-CSRFToken", async () => {
      Cookie.get.mockReturnValue("token-should-not-appear");
      fetch.mockResolvedValue(jsonResponse({ results: [] }));
      await api.get("exemption/", { params: { q: "x" } });
      const [, init] = fetch.mock.calls[0];
      expect(init.method).toBe("GET");
      expect(init.headers).toEqual({ Accept: "application/json" });
      expect(init.body).toBeUndefined();
    });

    it("sends same-origin credentials so the session cookie is included", async () => {
      fetch.mockResolvedValue(jsonResponse({ results: [] }));
      await api.get("exemption/");
      const [, init] = fetch.mock.calls[0];
      expect(init.credentials).toBe("same-origin");
    });

    it("resolves with { data, status } on success", async () => {
      fetch.mockResolvedValue(
        jsonResponse({ results: [1, 2] }, { ok: true, status: 200 }),
      );
      const response = await api.get("exemption/");
      expect(response).toEqual({ data: { results: [1, 2] }, status: 200 });
    });
  });

  describe("post()", () => {
    it("sends POST with JSON body to baseURL + path", async () => {
      fetch.mockResolvedValue(jsonResponse({ ok: true }, { status: 201 }));
      await api.post("exemption/submit/", { foia: 7, language: "en" });
      const [url, init] = fetch.mock.calls[0];
      expect(String(url)).toBe(
        "https://dev.muckrock.com/api_v1/exemption/submit/",
      );
      expect(init.method).toBe("POST");
      expect(init.body).toBe(JSON.stringify({ foia: 7, language: "en" }));
    });

    it("sets Content-Type: application/json on POST", async () => {
      fetch.mockResolvedValue(jsonResponse({}));
      await api.post("exemption/submit/", { foia: 1 });
      const [, init] = fetch.mock.calls[0];
      expect(init.headers["Content-Type"]).toBe("application/json");
    });

    it("reads csrftoken from the cookie and forwards it as X-CSRFToken", async () => {
      Cookie.get.mockReturnValue("abc123");
      fetch.mockResolvedValue(jsonResponse({}));
      await api.post("exemption/submit/", { foia: 1 });
      expect(Cookie.get).toHaveBeenCalledWith("csrftoken");
      const [, init] = fetch.mock.calls[0];
      expect(init.headers["X-CSRFToken"]).toBe("abc123");
    });

    it("omits X-CSRFToken when no csrftoken cookie is set", async () => {
      Cookie.get.mockReturnValue(undefined);
      fetch.mockResolvedValue(jsonResponse({}));
      await api.post("exemption/submit/", { foia: 1 });
      const [, init] = fetch.mock.calls[0];
      expect(init.headers["X-CSRFToken"]).toBeUndefined();
    });

    it("resolves with { data, status } on success", async () => {
      fetch.mockResolvedValue(
        jsonResponse({ ok: true }, { ok: true, status: 201 }),
      );
      const response = await api.post("exemption/submit/", { foia: 1 });
      expect(response).toEqual({ data: { ok: true }, status: 201 });
    });

    it("rejects with err.response.{data,status} on non-2xx, mirroring axios", async () => {
      fetch.mockResolvedValue(
        jsonResponse({ error: "bad" }, { ok: false, status: 400 }),
      );
      await expect(
        api.post("exemption/submit/", { foia: 1 }),
      ).rejects.toMatchObject({
        response: { data: { error: "bad" }, status: 400 },
      });
    });

    it("rejects gracefully when the error body is not JSON", async () => {
      fetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error("not json")),
      });
      await expect(
        api.post("exemption/submit/", { foia: 1 }),
      ).rejects.toMatchObject({
        response: { data: null, status: 500 },
      });
    });
  });
});
