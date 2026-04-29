<script>
  import ContactForm from "./ContactForm.svelte";
  import Self from './ProblemItem.svelte';

  let { problem, csrfToken = "" } = $props();
  let showContact = $state(false);
</script>

<details class="get-help__problem-item">
  <summary>{problem.title}</summary>
  <div class="get-help__problem-content">
    {#if problem.resolution_html}
      <div class="get-help__resolution">
        {@html problem.resolution_html}
      </div>
    {/if}

    {#if problem.children && problem.children.length > 0}
      <div class="get-help__children">
        {#each problem.children as child (child.id)}
          <Self problem={child} {csrfToken} />
        {/each}
        <Self problem={{id: "other", title: "Other"}} {csrfToken} />
      </div>
    {:else}
      {#if problem.resolution_html && !showContact}
      <button
          type="button"
          class="button"
          onclick={() => (showContact = true)}
      >
          I still need help
      </button>
      {:else}
      <ContactForm flagCategory={problem.flag_category} {csrfToken} />
      {/if}
    {/if}
  </div>
</details>

<style>
  .get-help__problem-item {
    background-color: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
  }

  summary {
    margin: 0;
    padding: 0.75rem 1rem;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    overflow: hidden;
  }

  summary:hover {
    background-color: #BBD6FA;
  }

  .get-help__problem-content {
    border-top: 1px solid #f3f3f3;
    padding: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .get-help__resolution {
    margin: 0;
    padding: 0.5rem;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .get-help__children {
    display: flex;
    flex-direction: column;
    gap: 0.25em;
  }
</style>
