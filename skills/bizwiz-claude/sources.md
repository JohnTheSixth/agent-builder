# BizWiz source catalog

Substitute from the fingerprint: `<name>` (quoted), `<legal name>`, `<city>`,
`<state>`, `<domain>`, `<phone>`, `<industry>`.

## Search technique (everyone reads this)

**Evidence levels** — tag every rating, count, date, and record:

| Level | Meaning |
|---|---|
| `page` | You fetched the platform's own page or the official record and saw it. |
| `mirror` | You fetched a third-party page that republishes the data (e.g. Birdeye or Yahoo Local showing Google/Yelp ratings, BuildZoom showing license records). Check the address matches; note the newest date — mirrors go stale. |
| `snippet` | Seen only in WebSearch output. WebSearch returns *summaries*, not raw snippets, so a snippet is a lead: fetch the cited URL when you can, and keep the URL with the number. |

**Dates:** `YYYY-MM-DD`; `~YYYY-MM (relative)` for "5 months ago"; `undated`.

**Tool behavior (verified 2026-09):**
- `site:` and `-site:` are unreliable in WebSearch — sometimes ignored, and some
  domains are rejected. Put the platform name in the query as a keyword
  (`"<name>" <city> yelp`) and filter result URLs yourself.
- **Fetch well:** Trustpilot, BBB (profile, `/complaints`, `/customer-reviews`),
  business websites, BuildZoom, mirror listings, most government sites.
- **Blocked:** Yelp (403), Angi/HomeAdvisor (often 403), Indeed (403), X (402),
  Facebook, Nextdoor, Google Maps (login/JS), and Reddit — WebSearch and
  WebFetch both refuse reddit.com, so Reddit content surfaces only indirectly.
- Once a domain blocks you, don't fetch its other pages — look for mirrors or
  snippets instead.
- If WebFetch can't parse a PDF (court filings, AG complaints) but saves it
  locally, `Read` the saved file.

**Efficiency:**
- Combine terms with `OR` instead of running near-duplicate queries.
- **Name variants:** when a source misses, retry at most twice — legal name or
  DBA, then phone or domain. For generic names, never search the name alone.
- **Beat default sort:** on star platforms, also query
  `"<name>" ("1 star" OR "2 star" OR terrible OR worst)` and
  `"<name>" review <current year>`; prefer "newest"/"lowest rated" views.

## Reviews (Reviews subagent)

| Source | How | Capture |
|---|---|---|
| **Google Business** | `"<name>" <city> google reviews`; `"<name>" <address>`. Mirrors: Birdeye, Yahoo Local, Yellow Pages, MapQuest. | No knowledge panel reaches WebSearch, and snippet counts often come from third-party directories that disagree — prefer a fetched mirror. |
| **Yelp** | `"<name>" <city> yelp`; `"<name>" yelp "not currently recommended"` | Blocked, but result titles often show the review count and Yahoo Local often mirrors the rating. Consumer alerts and filtered counts if visible. |
| **Facebook** | `"<name>" <city> facebook reviews` | "% recommend" and count, from snippets. |
| **Trustpilot** | Fetch `trustpilot.com/review/<domain>` | TrustScore (the displayed stars are it, rounded), review count, % breakdown by star, "Claimed profile", "asking for reviews" history, "replied to negative reviews" rate. |
| **BBB** | `"<name>" <city> bbb`; fetch profile, `/complaints`, `/customer-reviews` | Grade, accreditation, complaints 3 yr / 12 mo, types, resolved vs. unresolved, alerts, principals, incorporation date. |
| **BBB Scam Tracker** | Search `bbb.org/scamtracker` by name, phone, website | Reports, separate from complaints. |
| **ConsumerAffairs** | `"<name>" consumeraffairs` | Note "accredited" (paid placement). |
| **Sitejabber** | `"<name>" sitejabber` | Mostly online businesses. |
| **PissedConsumer / Ripoff Report** | `"<name>" pissedconsumer OR ripoffreport` | Negative-skewed and unverified — themes only; corroborate. |
| **Consumers' Checkbook** | `"<name>" checkbook.org` | Survey-based local ratings in major metros; often paywalled. |

## Community (Community subagent)

| Source | How | Capture |
|---|---|---|
| **Reddit** | `"<name>" <city> reddit`; `<city> reddit recommend <industry> "<name>"` | Whatever summaries expose, with thread URL, status `Snippets only`. If nothing surfaces, status `Blocked`, not `No results`. |
| **X / Twitter** | Handle from the website; `"<name>" x.com OR twitter (scam OR complaint OR avoid OR recommend)` | Snippets only. Cite `https://x.com/<user>/status/<id>`. Public replies from the business. |
| **Nextdoor** | `"<name>" nextdoor` | Faves count, recommendation gist. High signal for local services. |
| **Facebook groups** | `"<name>" <city> facebook group recommend` | Recommendation or warning gist. |
| **YouTube** | `"<name>" review youtube` | Common for contractors, auto, e-commerce. |
| **Recommendation threads** | `best <industry> <city>`; `<city> recommend <industry>` | Whether locals name this business when asked whom to hire; up to 3 recurring alternatives, with links — don't research them. |

## Risk & legitimacy (Risk subagent)

| Check | How |
|---|---|
| **Registration** | State Secretary of State entity search (often JS-only); fallback OpenCorporates, BBB incorporation date. Status (active/dissolved), formation date, officers, prior names, related entities. |
| **License** | Industry table licensing column, plus city-level licenses where the trade requires them. Number, status, expiry, discipline. |
| **Insurance, bond, certifications** | Board records sometimes show bond/insurance. Verify certifications on the certifier's locator (manufacturer "certified installer" finders, board-certification lookups). |
| **Courts & bankruptcy** | `"<legal name>" (lawsuit OR "v." OR bankruptcy OR judgment OR lien)`; CourtListener (strong on federal and appellate, thin on state); state/county portals where searchable. Record court, role (plaintiff/defendant), claim, outcome, date. |
| **Regulators** | State Attorney General actions and lawsuit search; `"<name>" ftc.gov`; CFPB; OSHA establishment search (trades); industry regulators in the Industry table. |
| **Recalls & safety** | CPSC / NHTSA / FDA where the business sells or services regulated products. |
| **News** | `"<name>" <city>` news; local TV consumer segments (`"<name>" "on your side" OR investigation`). |
| **Web presence** | Domain age via ICANN lookup (`lookup.icann.org` — RDAP replaced WHOIS); Wayback Machine if the domain or name looks new; storefront vs. virtual office/UPS box; name/address/phone consistency; "permanently closed" on any listing. |
| **Employee reviews** | `"<name>" glassdoor OR indeed` — turnover, pressure-sales culture, unpaid staff, ownership chaos. |

## Industry

Add every matching row. **Industry subagent:** review-site column. **Risk
subagent:** licensing column. Core platforms already in Reviews aren't repeated
here. Unlisted industry: search `best <industry> review sites` and
`<state> <industry> license lookup`, and use the "Unlisted" default concerns.

| Industry | Review sites | Licensing & regulators | Default concerns |
|---|---|---|---|
| **Home services / contractors** | Angi/HomeAdvisor (one source), Thumbtack, Houzz, Porch, BuildZoom (permits) | State/city contractor license, manufacturer certification locators, OSHA | Shows up on time; quote vs. final invoice; workmanship/callbacks; warranty honored |
| **Movers** | Angi/HomeAdvisor | FMCSA SAFER company snapshot (USDOT/MC number), FMCSA household-goods complaint search, fmcsa.dot.gov/protect-your-move | Price changes / hostage loads; damage claims; arrival window |
| **Restaurants / hospitality / lodging** | TripAdvisor, OpenTable, Resy, delivery-app ratings; Booking.com/Expedia | Local health-department inspections | Food/room quality; cleanliness; wait/service; billing surprises |
| **Medical / dental / therapy / senior care** | Healthgrades, Zocdoc, Vitals, RateMDs (paid-removal allegations exist), Psychology Today | State medical/dental board, CMS Care Compare (facilities, nursing homes, home health), HHS-OIG exclusions list, Leapfrog Hospital Safety Grade | Billing surprises; outcomes & safety; wait times; upselling |
| **Legal** | Avvo, Martindale-Hubbell, Justia | State bar lookup (discipline) | Communication; fees vs. estimate; outcomes; professionalism |
| **Financial / insurance / lending** | — | CFPB complaint database, FINRA BrokerCheck, SEC IAPD, NMLS Consumer Access, state insurance dept., NAIC Consumer Information Source | Hidden fees; claims handling; pressure sales; account errors |
| **Auto sales / repair** | DealerRater, Cars.com, Edmunds, CarGurus, RepairPal | State dealer license board, state AG auto complaints, NHTSA recalls | Honest diagnosis; price vs. quote; add-on/finance pressure; comebacks |
| **Real estate / property management** | Zillow, Realtor.com, ApartmentRatings, Apartments.com | State real-estate commission | Responsiveness; deposits & fees; maintenance; disclosure |
| **Software / SaaS / B2B** | G2, Capterra, TrustRadius, Gartner Peer Insights, Hacker News | Status-page history, data-breach news | Support; uptime; billing & cancellation; lock-in |
| **E-commerce / consumer products** | Amazon seller feedback, app-store reviews, ScamAdviser (can over-score new sites) | CPSC recalls, FTC actions | Shipping; returns/refunds; product as described; scam reports |
| **Gyms / salons / personal services** | ClassPass (in-app, snippets only) | State cosmetology/barber board | Contract cancellation; billing after cancel; hygiene; upselling |
| **Childcare / education** | Care.com, Winnie, GreatSchools, Niche | State childcare licensing inspection reports | Safety & incidents; licensing; staffing/ratios; communication |
| **Pet services** | Rover | State veterinary board | Animal handling & safety; pricing; emergencies |
| **Travel / events / weddings** | TripAdvisor, The Knot, WeddingWire, Viator/GetYourGuide | Seller-of-travel registration (states that require it) | Hidden fees; delivered as promised; no-shows; refunds |
| **Unlisted** | *(search for equivalents)* | *(search for equivalents)* | Quality of work; price honesty; communication; standing behind problems |

**Outside the US**, swap in local equivalents — e.g. UK: Companies House,
Which? Trusted Traders, Checkatrade, TrustATrader; Canada: provincial
registries, HomeStars, BBB; Australia: ABN Lookup/ASIC, ProductReview.com.au,
hipages. Otherwise search `<country> <industry> review sites` and
`<country> business registry`.

## Intent queries (parent)

```
"<name>" <city> reviews
"<name>" complaints OR "consumer alert" OR warning
"<name>" scam OR fraud OR ripoff
"<name>" lawsuit OR sued
"<name>" "never again" OR "stay away" OR avoid
"<name>" recommend OR recommended
"<legal name>" <state>
"<phone>"
"<domain>"   (keep only results not on the business's own site)
```

Per concern, 2–3 paraphrases — e.g. "hidden fees" →
`"<name>" ("hidden fees" OR "extra charge" OR "more than the quote")`.

## Protections & recourse (parent, while writing)

Search `<state> <industry> consumer protection law` for rules that apply to
this purchase — e.g. home-improvement deposit caps and written-contract
requirements, gym-contract cancellation rights, movers' binding estimates.
General protections, always applicable:
- The FTC Cooling-Off Rule (3-day cancellation for many in-home sales).
- Paying by credit card preserves chargeback rights; cash, wire, Zelle, and
  crypto don't.
- Where to complain if it goes wrong: licensing board, state AG, BBB, and the
  industry regulator (CFPB, FMCSA, etc.).
