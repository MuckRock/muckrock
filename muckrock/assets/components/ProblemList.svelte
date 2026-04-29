<script>
  import ProblemItem from "./ProblemItem.svelte";

  let { category, csrfToken = "" } = $props();

  let otherProblem = {
    title: "I need help with something else.",
  }
</script>

<div class="get-help__problem-list">
  <h3>{category.label}</h3>

  {#each category.problems as problem (problem.id)}
    <ProblemItem {problem} {csrfToken} />
  {/each}

  <ProblemItem problem={otherProblem} {csrfToken} />
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
</style>
