#!/usr/bin/env python3
"""Apply only high-confidence OCR recoveries for image-only MCQ options."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / '03_DATABASE' / 'questions.jsonl'
OCR_FILES = [Path('/tmp/jee-ocr-results.json'), Path('/tmp/jee-ocr-results2.json')]


def clean(value):
    value = re.sub(r'\s+', ' ', value or '').strip(' \t:;')
    value = re.sub(r'\b(MathonGo|JEE Main Previous Year Paper)\b', '', value, flags=re.I)
    return re.sub(r'\s+', ' ', value).strip(' \t:;')


QUESTION = re.compile(r'(?im)^\s*Q\s*(\d{1,3})\s*[.) :]')
LABEL = re.compile(r'(?<!\w)(?:\(([1-4])\)|([1-4])[.)])(?=\s|$)')


def blocks(text):
    matches = list(QUESTION.finditer(text))
    result = {}
    for i, match in enumerate(matches):
        number = int(match.group(1))
        body = text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        result[number] = body
    return result


def recover(text):
    found = []
    for match in LABEL.finditer(text):
        label = int(match.group(1) or match.group(2))
        if label != len(found) + 1:
            continue
        found.append((label, match.end()))
        if len(found) == 4:
            break
    if len(found) != 4 or [x[0] for x in found] != [1, 2, 3, 4]:
        return []
    values = []
    for i, (_, start) in enumerate(found):
        end = found[i + 1][1] if i + 1 < len(found) else len(text)
        value = clean(text[start:end])
        if not value or len(value) > 500:
            return []
        values.append(value)
    if len(set(values)) != 4:
        return []
    return values


def main():
    questions = [json.loads(line) for line in DB.read_text(encoding='utf-8').splitlines() if line.strip()]
    pages = []
    for path in OCR_FILES:
        if path.exists():
            pages.extend(json.loads(path.read_text(encoding='utf-8')))
    page_map = {}
    for page in pages:
        for number, body in blocks(page['text']).items():
            page_map.setdefault((page['source_file'], number), []).append(body)
    repaired = 0
    candidates = 0
    for q in questions:
        if q.get('question_type') != 'MCQ' or any(str(x).strip() for x in (q.get('options') or [])):
            continue
        candidates_on_pages = page_map.get((q.get('source_file'), int(q.get('question_number') or 0)), [])
        if len(candidates_on_pages) != 1:
            continue
        values = recover(candidates_on_pages[0])
        if values:
            candidates += 1
            q['options'] = values
            q['options_repaired'] = True
            q['options_source'] = 'ocr'
            repaired += 1
    DB.write_text(''.join(json.dumps(q, ensure_ascii=False) + '\n' for q in questions), encoding='utf-8')
    print(f'OCR candidates={candidates} repaired={repaired}')


if __name__ == '__main__':
    main()
