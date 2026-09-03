<script>
  /**
   * Repair one or several of an agency's broken communication channels.
   *
   * Everything arrives as props -- the component makes no fetches of its own.
   * It owns selection state across the channel cards and posts a normal form,
   * so the server stays the single place where a repair is validated.
   *
   * Unstyled on purpose: the markup is a scaffold for manual design work.
   */
  let { data = {}, csrfToken = "", action = "" } = $props();

  const channels = data.channels ?? [];

  // Which channels the staffer is repairing, and which requests move with them.
  let selectedChannels = $state(new Set());
  let selectedFoias = $state(new Set());
  let newEmail = $state("");
  let updateAgencyInfo = $state(false);
  let snailMail = $state(false);
  let resolve = $state(false);
  let reply = $state("");

  // A portal channel cannot be repaired by swapping in another email address.
  // Surfacing that here as well as server side keeps a staffer from filling in
  // a replacement that will only be rejected on submit.
  let selectedPortals = $derived(
    channels.filter((c) => selectedChannels.has(c.id) && c.is_portal),
  );
  let blockedByPortal = $derived(selectedPortals.length > 0 && !!newEmail);

  let selectedBlocked = $derived(
    channels
      .filter((c) => selectedChannels.has(c.id))
      .reduce((total, c) => total + c.blocked_count, 0),
  );

  function toggleChannel(channel) {
    // Selecting a channel takes its requests with it, which is the common
    // case; a staffer can then deselect individual requests.
    const channelIds = new Set(selectedChannels);
    const foiaIds = new Set(selectedFoias);
    if (channelIds.has(channel.id)) {
      channelIds.delete(channel.id);
      channel.foias.forEach((foia) => foiaIds.delete(foia.id));
    } else {
      channelIds.add(channel.id);
      channel.foias.forEach((foia) => foiaIds.add(foia.id));
    }
    selectedChannels = channelIds;
    selectedFoias = foiaIds;
  }

  function toggleFoia(id) {
    const foiaIds = new Set(selectedFoias);
    if (foiaIds.has(id)) {
      foiaIds.delete(id);
    } else {
      foiaIds.add(id);
    }
    selectedFoias = foiaIds;
  }

  function selectAllRepairable() {
    const channelIds = new Set();
    const foiaIds = new Set();
    channels
      .filter((c) => c.repairable_by_email && c.blocked_count > 0)
      .forEach((c) => {
        channelIds.add(c.id);
        c.foias.forEach((foia) => foiaIds.add(foia.id));
      });
    selectedChannels = channelIds;
    selectedFoias = foiaIds;
  }

  function clearSelection() {
    selectedChannels = new Set();
    selectedFoias = new Set();
  }
</script>

<form method="POST" {action} class="review-agency-repair-form">
  <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
  <input type="hidden" name="repair" value="true" />
  <input type="hidden" name="channel_pks" value={[...selectedChannels].join(",")} />
  <input type="hidden" name="foia_pks" value={[...selectedFoias].join(",")} />

  <fieldset>
    <legend>Channels</legend>

    <p>
      <button type="button" onclick={selectAllRepairable}>
        Select all repairable channels
      </button>
      <button type="button" onclick={clearSelection}>Clear</button>
    </p>

    {#each channels as channel (channel.id)}
      <article class="repair-channel">
        <label>
          <input
            type="checkbox"
            checked={selectedChannels.has(channel.id)}
            onchange={() => toggleChannel(channel)}
          />
          <code>{channel.email}</code>
          <strong>{channel.blocked_count}</strong> blocked
          {#if channel.is_primary}<span class="badge">Primary</span>{/if}
          {#if !channel.has_error}<span class="badge">Healthy</span>{/if}
          {#if channel.is_portal}<span class="badge">Portal</span>{/if}
          {#if channel.classification === "noreply"}
            <span class="badge">Do-not-reply</span>
          {/if}
          {#if channel.classification === "reputation"}
            <span class="badge">Sender reputation</span>
          {/if}
          {#if channel.is_stale_error}<span class="badge">Stale flag</span>{/if}
        </label>

        {#if channel.last_error_message}
          <p class="repair-channel__error">
            {channel.last_error_message}
            {#if channel.last_error_age !== null}
              &mdash; {channel.last_error_age} day{channel.last_error_age === 1
                ? ""
                : "s"} ago
            {/if}
          </p>
        {/if}

        {#if channel.is_portal}
          <p class="repair-channel__warning">
            This is a portal notification address. Switching the agency to a
            portal is separate work &mdash; no replacement email repairs it.
          </p>
        {/if}

        {#if channel.foias.length}
          <details open={selectedChannels.has(channel.id)}>
            <summary>{channel.foias.length} request(s) routed here</summary>
            <ul>
              {#each channel.foias as foia (foia.id)}
                <li>
                  <label>
                    <input
                      type="checkbox"
                      checked={selectedFoias.has(foia.id)}
                      onchange={() => toggleFoia(foia.id)}
                    />
                    <a href={foia.url}>{foia.title}</a>
                    <small>{foia.status}</small>
                  </label>
                </li>
              {/each}
            </ul>
          </details>
        {/if}
      </article>
    {/each}
  </fieldset>

  <fieldset>
    <legend>Repair</legend>

    <p>
      Repairing <strong>{selectedChannels.size}</strong> channel(s),
      moving <strong>{selectedFoias.size}</strong> of
      <strong>{selectedBlocked}</strong> blocked request(s).
    </p>

    <label>
      Replacement email address
      <input type="email" name="new_email" bind:value={newEmail} />
    </label>

    {#if blockedByPortal}
      <p class="repair-form__error" role="alert">
        {selectedPortals.map((c) => c.email).join(", ")} is a portal
        notification address. An email replacement is the wrong repair &mdash;
        deselect it or clear the replacement address.
      </p>
    {/if}

    <label>
      <input
        type="checkbox"
        name="update_agency_info"
        bind:checked={updateAgencyInfo}
      />
      Make this the agency's primary contact
    </label>

    <label>
      <input type="checkbox" name="snail_mail" bind:checked={snailMail} />
      Fall back to snail mail
    </label>

    <label>
      <input type="checkbox" name="resolve" bind:checked={resolve} />
      Resolve the affected tasks
    </label>

    <label>
      Follow-up message
      <textarea name="reply" rows="5" bind:value={reply}></textarea>
      <small>Leave blank to send no follow-up.</small>
    </label>

    <button type="submit" disabled={blockedByPortal}>Apply repair</button>
  </fieldset>
</form>
