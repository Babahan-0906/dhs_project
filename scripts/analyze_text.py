"""
02_analyze_text.py — KAIST Digital History Project

Part A: Term frequency per year from news corpus
Part B: Enrollment correlation and lag analysis
"""

import csv
import os
import re
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_CSV      = os.path.join(PROJECT_ROOT, "data/news/kaist_news_full.csv")
ENROLL_CSV    = os.path.join(PROJECT_ROOT, "data/enrollment/kaist_intl_enrollment.csv")
OUT_DIR       = os.path.join(PROJECT_ROOT, "output")
FREQ_CSV      = os.path.join(OUT_DIR, "term_frequency_by_year.csv")           # full corpus
FREQ_INST_CSV = os.path.join(OUT_DIR, "term_frequency_institutional.csv")     # institutional only
CORR_CSV      = os.path.join(OUT_DIR, "language_enrollment_correlation.csv")

FOCUS_YEARS = range(2006, 2026)   # analysis window (news is reliable from 2006)

TERMS = {
    "global":          ["global", "globally"],
    "international":   ["international", "internationally"],
    "world_class":     ["world-class", "worldclass", "world class"],
    "diversity":       ["diversity", "diverse", "multicultural"],
    "ranking":         ["ranking", "ranked", "rankings", "qs", "times higher"],
    "innovation":      ["innovation", "innovative", "innovate"],
    "excellence":      ["excellence", "excellent", "leading"],
    "collaboration":   ["collaboration", "collaborate", "partnership", "mou"],
    "foreign_students":["foreign student", "international student", "overseas student"],
    # internationalization-policy + topical-displacement terms
    "english":         ["english"],
    "ai":              ["artificial intelligence", "machine learning", "ai"],
    "entrepreneurship":["startup", "start-up", "entrepreneur", "entrepreneurship"],
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def count_terms(text):
    t = text.lower()
    counts = {}
    for label, variants in TERMS.items():
        n = 0
        for v in variants:
            # whole-word match for single words, substring for phrases
            if " " in v:
                n += t.count(v)
            else:
                n += len(re.findall(r'\b' + re.escape(v) + r'\b', t))
        counts[label] = n
    return counts


RESEARCH_RE = re.compile(
    r"\b(develop(?:ed|s)?|researchers?|professor|material|algorithm|"
    r"discovered|published|journal|nature|science|cells?|molecul|quantum|"
    r"semiconductor|battery|catalyst|protein|tumou?r)\b"
)

def is_research(text):
    """Heuristic: an article is a research press release if it hits many
    science/discovery cue words. Used to separate research PR from
    institutional/branding news so term frequency stays comparable across
    years (the corpus drifts heavily toward research PR after ~2016)."""
    return len(RESEARCH_RE.findall(text.lower())) >= 3


def interpolate_enrollment(enroll_data):
    """Linear interpolation to fill in missing years."""
    years = sorted(enroll_data)
    filled = {}
    for i in range(len(years) - 1):
        y0, y1 = years[i], years[i + 1]
        v0, v1 = enroll_data[y0], enroll_data[y1]
        for y in range(y0, y1 + 1):
            frac = (y - y0) / (y1 - y0)
            filled[y] = round(v0 + frac * (v1 - v0))
    filled[years[-1]] = enroll_data[years[-1]]
    return filled


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx  = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy  = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return None, None
    r = num / (dx * dy)
    return round(r, 4), n


# ─── Part A: term frequency per year ─────────────────────────────────────────

def compute_frequency(institutional_only):
    """Aggregate term frequency by year. If institutional_only, drop research
    press releases so the corpus stays genre-comparable across years."""
    year_words  = defaultdict(int)
    year_terms  = defaultdict(lambda: defaultdict(int))
    year_count  = defaultdict(int)

    with open(NEWS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            year = row.get("year", "").strip()
            if not year.isdigit() or int(year) not in FOCUS_YEARS:
                continue
            year = int(year)
            text = row.get("full_text", "")
            if institutional_only and is_research(text):
                continue
            wc = len(text.split())
            year_words[year] += wc
            year_count[year] += 1
            for label, cnt in count_terms(text).items():
                year_terms[year][label] += cnt

    rows = []
    for year in sorted(FOCUS_YEARS):
        total_w = year_words[year]
        if total_w == 0:
            continue
        row = {"year": year, "article_count": year_count[year], "total_words": total_w}
        for label in TERMS:
            raw = year_terms[year][label]
            row[f"{label}_count"] = raw
            row[f"{label}_per1000"] = round(raw / total_w * 1000, 4)
        rows.append(row)
    return rows


def write_freq(rows, path):
    os.makedirs(OUT_DIR, exist_ok=True)
    cols = ["year", "article_count", "total_words"] + \
           [f"{l}{s}" for l in TERMS for s in ("_count", "_per1000")]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def part_a():
    print("=== Part A: term frequency from news corpus ===")

    full_rows = compute_frequency(institutional_only=False)
    inst_rows = compute_frequency(institutional_only=True)
    write_freq(full_rows, FREQ_CSV)
    write_freq(inst_rows, FREQ_INST_CSV)

    inst_by_year = {r["year"]: r for r in inst_rows}
    full_by_year = {r["year"]: r for r in full_rows}
    print("  year | full-corpus intl/1k | institutional-only intl/1k | inst articles")
    for year in sorted(full_by_year):
        f_i = full_by_year[year]["international_per1000"]
        i_i = inst_by_year.get(year, {}).get("international_per1000", 0)
        n_i = inst_by_year.get(year, {}).get("article_count", 0)
        print(f"  {year}: full={f_i:5.2f}  inst={i_i:5.2f}  ({n_i} inst articles)")

    print(f"\nSaved → {FREQ_CSV}")
    print(f"Saved → {FREQ_INST_CSV}\n")
    # Part B correlates on the institutional-only series (genre-controlled)
    return inst_by_year


# ─── Part B: enrollment correlation + lag analysis ───────────────────────────

def part_b(freq_by_year):
    print("=== Part B: enrollment correlation + lag analysis ===")

    # Load enrollment
    enroll_raw = {}
    with open(ENROLL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            y = int(row["year"])
            v = row["total_international_students"]
            if v and v.isdigit():
                enroll_raw[y] = int(v)

    enroll = interpolate_enrollment(enroll_raw)

    # Build aligned series (years present in both datasets)
    term_labels = list(TERMS.keys())
    common_years = sorted(y for y in freq_by_year if y in enroll)
    print(f"  Overlapping years for correlation: {common_years[0]}–{common_years[-1]} "
          f"({len(common_years)} years)")

    # Correlation at lag 0
    print("\n  Pearson r with enrollment at lag 0 (same year):")
    corr_results = []
    for label in term_labels:
        xs = [freq_by_year[y][f"{label}_per1000"] for y in common_years]
        ys = [enroll[y] for y in common_years]
        r, n = pearson(xs, ys)
        if r is not None:
            print(f"    {label:<18}: r={r:+.4f}  (n={n})")
        corr_results.append({"term": label, "lag": 0, "r": r, "n": n})

    # Lag analysis for "international" term (key argument term)
    print("\n  Lag analysis for 'international' term:")
    print("  (positive lag = language leads enrollment by N years)")
    lag_rows = []
    for lag in range(-3, 4):
        pairs = []
        for y in common_years:
            y_enroll = y + lag
            if y_enroll in enroll and y in freq_by_year:
                pairs.append((freq_by_year[y]["international_per1000"], enroll[y_enroll]))
        if len(pairs) >= 3:
            xs, ys = zip(*pairs)
            r, n = pearson(list(xs), list(ys))
            flag = " <-- strongest?" if r and abs(r) > 0.85 else ""
            print(f"    lag={lag:+d}: r={r:+.4f}  (n={n}){flag}")
            lag_rows.append({"term": "international", "lag": lag, "r": r, "n": n})

    # Save correlation CSV
    all_corr = corr_results + lag_rows
    with open(CORR_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["term", "lag", "r", "n"])
        w.writeheader()
        w.writerows(all_corr)
    print(f"\nSaved → {CORR_CSV}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    freq = part_a()
    part_b(freq)
    print("Analysis complete.")
