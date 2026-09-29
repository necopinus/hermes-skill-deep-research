# Claims-Registry Pipeline

Full spec for Phases 3-7 of the deep-research workflow. **Supersedes
methodology.md's Phase 3-6 specifics where they conflict.** Phases 1-2 (scope,
plan/outline) and the Phase-8 packaging mechanics (lint, PDF, delivery) are
unchanged.

## Why this exists

The CWC citation audit (2026-09-28/29,
`~/research/Cryptographic_World_Computer_Research_20260927/redteam_report_part{A,B,C}.md`)
showed the old pipeline's failure mode: claims entered prose through uncontrolled
channels (subagent summaries treated as facts), and verification — when it
happened — came *after* prose existed. This pipeline makes the **claim** the
first-class artifact: claims are extracted from sources, adversarially checked by
independent agents, and only then drafted around. Verification lives in
**subagents** (cost control); the main context orchestrates and does not
re-fetch wholesale.

## Artifacts (per report, JSONL, committed to the vault)

- `sources.jsonl` — source registry, now with `provenance_tier` per entry.
- `claims.jsonl` — source-derived claims (schema:
  `schemas/claim.schema.json`). **The only source of factual premises
  for drafting.**
- `ERRATA.md` — standing dated log of post-publication corrections (what changed,
  why, where the error originated).

## Round 0 — Scope and outline (main context)

Phases 1-2 as before, plus: the outline is the **coverage contract**. Each
outline section gets *interest instructions* for round-2 agents — what kinds of
facts that section needs (dates, statuses, benchmarks, named actors, quotes,
positions).

## Round 1 — Source scouting (subagents)

Identify and summarize probable high-quality sources. Link spidering allowed;
**no deep reads** — quick summarization only. Output: entries in `sources.jsonl`
with `provenance_tier`:

| Tier | Examples | Rule |
| --- | --- | --- |
| primary | EIP/spec, EF blog, arXiv, project page/repo | load-bearing |
| official-tracker | forkcast, ethproofs, L2Beat, leanroadmap | load-bearing for status |
| secondary | The Block, CoinDesk, Galaxy, quality press | load-bearing with care |
| aggregator | Binance Square, CoinMarketCap Academy | locates primaries; NEVER load-bearing |
| transcription | vision-decoded figures (strawmap, post images) | partially verifiable; flag as such |

## Round 2 — Deep-read claim extraction (subagents, batches of 5-8 sources)

Batch size is capped by provider reality: fetch-heavy delegated runs have died
~20 minutes in (HTTP 401 mid-run). Keep batches small and single-topic until
that is resolved.

Each batch agent receives its source subset plus the interest instructions, deep-
reads, and appends **candidate** claims to `claims.jsonl`. Every claim
carries: `statement` (one checkable fact or implication), `kind`
(fact/implication/status/quote), `source_id` + `source_url`, **`evidence_quote`
(VERBATIM, mandatory — this field is the error-killer; "2 Euros" quoted verbatim
cannot drift into "2 ETH")**, `provenance_tier` (inherited), `fetched_at`.

`status`-kind claims use the source's own stage vocabulary (CFI/SFI per EIP-7723,
Draft/Review, devnet vs public testnet) and are re-verified at packaging.

## Round 3 — Adversarial claim checking (independent subagents)

For each candidate claim, a checker agent — **never the author** — FETCHES THE
PRIMARY SOURCE and compares the statement as written against it: units,
magnitudes, dates, proper nouns, stage labels, and quote fidelity (quoted text
verbatim or nothing). Verdicts:

- **confirmed** → lifecycle `validated`
- **refuted** → lifecycle `discarded` (notes required)
- **corrected** → original `discarded`; checker writes a corrected claim
  (`candidate`, round=3) which **must itself be checked by a new agent**.

Iterate to fixpoint. Checker-generated claims are never exempt from checking.
Aggregator-tier sources cannot validate a load-bearing claim: the checker must
locate the primary or discard.

## Coverage check (main context)

Before any drafting: map validated claims to outline sections.

- Section with factual work to do but no claims → targeted round-1/2 delta.
- Validated claims belonging to no section → outline gap or discard pile; decide
  explicitly.

**Omissions are found here, not by checkers** — adversarial checking validates
precision, never coverage. (The worst CWC finding was an absent fact, not a
wrong one.)

## Round 4 — Drafting (subagents)

The writer gets the outline plus the validated register. Three sentence types:

1. **Atomic factual assertions** (dates, numbers, statuses, "X happened") — MUST
   cite validated claims as `[C12]` (multi: `[C12, C7]`). No factual premise from
   outside the register.
2. **Reasoning** (comparison, weighing, mechanism) — free, no citation. This is
   the point of the report. Constraint is *grounding*, not citation: reasoning
   operates only over premises in the register.
3. **Characterizations smuggling checkable content** (proper noun + checkable
   predicate; "a restructuring completed in March") — treated as type 1.

"Analysis needs a premise the register lacks" → STOP; run a targeted round 1-3
delta; continue. **There is no escape valve from the write-claim / check-claim
loop.** Quoted spans in prose must be verbatim from a cited claim's
`evidence_quote` (no unattributed scare-quotes).

## Round 5 — Report red team (subagents)

Critics as before (structure, argument, prose quality) **plus a correctness
checker** verifying:

1. every `[Cn]` resolves to a `validated` claim;
2. every type-1/type-3 sentence carries claim citations (smuggled-premise lint);
3. `status`-kind claims re-verified against live sources if >48h since
   `fetched_at`;
4. facts appearing in both prose and tables are consistent (grep).

Fixes needing new facts loop back to rounds 1-3 — never prose-only edits.

## Round 6 — Mechanical conversion and packaging

1. **COMMIT** the claim-annotated draft plus registries (forensic checkpoint).
2. `python scripts/claims_convert.py --report draft.md --claims claims.jsonl --sources sources.jsonl`
   replaces `[Cn]` with `[Sn]` and regenerates the inline Bibliography from the
   registry. Then `scripts/resolve_citations.py`, markdownlint, and
   `verify_pdf_text.py` per quality-gates.md.
3. **COMMIT** again. The claim-annotated version stays in git history for
   forensics; later ERRATA entries can reference both versions.

## Mid-run scope changes

New source → round 2+3 for that source only. Scope/goal change → re-derive
interest instructions, generate delta claims only. Claims are never deleted —
only lifecycle-transitioned (`superseded` preserves the audit trail).

## Gaps

Sources that do not exist or cannot be reached go in the report's Limitations
section (lightweight analogue of a limitations register). Deleting an
unverifiable claim is the last resort — attempt harder sourcing first; deleting
a TRUE claim damages the report invisibly. Log any deletion in ERRATA.md.
