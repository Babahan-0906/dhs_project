"""
05_build_interactive.py — KAIST Digital History Project

Builds the interactive byproduct as TWO self-contained pages (Chart.js inlined,
offline-portable):
  - output/index.html    the themed essay + argument charts
  - output/explore.html  a build-your-own-chart data dashboard

Both share a live THEME SWITCHER (Editorial / Data-journalism / KAIST) that
re-skins the page and recolors charts instantly. Re-run after 02 / 02c.
"""

import csv
import json
import os

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL_CSV  = os.path.join(ROOT, "output/term_frequency_by_year.csv")
INST_CSV  = os.path.join(ROOT, "output/term_frequency_institutional.csv")
HTMLNAV   = os.path.join(ROOT, "output/html_nav_structure_by_year.csv")
ENROLL    = os.path.join(ROOT, "data/enrollment/kaist_intl_enrollment.csv")
CHARTJS   = os.path.join(ROOT, "scripts/vendor/chart.umd.min.js")
OUT_INDEX = os.path.join(ROOT, "output/index.html")
OUT_EXPL  = os.path.join(ROOT, "output/explore.html")

KEY_EVENTS = {
    2006: "Suh pres. (World-Class)", 2009: "ICU merger",
    2013: "Study Korea / Kang pres.", 2017: "Shin pres.",
    2019: "AI Grad School", 2021: "Lee pres. / COVID",
}

ALL_TERMS = ["international", "global", "world_class", "diversity", "ranking",
             "innovation", "excellence", "collaboration", "foreign_students",
             "english", "ai", "entrepreneurship"]


# ─── data helpers ────────────────────────────────────────────────────────────

def load_freq(path):
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[int(r["year"])] = {k: (float(v) if k != "year" else int(v))
                                   for k, v in r.items()}
    return out


def smooth(vals, window=3):
    out, half = [], window // 2
    for i in range(len(vals)):
        lo, hi = max(0, i - half), min(len(vals), i + half + 1)
        out.append(sum(vals[lo:hi]) / (hi - lo))
    return out


def pts(years, raw):
    sm = smooth(raw)
    return [{"x": y, "y": round(s, 3), "r": round(rr, 3)}
            for y, s, rr in zip(years, sm, raw)]


def term_pts(freq, term, years):
    return pts(years, [freq[y][f"{term}_per1000"] for y in years])


def load_enrollment(min_year=None):
    rows = []
    with open(ENROLL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = r["total_international_students"]
            if v and v.isdigit():
                y = int(r["year"])
                if min_year is None or y >= min_year:
                    rows.append({"x": y, "y": int(v), "c": r["confidence"]})
    return rows


def load_nav():
    """Read 02b nav-structure CSV → presence points for the dot-grid.
    Row order (y-index): admissions, exchange, global, international (intl on top)."""
    order = ["admissions", "exchange", "global", "international"]
    points = []
    with open(HTMLNAV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            yr = int(r["year"])
            if yr < 2003:
                continue
            for i, term in enumerate(order):
                if r.get(f"nav_{term}", "0") == "1":
                    points.append({"x": yr, "y": i})
    return {"labels": order, "points": points}


def build_index_data():
    inst, full = load_freq(INST_CSV), load_freq(FULL_CSV)
    years = sorted(inst)

    def bundle(freq, terms):
        return pts(years, [sum(freq[y][f"{t}_per1000"] for t in terms) for y in years])

    eras = [[2006, 2012], [2013, 2016], [2017, 2020], [2021, 2025]]
    era_terms = ["international", "global", "ranking", "ai", "entrepreneurship"]
    era_values = {t: [round(sum(inst[y][f"{t}_per1000"] for y in range(a, b + 1) if y in inst)
                             / len([y for y in range(a, b + 1) if y in inst]), 3)
                      for a, b in eras] for t in era_terms}

    return {
        "events": KEY_EVENTS,
        "terms": {t: term_pts(inst, t, years)
                  for t in ["international", "global", "ranking", "world_class"]},
        "enroll_all": load_enrollment(),
        "enroll_recent": load_enrollment(min_year=2005),
        "dual": {"international": term_pts(inst, "international", years),
                 "global": term_pts(inst, "global", years)},
        "displace": {"intl": bundle(full, ["international", "global", "foreign_students"]),
                     "ai": bundle(full, ["ai", "entrepreneurship"])},
        "confound": {"full": term_pts(full, "international", years),
                     "inst": term_pts(inst, "international", years)},
        "eras": [{"name": n} for n in ["Suh '06–12", "Kang '13–16",
                                       "Shin '17–20", "Lee '21–25"]],
        "era_terms": era_terms, "era_values": era_values,
        "nav": load_nav(),
    }


def build_explore_data():
    inst, full = load_freq(INST_CSV), load_freq(FULL_CSV)
    years = sorted(inst)
    return {
        "years": years,
        "events": KEY_EVENTS,
        "terms": ALL_TERMS,
        "full": {t: [round(full[y][f"{t}_per1000"], 3) for y in years] for t in ALL_TERMS},
        "inst": {t: [round(inst[y][f"{t}_per1000"], 3) for y in years] for t in ALL_TERMS},
        "enroll": [{"x": r["x"], "y": r["y"]} for r in load_enrollment(min_year=2006)],
    }


# ─── shared theme + helper JS ────────────────────────────────────────────────

THEME_JS = r"""
const THEMES = {
  editorial: {
    label:'Editorial',
    vars:{'--bg':'#faf8f3','--card':'#ffffff','--ink':'#1b1b19','--muted':'#6b6459',
          '--line':'#e7e1d6','--accent':'#14596b','--accent2':'#b5532e',
          '--headerbg':'linear-gradient(135deg,#123c47,#1d5b66)',
          '--headertext':'#f3efe6','--headersub':'#cfe0e2','--chip':'#eef3f2'},
    fontHead:"'Helvetica Neue','Segoe UI',system-ui,sans-serif",
    fontBody:"'Charter','Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif",
    charts:['#14596b','#b5532e','#4f7a4f','#c08a2e','#5b6b7a','#7d5a6f','#2f7e8c','#9c6b3f'],
    grey:'#bcb6aa', ink:'#1b1b19'
  },
  data: {
    label:'Data-journalism',
    vars:{'--bg':'#f7f8fa','--card':'#ffffff','--ink':'#111418','--muted':'#5c6571',
          '--line':'#e3e6eb','--accent':'#3a4f7a','--accent2':'#c0392b',
          '--headerbg':'linear-gradient(135deg,#1f2937,#374151)',
          '--headertext':'#f5f7fa','--headersub':'#c2c9d6','--chip':'#eef1f6'},
    fontHead:"'Inter','Segoe UI',system-ui,sans-serif",
    fontBody:"'Inter','Segoe UI',system-ui,sans-serif",
    charts:['#c0392b','#34495e','#7f8c8d','#16a085','#2c3e50','#8e6fa1','#95a5a6','#d98c00'],
    grey:'#aeb4bd', ink:'#111418'
  },
  kaist: {
    label:'KAIST',
    vars:{'--bg':'#f4f7fa','--card':'#ffffff','--ink':'#0a1a2f','--muted':'#5a6b82',
          '--line':'#dce6ef','--accent':'#004191','--accent2':'#e08a1e',
          '--headerbg':'linear-gradient(135deg,#002d6b,#004191)',
          '--headertext':'#eef4fb','--headersub':'#a9c4e0','--chip':'#e7eff7'},
    fontHead:"'Helvetica Neue','Segoe UI',system-ui,sans-serif",
    fontBody:"Georgia,'Times New Roman',serif",
    charts:['#004191','#00a0c6','#2a9d8f','#e08a1e','#5a6b82','#9b5d7a','#3f72af','#c1654a'],
    grey:'#a8b8c8', ink:'#0a1a2f'
  }
};
let CURTHEME = THEMES.editorial;
const ORDER = ['international','global','ranking','world_class','ai','entrepreneurship',
               'english','diversity','innovation','excellence','collaboration','foreign_students'];
function cof(term){ const i=ORDER.indexOf(term); return CURTHEME.charts[(i<0?0:i)%CURTHEME.charts.length]; }
function setTheme(name){
  const t=THEMES[name]; if(!t) return; CURTHEME=t;
  const r=document.documentElement.style;
  Object.entries(t.vars).forEach(([k,v])=>r.setProperty(k,v));
  r.setProperty('--font-head',t.fontHead); r.setProperty('--font-body',t.fontBody);
  try{localStorage.setItem('dh_theme',name);}catch(e){}
  document.querySelectorAll('.theme-btn').forEach(b=>b.classList.toggle('on',b.dataset.t===name));
  if(window.rebuildCharts) window.rebuildCharts();
}
window.addEventListener('DOMContentLoaded',()=>{
  let init='editorial'; try{init=localStorage.getItem('dh_theme')||'editorial';}catch(e){}
  setTheme(init);
});
const eventLines = { id:'eventLines',
  afterDraw(chart,a,opts){ const ev=opts && opts.milestones; if(!ev) return;
    const {ctx,chartArea:{top,bottom},scales:{x}}=chart; ctx.save();
    Object.entries(ev).forEach(([yr,label])=>{ const px=x.getPixelForValue(+yr);
      if(px<x.left||px>x.right) return;
      ctx.strokeStyle='rgba(120,120,120,.4)'; ctx.setLineDash([4,4]); ctx.lineWidth=1;
      ctx.beginPath(); ctx.moveTo(px,top); ctx.lineTo(px,bottom); ctx.stroke();
      ctx.setLineDash([]); ctx.fillStyle='rgba(110,110,110,.8)'; ctx.font='10px system-ui';
      ctx.save(); ctx.translate(px+3,top+4); ctx.rotate(Math.PI/2);
      ctx.textBaseline='middle'; ctx.fillText(label,0,0); ctx.restore(); });
    ctx.restore(); } };
Chart.register(eventLines);
const NICE={world_class:'world-class',foreign_students:'foreign students',
            ai:'AI',entrepreneurship:'entrepreneurship'};
const nm=t=>NICE[t]||t;
function jsSmooth(a,w){ if(!w) return a.slice(); const h=(w-1)/2, o=[];
  for(let i=0;i<a.length;i++){ let s=0,n=0;
    for(let j=Math.max(0,i-h);j<=Math.min(a.length-1,i+h);j++){s+=a[j];n++;} o.push(+(s/n).toFixed(3)); }
  return o; }
"""

SHARED_CSS = r"""
  :root { --bg:#faf8f3; --card:#fff; --ink:#1b1b19; --muted:#6b6459; --line:#e7e1d6;
          --accent:#14596b; --accent2:#b5532e; --headerbg:#1a1a2e; --headertext:#fff;
          --headersub:#ccc; --chip:#eee;
          --font-head:system-ui,sans-serif; --font-body:Georgia,serif; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:var(--font-body); color:var(--ink); background:var(--bg);
         line-height:1.7; }
  h1,h2,h3,.themebar,.meta,.cap,.hint,.keyfind,table,nav,button,label,.pill,.controls,select,
  .badge { font-family:var(--font-head); }
  header { background:var(--headerbg); color:var(--headertext); padding:3rem 1.5rem 2.4rem; }
  .wrap { max-width:900px; margin:0 auto; padding:0 1.5rem; }
  h1 { font-size:2.3rem; line-height:1.15; margin:0 0 .5rem; letter-spacing:-.01em; }
  .sub { font-size:1.08rem; color:var(--headersub); font-style:italic; margin:0; }
  .meta { margin-top:1.2rem; font-size:.82rem; color:var(--headersub); }
  nav.top { margin:1.2rem 0 0; display:flex; gap:1rem; align-items:center; flex-wrap:wrap; }
  nav.top a { color:var(--headertext); text-decoration:none; border:1px solid rgba(255,255,255,.4);
              padding:.35rem .8rem; border-radius:20px; font-size:.85rem; }
  nav.top a:hover { background:rgba(255,255,255,.12); }
  .themebar { display:flex; gap:.4rem; align-items:center; font-size:.8rem;
              color:var(--headersub); }
  .theme-btn { cursor:pointer; border:1px solid rgba(255,255,255,.35); background:transparent;
               color:var(--headertext); padding:.3rem .7rem; border-radius:20px; font-size:.8rem; }
  .theme-btn.on { background:var(--headertext); color:#222; font-weight:600; }
  h2 { font-size:1.55rem; margin:3rem 0 .3rem; padding-top:1rem; border-top:2px solid var(--line); }
  h2 .n { color:var(--accent2); font-size:.95rem; display:block; letter-spacing:.1em; }
  p { margin:.8rem 0; } a { color:var(--accent); }
  .question { background:var(--card); border-left:5px solid var(--accent2);
              padding:1.2rem 1.5rem; margin:2rem 0; font-size:1.12rem;
              box-shadow:0 2px 12px rgba(0,0,0,.05); }
  .thesis { background:var(--accent); color:#fff; padding:1.4rem 1.7rem; border-radius:8px;
            margin:2rem 0; font-size:1.08rem; }
  .thesis strong { color:#fff; text-decoration:underline; text-decoration-color:var(--accent2);
                   text-underline-offset:3px; }
  .note { font-size:.88rem; background:var(--chip); border-radius:6px; padding:.7rem 1rem; }
  .chartbox { background:var(--card); border:1px solid var(--line); border-radius:8px;
              padding:1rem 1.2rem 1.3rem; margin:2rem 0; box-shadow:0 2px 12px rgba(0,0,0,.04); }
  .cap { font-size:.83rem; color:var(--muted); margin:.6rem 0 0; font-style:italic; }
  .hint { font-style:normal; color:#9a9a9a; }
  .canvas-h { position:relative; height:420px; }
  .keyfind { background:var(--chip); border:1px solid var(--line); border-radius:6px;
             padding:1rem 1.3rem; margin:1.5rem 0; font-size:.95rem; }
  .keyfind b { color:var(--accent2); }
  table { width:100%; border-collapse:collapse; margin:1.5rem 0; font-size:.9rem; }
  th,td { padding:.5rem .7rem; border-bottom:1px solid var(--line); text-align:left; }
  th { background:var(--chip); }
  ul { padding-left:1.2rem; }
  footer { margin-top:4rem; padding:2rem 1.5rem; background:var(--headerbg);
           color:var(--headersub); font-size:.82rem; }
"""


def header_block(title, sub, meta, here):
    other = ("explore.html", "Explore the data →") if here == "index" else \
            ("index.html", "← Back to the essay")
    return f"""
<header>
  <div class="wrap">
    <h1>{title}</h1>
    <p class="sub">{sub}</p>
    <nav class="top">
      <a href="{other[0]}">{other[1]}</a>
      <span class="themebar">Theme:
        <button class="theme-btn" data-t="editorial" onclick="setTheme('editorial')">Editorial</button>
        <button class="theme-btn" data-t="data" onclick="setTheme('data')">Data-journalism</button>
        <button class="theme-btn" data-t="kaist" onclick="setTheme('kaist')">KAIST</button>
      </span>
    </nav>
    <p class="meta">{meta}</p>
  </div>
</header>"""


# ─── INDEX page ──────────────────────────────────────────────────────────────

def build_index(chartjs):
    data = json.dumps(build_index_data())
    head = header_block(
        "Talking Global",
        "How KAIST's internationalization language led, decoupled from, and was displaced by reality, 2006–2025",
        "An interactive digital-history text-mining study · HSS207/DHS211, KAIST Spring 2026 · "
        "Corpus: 2,518 KAIST news articles (1.09M words) + 1,100 archived pages + verified enrollment",
        "index")

    body = r"""
<main class="wrap">
  <div class="question"><strong>Research question.</strong> How did KAIST's internationalization
  language in official communications shift between 2006 and 2025, and did it <em>lead, track, or
  lag</em> the actual growth of international student enrollment?</div>

  <p>KAIST's polished "global" image influenced my decision to study here. That personal interest
  raised a historical question: when KAIST describes itself as "global," is the language describing a
  reality, anticipating one, or presenting an identity to an external audience? Institutional web pages
  and press releases are not neutral records; they are acts of self-presentation. Read as primary
  sources, they allow a direct test of whether the language of internationalization moved with the
  reality of it.</p>

  <p class="note"><b>This page is interactive.</b> Switch the theme above, hover any chart for exact
  values, and click a legend entry to show or hide a line. Dotted verticals mark policy events. To
  query the data yourself, <a href="explore.html">open the explorer</a>.</p>

  <div class="thesis"><strong>Argument.</strong> KAIST's internationalization language was driven more
  by <strong>leadership and policy initiatives than by enrollment</strong>. It peaked early (2008–2010,
  around the 2009 ICU merger and the "World-Class University" presidency), remained
  <strong>decoupled</strong> from actual international-student numbers — it held roughly flat even as
  enrollment fell during COVID — and was later <strong>displaced by an AI and entrepreneurship
  agenda</strong>. The language ran ahead of the reality and did not synchronize with it.</div>

  <h2><span class="n">01 · METHOD</span>The data and how it was read</h2>
  <p>The primary corpus is <b>2,518 English-language articles</b> (1.09 million words) scraped
  from the KAIST News Center, 2004–2026. A secondary corpus of ~1,100 archived Wayback Machine
  pages (1997–2026) documents the institutional web structure. Enrollment figures from KAIST's
  International Office, admission guides, and Wikipedia were <b>independently re-verified
  against live sources</b>, which corrected two errors (see &sect;10). The method is
  <b>normalized term-frequency analysis</b>: mentions per 1,000 words, comparable across
  years. Lines are 3-year smoothed; hover for the raw yearly value.</p>

  <h2><span class="n">02 · METHODOLOGICAL TURN</span>The naive result is an artifact</h2>
  <p>Run over the whole corpus, "international" correlates <em>negatively</em> with enrollment
  (Pearson <b>r = &minus;0.61</b>). This appears to show hollow branding, but it is largely an
  artifact. Research press releases grew from ~25% of articles (2006–09) to ~85% (2018–26); as
  research coverage increases, every branding term is mechanically diluted. Restricting the analysis
  to <b>institutional (non-research) articles</b> reduces the correlation to <b>r = &minus;0.05</b>,
  effectively zero.</p>
  <div class="chartbox"><div class="canvas-h"><canvas id="cConfound"></canvas></div>
    <p class="cap">The naive decline (grey) is largely corpus drift; the genre-controlled
    series is flat. <span class="hint">Hover for raw values; click legend to toggle.</span></p></div>
  <div class="keyfind"><b>Key finding.</b> The headline correlation was a measurement artifact.
  That is itself the contribution: in institutional text mining, corpus <em>composition</em>
  can be mistaken for historical <em>change</em>. Every result below uses the genre-controlled corpus.</div>

  <h2><span class="n">03 · POLICY, NOT ENROLLMENT</span>Language follows policy, not enrollment</h2>
  <p>In the genre-controlled corpus, "international" does not trend with enrollment; it spikes on
  specific events. Its highest year is <b>2009</b> (the ICU merger), and "world-class" peaks in
  <b>2006</b>, the year MIT-trained president Suh Nam-pyo took office and launched his "World-Class
  University" initiative.</p>
  <div class="chartbox"><div class="canvas-h"><canvas id="cTerms"></canvas></div>
    <p class="cap">Branding terms over time (genre-controlled). Dotted lines mark policy events.
    <span class="hint">Click legend to toggle.</span></p></div>

  <h2><span class="n">04 · THE ARGUMENT CHART</span>Language versus reality</h2>
  <p>Placed on one timeline, the decoupling is clear. "international" (left axis) peaks early and
  stays flat, while actual enrollment (right axis) rises about a decade later. Only "global" rises
  with the student body in the 2020s, and as &sect;6 shows, that increase coincides with a different
  agenda.</p>
  <div class="chartbox"><div class="canvas-h"><canvas id="cDual"></canvas></div>
    <p class="cap">Dual axis: language (left) vs. international enrollment (right).</p></div>
  <div class="chartbox"><div class="canvas-h"><canvas id="cEnroll"></canvas></div>
    <p class="cap">Enrollment; points colour-coded by source confidence (green = verified,
    amber = medium, red = estimated). The verified COVID dip runs 1,027 (2019) → 817 (2021).</p></div>

  <h2><span class="n">05 · NATURAL EXPERIMENT</span>COVID: enrollment fell, language did not</h2>
  <p>Verified records show international enrollment <b>fell from 1,027 (2019) to 817 (2021)</b>, a
  contraction of about 16%. If the language tracked reality, the branding should have softened. It
  did not.</p>
  <table><tr><th>Phase</th><th>Intl enrollment</th><th>"international" /1k</th><th>"global" /1k</th></tr>
    <tr><td>Pre-COVID (2018–19)</td><td>1,027</td><td>1.25</td><td>3.52</td></tr>
    <tr><td>COVID (2020–21)</td><td>868</td><td>1.14</td><td>3.51</td></tr>
    <tr><td>Recovery (2022–23)</td><td>1,200</td><td>1.94</td><td>7.11</td></tr></table>
  <p>The branding language was stable through the contraction. KAIST did not reduce its "global"
  language when it became, briefly, less global.</p>

  <h2><span class="n">06 · DISPLACEMENT</span>What replaced internationalization</h2>
  <p>The decline in internationalization language is not a move into silence but a change of agenda.
  AI and entrepreneurship language is near-absent before 2013, then rises steeply and overtakes the
  internationalization bundle around 2020–2022.</p>
  <div class="chartbox"><div class="canvas-h"><canvas id="cDisplace"></canvas></div>
    <p class="cap">Internationalization bundle vs. AI + entrepreneurship bundle (full corpus).</p></div>

  <h2><span class="n">07 · LEADERSHIP</span>Each president, a signature term</h2>
  <p>Mapped onto presidential tenures, the discourse is clearly directed from the top. Suh emphasizes
  "world-class" and "international"; Kang emphasizes "ranking"; "AI" appears under Shin; and Lee
  emphasizes "global," "AI," and "entrepreneurship" together.</p>
  <div class="chartbox"><div class="canvas-h"><canvas id="cEras"></canvas></div>
    <p class="cap">Mean term frequency by president (institutional corpus).
    <span class="hint">Click legend entries to compare terms.</span></p></div>

  <h2><span class="n">08 · ROBUSTNESS</span>A second source: the web archive</h2>
  <p>The findings so far rest on the news corpus. An independent source allows a different check on the
  timing: ~1,100 of KAIST's own pages, captured by the Internet Archive's Wayback Machine (1997–2026).
  Counting words in this uneven, partly-sampled archive would be noisy, so I ask a question that is
  robust to sampling: <b>did internationalization terms appear in the site's navigation menu that
  year?</b> A navigation-menu item is a deliberate structural choice rather than a turn of phrase; it is
  either present or absent.</p>
  <div class="chartbox"><div class="canvas-h"><canvas id="cNav"></canvas></div>
    <p class="cap">A marker = the term appeared in KAIST's English-site navigation that year (Wayback
    corpus). <span class="hint">"international" and "global" appear from 2009–2010 and do not disappear.</span></p></div>
  <p>The pattern is consistent. Across 2004–2007, years with reasonable captures (18–28 pages each),
  internationalization terms are <b>absent</b> from the menu. From <b>2009–2010</b> they appear and
  remain. (The single surviving 2009 page already shows them, and the denser 2010 capture of 41 pages
  confirms it.) A second, independent source therefore dates the <b>structural</b> institutionalization
  of internationalization to the ICU-merger period, the same point at which the news language peaks. The
  admissions-page text shows the same pattern qualitatively, with "international" dominant in the 2010s
  before "global" overtakes it in the 2020s, though that slice is too sparse to rely on numerically.</p>

  <h2><span class="n">09 · LENS</span>Huntington and the "Davos veneer"</h2>
  <p>Samuel Huntington's <em>The Clash of Civilizations</em> (1996) provides the theoretical frame.
  Two of his arguments apply here. First, <b>modernization is not the same as Westernization</b>:
  non-Western societies can become modern while remaining culturally distinct. Second, the
  cosmopolitan, English-speaking, globally-mobile elite he calls the <b>"Davos Culture"</b> is, in
  Václav Havel's words (which Huntington endorses), "no more than a thin veneer" over deeper, persistent
  cultures. Huntington places Korea in the <em>Sinic</em> civilization, so KAIST's Western-style
  internationalization is a cross-civilizational move.</p>
  <p>This reframes the question in civilizational terms: when KAIST says "global," is it transcending
  civilizational boundaries or aligning with one civilization's standards of prestige? The data
  indicate alignment. The vocabulary KAIST amplifies is that of Western-defined excellence (QS/THE
  rankings, "world-class" status, English-only instruction, and now AI). That language is also stable and
  decoupled from reality, as the COVID period shows: a polished global self-presentation over a lived
  reality that, by international students' own accounts, does not always match it.</p>
  <p>The data therefore <b>confirm and measure</b> Huntington's veneer thesis, and extend it. The
  discourse is directed from the top by Western-educated leadership (the institutional counterpart of
  his Western-facing "torn" elites; our analogy, not his term); the veneer grows over time; and
  "international" gives way to "AI." Meanwhile the <em>indigenization</em> Huntington expected of
  modernizing non-Western societies (a reassertion of indigenous identity) is largely <b>absent</b>
  from KAIST's public-facing English discourse.</p>

  <h2><span class="n">10 · CRITICAL REFLECTION</span>What the data cannot show</h2>
  <ul>
    <li><b>Self-presentation only.</b> Institutional speech reveals what KAIST chose to
      broadcast, not internal deliberation or lived experience.</li>
    <li><b>English-only scope.</b> Korean pages were excluded; this measures the outward,
      foreigner-directed register.</li>
    <li><b>Estimated enrollment.</b> Few points are high-confidence; the rest interpolated.
      Verification corrected 2021 (1,100&nbsp;&rarr;&nbsp;<b>817</b>) and 2019
      (1,050&nbsp;&rarr;&nbsp;<b>1,027</b>), but the curve remains partly modeled.</li>
    <li><b>Archive survivorship.</b> Wayback coverage is uneven (2009 retains two pages);
      sparse early HTML reflects 1990s web technology, not domestic orientation.</li>
    <li><b>Small n.</b> Twenty yearly observations make correlations suggestive, not decisive.</li>
  </ul>

  <h2><span class="n">11 · CONVERSATION</span>Where this could go next</h2>
  <p>Three extensions invite other researchers: (1) add the Korean-language corpus to compare
  inward vs. outward registers; (2) apply the same genre-control method to the other three
  Korean science-and-technology institutes (UNIST, DGIST, GIST) to test whether "branding
  leads reality" is a KAIST trait or a sector-wide playbook; (3) trace the AI-displacement
  finding forward as serial institutional rebranding. The corpus, scripts, and
  <a href="explore.html">interactive explorer</a> are reusable for all three.</p>

  <h2><span class="n">12 · AI DISCLOSURE</span>Statement on the Use of generative AI</h2>
  <p>In accordance with course guidelines, this project utilized generative AI tools to assist in the research, development, and design process. Below is the disclosure of the specific tools, models, and workflows employed:</p>
  <ul>
    <li><b>Tools and Models:</b> Anthropic's Claude (via Claude Code, Opus/Sonnet) for data collection scripts, analysis, and visualization iteration; OpenAI's ChatGPT for grammar and readability improvements; and Google's Gemini for script debugging and initial drafting.</li>
    <li><b>Iterative Prompting Workflow:</b> The AI assistants were used under close human direction in an iterative, conversational loop. Core research questions, arguments, and historical interpretations remained entirely human-driven. Proposed scripts and arguments were continuously tested, audited, and corrected rather than accepted verbatim.</li>
    <li><b>Critical Refinement:</b> The most significant use of AI was in pressure-testing conclusions. By asking the assistant to identify analytical weaknesses, the negative correlation artifact (genre drift) was uncovered, prompting the implementation of the genre-control methodology.</li>
    <li><b>Design and Implementation:</b> The assistant assisted in visual design choices (color palettes, interactive CSS theming) and helped structure the frontend elements of this interactive essay.</li>
    <li><b>Fact Verification:</b> All critical data, such as enrollment figures and references to Huntington's text, were independently verified against primary resources to ensure empirical accuracy.</li>
  </ul>
</main>

<footer><div class="wrap">KAIST Digital History Project · Spring 2026 · Python text mining
(genre-controlled term-frequency, event &amp; correlation analysis) · Interactive charts via
Chart.js · All figures from the project's own scraped and verified data.</div></footer>
"""

    script = r"""
<script>/*__CHARTJS__*/</script>
<script>/*__THEME__*/</script>
<script>
const DATA = /*__DATA__*/;
const CH = {};
const rawTip = { callbacks:{ label:c=>{ const r=c.raw.r;
  return ` ${c.dataset.label}: ${c.parsed.y} /1k` + (r!==undefined?` (raw ${r})`:''); }}};
function baseLine(events){ return { responsive:true, maintainAspectRatio:false,
  interaction:{mode:'nearest',intersect:false},
  scales:{ x:{type:'linear',ticks:{callback:v=>v,stepSize:2},title:{display:true,text:'Year'}},
           y:{title:{display:true,text:'mentions per 1,000 words'}} },
  plugins:{ legend:{position:'top'}, tooltip:rawTip,
            eventLines:{milestones:events?DATA.events:null} } }; }
const lineDS=(term,data,color)=>({ label:nm(term), data, borderColor:color||cof(term),
  backgroundColor:(color||cof(term))+'22', borderWidth:2.4, pointRadius:2.4,
  pointHoverRadius:5, tension:.25 });

function rebuildCharts(){
  Object.values(CH).forEach(c=>c.destroy());
  const CONF={high:'#3a8a4f',medium:'#d98c00',low:'#c0392b'};

  CH.confound=new Chart(cConfound,{type:'line',options:baseLine(false),data:{datasets:[
    {label:'full corpus (confounded)',data:DATA.confound.full,borderColor:CURTHEME.grey,
     borderDash:[6,5],borderWidth:2.4,pointRadius:2,tension:.25,backgroundColor:'transparent'},
    {label:'institutional only (controlled)',data:DATA.confound.inst,borderColor:cof('international'),
     borderWidth:2.6,pointRadius:2.4,tension:.25,backgroundColor:'transparent'}]}});

  const termsOpt=baseLine(true);
  CH.terms=new Chart(cTerms,{type:'line',options:termsOpt,
    data:{datasets:Object.keys(DATA.terms).map(t=>lineDS(t,DATA.terms[t]))}});

  CH.dual=new Chart(cDual,{type:'line',options:{responsive:true,maintainAspectRatio:false,
    interaction:{mode:'nearest',intersect:false},
    scales:{x:{type:'linear',min:2005,max:2026,ticks:{callback:v=>v,stepSize:2},title:{display:true,text:'Year'}},
            y:{position:'left',title:{display:true,text:'language /1,000 words'}},
            y1:{position:'right',grid:{drawOnChartArea:false},title:{display:true,text:'international students'}}},
    plugins:{legend:{position:'top'},tooltip:rawTip,eventLines:{milestones:DATA.events}}},
    data:{datasets:[ lineDS('international',DATA.dual.international),
      lineDS('global',DATA.dual.global),
      {label:'intl enrollment',data:DATA.enroll_recent,yAxisID:'y1',borderColor:CURTHEME.ink,
       borderWidth:2.6,borderDash:[7,4],pointRadius:3,pointHoverRadius:5,tension:.15,
       backgroundColor:'transparent'} ]}});

  CH.enroll=new Chart(cEnroll,{type:'line',options:{responsive:true,maintainAspectRatio:false,
    interaction:{mode:'nearest',intersect:false},
    scales:{x:{type:'linear',ticks:{callback:v=>v,stepSize:5},title:{display:true,text:'Year'}},
            y:{title:{display:true,text:'international students'},beginAtZero:true}},
    plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>` ${c.parsed.y} students (${c.raw.c}-confidence)`}},
      eventLines:{milestones:DATA.events}}},
    data:{datasets:[{label:'intl enrollment',data:DATA.enroll_all,borderColor:CURTHEME.grey,
      borderWidth:1.8,tension:.2,fill:false,pointRadius:6,pointHoverRadius:8,
      pointBackgroundColor:DATA.enroll_all.map(p=>CONF[p.c]||'#999'),pointBorderColor:'#fff'}]}});

  CH.displace=new Chart(cDisplace,{type:'line',options:baseLine(false),data:{datasets:[
    {label:'internationalization bundle',data:DATA.displace.intl,borderColor:cof('global'),
     backgroundColor:cof('global')+'22',borderWidth:2.6,fill:true,pointRadius:2,tension:.3},
    {label:'AI + entrepreneurship bundle',data:DATA.displace.ai,borderColor:cof('ai'),
     backgroundColor:cof('ai')+'22',borderWidth:2.6,fill:true,pointRadius:2,tension:.3}]}});

  CH.eras=new Chart(cEras,{type:'bar',options:{responsive:true,maintainAspectRatio:false,
    scales:{x:{title:{display:true,text:'president (tenure)'}},
            y:{title:{display:true,text:'mentions per 1,000 words'},beginAtZero:true}},
    plugins:{legend:{position:'top'},
      tooltip:{callbacks:{label:c=>` ${c.dataset.label}: ${c.parsed.y} /1k`}}}},
    data:{labels:DATA.eras.map(e=>e.name),
      datasets:DATA.era_terms.map(t=>({label:nm(t),data:DATA.era_values[t],backgroundColor:cof(t)}))}});

  CH.nav=new Chart(cNav,{type:'scatter',options:{responsive:true,maintainAspectRatio:false,
    interaction:{mode:'nearest',intersect:false},
    scales:{x:{type:'linear',min:2002,max:2027,ticks:{stepSize:2,callback:v=>v},
               title:{display:true,text:'Year'}},
            y:{min:-0.6,max:DATA.nav.labels.length-0.4,
               ticks:{stepSize:1,callback:v=>nm(DATA.nav.labels[v]||'')},grid:{color:'rgba(0,0,0,.05)'}}},
    plugins:{legend:{display:false},
      tooltip:{callbacks:{title:()=>'',label:c=>` "${nm(DATA.nav.labels[c.parsed.y])}" in nav menu — ${c.parsed.x}`}},
      eventLines:{milestones:{2009:'ICU merger'}}}},
    data:{datasets:[{data:DATA.nav.points,backgroundColor:cof('international'),
      pointRadius:8,pointHoverRadius:11,pointStyle:'rectRounded'}]}});
}
window.rebuildCharts=rebuildCharts;
</script>
"""
    page = ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>Talking Global — KAIST Internationalization Discourse, 2006–2025</title>"
            "<style>" + SHARED_CSS + "</style></head><body>"
            + head + body + script + "</body></html>")
    return (page.replace("/*__CHARTJS__*/", chartjs)
                .replace("/*__THEME__*/", THEME_JS)
                .replace("/*__DATA__*/", data))


# ─── EXPLORE page ────────────────────────────────────────────────────────────

def build_explore(chartjs):
    data = json.dumps(build_explore_data())
    head = header_block(
        "Explore the corpus",
        "Build your own chart from the KAIST internationalization dataset",
        "Pick any terms, choose the full or genre-controlled corpus, toggle smoothing and the "
        "enrollment overlay. Same data behind the essay — ask your own questions.",
        "explore")

    body = r"""
<main class="wrap">
  <p class="note">Select terms and options below; the chart updates live. The
  <b>genre-controlled (institutional)</b> corpus drops research press releases so years stay
  comparable; the <b>full</b> corpus includes everything, and shifts toward research coverage after
  ~2016. <a href="index.html">← Back to the argument</a></p>

  <div class="chartbox">
    <div id="termPills" class="controls" style="display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.8rem;"></div>
    <div class="controls" style="display:flex;flex-wrap:wrap;gap:1.4rem;align-items:center;
         margin-bottom:1rem;font-size:.9rem;">
      <span>Corpus:
        <label><input type="radio" name="corpus" value="inst" checked> genre-controlled</label>
        <label><input type="radio" name="corpus" value="full"> full</label></span>
      <label><input type="checkbox" id="smooth" checked> 3-yr smoothing</label>
      <label><input type="checkbox" id="overlay"> overlay enrollment</label>
      <button class="theme-btn" style="border-color:var(--accent);color:var(--accent)"
              onclick="clearAll()">clear all</button>
    </div>
    <div class="canvas-h" style="height:460px;"><canvas id="cExp"></canvas></div>
    <p class="cap">mentions per 1,000 words by year. <span class="hint">Click a term chip to
    add/remove it; click a legend entry to hide a line.</span></p>
  </div>

  <h2><span class="n">HOW TO READ</span>Suggested questions to try</h2>
  <ul>
    <li>Select <b>english</b> alone to see English-only-policy language decline after the Suh era.</li>
    <li>Compare <b>international</b> and <b>ai</b> on the full corpus to see the change in agenda.</li>
    <li>Switch <b>diversity</b> and <b>collaboration</b> between corpora to see how much the full
      corpus is inflated by research-partnership language.</li>
    <li>Overlay enrollment and add <b>global</b>, the one term that tracks the student curve.</li>
  </ul>
</main>
<footer><div class="wrap">KAIST Digital History Project · Spring 2026 · Explorer over the
genre-controlled and full news corpora · Chart.js.</div></footer>
"""

    script = r"""
<script>/*__CHARTJS__*/</script>
<script>/*__THEME__*/</script>
<script>
const D = /*__EXPLORE__*/;
const sel = new Set(['international','global']);
let chart=null;

function pills(){ const box=document.getElementById('termPills');
  box.innerHTML='';
  D.terms.forEach(t=>{ const b=document.createElement('button');
    b.className='theme-btn'; b.textContent=nm(t); b.dataset.t=t;
    if(sel.has(t)){ b.style.background=cof(t); b.style.borderColor=cof(t); b.style.color='#fff'; }
    else { b.style.background='transparent'; b.style.borderColor='var(--muted)'; b.style.color='var(--ink)'; }
    b.onclick=()=>{ sel.has(t)?sel.delete(t):sel.add(t); render(); };
    box.appendChild(b); }); }

function clearAll(){ sel.clear(); render(); }

function render(){
  pills();
  const corpus=document.querySelector('input[name=corpus]:checked').value;
  const sm=document.getElementById('smooth').checked;
  const ov=document.getElementById('overlay').checked;
  const w=sm?3:0;
  const ds=[...sel].map(t=>{ const raw=D[corpus][t];
    const ys=jsSmooth(raw,w).map((y,i)=>({x:D.years[i],y,r:raw[i]}));
    return {label:nm(t),data:ys,borderColor:cof(t),backgroundColor:cof(t)+'22',
            borderWidth:2.4,pointRadius:2.2,pointHoverRadius:5,tension:.25,yAxisID:'y'}; });
  if(ov) ds.push({label:'intl enrollment',data:D.enroll,yAxisID:'y1',borderColor:CURTHEME.ink,
    borderWidth:2.4,borderDash:[7,4],pointRadius:3,tension:.15,backgroundColor:'transparent'});
  const scales={ x:{type:'linear',ticks:{callback:v=>v,stepSize:2},title:{display:true,text:'Year'}},
    y:{title:{display:true,text:'mentions per 1,000 words'},beginAtZero:true} };
  if(ov) scales.y1={position:'right',grid:{drawOnChartArea:false},
    title:{display:true,text:'international students'}};
  if(chart) chart.destroy();
  chart=new Chart(cExp,{type:'line',data:{datasets:ds},options:{responsive:true,
    maintainAspectRatio:false,interaction:{mode:'nearest',intersect:false},scales,
    plugins:{legend:{position:'top'},eventLines:{milestones:D.events},
      tooltip:{callbacks:{label:c=>{const r=c.raw.r;
        return ` ${c.dataset.label}: ${c.parsed.y}`+(r!==undefined?` /1k (raw ${r})`:' students');}}}}}});
}
window.rebuildCharts=render;
['change'].forEach(ev=>document.addEventListener(ev,e=>{
  if(['corpus','smooth','overlay'].includes(e.target.name)||['smooth','overlay'].includes(e.target.id)) render();
}));
</script>
"""
    page = ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>Explore — KAIST Internationalization Corpus</title>"
            "<style>" + SHARED_CSS + "</style></head><body>"
            + head + body + script + "</body></html>")
    return (page.replace("/*__CHARTJS__*/", chartjs)
                .replace("/*__THEME__*/", THEME_JS)
                .replace("/*__EXPLORE__*/", data))


if __name__ == "__main__":
    chartjs = open(CHARTJS, encoding="utf-8").read()
    with open(OUT_INDEX, "w", encoding="utf-8") as f:
        f.write(build_index(chartjs))
    with open(OUT_EXPL, "w", encoding="utf-8") as f:
        f.write(build_explore(chartjs))
    print(f"Wrote {OUT_INDEX} ({os.path.getsize(OUT_INDEX)/1024:.0f} KB)")
    print(f"Wrote {OUT_EXPL} ({os.path.getsize(OUT_EXPL)/1024:.0f} KB)")
