"""
04_build_byproduct.py — KAIST Digital History Project

Assembles the final byproduct: a single self-contained index.html with all
charts embedded as base64 (no external files, no broken-link risk). Re-run
after regenerating charts to refresh the page.
"""

import base64
import os

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS = os.path.join(ROOT, "output/charts")
OUT    = os.path.join(ROOT, "output/index.html")


def img(name, alt):
    path = os.path.join(CHARTS, name)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f'<figure><img src="data:image/png;base64,{b64}" alt="{alt}">'
            f'<figcaption>{alt}</figcaption></figure>')


HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Talking Global — KAIST Internationalization Discourse, 2006–2025</title>
<style>
  :root {{ --ink:#1a1a2e; --accent:#d62728; --blue:#1f77b4; --muted:#6c757d;
           --bg:#fbfbfd; --card:#fff; --line:#e3e3ea; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:Georgia,'Times New Roman',serif; color:var(--ink);
          background:var(--bg); line-height:1.7; }}
  header {{ background:linear-gradient(135deg,#1a1a2e,#2d2d5a); color:#fff;
            padding:4rem 1.5rem 3rem; }}
  .wrap {{ max-width:860px; margin:0 auto; padding:0 1.5rem; }}
  header .wrap {{ padding:0 1.5rem; }}
  h1 {{ font-size:2.3rem; line-height:1.2; margin:0 0 .6rem; }}
  .sub {{ font-size:1.1rem; color:#cfd2ff; font-style:italic; margin:0; }}
  .meta {{ margin-top:1.5rem; font-size:.85rem; color:#a9adde;
           font-family:system-ui,sans-serif; }}
  h2 {{ font-size:1.6rem; margin:3rem 0 .3rem; padding-top:1rem;
        border-top:2px solid var(--line); }}
  h2 .n {{ color:var(--accent); font-family:system-ui,sans-serif; font-size:1rem;
           display:block; letter-spacing:.1em; }}
  h3 {{ font-size:1.2rem; margin:2rem 0 .3rem; }}
  p {{ margin:.8rem 0; }}
  .question {{ background:var(--card); border-left:5px solid var(--accent);
               padding:1.2rem 1.5rem; margin:2rem 0; font-size:1.15rem;
               box-shadow:0 2px 12px rgba(0,0,0,.05); }}
  .thesis {{ background:#1a1a2e; color:#fff; padding:1.5rem 1.8rem; border-radius:8px;
             margin:2rem 0; font-size:1.1rem; }}
  .thesis strong {{ color:#ffd166; }}
  figure {{ margin:2rem 0; text-align:center; }}
  figure img {{ max-width:100%; border:1px solid var(--line); border-radius:6px;
                background:#fff; }}
  figcaption {{ font-size:.85rem; color:var(--muted); margin-top:.5rem;
                font-family:system-ui,sans-serif; font-style:italic; }}
  .keyfind {{ background:#fff6f6; border:1px solid #f3d0d0; border-radius:6px;
              padding:1rem 1.3rem; margin:1.5rem 0; font-family:system-ui,sans-serif;
              font-size:.95rem; }}
  .keyfind b {{ color:var(--accent); }}
  table {{ width:100%; border-collapse:collapse; margin:1.5rem 0; font-size:.9rem;
           font-family:system-ui,sans-serif; }}
  th,td {{ padding:.5rem .7rem; border-bottom:1px solid var(--line); text-align:left; }}
  th {{ background:#f3f3f8; }}
  code {{ background:#eee; padding:.1rem .35rem; border-radius:3px; font-size:.85em; }}
  .caveat {{ font-size:.9rem; color:var(--muted); border-left:3px solid var(--line);
             padding-left:1rem; }}
  footer {{ margin-top:4rem; padding:2rem 1.5rem; background:#1a1a2e; color:#a9adde;
            font-size:.85rem; font-family:system-ui,sans-serif; }}
</style>
</head>
<body>

<header>
  <div class="wrap">
    <h1>Talking Global</h1>
    <p class="sub">How KAIST's internationalization language led, decoupled from,
       and was displaced by reality, 2006–2025</p>
    <p class="meta">A digital-history text-mining study · HSS207/DHS211, KAIST Spring 2026<br>
       Corpus: 2,518 KAIST news articles (1.09M words) + 1,100 archived web pages +
       web-verified enrollment records</p>
  </div>
</header>

<main class="wrap">

  <div class="question">
    <strong>Research question.</strong> How did KAIST's institutional discourse around
    internationalization shift between 2006 and 2025 — and did the language of
    globalization in official communications <em>lead, track, or lag</em> actual
    international-enrollment growth?
  </div>

  <p>I came to KAIST as one of the international students this institution says it
  wants. That personal stake prompted a simple historical question: when KAIST
  talks about being "global," is it describing something that exists, predicting
  something it hopes to build, or performing an identity for an external audience?
  Institutional web pages and press releases are not neutral records — they are
  acts of self-presentation. Read as primary historical sources, they let us test
  whether the <em>language</em> of internationalization moved with the <em>reality</em>
  of it.</p>

  <div class="thesis">
    <strong>Argument.</strong> KAIST's internationalization language was driven by
    <strong>leadership and policy moments, not by enrollment</strong>. It peaked early
    (2008–2010, around the ICU merger and the "World-Class University" presidency),
    stayed <strong>decoupled</strong> from actual international-student numbers — most
    visibly holding flat while enrollment <em>fell</em> during COVID — and was
    ultimately <strong>displaced by an AI / entrepreneurship agenda</strong>. The
    branding led reality in timing and never synchronized with it.
  </div>

  <h2><span class="n">01 · METHOD</span>The data and how it was read</h2>
  <p>The primary corpus is <b>2,518 English-language articles</b> (1.09 million words)
  scraped from the KAIST News Center, spanning 2004–2026. A secondary corpus of ~1,100
  archived pages from the Wayback Machine (1997–2026) supplies the institutional web
  structure. International-enrollment figures were drawn from KAIST's International
  Office, official admission guides, and Wikipedia, then <b>independently
  re-verified against the live sources</b> — a step that corrected two material errors
  (see &sect;7).</p>
  <p>The method is <b>normalized term-frequency analysis</b>: for each year I count
  mentions of grouped internationalization terms and divide by total words, giving a
  rate per 1,000 words that is comparable across years of very different volume. Terms
  are grouped (<code>global</code>, <code>international</code>, <code>world-class</code>,
  <code>ranking</code>, <code>AI</code>, <code>entrepreneurship</code>, &hellip;) and
  correlated against enrollment, policy events, and presidential tenures.</p>

  <h2><span class="n">02 · METHODOLOGICAL TURN</span>The obvious answer is wrong</h2>
  <p>Run naively over the whole corpus, the data seems to deliver a dramatic result:
  the word "international" correlates <em>negatively</em> with enrollment (Pearson
  <b>r = &minus;0.61</b>) — language falls as students arrive. It is tempting to call
  this proof of hollow early branding. <b>It is mostly an artifact.</b></p>
  <p>The KAIST News Center changed character over time: research press releases grew
  from ~25% of articles (2006–09) to ~85% (2018–26). As science stories flood the
  corpus, every institutional-branding term is mechanically diluted regardless of
  intent. Restricting to <b>institutional (non-research) articles</b> — comparing like
  with like — collapses the correlation to <b>r = &minus;0.05</b>, essentially zero.</p>
  {img("06_confound_full_vs_institutional.png", "The naive decline (grey) is mostly corpus drift; the genre-controlled series (red) is flat.")}
  <div class="keyfind">
    <b>Key finding.</b> The headline correlation was a measurement artifact. This is
    itself the methodological contribution: in institutional text mining, corpus
    <em>composition</em> can masquerade as historical <em>change</em>. Every result
    below uses the genre-controlled corpus.
  </div>

  <h2><span class="n">03 · POLICY, NOT ENROLLMENT</span>Language tracks power, not students</h2>
  <p>Genre-controlled, "international" does not trend with enrollment — it
  <b>spikes on events</b>. Its peak year is <b>2009</b>, the ICU merger; "world-class"
  peaks in <b>2006</b>, the inauguration of the MIT-trained president Suh Nam-pyo and
  his "World-Class University" drive. The language of internationalization is the
  language of institutional <em>moments</em>, not of a growing student body.</p>
  {img("01_term_frequency_trends.png", "Branding terms over time (genre-controlled), with policy events marked. 'international' and 'world-class' spike on leadership/structural events.")}

  <h2><span class="n">04 · THE ARGUMENT CHART</span>Language vs. reality</h2>
  <p>Placing language and enrollment on the same timeline makes the decoupling visible.
  "international" (red) peaks early and stays episodic and flat. Actual enrollment
  (black) climbs steadily a decade <em>later</em>. Only "global" (blue) rises with the
  student body in the 2020s — and as &sect;6 shows, even that is entangled with a
  different agenda.</p>
  {img("03_language_vs_enrollment.png", "Dual axis: 'international' language peaks early and decouples; enrollment grows later; 'global' rises with enrollment in the 2020s.")}
  {img("02_enrollment_growth.png", "International enrollment with confidence-coded data points. Note the verified COVID dip from 1,027 (2019) to 817 (2021).")}

  <h2><span class="n">05 · NATURAL EXPERIMENT</span>COVID: when reality fell and language didn't</h2>
  <p>The pandemic provides a clean test. Verified records show international enrollment
  <b>fell from 1,027 (2019) to 817 (2021)</b> — a ~16% contraction. If language tracked
  reality, branding should have softened. It did not.</p>
  <table>
    <tr><th>Phase</th><th>Intl enrollment</th><th>"international" /1k</th><th>"global" /1k</th></tr>
    <tr><td>Pre-COVID (2018–19)</td><td>1,027</td><td>1.25</td><td>3.52</td></tr>
    <tr><td>COVID (2020–21)</td><td>868</td><td>1.14</td><td>3.51</td></tr>
    <tr><td>Recovery (2022–23)</td><td>1,200</td><td>1.94</td><td>7.11</td></tr>
  </table>
  <p>Branding language was <b>sticky</b> — flat through the contraction. KAIST did not
  talk less "global" when it became, briefly, less global. Language is decoupled from
  reality not just in timing but in direction.</p>

  <h2><span class="n">06 · DISPLACEMENT</span>What replaced internationalization</h2>
  <p>The falling internationalization line is not decline into silence — it is
  <b>agenda replacement</b>. Near-absent before 2013, AI and entrepreneurship language
  climbs steeply and overtakes the internationalization bundle around 2020–2022. The
  institution's promotional energy migrated from "global" to "AI."</p>
  {img("04_topical_displacement.png", "The internationalization bundle gives way to an AI + entrepreneurship bundle, crossing over around 2020.")}

  <h2><span class="n">07 · LEADERSHIP</span>Each president, a signature word</h2>
  <p>Mapping terms onto presidential tenures shows discourse is steered from the top.
  Suh (2006–12) owns "world-class" and "international"; Kang (2013–16) owns "ranking";
  under Shin (2017–20) "AI" arrives; Lee (2021–25) owns "global," "AI," and
  "entrepreneurship" together. Internationalization language is an instrument of
  presidential agenda-setting.</p>
  {img("05_presidential_eras.png", "Mean term frequency by president. Each administration has a distinct signature term.")}

  <h2><span class="n">08 · LENS</span>Huntington and the performance of "global"</h2>
  <p>Samuel Huntington's <em>The Clash of Civilizations</em> argues that civilizational
  identity, not ideology, organizes the post–Cold War world. KAIST's "global" project
  can be read as an attempt to operate <em>across</em> those boundaries — recruiting
  from 100+ countries, teaching in English. But the data complicate the optimistic
  reading. The vocabulary KAIST actually amplifies is the vocabulary of Western-defined
  excellence — rankings, world-class status, innovation, AI. On Huntington's terms this
  looks less like transcending civilizational boundaries than <b>assimilating to one
  civilization's metrics of prestige</b>. "Global," here, names a direction of
  alignment, not a dissolution of difference.</p>

  <h2><span class="n">09 · CRITICAL REFLECTION</span>What the data cannot show</h2>
  <ul>
    <li><b>Self-presentation only.</b> News and web copy are institutional speech; they
      reveal what KAIST chose to broadcast, not internal deliberation or lived
      experience.</li>
    <li><b>English-only scope.</b> Korean-language pages were excluded, so this measures
      the outward-facing, foreigner-directed register — appropriate for a branding
      question, but a real limit on generality.</li>
    <li><b>Estimated enrollment.</b> Only a handful of enrollment points are
      high-confidence; the rest are interpolated. Verification corrected the 2021 figure
      (1,100&nbsp;&rarr;&nbsp;<b>817</b>) and 2019 (1,050&nbsp;&rarr;&nbsp;<b>1,027</b>),
      but the curve remains partly modeled.</li>
    <li><b>Archive survivorship.</b> Wayback coverage is uneven (2009 retains only two
      pages); sparse early HTML reflects 1990s web technology, <em>not</em> a domestic
      orientation.</li>
    <li><b>Small n.</b> Twenty yearly observations make correlations suggestive, not
      statistically decisive.</li>
  </ul>

  <h2><span class="n">10 · CONVERSATION</span>Where this could go next</h2>
  <p>Three extensions invite other researchers: (1) add the Korean-language corpus to
  compare inward vs. outward registers; (2) apply the same genre-control method to peer
  institutions (SNU, POSTECH) to test whether "branding leads reality" is a KAIST trait
  or a Korean-higher-education pattern; (3) trace the AI-displacement finding forward as
  a study of how universities serially rebrand. The corpus and scripts are reusable for
  all three.</p>

</main>

<footer>
  <div class="wrap">
    KAIST Digital History Project · Spring 2026 · Method: Python text mining
    (term-frequency, genre-controlled corpus, event &amp; correlation analysis) ·
    All figures generated from the project's own scraped and verified data.
  </div>
</footer>

</body>
</html>"""


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HTML)
    size = os.path.getsize(OUT) / 1024
    print(f"Wrote {OUT} ({size:.0f} KB, self-contained)")
