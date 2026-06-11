import csv
import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://news.kaist.ac.kr/newsen/html/news/"
HEADERS = {"User-Agent": "Mozilla/5.0 (KAIST Digital History Research) Chrome/91.0"}
OUT_CSV = os.path.join(os.path.dirname(__file__), "../data/news/kaist_news_full.csv")
FIELDNAMES = ["mng_no", "date", "year", "title", "url", "full_text", "word_count"]

TOTAL_PAGES = 213  # last known page count; script stops early if a page returns 0 links


# ─── Fetch helpers ────────────────────────────────────────────────────────────

def get(url, retries=3):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.text
        except Exception as e:
            if attempt == retries:
                print(f"  [FAIL] {url} — {e}")
                return None
            wait = 10 * attempt + random.uniform(0, 3)
            print(f"  [retry {attempt}] {e} — waiting {wait:.0f}s")
            time.sleep(wait)


# ─── Phase 1: collect mng_no IDs from listing pages ──────────────────────────

def collect_ids(start_page=1, end_page=TOTAL_PAGES):
    ids = []
    for page in range(start_page, end_page + 1):
        url = f"{BASE_URL}?mode=L&GotoPage={page}"
        print(f"[listing] page {page}/{end_page} — {url}")
        html = get(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        links = [a["href"] for a in soup.find_all("a", href=True) if "mng_no" in a.get("href", "")]
        if not links:
            print(f"  [listing] no links on page {page}, stopping.")
            break
        for href in links:
            m = re.search(r"mng_no=(\d+)", href)
            if m:
                ids.append(int(m.group(1)))
        print(f"  found {len(links)} links — total so far: {len(ids)}")
        time.sleep(random.uniform(0.8, 1.5))
    return ids


# ─── Phase 2: fetch and parse each article ───────────────────────────────────

def parse_article(mng_no):
    url = f"{BASE_URL}?mode=V&mng_no={mng_no}"
    html = get(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Title
    layout = soup.find("div", class_="prog_layout")
    title_tag = layout.find(["h3", "h4", "strong"]) if layout else None
    title = title_tag.get_text(strip=True) if title_tag else ""
    title = re.sub(r"​", "", title).strip()  # strip zero-width spaces

    # Date
    date_tag = soup.find("span", class_="date")
    date_raw = date_tag.get_text(strip=True) if date_tag else ""
    date = re.sub(r"^Date:\s*", "", date_raw).strip()

    # Body
    body_tag = soup.find("div", class_="txt_box")
    full_text = body_tag.get_text(separator=" ", strip=True) if body_tag else ""

    year = date[:4] if date else ""
    word_count = len(full_text.split())

    return {
        "mng_no": mng_no,
        "date": date,
        "year": year,
        "title": title,
        "url": url,
        "full_text": full_text,
        "word_count": word_count,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def load_done_ids(path):
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {int(row["mng_no"]) for row in csv.DictReader(f) if row.get("mng_no")}


def main():
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    done_ids = load_done_ids(OUT_CSV)
    print(f"Already scraped: {len(done_ids)} articles")

    # Phase 1 — collect IDs
    print("\n=== Phase 1: collecting article IDs from listing pages ===")
    all_ids = collect_ids()
    new_ids = [i for i in all_ids if i not in done_ids]
    print(f"\nTotal IDs found: {len(all_ids)} | New to fetch: {len(new_ids)}")

    # Phase 2 — fetch articles
    print("\n=== Phase 2: fetching articles ===")
    write_header = not os.path.exists(OUT_CSV)
    with open(OUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        for i, mng_no in enumerate(new_ids, 1):
            print(f"[{i}/{len(new_ids)}] mng_no={mng_no}")
            row = parse_article(mng_no)
            if row:
                writer.writerow(row)
                f.flush()
                print(f"  {row['date']} | {row['word_count']} words | {row['title'][:60]}")
            time.sleep(random.uniform(0.8, 1.5))

    print(f"\nDone. Output: {OUT_CSV}")


if __name__ == "__main__":
    main()
