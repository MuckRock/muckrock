import { mount } from "svelte";
import GetHelp from "../components/GetHelp.svelte";

window.addEventListener("DOMContentLoaded", () => {
  const el = document.getElementById("get-help-widget");
  if (el) {
    const dataEl = document.getElementById("help-problems-data");
    const problems = dataEl ? JSON.parse(dataEl.textContent || "{}") : {};

    mount(GetHelp, {
      target: el,
      props: {
        problems,
        foiaId: el.dataset.foiaId || "",
      },
    });
  }

  document.querySelectorAll<HTMLElement>("[data-gethelp-trigger]").forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      document.dispatchEvent(new CustomEvent("gethelp:open"));
    });
  });
});
