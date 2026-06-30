import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("./api", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
  rootDomain: "https://dev.muckrock.com",
}));

import api from "./api";
import {
  searchExemptions,
  submitExemption,
  UPDATE_EXEMPTION_QUERY,
  UPDATE_EXEMPTION_RESULTS,
  LOAD_EXEMPTION_RESULTS,
  UPDATE_VISIBILITY_FILTER,
  SUBMIT_EXEMPTION,
} from "./actions";

describe("searchExemptions", () => {
  let dispatch;

  beforeEach(() => {
    dispatch = vi.fn();
    api.get.mockReset();
    api.post.mockReset();
  });

  it("calls api.get with the exemption path and query as params", async () => {
    api.get.mockResolvedValue({ data: { results: [] } });
    const query = { q: "foo", jurisdiction: 1 };
    await searchExemptions(query)(dispatch);
    expect(api.get).toHaveBeenCalledWith("exemption/", { params: query });
  });

  it("dispatches load + query update before the request resolves", async () => {
    let resolve;
    api.get.mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    const promise = searchExemptions({ q: "foo" })(dispatch);
    expect(dispatch).toHaveBeenNthCalledWith(1, {
      type: LOAD_EXEMPTION_RESULTS,
    });
    expect(dispatch).toHaveBeenNthCalledWith(2, {
      type: UPDATE_EXEMPTION_QUERY,
      query: "foo",
    });
    resolve({ data: { results: [] } });
    await promise;
  });

  it("on success dispatches results and SHOW_SEARCH visibility filter", async () => {
    const results = [{ id: 1 }, { id: 2 }];
    api.get.mockResolvedValue({ data: { results } });
    await searchExemptions({ q: "foo" })(dispatch);
    expect(dispatch).toHaveBeenCalledWith({
      type: UPDATE_EXEMPTION_RESULTS,
      results,
    });
    expect(dispatch).toHaveBeenCalledWith({
      type: UPDATE_VISIBILITY_FILTER,
      filter: "SHOW_SEARCH",
    });
  });

  it("on failure dispatches SHOW_ERROR visibility filter", async () => {
    api.get.mockRejectedValue(new Error("boom"));
    await searchExemptions({ q: "foo" })(dispatch);
    expect(dispatch).toHaveBeenCalledWith({
      type: UPDATE_VISIBILITY_FILTER,
      filter: "SHOW_ERROR",
    });
  });

  it("reads results from response.data.results (not response.results)", async () => {
    api.get.mockResolvedValue({ data: { results: ["a"] } });
    await searchExemptions({ q: "foo" })(dispatch);
    const call = dispatch.mock.calls.find(
      (c) => c[0].type === UPDATE_EXEMPTION_RESULTS,
    );
    expect(call[0].results).toEqual(["a"]);
  });
});

describe("submitExemption", () => {
  let dispatch;

  beforeEach(() => {
    dispatch = vi.fn();
    api.get.mockReset();
    api.post.mockReset();
  });

  it("calls api.post with the submit path and the data as the body argument", async () => {
    api.post.mockResolvedValue({ data: { ok: true } });
    const data = { foia: 42, language: "en" };
    await submitExemption(data)(dispatch);
    expect(api.post).toHaveBeenCalledWith("exemption/submit/", data);
  });

  it("dispatches LOADING before the request resolves", async () => {
    let resolve;
    api.post.mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    const promise = submitExemption({ foia: 1 })(dispatch);
    expect(dispatch).toHaveBeenCalledWith({
      type: SUBMIT_EXEMPTION,
      state: "LOADING",
      response: undefined,
    });
    resolve({ data: { ok: true } });
    await promise;
  });

  it("on success dispatches SUCCESS with the full response", async () => {
    const response = { data: { ok: true }, status: 200 };
    api.post.mockResolvedValue(response);
    await submitExemption({ foia: 1 })(dispatch);
    expect(dispatch).toHaveBeenCalledWith({
      type: SUBMIT_EXEMPTION,
      state: "SUCCESS",
      response,
    });
  });

  it("on failure dispatches FAILURE with error.response as a stray second dispatch arg", async () => {
    const errResponse = { data: { error: "bad" }, status: 400 };
    api.post.mockRejectedValue({ response: errResponse });
    await submitExemption({ foia: 1 })(dispatch);
    // actions.js:87 has a misplaced paren: dispatch(submitExemptionState('FAILURE'), error.response)
    // — error.response is passed to dispatch() rather than into submitExemptionState(), so
    // the FAILURE action carries response: undefined and dispatch receives a stray 2nd arg.
    // Pinning current behavior; do not "fix" without coordinating with consumers.
    expect(dispatch).toHaveBeenCalledWith(
      { type: SUBMIT_EXEMPTION, state: "FAILURE", response: undefined },
      errResponse,
    );
  });
});
