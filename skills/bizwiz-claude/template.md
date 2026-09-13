# BizWiz note template

**Formatting rules**
- External URLs use `[text](url)`. `[[wikilinks]]` only for notes that already
  exist in the vault — never invent them.
- Cite inline; use footnotes (`[^n]`) only where a link would clutter a table
  cell. Every review example carries a date in the sources.md date format.
- Frontmatter tags have no `#`. Unknown frontmatter values are left empty.
- Everything below the H1 goes between `%% bizwiz:start %%` and
  `%% bizwiz:end %%`.
- Sections marked *(optional)* — and the Red flags callout — are omitted when
  empty. All others always appear; write "None found" or "Not visible on
  accessible pages" rather than dropping them.
- Don't repeat content across sections; link instead (`[[#Your concerns]]`).
- `<angle brackets>` are placeholders. Never carry placeholder text or example
  values into a note.
- Verdict callout type: Contact → `success`; Contact with caution → `warning`;
  Avoid → `danger`; Insufficient data → `question`.
- On **Avoid**, "Before you contact them" lists the conditions that would have
  to change, or the protections to insist on if contacting anyway.

---

```markdown
---
aliases:
  - <DBA / former names>
tags:
  - business
  - bizwiz
  - <industry-slug>
business: <legal or trading name>
industry: <industry>
location: <City, ST>
entity-type: <independent | franchise | chain-location | lead-gen-broker | unknown>
website: <url>
phone: <number>
researched: <YYYY-MM-DD>
verdict: <contact | caution | avoid | insufficient-data>
confidence: <high | medium | low>
weighted-rating: <number, or empty if no verified rating>
total-reviews: <reviews behind weighted-rating>
license-status: <active | expired | suspended | not-required | not-found | mirror-only | unverified>
concerns:
  - <concern>
---

# <Business Name>

%% bizwiz:start %%

> [!<type>] Verdict: <Contact | Contact with caution | Avoid | Insufficient data> — <High | Medium | Low> confidence
> <2–4 sentences: the bottom line, the main reason, and the single most important thing to know before contacting.>
>
> **Would raise confidence:** <the one or two checks that would most change or firm up this call>

## At a glance

| | |
|---|---|
| **Weighted rating** | <x.x★ across <review count> reviews on <platform count> platforms; "low volume" if under 20 — or "No verified rating"> |
| **Trend (12–24 mo)** | <Improving / Stable / Declining / Not enough dated reviews — why> |
| **In business since** | <year> ([source](<url>)) |
| **License** | <status, number, expiry, evidence level ([source](<url>))> |
| **Insurance / bond / certifications** | <verified / claimed only / not found ([source](<url>))> |
| **BBB** | <grade; accredited (paid) or not; complaints (3 yr), unresolved ([profile](<url>))> |
| **Legal / regulatory / financial** | <None found — or summary with role, outcome, date, links> |
| **Service area & practical fit** *(optional)* | <service area, insurance networks, booking lead time, response rate> |

## Your concerns

### <Concern>
**Evidence:** <Strong | Moderate | Weak | No data>
<What the evidence says, with dated links. Say plainly if nothing addresses it.>

## Ratings by platform

| Platform | Rating | Reviews | Newest | Level | In avg | Notes |
|---|---|---|---|---|---|---|
| [<platform>](<url>) | <rating or —> | <count or unknown> | <date> | <page / mirror / snippet> | <yes / no> | <filtered counts, labels, conflicts, why excluded> |

## What people praise

- **<Theme>** — <N> of <reviews read> reviews read, across <platforms>, mostly <recent / older>. e.g. [<platform>, <date>](<url>)

## What people complain about

- **<Theme>** — <N> of <reviews read> reviews read, across <platforms>. <Severity.> e.g. [<platform>, <date>](<url>)

## Money & terms *(optional)*

- **Price level:** <published prices, $-indicators, amounts reviewers cite — linked>
- **Deposits / payment:** <policy or reports — linked>
- **Contracts, cancellation, refunds:** <published policy + reports — linked>
- **Warranty:** <stated terms vs. whether it's honored — linked>

## How the business responds

<Owner-reply patterns across platforms and social: speed, tone, whether problems get fixed, any hostile replies — linked. Or "No owner replies visible on accessible pages.">

> [!danger] Red flags
> - **<Serious | Moderate>:** <flag> — [source](<url>)

> [!info]- Review authenticity signals
> <Bursts, generic praise, platform gaps and whether they met the ≥5-recent-items bar, gating, filtered counts — or "No notable signals found.">

## Community, social & news *(optional)*

- [<source>, <date>](<url>) — <one-line gist; note if the business replied>

## Alternatives locals mention *(optional)*

- <Business> — named in [<thread>](<url>) for <reason>. *Not researched.*

## Before you contact them

- [ ] <Specific thing to ask, verify, or get in writing, derived from the findings — including any unverified items>

**Your protections:** <applicable consumer-protection rules, payment-method advice, and where to complain — linked>

## Identity

- **Legal name:** <…> · **DBAs / former names:** <…> · **Parent company:** <…>
- **Address:** <…> · **Phone:** <…> · **Website:** [<domain>](<url>)
- **Owner / principals:** <…> · **Entity:** <…> · **Work done by:** <employees / subcontractors / unknown>
- **Social:** [<@handle>](<url>)
- **Registration:** <status, formed YYYY, evidence level> ([record](<url>))
- **Disambiguation:** <similar names or other locations excluded, and how they were told apart>

## Coverage

Status: `Found` · `Snippets only` · `Blocked` · `Not listed` · `No results` · `Not searched`

| Section | Source | Status | Link |
|---|---|---|---|
| Reviews | Google (incl. mirrors) | | |
| Reviews | Yelp | | |
| Reviews | Facebook | | |
| Reviews | Trustpilot | | |
| Reviews | BBB / Scam Tracker | | |
| Reviews | ConsumerAffairs / Sitejabber | | |
| Reviews | PissedConsumer / Ripoff Report | | |
| Reviews | Consumers' Checkbook | | |
| Community | Reddit | | |
| Community | X | | |
| Community | Nextdoor / Facebook groups | | |
| Community | YouTube | | |
| Community | Recommendation threads | | |
| Risk | Registration | | |
| Risk | License | | |
| Risk | Insurance / certifications | | |
| Risk | Courts & bankruptcy | | |
| Risk | Regulators & recalls | | |
| Risk | News | | |
| Risk | Web presence | | |
| Risk | Employee reviews | | |
| Industry | <each industry source> | | |

> [!example]- Queries used
> `<query>` · `<query>`

## Research log

- <YYYY-MM-DD> — <Initial research | Quick run | Re-run: what changed since last entry>

%% bizwiz:end %%
```
