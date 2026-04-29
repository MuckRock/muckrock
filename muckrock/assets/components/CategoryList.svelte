<script>
  let { categories, onSelect, onOther } = $props();
</script>

<div class="get-help__category-list">
  <h3>What do you need help with?</h3>
  <ul>
    {#each categories as category (category.key)}
      <li>
        <button type="button" class="get-help__category-button" onclick={() => onSelect(category.key)}>
          {category.label}
        </button>
      </li>
    {/each}
    <li>
      <button type="button" class="get-help__category-button get-help__category-other" onclick={onOther}>
        Other
      </button>
    </li>
  </ul>
</div>

<style>
  .get-help__category-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  h3 {
    margin: 0;
    font-size: 1.125rem;
  }

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .get-help__category-button {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.625rem 0.75rem;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    font-size: 0.875rem;
    font-family: inherit;
    font-weight: 500;
  }

  .get-help__category-button:hover {
    background-color: #BBD6FA;
  }

  .get-help__category-other {
    font-style: italic;
    color: #666;
  }
</style>
