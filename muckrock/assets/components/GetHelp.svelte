<script>
  import { onMount } from "svelte";
  import CategoryList from "./CategoryList.svelte";
  import ProblemList from "./ProblemList.svelte";
  import ContactForm from "./ContactForm.svelte";

  let { problems = {}, foiaId = "" } = $props();

  // State: "closed" | "categories" | "problems" | "contact"
  let view = $state("closed");
  let selectedCategory = $state(null);

  // Get CSRF token from the page
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value ?? "";

  // Build category list from problems data
  let categories = $derived(
    Object.entries(problems).map(([key, data]) => ({
      key,
      label: data.label,
    }))
  );

  function getOverlay() {
    return document.getElementById("modal-overlay");
  }

  function openModal() {
    view = "categories";
    const overlay = getOverlay();
    if (overlay) {
      overlay.classList.add("visible");
      overlay.addEventListener("click", closeModal, { once: true });
    }
  }

  onMount(() => {
    document.addEventListener("gethelp:open", openModal);
    return () => document.removeEventListener("gethelp:open", openModal);
  });

  function closeModal() {
    view = "closed";
    selectedCategory = null;
    const overlay = getOverlay();
    if (overlay) {
      overlay.classList.remove("visible");
    }
  }

  function selectCategory(key) {
    selectedCategory = key;
    view = "problems";
  }

  function showContact() {
    view = "contact";
  }

  function goBack() {
    if (view === "problems" || view === "contact") {
      view = "categories";
      selectedCategory = null;
    } else {
      closeModal();
    }
  }
</script>

<div class="modal" class:visible={view !== "closed"} ongethelpclose={closeModal}>
  <header>
    {#if view === "problems" || view === "contact"}
    <button type="button" class="get-help__back-button" onclick={goBack}>
      &larr; Back to categories
    </button>
    {:else}
    <h2>Get Help</h2>
    {/if}
    <button class="close-modal" onclick={closeModal}>Close</button>
  </header>
  <main>
  {#if view === "categories"}
    <CategoryList {categories} onSelect={selectCategory} onOther={showContact} />
  {:else if view === "problems" && selectedCategory && problems[selectedCategory]}
    <ProblemList
      category={problems[selectedCategory]}
      {csrfToken}
      foiaPk={foiaId}
      onBack={goBack}
    />
  {:else if view === "contact"}
    <div class="get-help__contact-view">
      <h3>Contact Support</h3>
      <ContactForm {csrfToken} foiaPk={foiaId} />
    </div>
  {/if}
  </main>
</div>

<style>
  .modal {
    padding: 0;
    max-height: 70vh;
    overflow-y: auto;
    margin-top: -5%;
  }
  .modal header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 1;
    padding: 1em;
    margin: 0;
    background: #F7F8FA;
    border-bottom: 1px solid #D5DAE0;
  }
  .modal main {
    padding: 1em;
  }

  .modal header h2 {
    font-size: 1.5em;
    line-height: 1;
    margin: 0;
  }

  .get-help__contact-view {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .get-help__back-button,
  .close-modal {
    appearance: none;
    border: none;
    border-radius: 4px;
    background-color: transparent;
    color: #4582CC;
    font-weight: 500;
    align-self: flex-start;
    font-size: 0.875rem;
    transition: background-color 0.1s linear;
  }

  .get-help__back-button:hover,
  .close-modal:hover {
    background-color: #BBD6FA;
  }

  .close-modal {
    float: none;
    margin: 0;
  }

  h3 {
    margin: 0;
    font-size: 1.125rem;
  }
</style>
