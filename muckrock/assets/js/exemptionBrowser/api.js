// Fetch-based client for /api_v1/. Returns { data, status } on success and
// throws with err.response.{data, status} on non-2xx — the shape actions.js
// callers depend on.
import Cookie from "js-cookie";

const baseURL = "/api_v1/";

function buildURL(path) {
  const base =
    typeof window !== "undefined"
      ? window.location.origin + baseURL
      : "http://localhost" + baseURL;
  return new URL(path, base);
}

async function request(method, path, { params, body } = {}) {
  const url = buildURL(path);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value);
    }
  }
  const headers = { Accept: "application/json" };
  if (method !== "GET") {
    headers["Content-Type"] = "application/json";
    const csrftoken = Cookie.get("csrftoken");
    if (csrftoken) headers["X-CSRFToken"] = csrftoken;
  }
  const init = { method, headers, credentials: "same-origin" };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }
  const response = await fetch(url, init);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const err = new Error(`Request failed with status ${response.status}`);
    err.response = { data, status: response.status };
    throw err;
  }
  return { data, status: response.status };
}

const api = {
  get: (path, config) => request("GET", path, config),
  post: (path, body) => request("POST", path, { body }),
};

export default api;