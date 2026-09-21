# Review Agency Task — Design Planning

Written by Claude Opus 5, edited by Allan Lasser.

Design doc for [#2224 "Simplify the task UI"](https://github.com/MuckRock/muckrock/issues/2224). Grounded in the read-only production analysis in [`agency_quality_research.md`](./agency_quality_research.md) and the channel measurements in [`agency_channel_sizing.md`](./agency_channel_sizing.md).

**This document kicks off a design process, not a single implementation.** It fixes the framing, the scope, the unit of work, and the information that has to be legible. It deliberately does *not* specify layout — we'll iterate on the UI against real data as we build.

## 1. What this work actually is

**We are healing agency communication channels.** 

An agency's channel roster varies enormously by size:

- **Large agencies have many active channels.** Departments and divisions each have their own FOIA contact. A single agency may be routing live requests through several different addresses, some working, some dead.
- **Small agencies have a few, one, or none.** A rural building department may have exactly one address, or no working channel at all.

The current `ReviewAgencyTask` model flattens all of that into one row per `(agency, source)`. That flattening is the root of most of the UI problems in #2224: a task can't tell you *what* is broken because it isn't attached to a channel.

### 1.1. Three real problems

**The per-task UI needs work.** #2224 catalogs it: no summary of what's at stake, the contact list swamped with inactive addresses, mail and phone crowding out what's actually broken, resolved tasks hard to audit. Staff can't be productive inside a single task as it stands.

**The queue needs triage, and the head is heavy.** 3,677 open tasks across ~3,671 agencies. **2,265 distinct broken email channels on 1,684 agencies gate 8,562 active FOIA requests — ~18% of all live activity** (sizing §1). The top 30 agencies hold 39% of that. Today every task looks equivalent: a task blocking 1,075 FBI requests reads the same as one blocking a single request at a local library. Nothing in the ordering or layout reflects the difference.

**The heaviest agencies need to be workable one at a time.** Per-agency load comes in two shapes, and they need different repairs:

1. **Concentrated.** The FBI has 1,075 blocked requests, and **869 of them (81%) sit on a single real mailbox** — `foipaquestions@fbi.gov`, which exists as three separate rows differing only in capitalization. One correct repair moves 10% of the entire in-scope backlog.
2. **Spread.** Department of Energy HQ has 22 channels for 49 blocked requests, the largest holding 16%. Nothing here is one repair.

Across the 309 agencies with more than one blocked channel, the biggest channel holds a median 61% of that agency's blocked requests — so **1,979 requests (23% of the pool) sit on channels that aren't their agency's biggest.** Repairing only the top channel per agency would leave nearly a quarter of the backlog on the floor.

Either shape needs the same thing: a **detail view for one agency**, where the whole channel roster is visible and repairable in one place, rather than a queue row that opens a modal.

## 2. Scope for this pass

**Email only.** Broken email channels gate **8,562 requests across 1,684 agencies** — the large majority of the blocked pool. Unlabeled tasks are overwhelmingly email problems that predate source labelling. Fixing email fixes most of the backlog.

| In scope | Out of scope this pass |
|---|---|
| `email`-source tasks | `fax`-source repair workflow (1,218 blocked) |
| *unlabeled* tasks (triaged as email) | Snail-mail address repair |
| Agency detail view for channel repair | `stale` task action set (416 blocked) |
| Per-channel task model + migration | Zendesk integration |
| Impact-ordered queue | `stale` Celery job trigger conditions |
| Resolved-task readout | Portal switching (see below) |
| Case-variant channel collapsing (§4) | Repair of portal-hosted agencies |

**Fax and snail mail aren't going away** — they stay visible, and existing behavior keeps working. We're just not designing their repair workflows now.

### 2.1. The portal stub — and what it costs us

Sometimes the right repair isn't a new email address — it's recognizing that the agency has moved to a **FOIA portal**, and the channel should switch from email to portal. Portal notification addresses are already sitting in the blocked-channel data, masquerading as broken emails:

| Address | Agency | Blocked | Actually |
|---|---|---:|---|
| `seattle@mycusthelp.net` | Seattle PD | **159** (89% of its total) | GovQA portal |
| `noreply@securerelease.us` | ICE + DHS | 63 | SecureRelease portal |
| `no-reply@` / `foia@` / `admin@foiaonline.gov` | FBI, DHS | ~37 | FOIAonline — already a `PORTAL_TYPES` entry |
| `noreply@mail.foia.state.gov` | State | 1 | State's portal |

A subset of head agencies — Seattle PD prominently among them — cannot be repaired in this pass. Seattle PD's single largest channel is a GovQA notification address. **No replacement email repairs it** — picking one would be actively wrong.

This tells us an important detail on how we expect this work to fit into the bigger picture: this is a step in the right direction, but not a complete solution. We can't expect just a UI cleanup to address some of the deeper, harder repair work that's needed here. **We don't yet have an open issue describing how switching to portal should work or improve.**

That needs deeper consideration than this pass allows: `Agency.portal` is a FK to a `Portal` with a type (`govqa`, `nextrequest`, `foiaxpress`, `fbi`, `webform`, …), several of those types have live automation classes, and `FOIARequest.get_contact_info()` puts portal *ahead* of email in the preference order — so setting a portal silently reroutes every request on that agency. **Portal switching stays out of this pass**, named as follow-on work, with an obvious seam left where it will land.

**What this pass should still do, cheaply: not mislead staff into a wrong repair.** If a channel is recognizably a portal address, say so rather than inviting an email replacement. That's a display concern, not machinery.

## 3. Design principles

- **The unit of work is the broken communication channel, not the agency.** For small agencies these collapse: one address, one task, and that's **81.7% of agencies**. For large ones they don't. The ~1:1 agency-to-task ratio in the research is an artifact of `ensure_one_created`'s `(agency, source)` dedup key, which unhelpfully collapses all subtasks into one gnarly, rat-king task.

- **A channel is a mailbox, not a database row.** `EmailAddress.email` is `unique=True` and `_normalize_email` evidently lowercases only the domain, so the same real mailbox exists as several rows. The FBI has `FOIPAQUESTIONS@fbi.gov` (481 blocked), `foipaquestions@fbi.gov` (387), and `FOIPAQuestions@fbi.gov` (1) — **one mailbox, 869 requests, three rows.** Also `OIP-NoReply@` / `oip-noreply@usdoj.gov` (42 combined), `FOIPARequest@` / `foiparequest@ic.fbi.gov`, `FBI.FOIPA.NEGOTIATION@` / `fbi.foipa.negotiation@fbi.gov`. Channels must be identified case-insensitively on the local part. Two reasons: the **lever** — 869 requests is the single highest-leverage repair in the system, and it's invisible while the rows stay split — and the **trap** — list them as three channels and staff will fix one while the other two keep failing. FBI's 23 channels are really ~18. This belongs in the model, not the template.

- **Channels fail in three distinct ways, and they need different repairs.** Conflating them is what makes the current UI unhelpful, but we have an opportunity to guide staff by better classifying the repair work to be done:
  1. **The mailbox is dead** — someone left, a role address was retired. 71% SMTP 550. Repair: a new address. This is the assumed case today and it *is* the majority.
  2. **The agency moved to a portal** — the address is a portal notification sender. Repair: switch the channel (out of scope this pass, §2.1), but it must be *recognizable* so nobody attempts an email swap.
  3. **We're mailing a do-not-reply address** — `postmaster@usdoj.gov`, `donotreply@hq.dhs.gov`, `no-reply@`, `oip-noreply@`, `notification@pay.gov`. These were harvested from inbound mail and then used as outbound targets. Repair: point back at the real, working mailbox.

- **"Active channel" means a channel carrying live traffic** — not every address on file. This distinction is load-bearing, and the sizing run confirms it: counting every error-status `AgencyEmail` link yields 4,562 channels, while counting only those carrying blocked traffic yields **2,265 — half as many**. A channel earns a task when active requests are actually routed to it (`FOIARequest.email` pointing at an error-status address), not merely because a stale `AgencyEmail` row is flagged.

- **Channel count is not an impact signal.** DOE HQ has 22 channels for 49 blocked requests; FBI has 23 for 1,075. A long channel list must not read as urgent on its own — blocked count drives priority, _always_.

- **Impact-first ordering.** Default sort is blocked-active-request count, descending. Source, jurisdiction, and age are filters and badges — never the primary sort.

- **Actionable over exhaustive.** Surface the affected channel and its recent errors; demote historical addresses, mailing addresses, and phone numbers. If it doesn't inform the repair, it isn't in the default view. Corollary from the data: **61% of "error" flags on these agencies are stale** — no bounce event in two years — so error-flag age is itself a signal worth showing.

- **Source is context, not workflow.** Source drives a badge and a filter, not a separate page or form.

- **Each agency stands alone.** Even where agencies share administrative parentage (DOJ, DHS, municipal police departments), each has its own process, contacts, and repair path. No cross-agency grouping. Sameness of parent doesn't mean sameness of workflow.

- **The agency is the container; the channel is the primitive.** Shared agency framing — name, jurisdiction, roster, total blocked — renders once. Channels stack inside it. Same structure whether there's one channel or twelve.

## 4. The unit of work — per-channel tasks

**Decision: we commit to per-channel tasks and a retroactive migration.**

### The change

| | Today | Redesigned |
|---|---|---|
| Task identity | `(agency, source)` | `(agency, source, channel)` |
| What "channel" is | — | FK to the specific `EmailAddress` (this pass); extensible to `PhoneNumber` / `Portal` later |
| Dedup | `ensure_one_created(agency=…, source=…)` | keyed on the channel too |
| Existing tasks | — | split retroactively into per-channel tasks |

`(agency, source, channel)` never collapses back to `(agency, source)`. A single-channel agency is just N=1 of the same shape — that's what makes one design serve the whole distribution.

### Why this is cheaper than it looks

**Every call site that creates an email-source task already has the broken address in hand and throws it away.**

| Call site | Address available as | Currently passes |
|---|---|---|
| [muckrock/mailgun/views.py:465](muckrock/mailgun/views.py#L465) | `recipient` (just set to `status="error"`) | `agency`, `source="email"` |
| [muckrock/foia/models/request.py:955](muckrock/foia/models/request.py#L955) | `self.email` (just set to `status="error"`) | `agency`, `source="email"` |

Both already mark the specific address as errored on the line above. Threading it into `ensure_one_created` is a mechanical change. New tasks become correctly channel-scoped essentially for free; the retroactive split of the existing 3,677 is the harder part, and case-collapsing (§4) is the only genuinely delicate piece of it.

The `staff` and `stale` call sites ([muckrock/agency/views.py:117](muckrock/agency/views.py#L117), [muckrock/foia/views/list.py:326](muckrock/foia/views/list.py#L326), [muckrock/agency/tasks.py:23](muckrock/agency/tasks.py#L23)) genuinely have no channel to point at — they stay agency-level with a null channel. That's correct, not a gap: those tasks *are* about the agency.

### The retroactive split — measured and decided

Existing tasks don't record which channel triggered them; the evidence lives in `EmailError` rows a couple of joins away. Three candidate definitions, now measured (sizing §6):

| Strategy | Tasks produced | vs. today's 3,677 | Verdict |
|---|---:|---|---|
| 1. Every error-status `AgencyEmail` link | 4,562 | +24% | Rejected — inflated by stale flags, half carry no live traffic |
| 2. Addresses with an `EmailError` in last 24mo | 1,380 | −62% | Rejected alone — *misses* live-traffic channels that broke earlier |
| **3. Channels carrying blocked active traffic** | **2,265** | **−38%** | **Adopted** — matches the §3 "active channel" principle |
| 2 ∪ 3 | 2,931 | −20% | Optional secondary sweep |

**Decision: strategy 3**, with `2 ∪ 3` available if we want to catch recently-broken channels with no current traffic. The split **shrinks** the queue rather than exploding it — the fear that motivated this query turned out to be unfounded.

The distribution makes the migration safe: **81.7% of agencies get exactly one task, p90 is 2, p99 is 5, and the max is 23** (FBI). No cap or manual-review path for the head is needed.

**The migration must case-collapse.** Per §3, group candidate channels case-insensitively on the local part and emit one task per real mailbox, summing blocked counts across the merged rows. Without this the FBI gets 23 tasks for ~18 mailboxes and its largest repair is split three ways. This is the one piece of migration logic that needs real care — the rest is mechanical.

## 5. Queue view — what it must surface

*Layout is deliberately unspecified. These are the information requirements.*

**Must be legible without expanding anything:**

- **Blocked active request count** — the primary ordering key, at both agency and channel level. Never channel count (§3).
- **Which channel is broken**, identifiably (the address itself, not "an email").
- **Which failure class it is** (§3): dead mailbox / portal address / do-not-reply. At minimum, portal addresses must be visually distinct so staff don't attempt an email swap on Seattle PD's GovQA channel.
- **Whether it's the agency's active/primary contact**.
- **Last error, with recency** — SMTP code translated into plain language, plus age. Recency distinguishes live breakage (high priority triage) from a stale flag (lower priority triage).
- **Last successful response** — per #2224, with both absolute and relative dates.
- **Source badge** and complication flags (federal, high-volume).

**Must be possible:**

- Order by impact, not creation date.
- Filter to a single agency to get its detail view — the primary entry point when a staffer already knows where they're going. Deep-linkable and shareable.
- Filter by minimum/maximum blocked count, to isolate the head or the tail.
- Filter to or away from unlabeled tasks — currently impossible, since the filter only offers the four labelled sources.
- See agency-level grouping when one agency has several channel tasks, so twelve State Department rows don't read as twelve unrelated items.

**Known constraint:** annotating blocked counts across the full list may be expensive. Needs benchmarking before we commit to computing it live (§9).

## 6. Agency detail view — what it must support

The two shapes of heavy agency (§1) are what motivate this. Whether an agency's load is concentrated on one mailbox or spread across 22, the work is *the roster* — and a roster deserves its own surface rather than an inline AJAX panel. A real URL is shareable in Slack and tickets, the back button works, and heavy work doesn't push the queue off-screen. Today's inline panel is an artifact of the original implementation, not a requirement.

**Sizing target:** optimize for 1–2 channels (81.7% / p90), stay comfortable to ~5 (p99), remain usable at 23 (FBI). A 22-channel agency like DOE HQ with 2.2 requests per channel should feel like a long thin list, not an emergency.

**Purpose:** triage and repair *all* of one agency's communication channels in one place.

**Must show:**

- Agency identity, jurisdiction, links out to the agency page and admin.
- **Total blocked requests** across all channels—this acts as a scorecard, indicating how much work is left to be done.
- **Channel roster shape** — how many known contacts, how many broken, how many carrying live traffic. This is where "large agencies have many channels, small ones have none" becomes visible.
- Last successful response across any channel.
- Complication flags, as triage signal rather than a mid-panel warning.
- **Per channel:** the address, blocked count, primary/role status, recent error events with codes, and the requests currently routed to it.
- Healthy channels too, not just broken ones — staff deciding on a replacement need to know whether a working alternate already exists. Hiding them pushes that lookup to the admin page and breaks flow.
- Mail and phone, demoted behind a disclosure (per #2224) but reachable.

**Must let staff:**

- Repair one channel: point the affected requests at a new address, optionally update the agency's default contact, optionally send a follow-up.
- **Repair several channels in one pass when the same fix applies.** This is not optional polish: the median multi-channel agency has only 61% of its blocked requests on its biggest channel, and **1,979 requests sit on non-biggest channels** (§1). Single-channel-only repair structurally cannot clear the backlog.
- Record "this agency moved to a portal" as an outcome (**stub** — §2), and be told when email repair is the wrong tool.
- Resolve without a contact change, for cases where nothing is actually broken.

**Error display:** show the most recent few events, full log behind a disclosure. Research §11 justifies the compression — **100% of recent errors are permanent failures and 71% are SMTP 550** ("mailbox doesn't exist"). Staff need the latest code and reason, not a twenty-row scroll. The interesting variance is the ~3% that are sender-side reputation problems (`blacklisted`, `espblock`), which **no address swap will fix** — those need to be distinguishable, because they're a different job.

## 7. Resolved-task readout

References [#1869](https://github.com/MuckRock/muckrock/issues/1869) and [#1870](https://github.com/MuckRock/muckrock/issues/1870). Today the resolved view hides the interesting parts.

- **What was done** — one line: which channel, old value → new value, how many requests updated, whether a follow-up went out, by whom, when.
- **Whether it held** — has the agency had a successful communication since the resolve?
- **Reopen linkage** — if a new task appears on the same channel, link forward from the resolved one.

The reopen linkage matters because **the queue is growing** — roughly +20 newly-blocked requests per day across the research snapshots. A resolve that didn't hold is a signal, not noise.

## 8. Empty-queue agencies

639 agencies have an open task but zero active requests. They are **not** auto-resolve candidates, and the earlier "just close them" instinct was wrong:

- **472 of them are email-source** — the address is still broken. The next request in hits the same wall and reopens the task.
- **46% had request activity within the last year**, some within a day of the research snapshot. "Zero active" means the queue happens to be empty right now, not that the agency is abandoned.

Treat "zero active" as a **triage hint** — small blast radius, safe to defer — not a resolve trigger. Default them out of the impact-ordered view, with a way to opt into them for preventative repair. The genuinely safe bulk-resolve slice (unlabeled + zero active + 3+ years quiet) is ~44 agencies: real, but a rounding error.

## 9. Research and data we still need

### Queries to run

✅ **Done:** channels-per-agency distribution and migration sizing — see [`agency_channel_sizing.md`](./agency_channel_sizing.md), consumed in §1, §3, §4, §6.

| Query | Why it matters |
|---|---|
| **Case-variant collision count across all 2,265 channels** | §3/§4 commit to case-collapsing on the strength of the FBI example. Need the real magnitude: how many mailboxes are split across rows, and how many blocked requests are hiding behind the split. Directly sizes the migration's hardest step. |
| **Portal-notification addresses among the 2,265** | Quantifies the §2 accepted limitation. Match against `PORTAL_TYPES` domains (`mycusthelp.net`, `securerelease.us`, `foiaonline.gov`, `nextrequest.com`, …) and count agencies and requests unreachable this pass. Also gives the portal follow-on its business case. |
| **Do-not-reply addresses among the 2,265** | Sizes failure class 3 (§3) — `no-reply@`, `donotreply@`, `postmaster@`, `notification@` patterns. If large, the upstream reply-to selection bug is worth its own ticket. |
| Blocked-count annotation cost on the full list | Decides whether we compute live, cache on the task, or materialize (§5). Still unbenchmarked. |
| Same broken address linked to N agencies | `ICE-FOIA@ice.dhs.gov` already appears on both ICE (76) and DHS (11). The top of that list is a cross-agency bulk-repair unit. |
| Task age distribution by source | Whether recent tasks are a resolvable working set or the backlog is ossified. |
| Task intake vs. resolve rate, last 12 months | Confirms the growth signal and sizes the treadmill. |

### Heavy-head data locally — early workstream, not a blocker

Our dev database doesn't contain the top-of-distribution agencies at all. We can't design or test the detail view against State Dept, CIA, or Seattle PD shape without them, and any decision made against synthetic data will miss the real thing. This should proceed **in parallel** with design work rather than gating it — the corrected head size means we're no longer designing for an extreme outlier.

Approach:

1. **Anchor on sizing §3's top 30**, not research §11.5's top 50 — the latter's per-agency figures are unreliable (§1). Include FBI (the 23-channel, case-split case), DOE HQ (22 channels, low impact), and Seattle PD (portal-address case) specifically: those three are the shapes the design has to survive. Per agency: the agency row, all `AgencyEmail` links (primary and not), attached `EmailAddress` rows, open `ReviewAgencyTask`s, a bounded sample of attached `FOIARequest`s, and `EmailCommunication` + `EmailError` rows within 24 months.
2. **Write a management command** rather than ad-hoc `dumpdata` — the relationship walk is non-trivial and it needs to be re-runnable.
3. **Redact only non-public data.** MuckRock's non-embargoed requests are already public at `/foi/*`; redacting what's already on the web costs design fidelity and buys nothing.
   - **Always redact:** `User.email`, `User.password` (set unusable).
   - **Embargoed requests only:** request title and body, associated communication bodies, requester first/last name. Check current embargo state per request; treat expired embargoes as non-embargoed.
   - **Leave as-is:** non-embargoed request content and user names; agency emails (public FOIA contacts); SMTP responses and `EmailError` fields (machine output); agency metadata; task rows.
4. **Keep the fixture gitignored.** Don't leak this data into our commit history.

## 10. Anticipated touch surface

| File | Change |
|---|---|
| [muckrock/task/models.py:332](muckrock/task/models.py#L332) | Channel FK on `ReviewAgencyTask`; uniqueness `(agency, source, channel)` |
| Data migration (new) | Retroactive per-channel split (§4) |
| [muckrock/task/querysets.py:334](muckrock/task/querysets.py#L334) | `ensure_one_created` dedup keyed on channel; `preload_list` updated for grouping |
| [muckrock/mailgun/views.py:465](muckrock/mailgun/views.py#L465), [muckrock/foia/models/request.py:955](muckrock/foia/models/request.py#L955) | Pass the already-in-hand address into `ensure_one_created` |
| [muckrock/task/views.py:326](muckrock/task/views.py#L326) | Impact ordering, blocked-count annotation, agency grouping |
| muckrock/task/views.py — new | Agency detail view (§6) |
| muckrock/task/urls.py | Route for the agency detail view |
| [muckrock/task/filters.py:209](muckrock/task/filters.py#L209) | Minimum-blocked filter; unlabeled as a filterable value; agency filter promoted |
| [muckrock/task/forms.py:47](muckrock/task/forms.py#L47) | Single-channel and multi-channel repair submission |
| muckrock/templates/task/review_agency.html | Agency-grouped queue rows |
| muckrock/templates/task/ — new | Agency detail page shell |
| [muckrock/templates/lib/review_agency.html](muckrock/templates/lib/review_agency.html) | Superseded by the detail view; keep as fallback during rollout |
| muckrock/assets/components/ — new | Repair UI (see below) |

**Frontend:** Svelte 5 and Vite are **already in the stack**, with components in [muckrock/assets/components/](muckrock/assets/components/). The repair surface is a good fit for a component: shared selection state across channel cards, and one repair form that mounts both inside a channel and in a multi-channel context.

Explicitly not changing: source choices, resolve semantics, the `stale` job's trigger conditions, Zendesk.

## 11. What this is not

- **Not a bulk auto-resolve tool.** Almost nothing here is safely mass-closable — the channels are still broken (§8).
- **Not a source-per-workflow split.** Sources overlap in agency and remediation; separate pages fragment a naturally per-channel workflow.
- **Not a filter-heavy UI.** The head is heavy. Staff time belongs at the top of the queue, not segmenting a 3,677-row list.
- **Not the whole product bottleneck.** ~82% of active requests are on unflagged agencies or working channels. This work can't reach them, and framing it as "unblock everything" would overpromise. **The honest ceiling: ~6,749 requests** — 8,562 on broken email channels, less the 1,813 that already have a working portal and aren't truly blocked. Minus, in turn, the portal-hosted agencies this pass can't repair at all (§2).
- **Not finished when the first PR ships.** This is a design process. We expect to learn things in the detail view that change the queue view, and vice versa.

## Reference

- Channel sizing (2026-08-11, load-bearing): [`agency_channel_sizing.md`](./agency_channel_sizing.md)
- Research (2026-07 snapshot; per-agency figures in §11.5 superseded — see §1): [`agency_quality_research.md`](./agency_quality_research.md)
- Issue: [MuckRock/muckrock#2224](https://github.com/MuckRock/muckrock/issues/2224)
- Resolved-task issues: [#1869](https://github.com/MuckRock/muckrock/issues/1869), [#1870](https://github.com/MuckRock/muckrock/issues/1870)
- Milestone: Review Agency Task UX
