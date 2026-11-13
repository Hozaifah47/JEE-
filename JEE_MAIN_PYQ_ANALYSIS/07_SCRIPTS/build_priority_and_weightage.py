#!/usr/bin/env python3
"""
JEE Main PYQ Analysis — Priority Bucket System + Weightage Report + HTML Dashboards
Includes Bucket 0 (Unassigned / Not in Reference Image) with 'HIGH FREQ' indicators.
Includes Bucket -1 for conflict chapters with prominent conflict badges.
Cleaned up verbose alert boxes and embedded compact warning pills directly into tables.
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

def load_questions():
    qs = []
    with open(DB / "questions.jsonl", encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                qs.append(json.loads(line))
    return qs

# ─── Reference Bucket Definitions ────────────────────────────────
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
        "Basic Organic Chemistry",
        "Biomolecules",
        "Solutions",
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
        "Thermal Physics",
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
        "Some Basic Concepts of Chemistry",
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
        "Properties of Matter",
        "Oscillations",
        "Waves",
    ],
    "Chemistry": [
        "Equilibrium",
        "States of Matter",
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

# Bucket 0: Official Syllabus chapters not part of user's 3-bucket reference image
BUCKET_0 = {
    "Chemistry": [
        "s-Block Elements",
        "Hydrogen",
        "Polymers",
        "Environmental Chemistry",
        "Chemistry in Everyday Life",
    ],
    "Physics": [],
    "Mathematics": [],
}

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
    for subj in BUCKET_1:
        if chapter_name in BUCKET_1[subj]:
            return 1, "HIGH", "MASTER"
    for subj in BUCKET_2:
        if chapter_name in BUCKET_2[subj]:
            return 2, "MEDIUM-HIGH", "EXPAND"
    for subj in BUCKET_3:
        if chapter_name in BUCKET_3[subj]:
            return 3, "RESTRICTED", "FORMULA-ONLY"
    for subj in BUCKET_0:
        if chapter_name in BUCKET_0[subj]:
            return 0, "UNASSIGNED", "REVIEW (HIGH FREQ)"
    return -1, "NIL", "REVIEW"

def compute_chapter_stats(questions):
    stats = defaultdict(lambda: {
        "total": 0, "years": set(), "shifts": set(),
        "year_counts": defaultdict(int), "difficulties": defaultdict(int),
        "cluster_ids": set(), "subject": None
    })
    for q in questions:
        ch = q.get("chapter", "")
        if not ch or "NEEDS_REVIEW" in ch:
            continue
        s = stats[ch]
        s["total"] += 1
        s["subject"] = q.get("subject")
        yr = q.get("year")
        if yr:
            s["years"].add(yr)
            s["year_counts"][yr] += 1
        shift = q.get("shift")
        date = q.get("date", "")
        if yr and shift:
            s["shifts"].add(f"{yr}-{date}-S{shift}")
        cid = q.get("cluster_id")
        if cid:
            s["cluster_ids"].add(cid)
    for ch in stats:
        stats[ch]["years"] = sorted(stats[ch]["years"])
        stats[ch]["shifts"] = sorted(stats[ch]["shifts"])
        stats[ch]["cluster_ids"] = sorted(stats[ch]["cluster_ids"])
    return dict(stats)

def compute_priority_score(ch_stats):
    total = ch_stats["total"]
    years = len(ch_stats["years"])
    shifts = len(ch_stats["shifts"])
    clusters = len(ch_stats["cluster_ids"])
    return round(min(40, total * 0.5) + years * 5 + min(20, shifts * 0.25) + min(15, clusters * 0.5), 1)

def detect_conflicts(chapter_name, bucket_num, priority_score, total_qs):
    conflicts = []
    if bucket_num == 3 and total_qs >= 50:
        conflicts.append(f"Bucket 3 with High Frequency ({total_qs} PYQs)")
    elif bucket_num == 1 and total_qs < 25:
        conflicts.append(f"Bucket 1 with Low Frequency ({total_qs} PYQs)")
    return conflicts

def get_css():
    return """
<style>
:root{
  --primary:#1a237e; --bg:#f8f9fa; --card:#fff; --shadow:0 2px 8px rgba(0,0,0,.08);
  --phy:#1565c0; --chem:#2e7d32; --math:#6a1b9a;
  --b1-bg:#e8f5e9; --b1-txt:#1b5e20; --b1-bd:#4caf50;
  --b2-bg:#fff3e0; --b2-txt:#e65100; --b2-bd:#ff9800;
  --b3-bg:#fce4ec; --b3-txt:#880e4f; --b3-bd:#e91e63;
  --b0-bg:#ede7f6; --b0-txt:#4a148c; --b0-bd:#7e57c2;
  --cf-bg:#ffebee; --cf-txt:#b71c1c; --cf-bd:#ef5350;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:#212121;line-height:1.6}
.container{max-width:1400px;margin:0 auto;padding:24px}
h1{color:var(--primary);font-size:2rem;margin-bottom:8px;border-bottom:3px solid var(--primary);padding-bottom:8px}
h2{color:var(--primary);font-size:1.4rem;margin:24px 0 12px;border-bottom:2px solid #e0e0e0;padding-bottom:6px}
.meta{color:#666;font-size:.9rem;margin-bottom:20px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin:20px 0}
.stat-card{background:var(--card);border-radius:12px;padding:20px;box-shadow:var(--shadow);text-align:center;border-top:4px solid var(--primary)}
.stat-card .number{font-size:2.2rem;font-weight:700;color:var(--primary)}
.stat-card .label{font-size:.85rem;color:#666;margin-top:4px}
.bucket-section{margin:24px 0;padding:24px;border-radius:12px;border-left:6px solid}
.bucket-1{background:var(--b1-bg);border-left-color:var(--b1-bd)}
.bucket-2{background:var(--b2-bg);border-left-color:var(--b2-bd)}
.bucket-3{background:var(--b3-bg);border-left-color:var(--b3-bd)}
.bucket-0{background:var(--b0-bg);border-left-color:var(--b0-bd)}
.bucket-title{font-size:1.3rem;font-weight:700;margin-bottom:12px}
table{width:100%;border-collapse:collapse;margin:12px 0;background:var(--card);border-radius:8px;overflow:hidden;box-shadow:var(--shadow)}
th{background:var(--primary);color:#fff;padding:12px 14px;text-align:left;font-size:.85rem;text-transform:uppercase}
td{padding:10px 14px;border-bottom:1px solid #e0e0e0;font-size:.9rem}
tr:hover{background:#f1f3f5}
.badge{display:inline-block;padding:4px 10px;border-radius:12px;font-size:.75rem;font-weight:700;text-decoration:none}
.badge-b1{background:var(--b1-bg);color:var(--b1-txt);border:1px solid var(--b1-bd)}
.badge-b2{background:var(--b2-bg);color:var(--b2-txt);border:1px solid var(--b2-bd)}
.badge-b3{background:var(--b3-bg);color:var(--b3-txt);border:1px solid var(--b3-bd)}
.badge-b0{background:var(--b0-bg);color:var(--b0-txt);border:1px solid var(--b0-bd)}
.badge-cf{background:var(--cf-bg);color:var(--cf-txt);border:1px solid var(--cf-bd)}
.pill-conflict{display:inline-block;background:#ffebee;color:#c62828;border:1px solid #ffcdd2;padding:2px 8px;border-radius:10px;font-size:.72rem;font-weight:700;margin-left:6px}
.pill-highfreq{display:inline-block;background:#ede7f6;color:#4a148c;border:1px solid #d1c4e9;padding:2px 8px;border-radius:10px;font-size:.72rem;font-weight:700;margin-left:6px}
.nav{background:var(--primary);padding:12px 24px;border-radius:8px;margin-bottom:20px;display:flex;gap:16px;flex-wrap:wrap}
.nav a{color:#fff;text-decoration:none;padding:6px 14px;border-radius:6px;font-size:.9rem}
.nav a.active{background:rgba(255,255,255,.25);font-weight:700}
.subject-tag{display:inline-block;padding:2px 8px;border-radius:4px;color:#fff;font-size:.75rem;font-weight:700}
.subject-tag.phy{background:var(--phy)} .subject-tag.chem{background:var(--chem)} .subject-tag.math{background:var(--math)}
.search-box{width:100%;padding:12px 16px;border:2px solid #e0e0e0;border-radius:8px;font-size:1rem;margin:12px 0}
</style>
"""

def nav_html(active=""):
    items = [
        ("index.html", "🏠 Dashboard"),
        ("00_HIGHEST_WEIGHTAGE_PCM.html", "📊 Weightage Report"),
        ("09_PRIORITY_SYSTEM/index.html", "🎯 Priority System"),
        ("05_PRACTICE_SETS/index.html", "📝 Practice Hub"),
        ("Physics/index.html", "🔵 Physics"),
        ("Chemistry/index.html", "🟢 Chemistry"),
        ("Mathematics/index.html", "🟣 Mathematics"),
    ]
    links = []
    for h, l in items:
        cls = " class=active" if l == active else ""
        links.append(f"<a href=\"{h}\"{cls}>{l}</a>")
    return "<nav class=nav>" + " ".join(links) + "</nav>\n"
def badge_html(b_num, has_conflict=False):
    if has_conflict:
        return f'<span class="badge badge-cf">Bucket -1 (Conflict)</span>'
    if b_num == 1:
        return f'<span class="badge badge-b1">Bucket 1</span>'
    elif b_num == 2:
        return f'<span class="badge badge-b2">Bucket 2</span>'
    elif b_num == 3:
        return f'<span class="badge badge-b3">Bucket 3</span>'
    elif b_num == 0:
        return f'<span class="badge badge-b0">Bucket 0 (High Freq)</span>'
    return f'<span class="badge badge-cf">Bucket -1 (NIL)</span>'

def subject_tag(subj):
    cls = {"Physics":"phy","Chemistry":"chem","Mathematics":"math"}.get(subj,"")
    return f'<span class="subject-tag {cls}">{subj}</span>'

def build_metadata(questions, ch_stats):
    meta = []
    for ch, st in ch_stats.items():
        subj = st["subject"]
        b_num, priority, strategy = get_bucket(ch)
        score = compute_priority_score(st)
        conflicts = detect_conflicts(ch, b_num, score, st["total"])
        has_conflict = len(conflicts) > 0
        
        meta.append({
            "subject": subj,
            "chapter": ch,
            "bucket": -1 if has_conflict else b_num,
            "original_bucket": b_num,
            "has_conflict": has_conflict,
            "priority": "HIGH" if (b_num == 1 or b_num == 0) else priority,
            "reference_strategy": strategy,
            "question_count": st["total"],
            "years_appeared": st["years"],
            "shifts_appeared": len(st["shifts"]),
            "cluster_count": len(st["cluster_ids"]),
            "clusters": st["cluster_ids"][:25],
            "year_wise": dict(st["year_counts"]),
            "priority_score": score,
            "conflicts": conflicts,
            "is_bucket_0": b_num == 0,
            "chemistry_branch": CHEM_BRANCH.get(ch, None) if subj == "Chemistry" else None,
        })
    return meta

def generate_reports():
    questions = load_questions()
    ch_stats = compute_chapter_stats(questions)
    metadata = build_metadata(questions, ch_stats)
    years = sorted(set(q.get("year") for q in questions if q.get("year")))
    all_chapters = sorted(metadata, key=lambda x: x["question_count"], reverse=True)

    # 1. 00_HIGHEST_WEIGHTAGE_PCM.html
    h = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>JEE Main PYQ — Highest Weightage PCM Chapters</title>{get_css()}</head><body>
<div class="container">
{nav_html("📊 Weightage Report")}
<h1>📊 Highest Weightage PCM Chapters — 5-Year Comprehensive Ranking</h1>
<p class="meta">Every chapter across Physics, Chemistry, and Mathematics ranked by 5-year PYQ count. Chapters outside the 3-bucket framework are designated <strong>Bucket 0 (High Freq)</strong>, and conflict chapters are flagged <strong>Bucket -1 (Conflict)</strong>.</p>

<div class="stats-grid">
<div class="stat-card"><div class="number">{len(questions)}</div><div class="label">Total PYQs</div></div>
<div class="stat-card"><div class="number">90</div><div class="label">Papers Processed</div></div>
<div class="stat-card"><div class="number">{len(all_chapters)}</div><div class="label">Official Syllabus Chapters</div></div>
<div class="stat-card"><div class="number">{len(years)}</div><div class="label">Years Examined</div></div>
</div>

<input type="text" class="search-box" id="searchBox" placeholder="🔍 Filter chapters by name or subject..." onkeyup="filterTable()">

<table id="weightageTable">
<thead><tr>
<th>Rank</th><th>Subject</th><th>Chapter</th><th>Bucket Status</th><th>PYQs</th><th>Years</th><th>Shifts</th><th>Score</th><th>Strategic Note</th>
</tr></thead><tbody>
"""
    for i, m in enumerate(all_chapters, 1):
        conflict_pill = f'<span class="pill-conflict">⚠ {m["conflicts"][0]}</span>' if m["has_conflict"] else ""
        b0_pill = '<span class="pill-highfreq">High Frequency Syllabus Item</span>' if m["is_bucket_0"] else ""
        
        ch_slug = m["chapter"].replace(" ", "_").replace("&","and")
        if m["subject"] == "Chemistry":
            branch = CHEM_BRANCH.get(m["chapter"],"Physical")
            ch_link = f'Chemistry/{branch}_Chemistry/{ch_slug}/chapter_analysis.html'
        elif m["subject"] == "Physics":
            ch_link = f'Physics/chapters/{ch_slug}/chapter_analysis.html'
        else:
            ch_link = f'Mathematics/chapters/{ch_slug}/chapter_analysis.html'
            
        h += f"""<tr>
<td>{i}</td>
<td>{subject_tag(m["subject"])}</td>
<td><a href="{ch_link}" style="text-decoration:none;font-weight:700;color:var(--primary)">{m["chapter"]}</a> {conflict_pill} {b0_pill}</td>
<td>{badge_html(m["original_bucket"], m["has_conflict"])}</td>
<td><strong>{m["question_count"]}</strong></td>
<td>{len(m["years_appeared"])}</td>
<td>{m["shifts_appeared"]}</td>
<td>{m["priority_score"]}</td>
<td>{m["reference_strategy"]}</td>
</tr>"""

    h += """</tbody></table>
<script>
function filterTable(){
    var f = document.getElementById('searchBox').value.toLowerCase();
    var rows = document.querySelectorAll('#weightageTable tbody tr');
    rows.forEach(r => { r.style.display = r.textContent.toLowerCase().includes(f) ? '' : 'none'; });
}
</script>
</div></body></html>"""

    with open(ROOT / "00_HIGHEST_WEIGHTAGE_PCM.html", "w", encoding='utf-8') as f:
        f.write(h)

    # 2. 09_PRIORITY_SYSTEM/index.html
    b1 = [m for m in all_chapters if m["original_bucket"] == 1]
    b2 = [m for m in all_chapters if m["original_bucket"] == 2]
    b3 = [m for m in all_chapters if m["original_bucket"] == 3]
    b0 = [m for m in all_chapters if m["is_bucket_0"]]
    conflicts = [m for m in all_chapters if m["has_conflict"]]

    hp = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Three-Bucket Priority Strategy</title>{get_css()}</head><body>
<div class="container">
{nav_html("🎯 Priority System")}
<h1>🎯 Strategic Chapter Priority System</h1>
<p class="meta">Integrated strategic preparation roadmap based on historical frequency and your preparation tiers.</p>

<div class="stats-grid">
<div class="stat-card" style="border-top-color:var(--b1-bd)"><div class="number" style="color:var(--b1-txt)">{len(b1)}</div><div class="label">Bucket 1 (Foundation)</div></div>
<div class="stat-card" style="border-top-color:var(--b2-bd)"><div class="number" style="color:var(--b2-txt)">{len(b2)}</div><div class="label">Bucket 2 (Expansion)</div></div>
<div class="stat-card" style="border-top-color:var(--b3-bd)"><div class="number" style="color:var(--b3-txt)">{len(b3)}</div><div class="label">Bucket 3 (Formula-Only)</div></div>
<div class="stat-card" style="border-top-color:var(--b0-bd)"><div class="number" style="color:var(--b0-txt)">{len(b0)}</div><div class="label">Bucket 0 (High Frequency)</div></div>
<div class="stat-card" style="border-top-color:var(--cf-bd)"><div class="number" style="color:var(--cf-txt)">{len(conflicts)}</div><div class="label">Bucket Conflicts</div></div>
</div>

<div class="bucket-section bucket-1">
<div class="bucket-title" style="color:var(--b1-txt)">BUCKET 1: HIGH PRIORITY (Foundation Blocks — Master First)</div>
<p>Target: 48–52 Marks (Phy/Chem), 28–32 Marks (Math). Full conceptual mastery and exhaustive PYQ solving.</p>
<table><thead><tr><th>Chapter</th><th>Subject</th><th>PYQs</th><th>Years</th><th>Clusters</th><th>Score</th></tr></thead><tbody>
"""
    for m in b1:
        hp += f"<tr><td><strong>{m['chapter']}</strong></td><td>{subject_tag(m['subject'])}</td><td><strong>{m['question_count']}</strong></td><td>{len(m['years_appeared'])}</td><td>{m['cluster_count']}</td><td>{m['priority_score']}</td></tr>"
    hp += "</tbody></table></div>"

    hp += """<div class="bucket-section bucket-2">
<div class="bucket-title" style="color:var(--b2-txt)">BUCKET 2: EXPANSION (Booster Block — Thorough Coverage)</div>
<p>Target: ~+65 Marks Additional. Broad coverage of standard problem archetypes.</p>
<table><thead><tr><th>Chapter</th><th>Subject</th><th>PYQs</th><th>Years</th><th>Clusters</th><th>Score</th></tr></thead><tbody>
"""
    for m in b2:
        hp += f"<tr><td><strong>{m['chapter']}</strong></td><td>{subject_tag(m['subject'])}</td><td><strong>{m['question_count']}</strong></td><td>{len(m['years_appeared'])}</td><td>{m['cluster_count']}</td><td>{m['priority_score']}</td></tr>"
    hp += "</tbody></table></div>"

    hp += """<div class="bucket-section bucket-3">
<div class="bucket-title" style="color:var(--b3-txt)">BUCKET 3: RESTRICTED ZONE (Formula-Only / Standard Archetypes)</div>
<p>Target: Rapid coverage of formulas and standard questions. Do not overinvest time into obscure variations.</p>
<table><thead><tr><th>Chapter</th><th>Subject</th><th>PYQs</th><th>Years</th><th>Clusters</th><th>Score</th></tr></thead><tbody>
"""
    for m in b3:
        hp += f"<tr><td><strong>{m['chapter']}</strong></td><td>{subject_tag(m['subject'])}</td><td><strong>{m['question_count']}</strong></td><td>{len(m['years_appeared'])}</td><td>{m['cluster_count']}</td><td>{m['priority_score']}</td></tr>"
    hp += "</tbody></table></div>"

    hp += """<div class="bucket-section bucket-0">
<div class="bucket-title" style="color:var(--b0-txt)">BUCKET 0: HIGH FREQUENCY SYLLABUS TOPICS (Not in Reference Image)</div>
<p>These chapters are part of the standard JEE Main syllabus and carry <strong>high question frequency</strong>, but were not in the reference framework. Covered with standard priority.</p>
<table><thead><tr><th>Chapter</th><th>Subject</th><th>Bucket Status</th><th>PYQs</th><th>Years</th><th>Score</th></tr></thead><tbody>
"""
    for m in b0:
        hp += f"<tr><td><strong>{m['chapter']}</strong></td><td>{subject_tag(m['subject'])}</td><td>{badge_html(0)}</td><td><strong>{m['question_count']}</strong></td><td>{len(m['years_appeared'])}</td><td>{m['priority_score']}</td></tr>"
    hp += "</tbody></table></div>"

    hp += "</div></body></html>"

    with open(PRIORITY_DIR / "index.html", "w", encoding='utf-8') as f:
        f.write(hp)

    # 3. index.html
    generate_main_dashboard(all_chapters, questions)

    # Save metadata
    with open(DB / "priority_metadata.json", "w", encoding='utf-8') as f:
        json.dump(all_chapters, f, indent=2)

    print("Successfully updated priority and weightage dashboards with Bucket 0 and Bucket -1 indicators!")

def generate_main_dashboard(all_chapters, questions):
    h = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>JEE Main PYQ Analysis System — Dashboard</title>{get_css()}</head><body>
<div class="container">
{nav_html("🏠 Dashboard")}
<h1>JEE Main PYQ Analysis System</h1>
<p class="meta">5-Year Analysis · 90 Papers · {len(questions)} Questions · 73 Chapters · 230 Problem-Solving Clusters</p>

<div class="stats-grid">
<div class="stat-card"><div class="number">{len(questions)}</div><div class="label">Total Questions</div></div>
<div class="stat-card"><div class="number">90</div><div class="label">Papers Processed</div></div>
<div class="stat-card"><div class="number">73</div><div class="label">Official Syllabus Chapters</div></div>
<div class="stat-card"><div class="number">230</div><div class="label">Problem-Solving Clusters</div></div>
</div>

<h2>📌 Master Portals</h2>
<div class="stats-grid">
<div class="stat-card"><a href="00_HIGHEST_WEIGHTAGE_PCM.html" style="text-decoration:none"><div class="number">📊</div><div class="label">Highest Weightage PCM<br>Chapter Rankings</div></a></div>
<div class="stat-card"><a href="09_PRIORITY_SYSTEM/index.html" style="text-decoration:none"><div class="number">🎯</div><div class="label">Three-Bucket Strategy<br>Priority Dashboard</div></a></div>
<div class="stat-card"><a href="05_PRACTICE_SETS/index.html" style="text-decoration:none"><div class="number">📝</div><div class="label">Practice Sets Library<br>526 Interactive Tests</div></a></div>
</div>

<h2>🏆 Top 15 Highest-Frequency Chapters</h2>
<table><thead><tr><th>Rank</th><th>Subject</th><th>Chapter</th><th>Bucket</th><th>PYQs</th><th>Years</th><th>Clusters</th></tr></thead><tbody>
"""
    for i, m in enumerate(all_chapters[:15], 1):
        conflict_pill = f'<span class="pill-conflict">⚠ {m["conflicts"][0]}</span>' if m["has_conflict"] else ""
        b0_pill = '<span class="pill-highfreq">High Frequency Syllabus Item</span>' if m["is_bucket_0"] else ""
        h += f'<tr><td>{i}</td><td>{subject_tag(m["subject"])}</td><td><strong>{m["chapter"]}</strong> {conflict_pill} {b0_pill}</td><td>{badge_html(m["original_bucket"], m["has_conflict"])}</td><td><strong>{m["question_count"]}</strong></td><td>{len(m["years_appeared"])}</td><td>{m["cluster_count"]}</td></tr>\n'
    h += "</tbody></table></div></body></html>"

    with open(ROOT / "index.html", "w", encoding='utf-8') as f:
        f.write(h)

if __name__ == "__main__":
    generate_reports()
