#!/usr/bin/env python3
"""
Structural validation of a claims register (claims-registry pipeline).

Checks, per entry:
  - required fields present; enums valid; claim_id shape (C<number>)
  - evidence_quote non-empty (verbatim evidence is mandatory)
  - lifecycle transitions coherent: validated/discarded/superseded claims have a
    `check` record; candidates have none; discarded claims have notes;
    corrected chains (superseded_by / supersedes / corrected_claim_id) resolve
    to existing claim ids
  - duplicate claim_id detection

Usage:
    python claims_check.py --claims claims.jsonl

Exit 0 if clean, 1 otherwise. Stdlib only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = ["claim_id", "statement", "kind", "source_id", "source_url",
            "evidence_quote", "provenance_tier", "fetched_at", "authored_by",
            "lifecycle"]
KINDS = {"fact", "implication", "status", "quote"}
TIERS = {"primary", "official-tracker", "secondary", "aggregator", "transcription"}
LIFECYCLES = {"candidate", "validated", "discarded", "superseded"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", "-c", required=True)
    args = ap.parse_args()

    errors = []
    claims = []
    for i, line in enumerate(Path(args.claims).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            claims.append(json.loads(line))
        except json.JSONDecodeError as e:
            errors.append(f"line {i}: invalid JSON: {e}")

    ids = [c.get("claim_id") for c in claims]
    for cid in ids:
        if ids.count(cid) > 1:
            errors.append(f"duplicate claim_id {cid}")
    idset = set(ids)

    for c in claims:
        cid = c.get("claim_id", "<no id>")
        for f in REQUIRED:
            if f not in c:
                errors.append(f"{cid}: missing required field '{f}'")
        if not re.fullmatch(r"C\d+", str(c.get("claim_id", ""))):
            errors.append(f"{cid}: claim_id must match ^C\\d+$")
        if c.get("kind") not in KINDS:
            errors.append(f"{cid}: bad kind {c.get('kind')!r}")
        if c.get("provenance_tier") not in TIERS:
            errors.append(f"{cid}: bad provenance_tier {c.get('provenance_tier')!r}")
        if not str(c.get("evidence_quote", "")).strip():
            errors.append(f"{cid}: evidence_quote must be non-empty (verbatim)")
        lc = c.get("lifecycle")
        if lc not in LIFECYCLES:
            errors.append(f"{cid}: bad lifecycle {lc!r}")
            continue
        chk = c.get("check")
        if lc == "candidate" and chk is not None:
            errors.append(f"{cid}: candidate claim must not have a check record")
        if lc in {"validated", "discarded", "superseded"}:
            if not chk:
                errors.append(f"{cid}: {lc} claim needs a check record")
            else:
                if chk.get("verdict") not in {"confirmed", "refuted", "corrected"}:
                    errors.append(f"{cid}: bad check verdict {chk.get('verdict')!r}")
                if lc == "discarded" and not str(chk.get("notes", "")).strip():
                    errors.append(f"{cid}: discarded claim needs check.notes")
        for fld in ("supersedes", "superseded_by"):
            v = c.get(fld)
            if v is not None and v not in idset:
                errors.append(f"{cid}: {fld} references unknown claim {v}")
        if chk and chk.get("corrected_claim_id") and chk["corrected_claim_id"] not in idset:
            errors.append(f"{cid}: check.corrected_claim_id references unknown claim")

    counts = {lc: sum(1 for c in claims if c.get("lifecycle") == lc) for lc in LIFECYCLES}
    print(f"claims: {len(claims)}  " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
