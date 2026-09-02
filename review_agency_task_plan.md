# Review Agency Task — Implementation Plan

Engineering plan for [#2224](https://github.com/MuckRock/muckrock/issues/2224), derived from [`review_agency_task_design.md`](./review_agency_task_design.md).

**Method:** red-green TDD. Every phase opens with failing tests, implements against them, and closes green. Run tests as `inv test --create-db --path=<path>`; run `inv format` and `inv pylint` before each PR.

**Explicit non-goal:** layout and visual design. Each phase's job is to get correct, complete data into a Django template context or a Svelte component's props. Markup is a scaffold — unstyled, semantic, sufficient to assert against. Design work happens by hand afterward.

**Phase sequencing rationale:** the model change (1) must land before anything can be keyed on a channel; the channel-summary layer (2) is the shared data vocabulary the queue (3), detail view (4), and repair (5) all consume; resolved-task readout (6) depends on repair having recorded an outcome. Phases 1–2 are backend-only and shippable behind existing UI. Phases 3–6 each ship user-visible surfaces.

---

## Phase 0 — Test data across the whole distribution (parallel, non-blocking)

Runs alongside Phase 1 rather than gating it. Two tracks, split by whether the shape is worth pulling from production or cheaper to build to spec.

### 0a — Synthesized shapes (factories)

Everything at or near N=1 is simple enough to construct exactly, and an arbitrary long-tail agency is a *worse* fixture than a built one: it carries incidental data, can't be asserted against precisely, and doesn't isolate the variation under test. Build these as reusable factory traits in `muckrock/task/factories.py`, not as a dumped JSON fixture — Phases 1–6 then assert against them directly, and the test suite stays independent of the gitignored dump.

`agency_with_channels(...)` builder emitting these shapes:

| Shape | Why it's needed |
|---|---|
| N=0 broken, task with null channel | `staff`/`stale` sources — must survive Phase 1 unchanged |
| N=1 dead mailbox, SMTP 550 | The 81.7% majority case; the design's default assumption |
| N=1, zero active requests | Design §8 — triage hint, must not auto-resolve |
| N=1, stale error flag (no bounce in 24mo) | 61% of error flags; recency display in Phase 3 |
| N=2 (p90), N=5 (p99) | The realistic multi-channel middle, and multi-repair in Phase 5 |
| N=2 where both rows are one mailbox by case | Collapse logic at a scale small enough to assert exactly |
| N=1 no-reply address | Failure class 3 classification |
| N=1 reputation error (`blacklisted`/`espblock`) | The ~3% no address swap fixes |
| One broken address linked to 2 agencies | `ICE-FOIA@` shape; must not cross-group (design §3) |

Use `create_batch()` for repeated channels per CLAUDE.md.

### 0b — Real head agencies (dump command)

Only the head is genuinely hard to synthesize — its complexity is the point.

- New `muckrock/agency/management/commands/dump_agency_fixture.py`: given agency IDs, walk `Agency` → `AgencyEmail`/`AgencyPhone`/`AgencyAddress` → `EmailAddress` → open `ReviewAgencyTask`s → bounded `FOIARequest` sample → `EmailCommunication` + `EmailError` within 24 months.
- Redaction per design §9.3: always blank `User.email` and set unusable passwords; for currently-embargoed requests only, blank title, body, communication bodies, and requester name. Leave non-embargoed content, agency emails, and SMTP output as-is.
- Target FBI (23 channels, case-split), DOE HQ (22 channels, low impact), Seattle PD (portal address). Output gitignored.

**Tests:** `muckrock/agency/tests/test_commands.py` — redaction applies to embargoed and not to non-embargoed; the walk includes error rows and excludes rows older than 24 months.

---

## Phase 1 — Per-channel task model

**Goal:** `ReviewAgencyTask` identity becomes `(agency, source, email)`.

### Red

New `muckrock/task/tests/test_querysets.py::TestReviewAgencyTaskQuerySet`:

- `ensure_one_created(agency=a, source="email", email=e1)` and the same call with `e2` produce **two** tasks.
- Repeating the `e1` call returns the same task (idempotent).
- `email=None` (staff/stale) still dedups to one task per `(agency, source)`.
- Pre-existing duplicates on the same key still collapse via the `MultipleObjectsReturned` path.

In `test_models.py`: a mailgun bounce on `FOIPAQUESTIONS@fbi.gov` creates a task carrying that `EmailAddress`; a second bounce on a *different* address at the same agency creates a second task, not a reuse of the first.

### Green

- `muckrock/task/models.py:332` — add `email = models.ForeignKey("communication.EmailAddress", null=True, blank=True, on_delete=models.PROTECT, related_name="review_tasks")`. Nullable is required: `staff`/`stale` tasks legitimately have no channel. Schema migration only.
- `muckrock/task/querysets.py:334` — `ensure_one_created` already forwards `**kwargs` to `get_or_create`, so passing `email=` works with no signature change. Verify the `MultipleObjectsReturned` recovery path filters on the same kwargs (it does).
- `muckrock/mailgun/views.py:465` — pass `email=recipient`.
- `muckrock/foia/models/request.py:955` — pass `email=self.email`.
- Leave `muckrock/agency/views.py:117`, `muckrock/foia/views/list.py:326`, `muckrock/agency/tasks.py:23` alone — null channel is correct there.
- `ReviewAgencyTaskFactory` gains an optional `email` sub-factory (default `None`).

No DB-level unique constraint. `ensure_one_created` is the only creation path, and a constraint over a nullable column plus the existing duplicate-collapse logic buys inconsistency, not safety.

### Green criterion

New queryset tests pass; the full existing `muckrock/task/tests/` suite passes unchanged.

---

## Phase 2 — Channel identity, classification, and impact

**Goal:** one place that answers, for an agency: what are its real mailboxes, which are broken, how, and how much traffic each is blocking. This is the data layer for Phases 3–5.

### Red

New `muckrock/task/tests/test_channels.py`:

- **Case collapsing:** `FOIPAQUESTIONS@fbi.gov` (2 blocked), `foipaquestions@fbi.gov` (3), `FOIPAQuestions@fbi.gov` (1) collapse to one channel with 6 blocked and 3 member rows. Assert the canonical address chosen is deterministic (lowest-pk row).
- **Active-channel definition:** an error-status `AgencyEmail` link with no open requests routed to it is *not* an active channel; an address with open requests routed to it *is*, even if the `AgencyEmail` link is clean.
- **Failure classification:** `seattle@mycusthelp.net` → `portal`; `noreply@securerelease.us` → `portal`; `donotreply@hq.dhs.gov`, `no-reply@x.gov`, `postmaster@usdoj.gov` → `noreply`; `foia@example.gov` with SMTP 550 → `dead`.
- **Reputation errors distinguishable:** an error with `reason` in (`blacklisted`, `espblock`) surfaces as sender-side, not as a dead mailbox.
- **Error recency:** last-error datetime and age exposed; a channel whose newest error is 3 years old is flagged stale.
- **Blocked count never conflated with channel count:** an agency with 22 channels and 49 blocked reports 49, not 22.

### Green

New module `muckrock/task/channels.py`:

- `normalize_channel_key(email) -> str` — lowercase local part and domain. This is the collapse key; it deliberately differs from `EmailAddressQuerySet._normalize_email` (`muckrock/communication/models.py:81`), which lowercases only the domain. Do not change `_normalize_email` — existing rows depend on its behavior.
- `classify_channel(email_address, errors) -> str` in `{"dead", "portal", "noreply", "reputation"}`. Portal detection matches the address domain against portal domains derived from `PORTAL_TYPES` plus a small explicit map (`mycusthelp.net`, `securerelease.us`, `foiaonline.gov`, `nextrequest.com`, `mail.foia.state.gov`). No-reply detection matches local-part prefixes. Classification is display-only — it never triggers a repair action.
- `Channel` dataclass: `key`, `canonical_address`, `member_addresses`, `blocked_count`, `is_primary`, `classification`, `last_error`, `last_error_code`, `last_error_reason`, `last_confirm`, `error_count`, `foias`.
- `agency_channels(agency) -> list[Channel]` — builds the roster for one agency, sorted by `blocked_count` descending. Includes healthy channels (design §6) with a `has_error` flag so callers can filter.
- `Agency`-level rollup: `total_blocked`, `channels_known`, `channels_broken`, `channels_active`, `last_success`.

Query budget: reuse the shape already proven in `ReviewAgencyTask.get_review_data()` — one query for open requests grouped by email, separate `in_bulk` annotation queries for error/confirm/open stats. Keep it constant-query per agency regardless of channel count.

### Green criterion

`test_channels.py` passes. Add an `assertNumQueries` test pinning `agency_channels` to a fixed query count with 1 channel and with 20.

---

## Phase 3 — Impact-ordered queue

**Goal:** the list view orders and reads by blocked-request impact, and exposes the filters staff need.

### Red

`muckrock/task/tests/test_views.py::ReviewAgencyTaskListViewTests` additions:

- Default ordering is `blocked_count` descending — a task blocking 100 requests precedes one blocking 1, regardless of `date_created`.
- `?sort=date_created` still works (impact is the *default*, not the only order).
- `min_blocked=10` excludes a task blocking 3.
- `source=unlabeled` returns only null-source tasks; `source=email` excludes them. Currently impossible — the filter offers only the four labelled sources.
- Tasks for the same agency carry a shared grouping key in context, so twelve State Dept rows render as one group.
- Zero-active-request tasks are excluded by default and included with `?zero_active=1` (design §8).
- `assertNumQueries` does not grow with the number of tasks in the list.

### Green

- `muckrock/task/views.py:326` — `ReviewAgencyTaskList.get_queryset()` annotates `blocked_count` via a `Count` subquery over open requests routed to the task's channel (falling back to all the agency's open requests when `email` is null). Set `default_sort = "-blocked_count"` and add `sort_map` entries.
- `muckrock/task/querysets.py` — `ReviewAgencyTaskQuerySet.annotate_blocked()`; extend `preload_list()` to `select_related("email")`.
- `muckrock/task/filters.py:209` — add `min_blocked`/`max_blocked` `NumberFilter`s, a `source` choice for unlabeled (`ChoiceFilter` with a `method` mapping the sentinel to `source__isnull=True`), and a `zero_active` boolean.
- `muckrock/templates/task/review_agency.html` — per-row: address, blocked count, classification badge, primary flag, last error (code translated, with age), last successful response (absolute + relative), source badge, link to the detail view. Group consecutive rows by agency. Plain markup, no styling.

**Benchmark gate (design §9):** before merging, time the annotated list against production-scale row counts locally. If it exceeds ~1s, cache `blocked_count` on the task, refreshed by the existing task-list path, rather than reworking the view.

### Green criterion

New view tests pass; `_test_n_plus_one_query` still holds.

---

## Phase 4 — Agency detail view

**Goal:** a real URL rendering one agency's full channel roster, replacing the inline AJAX panel.

### Red

New `muckrock/task/tests/test_views.py::ReviewAgencyDetailViewTests`:

- `GET /task/review-agency/agency/<agency_pk>/` returns 200 for staff, 302/403 for non-staff.
- Context contains agency identity, `total_blocked`, roster shape counts, `last_success`, and a `channels` list.
- Case-variant rows appear as **one** channel entry.
- Healthy channels are present and marked.
- A portal-classified channel is present with its classification, and the context flags that email repair is the wrong tool.
- Mail and phone are in context (demoted, not omitted).
- `assertNumQueries` is constant between a 1-channel and a 20-channel agency.
- The rendered page contains a `<script type="application/json">` payload that round-trips to the same channel data (the Svelte handoff).

### Green

- `muckrock/task/views.py` — new `ReviewAgencyDetailView(DetailView)` on `Agency`, staff-gated, consuming `agency_channels()` from Phase 2.
- `muckrock/task/urls.py` — route `review-agency/agency/<int:pk>/`, name `review-agency-detail`.
- `muckrock/templates/task/review_agency_detail.html` — minimal shell: agency header, rollup numbers, and a `{{ channels_json|json_script:"review-agency-data" }}` block plus a mount `<div id="review-agency-app">`. Mail/phone behind a `<details>`.
- Keep `review_agency_ajax` and `muckrock/templates/lib/review_agency.html` working as the rollout fallback.

### Green criterion

Detail view tests pass; existing AJAX-panel tests unchanged.

---

## Phase 5 — Repair, single and multi-channel

**Goal:** staff can repair one channel or several in one submit, and the Svelte component owns selection state.

### Red

New `muckrock/task/tests/test_forms.py::TestChannelRepairForm` and view tests:

- Single channel: new address set on the selected requests; `update_agency_info` promotes the new `AgencyEmail` to primary and demotes the old one; the task resolves when asked.
- **Multi-channel:** one submitted replacement address applied across requests drawn from three different channels resolves all three tasks in a single transaction. Design §6 makes this load-bearing — 1,979 requests sit on non-biggest channels.
- Selecting a portal-classified channel and submitting an email replacement is rejected with a message naming portal switching as out of scope.
- Resolve-without-change closes the task and records no contact edit.
- A repair outcome record is written: which channel, old → new, request count, follow-up sent, by whom, when.
- Follow-up reply still routes through `submit_review_update.delay` on commit.

### Green

- `muckrock/task/forms.py:47` — `ChannelRepairForm`: `new_email`, `channel_keys` (multi), `foia_pks`, `update_agency_info`, `snail_mail`, `resolve`, `reply`. Validation rejects portal-classified targets. Keep `ReviewAgencyTaskForm` in place for the fallback panel.
- `muckrock/task/models.py` — extend `update_contact()` (currently at `:560`) or add `repair_channels(...)` wrapping it for the multi-task case, resolving every affected task inside one `transaction.atomic()`.
- Outcome recording: reuse the existing `Task.note` field (added in migration `0059_task_note`) with a structured payload, plus `resolved_by`/`date_done`. No new model — the readout in Phase 6 needs a few fields, not a table.
- `muckrock/assets/components/ReviewAgencyRepair.svelte` + `muckrock/assets/js/reviewAgency.ts` mount script, following the `getHelp.ts` pattern: read the JSON payload, hold selection state across channel cards, POST a normal form. `{% vite_asset %}` it from the detail template.
- Component receives everything as props — no fetches. Unstyled; markup is a placeholder for manual design work.

### Green criterion

Form and view tests pass. Manually exercise the detail view against the Phase 0 FBI fixture: three case-variant rows must appear as one channel and repair once.

---

## Phase 6 — Resolved-task readout and reopen linkage

### Red

- A resolved task renders its outcome line: channel, old → new, requests updated, follow-up sent, by whom, when.
- "Did it hold" — a successful communication after `date_done` shows as held; none shows as unverified.
- A new task on the same `(agency, email)` after a resolve links forward from the resolved task.

### Green

- `ReviewAgencyTaskQuerySet` — `with_outcome()` annotating the post-resolve success check.
- `ReviewAgencyTask.successor` — a property resolving the newest open task on the same `(agency, email)`. A property, not a FK: the link is derivable, and a FK needs backfilling and can go stale.
- Resolved-task template block rendering all three.

---

## Migration (after Phase 5, before Phase 6)

Retroactive split, strategy 3 from design §4: channels carrying blocked active traffic → ~2,265 tasks, down from 3,677.

- Write as a **management command**, not a data migration. It needs dry-run output, re-runnability, and a staged production run — none of which a migration gives us.
- Reuse `agency_channels()` from Phase 2 so the split and the UI agree by construction.
- Case-collapse before emitting: one task per real mailbox, blocked counts summed. This is the one delicate step.
- For each open task: emit per-channel tasks preserving `date_created` and `source` (null source stays null), then resolve the original with a note pointing at its successors. Never delete.
- Tests: FBI-shaped input (23 rows → ~18 tasks, the 869-request mailbox intact as one); single-channel agency → exactly one task; zero-active agency → no task; `--dry-run` writes nothing.

## Out of scope, per design §2

Portal switching (leave the classification seam only), fax and snail-mail repair workflows, the `stale` job's trigger conditions, Zendesk, bulk auto-resolve. Source choices and resolve semantics unchanged.
