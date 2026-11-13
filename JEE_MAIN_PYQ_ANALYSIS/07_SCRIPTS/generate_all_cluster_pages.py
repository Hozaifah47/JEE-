#!/usr/bin/env python3
"""
generate_all_cluster_pages.py — Generates individual cluster directories and HTML pages
for ALL 231 clusters across Physics, Chemistry, and Mathematics.
"""

import json, os, html
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_JSONL = ROOT / "03_DATABASE" / "questions.jsonl"
CLUSTERS_FILE = ROOT / "03_DATABASE" / "clusters.json"
TAXONOMY_FILE = ROOT / "03_DATABASE" / "chapter_taxonomy.json"
PRIORITY_FILE = ROOT / "03_DATABASE" / "priority_metadata.json"

def get_chem_branch(tax):
    chem_branches = {}
    for branch, bdata in tax['subjects']['Chemistry']['sub_divisions'].items():
        for ch in bdata['chapters']:
            chem_branches[ch['name']] = branch
    return chem_branches

def escape(s):
    return html.escape(str(s)) if s else ""

def main():
    with open(CLUSTERS_FILE) as f:
        cdata = json.load(f)
    clusters = {c['cluster_id']: c for c in cdata['clusters']}

    with open(TAXONOMY_FILE) as f:
        tax = json.load(f)
    chem_branches = get_chem_branch(tax)

    with open(PRIORITY_FILE) as f:
        pm = json.load(f)
    ch_bucket = {m['chapter']: m.get('bucket', 1) for m in pm}

    # Group questions by cluster_id
    cluster_qs = defaultdict(list)
    with open(QUESTIONS_JSONL) as f:
        for line in f:
            if line.strip():
                q = json.loads(line)
                cid = q.get('cluster_id')
                if cid:
                    cluster_qs[cid].append(q)

    print(f"Generating cluster pages for {len(clusters)} clusters...")

    css = """
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f5;color:#212121;margin:0;padding:20px;line-height:1.6}
.container{max-width:960px;margin:0 auto;background:#fff;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.75rem;font-weight:600;margin:2px}
.b1{background:#c8e6c9;color:#1b5e20}.b2{background:#ffe0b2;color:#e65100}.b3{background:#f8bbd0;color:#880e4f}
.q-card{background:#fcfcfc;border:1px solid #e0e0e0;border-left:4px solid #1a237e;border-radius:8px;padding:16px;margin:16px 0}
.ans-toggle{background:#1a237e;color:#fff;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;margin-top:8px}
.ans-box{display:none;background:#e8f5e9;border:1px solid #c8e6c9;padding:10px;border-radius:6px;margin-top:8px;font-weight:600;color:#1b5e20}
table{width:100%;border-collapse:collapse;margin:16px 0}
th{background:#1a237e;color:#fff;padding:8px 12px;text-align:left}
td{padding:8px 12px;border-bottom:1px solid #eee}
nav a{margin-right:12px;color:#1a237e;text-decoration:none;font-weight:600}
</style>
"""
    js = """
<script>
function toggleAns(id){
    var el = document.getElementById('ans-'+id);
    el.style.display = (el.style.display === 'block') ? 'none' : 'block';
}
</script>
"""

    created_count = 0
    for cid, cinfo in clusters.items():
        qs = cluster_qs.get(cid, [])
        subj = cinfo.get('subject') or 'General'
        ch = cinfo.get('chapter') or 'General'
        ch_slug = ch.replace(' ', '_').replace('&', 'and')
        b_num = ch_bucket.get(ch, 1)

        # Target cluster directory
        if subj == 'Chemistry':
            branch = chem_branches.get(ch, 'Physical_Chemistry')
            target_dir = ROOT / 'Chemistry' / branch / ch_slug / 'clusters' / cid
        elif subj == 'Physics':
            target_dir = ROOT / 'Physics' / 'chapters' / ch_slug / 'clusters' / cid
        elif subj == 'Mathematics':
            target_dir = ROOT / 'Mathematics' / 'chapters' / ch_slug / 'clusters' / cid
        else:
            target_dir = ROOT / '04_MASTER_REPORTS' / 'clusters' / cid

        target_dir.mkdir(parents=True, exist_ok=True)

        nav = f'<nav><a href="../../index.html">← Chapter Overview</a><a href="questions.html">📝 Practice Questions</a><a href="cluster_analysis.html">🔬 Cluster Analysis</a><a href="answers.html">🔑 Answer Key</a></nav>'

        # 1. index.html
        with open(target_dir / "index.html", "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{escape(cid)} - {escape(cinfo['cluster_name'])}</title>{css}</head><body>
<div class="container">{nav}
<h1>Cluster: {escape(cid)}</h1>
<h3>{escape(cinfo['cluster_name'])}</h3>
<p><span class="badge b{b_num}">Bucket {b_num}</span> · <strong>{len(qs)} PYQs</strong> · Subject: {escape(subj)} · Chapter: {escape(ch)}</p>
<div style="background:#e8eaf6;padding:16px;border-radius:8px;margin:16px 0">
<p><strong>Core Concept:</strong> {escape(cinfo.get('core_concept','N/A'))}</p>
<p><strong>Required Approach:</strong> {escape(cinfo.get('required_approach','N/A'))}</p>
<p><strong>Standard Formula / Rule:</strong> <code>{escape(cinfo.get('formula','N/A'))}</code></p>
</div>
<p><a href="questions.html" style="display:inline-block;background:#1a237e;color:#fff;padding:8px 16px;border-radius:6px;text-decoration:none;font-weight:600">Solve All {len(qs)} Questions in this Cluster →</a></p>
</div></body></html>""")

        # 2. questions.html
        with open(target_dir / "questions.html", "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Questions - {escape(cid)}</title>{css}{js}</head><body>
<div class="container">{nav}
<h2>Questions: {escape(cinfo['cluster_name'])} ({len(qs)} PYQs)</h2>
""")
            for i, q in enumerate(qs, 1):
                qid = q.get('question_id', f'Q{i}')
                y = q.get('year', '')
                sh = q.get('shift', '')
                qtype = q.get('question_type', 'MCQ')
                diff = q.get('difficulty', 'Moderate')
                qtext = escape(q.get('question_text', ''))
                opts = q.get('options') or []
                ans = escape(q.get('correct_answer') or 'Refer to Answer Key')

                opts_html = ""
                if opts:
                    opts_html = "<ol type='1' style='margin:10px 0 10px 20px'>"
                    for opt in opts:
                        opts_html += f"<li>{escape(opt)}</li>"
                    opts_html += "</ol>"

                f.write(f"""
<div class="q-card">
<div><strong>Question {i}</strong> ({escape(qid)}) <span class="badge" style="background:#e0e0e0">{y} Shift {sh}</span> <span class="badge" style="background:#e3f2fd;color:#0d47a1">{escape(qtype)}</span> <span class="badge" style="background:#fff3e0;color:#e65100">{escape(diff)}</span></div>
<p style="margin-top:10px">{qtext}</p>
{opts_html}
<button class="ans-toggle" onclick="toggleAns('{qid}')">Show Answer</button>
<div id="ans-{qid}" class="ans-box">Answer: {ans}</div>
</div>
""")
            f.write("</div></body></html>")

        # 3. cluster_analysis.html
        with open(target_dir / "cluster_analysis.html", "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Analysis - {escape(cid)}</title>{css}</head><body>
<div class="container">{nav}
<h2>Archetype Analysis: {escape(cinfo['cluster_name'])}</h2>
<table style="margin:20px 0">
<tr><th>Property</th><th>Details</th></tr>
<tr><td><strong>Cluster ID</strong></td><td><code>{escape(cid)}</code></td></tr>
<tr><td><strong>Subject</strong></td><td>{escape(subj)}</td></tr>
<tr><td><strong>Chapter</strong></td><td>{escape(ch)}</td></tr>
<tr><td><strong>Total PYQ Appearances</strong></td><td><strong>{len(qs)}</strong></td></tr>
<tr><td><strong>Core Principle</strong></td><td>{escape(cinfo.get('core_concept','N/A'))}</td></tr>
<tr><td><strong>Problem-Solving Method</strong></td><td>{escape(cinfo.get('required_approach','N/A'))}</td></tr>
<tr><td><strong>Primary Formulation</strong></td><td><code>{escape(cinfo.get('formula','N/A'))}</code></td></tr>
</table>
<h3>Exam Strategy & Common Traps</h3>
<ul>
<li>Review the standard boundary conditions before applying formulas.</li>
<li>Avoid common algebraic or arithmetic conversion errors (e.g. units conversion into SI).</li>
<li>This archetype regularly re-appears in morning and evening shifts with altered numerical parameters.</li>
</ul>
</div></body></html>""")

        # 4. answers.html
        with open(target_dir / "answers.html", "w", encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Answer Key - {escape(cid)}</title>{css}</head><body>
<div class="container">{nav}
<h2>Answer Key: {escape(cinfo['cluster_name'])}</h2>
<table><thead><tr><th>#</th><th>Question ID</th><th>Year</th><th>Shift</th><th>Correct Answer</th></tr></thead><tbody>
""")
            for i, q in enumerate(qs, 1):
                f.write(f"<tr><td>{i}</td><td>{escape(q.get('question_id',''))}</td><td>{escape(q.get('year',''))}</td><td>{escape(q.get('shift',''))}</td><td><strong>{escape(q.get('correct_answer') or 'Key in Source')}</strong></td></tr>\n")
            f.write("</tbody></table></div></body></html>")

        created_count += 1

    print(f"Successfully generated full 4-file suites for all {created_count} clusters!")

if __name__ == "__main__":
    main()
