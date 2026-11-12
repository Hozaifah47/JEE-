#!/usr/bin/env python3
"""
extract_questions.py — JEE Main PYQ Analysis System
Extracts questions from registered PDFs using PyMuPDF + heuristics.

Usage:
    python 07_SCRIPTS/extract_questions.py
    python 07_SCRIPTS/extract_questions.py --file-id JEE-2024-0129-S1
    python 07_SCRIPTS/extract_questions.py --year 2024
    python 07_SCRIPTS/extract_questions.py --dry-run
"""

import os
import re
import csv
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ROOT   = Path(__file__).resolve().parent.parent
ADMIN_DIR      = PROJECT_ROOT / "00_ADMIN"
DATABASE_DIR   = PROJECT_ROOT / "03_DATABASE"
EXTRACTED_DIR  = PROJECT_ROOT / "02_EXTRACTED_DATA"
LOG_DIR        = PROJECT_ROOT / "08_LOGS"

SOURCE_INV     = ADMIN_DIR    / "source_inventory.csv"
Q_INV          = ADMIN_DIR    / "question_inventory.csv"
MANIFEST       = ADMIN_DIR    / "master_manifest.json"
STATUS_FILE    = ADMIN_DIR    / "project_status.json"

QUESTIONS_JSONL = DATABASE_DIR / "questions.jsonl"
QUESTIONS_CSV   = DATABASE_DIR / "questions.csv"
EXTRACT_LOG     = LOG_DIR      / "extraction.log"

# JEE Main: 1-30 Physics, 31-60 Chemistry, 61-90 Mathematics
SUBJECT_RANGES = {
    "Physics":     (1, 30),
    "Chemistry":   (31, 60),
    "Mathematics": (61, 90),
}
SUBJECT_CODES  = {"Physics": "PHY", "Chemistry": "CHEM", "Mathematics": "MATH"}

# Regex patterns for MathonGo-formatted PDFs
RE_QUESTION_NUM   = re.compile(r"^\s*(?:Q\.?\s*)?(\d{1,2})\s*[.:)]\s+(.+)", re.MULTILINE | re.DOTALL)
RE_QUESTION_START = re.compile(r"(?:^|\n)\s*(?:Q\.?\s*)?(\d{1,2})[\s.:)]+")
RE_OPTION_LINE    = re.compile(r"^\s*[\(\[]?\s*([A-D])\s*[\)\].]?\s*[.:)]\s*(.+)", re.IGNORECASE)
RE_OPTION_NUM     = re.compile(r"^\s*([1-4])\s*[.:)]\s*(.+)")
RE_ANSWER_KEY     = re.compile(r"(?:answer\s*key|answers?|ans\.?)\s*[:—\-]?\s*\n", re.IGNORECASE)
RE_ANS_LINE       = re.compile(r"\b(\d{1,2})\s*[.:)]\s*([A-D]|\d{1,3})\b", re.IGNORECASE)

QUESTION_CSV_HEADERS = [
    "question_id", "subject", "chapter", "topic", "concept", "cluster_id",
    "year", "date", "shift", "question_number", "question_type",
    "question_text", "correct_answer", "difficulty",
    "source_file", "source_page", "extraction_confidence", "review_required"
]

Q_INV_HEADERS = [
    "question_id", "source_file_id", "subject", "chapter", "topic", "concept",
    "cluster_id", "year", "date", "shift", "question_number", "question_type",
    "difficulty", "extraction_confidence", "review_required"
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXTRACT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_subject(q_num: int) -> str:
    for subj, (lo, hi) in SUBJECT_RANGES.items():
        if lo <= q_num <= hi:
            return subj
    return "Unknown"


def get_question_type(text: str) -> str:
    """Heuristically determine question type."""
    t = text.lower()
    if any(x in t for x in ["integer type", "integer answer", "numerical value", "nearest integer"]):
        return "Integer"
    if any(x in t for x in ["numerical", "calculate", "find the value"]):
        return "Numerical"
    return "MCQ"


def build_question_id(subject: str, year: int, date: str, shift: int, q_num: int) -> str:
    code = SUBJECT_CODES.get(subject, "UNK")
    # date: "2024-01-29" → "0129"
    date_part = date.replace("-", "")[4:]  # MMDD
    return f"{code}-{year}-{date_part}-S{shift}-Q{q_num:03d}"


def extract_text_from_pdf(pdf_path: Path) -> list:
    """Return list of (page_num, text) tuples."""
    try:
        import fitz
    except ImportError:
        log("PyMuPDF not installed. Install with: pip install pymupdf", "ERROR")
        return []
    try:
        doc = fitz.open(str(pdf_path))
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            pages.append((i, text))
        doc.close()
        return pages
    except Exception as e:
        log(f"Error reading {pdf_path.name}: {e}", "ERROR")
        return []


def extract_answer_key(all_text: str) -> dict:
    """
    Try to find an answer key section. Returns dict {q_num_int: answer_str}.
    """
    answers = {}
    # Look for section after "Answer Key" or "Answers"
    m = RE_ANSWER_KEY.search(all_text)
    if m:
        key_section = all_text[m.end():]
        for match in RE_ANS_LINE.finditer(key_section[:3000]):
            qn  = int(match.group(1))
            ans = match.group(2).upper()
            if 1 <= qn <= 90:
                answers[qn] = ans
    return answers


def parse_questions_from_text(pages: list, file_id: str, year: int, date: str, shift: int) -> list:
    """
    Parse questions from extracted text pages.
    Returns list of question dicts.
    """
    all_text = "\n".join(text for _, text in pages)

    # Build page index: char_offset → page_num
    page_starts = []
    offset = 0
    for pnum, text in pages:
        page_starts.append((offset, pnum))
        offset += len(text) + 1  # +1 for the \n we added

    def char_to_page(pos: int) -> int:
        page = 1
        for start, pnum in page_starts:
            if start <= pos:
                page = pnum
            else:
                break
        return page

    # Extract answer key
    answer_key = extract_answer_key(all_text)
    log(f"  Found {len(answer_key)} answers in answer key")

    # Split text into question blocks by detecting "Q.N" or "N." patterns
    # Find all question start positions
    question_starts = []
    for m in RE_QUESTION_START.finditer(all_text):
        qn = int(m.group(1))
        if 1 <= qn <= 90:
            question_starts.append((m.start(), qn, m.end()))

    # Deduplicate: keep only first occurrence of each q_num
    seen_qnums  = {}
    dedup_starts = []
    for pos, qn, end in question_starts:
        if qn not in seen_qnums:
            seen_qnums[qn] = pos
            dedup_starts.append((pos, qn, end))

    dedup_starts.sort(key=lambda x: x[0])

    questions = []
    for idx, (pos, qn, end) in enumerate(dedup_starts):
        # Text until next question start (or end of doc)
        if idx + 1 < len(dedup_starts):
            block = all_text[end:dedup_starts[idx + 1][0]]
        else:
            # Last question: take up to answer key or 2000 chars
            block = all_text[end:end + 2000]

        # Extract options if MCQ
        options = {}
        lines = block.split("\n")
        q_lines = []
        for line in lines:
            opt_m = RE_OPTION_LINE.match(line)
            if opt_m:
                options[opt_m.group(1).upper()] = opt_m.group(2).strip()
            else:
                q_lines.append(line)

        q_text = " ".join(l.strip() for l in q_lines if l.strip())
        q_text = re.sub(r"\s{2,}", " ", q_text).strip()

        subject = get_subject(qn)
        q_type  = get_question_type(q_text)
        if options:
            q_type = "MCQ"

        confidence = 0.9 if options else 0.7
        if len(q_text) < 20:
            confidence = 0.4

        q_id = build_question_id(subject, year, date, shift, qn)
        source_page = char_to_page(pos)

        q = {
            "question_id":           q_id,
            "subject":               subject,
            "chapter":               "",
            "chapter_id":            "",
            "topic":                 "",
            "concept":               "",
            "cluster_id":            "",
            "year":                  year,
            "date":                  date,
            "shift":                 shift,
            "question_number":       qn,
            "question_type":         q_type,
            "question_text":         q_text,
            "options":               options,
            "correct_answer":        answer_key.get(qn, ""),
            "difficulty":            "",
            "source_file":           file_id,
            "source_page":           source_page,
            "extraction_confidence": round(confidence, 2),
            "review_required":       confidence < 0.7,
        }
        questions.append(q)

    return questions


def save_extracted_text(file_id: str, subject: str, year: int, pages: list):
    """Save per-paper raw text to 02_EXTRACTED_DATA/{Subject}/."""
    subj_dir = EXTRACTED_DIR / subject
    subj_dir.mkdir(parents=True, exist_ok=True)
    out_path = subj_dir / f"{file_id}_{subject}_raw.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        for pnum, text in pages:
            f.write(f"\n{'─'*60}\nPAGE {pnum}\n{'─'*60}\n{text}\n")
    return out_path


def load_registered_pdfs(year_filter=None, file_id_filter=None):
    rows = []
    if not SOURCE_INV.exists():
        return rows
    with open(SOURCE_INV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if file_id_filter and row["file_id"] != file_id_filter:
                continue
            if year_filter and str(row["year"]) != str(year_filter):
                continue
            rows.append(row)
    return rows


def get_extracted_ids():
    """Return set of file_ids already in questions.jsonl."""
    if not QUESTIONS_JSONL.exists():
        return set()
    ids = set()
    with open(QUESTIONS_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    q = json.loads(line)
                    ids.add(q.get("source_file", ""))
                except json.JSONDecodeError:
                    pass
    return ids


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Extract questions from registered PDFs.")
    parser.add_argument("--file-id", help="Process only this file_id.")
    parser.add_argument("--year",    type=int, help="Process only this year.")
    parser.add_argument("--force",   action="store_true", help="Re-extract even if already done.")
    parser.add_argument("--dry-run", action="store_true", help="Scan only, do not write.")
    args = parser.parse_args()

    log("=" * 60)
    log("JEE Main PYQ — Extract Questions")

    registered  = load_registered_pdfs(year_filter=args.year, file_id_filter=args.file_id)
    extracted   = get_extracted_ids()

    log(f"Registered PDFs: {len(registered)}")
    log(f"Already extracted: {len(extracted)}")

    total_q  = 0
    papers   = 0
    low_conf = 0

    # Open files for appending
    if not args.dry_run:
        qjsonl_f = open(QUESTIONS_JSONL, "a", encoding="utf-8")
        qcsv_f   = open(QUESTIONS_CSV, "a", newline="", encoding="utf-8")
        qinv_f   = open(Q_INV, "a", newline="", encoding="utf-8")
        qcsv_writer = csv.DictWriter(qcsv_f, fieldnames=QUESTION_CSV_HEADERS, extrasaction="ignore")
        qinv_writer = csv.DictWriter(qinv_f, fieldnames=Q_INV_HEADERS, extrasaction="ignore")

    try:
        for row in registered:
            file_id   = row["file_id"]
            pdf_path  = Path(row["source_path"])
            year      = int(row["year"])
            date      = row["date"]
            shift     = int(row["shift"])

            if file_id in extracted and not args.force:
                log(f"  SKIP (already extracted): {file_id}")
                continue

            if not pdf_path.exists():
                log(f"  ERROR: PDF not found: {pdf_path}", "ERROR")
                continue

            log(f"  Processing: {file_id}  →  {pdf_path.name[:60]}")
            pages = extract_text_from_pdf(pdf_path)
            if not pages:
                log(f"  ERROR: Could not read pages from {file_id}", "ERROR")
                continue

            questions = parse_questions_from_text(pages, file_id, year, date, shift)
            log(f"  Extracted {len(questions)} questions")

            # Save per-subject raw text
            if not args.dry_run:
                for subject in ["Physics", "Chemistry", "Mathematics"]:
                    save_extracted_text(file_id, subject, year, pages)

            for q in questions:
                total_q  += 1
                if q["review_required"]:
                    low_conf += 1

                if not args.dry_run:
                    qjsonl_f.write(json.dumps(q, ensure_ascii=False) + "\n")
                    qcsv_writer.writerow(q)
                    qinv_writer.writerow({
                        "question_id":           q["question_id"],
                        "source_file_id":        file_id,
                        "subject":               q["subject"],
                        "chapter":               q["chapter"],
                        "topic":                 q["topic"],
                        "concept":               q["concept"],
                        "cluster_id":            q["cluster_id"],
                        "year":                  q["year"],
                        "date":                  q["date"],
                        "shift":                 q["shift"],
                        "question_number":       q["question_number"],
                        "question_type":         q["question_type"],
                        "difficulty":            q["difficulty"],
                        "extraction_confidence": q["extraction_confidence"],
                        "review_required":       q["review_required"],
                    })

            papers += 1
            extracted.add(file_id)

    finally:
        if not args.dry_run:
            qjsonl_f.close()
            qcsv_f.close()
            qinv_f.close()

    # Update manifest & status
    if not args.dry_run:
        with open(MANIFEST, encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["total_questions_extracted"] = manifest.get("total_questions_extracted", 0) + total_q
        manifest["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        with open(STATUS_FILE, encoding="utf-8") as f:
            status = json.load(f)
        status["questions_extracted"] = status.get("questions_extracted", 0) + total_q
        status["last_action"]  = f"Extracted {total_q} questions from {papers} papers"
        status["last_updated"] = datetime.now().isoformat()
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print(f"{'EXTRACTION SUMMARY':^60}")
    print("=" * 60)
    print(f"  Papers processed  : {papers}")
    print(f"  Questions found   : {total_q}")
    print(f"  Review required   : {low_conf}")
    if papers:
        print(f"  Avg per paper     : {total_q // papers}")
    print("=" * 60)
    print("\nNext step: python 07_SCRIPTS/classify_questions.py")


if __name__ == "__main__":
    main()
