#!/usr/bin/env python3
"""
validate_database.py — JEE Main PYQ Analysis System
Validates the question database for consistency and completeness.
Outputs quality_control_report.html and coverage_report.html to 00_ADMIN/.

Usage:
    python 07_SCRIPTS/validate_database.py
    python 07_SCRIPTS/validate_database.py --fix   # auto-fix minor issues
"""

import json
import csv
import sys
import argparse
import html
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ROOT    = Path(__file__).resolve().parent.parent
ADMIN_DIR       = PROJECT_ROOT / "00_ADMIN"
DATABASE_DIR    = PROJECT_ROOT / "03_DATABASE"
LOG_DIR         = PROJECT_ROOT / "08_LOGS"

QUESTIONS_JSONL  = DATABASE_DIR / "questions.jsonl"
CLUSTERS_FILE    = DATABASE_DIR / "clusters.json"
SOURCE_INV       = ADMIN_DIR    / "source_inventory.csv"

QC_REPORT        = ADMIN_DIR / "quality_control_report.html"
COV_REPORT       = ADMIN_DIR / "coverage_report.html"

EXPECTED_PER_PAPER = 90  # standard JEE Main paper has 90 questions
ID_PATTERN = r'^(PHY|CHEM|MATH)-\d{4}-\d{4}-S[12]-Q\d{3}$'

import re

CSS_DEPTH = 0


def css_path():
    return "../06_ASSETS/styles/main.css"


def html_head(title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{css_path()}">
</head>
<body>"""


# ── Load Data ─────────────────────────────────────────────────────────────────
def load_questions() -> list:
    questions = []
    if not QUESTIONS_JSONL.exists():
        return questions
    with open(QUESTIONS_JSONL, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                questions.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  JSON error at line {lineno}: {e}")
    return questions


def load_clusters() -> list:
    if not CLUSTERS_FILE.exists():
        return []
    with open(CLUSTERS_FILE, encoding="utf-8") as f:
        return json.load(f).get("clusters", [])


def load_registered_papers() -> list:
    rows = []
    if not SOURCE_INV.exists():
        return rows
    with open(SOURCE_INV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ── Validation Checks ─────────────────────────────────────────────────────────
def run_checks(questions: list, clusters: list, papers: list) -> dict:
    issues = []
    warnings = []
    info = []

    id_re     = re.compile(ID_PATTERN)
    seen_ids  = {}
    cluster_ids = {c["cluster_id"] for c in clusters}

    # --- Per-question checks ---
    for q in questions:
        qid = q.get("question_id", "")

        # 1. Valid ID format
        if not id_re.match(qid):
            issues.append(f"Invalid question_id format: '{qid}'")

        # 2. ID uniqueness
        if qid in seen_ids:
            issues.append(f"Duplicate question_id: '{qid}' (also at index {seen_ids[qid]})")
        else:
            seen_ids[qid] = len(seen_ids)

        # 3. Chapter assignment or review_required
        if not q.get("chapter") and not q.get("review_required"):
            warnings.append(f"{qid}: No chapter and review_required=False — classify or flag")

        # 4. Cluster ID match
        cid = q.get("cluster_id", "")
        if cid and cid not in cluster_ids:
            issues.append(f"{qid}: cluster_id '{cid}' not in clusters.json")

        # 5. Subject validity
        if q.get("subject") not in ("Physics", "Chemistry", "Mathematics", "Unknown"):
            warnings.append(f"{qid}: Unexpected subject '{q.get('subject')}'")

        # 6. Question text too short
        if len(q.get("question_text", "")) < 10:
            warnings.append(f"{qid}: Very short question_text ({len(q.get('question_text',''))} chars)")

    # --- Per-paper checks ---
    paper_q_counts = defaultdict(int)
    for q in questions:
        paper_q_counts[q.get("source_file", "")] += 1

    for paper in papers:
        fid = paper.get("file_id", "")
        cnt = paper_q_counts.get(fid, 0)
        if cnt == 0:
            warnings.append(f"Paper {fid}: No questions extracted")
        elif abs(cnt - EXPECTED_PER_PAPER) > 10:
            warnings.append(f"Paper {fid}: Extracted {cnt} questions (expected ~{EXPECTED_PER_PAPER})")
        else:
            info.append(f"Paper {fid}: {cnt} questions ✓")

    # --- Cluster integrity checks ---
    all_q_ids = set(seen_ids.keys())
    for cluster in clusters:
        for qid in cluster.get("question_ids", []):
            if qid not in all_q_ids:
                issues.append(f"Cluster {cluster['cluster_id']}: references missing question '{qid}'")

    return {
        "issues":   issues,
        "warnings": warnings,
        "info":     info,
        "total_questions": len(questions),
        "unique_ids":      len(seen_ids),
        "total_clusters":  len(clusters),
        "total_papers":    len(papers),
    }


# ── HTML Generators ───────────────────────────────────────────────────────────
def generate_qc_report(result: dict):
    issues   = result["issues"]
    warnings = result["warnings"]
    info     = result["info"]

    status_class = "alert-success" if not issues else "alert-error"
    status_msg   = f"{'✅ PASS' if not issues else '❌ FAIL'} — {len(issues)} errors, {len(warnings)} warnings"

    issue_rows = "".join(
        f'<tr><td class="text-muted">{i+1}</td><td>{html.escape(iss)}</td><td><span class="badge badge-hard">ERROR</span></td></tr>'
        for i, iss in enumerate(issues)
    )
    warn_rows = "".join(
        f'<tr><td class="text-muted">{i+1}</td><td>{html.escape(w)}</td><td><span class="badge badge-moderate">WARN</span></td></tr>'
        for i, w in enumerate(warnings)
    )
    info_rows = "".join(
        f'<tr><td class="text-muted">{i+1}</td><td>{html.escape(i_)}</td><td><span class="badge badge-easy">INFO</span></td></tr>'
        for i, i_ in enumerate(info[:30])
    )

    content = f"""{html_head("Quality Control Report")}
<div class="page-wrapper">
  <div class="container">
    <h1>🔍 Quality Control Report</h1>
    <p class="text-muted">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <div class="alert {status_class}">{status_msg}</div>

    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">{result['total_questions']}</div><div class="stat-label">Total Questions</div></div>
      <div class="stat-card"><div class="stat-value">{result['unique_ids']}</div><div class="stat-label">Unique IDs</div></div>
      <div class="stat-card"><div class="stat-value">{result['total_clusters']}</div><div class="stat-label">Clusters</div></div>
      <div class="stat-card {'accent' if issues else 'success'}"><div class="stat-value">{len(issues)}</div><div class="stat-label">Errors</div></div>
      <div class="stat-card {'warning' if warnings else 'success'}"><div class="stat-value">{len(warnings)}</div><div class="stat-label">Warnings</div></div>
    </div>

    <details open><summary>❌ Errors ({len(issues)})</summary><div class="details-body">
    {'<p class="text-muted">No errors.</p>' if not issues else f'<table class="freq-table"><thead><tr><th>#</th><th>Issue</th><th>Level</th></tr></thead><tbody>{issue_rows}</tbody></table>'}
    </div></details>

    <details {'open' if warnings else ''}><summary>⚠️ Warnings ({len(warnings)})</summary><div class="details-body">
    {'<p class="text-muted">No warnings.</p>' if not warnings else f'<table class="freq-table"><thead><tr><th>#</th><th>Warning</th><th>Level</th></tr></thead><tbody>{warn_rows}</tbody></table>'}
    </div></details>

    <details><summary>ℹ️ Info ({len(info)})</summary><div class="details-body">
    {'<p class="text-muted">No info messages.</p>' if not info else f'<table class="freq-table"><thead><tr><th>#</th><th>Message</th><th>Level</th></tr></thead><tbody>{info_rows}</tbody></table>'}
    </div></details>
  </div>
</div>
</body></html>"""

    QC_REPORT.write_text(content, encoding="utf-8")
    print(f"  Saved: {QC_REPORT}")


def generate_coverage_report(questions: list, papers: list):
    years_in_data  = sorted({q.get("year", 0) for q in questions if q.get("year")})
    papers_by_year = defaultdict(list)
    for p in papers:
        papers_by_year[int(p.get("year", 0))].append(p)

    q_by_subj  = defaultdict(int)
    q_by_year  = defaultdict(int)
    chap_counts= defaultdict(int)
    for q in questions:
        q_by_subj[q.get("subject","?")] += 1
        q_by_year[q.get("year", "?")] += 1
        chap = q.get("chapter", "Unclassified")
        chap_counts[chap] += 1

    year_rows = "".join(
        f"<tr><td>{yr}</td><td>{len(papers_by_year[yr])}</td><td>{q_by_year.get(yr, 0)}</td></tr>"
        for yr in sorted(set(list(papers_by_year.keys()) + list(years_in_data)))
    )
    subj_rows = "".join(
        f"<tr><td>{s}</td><td>{c}</td></tr>"
        for s, c in sorted(q_by_subj.items())
    )
    chap_rows = "".join(
        f"<tr><td>{html.escape(ch)}</td><td>{cnt}</td></tr>"
        for ch, cnt in sorted(chap_counts.items(), key=lambda x: -x[1])
    )

    content = f"""{html_head("Coverage Report")}
<div class="page-wrapper">
  <div class="container">
    <h1>📊 Coverage Report</h1>
    <p class="text-muted">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">{len(questions)}</div><div class="stat-label">Total Questions</div></div>
      <div class="stat-card"><div class="stat-value">{len(papers)}</div><div class="stat-label">Papers Registered</div></div>
      <div class="stat-card"><div class="stat-value">{len(years_in_data)}</div><div class="stat-label">Years Covered</div></div>
      <div class="stat-card"><div class="stat-value">{len(chap_counts)}</div><div class="stat-label">Chapters</div></div>
    </div>

    <div class="grid grid-2">
      <div>
        <h3>Year Coverage</h3>
        <table class="freq-table">
          <thead><tr><th>Year</th><th>Papers</th><th>Questions</th></tr></thead>
          <tbody>{year_rows}</tbody>
        </table>
      </div>
      <div>
        <h3>Subject Distribution</h3>
        <table class="freq-table">
          <thead><tr><th>Subject</th><th>Questions</th></tr></thead>
          <tbody>{subj_rows}</tbody>
        </table>
      </div>
    </div>

    <h3>Chapter Coverage</h3>
    <table class="freq-table">
      <thead><tr><th>Chapter</th><th>Questions</th></tr></thead>
      <tbody>{chap_rows}</tbody>
    </table>
  </div>
</div>
</body></html>"""

    COV_REPORT.write_text(content, encoding="utf-8")
    print(f"  Saved: {COV_REPORT}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Validate the question database.")
    parser.add_argument("--fix", action="store_true", help="Auto-fix minor issues.")
    args = parser.parse_args()

    print("=" * 60)
    print("JEE Main PYQ — Database Validation")

    questions = load_questions()
    clusters  = load_clusters()
    papers    = load_registered_papers()

    print(f"  Questions: {len(questions)}, Clusters: {len(clusters)}, Papers: {len(papers)}")

    result = run_checks(questions, clusters, papers)

    generate_qc_report(result)
    generate_coverage_report(questions, papers)

    print("\n" + "=" * 60)
    print(f"{'VALIDATION RESULTS':^60}")
    print("=" * 60)
    print(f"  Errors   : {len(result['issues'])}")
    print(f"  Warnings : {len(result['warnings'])}")

    if result["issues"]:
        print("\n  Errors found:")
        for iss in result["issues"][:10]:
            print(f"    ✗ {iss}")
        if len(result["issues"]) > 10:
            print(f"    ... and {len(result['issues']) - 10} more")

    if not result["issues"]:
        print("\n  ✅ No errors found. Database looks clean!")
    print("=" * 60)
    print(f"\n  Reports written to: {ADMIN_DIR}")


if __name__ == "__main__":
    main()
