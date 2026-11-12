#!/usr/bin/env python3
"""
JEE Main PYQ Analysis — Priority Bucket System + Weightage Report + HTML Dashboards
Builds: 09_PRIORITY_SYSTEM/, 00_HIGHEST_WEIGHTAGE_PCM.html, index.html, subject dashboards
"""
import json, csv, os, sys, html
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "03_DATABASE"
REPORTS = ROOT / "04_MASTER_REPORTS"
ASSETS = ROOT / "06_ASSETS" / "styles"
PRIORITY_DIR = ROOT / "09_PRIORITY_SYSTEM"

# ─── Load database ────────────────────────────────────────────────
def load_questions():
    qs = []
    with open(DB / "questions.jsonl") as f:
        for line in f:
            line = line.strip()
            if line:
                qs.append(json.loads(line))
    return qs

def load_taxonomy():
    with open(DB / "chapter_taxonomy.json") as f:
        return json.load(f)

def load_clusters():
    with open(DB / "clusters.json") as f:
        return json.load(f)

def load_trends():
    with open(REPORTS / "trends_data.json") as f:
        return json.load(f)

# ─── Bucket Definitions (from user's reference) ──────────────────
BUCKET_1 = {
    "Physics": [
        "Units & Measurements",
        "Dual Nature of Radiation & Matter",
        "Atoms & Nuclei",
        "Semiconductors & Electronic Devices",
        "Electromagnetic Waves",
        "Current Electricity",
        "Electrostatics",
        "Ray Optics",
    ],
    "Chemistry": [
        "Periodic Properties",
        "Chemical Bonding & Molecular Structure",
        "Coordination Compounds",
        "d & f Block Elements",
        "Basic Organic Chemistry",  # GOC and Isomerism
        "Biomolecules",
        "Solutions",              # Liquid Solutions
        "Chemical Kinetics",
        "Electrochemistry",
    ],
    "Mathematics": [
        "Vectors",
        "3D Geometry",
        "Matrices",
        "Determinants",
        "Sequences & Series",
        "Statistics",
        "Quadratic Equations",
        "Binomial Theorem",
    ],
}

BUCKET_2 = {
    "Physics": [
        "Thermal Physics",        # includes Kinetic Theory + Thermodynamics
        "Magnetic Effects of Current",
        "Magnetism & Matter",
        "Electromagnetic Induction",
        "Alternating Current",
        "Wave Optics",
        "Gravitation",
        "Kinematics",
        "Laws of Motion",
        "Work Energy Power",
    ],
    "Chemistry": [
        "Atomic Structure",
        "Thermodynamics",
        "Some Basic Concepts of Chemistry",  # Mole Concept
        "Redox Reactions",
        "Hydrocarbons",
        "Haloalkanes & Haloarenes",
        "Alcohols Phenols & Ethers",
        "Aldehydes Ketones & Carboxylic Acids",
        "Amines",
        "p-Block Elements",
    ],
    "Mathematics": [
        "Sets Relations & Functions",
        "Limits",
        "Continuity & Differentiability",
        "Straight Lines",
        "Circles",
        "Integration",
        "Differential Equations",
        "Probability",
    ],
}

BUCKET_3 = {
    "Physics": [
        "Rotational Motion",
        "Properties of Matter",   # Fluid Mechanics
        "Oscillations",           # SHM
        "Waves",                  # included with SHM
    ],
    "Chemistry": [
        "Equilibrium",            # Ionic Equilibrium
        "States of Matter",       # Salt Analysis overlap
        "Surface Chemistry",
    ],
    "Mathematics": [
        "Complex Numbers",
        "Permutations & Combinations",
        "Parabola",
        "Ellipse",
        "Hyperbola",
        "Differentiation & Applications",
        "Trigonometry",
        "Mathematical Reasoning",
    ],
}

# Chemistry branch mapping
CHEM_BRANCH = {
    "Some Basic Concepts of Chemistry": "Physical",
    "Atomic Structure": "Physical",
    "Chemical Bonding & Molecular Structure": "Physical",
    "States of Matter": "Physical",
    "Thermodynamics": "Physical",
    "Equilibrium": "Physical",
    "Redox Reactions": "Physical",
    "Electrochemistry": "Physical",
    "Chemical Kinetics": "Physical",
    "Surface Chemistry": "Physical",
    "Solutions": "Physical",
    "Basic Organic Chemistry": "Organic",
    "Hydrocarbons": "Organic",
    "Haloalkanes & Haloarenes": "Organic",
    "Alcohols Phenols & Ethers": "Organic",
    "Aldehydes Ketones & Carboxylic Acids": "Organic",
    "Amines": "Organic",
    "Biomolecules": "Organic",
    "Polymers": "Organic",
    "Chemistry in Everyday Life": "Organic",
    "Periodic Properties": "Inorganic",
    "Hydrogen": "Inorganic",
    "s-Block Elements": "Inorganic",
    "p-Block Elements": "Inorganic",
    "d & f Block Elements": "Inorganic",
    "Coordination Compounds": "Inorganic",
    "Environmental Chemistry": "Inorganic",
}

def get_bucket(chapter_name):
    """Return (bucket_number, priority_label, strategy) for a chapter."""
    for subj in BUCKET_1:
        if chapter_name in BUCKET_1[subj]:
            return 1, "HIGH", "MASTER"
    for subj in BUCKET_2:
        if chapter_name in BUCKET_2[subj]:
            return 2, "MEDIUM-HIGH", "EXPAND"
    for subj in BUCKET_3:
        if chapter_name in BUCKET_3[subj]:
            return 3, "RESTRICTED", "FORMULA-ONLY"
    return 0, "UNASSIGNED", "REVIEW"

def get_subject_for_chapter(chapter_name):
    for subj in BUCKET_1:
        if chapter_name in BUCKET_1[subj]: return subj
    for subj in BUCKET_2:
        if chapter_name in BUCKET_2[subj]: return subj
    for subj in BUCKET_3:
        if chapter_name in BUCKET_3[subj]: return subj
    return None

# ─── Compute chapter statistics from real data ───────────────────
def compute_chapter_stats(questions):
    stats = defaultdict(lambda: {
        "total": 0, "years": set(), "shifts": set(),
        "year_counts": defaultdict(int), "difficulties": defaultdict(int),
        "question_types": defaultdict(int), "cluster_ids": set(),
        "subject": None
    })
    for q in questions:
        ch = q.get("chapter", "Unclassified") or "Unclassified"
        s = stats[ch]
        s["total"] += 1
        s["subject"] = q.get("subject")
        yr = q.get("year")
        if yr: 
            s["years"].add(yr)
            s["year_counts"][yr] += 1
        shift = q.get("shift")
        date = q.get("date","")
        if yr and shift:
            s["shifts"].add(f"{yr}-{date}-S{shift}")
        diff = q.get("difficulty","Unknown")
        s["difficulties"][diff] += 1
        qt = q.get("question_type","MCQ")
        s["question_types"][qt] += 1
        cid = q.get("cluster_id")
        if cid:
            s["cluster_ids"].add(cid)
    # Convert sets to sorted lists
    for ch in stats:
        stats[ch]["years"] = sorted(stats[ch]["years"])
        stats[ch]["shifts"] = sorted(stats[ch]["shifts"])
        stats[ch]["cluster_ids"] = sorted(stats[ch]["cluster_ids"])
    return dict(stats)

# ─── Priority scoring (evidence-based) ───────────────────────────
def compute_priority_score(ch_stats):
    """Score 0-100 based on historical frequency, recurrence, diversity."""
    total = ch_stats["total"]
    years = len(ch_stats["years"])
    shifts = len(ch_stats["shifts"])
    clusters = len(ch_stats["cluster_ids"])
    
    # Frequency score (0-40): based on total questions
    freq_score = min(40, total * 0.5)
    
    # Year recurrence (0-25): bonus for appearing in more years
    year_score = years * 5  # max 25 for 5 years
    
    # Shift coverage (0-20): how many distinct shifts
    shift_score = min(20, shifts * 0.25)
    
    # Archetype diversity (0-15): distinct clusters
    diversity_score = min(15, clusters * 0.5)
    
    return round(freq_score + year_score + shift_score + diversity_score, 1)

# ─── Detect bucket conflicts ─────────────────────────────────────
def detect_conflicts(chapter_name, bucket_num, priority_score, total_qs):
    conflicts = []
    if bucket_num == 3 and priority_score > 50:
        conflicts.append(f"BUCKET CONFLICT — HIGH HISTORICAL FREQUENCY: {total_qs} questions across dataset")
    if bucket_num == 3 and total_qs > 100:
        conflicts.append(f"BUCKET CONFLICT — VERY HIGH QUESTION COUNT: {total_qs} PYQs found, consider expanding coverage")
    if bucket_num == 1 and priority_score < 20:
        conflicts.append(f"LOW HISTORICAL FREQUENCY for Bucket 1: only {total_qs} questions found in dataset")
    if bucket_num == 1 and total_qs < 10:
        conflicts.append(f"VERY LOW QUESTION COUNT for Bucket 1: only {total_qs} PYQs — verify classification accuracy")
    return conflicts

# ─── CSS ──────────────────────────────────────────────────────────
def get_css():
    return """
<style>
:root{
  --primary:#1a237e; --accent:#e53935; --success:#2e7d32;
  --bg:#f5f5f5; --card:#fff; --shadow:0 2px 8px rgba(0,0,0,.12);
  --phy:#1565c0; --chem:#2e7d32; --math:#6a1b9a;
  --b1:#e8f5e9; --b1-border:#4caf50; --b1-text:#1b5e20;
  --b2:#fff3e0; --b2-border:#ff9800; --b2-text:#e65100;
  --b3:#fce4ec; --b3-border:#e91e63; --b3-text:#880e4f;
  --font:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:#212121;line-height:1.6}
.container{max-width:1400px;margin:0 auto;padding:24px}
h1{color:var(--primary);font-size:2rem;margin-bottom:8px;border-bottom:3px solid var(--primary);padding-bottom:8px}
h2{color:var(--primary);font-size:1.5rem;margin:24px 0 12px;border-bottom:2px solid #e0e0e0;padding-bottom:6px}
h3{color:#333;font-size:1.2rem;margin:16px 0 8px}
.meta{color:#666;font-size:.9rem;margin-bottom:20px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin:20px 0}
.stat-card{background:var(--card);border-radius:12px;padding:20px;box-shadow:var(--shadow);text-align:center;border-top:4px solid var(--primary)}
.stat-card.phy{border-top-color:var(--phy)} .stat-card.chem{border-top-color:var(--chem)} .stat-card.math{border-top-color:var(--math)}
.stat-card .number{font-size:2.5rem;font-weight:700;color:var(--primary)}
.stat-card .label{font-size:.85rem;color:#666;margin-top:4px}
.bucket-section{margin:24px 0;padding:24px;border-radius:12px;border-left:6px solid}
.bucket-1{background:var(--b1);border-left-color:var(--b1-border)}
.bucket-2{background:var(--b2);border-left-color:var(--b2-border)}
.bucket-3{background:var(--b3);border-left-color:var(--b3-border)}
.bucket-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.bucket-title{font-size:1.4rem;font-weight:700}
.bucket-1 .bucket-title{color:var(--b1-text)} .bucket-2 .bucket-title{color:var(--b2-text)} .bucket-3 .bucket-title{color:var(--b3-text)}
.target-badge{padding:6px 16px;border-radius:20px;font-weight:600;font-size:.9rem;color:#fff}
.bucket-1 .target-badge{background:var(--b1-border)} .bucket-2 .target-badge{background:var(--b2-border)} .bucket-3 .target-badge{background:var(--b3-border)}
table{width:100%;border-collapse:collapse;margin:12px 0;background:var(--card);border-radius:8px;overflow:hidden;box-shadow:var(--shadow)}
th{background:var(--primary);color:#fff;padding:12px 16px;text-align:left;font-weight:600;font-size:.85rem;text-transform:uppercase;letter-spacing:.5px}
td{padding:10px 16px;border-bottom:1px solid #e0e0e0;font-size:.9rem}
tr:hover{background:#f5f5f5}
tr:last-child td{border-bottom:none}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.75rem;font-weight:600}
.badge-b1{background:#c8e6c9;color:#1b5e20} .badge-b2{background:#ffe0b2;color:#e65100} .badge-b3{background:#f8bbd0;color:#880e4f} .badge-un{background:#e0e0e0;color:#424242}
.badge-easy{background:#c8e6c9;color:#1b5e20} .badge-moderate{background:#fff9c4;color:#f57f17} .badge-hard{background:#ffcdd2;color:#c62828}
.conflict{background:#fff3e0;border:2px solid #ff9800;border-radius:8px;padding:12px 16px;margin:8px 0;font-size:.85rem;color:#e65100;font-weight:500}
.conflict::before{content:'⚠ ';font-size:1.1rem}
.bar-chart{margin:12px 0}
.bar-row{display:flex;align-items:center;margin:4px 0;gap:8px}
.bar-label{width:250px;font-size:.8rem;text-align:right;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar{height:24px;border-radius:4px;transition:width .3s;min-width:2px;display:flex;align-items:center;padding-left:6px;color:#fff;font-size:.75rem;font-weight:600}
.bar.phy{background:var(--phy)} .bar.chem{background:var(--chem)} .bar.math{background:var(--math)}
.bar.b1{background:var(--b1-border)} .bar.b2{background:var(--b2-border)} .bar.b3{background:var(--b3-border)}
.nav{background:var(--primary);padding:12px 24px;border-radius:8px;margin-bottom:20px;display:flex;gap:16px;flex-wrap:wrap;align-items:center}
.nav a{color:#fff;text-decoration:none;padding:6px 16px;border-radius:6px;font-size:.9rem;transition:background .2s}
.nav a:hover{background:rgba(255,255,255,.2)}
.nav a.active{background:rgba(255,255,255,.3);font-weight:600}
.top10{background:linear-gradient(135deg,#fff8e1,#fff3e0);border:2px solid #ffa000;border-radius:8px;padding:4px 8px;font-weight:700}
a{color:var(--primary);text-decoration:none} a:hover{text-decoration:underline}
.subject-tag{display:inline-block;padding:2px 8px;border-radius:4px;color:#fff;font-size:.75rem;font-weight:600;margin-right:4px}
.subject-tag.phy{background:var(--phy)} .subject-tag.chem{background:var(--chem)} .subject-tag.math{background:var(--math)}
.search-box{width:100%;padding:12px 16px;border:2px solid #e0e0e0;border-radius:8px;font-size:1rem;margin:12px 0;outline:none;transition:border-color .2s}
.search-box:focus{border-color:var(--primary)}
.hidden{display:none}
details{margin:8px 0} details summary{cursor:pointer;font-weight:600;color:var(--primary);padding:4px 0}
.print-only{display:none}
@media print{
  .nav,.search-box{display:none!important}
  .print-only{display:block}
  .bucket-section{break-inside:avoid}
  body{background:#fff}
  table{box-shadow:none;border:1px solid #ccc}
}
@media(max-width:768px){
  .container{padding:12px}
  .bar-label{width:150px;font-size:.7rem}
  .stats-grid{grid-template-columns:1fr 1fr}
}
</style>
"""

# ─── Build priority metadata JSON ────────────────────────────────
def build_priority_metadata(questions, ch_stats):
    metadata = []
    all_chapters = set()
    for q in questions:
        ch = q.get("chapter")
        subj = q.get("subject")
        if ch and ch != "Unclassified":
            all_chapters.add((subj, ch))
    
    for subj, ch in sorted(all_chapters):
        bucket_num, priority, strategy = get_bucket(ch)
        st = ch_stats.get(ch, {"total":0,"years":[],"shifts":[],"cluster_ids":[],"year_counts":{},"difficulties":{}})
        score = compute_priority_score(st)
        conflicts = detect_conflicts(ch, bucket_num, score, st["total"])
        
        depth_map = {1: "DEEP", 2: "THOROUGH", 3: "RESTRICTED", 0: "REVIEW"}
        
        entry = {
            "subject": subj,
            "chapter": ch,
            "bucket": bucket_num,
            "priority": priority,
            "reference_strategy": strategy,
            "pyq_frequency": st["total"],
            "years_appeared": st["years"],
            "shifts_appeared": len(st["shifts"]),
            "question_count": st["total"],
            "cluster_count": len(st["cluster_ids"]),
            "clusters": st["cluster_ids"][:20],  # top 20
            "year_wise": dict(st["year_counts"]),
            "difficulty_distribution": dict(st["difficulties"]),
            "priority_score": score,
            "recommended_study_depth": depth_map.get(bucket_num, "REVIEW"),
            "conflicts": conflicts,
            "status": "NOT_STARTED",
            "chemistry_branch": CHEM_BRANCH.get(ch, None) if subj == "Chemistry" else None,
        }
        metadata.append(entry)
    
    return metadata

# ─── HTML Generators ──────────────────────────────────────────────

def nav_html(active=""):
    items = [
        ("index.html", "🏠 Dashboard"),
        ("00_HIGHEST_WEIGHTAGE_PCM.html", "📊 Weightage Report"),
        ("09_PRIORITY_SYSTEM/index.html", "🎯 Priority System"),
        ("Physics/index.html", "🔵 Physics"),
        ("Chemistry/index.html", "🟢 Chemistry"),
        ("Mathematics/index.html", "🟣 Mathematics"),
    ]
    links = ""
    for href, label in items:
        cls = ' class="active"' if label == active else ""
        links += f'<a href="{href}"{cls}>{label}</a>\n'
    return f'<nav class="nav">{links}</nav>'

def escape(text):
    return html.escape(str(text)) if text else ""

def badge_bucket(bucket_num):
    m = {1:"badge-b1", 2:"badge-b2", 3:"badge-b3", 0:"badge-un"}
    labels = {1:"Bucket 1", 2:"Bucket 2", 3:"Bucket 3", 0:"Unassigned"}
    return f'<span class="badge {m.get(bucket_num,"badge-un")}">{labels.get(bucket_num,"Review")}</span>'

def subject_tag(subj):
    cls = {"Physics":"phy","Chemistry":"chem","Mathematics":"math"}.get(subj,"")
    return f'<span class="subject-tag {cls}">{escape(subj)}</span>'

# ─── Generate 00_HIGHEST_WEIGHTAGE_PCM.html ──────────────────────
def generate_weightage_report(metadata, ch_stats, questions):
    # Sort all chapters by total PYQs descending
    all_chapters = [m for m in metadata if m["question_count"] > 0]
    all_chapters.sort(key=lambda x: x["question_count"], reverse=True)
    
    # Year-wise data
    years = sorted(set(q.get("year") for q in questions if q.get("year")))
    
    total_qs = sum(m["question_count"] for m in all_chapters)
    total_papers = 90  # from ingestion
    
    # Max for bar scaling
    max_qs = all_chapters[0]["question_count"] if all_chapters else 1
    
    h = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JEE Main PYQ — Highest Weightage PCM Chapters</title>
{get_css()}
</head><body>
<div class="container">
{nav_html("📊 Weightage Report")}
<h1>📊 Highest Weightage PCM Chapters — 5-Year Analysis</h1>
<p class="meta">Based on {total_qs} questions extracted from {total_papers} papers across {len(years)} years ({', '.join(str(y) for y in years)})</p>

<div class="stats-grid">
<div class="stat-card"><div class="number">{total_qs}</div><div class="label">Total Questions Analysed</div></div>
<div class="stat-card"><div class="number">{total_papers}</div><div class="label">Papers Processed</div></div>
<div class="stat-card"><div class="number">{len(all_chapters)}</div><div class="label">Chapters Identified</div></div>
<div class="stat-card"><div class="number">{len(years)}</div><div class="label">Years Covered</div></div>
</div>

<h2>1. Overall Ranking — All Subjects Combined</h2>
<p>Every chapter from Physics, Chemistry, and Mathematics sorted by total PYQ question count.</p>

<input type="text" class="search-box" id="searchAll" placeholder="🔍 Search chapters..." onkeyup="filterTable('overallTable','searchAll')">

<table id="overallTable">
<thead><tr>
<th>Rank</th><th>Subject</th><th>Chapter</th><th>Bucket</th><th>Total PYQs</th><th>Years</th><th>Shifts</th><th>Avg/Shift</th><th>Clusters</th><th>Priority Score</th>
</tr></thead><tbody>
"""
    for i, m in enumerate(all_chapters, 1):
        avg_per_shift = round(m["question_count"] / max(m["shifts_appeared"],1), 1)
        top10_cls = ' class="top10"' if i <= 10 else ""
        conflicts_html = ""
        for c in m.get("conflicts", []):
            conflicts_html += f'<div class="conflict">{escape(c)}</div>'
        
        # Link to chapter folder
        ch_slug = m["chapter"].replace(" ", "_").replace("&","and")
        if m["subject"] == "Chemistry":
            branch = CHEM_BRANCH.get(m["chapter"],"Physical")
            ch_link = f'Chemistry/{branch}_Chemistry/{ch_slug}/chapter_analysis.html'
        elif m["subject"] == "Physics":
            ch_link = f'Physics/chapters/{ch_slug}/chapter_analysis.html'
        else:
            ch_link = f'Mathematics/chapters/{ch_slug}/chapter_analysis.html'
        
        h += f"""<tr>
<td{top10_cls}>{i}</td>
<td>{subject_tag(m["subject"])}</td>
<td><a href="{ch_link}">{escape(m["chapter"])}</a>{conflicts_html}</td>
<td>{badge_bucket(m["bucket"])}</td>
<td><strong>{m["question_count"]}</strong></td>
<td>{len(m["years_appeared"])}</td>
<td>{m["shifts_appeared"]}</td>
<td>{avg_per_shift}</td>
<td>{m["cluster_count"]}</td>
<td>{m["priority_score"]}</td>
</tr>
"""
    h += "</tbody></table>"
    
    # ─── Subject-wise rankings ───
    for subj, subj_cls in [("Physics","phy"),("Chemistry","chem"),("Mathematics","math")]:
        subj_chapters = [m for m in all_chapters if m["subject"] == subj]
        h += f'\n<h2>2.{"A" if subj=="Physics" else "B" if subj=="Chemistry" else "C"}. {subj} — Highest Weightage Chapters</h2>\n'
        
        if subj == "Chemistry":
            # Group by branch
            for branch in ["Physical","Organic","Inorganic"]:
                branch_chs = [m for m in subj_chapters if CHEM_BRANCH.get(m["chapter"],"") == branch]
                if branch_chs:
                    h += f'<h3>{branch} Chemistry</h3>\n'
                    h += _chapter_table(branch_chs, years)
        else:
            h += _chapter_table(subj_chapters, years)
        
        # Bar chart
        h += f'<div class="bar-chart">'
        for m in subj_chapters[:20]:
            w = max(2, int(m["question_count"] / max_qs * 600))
            h += f'<div class="bar-row"><span class="bar-label">{escape(m["chapter"])}</span><div class="bar {subj_cls}" style="width:{w}px">{m["question_count"]}</div></div>\n'
        h += '</div>'
    
    # ─── Year-wise breakdown ───
    h += '\n<h2>3. Year-Wise Breakdown</h2>\n'
    h += '<table><thead><tr><th>Chapter</th><th>Subject</th><th>Bucket</th>'
    for y in years:
        h += f'<th>{y}</th>'
    h += '<th>Total</th><th>Years Present</th><th>Avg/Shift</th></tr></thead><tbody>\n'
    
    for m in all_chapters:
        h += f'<tr><td>{escape(m["chapter"])}</td><td>{subject_tag(m["subject"])}</td><td>{badge_bucket(m["bucket"])}</td>'
        for y in years:
            cnt = m["year_wise"].get(str(y), m["year_wise"].get(y, 0))
            h += f'<td>{cnt if cnt else "—"}</td>'
        avg = round(m["question_count"] / max(m["shifts_appeared"],1), 1)
        h += f'<td><strong>{m["question_count"]}</strong></td><td>{len(m["years_appeared"])}</td><td>{avg}</td></tr>\n'
    h += '</tbody></table>\n'
    
    # ─── Visualisation: combined PCM bar chart ───
    h += '\n<h2>4. Combined PCM Chapter Ranking — Top 20</h2>\n'
    h += '<div class="bar-chart">'
    for i, m in enumerate(all_chapters[:20], 1):
        subj_cls = {"Physics":"phy","Chemistry":"chem","Mathematics":"math"}.get(m["subject"],"phy")
        w = max(2, int(m["question_count"] / max_qs * 700))
        top = " 🏆" if i <= 3 else ""
        h += f'<div class="bar-row"><span class="bar-label">#{i} {escape(m["chapter"])}{top}</span><div class="bar {subj_cls}" style="width:{w}px">{m["question_count"]}</div></div>\n'
    h += '</div>'
    
    # ─── Top 10 highlight ───
    h += '\n<h2>5. Top 10 Most Frequently Appearing Chapters</h2>\n'
    h += '<div class="stats-grid">'
    for i, m in enumerate(all_chapters[:10], 1):
        subj_cls = {"Physics":"phy","Chemistry":"chem","Mathematics":"math"}.get(m["subject"],"phy")
        h += f'''<div class="stat-card {subj_cls}">
<div class="number">#{i}</div>
<div class="label">{escape(m["chapter"])}<br>{subject_tag(m["subject"])}<br><strong>{m["question_count"]} PYQs</strong> · {len(m["years_appeared"])} years</div>
</div>'''
    h += '</div>'
    
    # ─── Priority bucket conflicts section ───
    h += '\n<h2>6. Bucket Conflict Analysis</h2>\n'
    conflict_chapters = [m for m in all_chapters if m.get("conflicts")]
    if conflict_chapters:
        h += f'<p>{len(conflict_chapters)} chapters have conflicts between assigned bucket and historical data:</p>\n'
        h += '<table><thead><tr><th>Chapter</th><th>Subject</th><th>Bucket</th><th>PYQs</th><th>Score</th><th>Conflicts</th></tr></thead><tbody>\n'
        for m in conflict_chapters:
            conflicts_html = "<br>".join(f'<span class="conflict">{escape(c)}</span>' for c in m["conflicts"])
            h += f'<tr><td>{escape(m["chapter"])}</td><td>{subject_tag(m["subject"])}</td><td>{badge_bucket(m["bucket"])}</td><td>{m["question_count"]}</td><td>{m["priority_score"]}</td><td>{conflicts_html}</td></tr>\n'
        h += '</tbody></table>'
    else:
        h += '<p>No conflicts detected.</p>'
    
    # ─── Data accuracy note ───
    h += '''
<h2>7. Data Accuracy & Methodology</h2>
<div style="background:#e3f2fd;border-radius:8px;padding:16px;margin:12px 0">
<h3>How These Numbers Were Calculated</h3>
<ul>
<li><strong>Source:</strong> 90 MathonGo JEE Main papers (2021–2025), all available sessions and shifts</li>
<li><strong>Extraction:</strong> PyMuPDF text extraction with regex-based question boundary detection</li>
<li><strong>Classification:</strong> Keyword-based chapter matching against 73-chapter JEE Main taxonomy</li>
<li><strong>Counting:</strong> Each question occurrence counted once per paper; no duplicate paper counting</li>
<li><strong>Limitations:</strong> Keyword matching may misclassify some questions. 2062 questions flagged as "Unclassified" due to low confidence</li>
<li><strong>Not predictions:</strong> These are historical occurrence counts, not guaranteed future weightage</li>
</ul>
</div>
'''
    
    h += """
<script>
function filterTable(tableId, inputId) {
    var input = document.getElementById(inputId);
    var filter = input.value.toLowerCase();
    var table = document.getElementById(tableId);
    var rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    for (var i = 0; i < rows.length; i++) {
        var text = rows[i].textContent.toLowerCase();
        rows[i].style.display = text.indexOf(filter) > -1 ? '' : 'none';
    }
}
</script>
</div></body></html>
"""
    
    with open(ROOT / "00_HIGHEST_WEIGHTAGE_PCM.html", "w") as f:
        f.write(h)
    print("[OK] Generated 00_HIGHEST_WEIGHTAGE_PCM.html")
    return h

def _chapter_table(chapters, years):
    h = '<table><thead><tr><th>Rank</th><th>Chapter</th><th>Bucket</th><th>Total PYQs</th>'
    for y in years:
        h += f'<th>{y}</th>'
    h += '<th>Years</th><th>Shifts</th><th>Score</th></tr></thead><tbody>\n'
    for i, m in enumerate(chapters, 1):
        h += f'<tr><td>{i}</td><td>{escape(m["chapter"])}</td><td>{badge_bucket(m["bucket"])}</td><td><strong>{m["question_count"]}</strong></td>'
        for y in years:
            cnt = m["year_wise"].get(str(y), m["year_wise"].get(y, 0))
            h += f'<td>{cnt if cnt else "—"}</td>'
        h += f'<td>{len(m["years_appeared"])}</td><td>{m["shifts_appeared"]}</td><td>{m["priority_score"]}</td></tr>\n'
    h += '</tbody></table>\n'
    return h

# ─── Generate 09_PRIORITY_SYSTEM ─────────────────────────────────
def generate_priority_system(metadata, ch_stats, questions):
    # Create directory structure
    for d in [
        PRIORITY_DIR,
        PRIORITY_DIR / "bucket_1_high_priority" / "Physics",
        PRIORITY_DIR / "bucket_1_high_priority" / "Chemistry",
        PRIORITY_DIR / "bucket_1_high_priority" / "Mathematics",
        PRIORITY_DIR / "bucket_2_expansion" / "Physics",
        PRIORITY_DIR / "bucket_2_expansion" / "Chemistry",
        PRIORITY_DIR / "bucket_2_expansion" / "Mathematics",
        PRIORITY_DIR / "bucket_3_restricted" / "Physics",
        PRIORITY_DIR / "bucket_3_restricted" / "Chemistry",
        PRIORITY_DIR / "bucket_3_restricted" / "Mathematics",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Save priority metadata JSON
    with open(PRIORITY_DIR / "priority_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    
    years = sorted(set(q.get("year") for q in questions if q.get("year")))
    
    # ─── Main priority dashboard ───
    b1 = [m for m in metadata if m["bucket"] == 1]
    b2 = [m for m in metadata if m["bucket"] == 2]
    b3 = [m for m in metadata if m["bucket"] == 3]
    b0 = [m for m in metadata if m["bucket"] == 0]
    
    total_b1 = sum(m["question_count"] for m in b1)
    total_b2 = sum(m["question_count"] for m in b2)
    total_b3 = sum(m["question_count"] for m in b3)
    
    h = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JEE Main PYQ — Three-Bucket Priority System</title>
{get_css()}
</head><body>
<div class="container">
{nav_html("🎯 Priority System")}
<h1>🎯 Three-Bucket Chapter Priority System</h1>
<p class="meta">Strategy: Bucket 1 → Master First | Bucket 2 → Expand Coverage | Bucket 3 → Formula-Only / Restricted<br>
Data: {sum(m["question_count"] for m in metadata)} classified questions from {len(years)} years ({', '.join(str(y) for y in years)})</p>

<div class="stats-grid">
<div class="stat-card" style="border-top-color:var(--b1-border)"><div class="number" style="color:var(--b1-text)">{len(b1)}</div><div class="label">Bucket 1 Chapters<br>{total_b1} PYQs</div></div>
<div class="stat-card" style="border-top-color:var(--b2-border)"><div class="number" style="color:var(--b2-text)">{len(b2)}</div><div class="label">Bucket 2 Chapters<br>{total_b2} PYQs</div></div>
<div class="stat-card" style="border-top-color:var(--b3-border)"><div class="number" style="color:var(--b3-text)">{len(b3)}</div><div class="label">Bucket 3 Chapters<br>{total_b3} PYQs</div></div>
<div class="stat-card"><div class="number">{len(b0)}</div><div class="label">Unassigned<br>Needs Review</div></div>
</div>

<div style="display:flex;gap:12px;margin:16px 0;flex-wrap:wrap">
<a href="bucket_1_high_priority/index.html" class="target-badge" style="background:var(--b1-border);color:#fff;text-decoration:none">📗 Bucket 1 Details →</a>
<a href="bucket_2_expansion/index.html" class="target-badge" style="background:var(--b2-border);color:#fff;text-decoration:none">📙 Bucket 2 Details →</a>
<a href="bucket_3_restricted/index.html" class="target-badge" style="background:var(--b3-border);color:#fff;text-decoration:none">📕 Bucket 3 Details →</a>
<a href="priority_comparison.html" class="target-badge" style="background:var(--primary);color:#fff;text-decoration:none">📊 Full Comparison →</a>
</div>
"""
    
    # ─── BUCKET 1 Section ───
    h += _bucket_section_html(1, b1, "HIGH PRIORITY — Master First",
        "🟢 These chapters form the foundation. Master every concept, cluster, and question archetype.",
        {"Physics": "48–52 marks", "Chemistry": "48–52 marks", "Mathematics": "28–32 marks"},
        years)
    
    # ─── BUCKET 2 Section ───
    h += _bucket_section_html(2, b2, "EXPANSION — Boost Coverage",
        "🟠 Study after establishing Bucket 1. Provides additional ~65 marks coverage.",
        {"Overall": "~65 marks additional"},
        years)
    
    # ─── BUCKET 3 Section ───
    h += _bucket_section_html(3, b3, "FORMULA-ONLY / RESTRICTED",
        "🔴 Cover standard formulae, definitions, and recurring PYQ patterns. Avoid deep-diving uncommon variations until Buckets 1 & 2 are solid.",
        {},
        years)
    
    # ─── Unassigned ───
    if b0:
        h += '<h2>⚠ Unassigned Chapters (Not in Reference Image)</h2>\n'
        h += '<p>These chapters were found in the database but not assigned to any bucket. Review and assign manually.</p>\n'
        h += _priority_table(b0, years)
    
    # ─── Study strategy sections ───
    h += """
<h2>Study Strategy by Bucket</h2>

<div class="bucket-section bucket-1">
<h3>Bucket 1 — MASTERY Strategy</h3>
<ol>
<li>Complete the fundamental theory for each chapter</li>
<li>Understand all important concepts and their interconnections</li>
<li>Learn required formulas, principles, and derivations</li>
<li>Study every identified question archetype (cluster)</li>
<li>Solve ALL available PYQs from 2021–2025</li>
<li>Practise variations within each cluster</li>
<li>Revise mistakes and difficult questions systematically</li>
</ol>
<p><strong>Goal:</strong> Recognise and solve the full range of standard JEE Main problems from these chapters.</p>
</div>

<div class="bucket-section bucket-2">
<h3>Bucket 2 — EXPANSION Strategy</h3>
<ol>
<li>Cover the standard theory thoroughly</li>
<li>Identify commonly tested concepts using cluster analysis</li>
<li>Study recurring clusters (highest frequency first)</li>
<li>Cover standard and moderate difficulty questions</li>
<li>Practise PYQs across all available years</li>
<li>Identify which difficult variations deserve additional attention</li>
</ol>
<p><strong>Goal:</strong> Strong and reasonably broad coverage to boost score beyond Bucket 1.</p>
</div>

<div class="bucket-section bucket-3">
<h3>Bucket 3 — RESTRICTED Strategy</h3>
<ol>
<li>Identify and memorise standard formulae</li>
<li>Cover fundamental definitions and concepts</li>
<li>Learn the most common direct applications</li>
<li>Identify recurring basic PYQ patterns from cluster analysis</li>
<li>Solve standard and accessible PYQs only</li>
<li>Avoid disproportionate time on rare, advanced variations</li>
</ol>
<p><strong>Goal:</strong> Maximise useful coverage while strictly controlling preparation time.</p>
</div>
"""
    
    h += '</div></body></html>'
    
    with open(PRIORITY_DIR / "index.html", "w") as f:
        f.write(h)
    print("[OK] Generated 09_PRIORITY_SYSTEM/index.html")
    
    # ─── Bucket sub-pages ───
    for bucket_num, folder, title in [
        (1, "bucket_1_high_priority", "Bucket 1 — High Priority"),
        (2, "bucket_2_expansion", "Bucket 2 — Expansion"),
        (3, "bucket_3_restricted", "Bucket 3 — Restricted"),
    ]:
        bucket_chapters = [m for m in metadata if m["bucket"] == bucket_num]
        _generate_bucket_page(bucket_num, folder, title, bucket_chapters, years, questions)
    
    # ─── Priority comparison page ───
    _generate_comparison_page(metadata, years)

def _bucket_section_html(bucket_num, chapters, title, description, targets, years):
    bucket_cls = f"bucket-{bucket_num}"
    h = f'\n<div class="bucket-section {bucket_cls}">\n'
    h += f'<div class="bucket-header"><span class="bucket-title">BUCKET {bucket_num}: {title}</span>\n'
    if targets:
        badges = " | ".join(f'{k}: {v}' for k, v in targets.items())
        h += f'<span class="target-badge">🎯 {badges}</span>'
    h += '</div>\n'
    h += f'<p>{description}</p>\n'
    
    # Subject breakdown
    for subj in ["Physics", "Chemistry", "Mathematics"]:
        subj_chs = [m for m in chapters if m["subject"] == subj]
        if subj_chs:
            h += f'<h3>{subject_tag(subj)} {subj} ({len(subj_chs)} chapters, {sum(m["question_count"] for m in subj_chs)} PYQs)</h3>\n'
            h += _priority_table(subj_chs, years)
    
    # Conflicts
    conflict_chs = [m for m in chapters if m.get("conflicts")]
    if conflict_chs:
        for m in conflict_chs:
            for c in m["conflicts"]:
                h += f'<div class="conflict">{escape(m["chapter"])}: {escape(c)}</div>\n'
    
    h += '</div>\n'
    return h

def _priority_table(chapters, years):
    chapters_sorted = sorted(chapters, key=lambda x: x["question_count"], reverse=True)
    h = '<table><thead><tr><th>#</th><th>Chapter</th><th>PYQs</th>'
    for y in years:
        h += f'<th>{y}</th>'
    h += '<th>Years</th><th>Clusters</th><th>Score</th><th>Strategy</th></tr></thead><tbody>\n'
    
    for i, m in enumerate(chapters_sorted, 1):
        h += f'<tr><td>{i}</td><td>{escape(m["chapter"])}</td><td><strong>{m["question_count"]}</strong></td>'
        for y in years:
            cnt = m["year_wise"].get(str(y), m["year_wise"].get(y, 0))
            h += f'<td>{cnt if cnt else "—"}</td>'
        h += f'<td>{len(m["years_appeared"])}</td><td>{m["cluster_count"]}</td><td>{m["priority_score"]}</td><td>{escape(m["reference_strategy"])}</td></tr>\n'
    h += '</tbody></table>\n'
    return h

def _generate_bucket_page(bucket_num, folder, title, chapters, years, questions):
    bucket_cls = f"bucket-{bucket_num}"
    total_qs = sum(m["question_count"] for m in chapters)
    
    strategy_desc = {
        1: "Complete mastery of every concept, cluster, and question archetype.",
        2: "Thorough coverage with focus on recurring patterns and commonly tested concepts.",
        3: "Standard formulae, definitions, and direct applications only. Control time expenditure.",
    }
    
    h = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JEE Main PYQ — {title}</title>
{get_css()}
</head><body>
<div class="container">
<nav class="nav"><a href="../index.html">← Priority Dashboard</a><a href="../../index.html">🏠 Home</a></nav>
<h1>🎯 {title}</h1>
<p class="meta">{len(chapters)} chapters · {total_qs} PYQs · Strategy: {strategy_desc.get(bucket_num,"")}</p>

<div class="stats-grid">
"""
    for subj in ["Physics","Chemistry","Mathematics"]:
        s_chs = [m for m in chapters if m["subject"] == subj]
        s_total = sum(m["question_count"] for m in s_chs)
        subj_cls = {"Physics":"phy","Chemistry":"chem","Mathematics":"math"}.get(subj,"")
        h += f'<div class="stat-card {subj_cls}"><div class="number">{len(s_chs)}</div><div class="label">{subj} Chapters<br>{s_total} PYQs</div></div>\n'
    
    h += '</div>\n'
    
    # Per-subject detail
    for subj in ["Physics","Chemistry","Mathematics"]:
        s_chs = sorted([m for m in chapters if m["subject"] == subj], key=lambda x: x["question_count"], reverse=True)
        if not s_chs: continue
        
        h += f'<h2>{subject_tag(subj)} {subj}</h2>\n'
        
        if subj == "Chemistry":
            for branch in ["Physical","Organic","Inorganic"]:
                branch_chs = [m for m in s_chs if CHEM_BRANCH.get(m["chapter"],"") == branch]
                if branch_chs:
                    h += f'<h3>{branch} Chemistry</h3>\n'
                    for m in branch_chs:
                        h += _chapter_detail_card(m, years, questions, bucket_num)
        else:
            for m in s_chs:
                h += _chapter_detail_card(m, years, questions, bucket_num)
    
    h += '</div></body></html>'
    
    with open(PRIORITY_DIR / folder / "index.html", "w") as f:
        f.write(h)
    print(f"[OK] Generated 09_PRIORITY_SYSTEM/{folder}/index.html")

def _chapter_detail_card(m, years, questions, bucket_num):
    """Generate a detailed card for one chapter inside a bucket page."""
    h = f'<details style="margin:8px 0;background:var(--card);border-radius:8px;padding:16px;box-shadow:var(--shadow)">\n'
    h += f'<summary style="font-size:1.1rem"><strong>{escape(m["chapter"])}</strong> — {m["question_count"]} PYQs, {m["cluster_count"]} clusters, Score: {m["priority_score"]}</summary>\n'
    
    # Year-wise mini-table
    h += '<table style="margin:12px 0"><thead><tr>'
    for y in years:
        h += f'<th>{y}</th>'
    h += '<th>Total</th></tr></thead><tbody><tr>'
    for y in years:
        cnt = m["year_wise"].get(str(y), m["year_wise"].get(y, 0))
        h += f'<td>{cnt if cnt else "—"}</td>'
    h += f'<td><strong>{m["question_count"]}</strong></td></tr></tbody></table>\n'
    
    # Clusters list
    if m["clusters"]:
        h += '<p><strong>Question Clusters:</strong></p><ul>'
        for cid in m["clusters"][:10]:
            h += f'<li><code>{escape(cid)}</code></li>'
        if len(m["clusters"]) > 10:
            h += f'<li>... and {len(m["clusters"])-10} more</li>'
        h += '</ul>\n'
    
    # Conflicts
    for c in m.get("conflicts",[]):
        h += f'<div class="conflict">{escape(c)}</div>\n'
    
    h += '</details>\n'
    return h

def _generate_comparison_page(metadata, years):
    """Generate the full priority comparison table page."""
    h = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JEE Main PYQ — Priority Comparison</title>
{get_css()}
</head><body>
<div class="container">
<nav class="nav"><a href="index.html">← Priority Dashboard</a><a href="../index.html">🏠 Home</a></nav>
<h1>📊 Full Chapter Priority Comparison</h1>
<p class="meta">All chapters sorted by subject, with bucket assignment vs. historical evidence</p>

<input type="text" class="search-box" id="searchComp" placeholder="🔍 Search chapters..." onkeyup="filterTable('compTable','searchComp')">
"""
    for subj in ["Physics","Chemistry","Mathematics"]:
        s_chs = sorted([m for m in metadata if m["subject"] == subj], key=lambda x: x["question_count"], reverse=True)
        h += f'<h2>{subject_tag(subj)} {subj}</h2>\n'
        h += '<table id="compTable"><thead><tr><th>Chapter</th><th>Bucket</th><th>PYQs</th><th>Years</th><th>Clusters</th><th>Score</th><th>Strategy</th><th>Conflicts</th></tr></thead><tbody>\n'
        for m in s_chs:
            conflict_html = "<br>".join(f'⚠ {escape(c)}' for c in m.get("conflicts",[])) or "—"
            h += f'<tr><td>{escape(m["chapter"])}</td><td>{badge_bucket(m["bucket"])}</td><td><strong>{m["question_count"]}</strong></td><td>{len(m["years_appeared"])}</td><td>{m["cluster_count"]}</td><td>{m["priority_score"]}</td><td>{escape(m["reference_strategy"])}</td><td style="font-size:.8rem">{conflict_html}</td></tr>\n'
        h += '</tbody></table>\n'
    
    h += """
<script>
function filterTable(tableId, inputId) {
    var input = document.getElementById(inputId);
    var filter = input.value.toLowerCase();
    var tables = document.querySelectorAll('table');
    tables.forEach(function(table) {
        var rows = table.querySelectorAll('tbody tr');
        rows.forEach(function(row) {
            row.style.display = row.textContent.toLowerCase().indexOf(filter) > -1 ? '' : 'none';
        });
    });
}
</script>
</div></body></html>
"""
    with open(PRIORITY_DIR / "priority_comparison.html", "w") as f:
        f.write(h)
    print("[OK] Generated 09_PRIORITY_SYSTEM/priority_comparison.html")

# ─── Generate Main Dashboard (index.html) ────────────────────────
def generate_main_dashboard(metadata, ch_stats, questions, clusters_data):
    years = sorted(set(q.get("year") for q in questions if q.get("year")))
    total_qs = len(questions)
    classified = sum(1 for q in questions if q.get("chapter") and q["chapter"] != "Unclassified")
    
    h = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JEE Main PYQ Analysis System — Dashboard</title>
{get_css()}
</head><body>
<div class="container">
{nav_html("🏠 Dashboard")}
<h1>JEE Main PYQ Analysis System</h1>
<p class="meta">5-Year Analysis · 90 Papers · {total_qs} Questions · 73 Chapters · {len(years)} Years ({', '.join(str(y) for y in years)})</p>

<div class="stats-grid">
<div class="stat-card"><div class="number">{total_qs}</div><div class="label">Total Questions</div></div>
<div class="stat-card"><div class="number">90</div><div class="label">Papers Processed</div></div>
<div class="stat-card"><div class="number">{classified}</div><div class="label">Questions Classified</div></div>
<div class="stat-card phy"><div class="number">2700</div><div class="label">Physics Questions</div></div>
<div class="stat-card chem"><div class="number">2700</div><div class="label">Chemistry Questions</div></div>
<div class="stat-card math"><div class="number">2559</div><div class="label">Mathematics Questions</div></div>
</div>

<h2>📌 Quick Links</h2>
<div class="stats-grid">
<div class="stat-card"><a href="00_HIGHEST_WEIGHTAGE_PCM.html" style="text-decoration:none"><div class="number" style="font-size:1.5rem">📊</div><div class="label">Highest Weightage PCM<br>Chapter Rankings</div></a></div>
<div class="stat-card"><a href="09_PRIORITY_SYSTEM/index.html" style="text-decoration:none"><div class="number" style="font-size:1.5rem">🎯</div><div class="label">Three-Bucket<br>Priority System</div></a></div>
<div class="stat-card"><a href="09_PRIORITY_SYSTEM/priority_comparison.html" style="text-decoration:none"><div class="number" style="font-size:1.5rem">📋</div><div class="label">Priority Comparison<br>All Chapters</div></a></div>
</div>

<h2>📚 Subject Navigation</h2>
<div class="stats-grid">
"""
    for subj, cls, icon in [("Physics","phy","🔵"),("Chemistry","chem","🟢"),("Mathematics","math","🟣")]:
        s_chs = [m for m in metadata if m["subject"] == subj]
        s_total = sum(m["question_count"] for m in s_chs)
        top_ch = max(s_chs, key=lambda x: x["question_count"])["chapter"] if s_chs else "—"
        h += f'''<div class="stat-card {cls}">
<a href="{subj}/index.html" style="text-decoration:none;color:inherit">
<div class="number" style="font-size:1.5rem">{icon}</div>
<div class="label"><strong>{subj}</strong><br>{len(s_chs)} chapters · {s_total} PYQs<br>Top: {escape(top_ch)}</div>
</a></div>
'''
    h += '</div>\n'
    
    # Top 10 chapters
    all_sorted = sorted(metadata, key=lambda x: x["question_count"], reverse=True)
    h += '<h2>🏆 Top 10 Highest-Frequency Chapters</h2>\n'
    h += '<table><thead><tr><th>Rank</th><th>Subject</th><th>Chapter</th><th>Bucket</th><th>PYQs</th><th>Years</th><th>Clusters</th></tr></thead><tbody>\n'
    for i, m in enumerate(all_sorted[:10], 1):
        h += f'<tr><td>{i}</td><td>{subject_tag(m["subject"])}</td><td>{escape(m["chapter"])}</td><td>{badge_bucket(m["bucket"])}</td><td><strong>{m["question_count"]}</strong></td><td>{len(m["years_appeared"])}</td><td>{m["cluster_count"]}</td></tr>\n'
    h += '</tbody></table>\n'
    
    # Year coverage
    h += '<h2>📅 Year Coverage</h2>\n'
    h += '<div class="stats-grid">'
    year_counts = defaultdict(int)
    for q in questions:
        yr = q.get("year")
        if yr: year_counts[yr] += 1
    for y in years:
        papers = sum(1 for q in questions if q.get("year") == y) // 30 if year_counts[y] > 0 else 0
        # Count papers from source inventory
        h += f'<div class="stat-card"><div class="number">{year_counts[y]}</div><div class="label">{y}<br>Questions</div></div>\n'
    h += '</div>\n'
    
    h += '</div></body></html>'
    
    with open(ROOT / "index.html", "w") as f:
        f.write(h)
    print("[OK] Generated index.html")

# ─── Generate Subject Dashboards ─────────────────────────────────
def generate_subject_dashboards(metadata, ch_stats, questions):
    years = sorted(set(q.get("year") for q in questions if q.get("year")))
    
    for subj in ["Physics","Chemistry","Mathematics"]:
        subj_dir = ROOT / subj
        subj_dir.mkdir(exist_ok=True)
        
        s_chs = sorted([m for m in metadata if m["subject"] == subj], key=lambda x: x["question_count"], reverse=True)
        s_total = sum(m["question_count"] for m in s_chs)
        cls = {"Physics":"phy","Chemistry":"chem","Mathematics":"math"}.get(subj,"")
        icon = {"Physics":"🔵","Chemistry":"🟢","Mathematics":"🟣"}.get(subj,"")
        
        h = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JEE Main PYQ — {subj}</title>
{get_css()}
</head><body>
<div class="container">
<nav class="nav"><a href="../index.html">🏠 Home</a><a href="../09_PRIORITY_SYSTEM/index.html">🎯 Priority</a><a href="../00_HIGHEST_WEIGHTAGE_PCM.html">📊 Weightage</a></nav>
<h1>{icon} {subj} — Chapter Analysis</h1>
<p class="meta">{len(s_chs)} chapters · {s_total} classified PYQs · {len(years)} years</p>

<div class="stats-grid">
<div class="stat-card {cls}"><div class="number">{s_total}</div><div class="label">Total PYQs</div></div>
<div class="stat-card {cls}"><div class="number">{len(s_chs)}</div><div class="label">Chapters</div></div>
<div class="stat-card {cls}"><div class="number">{sum(m["cluster_count"] for m in s_chs)}</div><div class="label">Question Clusters</div></div>
</div>

<h2>Chapters by Question Count</h2>
<input type="text" class="search-box" id="searchCh" placeholder="🔍 Search chapters..." onkeyup="filterTable('chTable','searchCh')">
<table id="chTable"><thead><tr><th>#</th><th>Chapter</th><th>Bucket</th><th>PYQs</th>"""
        for y in years:
            h += f'<th>{y}</th>'
        h += '<th>Years</th><th>Clusters</th><th>Score</th></tr></thead><tbody>\n'
        
        if subj == "Chemistry":
            for branch in ["Physical","Organic","Inorganic"]:
                branch_chs = [m for m in s_chs if CHEM_BRANCH.get(m["chapter"],"") == branch]
                if branch_chs:
                    h += f'<tr><td colspan="{len(years)+6}" style="background:#e0e0e0;font-weight:700;font-size:1rem">{branch} Chemistry</td></tr>\n'
                    for i, m in enumerate(branch_chs, 1):
                        h += _subject_table_row(i, m, years)
        else:
            for i, m in enumerate(s_chs, 1):
                h += _subject_table_row(i, m, years)
        
        h += '</tbody></table>\n'
        
        # Bar chart
        max_qs = s_chs[0]["question_count"] if s_chs else 1
        h += '<h2>Visual Frequency Distribution</h2><div class="bar-chart">'
        for m in s_chs:
            w = max(2, int(m["question_count"] / max_qs * 600))
            h += f'<div class="bar-row"><span class="bar-label">{escape(m["chapter"])}</span><div class="bar {cls}" style="width:{w}px">{m["question_count"]}</div></div>\n'
        h += '</div>\n'
        
        h += """
<script>
function filterTable(tableId, inputId) {
    var input = document.getElementById(inputId);
    var filter = input.value.toLowerCase();
    var table = document.getElementById(tableId);
    var rows = table.querySelectorAll('tbody tr');
    rows.forEach(function(row) {
        if (row.querySelector('td[colspan]')) return; // skip header rows
        row.style.display = row.textContent.toLowerCase().indexOf(filter) > -1 ? '' : 'none';
    });
}
</script>
</div></body></html>
"""
        with open(subj_dir / "index.html", "w") as f:
            f.write(h)
        print(f"[OK] Generated {subj}/index.html")

def _subject_table_row(i, m, years):
    h = f'<tr><td>{i}</td><td>{escape(m["chapter"])}</td><td>{badge_bucket(m["bucket"])}</td><td><strong>{m["question_count"]}</strong></td>'
    for y in years:
        cnt = m["year_wise"].get(str(y), m["year_wise"].get(y, 0))
        h += f'<td>{cnt if cnt else "—"}</td>'
    h += f'<td>{len(m["years_appeared"])}</td><td>{m["cluster_count"]}</td><td>{m["priority_score"]}</td></tr>\n'
    return h

# ─── MAIN ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("JEE Main PYQ — Building Priority System + Weightage Report")
    print("=" * 60)
    
    print("[1/7] Loading database...")
    questions = load_questions()
    taxonomy = load_taxonomy()
    clusters_data = load_clusters()
    print(f"  Loaded {len(questions)} questions")
    
    print("[2/7] Computing chapter statistics...")
    ch_stats = compute_chapter_stats(questions)
    print(f"  {len(ch_stats)} chapters found")
    
    print("[3/7] Building priority metadata...")
    metadata = build_priority_metadata(questions, ch_stats)
    print(f"  {len(metadata)} chapters with bucket assignments")
    
    # Count conflicts
    conflicts = sum(1 for m in metadata if m.get("conflicts"))
    print(f"  {conflicts} bucket conflicts detected")
    
    print("[4/7] Generating 00_HIGHEST_WEIGHTAGE_PCM.html...")
    generate_weightage_report(metadata, ch_stats, questions)
    
    print("[5/7] Generating 09_PRIORITY_SYSTEM/...")
    generate_priority_system(metadata, ch_stats, questions)
    
    print("[6/7] Generating main dashboard (index.html)...")
    generate_main_dashboard(metadata, ch_stats, questions, clusters_data)
    
    print("[7/7] Generating subject dashboards...")
    generate_subject_dashboards(metadata, ch_stats, questions)
    
    # Save priority metadata to database
    with open(DB / "priority_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    print(f"  Generated files:")
    print(f"    - index.html (main dashboard)")
    print(f"    - 00_HIGHEST_WEIGHTAGE_PCM.html (weightage report)")
    print(f"    - 09_PRIORITY_SYSTEM/index.html (priority dashboard)")
    print(f"    - 09_PRIORITY_SYSTEM/bucket_1_high_priority/index.html")
    print(f"    - 09_PRIORITY_SYSTEM/bucket_2_expansion/index.html")
    print(f"    - 09_PRIORITY_SYSTEM/bucket_3_restricted/index.html")
    print(f"    - 09_PRIORITY_SYSTEM/priority_comparison.html")
    print(f"    - Physics/index.html")
    print(f"    - Chemistry/index.html")
    print(f"    - Mathematics/index.html")
    print(f"    - 03_DATABASE/priority_metadata.json")
    print("=" * 60)
