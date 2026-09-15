# Maison&Objet Exhibitor Scraper

Scrapes Maison&Objet's public exhibitor directory (~1,774 companies) into a CSV:

```
registered_company_name, website, mom_brand_url, public_profile_url
```

No LinkedIn field — see [No LinkedIn field](#no-linkedin-field) below.

## Setup

Run inside the project's own `.venv` — one level up from this file, at `python-learning/.venv` — not a global interpreter. Commands below assume you're in this `scrape/` directory:

```
../.venv/bin/pip install playwright
../.venv/bin/python -m playwright install chromium
```

## Usage

Use the project venv's own interpreter (`../.venv/bin/python`), not a bare `python` — see [Setup](#setup).

```
# always test small first
../.venv/bin/python scrape_maison_objet.py --pages 1-2 --out test.csv

# full run, recommended: 4 parallel workers (~50 min — see Performance below)
../.venv/bin/python scrape_maison_objet.py --pages 1-74 --out exhibitors.csv --workers 4

# full run, sequential (~3.2 hours) — only if you have a reason to avoid parallelism
../.venv/bin/python scrape_maison_objet.py --pages 1-74 --out exhibitors.csv
```

The CSV is checkpointed after every listing page, so a crash partway through a run doesn't lose earlier pages. `--workers N` runs N OS processes in parallel (each with its own headless browser), merging their output at the end — see `scrape_parallel()`.

## Performance

`--workers` defaults to 1 (sequential) — you have to opt into parallelism.

Measured on a 10-core / 64GB machine: 1 worker took 472s for 72 companies (6.55 sec/company); 4 workers took 482s for 288 companies (72 each, matched per-worker load) — near-perfect linear scaling, no contention.

| Workers | Full run (~1,774 companies) |
|---|---|
| 1 (default) | ~3.2 hours |
| 4 (measured) | ~50 minutes |

Each worker is mostly waiting on network I/O rather than using CPU, so scaling likely continues past 4 (`--workers 8` would plausibly land around ~25 min) — untested, since pushing concurrency further against a real third-party site risks rate-limiting/blocking rather than teaching us anything new. `--workers 4` is a reasonable default for a full run.

## Running the full scrape

At ~50 min (`--workers 4`), you'll likely want to start it and walk away rather than babysit a terminal. Run it detached with `nohup`:

```
cd /path/to/python-learning/scrape
nohup ../.venv/bin/python scrape_maison_objet.py --pages 1-74 --out exhibitors.csv --workers 4 > run.log 2>&1 &
```

Check progress anytime with `tail -f run.log`; the CSV itself is checkpointed after every listing page regardless (see [Usage](#usage)). No open terminal or particular tool session is needed to run this — the venv, Playwright, and Chromium are all already set up, so a fresh terminal (or a brand-new Claude Code session pointed at this README) can kick it off the same way.

## How it works

Three hops per company, but only two of them use a browser:

1. **Find companies — no browser.** `fetch_listing_page()` calls Maison&Objet's Algolia search API directly over plain HTTP. The listing page's own `?page=N` URL parameter looks like real pagination but is inert (a fresh load always returns page 1 regardless); the site's real pagination is a JS-driven "Next" click that talks to this same Algolia endpoint. Calling it directly reproduces that exactly, without driving a browser through 74 pages of clicks. Each Algolia result is a *product*, not a company, and doesn't include the company's own profile URL — so we reconstruct it as `{brand.slug}-{slugify(sector)}`, a pattern verified against real profile URLs (46/46 match).
2. **Profile page (Playwright, headless).** `scrape_exhibitor()` visits the reconstructed profile URL for the company name and a link to its MOM ("Maison&Objet & More") brand page.
3. **MOM page (Playwright, headless).** The website isn't tagged in HTML — it's plain text near the address — so we regex-scan the visible page text for it.

Both Playwright hops run headless. The Algolia application ID + API key baked into the script are copied from the listing page's own client-side source — a search-only key meant to be called from any browser, not a secret.

## Known limitations

- **Selector drift.** `MOM_LINK_SELECTOR` was correct as of this writing; if Maison&Objet redesigns their site, this is the first thing to check.
- **Algolia access could change.** If the app ID/API key is ever rotated or domain-restricted, `fetch_listing_page()` fails loudly (an HTTP error) rather than silently — refresh the values from the live page's source if so.
- **Profile-URL reconstruction is a verified pattern, not a guarantee.** Confirmed against 46 real examples, not all ~1,774. A company whose slug doesn't follow the pattern fails to load and is silently missing from the output rather than erroring — worth spot-checking a full run's row count against the site's own advertised exhibitor total.

## No LinkedIn field

Maison&Objet doesn't publish LinkedIn Company Page links anywhere on their site. Getting one per company means an external lookup; scraping LinkedIn's own search results violates their Terms of Service. Standard compliant alternatives for a list this size:

1. Feed this CSV's company name + website into a B2B enrichment tool (Clearbit, Apollo.io, Cognism, Hunter.io, ZoomInfo) — most resolve a domain straight to a LinkedIn Company Page URL.
2. LinkedIn Sales Navigator's own account/company list upload feature.
3. A paid search API (SerpAPI, Bing Web Search API) querying `site:linkedin.com/company "<company name>"` per row, with a fuzzy-match/domain-verification step to avoid false positives on common company names.
