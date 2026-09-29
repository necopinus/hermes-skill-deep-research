#!/usr/bin/env python3
"""
Body-citation resolver: cross-checks [Sn] citations in a report's body against
(a) sources.jsonl registry and (b) the inline Bibliography/Sources section.

Why this exists: naive extraction with a bracket-anchored regex only captures
the FIRST id in multi-citation brackets like [S6, S7, S8] — dangling citations
and orphans hide in the tail positions. (Found the hard way, CWC audit 2026-09-29.)

Usage:
    python resolve_citations.py --report report.md [--sources sources.jsonl]

Exit 0 if clean in both directions, 1 otherwise.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def extract_body_ids(content: str) -> set:
    """All Sn ids inside any bracket group containing an S-id."""
    ids = set()
    for grp in re.findall(r"\[[^\]]*\bS\d+[^\]]*\]", content):
        ids.update(re.findall(r"S(\d+)", grp))
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", "-r", required=True)
    ap.add_argument("--sources", "-s", default=None,
                    help="sources.jsonl (default: alongside the report)")
    args = ap.parse_args()

    report = Path(args.report)
    content = report.read_text(encoding="utf-8")

    # body = everything before the bibliography section
    m = re.search(r"^## (Sources|Bibliography)", content, flags=re.M)
    body = content[: m.start()] if m else content
    bib = content[m.start():] if m else ""

    body_ids = extract_body_ids(body)

    registry_ids = set()
    registry_urls = set()
    spath = Path(args.sources) if args.sources else report.parent / "sources.jsonl"
    if spath.exists():
        for line in spath.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                row = json.loads(line)
                registry_ids.add(str(row.get("id") or row.get("source_id")).lstrip("S"))
                u = row.get("url") or row.get("raw_url") or row.get("canonical_locator")
                if u:
                    registry_urls.add(u.rstrip("/"))

    # inline bibliography entries under any '### Cited' subsection (or whole bib)
    cited_sec = bib
    cm = re.search(r"### Consulted", bib)
    if cm:
        cited_sec = bib[: cm.start()]
    inline_ids = set(re.findall(r"^- \[S(\d+)\]", cited_sec, flags=re.M))

    ok = True
    def show(label, ids):
        nonlocal ok
        ids = sorted(ids, key=int)
        print(f"{label}: {ids if ids else '[]'}")
        if ids:
            ok = False

    # Registry cross-check: if the registry uses S-numbered ids, compare ids
    # directly; otherwise (positional S-numbers from claims_convert) compare
    # inline-bibliography URLs against registry URLs instead.
    id_shaped = registry_ids and all(rid.isdigit() for rid in registry_ids)
    if id_shaped:
        show("cited in body, missing from registry", body_ids - registry_ids)
    elif registry_urls:
        bib_urls = set(u.rstrip("/") for u in re.findall(r"^- \[S\d+\].*?<([^>]+)>$", cited_sec, flags=re.M))
        show("inline Bibliography URLs missing from registry", bib_urls - registry_urls)
    if inline_ids:
        show("cited in body, missing from inline Bibliography", body_ids - inline_ids)
        show("inline Bibliography entries never cited in body", inline_ids - body_ids)
    print(f"distinct body citations: {len(body_ids)}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
