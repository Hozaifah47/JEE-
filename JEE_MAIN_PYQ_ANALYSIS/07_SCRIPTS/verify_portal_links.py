#!/usr/bin/env python3
"""Check local links and referenced image assets in generated JEE portals."""
from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ("Physics", "Chemistry", "Mathematics", "04_MASTER_REPORTS", "05_PRACTICE_SETS")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".bmp"}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        for key in ("id", "name"):
            if attrs.get(key):
                self.ids.add(attrs[key])
        for key in ("href", "src", "poster", "data-src"):
            value = attrs.get(key)
            if value:
                self.refs.append((key, value.strip()))


def collect_html(scope: Path) -> list[Path]:
    if scope.is_file() and scope.suffix.lower() == ".html":
        return [scope]
    return sorted(p for p in scope.rglob("*.html") if p.is_file()) if scope.exists() else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="print machine-readable report")
    ap.add_argument("scopes", nargs="*", default=list(SCOPES), help="paths relative to project root")
    args = ap.parse_args()
    pages = [p for s in args.scopes for p in collect_html(ROOT / s)]
    parsed: dict[Path, LinkParser] = {}
    for page in pages:
        parser = LinkParser()
        try:
            parser.feed(page.read_text(encoding="utf-8", errors="replace"))
            parsed[page.resolve()] = parser
        except OSError:
            continue

    broken: list[dict[str, str]] = []
    missing_images: list[dict[str, str]] = []
    external = ("http", "https", "mailto", "tel", "data", "javascript", "blob")
    for page, parser in parsed.items():
        for kind, raw in parser.refs:
            if not raw or raw == "#":
                continue
            if raw.startswith("#"):
                fragment = unquote(raw[1:])
                if fragment and fragment not in parser.ids:
                    broken.append({"page": str(page.relative_to(ROOT)), "target": raw, "kind": kind})
                continue
            url = urlsplit(raw)
            if url.scheme.lower() in external or url.netloc:
                continue
            target = (page.parent / unquote(url.path)).resolve() if url.path else page
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                entry = {"page": str(page.relative_to(ROOT)), "target": raw, "kind": kind}
                (missing_images if kind in {"src", "poster", "data-src"} and Path(url.path).suffix.lower() in IMAGE_SUFFIXES else broken).append(entry)
                continue
            if url.fragment and target.suffix.lower() == ".html":
                target_parser = parsed.get(target)
                if target_parser is None:
                    target_parser = LinkParser()
                    try:
                        target_parser.feed(target.read_text(encoding="utf-8", errors="replace"))
                    except OSError:
                        target_parser = None
                    if target_parser is not None:
                        parsed[target] = target_parser
                if target_parser is not None and unquote(url.fragment) not in target_parser.ids:
                    broken.append({"page": str(page.relative_to(ROOT)), "target": raw, "kind": kind})

    report = {"html_pages": len(pages), "broken_internal_links": broken, "missing_image_assets": missing_images}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"HTML pages checked: {len(pages)}")
        print(f"Broken internal links: {len(broken)}")
        for item in broken[:100]:
            print(f"  {item['page']} -> {item['target']} [{item['kind']}]")
        print(f"Missing image assets: {len(missing_images)}")
        for item in missing_images[:100]:
            print(f"  {item['page']} -> {item['target']} [{item['kind']}]")
    return 1 if broken or missing_images else 0


if __name__ == "__main__":
    raise SystemExit(main())
