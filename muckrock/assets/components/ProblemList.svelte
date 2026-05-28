<script>
  import ProblemItem from "./ProblemItem.svelte";

  let { category, csrfToken = "", foiaPk = "" } = $props();

  let otherProblem = {
    title: "I need help with something else.",
  }
</script>

<div class="get-help__problem-list">
  <h3>{category.label}</h3>

  {#if category.description_html}
    <div class="get-help__category-description">
      {@html category.description_html}
    </div>
  {/if}

  {#each category.problems as problem (problem.id)}
    <ProblemItem
      {problem}
      {csrfToken}
      {foiaPk}
      categoryLabel={category.label}
      categoryPlaceholder={category.placeholder}
    />
  {/each}

  <ProblemItem
    problem={otherProblem}
    {csrfToken}
    {foiaPk}
    categoryLabel={category.label}
    categoryPlaceholder={category.placeholder}
  />
</div>

<style>
  .get-help__problem-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  h3 {
    margin: 0 0 1rem;
    font-size: 1.25rem;
  }

  .get-help__category-description {
    margin: 0 0 1rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    line-height: 1.5;
    background-color: #F7F8FA;
    border-radius: 4px;
  }

  .get-help__category-description :global(p:first-child) {
    margin-top: 0;
  }

  .get-help__category-description :global(p:last-child) {
    margin-bottom: 0;
  }
</style>
