#!/usr/bin/env python3
"""
Mechanical claim-citation → source-citation conversion (claims pipeline, Phase 8).

Reads a claim-annotated report draft (with [C12] / [C12, C7] markers), the claims
register, and the source registry; produces the final markdown in which:
  - every [Cn] marker is replaced by [Sn] source citations (S-numbers assigned in
    order of first appearance in the document; multi-claim markers merge and
    de-duplicate their sources)
  - the '## Sources' (or '## Bibliography') section is regenerated from the
    registry under '### Cited in the report' (an existing '### Consulted'
    subsection is preserved)

Hard-fails (exit 1) if any marker references a missing, candidate, discarded, or
superseded claim, or a claim whose source_id is absent from the registry.
COMMIT the claim-annotated draft BEFORE running this; commit again after.

Usage:
    python claims_convert.py --report draft.md --claims claims.jsonl \
        --sources sources.jsonl [-o final.md]

Stdlib only.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def load_jsonl(p):
    rows = []
    for line in Path(p).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def source_key(s):
    return s.get("source_id") or s.get("id")


def source_url(s):
    return s.get("raw_url") or s.get("url") or s.get("canonical_locator", "")


def source_date(s):
    return s.get("year") or s.get("date") or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", "-r", required=True)
    ap.add_argument("--claims", "-c", required=True)
    ap.add_argument("--sources", "-s", required=True)
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    text = Path(args.report).read_text(encoding="utf-8")
    claims = {c["claim_id"]: c for c in load_jsonl(args.claims)}
    sources = {source_key(s): s for s in load_jsonl(args.sources)}

    errors = []
    s_numbers = {}
    order = []

    def s_for(src_id):
        if src_id not in s_numbers:
            s_numbers[src_id] = len(order) + 1
            order.append(src_id)
        return s_numbers[src_id]

    def convert_group(m):
        inner = m.group(1)
        cids = re.findall(r"C\d+", inner)
        srcs = []
        for cid in cids:
            c = claims.get(cid)
            if c is None:
                errors.append(f"{cid}: no such claim in register")
                continue
            if c["lifecycle"] != "validated":
                errors.append(f"{cid}: lifecycle is {c['lifecycle']} (must be validated)")
                continue
            sid = c["source_id"]
            if sid not in sources:
                errors.append(f"{cid}: source_id {sid!r} missing from registry")
                continue
            if sid not in srcs:
                srcs.append(sid)
        if not srcs:
            return m.group(0)
        return "[" + ", ".join(f"S{s_for(s)}" for s in srcs) + "]"

    bm = re.search(r"^## (Sources|Bibliography)\s*$", text, flags=re.M)
    body, bib_heading, consulted = text, "## Sources", ""
    if bm:
        body, bib_heading = text[: bm.start()], bm.group(0)
        bib_rest = text[bm.start():]
        cm = re.search(r"^### Consulted.*$", bib_rest, flags=re.M)
        if cm:
            consulted = bib_rest[cm.start():]

    converted = re.sub(r"\[((?:\s*C\d+\s*,?)+)\]", convert_group, body)

    if errors:
        print("FAIL — unresolved claim markers:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    entries = []
    for sid in order:
        s = sources[sid]
        n = s_numbers[sid]
        title = s.get("title", sid)
        date = source_date(s)
        url = source_url(s)
        date_part = f" {date}." if date else ""
        entries.append(f"- [S{n}] {title}.{date_part} <{url}>")
    new_bib = (bib_heading + "\n\n### Cited in the report\n\n" + "\n".join(entries)
               + ("\n\n" + consulted.rstrip() + "\n" if consulted else "\n"))

    out = converted.rstrip() + "\n\n" + new_bib
    out_path = Path(args.output) if args.output else Path(args.report)
    out_path.write_text(out, encoding="utf-8")
    print(f"{len(order)} sources in bibliography -> {out_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
