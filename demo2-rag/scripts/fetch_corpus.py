"""Freeze the approved English Backrooms article allowlist as Markdown.

Python 3.12; requests==2.34.2, beautifulsoup4==4.15.0, markdownify==1.2.0.
Run from any directory. Existing raw HTML is reused unless --refresh is given.
Only the explicit candidates below are fetched; this is not a recursive crawler.
Text is CC BY-SA 3.0; image/media files are deliberately excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

BASE_URL = "https://backrooms-wiki.wikidot.com/"
LICENSE = "CC BY-SA 3.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/3.0/"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CANDIDATES = {
    "level": [f"level-{i}" for i in range(30)],
    "entity": [f"entity-{i}" for i in range(3, 26)],
    "object": [f"object-{i}" for i in range(1, 21)],
}
TARGETS = {"level": 25, "entity": 15, "object": 10}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def convert_article(html: str, source_url: str) -> tuple[str, dict]:
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.select_one("#page-title")
    content = soup.select_one("#page-content")
    if not title_node or not content:
        raise ValueError("Not a Wikidot article with a title and article body")
    title = title_node.get_text(" ", strip=True)
    if "page does not exist" in content.get_text(" ", strip=True).lower():
        raise ValueError("Source page does not exist")

    license_box = content.select_one(".licensebox")
    citation = ""
    if license_box:
        citation_node = license_box.select_one(".list-pages-item blockquote")
        citation = (citation_node or license_box).get_text(" ", strip=True)
    authors = []
    match = re.search(r'\bby (.+?), from the\b', citation)
    if match:
        authors = [part.strip().strip(",") for part in
                   re.split(r",\s*(?:and\s+)?|\s+and\s+", match.group(1)) if part.strip()]
    info_box = content.select_one("#u-infobox")
    credit_text = info_box.get_text(" ", strip=True) if info_box else ""
    if not authors and info_box:
        # Keep explicitly credited usernames; no fabricated author identity.
        authors = list(dict.fromkeys(n.get_text(" ", strip=True)
                                     for n in info_box.select(".printuser")))
    page_info = soup.select_one("#page-info")
    revision_text = page_info.get_text(" ", strip=True) if page_info else ""
    revision = re.search(r"page revision:\s*(\d+)", revision_text)

    # Preserve the names of tabbed sections, including initially hidden content.
    for tabset in content.select(".yui-navset"):
        labels = [n.get_text(" ", strip=True) for n in tabset.select(".yui-nav > li")]
        panels = tabset.select(".yui-content > div")
        for label, panel in zip(labels, panels):
            heading = soup.new_tag("h3")
            heading.string = label
            panel.insert(0, heading)
        for nav in tabset.select(".yui-nav"):
            nav.decompose()

    # Some wiki themes expose their stylesheet as a syntax-highlighted <pre>.
    # It is site machinery, not a fictional source document or narrative code.
    for block in content.find_all("pre"):
        if re.search(r":root\s*\{|--theme-(?:base|id)|@import\s+url", block.get_text()):
            block.decompose()
    # Unresolved component parameters are artifacts, not survival instructions.
    for row in content.find_all("li"):
        if re.fullmatch(r"\s*\{\$[\w-]+\}\s*\.?\s*", row.get_text(" ", strip=True)):
            row.decompose()

    # Remove site machinery, repeated navigation, credits and separately licensed media.
    selectors = [
        "script", "style", "link", "iframe", "video", "audio", "svg", "canvas",
        "img", "picture", "source", "form", "button", ".licensebox", "#u-infobox",
        ".creditRate", ".page-rate-widget-box", ".translations", ".preview",
        ".footer-wikiwalk-nav", ".page-tags", ".content-separator", ".scp-image-block",
        ".scp-image-caption", ".image-container", ".collapsible-block-folded",
        ".collapsible-block-unfolded-link", ".footnote-footer", ".printuser.avatarhover",
    ]
    for node in content.select(", ".join(selectors)):
        node.decompose()
    for anchor in content.find_all("a"):
        href = anchor.get("href", "")
        if href.startswith(("javascript:", "data:")) or href in ("#", "###"):
            anchor.unwrap()
        elif href:
            anchor["href"] = urljoin(source_url, href)
    markdown = markdownify(str(content), heading_style="ATX", bullets="-",
                           strip=["img", "script", "style"], escape_underscores=False)
    markdown = re.sub(r"\n[ \t]+\n", "\n\n", markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    markdown = re.sub(r"\{\$[\w-]+\}", "", markdown)
    if len(markdown) < 500:
        raise ValueError(f"Suspiciously short article: {len(markdown)} characters")
    markdown = f"# {title}\n\n{markdown}\n"
    return markdown, {
        "title": title,
        "authors": authors,
        "citation": citation,
        "credit_text": credit_text,
        "revision": revision.group(1) if revision else None,
        "revision_text": revision_text,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Fetch fresh snapshots")
    parser.add_argument("--offline", action="store_true", help="Use raw cached HTML only")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Minimum pause between network requests, seconds")
    args = parser.parse_args()
    if args.offline and args.refresh:
        parser.error("--offline and --refresh are mutually exclusive")
    raw_dir, documents_dir = DATA_DIR / "raw", DATA_DIR / "documents"
    raw_dir.mkdir(parents=True, exist_ok=True)
    documents_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "University-RAG-Classroom-Corpus/1.0 (bounded article snapshot)"
    records, skipped = [], []
    for kind, candidates in CANDIDATES.items():
        accepted = 0
        for article_id in candidates:
            if accepted >= TARGETS[kind]:
                break
            source_url = urljoin(BASE_URL, article_id)
            raw_path, metadata_path = raw_dir / f"{article_id}.html", raw_dir / f"{article_id}.json"
            try:
                if args.refresh or not raw_path.exists():
                    if args.offline:
                        raise ValueError("No cached HTML available")
                    time.sleep(max(0.5, args.delay))
                    response = session.get(source_url, timeout=(10, 40))
                    response.raise_for_status()
                    response.encoding = "utf-8"
                    raw_path.write_text(response.text, encoding="utf-8")
                    metadata_path.write_text(json.dumps({"source_url": response.url,
                                                         "fetched_at": utc_now()}, indent=2) + "\n")
                fetched = json.loads(metadata_path.read_text()) if metadata_path.exists() else {
                    "source_url": source_url,
                    "fetched_at": datetime.fromtimestamp(raw_path.stat().st_mtime, timezone.utc).isoformat(),
                }
                markdown, metadata = convert_article(raw_path.read_text(encoding="utf-8"), source_url)
                path = documents_dir / f"{article_id}.md"
                path.write_text(markdown, encoding="utf-8")
                records.append({"id": article_id, "kind": kind,
                                "path": f"documents/{article_id}.md", "source_url": source_url,
                                "license": LICENSE, "license_url": LICENSE_URL,
                                "fetched_at": fetched["fetched_at"],
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), **metadata})
                accepted += 1
                print(f"{len(records):02d} {kind}: {article_id} — {metadata['title']}", flush=True)
            except (requests.RequestException, ValueError, OSError) as exc:
                skipped.append({"id": article_id, "source_url": source_url, "reason": str(exc)})
                print(f"SKIP {article_id}: {exc}", flush=True)
        if accepted < TARGETS[kind]:
            raise SystemExit(f"Only {accepted}/{TARGETS[kind]} {kind} articles acquired; no complete manifest written")
    manifest = {"schema_version": 1, "source_site": BASE_URL, "license": LICENSE,
                "license_url": LICENSE_URL, "fetched_at": utc_now(), "documents": records}
    (DATA_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    (DATA_DIR / "acquisition_report.json").write_text(json.dumps({"skipped": skipped}, indent=2) + "\n")
    attribution = ["# Backrooms classroom corpus — attribution", "",
                   "This is a curated snapshot of 50 English Backrooms Wiki articles: 25 levels, 15 entities and 10 objects.",
                   "", f"Article text: [{LICENSE}]({LICENSE_URL}). Source: [{BASE_URL}]({BASE_URL}).",
                   "", "Changes: article HTML converted to Markdown; navigation, credits, ratings, stylesheet code, unresolved template placeholders and media removed from retrieval text. Headings, prose, lists, links and tables retained where present. Media is excluded and not relicensed.",
                   "", "Individual citations and author credits follow. Full available credit-box text, snapshot times, page revisions and file hashes are preserved in manifest.json.", ""]
    for record in records:
        attribution.extend([f"## {record['title']}", "",
                            record["citation"] or f"Source: {record['source_url']}. Authors/credits: {', '.join(record['authors']) or 'see linked source and preserved credit_text in manifest.json'}.",
                            "", f"Source: {record['source_url']}",
                            f"Snapshot: {record['fetched_at']}; page revision: {record['revision'] or 'not exposed'}.", ""])
    (DATA_DIR / "ATTRIBUTION.md").write_text("\n".join(attribution), encoding="utf-8")
    print("Saved 50 Markdown articles, manifest.json and ATTRIBUTION.md.", flush=True)


if __name__ == "__main__":
    main()
