window.addEventListener("DOMContentLoaded", () => {
  const el = document.getElementById("review-agency-app");
  if (!el) {
    return;
  }

  const dataEl = document.getElementById("review-agency-data");
  const data = dataEl ? JSON.parse(dataEl.textContent || "{}") : {};
  const csrfToken =
    document.querySelector<HTMLInputElement>("[name=csrfmiddlewaretoken]")?.value ?? "";
});
