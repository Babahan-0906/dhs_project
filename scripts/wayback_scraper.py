import os
import re
import sys
import time
import random
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime

MAX_RETRIES = 4        # how many times to retry a failed request
BASE_RETRY_WAIT = 30   # seconds to wait before first retry (doubles each time)

# ─── Config ───────────────────────────────────────────────────────────────────

MAX_PAGES_PER_YEAR = 50

KEYWORDS = ['about', 'admission', 'homepage', 'news', 'international', 'global']

ALLOWED_DOMAINS = ['kaist.ac.kr', 'kaist.edu']

SEEDS = {
    1997: "https://web.archive.org/web/19971024025724/http://www.kaist.ac.kr/index.html.en",
    1998: "https://web.archive.org/web/19980128040312/http://www.kaist.ac.kr/index.html.en",
    # 1999: missing
    2000: "https://web.archive.org/web/20000422080935/http://www.kaist.ac.kr/index.html.en",
    2001: "https://web.archive.org/web/20010413034218/http://www.kaist.ac.kr/index.html.en",
    2002: "https://web.archive.org/web/20020929150729/http://www.kaist.edu/",
    2003: "https://web.archive.org/web/20030528172643/http://www.kaist.edu/",
    2004: "https://web.archive.org/web/20040321105712/http://www.kaist.edu/",
    2005: "https://web.archive.org/web/20050602014059/http://www.kaist.edu/",
    2006: "https://web.archive.org/web/20060702020933/http://www.kaist.edu/",
    2007: "https://web.archive.org/web/20070209195328/http://www.kaist.edu/",
    2008: "https://web.archive.org/web/20080522114248/http://www.kaist.ac.kr/",
    2009: "https://web.archive.org/web/20091228071256/http://www.kaist.edu/edu.html",
    2010: "https://web.archive.org/web/20100615165936/http://www.kaist.edu/edu.html",
    2011: "https://web.archive.org/web/20111010012450/http://www.kaist.edu/edu.html",
    2012: "https://web.archive.org/web/20121022061835/http://www.kaist.edu/edu.html",
    2013: "https://web.archive.org/web/20130729030646/http://www.kaist.edu/edu.html",
    2014: "https://web.archive.org/web/20140626044345/http://www.kaist.edu/html/en/index.html",
    2015: "https://web.archive.org/web/20151230092228/http://www.kaist.edu/html/en/index.html",
    2016: "https://web.archive.org/web/20161008200111/http://www.kaist.edu/html/en/index.html",
    2017: "https://web.archive.org/web/20170624100059/http://www.kaist.edu/html/en/index.html",
    2018: "https://web.archive.org/web/20180224115654/http://www.kaist.edu/html/en/index.html",
    2019: "https://web.archive.org/web/20190701075941/http://www.kaist.edu/html/en/index.html",
    2020: "https://web.archive.org/web/20200627113356/https://www.kaist.ac.kr/en/",
    2021: "https://web.archive.org/web/20210603045140/https://www.kaist.ac.kr/en/",
    2022: "https://web.archive.org/web/20220716075527/https://www.kaist.ac.kr/en/",
    2023: "https://web.archive.org/web/20231117073954/https://www.kaist.ac.kr/en/",
    2024: "https://web.archive.org/web/20240710104217/https://www.kaist.ac.kr/en/",
    2025: "https://web.archive.org/web/20250718152608/https://www.kaist.ac.kr/en/",
    2026: "https://web.archive.org/web/20260216001637/https://www.kaist.ac.kr/en/",
}

# Skip a year entirely if it already has scraped files
def year_already_done(year):
    year_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), str(year))
    if not os.path.isdir(year_dir):
        return False
    files = [f for f in os.listdir(year_dir) if f != 'errors.log']
    return len(files) > 0

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (KAIST Digital History Project) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Logging ──────────────────────────────────────────────────────────────────

LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB (matches log_rotator.py)

def rotate_log():
    """Rotate logs.txt if it exceeds LOG_MAX_BYTES."""
    log_path = os.path.join(BASE_DIR, 'logs.txt')
    if os.path.exists(log_path) and os.path.getsize(log_path) >= LOG_MAX_BYTES:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        rotated = os.path.join(BASE_DIR, f'logs_{ts}.txt')
        os.rename(log_path, rotated)
        print(f"[rotate] logs.txt rotated → logs_{ts}.txt", flush=True)

def log(msg):
    """Print timestamped message to stdout (caller pipes to tee/logfile)."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────

WAYBACK_RE = re.compile(r'https?://web\.archive\.org/web/(\d+)(?:[^/]*)/(.*)')

def parse_wayback_url(url):
    """Returns (timestamp_str, original_url) or (None, None)."""
    m = WAYBACK_RE.match(url)
    if not m:
        return None, None
    timestamp = m.group(1)
    original = m.group(2)
    # Ensure original has a scheme
    if not original.startswith('http'):
        original = 'http://' + original
    return timestamp, original


def is_kaist_domain(original_url):
    """True if the original URL belongs to an allowed KAIST domain."""
    try:
        host = urlparse(original_url).netloc.lower()
    except Exception:
        return False
    return any(host == d or host.endswith('.' + d) for d in ALLOWED_DOMAINS)


def is_relevant(original_url, link_text):
    """Keyword match against URL path + anchor text."""
    text = (original_url + ' ' + (link_text or '')).lower()
    return any(kw in text for kw in KEYWORDS)


def safe_filename(original_url):
    """Convert original URL path to a safe filename."""
    parsed = urlparse(original_url)
    path = parsed.path.strip('/')
    if not path:
        path = 'index'
    # Replace path separators and unsafe chars
    path = re.sub(r'[^\w.\-]', '_', path.replace('/', '_'))
    if not path.endswith(('.html', '.htm')):
        path += '.html'
    return path


def save_page(year, timestamp, original_url, html):
    """Save HTML to scrapes/YEAR/TIMESTAMP_filename.html. Returns save path."""
    year_dir = os.path.join(BASE_DIR, str(year))
    os.makedirs(year_dir, exist_ok=True)
    fname = f"{timestamp}_{safe_filename(original_url)}"
    save_path = os.path.join(year_dir, fname)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return save_path


def log_error(year, url, error):
    """Append failed URL to the year's errors.log."""
    err_path = os.path.join(BASE_DIR, str(year), 'errors.log')
    os.makedirs(os.path.dirname(err_path), exist_ok=True)
    with open(err_path, 'a', encoding='utf-8') as f:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{ts}] {url} — {error}\n")

# ─── Core crawler ─────────────────────────────────────────────────────────────

def crawl_year(year, seed_url, session):
    log(f"{'='*60}")
    log(f"Starting year {year} | seed: {seed_url}")
    log(f"{'='*60}")

    seed_urls = {seed_url}
    visited = set()
    visited_paths = set()  # normalized KAIST paths, to dedupe across timestamps
    queue = [seed_url]
    pages_scraped = 0

    while queue and pages_scraped < MAX_PAGES_PER_YEAR:
        url = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)
        # Also track by normalized KAIST path to avoid different-timestamp duplicates
        _, orig_check = parse_wayback_url(url)
        if orig_check:
            visited_paths.add(urlparse(orig_check).path.rstrip('/'))
        log(f"[{year}] [{pages_scraped+1}/{MAX_PAGES_PER_YEAR}] Fetching: {url}")

        html = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = session.get(url, headers=HEADERS, timeout=30)
                resp.raise_for_status()
                html = resp.text
                break
            except requests.exceptions.HTTPError as e:
                status_code = resp.status_code
                if status_code in (404, 403, 410):
                    # Hard errors: skip immediately
                    log(f"[{year}]   HTTP {status_code} — skipping (no retry): {url}")
                    log_error(year, url, str(e))
                    break
                else:
                    # Transient errors (429, 500, 502, 503, 504): retry with exponential backoff
                    wait = BASE_RETRY_WAIT * (2 ** (attempt - 1)) + random.uniform(0, 5)
                    if status_code == 429:
                        wait += 30  # Add extra cooling time for rate limit
                    log(f"[{year}]   HTTP {status_code} error (attempt {attempt}/{MAX_RETRIES}): {e}")
                    if attempt < MAX_RETRIES:
                        log(f"[{year}]   Waiting {wait:.0f}s before retry...")
                        time.sleep(wait)
                    else:
                        log(f"[{year}]   Giving up on this URL.")
                        log_error(year, url, str(e))
            except Exception as e:
                # Network errors (connection refused, timeout) — use exponential backoff
                wait = BASE_RETRY_WAIT * (2 ** (attempt - 1)) + random.uniform(0, 5)
                log(f"[{year}]   ATTEMPT {attempt}/{MAX_RETRIES} network error: {e}")
                if attempt < MAX_RETRIES:
                    log(f"[{year}]   Waiting {wait:.0f}s before retry...")
                    time.sleep(wait)
                else:
                    log(f"[{year}]   Giving up on this URL.")
                    log_error(year, url, str(e))
        if html is None:
            continue

        timestamp, original_url = parse_wayback_url(url)
        if not timestamp:
            log(f"[{year}]   SKIP — could not parse wayback URL")
            continue

        save_path = save_page(year, timestamp, original_url, html)
        log(f"[{year}]   Saved → {os.path.relpath(save_path, BASE_DIR)}")
        pages_scraped += 1

        is_current_page_seed = (url in seed_urls)

        # Extract and queue links
        soup = BeautifulSoup(html, 'html.parser')
        queued = 0
        
        candidates = []
        for a in soup.find_all('a', href=True):
            candidates.append((a['href'].strip(), a.get_text(strip=True), False))
        for f in soup.find_all(['frame', 'iframe'], src=True):
            candidates.append((f['src'].strip(), '', True))

        for href, link_text, is_frame in candidates:
            if href.startswith(('javascript:', 'mailto:', '#')):
                continue

            abs_url = urljoin(url, href)

            # Must be a wayback URL
            ts2, orig2 = parse_wayback_url(abs_url)
            if not ts2 or not orig2:
                continue

            # Must belong to a KAIST domain
            if not is_kaist_domain(orig2):
                continue

            # Skip already visited / already queued
            if abs_url in visited or abs_url in queue:
                continue

            # Skip if we've already scraped this KAIST path at a different timestamp
            norm_path = urlparse(orig2).path.rstrip('/')
            if norm_path in visited_paths:
                continue

            # If we find a frame/iframe on a seed page, it is also a seed URL!
            if is_current_page_seed and is_frame:
                seed_urls.add(abs_url)

            # Seed page or frame link: queue everything from KAIST domain
            # Sub-pages: keyword filter applies
            if is_current_page_seed or is_frame or is_relevant(orig2, link_text):
                queue.append(abs_url)
                queued += 1

        log(f"[{year}]   Queued {queued} new links. Queue depth: {len(queue)}")

        # Rate limiting — conservative delay to avoid being rate-limited
        if queue and pages_scraped < MAX_PAGES_PER_YEAR:
            delay = random.uniform(8.0, 15.0)
            log(f"[{year}]   Sleeping {delay:.0f}s...")
            time.sleep(delay)

    log(f"[{year}] Done — {pages_scraped} pages scraped.\n")
    return pages_scraped


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    rotate_log()
    log(f"Wayback KAIST Scraper v3 started — {datetime.now()}")
    log(f"MAX_PAGES_PER_YEAR={MAX_PAGES_PER_YEAR} | KEYWORDS={KEYWORDS}\n")

    # If year args passed (from monitor.sh), only run those years
    bypass_skip = False
    if len(sys.argv) > 1:
        try:
            target_years = [int(y) for y in sys.argv[1:]]
            bypass_skip = True
        except ValueError:
            print("Usage: python wayback_scraper_v3.py [year1 year2 ...]")
            sys.exit(1)
        log(f"Targeted years from args: {target_years} (bypassing skip check and archiving old folders)")
    else:
        target_years = sorted(SEEDS.keys())

    total = 0
    for year in target_years:
        if year not in SEEDS:
            log(f"Year {year} not in SEEDS, skipping.")
            continue

        # If explicitly targeted and directory exists, rename it to archive the old files
        year_dir = os.path.join(BASE_DIR, str(year))
        if bypass_skip and os.path.isdir(year_dir):
            files = [f for f in os.listdir(year_dir) if f != 'errors.log']
            if files:
                backup_dir = os.path.join(BASE_DIR, f"{year}_old")
                counter = 1
                while os.path.exists(backup_dir):
                    backup_dir = os.path.join(BASE_DIR, f"{year}_old_{counter}")
                    counter += 1
                log(f"Archiving old directory for {year} to {os.path.basename(backup_dir)}")
                os.rename(year_dir, backup_dir)

        if not bypass_skip and year_already_done(year):
            log(f"Skipping {year} — already has scraped files.")
            continue
        try:
            scraped = crawl_year(year, SEEDS[year])
            total += scraped
            # Brief pause between years
            if scraped > 0:
                pause = random.uniform(5.0, 10.0)
                log(f"Pausing {pause:.0f}s between years...")
                time.sleep(pause)
        except KeyboardInterrupt:
            log("Interrupted by user.")
            break
        except Exception as e:
            log(f"FATAL error for year {year}: {e}")

    log(f"\nAll done. Total pages scraped: {total}")


if __name__ == '__main__':
    main()
