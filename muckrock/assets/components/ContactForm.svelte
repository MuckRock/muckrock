<script>
  import { showMessage } from "../js/messages";

  let { flagCategory = "", csrfToken = "" } = $props();
  let text = $state("");
  let submitted = $state(false);
  let errorMessage = $state("");

  async function handleSubmit(event) {
    event.preventDefault();
    submitted = true;
    errorMessage = "";

    const form = event.target;
    const formData = new FormData(form);

    try {
      const response = await fetch(window.location.href, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        text = "";
        showMessage(data.message, "success");
        form.dispatchEvent(
          new CustomEvent("gethelpclose", { bubbles: true })
        );
      } else {
        errorMessage = data.message || "Something went wrong. Please try again.";
        submitted = false;
      }
    } catch {
      errorMessage = "A network error occurred. Please try again.";
      submitted = false;
    }
  }
</script>

<form method="post" class="get-help__contact-form" onsubmit={handleSubmit}>
  <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
  <input type="hidden" name="action" value="flag" />
  <input type="hidden" name="flag-category" value={flagCategory} />
  <textarea
    id="flag-text"
    name="flag-text"
    bind:value={text}
    required
    rows="4"
    placeholder="Describe your issue, providing as much detail as you can."
  ></textarea>
  {#if errorMessage}
    <p class="get-help__contact-form-error">{errorMessage}</p>
  {/if}
  <div class="get-help__contact-form-actions">
    <button type="submit" class="primary button" disabled={!text.trim() || submitted}>
      {submitted ? "Sending..." : "Contact Support"}
    </button>
  </div>
</form>

<style>
  .get-help__contact-form {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  textarea {
    width: 100%;
    margin: 0;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-family: inherit;
    font-size: 0.875rem;
    resize: vertical;
  }

  .get-help__contact-form-actions {
    display: flex;
    justify-content: flex-end;
  }

  .get-help__contact-form-error {
    color: #b00;
    font-size: 0.8125rem;
    margin: 0;
  }
</style>
