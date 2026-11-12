#!/usr/bin/env python3
"""
classify_questions.py — JEE Main PYQ Analysis System
Classifies extracted questions by chapter/topic/concept using keyword matching.

Usage:
    python 07_SCRIPTS/classify_questions.py
    python 07_SCRIPTS/classify_questions.py --subject Physics
    python 07_SCRIPTS/classify_questions.py --reclassify   # re-classify all, not just unclassified
"""

import json
import csv
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ROOT    = Path(__file__).resolve().parent.parent
ADMIN_DIR       = PROJECT_ROOT / "00_ADMIN"
DATABASE_DIR    = PROJECT_ROOT / "03_DATABASE"
LOG_DIR         = PROJECT_ROOT / "08_LOGS"

QUESTIONS_JSONL  = DATABASE_DIR / "questions.jsonl"
QUESTIONS_CSV    = DATABASE_DIR / "questions.csv"
TAXONOMY_FILE    = DATABASE_DIR / "chapter_taxonomy.json"
ANALYSIS_LOG     = LOG_DIR      / "analysis.log"
STATUS_FILE      = ADMIN_DIR    / "project_status.json"

QUESTION_CSV_HEADERS = [
    "question_id", "subject", "chapter", "topic", "concept", "cluster_id",
    "year", "date", "shift", "question_number", "question_type",
    "question_text", "correct_answer", "difficulty",
    "source_file", "source_page", "extraction_confidence", "review_required"
]

# Confidence thresholds
HIGH_CONF   = 2    # 2+ keywords matched
MEDIUM_CONF = 1    # 1 keyword matched
LOW_CONF    = 0    # no keywords

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANALYSIS_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_taxonomy() -> dict:
    with open(TAXONOMY_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_keyword_map(taxonomy: dict) -> dict:
    """
    Returns nested dict: {subject: [(chapter_name, chapter_id, [keywords])]}
    """
    kmap = {}

    # Physics
    phy_chapters = []
    for ch in taxonomy["subjects"]["Physics"]["chapters"]:
        phy_chapters.append((ch["name"], ch["id"], [kw.lower() for kw in ch["keywords"]]))
    kmap["Physics"] = phy_chapters

    # Chemistry — combine all sub-divisions
    chem_chapters = []
    chem = taxonomy["subjects"]["Chemistry"]["sub_divisions"]
    for div in chem.values():
        for ch in div["chapters"]:
            chem_chapters.append((ch["name"], ch["id"], [kw.lower() for kw in ch["keywords"]]))
    kmap["Chemistry"] = chem_chapters

    # Mathematics
    math_chapters = []
    for ch in taxonomy["subjects"]["Mathematics"]["chapters"]:
        math_chapters.append((ch["name"], ch["id"], [kw.lower() for kw in ch["keywords"]]))
    kmap["Mathematics"] = math_chapters

    return kmap


def classify_question(text: str, subject: str, keyword_map: dict) -> tuple:
    """
    Returns (chapter_name, chapter_id, confidence, review_required).
    confidence: 0=none, 1=low, 2=high
    """
    if subject not in keyword_map:
        return "", "", 0, True

    text_lower = text.lower()
    best_chapter = ""
    best_id      = ""
    best_score   = 0

    for chapter_name, chapter_id, keywords in keyword_map[subject]:
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score   = score
            best_chapter = chapter_name
            best_id      = chapter_id

    if best_score >= HIGH_CONF:
        return best_chapter, best_id, 2, False
    elif best_score == MEDIUM_CONF:
        return best_chapter, best_id, 1, False
    else:
        return "", "", 0, True


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


def save_questions(questions: list):
    with open(QUESTIONS_JSONL, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    with open(QUESTIONS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=QUESTION_CSV_HEADERS, extrasaction="ignore")
        writer.writeheader()
        for q in questions:
            writer.writerow(q)


def update_taxonomy_counts(questions: list, taxonomy: dict) -> dict:
    """Update question_count per chapter in taxonomy."""
    # Build count map
    chapter_counts = {}
    for q in questions:
        cid = q.get("chapter_id", "")
        if cid:
            chapter_counts[cid] = chapter_counts.get(cid, 0) + 1

    def update_chapters(chapters):
        for ch in chapters:
            ch["question_count"] = chapter_counts.get(ch["id"], 0)

    update_chapters(taxonomy["subjects"]["Physics"]["chapters"])
    update_chapters(taxonomy["subjects"]["Mathematics"]["chapters"])
    for div in taxonomy["subjects"]["Chemistry"]["sub_divisions"].values():
        update_chapters(div["chapters"])

    with open(TAXONOMY_FILE, "w", encoding="utf-8") as f:
        json.dump(taxonomy, f, indent=2)
    return taxonomy


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Classify questions by chapter/topic.")
    parser.add_argument("--subject",    help="Process only this subject.")
    parser.add_argument("--reclassify", action="store_true", help="Re-classify all questions.")
    args = parser.parse_args()

    log("=" * 60)
    log("JEE Main PYQ — Classify Questions")

    taxonomy    = load_taxonomy()
    keyword_map = build_keyword_map(taxonomy)
    questions   = load_questions()

    if not questions:
        log("No questions found. Run extract_questions.py first.", "WARN")
        sys.exit(0)

    log(f"Loaded {len(questions)} questions")

    classified   = 0
    skipped      = 0
    review_flags = 0
    subject_stats = {}

    for q in questions:
        subject = q.get("subject", "")
        if args.subject and subject != args.subject:
            continue

        # Skip if already classified, unless reclassify mode
        if q.get("chapter") and not args.reclassify:
            skipped += 1
            continue

        q_text = q.get("question_text", "")
        chapter_name, chapter_id, conf, review = classify_question(q_text, subject, keyword_map)

        q["chapter"]    = chapter_name
        q["chapter_id"] = chapter_id

        if review:
            q["review_required"] = True
            review_flags += 1
        else:
            # Only clear review flag if we had good confidence
            if conf >= HIGH_CONF and not q.get("review_required", False):
                q["review_required"] = False

        classified += 1
        subj_stat = subject_stats.setdefault(subject, {"classified": 0, "review": 0, "no_match": 0})
        subj_stat["classified"] += 1
        if review:
            subj_stat["review"] += 1
        if not chapter_name:
            subj_stat["no_match"] += 1

    # Save back
    save_questions(questions)
    update_taxonomy_counts(questions, taxonomy)

    # Update status
    with open(STATUS_FILE, encoding="utf-8") as f:
        status = json.load(f)
    total_classified = sum(1 for q in questions if q.get("chapter"))
    status["questions_classified"] = total_classified
    status["last_action"]  = f"Classified {classified} questions"
    status["last_updated"] = datetime.now().isoformat()
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    log(f"Classification complete. Classified={classified}, Skipped={skipped}, Review={review_flags}")

    # Summary
    print("\n" + "=" * 60)
    print(f"{'CLASSIFICATION SUMMARY':^60}")
    print("=" * 60)
    print(f"  Questions processed : {classified}")
    print(f"  Skipped (done)      : {skipped}")
    print(f"  Flagged for review  : {review_flags}")
    print()
    print(f"  {'Subject':<18} {'Classified':>12} {'Review':>8} {'No Match':>10}")
    print(f"  {'-'*50}")
    for subj, stat in sorted(subject_stats.items()):
        print(f"  {subj:<18} {stat['classified']:>12} {stat['review']:>8} {stat['no_match']:>10}")

    # Chapter counts
    print()
    print(f"  Top chapters by question count:")
    chapter_counts = {}
    for q in questions:
        ch = q.get("chapter", "")
        if ch:
            chapter_counts[ch] = chapter_counts.get(ch, 0) + 1
    for ch, cnt in sorted(chapter_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {ch:<40} {cnt:>5}")
    print("=" * 60)
    print("\nNext step: python 07_SCRIPTS/cluster_questions.py")


if __name__ == "__main__":
    main()
