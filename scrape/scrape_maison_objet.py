"""
Maison&Objet exhibitor scraper

Scrapes the ~1,774-company Maison&Objet exhibitor directory into a CSV
(registered_company_name, website, mom_brand_url, public_profile_url).

Full docs — setup, usage, how the pipeline works, known fragility — live
in README.md next to this file. Read that first.
"""

import argparse
import csv
import json                 # Algolia request/response bodies in fetch_listing_page()
import math                 # chunk_pages() rounds its split up, not down
import multiprocessing      # --workers: see scrape_parallel()
import os
import re
import time
import unicodedata          # slugify(): strips accents to match M&O's URL convention
import urllib.request       # fetch_listing_page() calls Algolia directly, no browser needed

# TimeoutError aliased so it doesn't shadow the builtin — this is the
# specific exception a Playwright wait_for_* call raises on timeout.
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Algolia: how we find companies, without a browser. Copied from the
# listing page's own <script> tag — a search-only key meant to be called
# from any browser, not a secret. See README.md if these ever stop working.
ALGOLIA_APP_ID = "LPN4STGLQG"
ALGOLIA_API_KEY = "3dfb0b32b6d93bd5a34dceabcc437108"
ALGOLIA_QUERY_URL = (
    f"https://{ALGOLIA_APP_ID.lower()}-dsn.algolia.net/1/indexes/*/queries"
    f"?x-algolia-agent=Algolia+for+Python"
    f"&x-algolia-application-id={ALGOLIA_APP_ID}"
    f"&x-algolia-api-key={ALGOLIA_API_KEY}"
)
ALGOLIA_INDEX = "InsertionProduct_hall_asc"  # backs the listing page's product grid
ALGOLIA_HITS_PER_PAGE = 24                   # ceil(1774 / 24) == the site's own "74 pages"

# On an exhibitor's public profile page, the link through to its MOM
# ("Maison&Objet & More") brand page, where the website actually lives.
# Most likely thing to need updating if Maison&Objet's frontend changes.
MOM_LINK_SELECTOR = "a[href*='mom.maison-objet.com/en/brand/']"

# Matches URL-looking text in a MOM page's visible body — the website
# isn't tagged in HTML there, just printed as plain text.
WEBSITE_RE = re.compile(r"https?://(?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/\S*)?")

# Resource types to abort on every request — images/fonts/media don't
# affect the text we scrape. "stylesheet" is deliberately excluded: CSS
# visibility (display:none etc.) affects what .inner_text() returns, and
# that matters on the MOM page, where we regex-scan body text for the URL.
BLOCKED_RESOURCE_TYPES = {"image", "font", "media"}


def block_unneeded_resources(route):
    """
    Route handler passed to `page.route("**/*", ...)`. Playwright calls
    this for every request the page makes; we abort the ones we don't
    need and let everything else (HTML, JS, XHR/fetch, CSS) through.
    """
    if route.request.resource_type in BLOCKED_RESOURCE_TYPES:
        route.abort()
    else:
        route.continue_()


def goto_with_retry(page, url, ready_selector=None, ready_timeout=6000, settle_ms=300, attempts=2, timeout=30000):
    """
    Navigate to `url`, waiting for `ready_selector` to appear (if given)
    rather than for Playwright's "networkidle" — that waits for zero
    in-flight requests, which analytics/chat-widget scripts on this site
    prevent from ever happening, timing out even when the content we
    wanted loaded in the first second. A wait_for_selector timeout is
    swallowed rather than retried, since some callers (e.g. the MOM page)
    have no reliable selector, and some content (e.g. a MOM link) can be
    legitimately absent rather than slow. `settle_ms` adds a small extra
    buffer afterward for trailing lazy-loaded content.

    Returns True if navigation succeeded, False if every attempt failed
    (the caller is expected to move on rather than crash the whole run).
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            if ready_selector:
                try:
                    page.wait_for_selector(ready_selector, timeout=ready_timeout)
                except PlaywrightTimeoutError:
                    pass  # selector may legitimately be absent on this page
            page.wait_for_timeout(settle_ms)
            return True
        except Exception as e:
            # Catch broadly (DNS issues, connection resets, etc.) so any
            # flaky load gets the same log-and-retry treatment.
            last_error = e
            print(f"    ! attempt {attempt}/{attempts} failed for {url}: {e}")
    print(f"    ! giving up on {url}: {last_error}")
    return False


def parse_page_range(spec: str):
    """
    Turn a command-line value like "1-74" or "3" into a Python `range`
    (or list) of page numbers to scrape.

    Examples:
        parse_page_range("1-74") -> range(1, 75)   # 1, 2, ..., 74
        parse_page_range("3")    -> [3]
    """
    if "-" in spec:
        start, end = spec.split("-")
        # range()'s upper bound is EXCLUSIVE in Python, so we add 1 to
        # make sure e.g. "1-74" really does include page 74.
        return range(int(start), int(end) + 1)
    return [int(spec)]


def slugify(text):
    """
    "Decor & Design" -> "decor-design", matching Maison&Objet's own
    URL-slug convention (see fetch_listing_page()). NFKD-normalizing then
    ASCII-encoding strips accents: "Fourès" -> "Foures".
    """
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()


def fetch_listing_page(page_num, log_prefix="", attempts=3):
    """
    Fetches one page of the exhibitor listing directly from Algolia's
    search API (see README.md) — no browser — returning one reconstructed
    public_profile_url per unique brand on that page. Empty list once
    past the real last page. `page_num` is 1-indexed like `--pages`
    elsewhere; Algolia's own `page` is 0-indexed.
    """
    algolia_page = page_num - 1
    params = (
        f"query=&hitsPerPage={ALGOLIA_HITS_PER_PAGE}&maxValuesPerFacet=1000"
        f"&page={algolia_page}&distinct=true&facetingAfterDistinct=true&filters="
    )
    body = json.dumps({"requests": [{"indexName": ALGOLIA_INDEX, "params": params}]}).encode()

    last_error = None
    result = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                ALGOLIA_QUERY_URL, data=body,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                result = json.load(response)
            break
        except Exception as e:
            last_error = e
            print(f"{log_prefix}  ! Algolia request failed for page {page_num} "
                  f"(attempt {attempt}/{attempts}): {e}")
    if result is None:
        print(f"{log_prefix}  ! giving up on page {page_num}: {last_error}")
        return []

    search_result = result["results"][0]
    # nbPages tells us how many real pages of results exist in total —
    # once we're past it, there's nothing left to scrape.
    if algolia_page >= search_result.get("nbPages", algolia_page + 1):
        return []

    seen_brand_ids = set()
    profile_urls = []
    for hit in search_result["hits"]:
        brand = hit.get("brand") or {}
        brand_id = brand.get("id")
        if brand_id is None or brand_id in seen_brand_ids:
            continue
        seen_brand_ids.add(brand_id)
        slug = f"{brand.get('slug', '')}-{slugify(hit.get('sector') or '')}"
        profile_urls.append(f"https://www.maison-objet.com/en/paris/exhibitors/{slug}")

    return profile_urls


def scrape(pages, out_path):
    """
    Main orchestrator: for each page number in `pages`, find every
    exhibitor via `fetch_listing_page()`, then visit each in turn via
    `scrape_exhibitor()`. `pages` can be any list of page numbers, in any
    order — no need to reach earlier pages first.
    """
    # multiprocessing names the main process "MainProcess"; workers get
    # "worker-N" (see scrape_parallel()), which we use to prefix output
    # so several workers' interleaved logs stay legible.
    proc_name = multiprocessing.current_process().name
    log_prefix = f"[{proc_name}] " if proc_name != "MainProcess" else ""

    rows = []
    seen_profile_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.route("**/*", block_unneeded_resources)  # see BLOCKED_RESOURCE_TYPES above

        for page_num in pages:
            print(f"{log_prefix}[list] page {page_num} (via Algolia)")
            profile_urls = fetch_listing_page(page_num, log_prefix)
            if not profile_urls:
                print(f"{log_prefix}  no results for page {page_num} — stopping")
                break

            new_urls = [u for u in profile_urls if u not in seen_profile_urls]
            seen_profile_urls.update(new_urls)
            print(f"{log_prefix}  found {len(new_urls)} new exhibitor profile links")

            for profile_url in new_urls:
                # Catch broadly so one bad page (odd DOM, etc.) costs us
                # just this row, not the whole run.
                try:
                    row = scrape_exhibitor(page, profile_url)
                except Exception as e:
                    print(f"{log_prefix}    ! error scraping {profile_url}: {e}")
                    row = None
                if row:
                    rows.append(row)
                    print(f"{log_prefix}    {row['registered_company_name']!r} -> {row['website']}")
                time.sleep(0.3)  # be polite — small pause between requests

            write_csv(rows, out_path)  # checkpoint after every listing page

        browser.close()

    return rows


def chunk_pages(pages_list, workers):
    """
    Splits page numbers into up to `workers` contiguous, roughly-equal
    chunks (capped at len(pages_list), so a 2-page run never spawns idle
    workers even if --workers asked for more).
    """
    workers = min(workers, len(pages_list)) or 1
    chunk_size = math.ceil(len(pages_list) / workers)
    return [pages_list[i:i + chunk_size] for i in range(0, len(pages_list), chunk_size)]


def scrape_parallel(pages, out_path, workers):
    """
    Runs `workers` OS processes at once, each calling the ordinary
    `scrape()` on its own slice of `pages` into its own part-CSV, then
    merges all part-CSVs into `out_path`.

    Separate processes rather than threads or async/await because
    Playwright's *sync* API (used throughout this script) isn't
    thread-safe; a full Playwright rewrite to the async API is the
    alternative, but processes are the smaller change. Each worker's
    browser is headless, so this runs with no visible windows.
    """
    pages_list = list(pages)
    chunks = chunk_pages(pages_list, workers)
    part_paths = [f"{out_path}.part{i}.csv" for i in range(len(chunks))]

    processes = [
        multiprocessing.Process(target=scrape, args=(chunk, part_path), name=f"worker-{i}")
        for i, (chunk, part_path) in enumerate(zip(chunks, part_paths))
    ]
    for proc in processes:
        proc.start()
    for proc in processes:
        proc.join()

    return merge_part_csvs(part_paths, out_path)


def merge_part_csvs(part_paths, out_path):
    """
    Combines every worker's part-CSV into one CSV at `out_path`, deduping
    by `public_profile_url` (each worker's own dedup only covers the
    pages it handled), then deletes the part files.
    """
    seen_urls = set()
    rows = []
    for part_path in part_paths:
        if not os.path.exists(part_path):
            continue  # a worker that crashed before writing anything at all
        with open(part_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["public_profile_url"] not in seen_urls:
                    seen_urls.add(row["public_profile_url"])
                    rows.append(row)
        os.remove(part_path)

    write_csv(rows, out_path)
    return rows


def scrape_exhibitor(page, profile_url):
    """
    Given one exhibitor's public profile URL, return a dict with its
    name, website, and the two source URLs we found it at — or None if
    the profile page couldn't be loaded at all.
    """
    # Wait for the MOM link specifically: it's the deepest piece of content
    # we need from this page, so its presence is a good proxy for "the JS
    # has finished rendering." (Some exhibitors genuinely have no MOM link;
    # goto_with_retry() treats that selector timeout as OK, not a failure.)
    if not goto_with_retry(page, profile_url, ready_selector=MOM_LINK_SELECTOR, ready_timeout=4000):
        return None

    # Company name: the page's browser-tab <title> looks like
    # "CRISTEL - Exhibitor Maison&Objet - Hall 4 ...", so we split on
    # " - Exhibitor" and keep the part before it.
    title = page.title()
    name = title.split(" - Exhibitor")[0].strip() if " - Exhibitor" in title else title.strip()

    # `.first` narrows a (possibly multi-match) locator down to just the
    # first element, so `.count()` and `.get_attribute()` below act on
    # a single, specific link rather than a whole collection.
    mom_link = page.locator(MOM_LINK_SELECTOR).first
    if mom_link.count() == 0:
        # Some exhibitors don't have a MOM page at all — still return
        # what we do have (the name) rather than silently dropping them.
        return {
            "registered_company_name": name,
            "website": "",
            "mom_brand_url": "",
            "public_profile_url": profile_url,
        }

    mom_href = mom_link.get_attribute("href")
    # Strips trailing junk like "/products#at_medium=..." down to the
    # clean brand root, e.g. ".../en/brand/2056/cristel".
    mom_brand_url = re.sub(r"(/en/brand/\d+/[^/?#]+).*", r"\1", mom_href)

    website = ""
    # No reliable selector for "website text has rendered" (it's plain
    # text, not tagged) — a slightly longer settle buffer instead.
    if goto_with_retry(page, mom_brand_url, settle_ms=700):
        body_text = page.locator("body").inner_text()
        # Website is printed as plain text near the address, not a tagged
        # <a> — scan for anything URL-shaped, skipping M&O's own domain
        # and cloudfront (an image CDN, so a false-positive source).
        candidates = [
            m for m in WEBSITE_RE.findall(body_text)
            if "maison-objet.com" not in m and "cloudfront" not in m
        ]
        if candidates:
            website = candidates[0]

    return {
        "registered_company_name": name,
        "website": website,
        "mom_brand_url": mom_brand_url,
        "public_profile_url": profile_url,
    }


def write_csv(rows, out_path):
    """
    Overwrites `out_path` with all of `rows`. Called after every listing
    page (see `scrape()`), not just once at the end, as the checkpoint.
    """
    fieldnames = ["registered_company_name", "website", "mom_brand_url", "public_profile_url"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="1-74", help="e.g. 1-74 or 3")
    ap.add_argument("--out", default="exhibitors.csv")
    ap.add_argument(
        "--workers", type=int, default=1,
        help="parallel worker processes, each with its own headless browser (default 1 = sequential)",
    )
    args = ap.parse_args()

    pages = parse_page_range(args.pages)
    if args.workers > 1:
        rows = scrape_parallel(pages, args.out, args.workers)
    else:
        rows = scrape(pages, args.out)
    print(f"\nDone. {len(rows)} rows written to {args.out}")
