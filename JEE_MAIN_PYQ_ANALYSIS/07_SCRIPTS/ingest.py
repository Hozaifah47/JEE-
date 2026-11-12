#!/usr/bin/env python3
"""
ingest.py — JEE Main PYQ Analysis System
Scans 01_RAW_PYQS/ and registers all PDFs into source_inventory.csv and master_manifest.json.

Usage:
    python 07_SCRIPTS/ingest.py
    python 07_SCRIPTS/ingest.py --dry-run
    python 07_SCRIPTS/ingest.py --year 2024
"""

import os
import re
import csv
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR      = PROJECT_ROOT / "01_RAW_PYQS"
ADMIN_DIR    = PROJECT_ROOT / "00_ADMIN"
LOG_DIR      = PROJECT_ROOT / "08_LOGS"

SOURCE_INV   = ADMIN_DIR / "source_inventory.csv"
MANIFEST     = ADMIN_DIR / "master_manifest.json"
STATUS_FILE  = ADMIN_DIR / "project_status.json"
PROC_LOG     = ADMIN_DIR / "processing_log.md"
INGEST_LOG   = LOG_DIR   / "ingest.log"

MONTH_MAP = {
    "Jan":  "01", "Feb":  "02", "Mar":  "03", "Apr":  "04",
    "May":  "05", "Jun":  "06", "Jul":  "07", "Aug":  "08",
    "Sep":  "09", "Oct":  "10", "Nov":  "11", "Dec":  "12",
}

# Pattern: "JEE Main 2024 (29 Jan Shift 1) Previous Year Paper..."
FILENAME_PATTERN = re.compile(
    r"JEE Main (\d{4}) \((\d{1,2}) ([A-Za-z]+) Shift (\d)\)",
    re.IGNORECASE
)

CSV_HEADERS = [
    "file_id", "filename", "year", "date", "session", "shift",
    "subject", "source_path", "registered_at", "readable",
    "duplicate_of", "notes"
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(INGEST_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def parse_filename(filename: str):
    """Extract year, date, shift from filename. Returns dict or None."""
    m = FILENAME_PATTERN.search(filename)
    if not m:
        return None
    year_str, day_str, mon_str, shift_str = m.groups()
    mon_num = MONTH_MAP.get(mon_str[:3].capitalize())
    if not mon_num:
        return None
    day = day_str.zfill(2)
    date_iso = f"{year_str}-{mon_num}-{day}"
    file_id  = f"JEE-{year_str}-{mon_num}{day}-S{shift_str}"
    return {
        "year":    int(year_str),
        "date":    date_iso,
        "shift":   int(shift_str),
        "file_id": file_id,
    }


def try_open_pdf(pdf_path: Path):
    """Try opening with PyMuPDF; return (readable:bool, page_count:int, notes:str)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        pages = doc.page_count
        doc.close()
        return True, pages, ""
    except ImportError:
        return None, 0, "PyMuPDF not installed — readability unchecked"
    except Exception as e:
        return False, 0, f"Cannot open: {e}"


def load_existing_ids():
    """Return set of already-registered file_ids from source_inventory.csv."""
    if not SOURCE_INV.exists():
        return set()
    with open(SOURCE_INV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["file_id"] for row in reader if row.get("file_id")}


def load_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: dict):
    manifest["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def save_status(status: dict):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


def append_proc_log(entry: str):
    with open(PROC_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n### {datetime.now().strftime('%Y-%m-%d %H:%M')} IST — Ingest Run\n{entry}\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Ingest JEE Main PYQ PDFs.")
    parser.add_argument("--dry-run", action="store_true", help="Scan only, do not write.")
    parser.add_argument("--year",    type=int,            help="Process only this year.")
    args = parser.parse_args()

    log("=" * 60)
    log("JEE Main PYQ — Ingest Script")
    log(f"Project root : {PROJECT_ROOT}")
    log(f"Dry run      : {args.dry_run}")

    if not RAW_DIR.exists():
        log(f"ERROR: RAW_DIR not found: {RAW_DIR}", "ERROR")
        sys.exit(1)

    existing_ids = load_existing_ids()
    log(f"Already registered: {len(existing_ids)} files")

    manifest = load_manifest()

    # Collect all PDFs
    all_pdfs = []
    for year_dir in sorted(RAW_DIR.iterdir()):
        if not year_dir.is_dir():
            continue
        if args.year and year_dir.name != str(args.year):
            continue
        for pdf_path in sorted(year_dir.glob("*.pdf")):
            all_pdfs.append(pdf_path)

    log(f"Found {len(all_pdfs)} PDF(s) in RAW_PYQS/")

    new_rows   = []
    skipped    = []
    errors     = []
    registered = 0

    for pdf_path in all_pdfs:
        filename = pdf_path.name
        parsed   = parse_filename(filename)

        if not parsed:
            log(f"  SKIP (unrecognised name): {filename}", "WARN")
            errors.append(filename)
            continue

        file_id = parsed["file_id"]

        if file_id in existing_ids:
            log(f"  SKIP (already registered): {file_id}")
            skipped.append(file_id)
            continue

        readable, pages, notes = try_open_pdf(pdf_path)

        row = {
            "file_id":       file_id,
            "filename":      filename,
            "year":          parsed["year"],
            "date":          parsed["date"],
            "session":       "",
            "shift":         parsed["shift"],
            "subject":       "All",
            "source_path":   str(pdf_path),
            "registered_at": datetime.now().isoformat(),
            "readable":      "true" if readable else ("unknown" if readable is None else "false"),
            "duplicate_of":  "",
            "notes":         f"{pages} pages. {notes}".strip(),
        }
        new_rows.append(row)
        existing_ids.add(file_id)
        registered += 1
        log(f"  + {file_id}  |  {filename[:60]}  |  readable={readable}  pages={pages}")

    # ── Write results ──────────────────────────────────────────────────────────
    if args.dry_run:
        log(f"\nDRY RUN — no files written. Would register {registered} new papers.")
        return

    # Append to source_inventory.csv
    write_header = not SOURCE_INV.exists() or SOURCE_INV.stat().st_size < 10
    with open(SOURCE_INV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if write_header:
            writer.writeheader()
        for row in new_rows:
            writer.writerow(row)

    # Update manifest
    manifest_paper_ids = {p["file_id"] for p in manifest.get("papers", [])}
    for row in new_rows:
        if row["file_id"] not in manifest_paper_ids:
            manifest["papers"].append({
                "file_id":    row["file_id"],
                "filename":   row["filename"],
                "year":       row["year"],
                "date":       row["date"],
                "shift":      row["shift"],
                "readable":   row["readable"],
                "registered": row["registered_at"],
                "questions_extracted": 0,
            })

    all_years = sorted({p["year"] for p in manifest["papers"]})
    manifest["years_covered"]          = all_years
    manifest["total_papers_registered"] = len(manifest["papers"])
    manifest["status"]                  = "REGISTERED"
    manifest["analysis_phase"]          = "EXTRACTION READY"
    save_manifest(manifest)

    # Update project_status.json
    with open(STATUS_FILE, encoding="utf-8") as f:
        status = json.load(f)
    status["papers_registered"] = manifest["total_papers_registered"]
    status["last_action"]       = f"Ingested {registered} new papers"
    status["last_updated"]      = datetime.now().isoformat()
    if "Register source PDFs" in status.get("pending_actions", []):
        status["pending_actions"].remove("Register source PDFs")
        status["pending_actions"].insert(0, "Run extract_questions.py")
    save_status(status)

    # Append to processing_log.md
    summary = (
        f"- Scanned: {len(all_pdfs)} PDFs\n"
        f"- Registered: {registered} new papers\n"
        f"- Skipped (already registered): {len(skipped)}\n"
        f"- Errors (unrecognised name): {len(errors)}\n"
        f"- Total in inventory: {manifest['total_papers_registered']}\n"
        f"- Years covered: {all_years}\n"
    )
    if errors:
        summary += "- Unrecognised files:\n" + "".join(f"  - {e}\n" for e in errors)
    append_proc_log(summary)

    # ── Summary Table ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"{'INGEST SUMMARY':^60}")
    print("=" * 60)
    print(f"  PDFs scanned      : {len(all_pdfs)}")
    print(f"  New registrations : {registered}")
    print(f"  Already existed   : {len(skipped)}")
    print(f"  Errors            : {len(errors)}")
    print(f"  Total in manifest : {manifest['total_papers_registered']}")
    print(f"  Years covered     : {all_years}")
    print("=" * 60)
    print("\nNext step: python 07_SCRIPTS/extract_questions.py")


if __name__ == "__main__":
    main()
