<script>
  /**
   * Repair one or several of an agency's broken communication channels.
   *
   * A repair either points the selected requests at a replacement email, or
   * moves them to the agency's portal, where each is resubmitted by hand
   * through its own Portal Task.
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
  // Stale requests on a healthy primary are waiting on the agency, not on a
  // broken address, so they do not disqualify it as the replacement.
  const primaryIsSound = !!primary && !primary.has_error && !primary.is_portal;
  // The agency's portal, or null when a portal repair has to add one
  const portal = data.portal ?? null;
  const portalTypes = data.portal_types ?? [];

  // Only a flagged channel with requests stuck on it needs repair.  A healthy
  // one may still have stale requests, but those are slow responses rather
  // than delivery failures, and a flagged one with nothing routed to it has
  // nothing to move.  Anything already selected also shows, so the filter
  // never hides part of what is about to be submitted.
  function needsAttention(channel) {
    return channel.has_error && channel.blocked_count > 0;
  }

  // Which channels the staffer is repairing, and which requests move with them.
  let selectedChannels = $state(new Set());
  let selectedFoias = $state(new Set());
  // A working primary is the likeliest replacement, so it starts filled in
  let newEmail = $state(primaryIsSound ? primary.email : "");
  let updateAgencyInfo = $state(false);
  let onlyNeedingAttention = $state(true);
  let snailMail = $state(false);
  // A repair almost always finishes its task; staff opt out, not in
  let resolve = $state(true);
  // Starts from the legacy task's follow-up text; clearing it sends none
  let reply = $state(data.default_reply ?? "");
  // "email" or "portal": where the selected requests move to
  const repairModes = [
    { value: "email", label: "Send to email" },
    { value: "portal", label: "Send to portal" },
  ];
  let repairVia = $state("email");
  // Only used when the agency has no portal yet
  let portalUrl = $state("");
  let portalName = $state(data.agency?.name ?? "");
  let portalType = $state("");

  // A portal channel cannot be repaired by swapping in another email address.
  // Surfacing that here as well as server side keeps a staffer from filling in
  // a replacement that will only be rejected on submit.
  let selectedPortals = $derived(
    channels.filter((c) => selectedChannels.has(c.id) && c.is_portal),
  );
  let blockedByPortal = $derived(
    repairVia === "email" && selectedPortals.length > 0 && !!newEmail,
  );
  // The replacement itself must not be a portal notification address either:
  // mail to one never reaches the records office.  Same domain rule as the
  // server's classify_address().
  const portalDomains = data.portal_domains ?? [];
  let replacementIsPortal = $derived.by(() => {
    const domain = (newEmail ?? "").split("@")[1]?.trim().toLowerCase() ?? "";
    return portalDomains.some(
      (portal) => domain === portal || domain.endsWith("." + portal),
    );
  });
  // Mirrors the server: a follow-up only goes out with a contact change
  let contactChanges = $derived(!!newEmail || snailMail);
  // A broken portal is a bigger problem than routing, so it stops the repair
  let portalReady = $derived(
    portal ? !portal.has_error : !!(portalUrl && portalName && portalType),
  );
  let canRepair = $derived(
    repairVia === "portal"
      ? selectedFoias.size > 0 && portalReady
      : selectedChannels.size > 0 && !blockedByPortal && !replacementIsPortal,
  );

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
    // A portal notification address is repaired by moving to the portal, so
    // selecting the first one switches modes; after that the choice stands
    const hadPortal = channels.some(
      (c) => c.is_portal && selectedChannels.has(c.id),
    );
    const hasPortal = channels.some((c) => c.is_portal && channelIds.has(c.id));
    if (!hadPortal && hasPortal) {
      repairVia = "portal";
    }
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

  // Selects exactly what the staffer can see, so the filter decides the scope
  function selectAllVisible() {
    const channelIds = new Set();
    const foiaIds = new Set();
    visibleChannels.forEach((c) => {
      channelIds.add(c.id);
      c.foias.forEach((foia) => foiaIds.add(foia.id));
    });
    setSelection(channelIds, foiaIds);
  }

  // Nearly every stuck request shares a status, so status heads a group
  // rather than repeating on each row.  Largest group first; within one, the
  // oldest filing first, since it has been stuck longest.
  function groupByStatus(foias) {
    const groups = new Map();
    foias.forEach((foia) => {
      if (!groups.has(foia.status)) groups.set(foia.status, []);
      groups.get(foia.status).push(foia);
    });
    return [...groups]
      .map(([status, rows]) => ({
        status,
        foias: rows.toSorted((a, b) =>
          (a.date_submitted ?? "").localeCompare(b.date_submitted ?? ""),
        ),
      }))
      .sort((a, b) => b.foias.length - a.foias.length);
  }

  function toggleGroup(foias) {
    const foiaIds = new Set(selectedFoias);
    const allSelected = foias.every((foia) => foiaIds.has(foia.id));
    foias.forEach((foia) =>
      allSelected ? foiaIds.delete(foia.id) : foiaIds.add(foia.id),
    );
    selectedFoias = foiaIds;
  }

  function formatDate(iso) {
    return iso ? new Date(iso).toLocaleDateString("en-US") : "";
  }

  // Arrow keys move between tabs, as the ARIA tabs pattern expects
  function switchTabByKey(event) {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    event.preventDefault();
    const index = repairModes.findIndex((mode) => mode.value === repairVia);
    const next =
      repairModes[(index + step + repairModes.length) % repairModes.length];
    repairVia = next.value;
    document.getElementById(`repair-tab-${next.value}`)?.focus();
  }

  function clearSelection() {
    setSelection(new Set(), new Set());
  }
</script>

<form method="POST" {action} class="review-agency-repair-form">
  <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
  <input type="hidden" name="repair" value="true" />
  <input type="hidden" name="repair_via" value={repairVia} />
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
        <button type="button" onclick={selectAllVisible}>
          Select all
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
            {#if !channel.has_error}<span class="green badge">Healthy</span>{/if}
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
              This is a portal notification address. No replacement email
              repairs it &mdash; move its requests to the agency's portal.
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
              <table class="repair-requests">
                <thead>
                  <tr>
                    <th scope="col" aria-label="Move"></th>
                    <th scope="col">Request</th>
                    <th scope="col">Filed</th>
                    <th scope="col">Last response</th>
                  </tr>
                </thead>
                {#each groupByStatus(channel.foias) as group (group.status)}
                  {@const groupSelected = group.foias.filter((foia) =>
                    selectedFoias.has(foia.id),
                  ).length}
                  <tbody>
                    <tr class="repair-requests__group">
                      <th scope="colgroup" colspan="4">
                        <label>
                          <input
                            type="checkbox"
                            checked={groupSelected === group.foias.length}
                            indeterminate={groupSelected > 0 &&
                              groupSelected < group.foias.length}
                            onchange={() => toggleGroup(group.foias)}
                          />
                          {group.status}
                          <small>({group.foias.length})</small>
                        </label>
                      </th>
                    </tr>
                    {#each group.foias as foia (foia.id)}
                      <tr>
                        <td>
                          <input
                            type="checkbox"
                            aria-label="Move {foia.title}"
                            checked={selectedFoias.has(foia.id)}
                            onchange={() => toggleFoia(foia.id)}
                          />
                        </td>
                        <td><a href={foia.url}>{foia.title}</a></td>
                        <td>
                          {#if foia.date_submitted}
                            <time datetime={foia.date_submitted}>
                              {formatDate(foia.date_submitted)}
                            </time>
                          {:else}
                            &mdash;
                          {/if}
                        </td>
                        <td>
                          {#if foia.last_response}
                            <time datetime={foia.last_response}>
                              {formatDate(foia.last_response)}
                            </time>
                          {:else}
                            Never
                          {/if}
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                {/each}
              </table>
            </details>
          {/if}
        </article>
      {:else}
        <p>
          {channels.length
            ? "Every channel is healthy."
            : "No channels on record for this agency."}
        </p>
      {/each}
    </div>
  </section>

  <!-- Flows straight on from the selection it acts on -->
  <fieldset class="repair-action" aria-label="Repair">
    <div class="repair-tabs" role="tablist" aria-label="Where requests go">
      {#each repairModes as mode (mode.value)}
        <button
          type="button"
          role="tab"
          id="repair-tab-{mode.value}"
          class="repair-tab"
          class:repair-tab--active={repairVia === mode.value}
          aria-selected={repairVia === mode.value}
          aria-controls="repair-panel"
          tabindex={repairVia === mode.value ? 0 : -1}
          onclick={() => (repairVia = mode.value)}
          onkeydown={switchTabByKey}
        >
          {mode.label}
        </button>
      {/each}
    </div>

    <div
      class="repair-panel"
      role="tabpanel"
      id="repair-panel"
      aria-labelledby="repair-tab-{repairVia}"
    >
      {#if repairVia === "portal"}
        <p class="repair-action__summary">
          Moving <strong>{selectedFoias.size}</strong> of
          <strong>{selectedStuck.blocked}</strong> blocked
          {#if selectedStuck.stale}
            and <strong>{selectedStuck.stale}</strong> stale
          {/if}
          request(s) to the portal. Each is resubmitted by hand through its own
          Portal Task.
        </p>

        {#if portal}
          <p>
            <span class="repair-field__label">Portal</span>
            <a href={portal.url} target="_blank" rel="noopener">{portal.name}</a>
            ({portal.type})
          </p>
          {#if portal.has_error}
            <p class="repair-form__error" role="alert">
              This portal is marked as an error. Find a working portal or review
              the agency's contact methods before moving requests to it
              (<a href={portal.admin_url}>edit in Admin</a>).
            </p>
          {/if}
        {:else}
          <p class="repair-channel__warning">
            This agency has no portal. The one added here becomes its portal, so
            its new requests will be submitted through it too.
          </p>
          <label>
            <span class="repair-field__label">Portal URL</span>
            <input
              type="url"
              name="portal_url"
              required
              placeholder="https://"
              bind:value={portalUrl}
            />
            <small>An existing portal with this URL is reused.</small>
          </label>
          <label>
            <span class="repair-field__label">Portal name</span>
            <input type="text" name="portal_name" required bind:value={portalName} />
          </label>
          <label>
            <span class="repair-field__label">Portal type</span>
            <select name="portal_type" required bind:value={portalType}>
              <option value="" disabled>Select a type</option>
              {#each portalTypes as type (type.value)}
                <option value={type.value}>{type.label}</option>
              {/each}
            </select>
          </label>
        {/if}

        <label>
          <input type="checkbox" name="resolve" bind:checked={resolve} />
          Resolve the affected tasks
        </label>

        <button type="submit" class="primary button" disabled={!canRepair}>
          Move to portal
        </button>
      {:else}
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
            notification address. An email replacement is the wrong repair
            &mdash; use <strong>Send to portal</strong> instead, or deselect
            it.
          </p>
        {/if}

        {#if replacementIsPortal}
          <p class="repair-form__error" role="alert">
            {newEmail} is a portal notification address. Mail sent to it does
            not reach the agency &mdash; choose the agency's own mailbox.
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
          <textarea
            name="reply"
            rows="5"
            bind:value={reply}
            disabled={!contactChanges}
          ></textarea>
          {#if contactChanges}
            <small>Leave blank to send no follow-up.</small>
          {:else}
            <small>
              No follow-up without a new address or snail mail &mdash; it would
              go back to the broken address.
            </small>
          {/if}
        </label>

        <button type="submit" class="primary button" disabled={!canRepair}>
          Apply repair
        </button>
      {/if}
    </div>
  </fieldset>
</form>
