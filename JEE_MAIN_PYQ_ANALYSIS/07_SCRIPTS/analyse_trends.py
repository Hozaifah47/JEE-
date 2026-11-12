#!/usr/bin/env python3
"""
analyse_trends.py — JEE Main PYQ Analysis System
Analyses frequency and trends across years, shifts, and chapters.

Usage:
    python 07_SCRIPTS/analyse_trends.py
    python 07_SCRIPTS/analyse_trends.py --subject Physics
"""

import json
import csv
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ROOT    = Path(__file__).resolve().parent.parent
ADMIN_DIR       = PROJECT_ROOT / "00_ADMIN"
DATABASE_DIR    = PROJECT_ROOT / "03_DATABASE"
REPORTS_DIR     = PROJECT_ROOT / "04_MASTER_REPORTS"
LOG_DIR         = PROJECT_ROOT / "08_LOGS"

QUESTIONS_JSONL  = DATABASE_DIR / "questions.jsonl"
CLUSTERS_FILE    = DATABASE_DIR / "clusters.json"
TAXONOMY_FILE    = DATABASE_DIR / "chapter_taxonomy.json"
STATUS_FILE      = ADMIN_DIR    / "project_status.json"
ANALYSIS_LOG     = LOG_DIR      / "analysis.log"


def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANALYSIS_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_questions() -> list:
    questions = []
    if not QUESTIONS_JSONL.exists():
        return questions
    with open(QUESTIONS_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    questions.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return questions


def load_clusters() -> list:
    if not CLUSTERS_FILE.exists():
        return []
    with open(CLUSTERS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("clusters", [])


def analyse(questions: list, clusters: list, subject_filter: str = None) -> dict:
    """Compute all trend metrics."""
    if subject_filter:
        questions = [q for q in questions if q.get("subject") == subject_filter]

    # Years & shifts seen
    all_years  = sorted({q["year"]  for q in questions if q.get("year")})
    all_shifts = sorted({q["shift"] for q in questions if q.get("shift")})

    # ── Chapter stats ─────────────────────────────────────────────────────────
    chapter_data = defaultdict(lambda: {
        "total": 0,
        "by_year": defaultdict(int),
        "by_shift": defaultdict(int),
        "by_type": defaultdict(int),
        "subjects": set(),
        "question_ids": [],
    })

    for q in questions:
        chap  = q.get("chapter", "") or "Unclassified"
        year  = q.get("year",  "?")
        shift = q.get("shift", "?")
        qtype = q.get("question_type", "MCQ")
        subj  = q.get("subject", "")
        qid   = q.get("question_id", "")

        d = chapter_data[chap]
        d["total"]        += 1
        d["by_year"][year] += 1
        d["by_shift"][shift] += 1
        d["by_type"][qtype] += 1
        d["subjects"].add(subj)
        d["question_ids"].append(qid)

    # Serialise chapter data
    chapter_stats = {}
    for ch, d in chapter_data.items():
        chapter_stats[ch] = {
            "chapter":    ch,
            "total":      d["total"],
            "by_year":    dict(d["by_year"]),
            "by_shift":   dict(d["by_shift"]),
            "by_type":    dict(d["by_type"]),
            "subjects":   list(d["subjects"]),
            "question_ids": d["question_ids"],
        }

    # ── Subject stats ─────────────────────────────────────────────────────────
    subject_data = defaultdict(lambda: {"total": 0, "by_year": defaultdict(int)})
    for q in questions:
        subj = q.get("subject", "Unknown")
        year = q.get("year", "?")
        subject_data[subj]["total"]        += 1
        subject_data[subj]["by_year"][year] += 1

    subject_stats = {
        s: {"total": d["total"], "by_year": dict(d["by_year"])}
        for s, d in subject_data.items()
    }

    # ── Cluster stats ─────────────────────────────────────────────────────────
    cluster_stats = []
    for cl in clusters:
        if subject_filter and cl.get("subject") != subject_filter:
            continue
        cluster_stats.append({
            "cluster_id":      cl["cluster_id"],
            "subject":         cl.get("subject", ""),
            "chapter":         cl.get("chapter", ""),
            "cluster_name":    cl.get("cluster_name", ""),
            "frequency":       cl.get("frequency", 0),
            "years_appeared":  cl.get("years_appeared", []),
            "similarity_level":cl.get("similarity_level", 3),
            "predicted_weight":cl.get("predicted_weight", "LOW"),
        })

    # Sort clusters by frequency
    cluster_stats.sort(key=lambda x: -x["frequency"])

    # ── Top recurring ─────────────────────────────────────────────────────────
    top_clusters_by_subject = {}
    for subj in ["Physics", "Chemistry", "Mathematics"]:
        top = [c for c in cluster_stats if c["subject"] == subj][:10]
        top_clusters_by_subject[subj] = top

    # ── High-probability topics (appeared in ≥3 years) ───────────────────────
    high_prob = {
        chap: stats
        for chap, stats in chapter_stats.items()
        if len(stats["by_year"]) >= 3 and stats["total"] >= 5
    }

    return {
        "generated_at":   datetime.now().isoformat(),
        "total_questions": len(questions),
        "years_covered":  all_years,
        "shifts":         all_shifts,
        "subject_stats":  subject_stats,
        "chapter_stats":  chapter_stats,
        "cluster_stats":  cluster_stats,
        "top_clusters_by_subject": top_clusters_by_subject,
        "high_probability_topics": high_prob,
    }


def save_reports(analysis: dict):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # trends_data.json — master file for HTML dashboard
    out_path = REPORTS_DIR / "trends_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    log(f"Saved {out_path}")

    # Per-subject JSON files
    for subject in ["Physics", "Chemistry", "Mathematics"]:
        subj_data = {
            "subject":    subject,
            "chapter_stats": {
                ch: stats
                for ch, stats in analysis["chapter_stats"].items()
                if subject in stats.get("subjects", [subject])
            },
            "cluster_stats": [
                c for c in analysis["cluster_stats"] if c["subject"] == subject
            ],
            "top_clusters": analysis["top_clusters_by_subject"].get(subject, []),
        }
        subj_path = REPORTS_DIR / f"{subject.lower()}_trends.json"
        with open(subj_path, "w", encoding="utf-8") as f:
            json.dump(subj_data, f, indent=2)
        log(f"Saved {subj_path}")

    # chapter_frequency.csv — easy to open in spreadsheet
    csv_path = REPORTS_DIR / "chapter_frequency.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["chapter", "total_questions", "years_appeared", "shifts_appeared",
                         "question_types", "subjects"])
        for ch, stats in sorted(analysis["chapter_stats"].items(), key=lambda x: -x[1]["total"]):
            writer.writerow([
                ch,
                stats["total"],
                len(stats["by_year"]),
                len(stats["by_shift"]),
                ";".join(f"{k}={v}" for k, v in stats["by_type"].items()),
                ";".join(stats["subjects"]),
            ])
    log(f"Saved {csv_path}")

    # cluster_frequency.csv
    ccsv_path = REPORTS_DIR / "cluster_frequency.csv"
    with open(ccsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cluster_id", "subject", "chapter", "cluster_name",
                         "frequency", "years_appeared", "similarity_level", "predicted_weight"])
        for c in analysis["cluster_stats"]:
            writer.writerow([
                c["cluster_id"], c["subject"], c["chapter"], c["cluster_name"],
                c["frequency"], ",".join(str(y) for y in c["years_appeared"]),
                c["similarity_level"], c["predicted_weight"],
            ])
    log(f"Saved {ccsv_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyse JEE Main PYQ trends.")
    parser.add_argument("--subject", help="Analyse only this subject.")
    args = parser.parse_args()

    log("=" * 60)
    log("JEE Main PYQ — Analyse Trends")

    questions = load_questions()
    clusters  = load_clusters()

    if not questions:
        log("No questions found. Run extract_questions.py first.", "WARN")
        sys.exit(0)

    log(f"Loaded {len(questions)} questions, {len(clusters)} clusters")

    analysis = analyse(questions, clusters, subject_filter=args.subject)
    save_reports(analysis)

    # Update status
    with open(STATUS_FILE, encoding="utf-8") as f:
        status = json.load(f)
    status["reports_generated"] = status.get("reports_generated", 0) + 1
    status["last_action"]  = "Trend analysis complete"
    status["last_updated"] = datetime.now().isoformat()
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print(f"{'TREND ANALYSIS SUMMARY':^60}")
    print("=" * 60)
    print(f"  Total questions analysed : {analysis['total_questions']}")
    print(f"  Years covered            : {analysis['years_covered']}")
    print(f"  Chapters analysed        : {len(analysis['chapter_stats'])}")
    print(f"  Clusters analysed        : {len(analysis['cluster_stats'])}")
    print()
    print(f"  {'Subject':<15} {'Total':>8}")
    for s, d in sorted(analysis["subject_stats"].items()):
        print(f"  {s:<15} {d['total']:>8}")
    print()
    print(f"  High probability topics (≥3 years, ≥5 Qs): {len(analysis['high_probability_topics'])}")
    for ch, stats in sorted(analysis["high_probability_topics"].items(), key=lambda x: -x[1]["total"])[:8]:
        print(f"    {ch:<40} {stats['total']:>5} Qs  [{len(stats['by_year'])} years]")
    print("=" * 60)
    print(f"\nReports saved to: {REPORTS_DIR}")
    print("Next step: python 07_SCRIPTS/generate_html.py")


if __name__ == "__main__":
    main()
