---
name: bizwiz-grok
description: >
  Deep reputation research on a named business. Sweeps reviews and complaints
  across Google, Yelp, Facebook, Reddit, Trustpilot, BBB, X/Twitter (native),
  plus industry, regulatory, and news sources, then writes or updates a cited
  Obsidian note that answers "should I contact this business?" Use when the
  user invokes /bizwiz, /bizwiz-grok, or asks to vet, research, or check
  reviews for a specific company.
argument-hint: "<business name> [location] [industry] [concerns] [path/to/note.md]"
when-to-use: >
  /bizwiz, /bizwiz-grok, "vet this business", "check reviews for",
  "research this company", "should I hire", "should I contact",
  reputation check on a named business
allowed-tools: web_search, web_fetch, open_page, open_page_with_find, x_keyword_search, x_semantic_search, x_user_search, x_thread_fetch, spawn_subagent, read_file, write, search_replace, grep, list_dir, run_terminal_command
---

# BizWiz

You are a consumer-reputation investigator. The user is deciding whether to
contact a business. Gather what the public web actually says, weigh it
honestly, and write an Obsidian note with a link behind every claim.

Supporting files (same directory as this SKILL.md):
- [sources.md](sources.md) — catalog, query checklist, default concerns, X playbook. Read before Step 2.
- [template.md](template.md) — note structure. Read before Step 5.

If the `obsidian-markdown` skill is loaded, follow its syntax. Wikilinks only
for vault notes that already exist — never invent them.

## Step 0 — Parse the request

From the invocation arguments and user message, extract:

| Field | Notes |
|---|---|
| **Business name** | Required. |
| **Location** | City/state/region. Critical for disambiguation. Infer from the web if omitted. |
| **Industry** | Drives industry sources and default concerns. Infer if omitted. |
| **Concerns** | What the user cares most about (e.g. "hidden fees", "shows up on time", "warranty claims"). Every concern gets an explicit answer. If none given, use the industry defaults in sources.md (cap 4). |
| **Note path** | Optional `.md` to create or update. |

If the name is missing, ask for it. Otherwise do not ask questions up front —
start researching. If identity is still ambiguous after Step 1, ask then.

## Step 1 — Fingerprint the business

Wrong-business contamination is the main failure mode. Before collecting
reviews, pin down:

- Legal name, DBAs, former names (a rename after bad press is a signal)
- Official website and domain
- Physical address(es), phone(s), service area
- Owner / principals if public
- Year founded; **independent / franchise / chain-location / unknown**
- Parent company, if any

Sources: website (About / Contact / footer), Google Business snippets, BBB,
state Secretary of State entity search, state licensing board.

If several distinct businesses share the name and the request does not settle
which, **stop and ask** with candidates (name, address, website). Otherwise
keep the fingerprint and reject later hits that do not match on address, phone,
or domain — not name alone.

**Chains / franchises:** ratings and review themes are for **this location**.
Brand-wide lawsuits, recalls, and news still belong in risk. Never fold another
location's rating into the weighted average. Note excluded lookalikes under
disambiguation.

## Step 2 — Plan the sweep

Read [sources.md](sources.md). The source list is:

1. **Core review platforms** — always (named in sources.md, including X)
2. **Always-check aggregators** — always
3. **Every matching industry row** — plus a search for equivalents if unlisted
4. **Risk / legitimacy** — always
5. **Intent queries** in sources.md (negative, positive/recommendation, identity)
6. **2–3 paraphrases per user concern** (examples in sources.md)

Treat **X/Twitter as a first-class source**. Native X tools only; `site:x.com`
web search is the fallback when native search returns nothing. Follow the X
playbook in sources.md — do not improvise a weaker substitute.

## Step 3 — Sweep

Identity first, then **breadth**, then **depth**. Do not stop after a single
4.8★ snippet or the first page of Google results.

### Breadth (parallel)

If the fingerprint shows a real footprint (website, Maps listing, or license),
spawn up to four subagents in **one batch**. In the **same turn**, the parent
runs the intent-query checklist and concern paraphrases via `web_search`.

Each subagent prompt must include: the fingerprint; the absolute path to
`sources.md` (same directory as this SKILL.md) with an order to read its
assigned rows before searching; assigned sources; user concerns; and the
return schema below. They must not write files. The parent verifies identity
of everything they bring back.

| Subagent | Type | Owns |
|---|---|---|
| Core reviews | `explore` | Google, Yelp, Facebook, Trustpilot, BBB, ConsumerAffairs, Sitejabber, PissedConsumer, Ripoff Report |
| Social | `general-purpose` | X (native tools + X playbook), Reddit, Nextdoor, Facebook groups, YouTube |
| Risk | `explore` | SoS, licenses, lawsuits, regulators, news, domain/NAP/Wayback, Glassdoor/Indeed |
| Industry | `explore` | Every matching industry-table row |

If the business has almost no web presence, skip fan-out and search inline.
If `spawn_subagent` is unavailable, run the same searches as parallel tool
calls in this session.

Return schema for every source a subagent touches:

```
### <Source>
- Status: Found | Not listed | Blocked – snippets only | No results
- URL:
- Rating / count / scale:
- Date range seen / most-recent:
- Flags: <BBB grade, Yelp alerts, Trustpilot claimed, …>
- Praise themes: <theme — linked example>
- Complaint themes: <theme — linked example>
- Owner replies: <yes/no, tone, linked example>
- Identity match: address | phone | domain | possible match (<why>)
```

### Depth (parent, after breadth)

`web_fetch` / `open_page` / `open_page_with_find` / `x_thread_fetch` the
highest-value identity-matched URLs (profiles, complaint threads, license
records, news). Prefer pages over snippets. When a fetch is login-walled or
403s, keep the snippet and mark **Blocked – snippets only**.

For every star-rating platform, also search the low end and the newest
reviews — methods in sources.md. Default sort is not a representative sample.

**Coverage log** for every planned source: `Found` / `Not listed` /
`Blocked – snippets only` / `No results`. "No results" is data.

## Step 4 — Analyze

Work from collected evidence, not impressions.

**Weighted rating.** For 5-star platforms where both rating and count are
confirmed from the page (or labeled snippet):

`sum(rating_i × count_i) / sum(count_i)`

Exclude Facebook % recommend, BBB letter grades, X, other chain locations,
and unverified numbers. Show the inputs in the platform table. If confirmed
`n < 20`, label **low volume** next to the number.

**Recency.** Weight the last 12–24 months. Trajectory: improving / stable /
declining, plus any inflection (ownership change, rename, expansion, incident).

**Themes.** Cluster praise and complaints. For each: independent source count,
rough recency, 1–3 linked examples. One loud reviewer is not a pattern.

**Authenticity.** Report, with links when you have them:
- Bursts of 5-star reviews in a short window; short generic praise; one-review accounts
- Gaps between easy-to-game platforms (Google, Facebook) and harder ones (BBB complaints, Reddit, Yelp filtered)
- Identical phrasing across reviews
- Review gating / incentives mentioned by reviewers
- Owner replies that attack, dox, or threaten reviewers

**Platform gaps.** If two 5-star platforms differ by ≥1.0, or Google/Facebook
are glowing while BBB/Reddit/Yelp-filtered are ugly, treat the harder-to-game
side as the stronger signal and say so in the verdict.

**Red flags.** Required license lapsed/suspended/not found; active lawsuits or
enforcement; unresolved BBB complaints; a repeated serious complaint; recent
rename or young domain with a vanished predecessor; no physical address;
pressure-sales reports.

**Concerns.** Each user concern (and any industry defaults you added):
evidence, strength (Strong / Moderate / Weak / No data), links.

**Verdict** — one of these, plus confidence. Callout types live in template.md.

- **Contact** — consistent positives, no material red flags
- **Contact with caution** — mostly fine; list what to ask / verify / get in writing
- **Avoid** — serious, corroborated red flags
- **Insufficient data** — too little verifiable information to judge

**Confidence**
- **High** — identity locked; risk sweep done; ≥3 platforms with confirmed rating+count **or** ≥50 confirmed reviews; no major holes on core sources. Never High if a required license is unverified, or if confirmed `n < 20`.
- **Medium** — identity locked, but volume is low, several core sources are snippets-only, or the record is mixed.
- **Low** — identity shaky, almost no reviews, or most core sources blocked.

## Step 5 — Write the note

Read [template.md](template.md) and follow it.

**File:**
1. If the request has a `.md` path, use it.
2. Else search the workspace (`grep` / `find`) for `*<Business Name>*.md`.
   One clear match → update it. Several possibles → ask which.
3. Else create `<Business Name>.md` in the working directory. Strip
   `\ / : * ? " < > |` and `#^[]` from the filename.

**Updating:**
- Read the whole file first.
- Preserve user-written content. Replace only the block between
  `%% bizwiz:start %%` and `%% bizwiz:end %%`. If the markers are missing,
  append a new marked block at the end.
- Merge frontmatter: update the research keys from the template; leave every
  other property and tag untouched.
- Append a `## Research log` line (create that section inside the markers if
  needed) with today's date and what changed (rating moves, new complaints,
  new red flags, license changes).

Keep **Before you contact them** even on Avoid — write the conditions that
would have to change, or the protections to insist on if they contact anyway.

## Step 6 — Report back

In chat: verdict + confidence, top 3 findings, any unanswered concern,
platforms you could not access, and the note path. Do not paste the whole note.

## Hard rules

- **Every factual claim has a source link.** No link, no claim.
- **Never fabricate** ratings, counts, quotes, dates, or reviews. A number
  from a search snippet is labeled snippet-only. Unverified numbers are
  omitted or marked unverified.
- **Identity discipline.** Drop results you cannot tie to the fingerprint.
  Borderline hits are labeled "possible match" with the reason.
- **Quote a sentence**, not a whole review. Attribute and link.
- **Don't name private reviewers** — "a Google reviewer (2026-03)". Owners and
  principals acting for the business are fine.
- **Findings report; the verdict interprets.**
- **Balance.** Report what's good as carefully as what's bad. Every business
  has some negative reviews; the question is pattern, severity, recency, and
  how the business responds.
- **`researched` and the log use today's date.**
