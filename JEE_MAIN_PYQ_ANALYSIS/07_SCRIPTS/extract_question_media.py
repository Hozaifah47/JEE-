#!/usr/bin/env python3
"""Extract offline page figures for questions whose text references visual material.

The source PDFs contain both raster figures and vector-only diagrams. Raster image
blocks are extracted losslessly; when a page has no extractable image block, a
high-resolution page crop is rendered as a reliable offline fallback.
"""
import hashlib
import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "03_DATABASE" / "questions.jsonl"
RAW = ROOT / "01_RAW_PYQS"
ASSETS = ROOT / "05_PRACTICE_SETS" / "assets"

VISUAL_RE = re.compile(r"\b(figure|fig\.?|graph|diagram|circuit|shown|truth table|matrix|ray|pulley|schematic|plot|image|table)\b", re.I)

def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)

def find_page(page_texts, question_number, question_text):
    needles = [question_text[:90].strip(), f"Q{question_number}", f"Q {question_number}"]
    for needle in needles:
        if len(needle) < 4:
            continue
        for page_number, page_text in enumerate(page_texts):
            if needle in page_text:
                return page_number
    return None

def extract_asset(page, stem):
    # Prefer actual embedded image blocks; they preserve the original diagram quality.
    candidates = []
    for image in page.get_images(full=True):
        xref = image[0]
        try:
            info = page.parent.extract_image(xref)
            if info.get("width", 0) * info.get("height", 0) >= 2500:
                candidates.append(info)
        except Exception:
            continue
    if candidates:
        info = max(candidates, key=lambda item: item.get("width", 0) * item.get("height", 0))
        suffix = info.get("ext", "png")
        out = ASSETS / f"{stem}.{suffix}"
        if not out.exists():
            out.write_bytes(info["image"])
        return out.name

    # Vector diagrams and tables are rendered from the page, cropped to the content area.
    pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False, clip=fitz.Rect(0, 55, page.rect.width, page.rect.height - 35))
    out = ASSETS / f"{stem}.png"
    if not out.exists():
        pix.save(str(out))
    return out.name

def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    questions = []
    with DB.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                questions.append(json.loads(line))

    pdf_by_name = {path.name: path for path in RAW.rglob("*.pdf")}
    pdf_by_safe_name = {safe_name(path.name).lower(): path for path in pdf_by_name.values()}

    pdf_cache = {}
    attached = 0
    for question in questions:
        text = question.get("question_text", "")
        options = question.get("options") or []
        if not (VISUAL_RE.search(text) or not any(str(option).strip() for option in options)):
            continue
        source_file = question.get("source_file", "")
        pdf_path = pdf_by_name.get(source_file) or pdf_by_safe_name.get(safe_name(source_file).lower())
        if not pdf_path:
            continue
        key = str(pdf_path)
        if key not in pdf_cache:
            doc = fitz.open(pdf_path)
            pdf_cache[key] = (doc, [page.get_text() for page in doc])
        doc, page_texts = pdf_cache[key]
        page_number = find_page(page_texts, question.get("question_number", 0), text)
        if page_number is None:
            continue
        stem = hashlib.sha1(question.get("question_id", "").encode()).hexdigest()[:16]
        question["media_asset"] = extract_asset(doc[page_number], stem)
        question["source_page"] = page_number + 1
        attached += 1

    with DB.open("w", encoding="utf-8") as handle:
        for question in questions:
            handle.write(json.dumps(question, ensure_ascii=False) + "\n")
    for doc, _ in pdf_cache.values():
        doc.close()
    print(f"Attached offline media to {attached} questions; assets in {ASSETS}")

if __name__ == "__main__":
    main()
