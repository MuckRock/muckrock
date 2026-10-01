# Channel sizing — snapshot 2026-08-11 13:40

## 1. Headline

| Metric | Value |
|---|---:|
| Open ReviewAgencyTasks | 3,677 |
| Agencies with an open task | 3,671 |
| Active FOIA requests (system-wide) | 48,038 |
| **Agencies with >=1 blocked email channel** | **1,684** |
| **Distinct blocked (agency, email) channels** | **2,265** |
| Blocked active requests on those channels | 8,562 |
| — excluding reqs with a working portal | 6,749 |
| — channels after portal exclusion | 2,151 |

## 2. Blocked channels per agency — distribution

| Blocked channels | Agencies | Share |
|---|---:|---:|
| 1 | 1,375 | 81.7% |
| 2 | 200 | 11.9% |
| 3 | 57 | 3.4% |
| 4–5 | 36 | 2.1% |
| 6–10 | 11 | 0.7% |
| 11–20 | 3 | 0.2% |
| 21–50 | 2 | 0.1% |

| Stat | Value |
|---|---:|
| Max channels on one agency | **23** |
| Mean | 1.35 |
| Median | 1 |
| p90 | 2 |
| p99 | 5 |
| Agencies with exactly 1 | 1,375 (81.7%) |
| Agencies with 2+ | 309 |

## 3. Top 30 agencies by blocked requests — how many channels each

| # | Agency | Lvl | Blocked | Channels | Biggest | Top ch. share |
|---:|---|:-:|---:|---:|---:|---:|
| 1 | Federal Bureau of Investigation | f | 1,075 | 23 | 481 | 45% |
| 2 | U.S. Department of State | f | 337 | 7 | 273 | 81% |
| 3 | Department of Homeland Security | f | 189 | 8 | 135 | 71% |
| 4 | Seattle Police Department | l | 178 | 3 | 159 | 89% |
| 5 | Immigration and Customs Enforcement | f | 155 | 5 | 76 | 49% |
| 6 | Environmental Protection Agency | f | 90 | 11 | 31 | 34% |
| 7 | Houston Police Department | l | 78 | 1 | 78 | 100% |
| 8 | Philadelphia Police Department | l | 74 | 2 | 70 | 95% |
| 9 | Department of Justice, United States Marshals | f | 67 | 10 | 37 | 55% |
| 10 | Office of the Director of National Intelligence | f | 67 | 3 | 49 | 73% |
| 11 | U.S. Office of Management and Budget | f | 66 | 2 | 59 | 89% |
| 12 | U.S. Citizenship and Immigration Services | f | 64 | 7 | 35 | 55% |
| 13 | New York State Police | s | 64 | 2 | 62 | 97% |
| 14 | Department of Justice, Office of the Attorney Genera | f | 62 | 8 | 34 | 55% |
| 15 | United States Customs and Border Protection | f | 59 | 6 | 23 | 39% |
| 16 | Boston Police Department | l | 58 | 4 | 41 | 71% |
| 17 | Securities and Exchange Commission | f | 57 | 5 | 47 | 82% |
| 18 | Department of Health and Human Services | f | 56 | 12 | 24 | 43% |
| 19 | National Security Agency | f | 53 | 4 | 38 | 72% |
| 20 | Department of Energy Headquarters | f | 49 | 22 | 8 | 16% |
| 21 | United States Secret Service | f | 47 | 4 | 43 | 91% |
| 22 | Austin Police Department | l | 47 | 4 | 27 | 57% |
| 23 | Los Angeles County Sheriff's Department | l | 46 | 2 | 29 | 63% |
| 24 | Texas Department of Public Safety | s | 45 | 1 | 45 | 100% |
| 25 | St. Louis Metropolitan Police Department | l | 43 | 2 | 26 | 60% |
| 26 | Chicago Police Department | l | 41 | 5 | 33 | 80% |
| 27 | Baltimore Police Department | l | 41 | 4 | 30 | 73% |
| 28 | Indianapolis Metropolitan Police | l | 40 | 1 | 40 | 100% |
| 29 | Jacksonville Sheriff's Office | l | 39 | 1 | 39 | 100% |
| 30 | Tampa Police Department | l | 38 | 1 | 38 | 100% |

## 4. Top 15 agencies by channel count

| # | Agency | Lvl | Channels | Blocked |
|---:|---|:-:|---:|---:|
| 1 | Federal Bureau of Investigation | f | 23 | 1,075 |
| 2 | Department of Energy Headquarters | f | 22 | 49 |
| 3 | Department of Health and Human Services | f | 12 | 56 |
| 4 | Environmental Protection Agency | f | 11 | 90 |
| 5 | Drug Enforcement Administration | f | 11 | 25 |
| 6 | Department of Defense, Office of the Secretary of De | f | 10 | 17 |
| 7 | Department of Justice, United States Marshals | f | 10 | 67 |
| 8 | Department of Commerce | f | 9 | 32 |
| 9 | Department of Homeland Security | f | 8 | 189 |
| 10 | Department of Justice, Executive Office for United S | f | 8 | 29 |
| 11 | Department of Justice, Office of the Attorney Genera | f | 8 | 62 |
| 12 | U.S. Department of State | f | 7 | 337 |
| 13 | U.S. Citizenship and Immigration Services | f | 7 | 64 |
| 14 | Department of Homeland Security Office of Inspector  | f | 7 | 22 |
| 15 | Executive Office for United States Attorneys | f | 6 | 17 |

## 5. Concentration within multi-channel agencies

Would fixing only the single biggest channel per agency be enough? (309 agencies have 2+ channels)

| Metric | Value |
|---|---:|
| Mean share of blocked on the biggest channel | 62.1% |
| Median share | 61.3% |
| Agencies where biggest channel is >=90% of blocked | 19 |
| Agencies where biggest channel is <50% of blocked | 36 |
| Blocked reqs NOT on each agency's biggest channel | 1,979 |

## 6. Migration sizing — tasks produced by each split strategy

| Strategy | Tasks | vs. (3) | Note |
|---|---:|---:|---|
| 1. every error-status AgencyEmail link | 4,562 | 2.0× | Inflated by stale flags (~61% have no recent bounce) |
| 2. addresses with an EmailError in last 24mo | 1,380 | 0.6× | Recent-breakage window; includes channels with no live traffic |
| **3. channels carrying blocked active traffic** | **2,265** | 1.0× | Matches the §3 'active channel' principle |
| 2 ∪ 3 (union) | 2,931 | — | Strategy 3 plus a recent-breakage sweep |

For reference, today's open task count is 3,677.

## 7. Per-channel breakdown — 5 worst agencies

**Federal Bureau of Investigation** — 1,075 blocked across 23 channel(s)

| Channel | Blocked |
|---|---:|
| FOIPAQUESTIONS@fbi.gov | 481 |
| foipaquestions@fbi.gov | 387 |
| FBI.FOIPA.NEGOTIATION@fbi.gov | 49 |
| foipaquestions@ic.fbi.gov | 42 |
| no-reply@foiaonline.gov | 25 |
| oip-noreply@usdoj.gov | 23 |
| David.Sobonya@ic.fbi.gov | 21 |
| OIP-NoReply@usdoj.gov | 19 |
| CRM.FOIA@usdoj.gov | 5 |
| foia@foiaonline.gov | 5 |
| FOIPARequest@ic.fbi.gov | 4 |
| foiparequest@ic.fbi.gov | 2 |
| fbi.foipa.engagement@fbi.gov | 2 |
| FOIA@socom.mil | 1 |
| EOUSA-NoReply@usdoj.gov | 1 |
| FOIASIG.NRC@uscis.dhs.gov | 1 |
| postmaster@usdoj.gov | 1 |
| Douglas.Hibbard@usdoj.gov | 1 |
| admin@foiaonline.gov | 1 |
| FOIA-no-reply@usdoj.gov | 1 |
| notification@pay.gov | 1 |
| FOIPAQuestions@fbi.gov | 1 |
| fbi.foiapa.negotiation@fbi.gov | 1 |

**U.S. Department of State** — 337 blocked across 7 channel(s)

| Channel | Blocked |
|---|---:|
| FOIAStatus@state.gov | 273 |
| A_FOIAacknowledgement@groups.state.gov | 41 |
| WOODKM1@state.gov | 19 |
| DNI-FOIA@dni.gov | 1 |
| BurksAS@state.gov | 1 |
| noreply@mail.foia.state.gov | 1 |
| SilberbergS@state.gov | 1 |

**Department of Homeland Security** — 189 blocked across 8 channel(s)

| Channel | Blocked |
|---|---:|
| FOIA@hq.dhs.gov | 135 |
| noreply@securerelease.us | 28 |
| ICE-FOIA@ice.dhs.gov | 11 |
| donotreply@hq.dhs.gov | 8 |
| foia@foiaonline.gov | 3 |
| no-reply@foiaonline.gov | 2 |
| FOIA.Officer@dot.gov | 1 |
| admin@foiaonline.gov | 1 |

**Seattle Police Department** — 178 blocked across 3 channel(s)

| Channel | Blocked |
|---|---:|
| seattle@mycusthelp.net | 159 |
| spdpdr@seattle.gov | 18 |
| Jennifer.Clark@seattle.gov | 1 |

**Immigration and Customs Enforcement** — 155 blocked across 5 channel(s)

| Channel | Blocked |
|---|---:|
| ICE-FOIA@ice.dhs.gov | 76 |
| wcmmonitoring@dhs.gov | 37 |
| noreply@securerelease.us | 35 |
| donotreply@hq.dhs.gov | 6 |
| FOIA@hq.dhs.gov | 1 |