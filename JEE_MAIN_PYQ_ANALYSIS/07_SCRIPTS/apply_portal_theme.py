#!/usr/bin/env python3
"""Add the shared persistent theme toggle to legacy portal HTML pages.

The main practice generator emits this itself. This compatibility pass covers
older analysis/report pages produced by the other generators.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "data-jee-theme-toggle"
CSS = """
<style data-jee-theme-toggle>
html[data-theme="dark"] { color-scheme: dark; }
html[data-theme="dark"] body { background:#0d0d11 !important; color:#f5f7fb !important; }
html[data-theme="dark"] body * { border-color:#27272e; }
html[data-theme="dark"] .container, html[data-theme="dark"] .page-wrapper,
html[data-theme="dark"] .card, html[data-theme="dark"] .question-block,
html[data-theme="dark"] .question-card, html[data-theme="dark"] .cluster-card,
html[data-theme="dark"] .stat-card, html[data-theme="dark"] .subject-card,
html[data-theme="dark"] details, html[data-theme="dark"] .tab-panel,
html[data-theme="dark"] table, html[data-theme="dark"] .table-wrap {
  background:#18181c !important; color:#f5f7fb !important;
}
html[data-theme="dark"] a { color:#8aaeff !important; }
html[data-theme="dark"] h1, html[data-theme="dark"] h2, html[data-theme="dark"] h3,
html[data-theme="dark"] h4, html[data-theme="dark"] .cluster-name { color:#f5f7fb !important; }
html[data-theme="dark"] td, html[data-theme="dark"] th { border-color:#27272e !important; }
.jee-theme-toggle { position:fixed; right:18px; top:14px; z-index:10000; border:1px solid rgba(255,255,255,.35); border-radius:999px; padding:7px 12px; background:#18181c; color:#fff; cursor:pointer; font:600 12px system-ui; box-shadow:0 4px 14px rgba(0,0,0,.25); }
</style>
"""
JS = """
<script data-jee-theme-toggle>
(function(){
  var root=document.documentElement;
  var button=document.createElement('button');
  button.className='jee-theme-toggle'; button.type='button';
  button.setAttribute('aria-label','Toggle dark mode');
  function saved(){try{return localStorage.getItem('jee-theme')}catch(e){return null}}
  function store(v){try{localStorage.setItem('jee-theme',v)}catch(e){}}
  function apply(v){root.dataset.theme=v;button.textContent=v==='dark'?'☀ Light mode':'🌙 Dark mode';store(v)}
  apply(saved()==='light'?'light':'dark');
  button.onclick=function(){apply(root.dataset.theme==='dark'?'light':'dark')};
  document.addEventListener('DOMContentLoaded',function(){document.body.appendChild(button)});
})();
</script>
"""

def main():
    changed = 0
    for path in ROOT.rglob('*.html'):
        text = path.read_text(encoding='utf-8')
        if 'function initTheme()' in text and MARKER in text:
            text = text.replace(CSS + JS, '', 1)
            path.write_text(text, encoding='utf-8')
            changed += 1
            continue
        if MARKER in text:
            continue
        if '</head>' not in text.lower():
            continue
        text = text.replace('</head>', CSS + JS + '</head>', 1)
        path.write_text(text, encoding='utf-8')
        changed += 1
    print(f'Added compatibility theme toggle to {changed} legacy HTML pages')

if __name__ == '__main__':
    main()
