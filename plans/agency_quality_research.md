# Agency Quality Research

Research notes for redesigning the ReviewAgencyTask UI. All numbers are read-only snapshots from production (2026-07-21 through 2026-07-27). No mutations performed or proposed.

> **TL;DR** — 3,647 open review-agency tasks span 3,641 agencies. Those agencies *touch* 25,962 active FOIA requests (54.6% of the 47,412 system-wide active pool) — but only **10,074 of those requests (~21.2% of live activity) are actually on a broken channel**. The other ~15,888 are on flagged agencies but routing through a working portal, alternate email, or otherwise-responsive queue. The refined figure is what the review-task UI should optimize for. See §11.5 for the refinement, §14 for the top-50 head, §15 for the strategic reframe, and §7 / §11 / §12 / §13 for composition detail.
>
> **Original "agencies touch" framing preserved below as a naïve upper bound; refined channel-aware counts are the load-bearing numbers.** Overcount by source: `stale` 78%, `email` 68%, unlabeled 51%, `fax` 49%, `staff` 0%.

---

## 1. Agency status (baseline)

| Status | Count | % of total |
|----------|-------:|-----------:|
| Approved | 28,561 | 81.2% |
| Rejected |  6,609 | 18.8% |
| Pending  |     25 |  0.1% |
| **Total** | **35,195** | **100%** |

---

## 2. Rejected agencies × attached FOIA requests

| Metric | Count |
|---|---:|
| Rejected agencies (total) | 6,609 |
| Rejected agencies with any request attached | 36 |
| Rejected agencies with an active request attached | 2 |
| Requests on rejected agencies (all statuses) | 52 |
| Active requests on rejected agencies | 3 |

"Active" = `FOIARequest.status` not in `END_STATUS` (`rejected`, `no_docs`, `done`, `partial`, `abandoned`, `consolidated`). Source: `foia/models/request.py:74`.

---

## 3. Open ReviewAgencyTasks — by source

| Source | Open tasks | Distinct agencies | Share of backlog |
|---|---:|---:|---:|
| `email` (bad email) | 2,173 | 2,169 | 59.6% |
| *(no source set)* | 646 | 645 | 17.7% |
| `fax` (bad fax) | 522 | 522 | 14.3% |
| `stale` (stale request) | 293 | 293 | 8.0% |
| `staff` (manual review) | 13 | 13 | 0.4% |
| **Total** | **3,647** | **3,641** | **100%** |

Source choices: `task/models.py:337-342`. Uniqueness is per `(agency, source)` open pair via `ReviewAgencyTaskQuerySet.ensure_one_created` (`task/querysets.py:334`).

---

## 4. Agencies with a quality problem — union view

| Bucket | Agencies | % of all agencies |
|---|---:|---:|
| All agencies | 35,195 | 100% |
| Approved & has open review task | 3,640 | 10.3% |
| Approved & clean | 24,921 | 70.8% |
| Rejected (any) | 6,609 | 18.8% |
| Rejected & has open review task | 1 | ~0% |
| Pending | 25 | 0.1% |
| **Union of "problem" agencies (rejected ∪ open-task)** | **~10,249** | **~29.1%** |

Rejected-agency cleanup and comm-channel-repair are essentially disjoint workstreams.

---

## 5. Unlabeled (`source=None`) tasks — by year created

| Year | Open tasks | Cumulative |
|---|---:|---:|
| 2019 | 100 | 100 |
| 2020 | 315 | 415 |
| 2021 | 231 | 646 |
| 2022+ | 0 | 646 |

Zero unlabeled tasks created since 2021 — the code path that produced them has already stopped.

## 6. Unlabeled (`source=None`) tasks — by jurisdiction level

| Level | Agencies | Share |
|---|---:|---:|
| Local (`l`) | 415 | 64.3% |
| State (`s`) | 147 | 22.8% |
| Federal (`f`) | 83 | 12.9% |
| **Total distinct agencies** | **645** | **100%** |

646 tasks over 645 agencies → one agency has 2 unlabeled tasks; effectively 1:1.

---

## 7. Backlog composition → design priority

| Source | % of backlog | Distinct workflow needed? | Design priority |
|---|---:|---|---|
| `email` | 59.6% | Fix broken email address | **P0 — dominant** |
| *unlabeled* | 17.7% | Triage bucket (all 2019–21) | **P1 — blocker for filters** |
| `fax` | 14.3% | Verify/replace fax, or snail | **P1** |
| `stale` | 8.0% | Nudge agency or close request | P2 — different action set |
| `staff` | 0.4% | Free-form review | P3 — rounding error |

---

## 8. Current UI inventory

### Form fields (`task/forms.py:47` — `ReviewAgencyTaskForm`)

| Field | Widget | Purpose |
|---|---|---|
| `email_or_fax` | Autocomplete select2 | Pick new contact address |
| `update_agency_info` | Checkbox | Also update agency's default contact |
| `snail_mail` | Checkbox | Fall back to snail mail |
| `resolve` | Checkbox | Mark task resolved after update |
| `reply` | Textarea | Follow-up message to selected requests |

### Action buttons (`templates/task/review_agency.html`)

| Button | Effect |
|---|---|
| Update email | Applies new contact to checked requests, optionally re-sends reply |
| Resolve | Marks task resolved without any update |
| Create ZenDesk Ticket | Defers to Zendesk |

### Filters (`task/filters.py:209` — `ReviewAgencyTaskFilterSet`)

| Filter | Values |
|---|---|
| `agency` | Agency autocomplete |
| `federal` | Yes / No |
| `complicated` | Yes / No (federal or >10 open requests) |
| `source` | staff / stale / email / fax |
| `resolved` / `resolved_by` | inherited from `TaskFilterSet` |

### AJAX detail panel (`templates/lib/review_agency.html`)

| Section | Contents |
|---|---|
| Agency summary | Name, admin link, contact channels (email/fax/phone/address), portal, total open requests, last response |
| Complicated warnings | Banner if federal; banner if >10 open requests |
| Per-address group | For each email/fax on the agency, shows error log + table of open requests with checkboxes |

---

## 9. Gaps: current UI vs. backlog reality

| Backlog reality | Current UI treatment | Gap |
|---|---|---|
| 60% are email problems | Same form as fax/stale/staff | No email-specific fast path (e.g., "domain bouncing for N agencies, replace in bulk") |
| 645 unlabeled legacy tasks | Filter uses `sources` choices only | Cannot filter *to* or *exclude* the legacy blob from any view |
| 293 `stale` tasks are decision-making, not contact-update | Same email_or_fax form | No native action for "nudge sender" or "close request as no-response" |
| ~1 task per agency but form is per-task page | Per-task page with AJAX load | No cross-agency batch surface (e.g., all bad emails on `@nypd.org`) |
| 13 `staff` tasks are one-offs | Same generic form | Fine — no gap |
| Federal / >10 requests are "complicated" | Reactive banner inline | Complication is a triage signal, not just a warning |

---

## 10. Email database — overview

| Metric | Count | % |
|---|---:|---:|
| `EmailAddress` total | 262,293 | 100% |
| `EmailAddress` status = error | 4,956 | 1.9% |
| Attached to ≥1 agency | 53,582 | 20.4% of all emails |
| Attached to ≥1 agency **and** status = error | 4,176 | 7.8% of on-agency emails |

The error rate on agency-attached emails (7.8%) is ~4× the rate on the total table (1.9%) — the agency subset is meaningfully worse.

### Agency ↔ email link table (`AgencyEmail`)

| Metric | Count |
|---|---:|
| `AgencyEmail` rows (total agency ↔ email links) | 70,955 |
| `AgencyEmail` rows where email is in error | 7,850 |

7,850 error links across 4,176 distinct broken emails → the same broken address is linked to ~1.9 agencies on average.

### Error links, by role

| `request_type` | `email_type` | Error links | Share |
|---|---|---:|---:|
| none | none | 6,038 | 76.9% |
| primary | to | 1,678 | 21.4% |
| primary | cc | 86 | 1.1% |
| none | to | 31 | 0.4% |
| primary | none | 11 | 0.1% |
| appeal | to | 5 | 0.1% |
| appeal | none | 1 | 0.0% |
| **Total** | | **7,850** | **100%** |

**Key insight:** 77% of "broken email" links are on emails that aren't currently the agency's primary or appeal contact (`role=none/none`). Only **1,775 error links (22.6%) are on the actively-used contact** (`primary` role). Most stored broken emails are historical/CC/alternate — replacing them won't unblock any request. The 1,775 primary error links are where the real backlog impact lives.

---

## 11. Email errors — types (open `source=email` review tasks, last 24 months)

Scoped to `EmailError` rows on addresses attached to any of the 2,173 agencies with an open email-source review task, `datetime >= now - 2y`.

| Metric | Count |
|---|---:|
| Agencies with an open email task | 2,173 |
| `EmailError` rows in window | 1,306 |
| Distinct email addresses w/ any error in window | 981 |
| Distinct addresses currently `status=error` on these agencies | 2,518 |

**Notable gap:** only 981 of the 2,518 currently-error addresses have generated an error in the last 2 years. **~61% of the "error" flags on these agencies are stale** (no recent bounce event) — either the address was marked bad long ago and never revisited, or the bounces predate the retention window.

### By `event`

| Event | Count | Share |
|---|---:|---:|
| `permanent` | 1,306 | 100% |

Every recent error is a permanent failure — no transient/temporary bounces in the mix. The dataset is unambiguous: mail *cannot* be delivered, retrying won't help.

### By SMTP code (top 10)

| Code | Count | Share | Meaning (typical) |
|---|---:|---:|---|
| `550` | 931 | 71.3% | Mailbox unavailable / user unknown |
| `602` | 136 | 10.4% | Recipient blocked / old address |
| `605` | 86 | 6.6% | Suppression list (past hard bounce) |
| `554` | 51 | 3.9% | Transaction failed / policy reject |
| `612` | 48 | 3.7% | Provider-specific block |
| `498` | 24 | 1.8% | ESP block |
| `450` | 9 | 0.7% | Mailbox busy (transient) |
| `553` | 5 | 0.4% | Mailbox name invalid |
| `502` | 5 | 0.4% | Command not implemented |
| Other | 11 | 0.8% | — |

`550` alone accounts for ~71% — "we mailed a person / mailbox that no longer exists." A dedicated "employee turnover" or "role-mailbox died" workflow would cover the majority.

### By `reason` (Mailgun-normalized)

| Reason | Count | Share |
|---|---:|---:|
| `generic` | 544 | 41.7% |
| `bounce` | 495 | 37.9% |
| `old` | 136 | 10.4% |
| `suppress-bounce` | 86 | 6.6% |
| `blacklisted` | 26 | 2.0% |
| `espblock` | 15 | 1.1% |
| `overquota` | 2 | 0.2% |
| `suppress-complaint` | 2 | 0.2% |
| **Total** | **1,306** | **100%** |

`generic + bounce + old + suppress-bounce = 96.6%` — the address is dead. `blacklisted + espblock = 3.1%` — sender-side reputation issue that no address swap will fix. Two very different remediation paths.

---

## 11.5. Channel-aware "blocked" — the load-bearing definition

The counts in §12 and §14 use a naïve definition: *request is "blocked" if it is active AND its agency has an open ReviewAgencyTask.* That overcounts. A request on a review-flagged agency may still be going through a working channel (portal, alternate email, non-broken fax). The task lives at the **agency** level; the block lives at the **channel** level.

### The channel model

`FOIARequest` stores its outbound channel as direct FKs: `portal`, `email`, `fax`, `address` (`foia/models/request.py:156–194`). `FOIARequest.get_contact_info()` (`foia/models/request.py:860–871`) picks the effective channel in that order — first non-`error`-status one wins; snail-mail address is always a fallback. `ReviewAgencyTask.source` only tags *what kind of problem exists on the agency* — it does not point at which requests are affected.

### Refined "blocked" — per source

Definitions applied:

| Source | Refined test |
|---|---|
| `email` | active AND `foia.email.status = 'error'` |
| `fax` | active AND `foia.fax.status = 'error'` |
| `stale` | active AND `foia.pk` is in `FOIARequest.objects.get_stale()` (per-request stale, not per-agency) |
| `staff` | active on agency (no automatable refinement — manual review) |
| *unlabeled* | active AND (`foia.email.status='error'` OR `foia.fax.status='error'`) |

### Results

| Source | Agencies | Naïve blocked | **Refined blocked** | Overcount | % overcounted |
|---|---:|---:|---:|---:|---:|
| `email` | 2,178 | 13,378 | **4,293** | 9,085 | 67.9% |
| `fax` | 525 | 2,372 | **1,218** | 1,154 | 48.7% |
| `stale` | 299 | 1,870 | **416** | 1,454 | 77.8% |
| `staff` | 13 | 127 | **127** | 0 | 0% |
| *unlabeled* | 646 | 8,215 | **4,020** | 4,195 | 51.1% |
| **Total** | **3,661** | **25,962** | **10,074** | **15,888** | **61.2%** |

Snapshot: 2026-07-27.

### Read-outs

- **~61% of the "blocked" pool was overcounted.** The real backlog impact is ~10,074 requests, not ~25,962. Against the 47,412 active-system total, that's **21.2% of live activity gated by broken channels**, not 54.6%.
- **`stale` is the worst offender (78% overcount).** `stale`-source tasks flag *agency-level* non-response; individual requests within that queue frequently have gotten recent responses via other means. Only the subset from `FOIARequest.objects.get_stale()` is legitimately stuck.
- **`email` overcounts 68%.** For every ~3 active requests on an email-flagged agency, only ~1 is actually on the broken email — the rest route via portal, an alternate email, or a non-broken address on the same agency.
- **`fax` overcounts ~half** (49%). Similar dynamic but less extreme — fax agencies tend to be more fax-committed (see CIA / OMB).
- **`staff` doesn't overcount** — but it's 13 tasks / 127 requests. Rounding error.
- **Priority order shifts.** By refined blocked count: `email` (4,293, 43%) ≈ *unlabeled* (4,020, 40%) > `fax` (1,218) > `stale` (416) > `staff` (127). Email and unlabeled together are 83% of the true backlog.

### Refined top-50 agencies (by channel-aware blocked count)

| # | Agency | Level | Source | Blocked |
|--:|---|:-:|---|--:|
| 1 | U.S. Department of State | f | email | **358** |
| 2 | Central Intelligence Agency | f | fax | 316 |
| 3 | National Security Agency | f | unlabeled | 241 |
| 4 | Department of Homeland Security | f | email | 189 |
| 5 | Immigration and Customs Enforcement | f | unlabeled | 188 |
| 6 | Seattle Police Department | l | unlabeled | 177 |
| 7 | Department of Interior, Office of the Secretary | f | unlabeled | 172 |
| 8 | Department of Energy Headquarters | f | unlabeled | 124 |
| 9 | Federal Bureau of Investigation | f | email | 114 |
| 10 | Drug Enforcement Administration | f | unlabeled | 110 |
| 11 | Environmental Protection Agency | f | unlabeled | 97 |
| 12 | Securities and Exchange Commission | f | unlabeled | 95 |
| 13 | United States Customs and Border Protection | f | unlabeled | 93 |
| 14 | U.S. Citizenship and Immigration Services | f | unlabeled | 92 |
| 15 | Department of Health and Human Services | f | unlabeled | 81 |
| 16 | Houston Police Department | l | email | 78 |
| 17 | Philadelphia Police Department | l | unlabeled | 74 |
| 18 | Department of Justice, United States Marshals | f | unlabeled | 73 |
| 19 | Office of the Director of National Intelligence | f | email | 67 |
| 20 | Department of Housing and Urban Development | f | unlabeled | 67 |
| 21 | New York State Police | s | email | 64 |
| 22 | Department of Justice, Office of the Attorney General | f | unlabeled | 64 |
| 23 | United States Secret Service | f | unlabeled | 57 |
| 24 | Boston Police Department | l | unlabeled | 56 |
| 25 | Austin Police Department | l | email | 47 |
| 26 | Texas Department of Public Safety | s | email | 46 |
| 27 | Los Angeles County Sheriff's Department | l | unlabeled | 46 |
| 28 | Bureau of Land Management | f | unlabeled | 44 |
| 29 | St. Louis Metropolitan Police Department | l | unlabeled | 43 |
| 30 | Inspector General Central Intelligence Agency | f | staff | 42 |
| 31 | Baltimore Police Department | l | email | 41 |
| 32 | Chicago Police Department | l | unlabeled | 41 |
| 33 | National Archives And Records Administration | f | fax | 39 |
| 34 | Jacksonville Sheriff's Office | l | unlabeled | 39 |
| 35 | Tampa Police Department | l | email | 38 |
| 36 | Indianapolis Metropolitan Police | l | email | 38 |
| 37 | Federal Communications Commission | f | email | 36 |
| 38 | Nassau County Police Department | l | staff | 36 |
| 39 | Pennsylvania State Police | s | email | 35 |
| 40 | Department of Transportation | f | unlabeled | 35 |
| 41 | U.S. Office of Management and Budget | f | fax | 34 |
| 42 | Department of Justice, Office of Information Policy | f | unlabeled | 34 |
| 43 | Indiana State Police | s | email | 33 |
| 44 | Department of Justice, Executive Office for U.S. Attorneys | f | unlabeled | 33 |
| 45 | Department of Commerce | f | email | 32 |
| 46 | San Francisco Police Department | l | unlabeled | 32 |
| 47 | St. Louis County Police Department | l | unlabeled | 32 |
| 48 | University of Michigan | s | email | 31 |
| 49 | Federal Trade Commission | f | unlabeled | 31 |
| 50 | Social Security Administration | f | unlabeled | 30 |

### Refined aggregates

| Metric | Value |
|---|---:|
| Total refined blocked | **10,076** |
| Top-50 subtotal | **4,015** |
| Top-50 share of refined backlog | **39.8%** |
| Top 5 (State, CIA, NSA, DHS, ICE) | 1,392 (13.8%) |
| Top 10 | 2,024 (20.1%) |

### Refined composition

| Level | Agencies in refined top-50 | Share |
|---|---:|---:|
| Federal (`f`) | 30 | 60% |
| Local (`l`) | 15 | 30% |
| State (`s`) | 5 | 10% |

| Source | Agencies in refined top-50 | Share |
|---|---:|---:|
| *unlabeled* | 29 | **58%** |
| `email` | 16 | 32% |
| `fax` | 3 | 6% |
| `staff` | 2 | 4% |

### Movement vs. naïve top-50 (§14)

| Agency | Naïve rank | Refined rank | Naïve → Refined | Note |
|---|:-:|:-:|:-:|---|
| FBI | #1 | #9 | 2,035 → 114 (−94%) | Almost all active FBI requests use a channel that isn't the flagged email |
| State | #3 | **#1** | 657 → 358 (−45%) | Real head — still the top block |
| CIA | #2 | #2 | 848 → 316 (−63%) | Fax-only agency; refined count is honest |
| NSA | #6 | #3 | 292 → 241 (−17%) | Small overcount → high refined rank |
| Seattle PD | #12 | #6 | 182 → 177 (−3%) | Tight — mostly real |
| NYPD | #8 | not in top-50 | 274 → below-cutoff | `stale` source — most NYPD requests aren't per-request stale |
| Phoenix PD | #30 | not in top-50 | 107 → below-cutoff | Same, `stale` source |

The `stale`-heavy municipal police entries (NYPD, Phoenix) drop out entirely — an insight the naïve count masked. The `unlabeled` federal cluster tightens its grip on the head.

---

## 12. Active requests blocked, per agency under review

> **Read note:** The counts in this section use the naïve definition — *active requests on a flagged agency*, regardless of which channel each request is actually using. That's the "agencies touch" upper bound. **For the channel-aware "actually blocked" figures see §11.5**, which corrects a 61% overcount. §12 and §14 are preserved as-is because they still measure something meaningful — the *scope of agencies with a review flag* — but they should not be read as the true block count.

### Distribution — active requests per agency (any source)

| Open active FOIAs | Agencies | Share |
|---|---:|---:|
| 0 | 645 | 17.7% |
| 1 | 1,141 | 31.3% |
| 2–5 | 1,167 | 32.0% |
| 6–10 | 287 | 7.9% |
| 11–50 | 328 | 9.0% |
| 51+ | 79 | 2.2% |
| **Total** | **3,647** | **100%** |

| Summary stat | Value |
|---|---:|
| Total blocked active requests | **25,822** |
| Mean per agency | 7.08 |
| Median per agency | 2 |
| Max on a single agency | 2,035 |

**Key insights:**
- **17.7% of tasks have zero active requests** — 645 agencies with no active queue right now. Initially looked like an obvious auto-resolve; §13 shows the picture is more nuanced (46% had activity within the last year — broken channel still needs fixing).
- **Long tail dominates**: median is 2 but the top 79 agencies (2.2%) each block 51+ requests. Prioritizing by "requests blocked" would fast-track ~5,000+ requests via just those 79.
- **407 agencies (11.2%) block 11+ requests each** — a "high-impact queue" filter is a natural triage lever.

### By task source — active-request load

| Source | Agencies | Active requests blocked | Avg per agency |
|---|---:|---:|---:|
| `email` | 2,173 | 13,316 | 6.1 |
| *unlabeled* | 646 | 8,181 | **12.7** |
| `fax` | 522 | 2,361 | 4.5 |
| `stale` | 293 | 1,860 | 6.3 |
| `staff` | 13 | 127 | 9.8 |
| **Total** | **3,647** | **25,845***| — |

<sub>*Cross-source sum slightly ≠ 25,822 total because a small number of agencies may hold multiple source-tagged tasks.</sub>

**Unlabeled tasks are the heaviest per agency** (12.7 blocked requests vs. 6.1 for email). This flips the priority calculus from §7: unlabeled is 17.7% of *tasks* but blocks ~32% of the *requests-blocked pool*. Cleaning the legacy blob has outsized user-facing impact.

---

## 13. Agencies with zero active requests — deep dive

Slight numerical drift from §12 because this query used `.distinct()` on the task→agency join, resolving a small number of agencies with multiple open tasks:

| Metric | §12 | §13 |
|---|---:|---:|
| Agencies with open review task | 3,647 (task count) | 3,641 (distinct agencies) |
| Of those, zero active requests | 645 | **639** |

### Overlap with unlabeled tasks — the hypothesis was wrong

| Set | Agencies |
|---|---:|
| Zero-active-requests agencies (A) | 639 |
| Unlabeled-task agencies (B) | 645 |
| **A ∩ B** — zero active AND unlabeled | **44** |
| A only — zero active, task has a source | 595 |
| B only — unlabeled task, has active requests | 601 |

Only 44 agencies are in both sets. The size similarity (639 vs 645) was coincidental — these are **two largely disjoint populations of ~600 agencies each**. Any UI needs to handle them separately.

### What source opened the zero-active tasks?

| Source | Zero-active agencies | Share |
|---|---:|---:|
| `email` | 472 | 73.9% |
| `fax` | 115 | 18.0% |
| *unlabeled* | 44 | 6.9% |
| `stale` | 7 | 1.1% |
| `staff` | 4 | 0.6% |
| **Total** | **639** | **100%** |

The zero-active pool is **dominated by broken email/fax channels** on agencies whose active queue happens to be empty right now. It is *not* a legacy blob — 92% have a modern source label.

### Historical request volume (any status)

| Total requests ever | Agencies | Share |
|---|---:|---:|
| 0 (never had any) | 1 | 0.2% |
| 1 | 201 | 31.5% |
| 2–5 | 337 | 52.7% |
| 6–20 | 94 | 14.7% |
| 21–100 | 6 | 0.9% |
| 101+ | 0 | 0.0% |
| **Total** | **639** | **100%** |

| Summary | Value |
|---|---:|
| Sum of requests across all 639 agencies | **2,205** |
| Max requests on any one agency | 35 |

These are **low-volume agencies** — 84% have ≤5 lifetime requests. They're the long-tail small locality / niche agency population, not the missing-federal-department kind.

### Recency of last request activity

| Last request update | Agencies | Share |
|---|---:|---:|
| Never had a request | 1 | 0.2% |
| < 1 year ago | 295 | 46.2% |
| 1–3 years ago | 241 | 37.7% |
| 3–5 years ago | 99 | 15.5% |
| 5–10 years ago | 3 | 0.5% |
| 10+ years ago | 0 | 0.0% |
| **Total** | **639** | **100%** |

| Extreme | Value |
|---|---|
| Oldest last-activity across the set | 2020-06-21 |
| Newest last-activity across the set | 2026-07-20 *(yesterday)* |

**The biggest surprise:** 46% of these agencies had a request update *in the last year* — some literally yesterday. So "zero active requests" ≠ "abandoned." It means: someone recently *closed* a request on this agency (rejected/done/etc.), the queue happens to be empty at this moment, and the review task lingers.

### Design implications — the "auto-resolve" idea needs qualification

The naive read from §12 was: "639 zero-active tasks → auto-resolve, nothing to fix." §13 refines that into a bad default:

- ✅ **Safe auto-resolve candidates**: `stale` source + zero active + last activity ≥ 3 years ago (~small number, low risk).
- ⚠️ **Not safe to auto-resolve**: the 472 email-source zero-active agencies. The broken email is *still broken* — the moment a new request comes in, it will hit the same wall and reopen the task. Resolving without a contact fix just kicks the can.
- 🧭 **Better framing**: "zero active" is a **triage hint** (small blast radius, safe to defer), not a **resolve trigger**. The UI should surface it as a filter, not an auto-action.

The 44 in the overlap (unlabeled + zero-active + generally 3–5y stale) *are* legitimately safe to bulk-resolve — but that's a rounding-error slice of the backlog, not a big win.

---

## 14. Top 50 agencies by blocked active requests (naïve — see §11.5 for channel-aware recount)

> **Read note:** The naïve headline below counts every active request on a flagged agency, not only requests on a broken channel. **The channel-aware refined counts in §11.5 correct this by 61%** — the true block pool is ~10,074 requests (21.2% of system-wide active), not 25,872 (54.6%). The naïve top-50 is retained here for the "on flagged agencies" upper bound and to make the FBI/NYPD/Phoenix rank shifts visible against §11.5.
>
> | Metric | Naïve (on-flagged-agency) | **Refined (channel-aware)** |
> |---|---:|---:|
> | Total active FOIA requests (system-wide) | 47,412 | 47,412 |
> | Blocked | 25,872 | **10,074** |
> | Share of live activity | 54.6% | **21.2%** |
> | Unblocked | 21,540 | 37,338 |
>
> **The queue is growing.** The naïve blocked total drifted from **25,822 → 25,872 → 25,962** across the three snapshot dates (2026-07-21 / 24 / 27) — roughly +20 requests newly attached to a flagged agency per day. Refined recount available only at the final snapshot (10,074), but the growth signal from the naïve number is unaffected by the refinement.

Ordered by count of active requests (`status not in END_STATUS`) attached to an agency with an open `ReviewAgencyTask`.

| # | Agency | Level | Jurisdiction | Source | Blocked |
|--:|---|:-:|---|---|--:|
| 1 | Federal Bureau of Investigation | f | United States of America | email | **2,035** |
| 2 | Central Intelligence Agency | f | United States of America | fax | 848 |
| 3 | U.S. Department of State | f | United States of America | email | 657 |
| 4 | Immigration and Customs Enforcement | f | United States of America | unlabeled | 537 |
| 5 | Department of Homeland Security | f | United States of America | email | 480 |
| 6 | National Security Agency | f | United States of America | unlabeled | 292 |
| 7 | Department of Interior, Office of the Secretary | f | United States of America | unlabeled | 288 |
| 8 | New York City Police Department | l | New York City (NY) | stale | 274 |
| 9 | United States Customs and Border Protection | f | United States of America | unlabeled | 253 |
| 10 | Department of Health and Human Services | f | United States of America | unlabeled | 236 |
| 11 | Drug Enforcement Administration | f | United States of America | unlabeled | 191 |
| 12 | Seattle Police Department | l | Seattle (WA) | unlabeled | 182 |
| 13 | Chicago Police Department | l | Chicago (IL) | unlabeled | 179 |
| 14 | Department of Energy Headquarters | f | United States of America | unlabeled | 179 |
| 15 | Philadelphia Police Department | l | Philadelphia (PA) | unlabeled | 159 |
| 16 | Environmental Protection Agency | f | United States of America | unlabeled | 157 |
| 17 | Securities and Exchange Commission | f | United States of America | unlabeled | 152 |
| 18 | Boston Police Department | l | Boston (MA) | unlabeled | 145 |
| 19 | United States Department of the Army | f | United States of America | email | 131 |
| 20 | U.S. Citizenship and Immigration Services | f | United States of America | unlabeled | 130 |
| 21 | Food and Drug Administration | f | United States of America | email | 130 |
| 22 | National Personnel Records Center, Military Personnel Records | f | United States of America | unlabeled | 126 |
| 23 | Houston Police Department | l | Houston (TX) | email | 120 |
| 24 | Massachusetts State Police | s | Massachusetts | unlabeled | 120 |
| 25 | Atlanta Police Department | l | Atlanta (GA) | email | 119 |
| 26 | Department of Defense, Office of the Secretary of Defense | f | United States of America | email | 112 |
| 27 | U.S. Department of Education | f | United States of America | email | 111 |
| 28 | Air Force | f | United States of America | unlabeled | 109 |
| 29 | San Francisco Police Department | l | San Francisco (CA) | unlabeled | 107 |
| 30 | Phoenix Police Department | l | Phoenix (AZ) | stale | 107 |
| 31 | Federal Communications Commission | f | United States of America | email | 102 |
| 32 | Detroit Police Department | l | Detroit (MI) | email | 98 |
| 33 | Department of Justice, Office of the Attorney General | f | United States of America | unlabeled | 97 |
| 34 | Department of Justice, United States Marshals | f | United States of America | unlabeled | 92 |
| 35 | U.S. Department of Veterans Affairs | f | United States of America | email | 90 |
| 36 | Department of Housing and Urban Development | f | United States of America | unlabeled | 90 |
| 37 | New York State Police | s | New York | email | 89 |
| 38 | Executive Office for United States Attorneys | f | United States of America | email | 87 |
| 39 | Las Vegas Metropolitan Police Department | l | Las Vegas (NV) | email | 85 |
| 40 | Baltimore Police Department | l | Baltimore (MD) | email | 82 |
| 41 | Bureau of Land Management | f | United States of America | unlabeled | 81 |
| 42 | Transportation Security Administration | f | United States of America | unlabeled | 80 |
| 43 | Office of Personnel Management | f | United States of America | email | 80 |
| 44 | Office of the Director of National Intelligence | f | United States of America | email | 79 |
| 45 | United States Secret Service | f | United States of America | unlabeled | 79 |
| 46 | Dallas Police Department | l | Dallas (TX) | email | 79 |
| 47 | Mayor's Office (Chicago) | l | Chicago (IL) | unlabeled | 78 |
| 48 | U.S. Office of Management and Budget | f | United States of America | fax | 76 |
| 49 | National Institutes of Health | f | United States of America | email | 76 |
| 50 | Los Angeles County Sheriff's Department | l | Los Angeles County (CA) | unlabeled | 75 |

### Aggregates

| Metric | Value |
|---|---:|
| Blocked requests in top 50 | **~10,361** |
| Share of the full 25,822-request backlog | **~40.1%** |
| FBI alone | 2,035 (7.9% of full backlog) |
| Top 5 (FBI, CIA, State, ICE, DHS) | 4,557 (17.6%) |
| Top 10 | 6,091 (23.6%) |

### Composition

| Level | Agencies in top 50 | Share |
|---|---:|---:|
| Federal (`f`) | 33 | 66% |
| Local (`l`) | 15 | 30% |
| State (`s`) | 2 | 4% |

| Source | Agencies in top 50 | Share of top 50 | Share of full backlog (from §3) |
|---|---:|---:|---:|
| *unlabeled* | 26 | **52%** | 17.7% |
| `email` | 20 | 40% | 59.6% |
| `fax` | 2 | 4% | 14.3% |
| `stale` | 2 | 4% | 8.0% |

---

## 15. Strategic reframe — a substantial but not majority bottleneck

The findings, taken together, change the character of what the ReviewAgencyTask UI redesign is *for*. This section was rewritten after the channel-aware refinement in §11.5 corrected the block count from 25,872 to 10,074 — a 61% reduction. Earlier drafts overstated scope; the corrected read follows.

### What we thought going in

An admin backlog. ~3,647 open review tasks — a maintenance queue. The design job is to make triage nicer for staff.

### What the data actually shows

| Framing shift | Old read | Corrected read (post-§11.5) |
|---|---|---|
| **Scope** | Internal admin cleanup | **~21% of live MuckRock activity gates behind broken channels** (10,074 of 47,412). Not a majority — but substantial, and the biggest single operational bottleneck we can see. |
| **Trend** | Static "always some backlog" | **Growing** — naïve blocked drifted +140 across 2026-07-21 → 07-27, roughly 20/day. Refined trend not yet measured but likely tracks proportionally. |
| **Distribution** | Long queue of similar items | Head-heavy but flatter than the naïve view suggested: **top 50 = 39.8% of refined pool** (was 40% naïve, similar). No single agency dominates the way FBI *appeared* to. |
| **`unlabeled` tasks** | Legacy cruft to filter out | Parked on the highest-leverage federal agencies — **58% of the refined top 50** (up from 52% naïve). Legacy blob is *more* overrepresented after refinement, not less. |
| **FBI** | #1 blocker (2,035 requests, 7.9% of pool) | **Drops to #9 (114 requests)** — the vast majority of active FBI requests use a working channel. Big, but not category-of-its-own. |
| **`stale`-heavy municipal police** (NYPD, Phoenix) | Top 50 entries | **Both drop out of the refined top 50** — per-agency `stale` doesn't mean per-request stale. |
| **"Zero active" tasks** | Auto-resolve candidates | Broken channels on live agencies — resolving without a fix just kicks the can. Unchanged. |
| **"Bad email" as a category** | Domain-level provider issues | **96.6% are "the address is dead"** (SMTP 550 dominant); only ~3% are sender-side reputation. Unchanged. |
| **Task per agency** | Assumed | Confirmed — ~1:1 agency-to-task ratio; per-agency is the natural unit. Unchanged. |

### What the redesign is really doing

Not a nicer admin queue. It is a **targeted intervention on the largest operational bottleneck we can measurably identify**: broken agency contact channels gating ~10K live FOIA requests (~21% of active volume). Ambitious but bounded — not the whole product.

That reframes the priority ordering:

1. **Refined top-blocked queue view** (sort by channel-aware blocked count desc). The refined top 50 clears ~4,015 requests with 50 targeted contact-repairs — ~40% of the true block pool. This is still by far the highest-leverage single UI change.
2. **Per-agency detail page as the unit of work.** Task-per-agency held up across every slice. Source (`email` / `fax` / `stale` / `unlabeled`) is a *badge* and a *filter*, not a workflow driver.
3. **Family / cohort grouping.** DOJ family (FBI + DEA + US Marshals + EOUSA + AG's Office + OIP = ~430 refined blocked), DHS family (DHS + ICE + CBP + USCIS + Secret Service = ~626 refined blocked), 15 municipal police departments in the refined top 50 — cohorts where one contact fix propagates.
4. **Growth-rate visibility.** Since the queue is growing, the UI should surface intake rate vs. resolve rate — a dashboard-level "are we ahead or behind" indicator.
5. **Legacy `unlabeled` triage is the single highest-leverage cleanup.** 40% of the refined block pool and 58% of the refined top 50. It's parked on major federal agencies. Not tidy-up work — it's restoring FOIA throughput on the biggest federal targets.
6. **`stale` is a lower-priority filter than the raw task count suggested.** 78% overcount means only 416 requests are per-request stale — the redesign should still handle them, but they're a rounding error at the level of the full block pool.

### What the redesign is *not*

- Not a bulk auto-resolve tool. Almost nothing here can be safely mass-closed; the underlying channels are still broken.
- Not a source-per-workflow split. The four sources overlap in agency and remediation; separating them into different pages fragments a naturally per-agency workflow.
- Not a filter-heavy UI. The head is heavy; most staff time should be spent on the top-of-queue, not on segmenting a 3,647-row list.
- **Not the whole product bottleneck.** ~79% of active requests are on unflagged agencies or on working channels — the review-task UI can't reach them. Framing this project as "unblock everything" would overpromise.

### Notable clusters (refined)

- **Municipal police departments (15 in the refined top 50):** Seattle, Houston, Philadelphia, Boston, Baltimore, Chicago, Jacksonville, Tampa, Indianapolis Metro, Nassau Cty, Austin, LA Cty Sheriff, St. Louis Metro, St. Louis Cty, SF. NYPD and Phoenix — top-of-list in the naïve view — drop out because their tasks are `stale` and most active requests aren't per-request stale. Still a cohort.
- **DOJ family** (FBI, DEA, US Marshals, EOUSA, AG's Office, OIP) = ~430 refined blocked. Sharp shrink from the naïve 2,442 — FBI alone accounts for most of that fall.
- **DHS family** (DHS, ICE, CBP, USCIS, Secret Service) = ~626 refined blocked. Naïve was 1,559 — refinement roughly halves this too.
- **`fax`-source in refined top 50 = CIA, OMB, NARA.** Fax-only agencies where the `fax` label reflects agency policy, not a bug. Different workflow: verify the number, not swap channels.

### Design implications

- **Head is heavy but not extreme.** ~40% of refined block pool on 50 agencies. A "top-blocked queue" prioritization view is still the single most impactful UI change.
- **Unlabeled is *even more* overrepresented in the refined top 50** (58% vs. 17.7% of tasks). Priority-one cleanup target.
- **The FBI is not the outlier we thought.** 114 refined blocked, tied with municipal PDs and mid-federal-agencies. Worth fixing but not a dedicated workflow.
- **`stale` deserves a UI de-emphasis.** The naïve view suggested `stale` tasks were 8% of the backlog; refined blocked is 4% of the pool. Keep the filter, but not a primary workflow.
- **The refined figure sets the expectation ceiling.** If the redesign works flawlessly and clears every review task tomorrow, ~10,074 requests unblock — not 25,872. Sizing the win realistically is important for prioritizing the project against other engineering work.

---

## 16. Read-only follow-up questions

Sharpened after §10–13 findings. Highest-signal ones first.

| Question | Would tell us |
|---|---|
| **Overlap: 645 zero-request agencies ∩ 646 unlabeled tasks** | Whether the "no active requests" agencies are essentially the abandoned legacy blob — if so, one filter handles both auto-resolve cases |
| Top email domains among the 981 recently-erroring addresses | Whether one bouncing provider (`.us` locality, a state ESP, a Barracuda-blocked domain) drives a large share — bulk-domain-replace becomes a real workflow |
| Top email domains among the 2,518 currently-`status=error` addresses | Same, but including stale flags — biggest cluster candidates for a domain-scoped triage view |
| Same broken email attached to N agencies (top of 4,176) | 4,176 broken addresses → 7,850 links means many repeats; the top of that list is a bulk-repair unit |
| Task age distribution by source | Where the backlog is oldest; whether recent (< 90d) tasks are a resolvable working set vs. an ossified backlog |
| Tasks created per week by source, last 12 months | Incoming rate vs. resolve rate — is the queue growing? |
| Agencies with 51+ blocked active requests (the 79) | Names + jurisdiction levels — these are the highest-ROI review targets in the system |
| SMTP-code × reason cross-tab | Confirm the "550 + generic/bounce/old" cluster is one workflow ("this person left") vs. "554/blacklisted" (sender-side, different action) |

---

## Reference

| File | Purpose |
|---|---|
| `muckrock/task/models.py:332` | `ReviewAgencyTask` model, sources tuple |
| `muckrock/task/querysets.py:308` | `ReviewAgencyTaskQuerySet.ensure_one_created` (dedup logic) |
| `muckrock/task/views.py:326` | `ReviewAgencyTaskList` view |
| `muckrock/task/views.py:843` | `review_agency_ajax` (detail panel) |
| `muckrock/task/forms.py:47` | `ReviewAgencyTaskForm` |
| `muckrock/task/filters.py:209` | `ReviewAgencyTaskFilterSet` |
| `muckrock/templates/task/review_agency.html` | Row template |
| `muckrock/templates/lib/review_agency.html` | AJAX detail panel |
| `muckrock/agency/models/agency.py:105` | Agency `status` field (pending/approved/rejected) |
| `muckrock/agency/tasks.py:20` | `stale` Celery task — creates `stale`-source ReviewAgencyTasks |
