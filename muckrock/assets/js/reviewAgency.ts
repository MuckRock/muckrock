import { mount } from "svelte";
import ReviewAgencyRepair from "../components/ReviewAgencyRepair.svelte";

window.addEventListener("DOMContentLoaded", () => {
  const el = document.getElementById("review-agency-app");
  if (!el) {
    return;
  }

  const dataEl = document.getElementById("review-agency-data");
  const data = dataEl ? JSON.parse(dataEl.textContent || "{}") : {};
  const csrfToken =
    document.querySelector<HTMLInputElement>("[name=csrfmiddlewaretoken]")?.value ?? "";

  mount(ReviewAgencyRepair, {
    target: el,
    props: {
      data,
      csrfToken,
      action: el.dataset.action || "",
    },
  });
});
