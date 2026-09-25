<script>
  /**
   * Repair one or several of an agency's broken communication channels.
   *
   * Everything arrives as props; the only fetches are address suggestions for
   * the replacement email.  It owns selection state across the channel cards
   * and posts a normal form, so the server stays the single place where a
   * repair is validated.
   *
   * Styles live in assets/css/reviewAgency.css alongside the page's.
   */
  import EmailAutocomplete from "./EmailAutocomplete.svelte";

  let { data = {}, csrfToken = "", action = "", emailSearchUrl = "" } = $props();

  // The server sends channels in impact order; the primary leads regardless,
  // since it is the address every other repair is weighed against.
  const channels = [...(data.channels ?? [])].sort(
    (a, b) => Number(b.is_primary) - Number(a.is_primary),
  );
  const primary = channels.find((c) => c.is_primary);
  const primaryIsSound =
    !!primary && !primary.has_error && !primary.blocked_count && !primary.is_portal;

  // A channel needs attention if it is flagged or still has traffic stuck on
  // it: blocked behind an error, or stale on a healthy address.  Anything
  // already selected also shows, so the filter never hides part of what is
  // about to be submitted.
  function needsAttention(channel) {
    return channel.has_error || channel.blocked_count > 0;
  }

  // Which channels the staffer is repairing, and which requests move with them.
  let selectedChannels = $state(new Set());
  let selectedFoias = $state(new Set());
  // A working primary is the likeliest replacement, so it starts filled in
  let newEmail = $state(primaryIsSound ? primary.email : "");
  let updateAgencyInfo = $state(false);
  let onlyNeedingAttention = $state(true);
  let snailMail = $state(false);
  let resolve = $state(false);
  // Starts from the legacy task's follow-up text; clearing it sends none
  let reply = $state(data.default_reply ?? "");

  // A portal channel cannot be repaired by swapping in another email address.
  // Surfacing that here as well as server side keeps a staffer from filling in
  // a replacement that will only be rejected on submit.
  let selectedPortals = $derived(
    channels.filter((c) => selectedChannels.has(c.id) && c.is_portal),
  );
  let blockedByPortal = $derived(selectedPortals.length > 0 && !!newEmail);
  let canRepair = $derived(selectedChannels.size > 0 && !blockedByPortal);

  let visibleChannels = $derived(
    onlyNeedingAttention
      ? channels.filter(
          (c) => needsAttention(c) || selectedChannels.has(c.id),
        )
      : channels,
  );
  let hiddenCount = $derived(channels.length - visibleChannels.length);

  // Requests stuck on a flagged channel are blocked; on a healthy one they
  // are stale.  Both move with a repair, but they are different problems.
  let selectedStuck = $derived(
    channels
      .filter((c) => selectedChannels.has(c.id))
      .reduce(
        (totals, c) => {
          totals[c.has_error ? "blocked" : "stale"] += c.blocked_count;
          return totals;
        },
        { blocked: 0, stale: 0 },
      ),
  );

  // Repairing the primary means replacing it, so selecting it sets the new
  // address as primary; deselecting it undoes that.  Only a change in the
  // primary's selection touches the checkbox, so a manual choice otherwise
  // stands.
  function setSelection(channelIds, foiaIds) {
    if (primary) {
      const wasSelected = selectedChannels.has(primary.id);
      const isSelected = channelIds.has(primary.id);
      if (wasSelected !== isSelected) {
        updateAgencyInfo = isSelected;
        // The primary cannot be its own replacement, so its prefill clears;
        // an address the staffer typed is left alone
        if (isSelected && newEmail === primary.email) {
          newEmail = "";
        } else if (!isSelected && !newEmail && primaryIsSound) {
          newEmail = primary.email;
        }
      }
    }
    selectedChannels = channelIds;
    selectedFoias = foiaIds;
  }

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
    setSelection(channelIds, foiaIds);
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
    setSelection(channelIds, foiaIds);
  }

  function formatDate(iso) {
    return iso ? new Date(iso).toLocaleDateString("en-US") : "";
  }

  function clearSelection() {
    setSelection(new Set(), new Set());
  }
</script>

<form method="POST" {action} class="review-agency-repair-form">
  <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
  <input type="hidden" name="repair" value="true" />
  <input type="hidden" name="channel_pks" value={[...selectedChannels].join(",")} />
  <input type="hidden" name="foia_pks" value={[...selectedFoias].join(",")} />

  <!-- A section rather than a fieldset: a legend cannot sit in a flex header -->
  <section class="repair-channels" aria-labelledby="repair-channels-heading">
    <header class="repair-channels__header">
      <h3 id="repair-channels-heading">Select channels to repair</h3>
      <div class="repair-channels__actions">
        <label class="repair-channels__filter">
          <input type="checkbox" bind:checked={onlyNeedingAttention} />
          Only channels needing repair
          {#if onlyNeedingAttention && hiddenCount > 0}
            ({hiddenCount} hidden)
          {/if}
        </label>
        <button type="button" onclick={selectAllRepairable}>
          Select all repairable channels
        </button>
        <button type="button" onclick={clearSelection}>Clear</button>
      </div>
    </header>

    <div class="repair-channels__list">
      {#each visibleChannels as channel (channel.id)}
        <article
          class="repair-channel"
          class:repair-channel--selected={selectedChannels.has(channel.id)}
        >
          <label class="repair-channel__header">
            <input
              type="checkbox"
              checked={selectedChannels.has(channel.id)}
              onchange={() => toggleChannel(channel)}
            />
            <code>{channel.email}</code>
            <strong>{channel.blocked_count}</strong>
            {channel.has_error ? "blocked" : "stale"}
            {#if channel.is_primary}<span class="blue badge">Primary</span>{/if}
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
              {#if channel.last_error}
                &mdash;
                <time datetime={channel.last_error}>
                  {formatDate(channel.last_error)}
                </time>
                {#if channel.last_error_age !== null}
                  ({channel.last_error_age} day{channel.last_error_age === 1
                    ? ""
                    : "s"} ago)
                {/if}
              {/if}
            </p>
          {/if}

          {#if channel.is_stale_error}
            <p class="repair-channel__note">
              Stale flag &mdash; nothing has bounced here in over two years.
            </p>
          {/if}

          {#if channel.is_portal}
            <p class="repair-channel__warning">
              This is a portal notification address. Switching the agency to a
              portal is separate work &mdash; no replacement email repairs it.
            </p>
          {/if}

          {#if channel.recent_errors.length}
            <!-- The latest few carry the whole signal; the rest is a scroll -->
            <details>
              <summary>
                {channel.error_count} error event{channel.error_count === 1
                  ? ""
                  : "s"}
              </summary>
              <ul>
                {#each channel.recent_errors as error}
                  <li>
                    <time datetime={error.datetime}>
                      {formatDate(error.datetime)}
                    </time>
                    &mdash; {error.code} {error.reason} {error.error}
                  </li>
                {/each}
              </ul>
            </details>
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
      {:else}
        <p>
          {channels.length
            ? "Every channel is healthy with no stale requests."
            : "No channels on record for this agency."}
        </p>
      {/each}
    </div>
  </section>

  <!-- Flows straight on from the selection it acts on -->
  <fieldset class="repair-action" aria-label="Repair">
    <p class="repair-action__summary">
      Repairing <strong>{selectedChannels.size}</strong> channel(s),
      moving <strong>{selectedFoias.size}</strong> of
      <strong>{selectedStuck.blocked}</strong> blocked
      {#if selectedStuck.stale}
        and <strong>{selectedStuck.stale}</strong> stale
      {/if}
      request(s).
    </p>

    <EmailAutocomplete
      label="Replacement email address"
      name="new_email"
      url={emailSearchUrl}
      bind:value={newEmail}
    />

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
      <span class="repair-field__label">Follow-up message</span>
      <textarea name="reply" rows="5" bind:value={reply}></textarea>
      <small>Leave blank to send no follow-up.</small>
    </label>

    <button type="submit" class="primary button" disabled={!canRepair}>
      Apply repair
    </button>
  </fieldset>
</form>
