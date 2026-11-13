#!/usr/bin/env python3
"""
generate_practice_sets.py
Generates the full Practice Sets library for JEE Main PYQ Analysis.
Outputs:
  - 05_PRACTICE_SETS/{Subject}/{chapter_slug}/practice.html
  - 05_PRACTICE_SETS/{Subject}/{chapter_slug}/answers.html
  - 05_PRACTICE_SETS/{Subject}/{chapter_slug}/clusters/{cluster_id}/practice.html
  - 05_PRACTICE_SETS/{Subject}/{chapter_slug}/clusters/{cluster_id}/answers.html
  - 05_PRACTICE_SETS/bucket_1_mixed_practice.html
  - 05_PRACTICE_SETS/bucket_2_mixed_practice.html
  - 05_PRACTICE_SETS/bucket_3_mixed_practice.html
  - 05_PRACTICE_SETS/index.html
"""

import json
import os
import re
import random
from collections import defaultdict
from pathlib import Path
from html import escape

# ─────────────────────────── PATHS ───────────────────────────
PROJECT_ROOT = Path("/home/hozaifah/HozzCode/JEE/JEE_MAIN_PYQ_ANALYSIS")
DB_FILE      = PROJECT_ROOT / "03_DATABASE" / "questions.jsonl"
PS_DIR       = PROJECT_ROOT / "05_PRACTICE_SETS"

# ─────────────────────── BUCKET MAPPINGS ─────────────────────
BUCKET_1_CHAPTERS = [
    "Units & Measurements", "Dual Nature of Radiation & Matter", "Atoms & Nuclei",
    "Semiconductors & Electronic Devices", "Electromagnetic Waves", "Current Electricity",
    "Electrostatics", "Ray Optics",
    "Periodic Properties", "Chemical Bonding & Molecular Structure", "Coordination Compounds",
    "d & f Block Elements", "Basic Organic Chemistry", "Biomolecules", "Solutions",
    "Chemical Kinetics", "Electrochemistry",
    "Vectors", "3D Geometry", "Matrices", "Determinants", "Sequences & Series",
    "Statistics", "Quadratic Equations", "Binomial Theorem"
]
BUCKET_2_CHAPTERS = [
    "Thermal Physics", "Magnetic Effects of Current", "Magnetism & Matter",
    "Electromagnetic Induction", "Alternating Current", "Wave Optics",
    "Gravitation", "Kinematics", "Laws of Motion", "Work Energy Power",
    "Atomic Structure", "Thermodynamics", "Some Basic Concepts of Chemistry",
    "Redox Reactions", "Hydrocarbons", "Haloalkanes & Haloarenes",
    "Alcohols Phenols & Ethers", "Aldehydes Ketones & Carboxylic Acids",
    "Amines", "p-Block Elements",
    "Sets Relations & Functions", "Limits", "Continuity & Differentiability",
    "Straight Lines", "Circles", "Integration", "Differential Equations", "Probability"
]
BUCKET_3_CHAPTERS = [
    "Rotational Motion", "Properties of Matter", "Oscillations", "Waves",
    "Equilibrium", "States of Matter", "Surface Chemistry",
    "Complex Numbers", "Permutations & Combinations", "Parabola", "Ellipse",
    "Hyperbola", "Differentiation & Applications", "Trigonometry", "Mathematical Reasoning"
]

ALL_BUCKETS = {
    1: BUCKET_1_CHAPTERS,
    2: BUCKET_2_CHAPTERS,
    3: BUCKET_3_CHAPTERS,
}

def chapter_to_bucket(chapter):
    for b, lst in ALL_BUCKETS.items():
        if chapter in lst:
            return b
    return None

# ─────────────────────── HELPERS ─────────────────────────────
def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '_', text.strip())
    return text[:60]

def format_date(date_str):
    """Convert 2024-01-27 → 27 Jan 2024"""
    try:
        from datetime import datetime
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%-d %b %Y")
    except Exception:
        return date_str or "—"

def shift_label(shift):
    try:
        s = int(shift)
        return f"Shift {s}"
    except Exception:
        return str(shift) if shift else "—"

def difficulty_badge(diff):
    d = (diff or "").strip().lower()
    if d in ("easy",):
        return f'<span class="badge badge-easy">Easy</span>'
    elif d in ("moderate", "medium"):
        return f'<span class="badge badge-moderate">Moderate</span>'
    elif d in ("difficult", "hard"):
        return f'<span class="badge badge-difficult">Difficult</span>'
    else:
        return f'<span class="badge badge-unknown">—</span>'

def qtype_badge(qtype):
    qt = (qtype or "").strip()
    cls = {"MCQ": "badge-mcq", "Integer": "badge-integer", "Numerical": "badge-numerical"}.get(qt, "badge-unknown")
    return f'<span class="badge {cls}">{escape(qt) if qt else "—"}</span>'

# ─────────────────────── CSS / JS ────────────────────────────
COMMON_CSS = """
<style>
  :root {
    --bg: #f8f9fa;
    --card: #ffffff;
    --border: #dee2e6;
    --accent: #0d6efd;
    --text: #212529;
    --muted: #6c757d;
    --easy: #198754;
    --moderate: #fd7e14;
    --difficult: #dc3545;
    --mcq: #0d6efd;
    --integer: #6f42c1;
    --numerical: #0dcaf0;
    --cluster-bg: #e9ecef;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg);
         color: var(--text); line-height: 1.6; padding: 0 0 60px; }
  header { background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
           color: #fff; padding: 20px 32px; }
  header h1 { font-size: 1.5rem; font-weight: 700; }
  header p  { font-size: 0.9rem; opacity: 0.85; margin-top: 4px; }
  nav.breadcrumb { background: #fff; border-bottom: 1px solid var(--border);
                   padding: 10px 32px; font-size: 0.85rem; }
  nav.breadcrumb a { color: var(--accent); text-decoration: none; }
  nav.breadcrumb a:hover { text-decoration: underline; }
  .container { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
  .stats-bar { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
  .stat-chip { background: var(--card); border: 1px solid var(--border);
               border-radius: 8px; padding: 8px 16px; font-size: 0.85rem; }
  .stat-chip strong { color: var(--accent); }
  /* cluster group */
  .cluster-group { margin-bottom: 40px; }
  .cluster-heading { background: var(--cluster-bg); border-left: 4px solid var(--accent);
                     border-radius: 4px; padding: 10px 16px; margin-bottom: 16px;
                     font-size: 0.95rem; font-weight: 600; }
  .cluster-heading .cluster-meta { font-weight: 400; color: var(--muted); font-size: 0.82rem; margin-left: 8px; }
  /* question card */
  .q-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px;
            padding: 20px 22px; margin-bottom: 16px; }
  .q-header { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 10px; }
  .q-num { font-weight: 700; font-size: 1rem; min-width: 36px; }
  .q-id  { font-size: 0.72rem; color: var(--muted); font-family: monospace; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 999px;
           font-size: 0.72rem; font-weight: 600; white-space: nowrap; }
  .badge-easy      { background: #d1fae5; color: var(--easy); }
  .badge-moderate  { background: #fff3cd; color: #856404; }
  .badge-difficult { background: #fde8e8; color: var(--difficult); }
  .badge-unknown   { background: #e9ecef; color: var(--muted); }
  .badge-mcq       { background: #dbeafe; color: #1d4ed8; }
  .badge-integer   { background: #ede9fe; color: #5b21b6; }
  .badge-numerical { background: #cffafe; color: #0e7490; }
  .badge-cluster   { background: #e9ecef; color: #495057; }
  .badge-year      { background: #e0f2fe; color: #0369a1; }
  .q-text { font-size: 0.95rem; margin: 10px 0; white-space: pre-wrap; }
  .options { margin: 10px 0 10px 8px; }
  .option { padding: 4px 0; font-size: 0.9rem; }
  .option-label { font-weight: 600; margin-right: 6px; }
  .integer-box { display: inline-block; border: 1px dashed var(--muted);
                 border-radius: 4px; padding: 4px 32px; margin: 8px 0;
                 color: var(--muted); font-size: 0.85rem; }
  .q-footer { margin-top: 12px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  /* answer reveal */
  .ans-reveal { margin-top: 10px; }
  .btn-show { background: var(--accent); color: #fff; border: none; border-radius: 6px;
              padding: 6px 14px; font-size: 0.82rem; cursor: pointer; }
  .btn-show:hover { background: #0a58ca; }
  .ans-box { display: none; margin-top: 8px; background: #f0fdf4; border: 1px solid #bbf7d0;
             border-radius: 6px; padding: 8px 14px; font-size: 0.9rem; }
  .ans-box .ans-label { font-weight: 700; color: var(--easy); margin-right: 6px; }
  /* answer key table */
  .ans-table { width: 100%; border-collapse: collapse; }
  .ans-table th, .ans-table td { padding: 8px 12px; border: 1px solid var(--border);
                                  font-size: 0.88rem; text-align: left; }
  .ans-table th { background: var(--cluster-bg); font-weight: 600; }
  .ans-table tr:nth-child(even) { background: #fafafa; }
  .ans-cell-hidden { cursor: pointer; user-select: none; }
  .ans-cell-hidden span.masked { background: #dee2e6; color: #dee2e6; border-radius: 4px; padding: 2px 10px; }
  .ans-cell-hidden span.revealed { display: none; font-weight: 600; color: var(--easy); }
  /* index nav */
  .subject-section h2 { margin: 32px 0 12px; font-size: 1.2rem;
                        border-bottom: 2px solid var(--accent); padding-bottom: 6px; }
  .chapter-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px,1fr)); gap: 12px; }
  .chapter-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px;
                  padding: 14px 16px; text-decoration: none; color: var(--text);
                  transition: box-shadow .15s; display: block; }
  .chapter-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.12); border-color: var(--accent); }
  .chapter-card h3 { font-size: 0.92rem; font-weight: 600; }
  .chapter-card .meta { font-size: 0.78rem; color: var(--muted); margin-top: 4px; }
  .bucket-links { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 24px; }
  .bucket-link { padding: 8px 16px; border-radius: 8px; text-decoration: none;
                 font-size: 0.88rem; font-weight: 600; border: 2px solid; }
  .b1 { border-color: var(--easy); color: var(--easy); }
  .b1:hover { background: #d1fae5; }
  .b2 { border-color: var(--moderate, #fd7e14); color: #fd7e14; }
  .b2:hover { background: #fff3cd; }
  .b3 { border-color: var(--difficult); color: var(--difficult); }
  .b3:hover { background: #fde8e8; }
  footer { margin-top: 60px; padding: 20px 32px; border-top: 1px solid var(--border);
           font-size: 0.8rem; color: var(--muted); text-align: center; }
  @media(max-width:600px){
    header { padding: 14px 16px; }
    .container { padding: 12px 10px; }
    .chapter-grid { grid-template-columns: 1fr; }
  }
</style>
<script>
function toggleAns(btn) {
  var box = btn.nextElementSibling;
  if (box.style.display === 'block') {
    box.style.display = 'none';
    btn.textContent = 'Show Answer';
  } else {
    box.style.display = 'block';
    btn.textContent = 'Hide Answer';
  }
}
function toggleAnsCell(cell) {
  var masked = cell.querySelector('.masked');
  var revealed = cell.querySelector('.revealed');
  if (masked && revealed) {
    if (revealed.style.display === 'inline') {
      revealed.style.display = 'none';
      masked.style.display = 'inline';
    } else {
      revealed.style.display = 'inline';
      masked.style.display = 'none';
    }
  }
}
</script>
"""

FOOTER_HTML = """<footer>JEE Main PYQ Analysis — Practice Sets &nbsp;|&nbsp;
<a href="../../index.html">🏠 Practice Home</a></footer>"""

FOOTER_HTML_ROOT = """<footer>JEE Main PYQ Analysis — Practice Sets</footer>"""

# ─────────────────────── RENDER QUESTION ─────────────────────
def render_question(q, num, show_cluster_badge=True):
    qid   = escape(q.get("question_id", ""))
    year  = q.get("year", "")
    date  = format_date(q.get("date", ""))
    shift = shift_label(q.get("shift", ""))
    diff  = q.get("difficulty", "")
    qtype = q.get("question_type", "MCQ")
    text  = (q.get("question_text") or "").strip()
    opts  = q.get("options") or {}
    ans   = q.get("correct_answer", "")
    cid   = q.get("cluster_id", "")

    if not text or len(text) < 5:
        text = "[Question text not available — refer to source paper]"

    year_badge = f'<span class="badge badge-year">{year} | {date} | {shift}</span>' if year else ""
    cluster_badge = f'<span class="badge badge-cluster">Cluster: {escape(cid)}</span>' if (show_cluster_badge and cid) else ""

    # options / answer box
    opts_html = ""
    if qtype == "MCQ" and opts:
        opts_html = '<div class="options">'
        for key in ("A", "B", "C", "D"):
            val = opts.get(key, "")
            if val:
                opts_html += f'<div class="option"><span class="option-label">({key})</span>{escape(str(val))}</div>'
        opts_html += "</div>"
    elif qtype in ("Integer", "Numerical"):
        opts_html = '<div class="options"><div class="integer-box">Enter your answer</div></div>'
    elif qtype == "MCQ":
        opts_html = '<div class="options"><em style="color:#6c757d;font-size:.85rem">Options not extracted — refer to source paper.</em></div>'

    # answer reveal
    ans_text = escape(str(ans)) if ans else "<em>Not available</em>"
    ans_html = f"""<div class="ans-reveal">
      <button class="btn-show" onclick="toggleAns(this)">Show Answer</button>
      <div class="ans-box"><span class="ans-label">Answer:</span> {ans_text}</div>
    </div>"""

    return f"""<div class="q-card">
  <div class="q-header">
    <span class="q-num">Q{num}</span>
    <span class="q-id">{qid}</span>
    {year_badge}
    {difficulty_badge(diff)}
    {qtype_badge(qtype)}
    {cluster_badge}
  </div>
  <div class="q-text">{escape(text)}</div>
  {opts_html}
  {ans_html}
</div>"""

# ─────────────────────── CHAPTER PRACTICE HTML ───────────────
def build_chapter_practice(subject, chapter, questions, out_path, cluster_link_prefix="clusters/"):
    total = len(questions)
    slug  = slugify(chapter)
    bucket = chapter_to_bucket(chapter)
    bucket_label = f"Bucket {bucket}" if bucket else "Unassigned"

    # Group by cluster
    by_cluster = defaultdict(list)
    for q in questions:
        cid = q.get("cluster_id") or "UNCLUSTERED"
        by_cluster[cid].append(q)

    clusters_html = ""
    q_global = 0
    for cid, cqs in sorted(by_cluster.items(), key=lambda x: (-len(x[1]), x[0])):
        q_global_start = q_global
        c_html = ""
        for q in cqs:
            q_global += 1
            c_html += render_question(q, q_global, show_cluster_badge=False)

        cluster_link = ""
        if len(cqs) >= 3:
            rel = f"{cluster_link_prefix}{escape(cid)}/practice.html"
            cluster_link = f'&nbsp;<a href="{rel}" style="font-size:.78rem;color:var(--accent)">↗ Cluster set</a>'

        clusters_html += f"""<div class="cluster-group">
  <div class="cluster-heading">
    📌 {escape(cid)}
    <span class="cluster-meta">({len(cqs)} question{"s" if len(cqs)!=1 else ""})</span>
    {cluster_link}
  </div>
  {c_html}
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(chapter)} — Practice | JEE Main PYQ</title>
{COMMON_CSS}
</head>
<body>
<header>
  <h1>📝 {escape(chapter)}</h1>
  <p>{escape(subject)} · {bucket_label} · {total} question{"s" if total!=1 else ""}</p>
</header>
<nav class="breadcrumb">
  <a href="../../index.html">🏠 Practice Home</a> &rsaquo;
  <a href="#">{escape(subject)}</a> &rsaquo;
  {escape(chapter)}
  &nbsp;|&nbsp; <a href="answers.html">📋 Answer Key</a>
</nav>
<div class="container">
  <div class="stats-bar">
    <div class="stat-chip">Total Questions: <strong>{total}</strong></div>
    <div class="stat-chip">Clusters: <strong>{len(by_cluster)}</strong></div>
    <div class="stat-chip">Subject: <strong>{escape(subject)}</strong></div>
    <div class="stat-chip">{bucket_label}</div>
  </div>
  {clusters_html}
</div>
{FOOTER_HTML}
</body></html>"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

# ─────────────────────── CHAPTER ANSWER KEY ──────────────────
def build_chapter_answers(subject, chapter, questions, out_path):
    total = len(questions)

    rows = ""
    for i, q in enumerate(questions, 1):
        qid   = escape(q.get("question_id", ""))
        year  = q.get("year", "")
        date  = format_date(q.get("date", ""))
        shift = shift_label(q.get("shift", ""))
        qtype = q.get("question_type", "")
        ans   = q.get("correct_answer", "")
        cid   = escape(q.get("cluster_id", ""))
        ans_text = escape(str(ans)) if ans else "N/A"
        rows += f"""<tr>
  <td>{i}</td>
  <td style="font-family:monospace;font-size:.78rem">{qid}</td>
  <td>{year} | {date} | {shift}</td>
  <td>{qtype_badge(qtype)}</td>
  <td>{cid}</td>
  <td class="ans-cell-hidden" onclick="toggleAnsCell(this)">
    <span class="masked">▓▓▓▓</span>
    <span class="revealed" style="display:none">{ans_text}</span>
  </td>
</tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(chapter)} — Answer Key | JEE Main PYQ</title>
{COMMON_CSS}
</head>
<body>
<header>
  <h1>📋 Answer Key — {escape(chapter)}</h1>
  <p>{escape(subject)} · {total} question{"s" if total!=1 else ""}</p>
</header>
<nav class="breadcrumb">
  <a href="../../index.html">🏠 Practice Home</a> &rsaquo;
  <a href="#">{escape(subject)}</a> &rsaquo;
  <a href="practice.html">{escape(chapter)}</a> &rsaquo;
  Answer Key
</nav>
<div class="container">
  <p style="margin-bottom:14px;color:var(--muted);font-size:.88rem">
    👆 Click any answer cell to reveal. Click again to hide.
  </p>
  <table class="ans-table">
    <thead><tr>
      <th>#</th><th>Question ID</th><th>Year / Date / Shift</th>
      <th>Type</th><th>Cluster</th><th>Answer (click to reveal)</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
{FOOTER_HTML}
</body></html>"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

# ─────────────────────── CLUSTER PRACTICE HTML ───────────────
def build_cluster_practice(subject, chapter, cluster_id, questions, out_path):
    total = len(questions)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(cluster_id)} — Cluster Practice | JEE Main PYQ</title>
{COMMON_CSS}
</head>
<body>
<header>
  <h1>📌 Cluster: {escape(cluster_id)}</h1>
  <p>{escape(chapter)} · {escape(subject)} · {total} question{"s" if total!=1 else ""}</p>
</header>
<nav class="breadcrumb">
  <a href="../../../../index.html">🏠 Practice Home</a> &rsaquo;
  <a href="../../practice.html">{escape(chapter)}</a> &rsaquo;
  Cluster {escape(cluster_id)}
  &nbsp;|&nbsp; <a href="answers.html">📋 Answer Key</a>
</nav>
<div class="container">
  <div class="stats-bar">
    <div class="stat-chip">Cluster: <strong>{escape(cluster_id)}</strong></div>
    <div class="stat-chip">Questions: <strong>{total}</strong></div>
  </div>
"""
    for i, q in enumerate(questions, 1):
        html += render_question(q, i, show_cluster_badge=False)

    html += f"""</div>
{FOOTER_HTML}
</body></html>"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

def build_cluster_answers(subject, chapter, cluster_id, questions, out_path):
    total = len(questions)
    rows = ""
    for i, q in enumerate(questions, 1):
        qid   = escape(q.get("question_id", ""))
        year  = q.get("year", "")
        date  = format_date(q.get("date", ""))
        shift = shift_label(q.get("shift", ""))
        qtype = q.get("question_type", "")
        ans   = q.get("correct_answer", "")
        ans_text = escape(str(ans)) if ans else "N/A"
        rows += f"""<tr>
  <td>{i}</td>
  <td style="font-family:monospace;font-size:.78rem">{qid}</td>
  <td>{year} | {date} | {shift}</td>
  <td>{qtype_badge(qtype)}</td>
  <td class="ans-cell-hidden" onclick="toggleAnsCell(this)">
    <span class="masked">▓▓▓▓</span>
    <span class="revealed" style="display:none">{ans_text}</span>
  </td>
</tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(cluster_id)} — Answer Key | JEE Main PYQ</title>
{COMMON_CSS}
</head>
<body>
<header>
  <h1>📋 Answer Key — {escape(cluster_id)}</h1>
  <p>{escape(chapter)} · {escape(subject)} · {total} questions</p>
</header>
<nav class="breadcrumb">
  <a href="../../../../index.html">🏠 Practice Home</a> &rsaquo;
  <a href="../../practice.html">{escape(chapter)}</a> &rsaquo;
  <a href="practice.html">Cluster {escape(cluster_id)}</a> &rsaquo;
  Answer Key
</nav>
<div class="container">
  <p style="margin-bottom:14px;color:var(--muted);font-size:.88rem">
    👆 Click any answer cell to reveal. Click again to hide.
  </p>
  <table class="ans-table">
    <thead><tr>
      <th>#</th><th>Question ID</th><th>Year / Date / Shift</th>
      <th>Type</th><th>Answer (click to reveal)</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
{FOOTER_HTML}
</body></html>"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

# ─────────────────────── MIXED BUCKET PRACTICE ───────────────
def build_bucket_practice(bucket_num, questions_sample, out_path):
    total = len(questions_sample)
    color = {1: "#198754", 2: "#fd7e14", 3: "#dc3545"}.get(bucket_num, "#0d6efd")
    label = {1: "High Priority", 2: "Medium Priority", 3: "Lower Priority"}.get(bucket_num, "")

    qs_html = ""
    for i, q in enumerate(questions_sample, 1):
        chapter = escape(q.get("chapter", ""))
        subject = escape(q.get("subject", ""))
        chapter_badge = f'<span class="badge badge-cluster">{subject} · {chapter}</span>'

        qid   = escape(q.get("question_id", ""))
        year  = q.get("year", "")
        date  = format_date(q.get("date", ""))
        shift = shift_label(q.get("shift", ""))
        diff  = q.get("difficulty", "")
        qtype = q.get("question_type", "MCQ")
        text  = (q.get("question_text") or "").strip()
        opts  = q.get("options") or {}
        ans   = q.get("correct_answer", "")

        if not text or len(text) < 5:
            text = "[Question text not available — refer to source paper]"

        year_badge = f'<span class="badge badge-year">{year} | {date} | {shift}</span>' if year else ""
        opts_html = ""
        if qtype == "MCQ" and opts:
            opts_html = '<div class="options">'
            for key in ("A", "B", "C", "D"):
                val = opts.get(key, "")
                if val:
                    opts_html += f'<div class="option"><span class="option-label">({key})</span>{escape(str(val))}</div>'
            opts_html += "</div>"
        elif qtype in ("Integer", "Numerical"):
            opts_html = '<div class="options"><div class="integer-box">Enter your answer</div></div>'
        elif qtype == "MCQ":
            opts_html = '<div class="options"><em style="color:#6c757d;font-size:.85rem">Options not extracted — refer to source paper.</em></div>'

        ans_text = escape(str(ans)) if ans else "<em>Not available</em>"
        qs_html += f"""<div class="q-card">
  <div class="q-header">
    <span class="q-num">Q{i}</span>
    <span class="q-id">{qid}</span>
    {year_badge}
    {difficulty_badge(diff)}
    {qtype_badge(qtype)}
    {chapter_badge}
  </div>
  <div class="q-text">{escape(text)}</div>
  {opts_html}
  <div class="ans-reveal">
    <button class="btn-show" onclick="toggleAns(this)">Show Answer</button>
    <div class="ans-box"><span class="ans-label">Answer:</span> {ans_text}</div>
  </div>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bucket {bucket_num} Mixed Practice | JEE Main PYQ</title>
{COMMON_CSS}
</head>
<body>
<header style="background:linear-gradient(135deg,{color}cc,{color})">
  <h1>🎯 Bucket {bucket_num} Mixed Practice — PCM</h1>
  <p>{label} · {total} questions from Physics, Chemistry &amp; Mathematics</p>
</header>
<nav class="breadcrumb">
  <a href="index.html">🏠 Practice Home</a> &rsaquo;
  Bucket {bucket_num} Mixed Practice
</nav>
<div class="container">
  <div class="stats-bar">
    <div class="stat-chip">Total Questions: <strong>{total}</strong></div>
    <div class="stat-chip">Mix: <strong>PCM</strong></div>
    <div class="stat-chip">Priority: <strong>Bucket {bucket_num}</strong></div>
  </div>
  {qs_html}
</div>
{FOOTER_HTML_ROOT}
</body></html>"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

# ─────────────────────── INDEX PAGE ──────────────────────────
def build_index(subject_data, cluster_counts, bucket_stats):
    """
    subject_data: { subject: { chapter: (total_q, slug, bucket) } }
    """
    subjects_html = ""
    for subj in ("Physics", "Chemistry", "Mathematics"):
        chapters = subject_data.get(subj, {})
        cards = ""
        for chapter, (total, slug, bucket) in sorted(chapters.items(), key=lambda x: x[0]):
            bucket_label = f"Bucket {bucket}" if bucket else ""
            cards += f"""<a class="chapter-card" href="{subj}/{slug}/practice.html">
  <h3>{escape(chapter)}</h3>
  <div class="meta">{total} question{"s" if total!=1 else ""} &nbsp;|&nbsp; {bucket_label}</div>
</a>"""
        subjects_html += f"""<div class="subject-section">
  <h2>{'⚡' if subj=='Physics' else '🧪' if subj=='Chemistry' else '📐'} {subj}</h2>
  <div class="chapter-grid">{cards}</div>
</div>"""

    total_chapters = sum(len(v) for v in subject_data.values())
    total_cluster_sets = cluster_counts
    b1n = bucket_stats.get(1, 0)
    b2n = bucket_stats.get(2, 0)
    b3n = bucket_stats.get(3, 0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JEE Main PYQ — Practice Sets Index</title>
{COMMON_CSS}
</head>
<body>
<header>
  <h1>🏠 JEE Main PYQ — Practice Sets Library</h1>
  <p>2021–2025 · 90 Papers · 7,959 Questions · {total_chapters} Chapters · {total_cluster_sets} Cluster Sets</p>
</header>
<div class="container">
  <div class="stats-bar">
    <div class="stat-chip">Total Chapters: <strong>{total_chapters}</strong></div>
    <div class="stat-chip">Cluster Sets: <strong>{total_cluster_sets}</strong></div>
    <div class="stat-chip">Bucket 1 Chapters: <strong>{b1n}</strong></div>
    <div class="stat-chip">Bucket 2 Chapters: <strong>{b2n}</strong></div>
    <div class="stat-chip">Bucket 3 Chapters: <strong>{b3n}</strong></div>
  </div>

  <h2 style="margin-bottom:12px;font-size:1.1rem">🎯 Mixed PCM Practice Sets</h2>
  <div class="bucket-links">
    <a class="bucket-link b1" href="bucket_1_mixed_practice.html">🟢 Bucket 1 Mixed (30 Q)</a>
    <a class="bucket-link b2" href="bucket_2_mixed_practice.html">🟡 Bucket 2 Mixed (30 Q)</a>
    <a class="bucket-link b3" href="bucket_3_mixed_practice.html">🔴 Bucket 3 Mixed (20 Q)</a>
  </div>

  {subjects_html}
</div>
{FOOTER_HTML_ROOT}
</body></html>"""

    (PS_DIR / "index.html").write_text(html, encoding="utf-8")

# ─────────────────────── MAIN ────────────────────────────────
def main():
    random.seed(42)
    print("Loading questions…")
    questions = []
    with open(DB_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    questions.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    print(f"  Loaded {len(questions)} questions")

    # ── Organise by subject → chapter → questions ──
    by_subject_chapter = defaultdict(lambda: defaultdict(list))
    for q in questions:
        s = q.get("subject", "").strip()
        c = q.get("chapter", "").strip()
        if s and c:
            by_subject_chapter[s][c].append(q)

    # ── Also organise bucket pools ──
    bucket_pool = defaultdict(list)
    for q in questions:
        chapter = q.get("chapter", "").strip()
        b = chapter_to_bucket(chapter)
        if b:
            bucket_pool[b].append(q)

    total_chapter_files = 0
    total_cluster_files = 0
    chapter_count = 0

    subject_data = {}   # for index

    for subject, chapters in by_subject_chapter.items():
        subject_data[subject] = {}
        for chapter, cqs in chapters.items():
            slug = slugify(chapter)
            bucket = chapter_to_bucket(chapter)
            chapter_dir = PS_DIR / subject / slug

            # chapter practice.html + answers.html
            build_chapter_practice(subject, chapter, cqs,
                                   chapter_dir / "practice.html")
            build_chapter_answers(subject, chapter, cqs,
                                  chapter_dir / "answers.html")
            total_chapter_files += 2
            chapter_count += 1

            subject_data[subject][chapter] = (len(cqs), slug, bucket)

            # cluster sets (≥3 questions)
            by_cluster = defaultdict(list)
            for q in cqs:
                cid = q.get("cluster_id") or "UNCLUSTERED"
                by_cluster[cid].append(q)

            for cid, cluster_qs in by_cluster.items():
                if len(cluster_qs) >= 3:
                    cid_slug = slugify(cid)
                    cl_dir = chapter_dir / "clusters" / cid_slug
                    build_cluster_practice(subject, chapter, cid, cluster_qs,
                                           cl_dir / "practice.html")
                    build_cluster_answers(subject, chapter, cid, cluster_qs,
                                          cl_dir / "answers.html")
                    total_cluster_files += 2

            print(f"  ✓ {subject}/{chapter} ({len(cqs)} q, {sum(1 for c,qs in by_cluster.items() if len(qs)>=3)} cluster sets)")

    cluster_sets_count = total_cluster_files // 2

    # ── Bucket mixed practice ──
    for bnum, count in [(1, 30), (2, 30), (3, 20)]:
        pool = bucket_pool[bnum]
        sample = random.sample(pool, min(count, len(pool)))
        out = PS_DIR / f"bucket_{bnum}_mixed_practice.html"
        build_bucket_practice(bnum, sample, out)
        print(f"  ✓ Bucket {bnum} mixed practice ({len(sample)} questions)")

    # ── Index ──
    bucket_stats = {b: sum(1 for c in subject_data.get(s, {}) if chapter_to_bucket(c) == b)
                    for b in (1,2,3) for s in ("Physics","Chemistry","Mathematics")}
    bucket_counts = defaultdict(int)
    for subj, chapters in subject_data.items():
        for ch in chapters:
            b = chapter_to_bucket(ch)
            if b:
                bucket_counts[b] += 1

    build_index(subject_data, cluster_sets_count, bucket_counts)
    print("  ✓ index.html")

    total_html = total_chapter_files + total_cluster_files + 3 + 1  # 3 bucket + index
    print(f"\n✅ Done!")
    print(f"   Chapters covered  : {chapter_count}")
    print(f"   Cluster sets      : {cluster_sets_count}")
    print(f"   Total HTML files  : {total_html}")
    return chapter_count, cluster_sets_count, total_html

if __name__ == "__main__":
    chapter_count, cluster_sets_count, total_html = main()
