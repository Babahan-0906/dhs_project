"""
03_visualize.py — KAIST Digital History Project

Charts built to support the REVISED thesis:
  - language is policy/leadership-driven, not enrollment-driven
  - branding stayed decoupled from reality (COVID)
  - internationalization agenda was displaced by AI/entrepreneurship

Outputs PNGs to output/charts/.
"""

import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL_CSV  = os.path.join(ROOT, "output/term_frequency_by_year.csv")
INST_CSV  = os.path.join(ROOT, "output/term_frequency_institutional.csv")
ENROLL    = os.path.join(ROOT, "data/enrollment/kaist_intl_enrollment.csv")
TIMELINE  = os.path.join(ROOT, "data/enrollment/kaist_policy_timeline.csv")
CHARTS    = os.path.join(ROOT, "output/charts")

# Key events to annotate (year -> short label)
KEY_EVENTS = {
    2006: "Suh pres.\n(World Class)",
    2009: "ICU merger",
    2013: "Study Korea\n/ Kang pres.",
    2019: "AI Grad School",
    2021: "Lee pres.\n/ COVID",
}

plt.rcParams.update({
    "figure.dpi": 110, "font.size": 11, "axes.grid": True,
    "grid.alpha": 0.3, "axes.spines.top": False, "axes.spines.right": False,
})


# ─── loaders ─────────────────────────────────────────────────────────────────

def load_freq(path):
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[int(r["year"])] = {k: float(v) if k != "year" else int(v)
                                   for k, v in r.items()}
    return out


def series(freq, term):
    yrs = sorted(freq)
    return yrs, [freq[y][f"{term}_per1000"] for y in yrs]


def smooth(vals, window=3):
    """Centered rolling mean to tame single-year noise."""
    out = []
    half = window // 2
    for i in range(len(vals)):
        lo, hi = max(0, i - half), min(len(vals), i + half + 1)
        out.append(sum(vals[lo:hi]) / (hi - lo))
    return out


def load_enrollment():
    rows = []
    with open(ENROLL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = r["total_international_students"]
            if v and v.isdigit():
                rows.append((int(r["year"]), int(v), r["confidence"]))
    return rows


def annotate_events(ax, ymax):
    for yr, label in KEY_EVENTS.items():
        ax.axvline(yr, color="gray", ls=":", lw=1, alpha=0.6)
        ax.text(yr, ymax * 0.98, label, rotation=90, va="top", ha="right",
                fontsize=7.5, color="gray")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))


# ─── Chart 1: term frequency trends (institutional corpus) ───────────────────

def chart_terms(inst):
    fig, ax = plt.subplots(figsize=(11, 6))
    for term, color in [("international", "#d62728"), ("global", "#1f77b4"),
                        ("ranking", "#2ca02c"), ("world_class", "#ff7f0e")]:
        yrs, vals = series(inst, term)
        ax.plot(yrs, smooth(vals), label=term.replace("_", "-"), color=color, lw=2)
    annotate_events(ax, ax.get_ylim()[1])
    ax.set(xlabel="Year", ylabel="mentions per 1,000 words (3-yr smoothed)",
           title="KAIST branding language over time (institutional news, genre-controlled)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "01_term_frequency_trends.png"))
    plt.close(fig)


# ─── Chart 2: enrollment with COVID dip ──────────────────────────────────────

def chart_enrollment(rows):
    fig, ax = plt.subplots(figsize=(11, 6))
    yrs  = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    # interpolated line
    ax.plot(yrs, vals, color="#555", lw=1.5, ls="--", zorder=1,
            label="enrollment (interpolated between data points)")
    # markers colored by confidence
    cmap = {"high": "#2ca02c", "medium": "#ff7f0e", "low": "#d62728"}
    for y, v, conf in rows:
        ax.scatter(y, v, color=cmap.get(conf, "gray"), s=55, zorder=3,
                   edgecolor="white")
    # highlight COVID dip
    ax.annotate("COVID dip\n1,027 → 817", xy=(2021, 817), xytext=(2021.3, 500),
                fontsize=9, color="#d62728",
                arrowprops=dict(arrowstyle="->", color="#d62728"))
    for conf, c in cmap.items():
        ax.scatter([], [], color=c, label=f"{conf}-confidence data point")
    ax.set(xlabel="Year", ylabel="international students",
           title="KAIST international student enrollment (verified + interpolated)")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "02_enrollment_growth.png"))
    plt.close(fig)


# ─── Chart 3: language vs enrollment dual axis (THE argument chart) ───────────

def chart_dual(inst, rows):
    fig, ax1 = plt.subplots(figsize=(11, 6))
    # language (left)
    yrs, intl = series(inst, "international")
    _,   glob = series(inst, "global")
    ax1.plot(yrs, smooth(intl), color="#d62728", lw=2, label="'international' /1k")
    ax1.plot(yrs, smooth(glob), color="#1f77b4", lw=2, label="'global' /1k")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("language: mentions per 1,000 words", color="#333")
    # enrollment (right)
    ax2 = ax1.twinx()
    ax2.spines["right"].set_visible(True)
    ax2.plot([r[0] for r in rows], [r[1] for r in rows], color="black",
             lw=2.5, ls="--", marker="o", ms=4, label="intl enrollment")
    ax2.set_ylabel("international students", color="black")
    ax2.grid(False)
    # combined legend
    l1, lab1 = ax1.get_legend_handles_labels()
    l2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lab1 + lab2, loc="upper left")
    ax1.set_title("Language vs. reality: 'international' peaks early & decouples; "
                  "'global' tracks enrollment")
    ax1.set_xlim(2005, 2026)
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "03_language_vs_enrollment.png"))
    plt.close(fig)


# ─── Chart 4: topical displacement ───────────────────────────────────────────

def chart_displacement(full):
    fig, ax = plt.subplots(figsize=(11, 6))
    yrs = sorted(full)
    intl = [full[y]["international_per1000"] + full[y]["global_per1000"] +
            full[y]["foreign_students_per1000"] for y in yrs]
    ai   = [full[y]["ai_per1000"] + full[y]["entrepreneurship_per1000"] for y in yrs]
    ax.plot(yrs, smooth(intl), color="#1f77b4", lw=2.5,
            label="internationalization bundle")
    ax.plot(yrs, smooth(ai), color="#9467bd", lw=2.5,
            label="AI + entrepreneurship bundle")
    ax.fill_between(yrs, smooth(intl), alpha=0.08, color="#1f77b4")
    ax.fill_between(yrs, smooth(ai), alpha=0.08, color="#9467bd")
    ax.set(xlabel="Year", ylabel="mentions per 1,000 words (3-yr smoothed)",
           title="Agenda displacement: internationalization gives way to AI (full corpus)")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "04_topical_displacement.png"))
    plt.close(fig)


# ─── Chart 5: presidential signatures ────────────────────────────────────────

def chart_eras(inst):
    presidents = [("Suh\n06-12", range(2006, 2013)),
                  ("Kang\n13-16", range(2013, 2017)),
                  ("Shin\n17-20", range(2017, 2021)),
                  ("Lee\n21-25", range(2021, 2026))]
    terms = ["international", "global", "ranking", "ai", "entrepreneurship"]
    colors = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#8c564b"]

    fig, ax = plt.subplots(figsize=(11, 6))
    import numpy as np
    x = np.arange(len(presidents))
    w = 0.16
    for i, (term, c) in enumerate(zip(terms, colors)):
        means = []
        for _, yrs in presidents:
            ys = [inst[y][f"{term}_per1000"] for y in yrs if y in inst]
            means.append(sum(ys) / len(ys) if ys else 0)
        ax.bar(x + (i - 2) * w, means, w, label=term.replace("_", "-"), color=c)
    ax.set_xticks(x)
    ax.set_xticklabels([p[0] for p in presidents])
    ax.set(ylabel="mentions per 1,000 words", xlabel="president (tenure)",
           title="Each president's signature term (institutional news)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "05_presidential_eras.png"))
    plt.close(fig)


# ─── Chart 6: the confound (methodological selling point) ────────────────────

def chart_confound(full, inst):
    fig, ax = plt.subplots(figsize=(11, 6))
    yrs, f_intl = series(full, "international")
    _,   i_intl = series(inst, "international")
    # 3-yr smoothed so the trend contrast (declining vs flat) is legible
    ax.plot(yrs, smooth(f_intl), color="#999", lw=2.5, ls="--",
            label="full corpus (confounded by research PR) — declines")
    ax.plot(yrs, smooth(i_intl), color="#d62728", lw=2.5,
            label="institutional only (genre-controlled) — flat")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set(xlabel="Year", ylabel="'international' per 1,000 words",
           title="Why genre control matters: the naive decline (r=-0.61) is mostly an artifact "
                 "(controlled r=-0.05)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "06_confound_full_vs_institutional.png"))
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(CHARTS, exist_ok=True)
    full = load_freq(FULL_CSV)
    inst = load_freq(INST_CSV)
    rows = load_enrollment()

    chart_terms(inst)
    chart_enrollment(rows)
    chart_dual(inst, rows)
    chart_displacement(full)
    chart_eras(inst)
    chart_confound(full, inst)

    print("Charts written to", CHARTS)
    for f in sorted(os.listdir(CHARTS)):
        print("  -", f)
