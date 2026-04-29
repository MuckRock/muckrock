<script>
  import CategoryList from "./CategoryList.svelte";
  import ProblemList from "./ProblemList.svelte";
  import ContactForm from "./ContactForm.svelte";

  let { problems = {}, foiaId = "" } = $props();

  // State: "closed" | "categories" | "problems" | "contact"
  let view = $state("closed");
  let selectedCategory = $state(null);

  // Get CSRF token from the page
  let csrfToken = $derived(
    document.querySelector("[name=csrfmiddlewaretoken]")?.value ?? ""
  );

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

{#if view === "closed"}
  <button type="button" class="button get-help__trigger" onclick={openModal}>
    Get Help
  </button>
{/if}

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
  {#if view === "categories"}
    <CategoryList {categories} onSelect={selectCategory} onOther={showContact} />
  {:else if view === "problems" && selectedCategory && problems[selectedCategory]}
    <ProblemList
      category={problems[selectedCategory]}
      {csrfToken}
      onBack={goBack}
    />
  {:else if view === "contact"}
    <div class="get-help__contact-view">
      <h3>Contact Support</h3>
      <ContactForm flagCategory="" {csrfToken} />
    </div>
  {/if}
</div>

<style>
  .modal header {
    display: flex;
    justify-content: space-between;
    align-items: center;
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
