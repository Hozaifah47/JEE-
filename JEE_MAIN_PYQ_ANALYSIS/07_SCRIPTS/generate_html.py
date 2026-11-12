#!/usr/bin/env python3
"""
generate_html.py — JEE Main PYQ Analysis System
Generates a full HTML dashboard from the question database and trend data.

Usage:
    python 07_SCRIPTS/generate_html.py
    python 07_SCRIPTS/generate_html.py --subject Physics
    python 07_SCRIPTS/generate_html.py --output-dir /custom/path
"""

import json
import csv
import sys
import argparse
import html
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ROOT   = Path(__file__).resolve().parent.parent
DATABASE_DIR   = PROJECT_ROOT / "03_DATABASE"
REPORTS_DIR    = PROJECT_ROOT / "04_MASTER_REPORTS"
ASSETS_DIR     = PROJECT_ROOT / "06_ASSETS"
LOG_DIR        = PROJECT_ROOT / "08_LOGS"

QUESTIONS_JSONL = DATABASE_DIR / "questions.jsonl"
CLUSTERS_FILE   = DATABASE_DIR / "clusters.json"
TAXONOMY_FILE   = DATABASE_DIR / "chapter_taxonomy.json"
TRENDS_FILE     = REPORTS_DIR  / "trends_data.json"


# ── Template Helpers ─────────────────────────────────────────────────────────
def css_path(depth: int) -> str:
    """Return relative path to main.css from given nesting depth."""
    return "../" * depth + "06_ASSETS/styles/main.css"


def mathjax_script():
    return """<!-- MathJax for math rendering -->
<script>
window.MathJax = {
  tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] },
  svg: { fontCache: 'global' }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" defer></script>"""


def html_head(title: str, css_depth: int = 0) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} | JEE Main PYQ Analysis</title>
<link rel="stylesheet" href="{css_path(css_depth)}">
{mathjax_script()}
</head>
<body>"""


def site_header(active: str = "") -> str:
    subjects = ["Physics", "Chemistry", "Mathematics"]
    nav_links = "".join(
        f'<a href="{s}/index.html" class="{"active" if active == s else ""}">{s}</a>'
        for s in subjects
    )
    return f"""<header class="site-header">
  <div class="container">
    <h1>📚 JEE Main PYQ Analysis</h1>
    <nav class="site-nav">
      <a href="index.html" class="{"active" if active == "home" else ""}">Home</a>
      {nav_links}
    </nav>
  </div>
</header>"""


def breadcrumb(crumbs: list) -> str:
    """crumbs = [(label, url), ..., (label, None)] — last one is current."""
    parts = []
    for i, (label, url) in enumerate(crumbs):
        if i < len(crumbs) - 1:
            parts.append(f'<a href="{url}">{html.escape(label)}</a>')
            parts.append('<span class="breadcrumb-sep">›</span>')
        else:
            parts.append(f'<span class="breadcrumb-current">{html.escape(label)}</span>')
    return f'<div class="breadcrumb container">{"".join(parts)}</div>'


def difficulty_badge(d: str) -> str:
    d = (d or "unknown").lower()
    cls = {"easy": "badge-easy", "moderate": "badge-moderate", "hard": "badge-hard"}.get(d, "badge-moderate")
    return f'<span class="badge {cls}">{html.escape(d)}</span>'


def subject_badge(s: str) -> str:
    cls = {"Physics": "badge-physics", "Chemistry": "badge-chemistry", "Mathematics": "badge-mathematics"}.get(s, "")
    return f'<span class="badge {cls}">{html.escape(s)}</span>'


def type_badge(t: str) -> str:
    cls = {"MCQ": "badge-mcq", "Integer": "badge-integer", "Numerical": "badge-numerical"}.get(t, "badge-mcq")
    return f'<span class="badge {cls}">{html.escape(t)}</span>'


def weight_badge(w: str) -> str:
    cls = {"HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low"}.get(w, "badge-low")
    return f'<span class="badge {cls}">{html.escape(w)} WEIGHT</span>'


def question_block(q: dict) -> str:
    qid  = html.escape(q.get("question_id", ""))
    text = html.escape(q.get("question_text", "(No text extracted)"))
    opts = q.get("options", {})
    ans  = q.get("correct_answer", "")
    year = q.get("year", "")
    shift= q.get("shift", "")
    qn   = q.get("question_number", "")
    qtype= q.get("question_type", "MCQ")

    opt_html = ""
    if opts:
        opt_html = '<div class="question-options">'
        for label in ["A", "B", "C", "D"]:
            val = opts.get(label, "")
            if val:
                correct_cls = "correct" if label == ans else ""
                opt_html += f'<div class="option {correct_cls}"><span class="option-label">{label}.</span> {html.escape(val)}</div>'
        opt_html += "</div>"
    elif qtype in ("Integer", "Numerical") and ans:
        opt_html = f'<div class="mt-1"><strong>Answer:</strong> <code>{html.escape(str(ans))}</code></div>'

    return f"""<div class="question-block {qtype.lower()}">
  <div class="question-header">
    <span class="question-num">Q{qn}  ({year} Shift {shift})</span>
    <div class="question-meta">
      {type_badge(qtype)}
      {difficulty_badge(q.get("difficulty", ""))}
    </div>
  </div>
  <div class="question-text">{text}</div>
  {opt_html}
  <div class="text-muted mt-1" style="font-size:0.75rem">{qid}</div>
</div>"""


def freq_table_rows(by_year: dict, all_years: list) -> str:
    rows = ""
    for year in all_years:
        cnt = by_year.get(year, 0)
        pct = int(cnt / max(sum(by_year.values()), 1) * 100)
        rows += f"""<tr>
  <td>{year}</td>
  <td>{cnt}</td>
  <td><div class="freq-bar"><div class="freq-bar-track"><div class="freq-bar-fill" style="width:{pct}%"></div></div> {pct}%</div></td>
</tr>"""
    return rows


# ── Page Generators ───────────────────────────────────────────────────────────
def generate_index(out_dir: Path, trends: dict, questions: list):
    total_q   = trends.get("total_questions", 0)
    years     = trends.get("years_covered", [])
    subj_stats= trends.get("subject_stats", {})

    stat_cards = ""
    for subj, cls in [("Physics", "physics"), ("Chemistry", "chemistry"), ("Mathematics", "mathematics")]:
        cnt = subj_stats.get(subj, {}).get("total", 0)
        stat_cards += f'<div class="stat-card {cls}"><div class="stat-value">{cnt}</div><div class="stat-label">{subj}</div></div>'

    papers = len({q.get("source_file", "") for q in questions})
    top_clusters_html = ""
    for subj in ["Physics", "Chemistry", "Mathematics"]:
        top = trends.get("top_clusters_by_subject", {}).get(subj, [])[:5]
        if top:
            rows = "".join(
                f"<tr><td>{html.escape(c['cluster_name'])}</td><td>{c['frequency']}</td>"
                f"<td>{', '.join(str(y) for y in c['years_appeared'])}</td>"
                f"<td>{weight_badge(c['predicted_weight'])}</td></tr>"
                for c in top
            )
            top_clusters_html += f"""<details open>
<summary>{subject_badge(subj)} Top Recurring Clusters</summary>
<div class="details-body">
<table class="freq-table">
<thead><tr><th>Cluster</th><th>Frequency</th><th>Years</th><th>Weight</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
</details>"""

    content = f"""{html_head("Dashboard", css_depth=0)}
{site_header("home")}
<div class="page-wrapper">
  <div class="container">
    {breadcrumb([("Home", None)])}
    <h1 style="margin-bottom:0.25rem">JEE Main PYQ Analysis Dashboard</h1>
    <p class="text-muted">Years: {min(years) if years else '—'} – {max(years) if years else '—'} &nbsp;|&nbsp; Papers: {papers} &nbsp;|&nbsp; Generated: {datetime.now().strftime('%Y-%m-%d')}</p>

    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">{total_q}</div><div class="stat-label">Total Questions</div></div>
      <div class="stat-card success"><div class="stat-value">{papers}</div><div class="stat-label">Papers</div></div>
      <div class="stat-card accent"><div class="stat-value">{len(years)}</div><div class="stat-label">Years Covered</div></div>
      {stat_cards}
    </div>

    <div class="section-header"><h2>Browse by Subject</h2></div>
    <div class="grid grid-3">
      <a href="Physics/index.html" style="text-decoration:none">
        <div class="subject-card physics">
          <h2>⚡ Physics</h2>
          <p>{subj_stats.get("Physics", {}).get("total", 0)} questions across 22 chapters</p>
        </div>
      </a>
      <a href="Chemistry/index.html" style="text-decoration:none">
        <div class="subject-card chemistry">
          <h2>🧪 Chemistry</h2>
          <p>{subj_stats.get("Chemistry", {}).get("total", 0)} questions across 27 chapters</p>
        </div>
      </a>
      <a href="Mathematics/index.html" style="text-decoration:none">
        <div class="subject-card mathematics">
          <h2>∑ Mathematics</h2>
          <p>{subj_stats.get("Mathematics", {}).get("total", 0)} questions across 24 chapters</p>
        </div>
      </a>
    </div>

    <div class="section-header mt-3"><h2>Top Recurring Clusters</h2></div>
    {top_clusters_html}

  </div>
</div>
<footer class="site-footer"><div>JEE Main PYQ Analysis System &copy; {datetime.now().year} &nbsp;|&nbsp; Data as of {datetime.now().strftime('%B %Y')}</div></footer>
<script>
document.querySelectorAll(".tab-btn").forEach(btn => {{
  btn.addEventListener("click", () => {{
    const panel = document.getElementById(btn.dataset.tab);
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    if (panel) panel.classList.add("active");
    btn.classList.add("active");
  }});
}});
</script>
</body></html>"""

    (out_dir / "index.html").write_text(content, encoding="utf-8")
    print(f"  Generated: {out_dir}/index.html")


def generate_subject_index(out_dir: Path, subject: str, trends: dict, questions: list, clusters: list):
    subj_dir = out_dir / subject
    subj_dir.mkdir(parents=True, exist_ok=True)

    subj_qs = [q for q in questions if q.get("subject") == subject]
    chapter_counts = defaultdict(int)
    for q in subj_qs:
        chap = q.get("chapter", "Unclassified")
        chapter_counts[chap] += 1

    max_count = max(chapter_counts.values(), default=1)

    chapter_cards_html = ""
    for chap, cnt in sorted(chapter_counts.items(), key=lambda x: -x[1]):
        slug   = chap.replace(" ", "_").replace("&", "and").replace("/", "_")
        bar_pct= int(cnt / max_count * 100)
        chapter_cards_html += f"""<a href="{slug}/chapter_analysis.html" style="text-decoration:none">
  <div class="chapter-card">
    <div class="chapter-name">{html.escape(chap)}</div>
    <div class="chapter-count">{cnt} questions</div>
    <div class="chapter-bar"><div class="chapter-bar-fill" style="width:{bar_pct}%"></div></div>
  </div>
</a>"""

    subj_cls  = subject.lower()
    subj_icon = {"Physics": "⚡", "Chemistry": "🧪", "Mathematics": "∑"}.get(subject, "📖")

    content = f"""{html_head(subject, css_depth=1)}
{site_header(subject)}
<div class="page-wrapper">
  <div class="container">
    {breadcrumb([("Home", "../index.html"), (subject, None)])}
    <h1>{subj_icon} {subject}</h1>
    <div class="stats-grid">
      <div class="stat-card {subj_cls}"><div class="stat-value">{len(subj_qs)}</div><div class="stat-label">Total Questions</div></div>
      <div class="stat-card"><div class="stat-value">{len(chapter_counts)}</div><div class="stat-label">Chapters</div></div>
    </div>

    <div class="search-container">
      <span class="search-icon">🔍</span>
      <input type="text" class="search-input" id="chapterSearch" placeholder="Search chapters..." oninput="filterChapters(this.value)">
      <div class="search-hint">Type to filter chapters</div>
    </div>

    <div class="section-header"><h2>Chapters</h2></div>
    <div class="chapter-grid" id="chapterGrid">{chapter_cards_html}</div>
  </div>
</div>
<footer class="site-footer">JEE Main PYQ Analysis System</footer>
<script>
function filterChapters(val) {{
  val = val.toLowerCase();
  document.querySelectorAll("#chapterGrid > a").forEach(card => {{
    card.style.display = card.textContent.toLowerCase().includes(val) ? "" : "none";
  }});
}}
</script>
</body></html>"""

    (subj_dir / "index.html").write_text(content, encoding="utf-8")
    print(f"  Generated: {subj_dir}/index.html")


def generate_chapter_page(chapter_dir: Path, subject: str, chapter: str, questions: list, clusters: list, all_years: list, css_depth: int = 2):
    chapter_dir.mkdir(parents=True, exist_ok=True)

    chap_qs = [q for q in questions if q.get("chapter") == chapter and q.get("subject") == subject]
    by_year = defaultdict(int)
    for q in chap_qs:
        by_year[q.get("year", 0)] += 1

    chap_clusters = [c for c in clusters if c.get("chapter") == chapter and c.get("subject") == subject]

    q_blocks = "".join(question_block(q) for q in chap_qs[:50])  # first 50
    more_note = f'<p class="text-muted">Showing first 50 of {len(chap_qs)} questions.</p>' if len(chap_qs) > 50 else ""

    cluster_cards = ""
    for c in sorted(chap_clusters, key=lambda x: -x.get("frequency", 0)):
        cluster_cards += f"""<div class="cluster-card">
  <div class="cluster-id">{html.escape(c.get("cluster_id",""))}</div>
  <div class="cluster-name">{html.escape(c.get("cluster_name",""))}</div>
  <div class="cluster-meta">
    <span class="chip">{c.get("frequency",0)} Qs</span>
    <span class="chip">{", ".join(str(y) for y in c.get("years_appeared",[]))}</span>
    {weight_badge(c.get("predicted_weight","LOW"))}
  </div>
</div>"""

    year_rows = freq_table_rows(dict(by_year), all_years)
    subj_cls  = subject.lower()
    subj_icon = {"Physics": "⚡", "Chemistry": "🧪", "Mathematics": "∑"}.get(subject, "📖")

    content = f"""{html_head(chapter, css_depth=css_depth)}
{site_header(subject)}
<div class="page-wrapper">
  <div class="container">
    {breadcrumb([("Home", "../" * css_depth + "index.html"), (subject, "../" * (css_depth-1) + "index.html"), (chapter, None)])}
    <h1>{subj_icon} {html.escape(chapter)}</h1>
    <div class="stats-grid">
      <div class="stat-card {subj_cls}"><div class="stat-value">{len(chap_qs)}</div><div class="stat-label">Total Questions</div></div>
      <div class="stat-card"><div class="stat-value">{len(all_years)}</div><div class="stat-label">Years</div></div>
      <div class="stat-card"><div class="stat-value">{len(chap_clusters)}</div><div class="stat-label">Clusters</div></div>
    </div>

    <div class="tabs">
      <button class="tab-btn active" data-tab="tab-clusters">Clusters</button>
      <button class="tab-btn" data-tab="tab-trend">Year Trend</button>
      <button class="tab-btn" data-tab="tab-questions">Questions</button>
    </div>

    <div id="tab-clusters" class="tab-panel active">
      <h3>Question Clusters</h3>
      {cluster_cards if cluster_cards else '<p class="text-muted">No clusters yet — run cluster_questions.py</p>'}
    </div>

    <div id="tab-trend" class="tab-panel">
      <h3>Year-wise Frequency</h3>
      <table class="freq-table">
        <thead><tr><th>Year</th><th>Questions</th><th>Frequency</th></tr></thead>
        <tbody>{year_rows}</tbody>
      </table>
    </div>

    <div id="tab-questions" class="tab-panel">
      <h3>Questions</h3>
      {more_note}
      {q_blocks if q_blocks else '<p class="text-muted">No questions extracted yet.</p>'}
    </div>
  </div>
</div>
<footer class="site-footer">JEE Main PYQ Analysis System</footer>
<script>
document.querySelectorAll(".tab-btn").forEach(btn => {{
  btn.addEventListener("click", () => {{
    const panel = document.getElementById(btn.dataset.tab);
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    if (panel) panel.classList.add("active");
    btn.classList.add("active");
  }});
}});
</script>
</body></html>"""

    out_path = chapter_dir / "chapter_analysis.html"
    out_path.write_text(content, encoding="utf-8")
    print(f"  Generated: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate HTML dashboard.")
    parser.add_argument("--output-dir", default=str(REPORTS_DIR), help="Output directory.")
    parser.add_argument("--subject", help="Generate only this subject.")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    questions = []
    if QUESTIONS_JSONL.exists():
        with open(QUESTIONS_JSONL, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        questions.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    clusters = []
    if CLUSTERS_FILE.exists():
        with open(CLUSTERS_FILE, encoding="utf-8") as f:
            clusters = json.load(f).get("clusters", [])

    trends = {}
    if TRENDS_FILE.exists():
        with open(TRENDS_FILE, encoding="utf-8") as f:
            trends = json.load(f)

    all_years = sorted({q.get("year", 0) for q in questions if q.get("year")})

    print(f"Generating HTML to: {out_dir}")
    print(f"  Questions: {len(questions)}, Clusters: {len(clusters)}, Years: {all_years}")

    # Generate index.html
    generate_index(out_dir, trends, questions)

    subjects = ["Physics", "Chemistry", "Mathematics"]
    if args.subject:
        subjects = [args.subject]

    for subject in subjects:
        print(f"\n── {subject} ──")
        generate_subject_index(out_dir, subject, trends, questions, clusters)

        # Group by chapter
        chapter_map = defaultdict(list)
        for q in questions:
            if q.get("subject") == subject and q.get("chapter"):
                chapter_map[q["chapter"]].append(q)

        for chapter, chap_qs in sorted(chapter_map.items()):
            slug = chapter.replace(" ", "_").replace("&", "and").replace("/", "_")
            chapter_dir = out_dir / subject / slug
            generate_chapter_page(chapter_dir, subject, chapter, chap_qs, clusters, all_years, css_depth=2)

    print(f"\n✅ HTML generation complete.")
    print(f"   Open: {out_dir}/index.html")


if __name__ == "__main__":
    main()
