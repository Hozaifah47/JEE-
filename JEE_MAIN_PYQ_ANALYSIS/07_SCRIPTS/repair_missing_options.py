#!/usr/bin/env python3
"""Recover MCQ options from source-page text when the first extraction missed them."""
import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / '03_DATABASE' / 'questions.jsonl'
RAW = ROOT / '01_RAW_PYQS'
PROMO = re.compile(r'Join the Most Relevant Test Series.*|https?://\S+|JEE Main Previous Year Paper|MathonGo', re.I)

def clean(value):
    value = PROMO.sub('', value or '')
    value = re.sub(r'\s+', ' ', value)
    return value.strip(' \n\t:;')

def option_values(page_text):
    matches = list(re.finditer(r'\(([1-4])\)\s*', page_text))
    if len(matches) < 4:
        return []
    values=[]
    for i, match in enumerate(matches[:4]):
        end = matches[i+1].start() if i + 1 < len(matches) else len(page_text)
        values.append(clean(page_text[match.end():end]))
    if all(values) and len(set(values)) > 1:
        return values
    return []

def main():
    questions=[json.loads(line) for line in DB.read_text(encoding='utf-8').splitlines() if line.strip()]
    pdfs={p.name:p for p in RAW.rglob('*.pdf')}
    docs={}; repaired=0
    for q in questions:
        if q.get('question_type') != 'MCQ' or any(str(x).strip() for x in (q.get('options') or [])):
            continue
        source=pdfs.get(q.get('source_file',''))
        if not source: continue
        key=str(source)
        if key not in docs: docs[key]=fitz.open(source)
        doc=docs[key]
        page_no=(q.get('source_page') or 1)-1
        page_no=max(0,min(page_no,len(doc)-1))
        values=option_values(doc[page_no].get_text())
        if values:
            q['options']=values
            q['options_repaired']=True
            repaired+=1
    DB.write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in questions),encoding='utf-8')
    for doc in docs.values(): doc.close()
    print(f'Repaired options for {repaired} MCQs')

if __name__ == '__main__': main()
