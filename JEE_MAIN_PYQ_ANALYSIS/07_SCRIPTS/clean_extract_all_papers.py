#!/usr/bin/env python3
"""
clean_extract_all_papers.py — Clean Question Extractor for JEE Main PYQs
1. Filters out headers (y < 65) and footers (y > 795) containing MathonGo URLs/promos.
2. Spatially reconstructs lines to embed mathematical expressions seamlessly into the sentence.
3. Reliably parses options (1), (2), (3), (4) or (A), (B), (C), (D) into distinct clean options.
4. Cleans up text artifacts and removes any residual promotional text.
"""

import json, re, csv, os
from pathlib import Path
import pymupdf

ROOT = Path("/home/hozaifah/HozzCode/JEE/JEE_MAIN_PYQ_ANALYSIS")
RAW_DIR = ROOT / "01_RAW_PYQS"
QUESTIONS_JSONL = ROOT / "03_DATABASE" / "questions.jsonl"
QUESTIONS_CSV = ROOT / "03_DATABASE" / "questions.csv"

# Load existing metadata (chapter classifications, clusters, etc.)
existing_meta = {}
if QUESTIONS_JSONL.exists():
    with open(QUESTIONS_JSONL, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    q = json.loads(line)
                    existing_meta[q.get("question_id")] = q
                except:
                    pass

print(f"Loaded existing metadata for {len(existing_meta)} questions.")

PROMO_PATTERNS = [
    r"Join the Most Relevant Test Series.*",
    r"https?://\S+",
    r"JEE Main \d{4} \([^\)]+\) Question Paper",
    r"JEE Main Previous Year Paper",
    r"MathonGo",
    r"Download MathonGo App.*",
]

def clean_text_line(text):
    for p in PROMO_PATTERNS:
        text = re.sub(p, "", text, flags=re.IGNORECASE)
    return text.strip()

def extract_clean_page_lines(page):
    words = page.get_text("words")
    # Discard top header (y < 65) and bottom footer (y > 792)
    content_words = [w for w in words if w[1] >= 62 and w[3] <= 792]
    # Sort vertically by line bands of 7pt, then horizontally
    content_words.sort(key=lambda w: (round(w[1] / 7) * 7, w[0]))
    
    lines = []
    curr_y = None
    curr_line = []
    for w in content_words:
        line_y = round(w[1] / 7) * 7
        w_text = w[4]
        if curr_y is None or line_y == curr_y:
            curr_y = line_y
            curr_line.append(w_text)
        else:
            cleaned = clean_text_line(" ".join(curr_line))
            if cleaned:
                lines.append(cleaned)
            curr_y = line_y
            curr_line = [w_text]
    if curr_line:
        cleaned = clean_text_line(" ".join(curr_line))
        if cleaned:
            lines.append(cleaned)
    return lines

def parse_questions_from_paper(pdf_path, year, date, shift):
    doc = pymupdf.open(pdf_path)
    all_lines = []
    
    # Check for answer key page
    num_pages = len(doc)
    # The last page or two might be the answer key table
    for p_idx in range(num_pages):
        page = doc[p_idx]
        lines = extract_clean_page_lines(page)
        all_lines.extend(lines)
        
    full_text = "\n".join(all_lines)
    
    # Split by Question markers: Q1., Q2., Q 1., etc.
    q_splits = re.split(r'\n(?=Q\s*\d+\s*[\.:\)])', "\n" + full_text)
    
    parsed_questions = []
    for block in q_splits:
        block = block.strip()
        if not block:
            continue
        m = re.match(r'Q\s*(\d+)\s*[\.:\)]\s*(.*)', block, re.DOTALL)
        if not m:
            continue
        q_num = int(m.group(1))
        content = m.group(2).strip()
        
        # Stop at Answer Key section if present
        if "Answer Key" in content or "ANSWER KEY" in content:
            content = re.split(r'Answer Key|ANSWER KEY', content, flags=re.IGNORECASE)[0].strip()
            
        # Determine Subject by Q-Number convention
        if q_num <= 30:
            subj = "Physics"
            prefix = "PHY"
        elif q_num <= 60:
            subj = "Chemistry"
            prefix = "CHEM"
        else:
            subj = "Mathematics"
            prefix = "MATH"
            
        date_slug = re.sub(r'[^0-9]', '', date)
        if len(date_slug) < 4:
            date_slug = "0101"
        qid = f"{prefix}-{year}-{date_slug}-S{shift}-Q{q_num:03d}"
        
        # Parse options
        # Look for (1), (2), (3), (4) or (A), (B), (C), (D)
        # Check if integer type question
        is_integer = False
        options = []
        q_text = content
        
        # Common integer question endings
        if "to the nearest integer" in content.lower() or "is ________" in content or "nearest integer" in content.lower():
            is_integer = True
            
        opt_matches = list(re.finditer(r'\(([1-4A-Da-d])\)\s*', content))
        if len(opt_matches) >= 4:
            # First option position is where question text ends
            q_text = content[:opt_matches[0].start()].strip()
            for i in range(len(opt_matches)):
                start = opt_matches[i].end()
                end = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(content)
                opt_val = content[start:end].strip()
                # Clean up newlines in option text
                opt_val = re.sub(r'\s+', ' ', opt_val)
                options.append(opt_val)
            options = options[:4]
            qtype = "MCQ"
        else:
            qtype = "Integer" if is_integer else "MCQ"
            
        # Final cleanup on question text
        q_text = re.sub(r'\n+', ' ', q_text).strip()
        q_text = re.sub(r'\s+', ' ', q_text)
        for p in PROMO_PATTERNS:
            q_text = re.sub(p, "", q_text, flags=re.IGNORECASE).strip()
            
        # Retrieve existing metadata if already classified/clustered
        prev = existing_meta.get(qid, {})
        
        parsed_questions.append({
            "question_id": qid,
            "subject": subj,
            "chapter": prev.get("chapter") or "General",
            "topic": prev.get("topic") or "General",
            "concept": prev.get("concept") or "Standard Problem Formulation",
            "cluster_id": prev.get("cluster_id") or f"{prefix}-GEN-STD_CONCEPT",
            "year": int(year),
            "session": f"Session {shift}",
            "date": date,
            "shift": int(shift),
            "question_number": q_num,
            "question_type": qtype,
            "question_text": q_text,
            "options": options,
            "correct_answer": prev.get("correct_answer") or "Refer to Answer Key",
            "provided_solution": None,
            "difficulty": prev.get("difficulty") or "Moderate",
            "source_file": Path(pdf_path).name,
            "review_required": False
        })
        
    return parsed_questions

def main():
    pdf_files = list(RAW_DIR.glob("**/*.pdf"))
    print(f"Found {len(pdf_files)} PDF papers to process.")
    
    all_extracted = []
    
    for pdf in sorted(pdf_files):
        # Filename pattern: JEE Main YYYY (DD Mon Shift N) ...
        m = re.search(r'JEE Main (\d{4})\s*\(([^)]+)\)', pdf.name)
        if not m:
            continue
        year = m.group(1)
        details = m.group(2)
        shift_m = re.search(r'Shift\s*(\d)', details, re.IGNORECASE)
        shift = shift_m.group(1) if shift_m else "1"
        date_m = re.search(r'(\d{1,2}\s+[A-Za-z]+)', details)
        date = date_m.group(1) if date_m else "Jan"
        
        qs = parse_questions_from_paper(pdf, year, date, shift)
        all_extracted.extend(qs)
        print(f"  ✓ {pdf.name[:45]}... -> {len(qs)} Qs")
        
    print(f"\nTotal questions cleanly extracted: {len(all_extracted)}")
    
    # Save to questions.jsonl
    with open(QUESTIONS_JSONL, "w", encoding='utf-8') as f:
        for q in all_extracted:
            f.write(json.dumps(q) + "\n")
            
    # Save to questions.csv
    headers = [
        "question_id", "subject", "chapter", "topic", "concept", "cluster_id",
        "year", "date", "shift", "question_number", "question_type",
        "question_text", "difficulty", "source_file"
    ]
    with open(QUESTIONS_CSV, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        for q in all_extracted:
            writer.writerow(q)
            
    print("Updated database files successfully!")

if __name__ == "__main__":
    main()
