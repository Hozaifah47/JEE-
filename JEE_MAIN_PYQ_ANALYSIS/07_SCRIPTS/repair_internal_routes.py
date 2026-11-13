#!/usr/bin/env python3
"""Create compatibility redirects for legacy portal URLs still used by links."""
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.hrefs=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag == 'a' and attrs.get('href'):
            self.hrefs.append(attrs['href'])

def redirect_html(target):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}"><title>Redirecting…</title></head><body><p>Redirecting to <a href="{target}">the current page</a>…</p><script>window.location.replace({target!r});</script></body></html>'''

def main():
    missing=[]
    for page in ROOT.rglob('*.html'):
        parser=LinkParser(); parser.feed(page.read_text(encoding='utf-8'))
        for href in parser.hrefs:
            if href.startswith(('#','http:','https:','mailto:','javascript:')): continue
            target=(page.parent/urlparse(href).path).resolve()
            if target.is_relative_to(ROOT.resolve()) and not target.exists():
                missing.append((target, page))

    created=0
    for target, source in sorted(set(missing), key=lambda pair: str(pair[0])):
        if target.exists(): continue
        relative=None
        if target.name in ('index.html','questions.html'):
            for candidate_name in ('practice.html','questions.html','chapter_analysis.html','index.html'):
                candidate=target.parent/candidate_name
                if candidate.exists():
                    relative=Path(candidate).relative_to(target.parent).as_posix(); break
            if relative is None and target.parent.name == 'chapters': relative='../index.html'
        elif target.name == 'chapter_analysis.html':
            slug=target.parent.name
            candidates=list(ROOT.rglob(f'{slug}/chapter_analysis.html'))
            if candidates:
                candidate=min(candidates, key=lambda p: len(p.parts))
                relative=Path(__import__('os').path.relpath(candidate, target.parent)).as_posix()
        elif target.name == '00_HIGHEST_WEIGHTAGE_PCM.html':
            candidate=ROOT/'00_HIGHEST_WEIGHTAGE_PCM.html'
            if candidate.exists(): relative=Path(__import__('os').path.relpath(candidate, target.parent)).as_posix()
        if relative:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(redirect_html(relative), encoding='utf-8')
            created += 1
    for practice in ROOT.rglob('clusters/*/practice.html'):
        alias = practice.parent / 'questions.html'
        if not alias.exists():
            alias.write_text(redirect_html('practice.html'), encoding='utf-8')
            created += 1
    for cross_subject_page in (ROOT / 'Physics' / 'chapters').rglob('chapter_analysis.html'):
        text = cross_subject_page.read_text(encoding='utf-8')
        updated = text
        for cluster_id in set(re.findall(r'href="clusters/(CHEM-[^"]+)/questions\.html"', text)):
            candidate = next(iter(ROOT.glob(f'05_PRACTICE_SETS/Chemistry/*/clusters/{cluster_id}/questions.html')), None)
            if candidate:
                rel = __import__('os').path.relpath(candidate, cross_subject_page.parent).replace(__import__('os').sep, '/')
                updated = updated.replace(f'href="clusters/{cluster_id}/questions.html"', f'href="{rel}"')
        if updated != text:
            cross_subject_page.write_text(updated, encoding='utf-8')
    print(f'Created {created} compatibility route redirects')

if __name__ == '__main__': main()
