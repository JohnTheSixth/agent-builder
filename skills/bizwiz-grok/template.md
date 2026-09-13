# BizWiz note template

Follow this structure.

- External URLs: `[text](url)`. `[[wikilinks]]` only for vault notes that
  already exist — do not invent them.
- Cite with inline links. Footnotes (`[^n]`) only when an inline link would
  clutter a table cell or sentence.
- Frontmatter tags have no `#`. Dates are `YYYY-MM-DD`.
- Omit any section that would be empty, except **Coverage** and **Your
  concerns**, which always appear. Prefill every always-source row in
  Coverage even when the status is `Not listed` or `No results`.
- Everything this skill generates below the frontmatter goes inside
  `%% bizwiz:start %%` / `%% bizwiz:end %%` so re-runs can replace it without
  touching the user's own notes.

Verdict callout types: Contact → `success`; Contact with caution → `warning`;
Avoid → `danger`; Insufficient data → `question`.

---

```markdown
---
aliases:
  - <DBA / former names>
tags:
  - business
  - bizwiz
  - <industry-slug>
business: <Legal or trading name>
industry: <industry>
location: <City, ST>
entity-type: <independent | franchise | chain-location | unknown>
website: <https://...>
phone: <number>
x-handle: <@handle or empty>
researched: <YYYY-MM-DD>
verdict: <contact | caution | avoid | insufficient-data>
confidence: <high | medium | low>
weighted-rating: <e.g. 4.3>
total-reviews: <sum across platforms used in the weighted rating>
concerns:
  - <concern 1>
  - <concern 2>
---

# <Business Name>

%% bizwiz:start %%

> [!<success | warning | danger | question>] Verdict: <Contact | Contact with caution | Avoid | Insufficient data> — <High/Medium/Low> confidence
> <2–4 sentences: the bottom line, the main reason, and the single most important thing to know before contacting.>

## At a glance

| | |
|---|---|
| **Weighted rating** | <x.x★ across N reviews on M platforms; add "low volume" when analysis labeled it> |
| **Trend (last 12–24 mo)** | <Improving / Stable / Declining — why> |
| **In business since** | <year> ([source](url)) |
| **License** | <Active #12345, exp. YYYY-MM-DD ([board](url)) / Not required / Not found> |
| **BBB** | <Grade, accredited?, N complaints (3 yr), N unresolved ([profile](url))> |
| **Legal / regulatory** | <None found / summary with links> |

## Identity

- **Legal name:** … · **DBAs / former names:** …
- **Address:** … · **Phone:** … · **Website:** [domain](url)
- **Owner / principals:** … · **Entity:** <independent / franchise / chain-location>
- **X:** [@handle](https://x.com/handle) · **Registration:** <status, formed YYYY> ([SoS record](url))
- **Disambiguation notes:** <similarly named businesses or other locations excluded, and how you told them apart>

## Your concerns

### <Concern 1>
**Evidence strength:** <Strong | Moderate | Weak | No data>
<What the evidence says, with linked examples. Say plainly if nothing addresses it.>

### <Concern 2>
…

## Ratings by platform

| Platform | Rating | Reviews | Most recent | Owner replies | Link | Notes |
|---|---|---|---|---|---|---|
| Google | 4.6★ | 312 | 2026-08 | Most, polite | [profile](url) | Snippets only |
| Yelp | 3.9★ | 88 | 2026-07 | Some | [profile](url) | 41 not recommended |
| X | — | <n public posts sampled> | 2026-09 | Replies from @handle | [search](url) | Native search; not in weighted average |
| … | | | | | | |

## What people praise

- **<Theme>** — <N> mentions across <platforms>, mostly <recent/older>. e.g. [Google review, 2026-05](url), [Reddit thread](url)
- …

## What people complain about

- **<Theme>** — <N> mentions across <platforms>. <Severity note.> e.g. [BBB complaint, 2025-11](url), [Yelp, 2026-02](url)
- …

## Mentions on X

- [@{user}, YYYY-MM-DD](https://x.com/user/status/id) — <one-line gist; note if the business replied>
- …

*(Omit this section if native X search found nothing attributable.)*

## How the business responds

<Owner-response patterns across platforms and on X: speed, tone, whether problems get resolved, any hostile replies. Linked examples.>

> [!warning] Red flags
> - <Flag> — [source](url)
>
> *(Omit this callout if none.)*

> [!info]- Review authenticity signals
> <Bursts, generic reviews, platform gaps (≥1★ spread or glowing Google vs ugly BBB/Reddit), gating, filtered-review counts — or "No notable signals found.">

## Community & news mentions

- <Reddit / Nextdoor / Facebook-group / YouTube / news items that aren't a platform review, with links>

## Before you contact them

- [ ] <Specific thing to ask, verify, or get in writing, derived from findings>
- [ ] <e.g. Confirm license # 12345 is active on the day you sign>
- [ ] …

*(Keep this section on Avoid: conditions that would have to change, or protections to insist on.)*

## Coverage

| Source | Status | Link |
|---|---|---|
| Google | | |
| Yelp | | |
| Facebook | | |
| Reddit | | |
| Trustpilot | | |
| BBB | | |
| X | | |
| Nextdoor | | |
| YouTube | | |
| ConsumerAffairs | | |
| Sitejabber | | |
| PissedConsumer | | |
| Ripoff Report | | |
| Glassdoor / Indeed | | |
| News | | |
| Secretary of State | | |
| License board | | |
| Lawsuits / courts | | |
| <industry source> | | |

**Keywords / queries used:** `…`, `…`

## Research log

- <YYYY-MM-DD> — Initial research. <or: Re-run: rating 4.4→4.1 on Google; 3 new BBB complaints about X; license renewed.>

%% bizwiz:end %%
```
