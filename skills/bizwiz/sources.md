# BizWiz source catalog

Substitute from the fingerprint: `<name>` (quoted), `<legal name>`, `<city>`,
`<state>`, `<address>`, `<domain>`, `<phone>`, `<handle>`, `<owner>`,
`<industry>`.

## Search technique (everyone reads this)

**Evidence levels.** Tag every rating, count, date, and record with one of these:

| Level | Meaning |
|---|---|
| `page` | You fetched the platform's own page or the official record and saw the value yourself. |
| `mirror` | You fetched a third-party page that republishes the data (e.g. Birdeye or Yahoo Local showing Google/Yelp ratings, BuildZoom showing license records). Check that the address matches and note the newest date, since mirrors go stale. |
| `snippet` | Seen only in search-result text. Many search tools return model-written *summaries* rather than raw page text, and these can be wrong or mix businesses together. A snippet is a lead: fetch the cited URL when you can, and keep the URL with the number. |

**Dates:** use `YYYY-MM-DD`, `~YYYY-MM (relative)` for "5 months ago", or `undated`.

**Tool behavior.** Access varies by harness and changes over time, so trust
what actually happens over what this list predicts.
- **Search operators** (`site:`, `-site:`, `OR`, quotes) work in some search
  tools and are ignored or rejected in others. Try `site:` once. If the
  results come back off-domain or empty, put the platform name in the query
  as a keyword instead (`"<name>" <city> yelp`) and filter the result URLs
  yourself.
- **Usually fetchable:** Trustpilot, BBB (profile, `/complaints`,
  `/customer-reviews`), business websites, BuildZoom, mirror listings, most
  government sites.
- **Often blocked** (403, login wall, JavaScript-only, or refused by the tool):
  Yelp, Angi/HomeAdvisor, Indeed, Facebook, Nextdoor, Google Maps, X (without
  native X tools), and Reddit. For Reddit, try `old.reddit.com/...` or append
  `.json` to the thread URL once. If both fail, Reddit content only surfaces
  through search results.
- Once a domain blocks you, don't fetch its other pages. Look for mirrors or
  snippets instead.
- **PDFs** (court filings, AG complaints): if the fetch tool can't parse one
  but saves it locally, read the saved file. If you can't read it at all, cite
  it as `snippet`.
- **Noisy pages:** if your tool can search within a fetched page, use it to
  pull a rating, count, or complaint total instead of reading the whole page.

**Efficiency:**
- Combine terms with `OR` instead of running near-duplicate queries, if the
  search tool honors `OR`.
- Ask for 10–20 results per query when the tool lets you set a count.
- **Name variants:** when a source misses, retry at most twice: first with the
  legal name or DBA, then with the phone or domain. For a distinctive name you
  may then try name + state. For a generic name, never search the name alone.
  Re-apply the fingerprint before keeping any hit.
- **Beat default sort:** on star platforms, also query
  `"<name>" ("1 star" OR "2 star" OR terrible OR worst)` and
  `"<name>" review <current year>`, and prefer "newest" or "lowest rated" views.

## Reviews (Reviews workstream)

| Source | How | Capture |
|---|---|---|
| **Google Business** | `"<name>" <city> google reviews`; `"<name>" <address>`. Mirrors: Birdeye, Yahoo Local, Yellow Pages, MapQuest. | Maps pages rarely fetch, and snippet counts often come from third-party directories that disagree with each other. Prefer a fetched mirror. |
| **Yelp** | `"<name>" <city> yelp`; `"<name>" yelp "not currently recommended"`; fetch `yelp.com/biz/<slug>` once. | If the page is blocked, result titles often show the review count and Yahoo Local often mirrors the rating. Capture consumer alerts and filtered counts if visible. |
| **Facebook** | `"<name>" <city> facebook reviews` | "% recommend" and count, from snippets. This is not a 5-star rating. |
| **Trustpilot** | Fetch `trustpilot.com/review/<domain>` | TrustScore (the displayed stars are the TrustScore, rounded), review count, % breakdown by star, "Claimed profile", "asking for reviews" history, rate of replies to negative reviews. |
| **BBB** | `"<name>" <city> bbb`; fetch the profile, `/complaints`, and `/customer-reviews` | Grade, accreditation, complaints (3 yr / 12 mo), complaint types, resolved vs. unresolved, alerts, principals, incorporation date. The letter grade is not customer sentiment. |
| **BBB Scam Tracker** | Search `bbb.org/scamtracker` by name, phone, and website | Reports, which are separate from complaints. |
| **ConsumerAffairs** | `"<name>" consumeraffairs` | Note "accredited" status, which is paid placement. |
| **Sitejabber** | `"<name>" sitejabber` | Mostly online businesses. |
| **PissedConsumer / Ripoff Report** | `"<name>" pissedconsumer OR ripoffreport` | Negative-skewed, unverified, unremovable, and sometimes abused by competitors. Use themes only, and corroborate them. |
| **Consumers' Checkbook** | `"<name>" checkbook.org` | Survey-based local ratings in major metros. Often paywalled. |

## Community (Community workstream)

| Source | How | Capture |
|---|---|---|
| **Reddit** | `"<name>" <city> reddit`; `"<name>" reddit`; `<city> reddit recommend <industry> "<name>"`. Fetch promising threads (see Tool behavior). | City subreddits are high-signal. If you saw content only in search results, the status is `Snippets only`. If nothing surfaces because Reddit was unreachable, the status is `Blocked`, not `No results`. |
| **X / Twitter** | Use native X search if you have it (X playbook below). Otherwise search the web: `"<name>" x.com OR twitter (scam OR complaint OR avoid OR recommend)`. | Cite posts as `https://x.com/<user>/status/<id>`. Capture public replies from the business. |
| **Nextdoor** | `"<name>" nextdoor` | Faves count and the gist of recommendations. High signal for local services. Usually login-walled, so snippets only. |
| **Facebook groups** | `"<name>" <city> facebook group recommend` | The gist of recommendations or warnings. |
| **YouTube** | `"<name>" <city> review youtube` | Common for contractors, auto, and e-commerce. |
| **Recommendation threads** | `best <industry> <city>`; `<city> recommend <industry>` | Whether locals name this business when asked whom to hire. Record up to 3 recurring alternatives, with links, but don't research them. |

### X playbook (when native X search is available)

1. Search X users for `<name>` (add the city if the name is generic). Confirm
   the handle against the fingerprint (bio, location, linked website). If
   nothing matches, record **no official handle** and still search the name.
2. Run keyword searches sorted by latest, about 10 results each:
   - `"<name>" (review OR reviews OR recommend OR recommended OR avoid OR scam OR complaint OR "never again")`
   - `@<handle> OR to:<handle> (scam OR complaint OR terrible OR recommend OR thanks)`
   - `from:<handle>` to see how the business talks to customers
3. If semantic search exists, run "customer experiences with `<name>` in `<city>`" and
   "should I hire `<name>`".
4. Fetch the full threads of the 2–5 highest-signal posts (complaints with
   engagement, or posts the business replied to).
5. If native search returns nothing, fall back to web search and mark X as
   `Snippets only`.

## Risk & legitimacy (Risk workstream)

| Check | How |
|---|---|
| **Registration** | State Secretary of State entity search (often JavaScript-only). Fall back to OpenCorporates or the BBB incorporation date. Capture status (active/dissolved/forfeited), formation date, registered agent, officers, prior names, and related entities. |
| **License** | Use the licensing column of the Industry table, plus city-level licenses where the trade requires them. Capture the number, status, expiry, and any discipline. |
| **Insurance, bond, certifications** | Board records sometimes show bond and insurance. Verify certifications on the certifier's own locator (manufacturer "certified installer" finders, board-certification lookups). |
| **Courts & bankruptcy** | `"<legal name>" (lawsuit OR "v." OR bankruptcy OR judgment OR lien)`; `"<owner>" "<name>"`. Also check CourtListener (strong on federal and appellate cases, thin on state) and state/county portals where they are searchable. Record the court, role (plaintiff/defendant), claim, outcome, and date. |
| **Regulators** | State Attorney General actions and lawsuit search; `"<name>" ftc.gov`; CFPB; OSHA establishment search (trades); EPA ECHO (industrial); plus the industry regulators in the Industry table. |
| **Recalls & safety** | CPSC, NHTSA, or FDA, where the business sells or services regulated products. |
| **News** | `"<name>" <city>` news; local TV consumer segments (`"<name>" "on your side" OR investigation`). |
| **Web presence** | Domain age via ICANN lookup (`lookup.icann.org`; RDAP replaced WHOIS). Wayback Machine if the domain or name looks new, and search former names on their own. Check for a real storefront vs. a virtual office or UPS box, name/address/phone consistency across listings, and "permanently closed" on any listing. |
| **Employee reviews** | `"<name>" glassdoor OR indeed`. Look for turnover, pressure-sales culture, unpaid staff, and ownership chaos. |

## Industry

Add every matching row. The **Industry workstream** takes the review-site
column and the **Risk workstream** takes the licensing column. Core platforms
already covered under Reviews aren't repeated here. For an unlisted industry,
search `best <industry> review sites` and `<state> <industry> license lookup`,
and use the "Unlisted" default concerns.

| Industry | Review sites | Licensing & regulators | Default concerns |
|---|---|---|---|
| **Home services / contractors** | Angi/HomeAdvisor (count as one source), Thumbtack, Houzz, Porch, BuildZoom (permits + license history) | State/city contractor license, manufacturer certification locators, OSHA | Shows up on time; quote vs. final invoice; workmanship/callbacks; warranty honored |
| **Movers** | Angi/HomeAdvisor | FMCSA SAFER company snapshot (USDOT/MC number), FMCSA household-goods complaint search, fmcsa.dot.gov/protect-your-move | Price changes / hostage loads; damage claims; arrival window |
| **Restaurants / hospitality / lodging** | TripAdvisor, OpenTable, Resy, delivery-app ratings; Booking.com/Expedia/Hotels.com | Local health-department inspections | Food/room quality; cleanliness; wait/service; billing surprises |
| **Medical / dental / therapy / senior care** | Healthgrades, Zocdoc, Vitals, WebMD Care, RateMDs (paid-removal allegations exist), Psychology Today | State medical/dental board, CMS Care Compare (facilities, nursing homes, home health), HHS-OIG exclusions list, Leapfrog Hospital Safety Grade | Billing surprises; outcomes & safety; wait times; upselling |
| **Legal** | Avvo, Martindale-Hubbell, Justia, Lawyers.com | State bar lookup (discipline) | Communication; fees vs. estimate; outcomes; professionalism |
| **Financial / insurance / lending** | — | CFPB complaint database, FINRA BrokerCheck, SEC IAPD, NMLS Consumer Access, state insurance dept., NAIC Consumer Information Source | Hidden fees; claims handling; pressure sales; account errors |
| **Auto sales / repair** | DealerRater, Cars.com, Edmunds, CarGurus, RepairPal | State dealer license board, state AG auto complaints, NHTSA recalls | Honest diagnosis; price vs. quote; add-on/finance pressure; comebacks |
| **Real estate / property management** | Zillow, Realtor.com, ApartmentRatings, Apartments.com | State real-estate commission | Responsiveness; deposits & fees; maintenance; disclosure |
| **Software / SaaS / B2B** | G2, Capterra, GetApp, TrustRadius, Gartner Peer Insights, Hacker News | Status-page history, data-breach news | Support; uptime; billing & cancellation; lock-in |
| **E-commerce / consumer products** | Amazon seller feedback, app-store reviews, product-category subreddits, ScamAdviser (can over-score new sites) | CPSC recalls, FTC actions | Shipping; returns/refunds; product as described; scam reports |
| **Gyms / salons / personal services** | ClassPass (in-app, so snippets only) | State cosmetology/barber board | Contract cancellation; billing after cancel; hygiene; upselling |
| **Childcare / education** | Care.com, Winnie, GreatSchools, Niche | State childcare licensing inspection reports | Safety & incidents; licensing; staffing/ratios; communication |
| **Pet services** | Rover | State veterinary board | Animal handling & safety; pricing; emergencies |
| **Travel / events / weddings** | TripAdvisor, The Knot, WeddingWire, Viator/GetYourGuide | Seller-of-travel registration (in states that require it) | Hidden fees; delivered as promised; no-shows; refunds |
| **Unlisted** | *(search for equivalents)* | *(search for equivalents)* | Quality of work; price honesty; communication; standing behind problems |

**Outside the US**, swap in local equivalents. For example: UK: Companies
House, Which? Trusted Traders, Checkatrade, TrustATrader. Canada: provincial
registries, HomeStars, BBB. Australia: ABN Lookup/ASIC, ProductReview.com.au,
hipages. Otherwise search `<country> <industry> review sites` and
`<country> business registry`. Swap US-specific protections (FTC, chargeback
rules) for local ones too.

## Intent queries (lead investigator)

```
"<name>" <city> reviews
"<name>" complaints OR "consumer alert" OR warning
"<name>" scam OR fraud OR ripoff
"<name>" lawsuit OR sued
"<name>" "never again" OR "stay away" OR avoid
"<name>" recommend OR recommended
"<legal name>" <state>
"<owner>" "<name>"   (apply the identity and allegation rules in SKILL.md)
"<phone>"
"<domain>"   (keep only results that aren't on the business's own site)
```

For each concern, add 2–3 paraphrases. For example, "hidden fees" becomes
`"<name>" ("hidden fees" OR "extra charge" OR "more than the quote")`.

## Protections & recourse (lead investigator, while writing)

Search `<state> <industry> consumer protection law` for rules that apply to
this purchase, such as home-improvement deposit caps and written-contract
requirements, gym-contract cancellation rights, or movers' binding estimates.

General protections that always apply (US):
- The FTC Cooling-Off Rule gives a 3-day cancellation right for many in-home sales.
- Paying by credit card preserves chargeback rights. Cash, wire, Zelle, and
  crypto don't.
- If it goes wrong, complain to the licensing board, the state AG, the BBB,
  and the industry regulator (CFPB, FMCSA, etc.).
