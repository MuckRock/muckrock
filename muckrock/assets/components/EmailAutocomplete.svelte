<script>
  /**
   * An email input that suggests addresses already in the system.
   *
   * Suggestions come from the email-autocomplete endpoint, the same one the
   * legacy Select2 widgets use.  The input stays a plain text field posted
   * under `name`: picking a suggestion fills it in, and a new address can
   * still be typed, since the server resolves whatever is submitted.
   *
   * Follows the ARIA combobox pattern with a listbox popup.
   */
  import { searchEmails } from "../js/emailAutocomplete";

  let {
    value = $bindable(""),
    url,
    name,
    label,
    placeholder = "Search for an email address",
  } = $props();

  const uid = $props.id();
  const inputId = `${uid}-input`;
  const listId = `${uid}-list`;

  // Short queries match most of the table, so wait for a little to go on
  const MIN_QUERY = 2;
  const DEBOUNCE_MS = 200;

  let options = $state([]);
  let open = $state(false);
  let activeIndex = $state(-1);
  let failed = $state(false);

  let timer;
  let controller;

  function search(query) {
    clearTimeout(timer);
    controller?.abort();
    if (query.trim().length < MIN_QUERY) {
      options = [];
      open = false;
      return;
    }
    timer = setTimeout(async () => {
      controller = new AbortController();
      try {
        options = await searchEmails(url, query.trim(), controller.signal);
        failed = false;
      } catch (error) {
        if (error.name === "AbortError") {
          return;
        }
        // Typing still works without suggestions, so this stays quiet
        options = [];
        failed = true;
      }
      activeIndex = -1;
      open = options.length > 0 || failed;
    }, DEBOUNCE_MS);
  }

  function choose(option) {
    value = option.email;
    close();
  }

  function close() {
    clearTimeout(timer);
    controller?.abort();
    open = false;
    activeIndex = -1;
  }

  function onKeydown(event) {
    if (!open || !options.length) {
      if (event.key === "ArrowDown" && value.trim().length >= MIN_QUERY) {
        search(value);
      }
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      activeIndex = (activeIndex + 1) % options.length;
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      activeIndex = activeIndex <= 0 ? options.length - 1 : activeIndex - 1;
    } else if (event.key === "Enter" && activeIndex >= 0) {
      // Picking a suggestion must not submit the repair form
      event.preventDefault();
      choose(options[activeIndex]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
  }
</script>

<div class="email-autocomplete">
  <label for={inputId} class="repair-field__label">{label}</label>
  <input
    id={inputId}
    type="email"
    {name}
    {placeholder}
    autocomplete="off"
    role="combobox"
    aria-autocomplete="list"
    aria-expanded={open}
    aria-controls={listId}
    aria-activedescendant={activeIndex >= 0 ? `${listId}-${activeIndex}` : undefined}
    bind:value
    oninput={() => search(value)}
    onkeydown={onKeydown}
    onblur={close}
  />

  <ul id={listId} role="listbox" class="email-autocomplete__list" hidden={!open}>
    {#each options as option, index (option.id)}
      <!-- mousedown, not click: a click lands after the input's blur has
           already closed the list -->
      <li
        id={`${listId}-${index}`}
        role="option"
        aria-selected={index === activeIndex}
        class="email-autocomplete__option"
        class:email-autocomplete__option--active={index === activeIndex}
        onmousedown={(event) => {
          event.preventDefault();
          choose(option);
        }}
      >
        <code>{option.email}</code>
        {#if option.name}<small>{option.name}</small>{/if}
      </li>
    {:else}
      {#if failed}
        <li class="email-autocomplete__note">
          Suggestions are unavailable &mdash; type the full address.
        </li>
      {/if}
    {/each}
  </ul>
</div>
