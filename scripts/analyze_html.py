"""
02b_analyze_html.py — KAIST Digital History Project

Structural + qualitative analysis of archived KAIST web pages (wayback_html).
This is CORROBORATING evidence to the news corpus, NOT a second independent
frequency dataset — the sample is capped (~50 pages/yr) and heterogeneous, so
raw cross-year frequency is confounded. We therefore do two robust things:

  Part 1 — Navigation/structure: does an internationalization term appear in the
           site's NAV menu that year? (presence/absence is robust to sampling)
  Part 2 — Page-type-controlled frequency: term rates computed ONLY within
           admissions + homepage pages, holding page type constant across years.

All known edge cases are handled: wayback toolbar stripping, junk/frame pages,
Korean-page exclusion, encoding errors, near-duplicate dedup.
"""

import csv
import os
import re
import hashlib
from collections import defaultdict
from bs4 import BeautifulSoup

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_DIR  = os.path.join(PROJECT_ROOT, "data/wayback_html")
OUT_DIR   = os.path.join(PROJECT_ROOT, "output")
NAV_CSV   = os.path.join(OUT_DIR, "html_nav_structure_by_year.csv")
FREQ_CSV  = os.path.join(OUT_DIR, "html_admissions_terms_by_year.csv")

MIN_WORDS   = 50      # drop frame shells / login / search pages below this
HANGUL_MAX  = 0.15    # drop pages where >15% of chars are Korean (English-term bias)

TERMS = {
    "global":        ["global", "globally"],
    "international": ["international", "internationally"],
    "world_class":   ["world-class", "worldclass", "world class"],
    "diversity":     ["diversity", "diverse", "multicultural"],
    "ranking":       ["ranking", "ranked", "rankings", "qs", "times higher"],
    "foreign":       ["foreign student", "international student", "overseas student"],
    "exchange":      ["exchange program", "study abroad", "dual degree", "joint degree"],
}

# Terms we look for specifically in NAV menus (institutional structure signal)
NAV_TERMS = ["international", "global", "foreign", "overseas", "exchange", "admissions"]


# ─── extraction + cleaning ───────────────────────────────────────────────────

HANGUL_RE = re.compile(r"[가-힣]")

def clean_soup(html):
    """Strip wayback toolbar, scripts, styles. Returns BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    # Wayback injects a toolbar div id=wm-ipp* — remove anything that mentions it
    for tag in soup.find_all(id=re.compile(r"wm-ipp")):
        tag.decompose()
    return soup


def hangul_ratio(text):
    if not text:
        return 0.0
    letters = [c for c in text if not c.isspace()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if HANGUL_RE.match(c)) / len(letters)


def extract_text(soup):
    return soup.get_text(separator=" ", strip=True)


def count_terms(text):
    t = text.lower()
    out = {}
    for label, variants in TERMS.items():
        n = 0
        for v in variants:
            if " " in v or "-" in v:
                n += t.count(v)
            else:
                n += len(re.findall(r"\b" + re.escape(v) + r"\b", t))
        out[label] = n
    return out


# ─── page-type classification (from filename/path) ───────────────────────────

def page_type(fname):
    f = fname.lower()
    if re.search(r"admiss|apply|entry", f):
        return "admissions"
    # homepage: index / en.html / main page roots
    if re.search(r"index|_en\.html$|/en\.html|english\.html$|edex", f):
        return "homepage"
    if re.search(r"global|international|intl|foreign|overseas", f):
        return "global_section"
    if re.search(r"about|glance|president|vision", f):
        return "about"
    return "other"


# ─── main passes ─────────────────────────────────────────────────────────────

def analyze():
    years = sorted(d for d in os.listdir(HTML_DIR)
                   if d.isdigit() and os.path.isdir(os.path.join(HTML_DIR, d)))

    nav_rows, freq_rows = [], []

    for year in years:
        ydir = os.path.join(HTML_DIR, year)
        files = [f for f in os.listdir(ydir) if f.endswith(".html")]

        seen_hashes = set()
        nav_terms_found = set()
        # frequency accumulators for admissions+homepage slice
        slice_words = 0
        slice_terms = defaultdict(int)
        slice_pages = 0
        kept_total, dropped_junk, dropped_korean, dropped_dup = 0, 0, 0, 0

        for fname in files:
            path = os.path.join(ydir, fname)
            try:
                html = open(path, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            soup = clean_soup(html)
            text = extract_text(soup)

            # edge case: junk / frame / login shells
            if len(text.split()) < MIN_WORDS:
                dropped_junk += 1
                continue
            # edge case: Korean pages skew English-term counts
            if hangul_ratio(text) > HANGUL_MAX:
                dropped_korean += 1
                continue
            # edge case: near-duplicate pages across timestamps
            h = hashlib.md5(text[:2000].encode("utf-8", "ignore")).hexdigest()
            if h in seen_hashes:
                dropped_dup += 1
                continue
            seen_hashes.add(h)
            kept_total += 1

            # ── Part 1: nav-menu term detection ──
            for nav in soup.find_all(["nav", "ul", "header"]):
                anchors = " ".join(a.get_text(" ", strip=True).lower()
                                   for a in nav.find_all("a"))
                # require it to look like a menu (several links)
                if len(nav.find_all("a")) >= 4:
                    for term in NAV_TERMS:
                        if re.search(r"\b" + re.escape(term) + r"\b", anchors):
                            nav_terms_found.add(term)

            # ── Part 2: page-type-controlled frequency ──
            ptype = page_type(fname)
            if ptype in ("admissions", "homepage"):
                wc = len(text.split())
                slice_words += wc
                slice_pages += 1
                for label, cnt in count_terms(text).items():
                    slice_terms[label] += cnt

        # record nav row
        nav_row = {"year": int(year), "pages_kept": kept_total}
        for term in NAV_TERMS:
            nav_row[f"nav_{term}"] = 1 if term in nav_terms_found else 0
        nav_rows.append(nav_row)

        # record frequency row (only if slice has content)
        if slice_words > 0:
            frow = {
                "year": int(year),
                "slice_pages": slice_pages,
                "slice_words": slice_words,
            }
            for label in TERMS:
                frow[f"{label}_per1000"] = round(slice_terms[label] / slice_words * 1000, 3)
            freq_rows.append(frow)

        nav_str = ",".join(sorted(nav_terms_found)) or "(none)"
        print(f"{year}: kept {kept_total:>2} "
              f"(junk {dropped_junk}, ko {dropped_korean}, dup {dropped_dup}) | "
              f"adm/home slice: {slice_pages}p/{slice_words}w | nav: {nav_str}")

    # write outputs
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(NAV_CSV, "w", newline="", encoding="utf-8") as f:
        cols = ["year", "pages_kept"] + [f"nav_{t}" for t in NAV_TERMS]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(nav_rows)
    with open(FREQ_CSV, "w", newline="", encoding="utf-8") as f:
        cols = ["year", "slice_pages", "slice_words"] + [f"{l}_per1000" for l in TERMS]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(freq_rows)

    print(f"\nSaved → {NAV_CSV}")
    print(f"Saved → {FREQ_CSV}")


if __name__ == "__main__":
    analyze()
