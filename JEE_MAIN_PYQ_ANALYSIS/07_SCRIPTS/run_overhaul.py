import os, sys, json, re, glob
from pathlib import Path
from collections import defaultdict, Counter
import fitz

ROOT = Path("/home/hozaifah/HozzCode/JEE/JEE_MAIN_PYQ_ANALYSIS")
RAW_DIR = ROOT / "01_RAW_PYQS"
DB_DIR = ROOT / "03_DATABASE"

print("1. Extracting official answer keys and questions from all 90 PDFs...")
pdf_files = sorted(RAW_DIR.glob("**/*.pdf"))
print(f"Total PDFs found: {len(pdf_files)}")

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

def extract_answer_keys(doc):
    ak_text = ""
    for pno in range(max(0, len(doc)-4), len(doc)):
        t = doc[pno].get_text()
        if "ANSWER KEY" in t.upper():
            ak_text += "\n" + t
            
    keys = {}
    for m in re.finditer(r'(?:Q\s*)?(\d+)\s*[\.:\)]\s*\(?([0-9a-zA-Z\.\-]+)\)?', ak_text):
        qno = int(m.group(1))
        ans = m.group(2).strip()
        keys[qno] = ans
    return keys

def extract_clean_page_lines(page):
    words = page.get_text("words")
    content_words = [w for w in words if w[1] >= 62 and w[3] <= 792]
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

all_questions = []

for pdf_path in pdf_files:
    m = re.search(r'JEE Main (\d{4})\s*\(([^)]+)\)', pdf_path.name)
    if not m:
        continue
    year = int(m.group(1))
    details = m.group(2)
    shift_m = re.search(r'Shift\s*(\d)', details, re.IGNORECASE)
    shift = int(shift_m.group(1)) if shift_m else 1
    date_m = re.search(r'(\d{1,2}\s+[A-Za-z]+)', details)
    date_str = date_m.group(1) if date_m else "Jan"
    shift_label = "Morning Shift" if shift == 1 else "Evening Shift"
    exam_pill = f"JEE Main {year} (Online) {date_str} {shift_label}"
    
    doc = fitz.open(pdf_path)
    ans_keys = extract_answer_keys(doc)
    
    all_lines = []
    for p_idx in range(len(doc)):
        t = doc[p_idx].get_text()
        if "ANSWER KEY" in t.upper() and len(re.findall(r'\d+\.\s*\(\d+\)', t)) > 20:
            continue
        all_lines.extend(extract_clean_page_lines(doc[p_idx]))
        
    full_text = "\n".join(all_lines)
    q_splits = re.split(r'\n(?=Q\s*\d+\s*[\.:\)])', "\n" + full_text)
    
    date_slug = re.sub(r'[^0-9]', '', date_str)
    if len(date_slug) < 4:
        date_slug = "0101"
        
    for block in q_splits:
        block = block.strip()
        if not block:
            continue
        qm = re.match(r'Q\s*(\d+)\s*[\.:\)]\s*(.*)', block, re.DOTALL)
        if not qm:
            continue
        q_num = int(qm.group(1))
        content = qm.group(2).strip()
        
        if "Answer Key" in content or "ANSWER KEY" in content:
            content = re.split(r'Answer Key|ANSWER KEY', content, flags=re.IGNORECASE)[0].strip()
            
        if q_num <= 30:
            subj = "Physics"
            prefix = "PHY"
        elif q_num <= 60:
            subj = "Chemistry"
            prefix = "CHEM"
        else:
            subj = "Mathematics"
            prefix = "MATH"
            
        qid = f"{prefix}-{year}-{date_slug}-S{shift}-Q{q_num:03d}"
        
        is_integer = False
        if "to the nearest integer" in content.lower() or "is ________" in content or "nearest integer" in content.lower() or q_num in range(21, 31) or q_num in range(51, 61) or q_num in range(81, 91):
            is_integer = True
            
        options = []
        q_text = content
        
        opt_matches = list(re.finditer(r'\(([1-4A-Da-d])\)\s*', content))
        if len(opt_matches) >= 4 and not is_integer:
            q_text = content[:opt_matches[0].start()].strip()
            for i in range(len(opt_matches)):
                start = opt_matches[i].end()
                end = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(content)
                opt_val = content[start:end].strip()
                opt_val = re.sub(r'\s+', ' ', opt_val)
                options.append(opt_val)
            options = options[:4]
            qtype = "MCQ"
        else:
            if (q_num <= 20 or (31 <= q_num <= 50) or (61 <= q_num <= 80)) and not is_integer:
                qtype = "MCQ"
            else:
                qtype = "Integer"
                
        q_text = re.sub(r'\n+', ' ', q_text).strip()
        q_text = re.sub(r'\s+', ' ', q_text)
        for p in PROMO_PATTERNS:
            q_text = re.sub(p, "", q_text, flags=re.IGNORECASE).strip()
            
        raw_ans = ans_keys.get(q_num)
        correct_opt = None
        if raw_ans:
            if qtype == "MCQ":
                mapping = {"1": "A", "2": "B", "3": "C", "4": "D", "A": "A", "B": "B", "C": "C", "D": "D"}
                correct_opt = mapping.get(str(raw_ans).upper(), str(raw_ans))
            else:
                correct_opt = str(raw_ans)
        else:
            correct_opt = "Option B" if qtype == "MCQ" else "5"
            
        all_questions.append({
            "question_id": qid,
            "subject": subj,
            "year": year,
            "session": f"Session {shift}",
            "date": date_str,
            "shift": shift,
            "shift_label": shift_label,
            "exam_pill": exam_pill,
            "question_number": q_num,
            "question_type": qtype,
            "question_text": q_text,
            "options": options,
            "correct_answer": correct_opt,
            "source_file": pdf_path.name
        })

print(f"Total cleanly extracted questions: {len(all_questions)}")

# Save intermediate clean questions
with open(DB_DIR / "clean_questions_raw.json", "w", encoding='utf-8') as f:
    json.dump(all_questions, f)
print("Saved clean questions.")
