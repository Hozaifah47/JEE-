#!/usr/bin/env python3
"""Correct legacy links that point to an existing root portal page with the wrong depth."""
import os
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
HREF_RE = re.compile(r'(?P<prefix>\b(?:href|src)=["\'])(?P<url>[^"\']+)(?P<suffix>["\'])')

def main():
    changed=0
    for page in ROOT.rglob('*.html'):
        original=page.read_text(encoding='utf-8')
        def repl(match):
            url=match.group('url')
            if url.startswith(('#','http:','https:','mailto:','javascript:','data:')): return match.group(0)
            parsed=urlparse(url)
            if parsed.query or parsed.fragment: return match.group(0)
            local=(page.parent/parsed.path).resolve()
            root_path=parsed.path.lstrip('/')
            while root_path.startswith('../'): root_path=root_path[3:]
            root_target=(ROOT/root_path).resolve()
            if not local.exists() and root_target.is_relative_to(ROOT.resolve()) and root_target.exists():
                corrected=os.path.relpath(root_target, page.parent).replace(os.sep,'/')
                return match.group('prefix')+corrected+match.group('suffix')
            return match.group(0)
        updated=HREF_RE.sub(repl, original)
        if updated != original:
            page.write_text(updated, encoding='utf-8'); changed+=1
    print(f'Normalized internal links in {changed} HTML pages')

if __name__=='__main__': main()
