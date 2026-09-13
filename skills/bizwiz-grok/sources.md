# BizWiz source catalog (Grok)

Substitute `<name>` (quoted), `<city>` / `<state>`, `<handle>`, `<domain>`,
`<legal name>`, `<owner>` from the fingerprint.

Prefer `web_search` with `num_results` 15–20 for discovery, then `web_fetch`
/ `open_page` on surviving profile URLs. Use `open_page_with_find` when you
already have a URL and need a rating, count, or complaint total from a noisy
page.

**Name variants.** Search the trading name, legal name, and each DBA. If a
source misses, retry with phone and with domain. If city+name misses, retry
name+state, then name alone (and re-apply the fingerprint before keeping a hit).

**Star-rating platforms.** Do not trust default sort. Also search
`"<name>" "1 star"`, `"<name>" "2 star"`, and a recency query
(`"<name>" review 2026` / current year). Sample newest and lowest, not only
"recommended."

## Core review platforms (always)

| Source | How | Access |
|---|---|---|
| **Google Business / Maps** | `web_search`: `"<name>" <city> reviews`; `"<name>" <address>`; `site:google.com/maps "<name>"`. | Maps pages rarely fetch. Snippets / knowledge-panel text usually carry rating + count. Mark snippets-only when you never saw the page. |
| **Yelp** | `site:yelp.com "<name>" <city>`; fetch `yelp.com/biz/<slug>`. Also `site:yelp.com "<name>" "not currently recommended"`. | Often 403s. Fall back to snippets. If fetched, capture Consumer Alert banners and filtered / "not recommended" counts. |
| **Facebook** | `site:facebook.com "<name>" <city> reviews`. Also `"<name>" <city> facebook group`. | Login wall. Snippets may show "X% recommend (N reviews)". That % is **not** a 5-star rating — do not fold it into the weighted average. |
| **Reddit** | `site:reddit.com "<name>"`; `site:reddit.com "<name>" <city>`; `site:reddit.com/r/<city> <industry> recommend`. Fetch promising threads; try `old.reddit.com/...` or append `.json` if `www` fails. | Local city subs are high-signal. |
| **Trustpilot** | `site:trustpilot.com "<name>"`; fetch `trustpilot.com/review/<domain>`. | Usually fetchable. Note TrustScore vs star average, Claimed, "Asks for reviews", reply-to-negative rate. |
| **BBB** | `site:bbb.org "<name>" <city>`; fetch the profile, then `/complaints` and `/customer-reviews`. | Usually fetchable. Capture accreditation, letter grade, complaint totals (3 yr / 12 mo), types, resolved vs unresolved, alerts. Letter grade ≠ customer sentiment and is **not** a 5-star rating. |
| **X / Twitter** | **Native tools, not web search.** X playbook below. | Grok can read public posts. Web `site:x.com` is fallback only. |

## X playbook

1. `x_user_search` on `<name>` (and city if the name is generic). Confirm the
   handle against the fingerprint (bio, location, linked website). Record
   **no official handle** if nothing matches — still search the name.
2. `x_keyword_search` `mode: Latest`, `limit: 10`:
   - `"<name>" (review OR reviews OR recommend OR recommended OR avoid OR scam OR complaint OR "never again")`
   - `@<handle> OR to:<handle> (scam OR complaint OR terrible OR recommend OR thanks)`
   - `from:<handle>` — how they talk to customers
3. `x_semantic_search`: "customer experiences with `<name>` in `<city>`";
   "should I hire `<name>`".
4. `x_thread_fetch` on the 2–5 highest-signal posts (complaints with
   engagement, or a reply from the business).
5. Link every cited post as `https://x.com/<user>/status/<id>`.

If native X search is empty, fall back to `web_search` `site:x.com "<name>"`
and mark coverage Partial.

## Broad complaint / review aggregators (always check)

| Source | Query / notes |
|---|---|
| **Nextdoor** | `site:nextdoor.com "<name>"`. High signal for local services; usually login-walled — snippets only. |
| **YouTube** | `site:youtube.com "<name>" <city> review`. Video reviews are common for contractors and auto. |
| **ConsumerAffairs** | `site:consumeraffairs.com "<name>"`. Paid placement exists; note if "accredited". |
| **Sitejabber** | `site:sitejabber.com "<name>"`. Mostly online / e-commerce. |
| **PissedConsumer** | `site:pissedconsumer.com "<name>"`. Negative-skewed by design; themes, not ratings. |
| **Ripoff Report** | `site:ripoffreport.com "<name>"`. Unverified, unremovable, sometimes competitor-abused — corroborate. |
| **Glassdoor / Indeed** | `site:glassdoor.com "<name>"`, `site:indeed.com/cmp "<name>"`. Employee reviews leak into customer experience (turnover, pressure-sales, ownership). |

## Industry-specific sources

Add every matching row. If the industry is not listed, search
`<industry> reviews site` and `best <industry> review websites` for the
equivalents, then use those.

| Industry | Sources |
|---|---|
| **Home services / contractors** (roofing, HVAC, plumbing, remodeling, landscaping, movers) | Angi (Angie's List), HomeAdvisor, Thumbtack, Houzz, Porch, BuildZoom (permits + license history), Nextdoor. Movers: FMCSA SAFER / protectmymove.gov (USDOT/MC number, complaints). |
| **Restaurants / food / hospitality** | TripAdvisor, OpenTable, Resy, DoorDash/Uber Eats ratings, local health-department inspection records; Booking.com/Expedia/Hotels.com for lodging. |
| **Medical / dental / therapy** | Healthgrades, Zocdoc, Vitals, WebMD Care, RateMDs, state medical/dental board license lookup (discipline), CMS Care Compare for facilities, Psychology Today for therapists. |
| **Legal** | Avvo, Martindale-Hubbell, Justia, Lawyers.com, state bar attorney lookup (discipline history). |
| **Financial / insurance / lending** | CFPB Consumer Complaint Database, FINRA BrokerCheck, SEC IAPD, NMLS Consumer Access, state insurance department complaint data, NAIC complaint index. |
| **Auto sales / repair** | DealerRater, Cars.com, Edmunds, CarGurus, RepairPal, state AG auto complaints. |
| **Real estate / property mgmt** | Zillow agent reviews, Realtor.com, state real-estate commission license lookup; property managers: ApartmentRatings, Apartments.com reviews. |
| **Software / SaaS / B2B** | G2, Capterra, TrustRadius, GetApp, Gartner Peer Insights, Hacker News (`site:news.ycombinator.com`), status-page / outage history. |
| **E-commerce / consumer products** | Amazon seller feedback, Sitejabber, ScamAdviser / domain age (WHOIS), app-store reviews, `r/<product category>`. |
| **Childcare / education** | State childcare licensing inspection reports, Care.com, Winnie, GreatSchools, Niche. |
| **Pet services** | Rover, local vet board lookup, Yelp/Google (primary for this category). |
| **Travel / events / wedding** | TripAdvisor, The Knot, WeddingWire, Viator/GetYourGuide. |

## Default concerns (when the user gave none)

Use up to 4. If the user gave concerns, answer those first; add an industry
default only when it is clearly material and they didn't already cover it.

| Industry | Defaults |
|---|---|
| **Home services / contractors** | Shows up on time; quote vs final invoice; workmanship / callbacks; warranty honored |
| **Restaurants / food / hospitality** | Food quality; wait times; cleanliness / health; service |
| **Medical / dental / therapy** | Billing surprises; wait times; outcome / bedside manner; upselling |
| **Legal** | Communication; fees vs estimate; outcome; professionalism |
| **Financial / insurance / lending** | Fees; claims handling; pressure-sales; account errors |
| **Auto sales / repair** | Honesty of diagnosis; price vs quote; comebacks; title / add-on pressure |
| **Real estate / property mgmt** | Responsiveness; pressure; disclosure; fees / deposits |
| **Software / SaaS / B2B** | Support quality; uptime; billing surprises; lock-in |
| **E-commerce / consumer products** | Shipping; returns; product-as-described; scam reports |
| **Childcare / education** | Safety; licensing; ratios / staffing; communication |
| **Pet services** | Animal handling; pricing; after-hours / emergencies |
| **Travel / events / wedding** | Hidden fees; delivered on promises; vendor no-shows |
| **Unlisted** | Quality of work; price honesty; communication; standing behind problems |

## Risk & legitimacy (always)

| Check | How |
|---|---|
| **Business registration** | State Secretary of State entity search: status (active/dissolved/forfeited), formation date, registered agent, officers, prior names. |
| **Professional license** | State licensing board for the trade. Required? Active? Expiration? Discipline? Bonded/insured claims verifiable? |
| **Lawsuits / court records** | `"<legal name>" lawsuit`, `"<legal name>" v.`, CourtListener (`site:courtlistener.com`), state/county portals. Include owner/principal names. |
| **Regulators / enforcement** | State AG press releases & complaints, FTC (`site:ftc.gov "<name>"`), CFPB, OSHA establishment search (trades), EPA ECHO (industrial). |
| **News** | `"<name>" <city>` news; local TV consumer-investigator segments (`"<city> 7 on your side" "<name>"`). |
| **Web presence** | Domain age (WHOIS via search); real storefront vs virtual office/UPS box; NAP (name/address/phone) consistency across listings. If the domain is young or the name looks new, check Wayback and search former names independently. |

## Intent queries (always, in addition to per-source)

```
"<name>" <city> reviews
"<name>" complaints
"<name>" scam OR fraud OR ripoff
"<name>" lawsuit OR sued
"<name>" warning OR "consumer alert"
"<name>" "never again" OR "stay away" OR "avoid"
"<name>" recommend OR recommended
best <industry> <city>
"<legal name>" <state>
"<owner name>" "<name>"
"<phone number>"
"<domain>" -site:<domain>
```

`best <industry> <city>` is a recommendation-thread check: does this business
show up when locals ask whom to hire — not just on its own review profiles?

For each user concern, add 2–3 paraphrases, e.g. concern "hidden fees" →
`"<name>" "hidden fees"`, `"<name>" "extra charge"`, `"<name>" "higher than quote"`.
