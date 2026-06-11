"""
02c_event_analysis.py — KAIST Digital History Project

Tests the REVISED thesis (language is policy-driven, not enrollment-driven)
with four event-aware analyses:

  1. Event study     — do branding-term spikes cluster in policy-event years?
  2. COVID experiment — did language hold up while enrollment actually fell?
  3. Topical displacement — internationalization vs AI/entrepreneurship agenda
  4. Presidential eras — mean term frequency per president tenure

Reads the institutional-only series for branding claims (genre-controlled) and
the full corpus for the agenda/displacement view.
"""

import csv
import os
from collections import defaultdict

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL_CSV  = os.path.join(ROOT, "output/term_frequency_by_year.csv")
INST_CSV  = os.path.join(ROOT, "output/term_frequency_institutional.csv")
TIMELINE  = os.path.join(ROOT, "data/enrollment/kaist_policy_timeline.csv")
ENROLL    = os.path.join(ROOT, "data/enrollment/kaist_intl_enrollment.csv")
OUT_DIR   = os.path.join(ROOT, "output")
EVENT_CSV = os.path.join(OUT_DIR, "event_study.csv")

BRANDING = ["international", "global", "ranking", "world_class"]
PRESIDENTS = [   # (name, start_year, end_year_inclusive)
    ("Suh Nam-pyo",     2006, 2012),
    ("Kang Sung-mo",    2013, 2016),
    ("Shin Sung-chul",  2017, 2020),
    ("Lee Kwang-hyung", 2021, 2025),
]


def load_freq(path):
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[int(r["year"])] = r
    return out


def per1000(freq, year, term):
    return float(freq[year][f"{term}_per1000"]) if year in freq else None


# ─── 1. Event study ──────────────────────────────────────────────────────────

def event_study(inst):
    print("=== 1. Event study: branding spikes vs policy-event years ===")

    # Years that have a policy-timeline event (within our analysis window)
    event_years = set()
    events_by_year = defaultdict(list)
    with open(TIMELINE, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            y = int(r["year"])
            if y in inst:
                event_years.add(y)
                events_by_year[y].append(r["event"][:50])

    all_years = sorted(inst)
    non_event = [y for y in all_years if y not in event_years]

    rows = []
    print(f"  Event years in window: {sorted(event_years)}")
    print(f"  (comparing each term's mean in event vs non-event years)\n")
    for term in BRANDING:
        ev_vals  = [per1000(inst, y, term) for y in sorted(event_years)]
        nev_vals = [per1000(inst, y, term) for y in non_event]
        ev_mean  = sum(ev_vals) / len(ev_vals)
        nev_mean = sum(nev_vals) / len(nev_vals)
        lift = (ev_mean / nev_mean - 1) * 100 if nev_mean else float("nan")
        print(f"  {term:<14}: event-yr mean={ev_mean:.2f}  non-event={nev_mean:.2f}  "
              f"lift={lift:+.0f}%")
        rows.append({"term": term, "event_mean": round(ev_mean, 3),
                     "nonevent_mean": round(nev_mean, 3), "lift_pct": round(lift, 1)})

    # Which single year was the peak for each branding term, and was it an event year?
    print("\n  Peak year per term (★ = coincides with a policy event):")
    for term in BRANDING:
        peak_y = max(all_years, key=lambda y: per1000(inst, y, term))
        star = "★" if peak_y in event_years else " "
        ev = "; ".join(events_by_year[peak_y]) if peak_y in event_years else "(no event)"
        print(f"    {term:<14}: {peak_y} {star}  {ev}")

    with open(EVENT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["term", "event_mean", "nonevent_mean", "lift_pct"])
        w.writeheader(); w.writerows(rows)
    print(f"\n  Saved → {EVENT_CSV}\n")


# ─── 2. COVID natural experiment ─────────────────────────────────────────────

def covid_experiment(inst):
    print("=== 2. COVID natural experiment (language vs real enrollment) ===")

    enroll = {}
    with open(ENROLL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = r["total_international_students"]
            if v and v.isdigit():
                enroll[int(r["year"])] = int(v)

    phases = [("pre-COVID  2018-19", [2018, 2019]),
              ("COVID      2020-21", [2020, 2021]),
              ("recovery   2022-23", [2022, 2023])]
    print("  phase                | intl_enrollment | international/1k | global/1k")
    for label, yrs in phases:
        en = [enroll[y] for y in yrs if y in enroll]
        en_str = f"{sum(en)//len(en)}" if en else "n/a"
        intl = sum(per1000(inst, y, "international") for y in yrs if y in inst) / len(yrs)
        glob = sum(per1000(inst, y, "global") for y in yrs if y in inst) / len(yrs)
        print(f"  {label} |   {en_str:>11}   |     {intl:6.2f}      |  {glob:6.2f}")
    print("  -> verified enrollment FELL 1027(2019) to 817(2021); "
          "did branding language fall with it?\n")


# ─── 3. Topical displacement ─────────────────────────────────────────────────

def displacement(full):
    print("=== 3. Topical displacement: internationalization vs AI/startup agenda ===")
    print("  (full corpus = overall news-center agenda)\n")
    print("  year | intl-bundle/1k | ai+startup/1k")
    for y in sorted(full):
        intl_bundle = (per1000(full, y, "international") +
                       per1000(full, y, "global") +
                       per1000(full, y, "foreign_students"))
        ai_bundle   = (per1000(full, y, "ai") +
                       per1000(full, y, "entrepreneurship"))
        bar_i = "#" * int(intl_bundle)
        bar_a = "*" * int(ai_bundle)
        print(f"  {y} |  {intl_bundle:6.2f} {bar_i:<8} | {ai_bundle:6.2f} {bar_a}")
    print()


# ─── 4. Presidential eras ────────────────────────────────────────────────────

def presidential_eras(inst):
    print("=== 4. Term frequency by presidential era (institutional corpus) ===")
    terms = BRANDING + ["english", "ai", "entrepreneurship"]
    header = "  president          " + "".join(f"{t[:9]:>11}" for t in terms)
    print(header)
    for name, y0, y1 in PRESIDENTS:
        yrs = [y for y in range(y0, y1 + 1) if y in inst]
        if not yrs:
            continue
        cells = ""
        for t in terms:
            mean = sum(per1000(inst, y, t) for y in yrs) / len(yrs)
            cells += f"{mean:>11.2f}"
        print(f"  {name:<18}{cells}")
    print()


if __name__ == "__main__":
    inst = load_freq(INST_CSV)
    full = load_freq(FULL_CSV)
    event_study(inst)
    covid_experiment(inst)
    displacement(full)
    presidential_eras(inst)
    print("Event analysis complete.")
