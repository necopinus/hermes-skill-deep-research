# Deep Research Methodology: 8-Phase Pipeline

## Overview

This document contains the detailed methodology for conducting deep research. The 8 phases
represent a comprehensive approach to gathering, verifying, and synthesizing information
from multiple sources.

**The claims flow is governed by [claims-pipeline.md](./claims-pipeline.md)** (source
scouting → deep-read claim extraction → adversarial claim checking → coverage check →
claim-grounded drafting → red team → mechanical conversion). This document provides the
phase-level mechanics those rounds build on: the search ladder, subagent architecture,
red-team audit axes, and packaging steps. Where the two disagree, claims-pipeline.md wins.

---

## Phase 1: SCOPE - Research Framing

**Objective:** Define research boundaries and success criteria

**Activities:**
1. Decompose the question into core components
2. Identify stakeholder perspectives
3. Define scope boundaries (what's in/out)
4. Establish success criteria
5. List key assumptions to validate

**Reasoning:** Take the time to explore multiple framings of the question before
committing to scope. Cheap at this phase, expensive later.

**Output:** Structured scope document with research boundaries

---

## Phase 2: PLAN - Strategy Formulation

**Objective:** Create an intelligent research roadmap

**Activities:**
1. Identify primary and secondary sources
2. Map knowledge dependencies (what must be understood first)
3. Create search query strategy with variants
4. Plan triangulation approach
5. Estimate time/effort per phase
6. Define quality gates

**Graph-of-Thoughts:** Branch into multiple potential research paths, then converge on
optimal strategy.

**Output:** Research plan with prioritized investigation paths

---

## Phase 3: RETRIEVE - Parallel Information Gathering

**Objective:** Systematically collect information from multiple sources using parallel
execution for maximum speed. In claims-pipeline terms this covers R1 (source scouting)
and R2 (deep-read claim extraction).

**CRITICAL: Execute ALL searches in parallel using a single message with multiple tool
calls.** Hermes runs independent tool calls in the same turn concurrently — batch them.

### Step 0: Get the current date

Before ANY searches, retrieve today's date: `date +%Y-%m-%d`
Use the returned year for all date-filtered queries and recency checks. Do NOT assume a
year from training data.

### The Search Ladder

Search proceeds as a ladder — start local, escalate outward only as needed. Each rung
feeds the next: note what you found, what gaps remain, and target the next rung at
those gaps.

#### Rung 1: Local wiki (`~/grimoire`) — always first

The shared wiki may already contain synthesized pages and raw sources on the topic.
Search it before touching the web:

```
mcp__obsidian_grimoire__search_notes(query="<concept>", limit=10)
mcp__obsidian_grimoire__search_notes(query="<alternate phrasing>", limit=10)
```

- Read the index (`index.md`) if the topic area is unfamiliar.
- Hits in `raw/` are immutable primary sources; hits elsewhere are synthesized pages.
- **Provenance rule:** when citing wiki content, trace it to the *original* source
  whenever possible. Raw sources carry `source_url:` in their frontmatter — cite THAT
  URL in the bibliography, not the wiki page. Synthesized wiki pages list their sources
  in frontmatter (`sources: [raw/articles/x.md]`) — follow them to the raw file, then
  to its `source_url:`. Only cite the wiki page itself when the claim is the wiki's own
  synthesis.
- Register grimoire-derived sources in `sources.jsonl` with their original URL and a
  `via: "grimoire"` note so the provenance chain is explicit.

#### Rung 2: Kagi MCP — primary web search

```
mcp__kagi__kagi_search_fetch(query="...", limit=10)
```

- Supports lenses (`lens_id`: 2 = Academic, 29 = News 360, 15 = Programming, etc.),
  domain filters (`include_domains`/`exclude_domains`), date filters
  (`after`/`before`/`time_relative`), and workflows (`search`, `news`, `videos`,
  `podcasts`, `images`).
- Use `extract_count: 1-3` on the most promising queries to inline full page content
  in the same call — saves a round trip.
- For deep-dives on a specific URL: `mcp__kagi__kagi_extract(url=...)`.

#### Rung 3: Exa via built-in `web_search` — semantic/neural search and gap-filling

```
web_search(query="<semantically rich description of ideal page>", limit=10)
```

- Exa is the configured `web.backend` (plugins/web/exa), so the native `web_search`
  and `web_extract` tools reach Exa directly — there is no `mcp__exa__*` server.
- Exa's strength is semantic retrieval: describe the *ideal page*, not keywords
  ("blog post comparing X and Y performance", not "X vs Y").
- Use alongside Kagi for coverage, and specifically to fill gaps Kagi left:
  alternative perspectives, academic treatments, older foundational sources.
- For full content of known URLs: `web_extract(urls=[...])` (batches several URLs
  in one call).

**Escalation guidance:** Rungs 1+2 are mandatory for Standard mode and above. Rung 3 is
mandatory for Deep/UltraDeep and recommended for Standard when Kagi coverage is thin or
the topic is conceptual/nuanced. Quick mode: Rung 1 + one Kagi batch.

### Query Decomposition Strategy

Before launching searches, decompose the research question into 5-10 independent search
angles:

1. **Core topic (semantic)** - Meaning-based exploration of main concept (Exa shines here)
2. **Technical details (keyword)** - Specific terms, APIs, implementations (Kagi)
3. **Recent developments (date-filtered)** - Last 12-18 months (Kagi `time_relative` or
   `after`, using the date from Step 0)
4. **Academic sources** - Papers, formal analysis (Kagi `lens_id: 2`, Exa via
   `web_search` with paper-oriented queries, or the arxiv skill)
5. **Alternative perspectives** - Competing approaches, criticisms
6. **Statistical/data sources** - Quantitative evidence, benchmarks
7. **Industry analysis** - Commercial applications, market trends
8. **Critical analysis/limitations** - Known problems, failure modes, edge cases

### Parallel Execution Protocol

**Step 1: Launch ALL searches concurrently (single message)**

Example (Standard mode, after grimoire sweep):

```
[Single message with multiple tool calls]
- mcp__kagi__kagi_search_fetch(query="quantum computing state of the art 2026", limit=10, extract_count=2)
- mcp__kagi__kagi_search_fetch(query="quantum computing limitations challenges", limit=10)
- mcp__kagi__kagi_search_fetch(query="quantum computing commercial applications", workflow="news", time_relative="month", limit=10)
- mcp__kagi__kagi_search_fetch(query="quantum error correction", lens_id="2", limit=10)
- web_search(query="technical deep-dive explaining why quantum error correction is hard", limit=10)
- web_search(query="critical analysis of quantum computing hype and failure modes", limit=10)
```

**Search execution:** The main context issues the search tool calls directly (they are
cheap, parallel, and stateless), but **result processing is delegated**: after the
parallel search batch returns, spawn a `delegate_task` subagent to:

1. Score sources with `source_evaluator.py`
2. Register sources with `citation_manager.py` — including a `provenance_tier`
   (primary / official-tracker / secondary / aggregator / transcription; see
   claims-pipeline.md R1)
3. Extract and persist evidence with `evidence_store.py`
4. Return a structured gap analysis: what was found, what's missing, what needs
   targeted follow-up

This keeps the main context free of raw search results and full-text extraction.

**Deep-read subagents (claims-pipeline R2):** For registered sources that merit full
reads, spawn `delegate_task` subagents in batches of 5-8 sources (batch cap is provider-
driven — fetch-heavy delegated runs have died ~20 minutes in). Each receives its source
subset plus the outline-derived interest instructions, and appends **candidate** claims
to `claims.jsonl` (structure: `schemas/claim.schema.json`). Subagents do NOT share your
conversation context — pass everything they need in the `context` field, and require
them to return URLs/paths you can verify yourself.

**Subagent claim output format:**

```json
{"statement": "one checkable fact or implication",
 "kind": "fact | implication | status | quote",
 "source_id": "...", "source_url": "https://...",
 "evidence_quote": "VERBATIM passage from the source (mandatory)",
 "fetched_at": "ISO-8601"}
```

The `evidence_quote` is the error-killer: a verbatim quote cannot silently drift the
way a paraphrase does (units, magnitudes, qualifiers).

**Step 3: Collect and organize results**

As results arrive:
1. Extract key passages with source metadata (title, URL, date, credibility)
2. Track information gaps that emerge
3. Follow promising tangents with additional targeted searches
4. Maintain source diversity (mix academic, industry, news, technical docs)
5. Monitor for quality threshold (see FFS pattern below)

### Evidence persistence (mandatory)

After each retrieval batch, persist evidence immediately:

```bash
# Register the source first (returns stable source_id)
python scripts/citation_manager.py register-source --json '{"raw_url": "...", "title": "..."}' --dir [folder]

# Then persist each evidence span from that source
python scripts/evidence_store.py add --json '{"source_id": "...", "quote": "exact text", "evidence_type": "direct_quote", "locator": "page 5"}' --dir [folder]
```

Evidence must not live only in model context — it must be persisted to `evidence.jsonl`
before synthesis begins. This survives context compaction and gives continuation
subagents and claim checking the full evidence trail.

### First Finish Search (FFS) Pattern

**Adaptive completion based on quality threshold:**

Proceed to Phase 4 when FIRST threshold reached:

- **Quick mode:** 10+ sources with avg credibility >60/100 OR 2 minutes elapsed
- **Standard mode:** 15+ sources with avg credibility >60/100 OR 5 minutes elapsed
- **Deep mode:** 25+ sources with avg credibility >70/100 OR 10 minutes elapsed
- **UltraDeep mode:** 30+ sources with avg credibility >75/100 OR 15 minutes elapsed

**Continue background searches:**

- If threshold reached early, continue remaining parallel searches in background
- Additional sources used in Phase 5 (SYNTHESIZE) for depth and diversity
- Allows fast progression without sacrificing thoroughness

### Quality Standards

**Source diversity requirements:**
- Minimum 3 source types (academic, industry, news, technical docs)
- Temporal diversity (mix of recent 12-18 months + foundational older sources)
- Perspective diversity (proponents + critics + neutral analysis)
- Geographic diversity (not just US sources)

**Credibility tracking:**
- Score each source 0-100 using source_evaluator.py
- Flag low-credibility sources (<40) for additional verification
- Prioritize high-credibility sources (>80) for core claims

**Techniques:**
- Grimoire search first (local, free, pre-vetted)
- Kagi MCP for web search (primary), Exa via `web_search` for semantic/gap-filling
- Kagi extract / `web_extract` for full page content
- `delegate_task` for parallel deep-dive subagents
- `execute_code` for computational analysis (when needed)

**Reproducible analysis rule:** Whenever the report derives numbers from data —
statistical summaries, growth-rate calculations, market-size estimates, cross-source
comparisons — write a short Python script to do the computation and save it to
`analysis/scripts/`, with input data in `analysis/data/`. Do NOT do arithmetic in your
head or in prose; the script IS the analysis. This makes every derived number
reproducible and auditable by the Phase 6 red team. Reserve model reasoning for
interpretation, narrative, and judgment calls — the things models are actually good for.

**Output:** Registered sources with provenance tiers, persisted evidence, candidate
claims in `claims.jsonl`, and a coverage map

---

## Phase 4: TRIANGULATE - Adversarial Claim Checking

**Objective:** Every candidate claim independently verified against its primary source
before it may appear in the report.

**This phase is governed by claims-pipeline.md R3** — the full contract (independent
checkers fetching primaries, lifecycle verdicts, checker-claims re-checked, fixpoint
iteration) lives there. The quality standards below are the checker's working criteria.

**Quality Standards (checker guidance):**

- Core claims should have 3+ independent sources where the topic allows; flag any
  single-source load-bearing claim.
- Flag contradictions between sources explicitly — note consensus vs. debate areas.
- Units, magnitudes, dates, proper nouns, stage labels, and quote fidelity are checked
  against the source as written, not against the claim's paraphrase.
- Note recency of information; `status`-kind claims use the source's own stage
  vocabulary.
- Aggregator-tier sources can never validate a load-bearing claim: locate the primary
  or discard.

**Output:** `claims.jsonl` with lifecycle verdicts — `validated` claims are the report's
only factual premises; `discarded`/`superseded` claims keep their audit trail

---

## Phase 4.5: OUTLINE REFINEMENT - Dynamic Evolution

**Objective:** Adapt research direction based on evidence discovered

**Problem Solved:** Prevents "locked-in" research when evidence points to different
conclusions or uncovers more important angles than initially planned.

**When to Execute:**
- **Standard/Deep/UltraDeep modes only** (Quick mode skips this)
- After Phase 4 (claim checking) completes, alongside the main-context coverage check
  (claims-pipeline.md)
- Before Phase 5 (SYNTHESIZE)

**Signals for adaptation (ANY triggers refinement):**

- Major findings contradict initial assumptions
- Evidence reveals more important angle than originally scoped
- Critical subtopic emerged that wasn't in original plan
- Original research question was too broad/narrow based on evidence
- Sources consistently discuss aspects not in initial outline

**Refinement actions:**

- Add sections for unexpected but important findings; demote/remove sections with
  insufficient evidence; reorder based on evidence strength
- Critical knowledge gaps → launch 2-3 targeted searches for newly identified angles
  (quick retrieval only; time-box 2-5 minutes), which re-enter the claims pipeline as
  delta claims (claims-pipeline.md "Mid-run scope changes")
- Document the adaptation rationale in the methodology appendix: what changed, why
  (evidence-driven reasons), what additional research was conducted

**Quality Standards:**

- Adaptation must be evidence-driven (cite specific sources that prompted change)
- No more than 50% outline restructuring (if more needed, scope was severely mis-scoped)
- Retain original research question core (don't drift into different topic entirely)
- New sections must have supporting claims already validated

**Anti-Pattern Warning:**

- DON'T adapt outline based on speculation or "what would be interesting"
- DON'T add sections without supporting evidence already in hand
- DON'T completely abandon original research question
- DO adapt when evidence clearly indicates better structure
- DO document rationale for changes
- DO stay within original topic scope

---

## Phase 5: SYNTHESIZE - Deep Analysis + Section Drafting

**Objective:** Connect insights, generate novel understanding, and draft report sections

**Execution: delegated per finding/section.** Synthesis is the most token-intensive
phase — delegate it aggressively. The main context coordinates; subagents draft.

**Architecture:**

1. **Main context** (control): read the refined outline + validated claims register,
   decide the finding list, and dispatch section-drafting subagents in batches
   (up to 3 concurrent).

2. **Section-drafting subagents** (`delegate_task` batch mode): each subagent
   receives the relevant claim subset (via `claims.jsonl` claim IDs, not full text),
   the outline section, the report style guide, and the target word count. It writes
   its section directly to the report file via
   `mcp__obsidian_research__write_note(mode="append")` and returns a 3-sentence
   abstract of what it wrote (for the main context's synthesis pass).

   ```
   delegate_task(tasks=[
     {"goal": "Draft Finding 1 ([title]) for [topic] research report, ~1500 words",
      "context": "Claims: ~/research/[folder]/claims.jsonl (use claim IDs [...]).
                  Append to report via obsidian-research MCP:
                  path=[folder]/research_report_[...].md, mode=append.
                  Drafting rules per claims-pipeline.md R4: atomic factual assertions
                  cite validated claims as [Cn] markers; reasoning/analysis is free
                  (no citation) but operates only over registered premises; quoted
                  spans verbatim from evidence_quote.
                  Style: prose-first >=80%, no placeholders.
                  If your section derives numbers from data (sums, averages, growth rates,
                  comparisons), write the computation as a script to analysis/scripts/
                  and save input data to analysis/data/ — do NOT do arithmetic in prose.
                  Return a 3-sentence abstract of the section."},
     {"goal": "Draft Finding 2 ...", "context": "..."},
     {"goal": "Draft Finding 3 ...", "context": "..."}
   ])
   ```

   "Analysis needs a premise the register lacks" → the subagent STOPS and reports the
   gap; the main context runs a targeted R1-R3 delta before drafting continues. There
   is no escape valve from the write-claim / check-claim loop.

3. **Main context** (synthesis): after all finding sections return, read the
   abstracts (not the full sections) and write the **Synthesis & Insights** section
   itself — this is the cross-cutting connective tissue and benefits from the main
   context's global view. Also writes Executive Summary last (after seeing all
   abstracts).

**Why this split:** finding sections are independent and parallelizable; the
synthesis section is inherently global and cheap (it works from abstracts). This
keeps ~80% of drafting tokens in subagents while preserving report coherence.

**Reasoning:** Subagents use extended reasoning on their claim subsets; the main
context uses it for cross-section pattern detection.

**Output:** All report sections written to the report file; main context holds
abstracts + synthesis section

---

## Phase 6: CRITIQUE - Quality Assurance + Independent Red Team

**Objective:** Rigorously evaluate research quality — structurally, numerically, and
adversarially — with fresh eyes that have no sunk cost in the research.

Phase 6 is **mandatory in Standard, Deep, and UltraDeep modes**. In Quick mode it is
skipped by default, but if the research is decision-critical the user should be asked
whether to include a critique pass (default suggestion: yes).

### 6A: Red Team — Independent Adversarial Audit (delegate_task, mandatory)

Spawn ONE independent red-team subagent via `delegate_task`. It must be a **fresh
context**: it receives the report path, `sources.jsonl`, `claims.jsonl` (the register),
`evidence.jsonl`, and (if present) `analysis/` — but NOT the research conversation,
the outline rationale, or the drafting subagents' abstracts. Its job is to attack the
report, not to appreciate it.

The red-team subagent audits four axes, in priority order:

**Axis 0 — Claims-pipeline integrity (the gating check).** Per claims-pipeline.md R5:
every `[Cn]` marker resolves to a `validated` claim; every atomic factual assertion
carries claim citations (smuggled-premise lint — watch for proper noun + checkable
predicate constructions); `status`-kind claims are re-verified against live sources
if >48h since `fetched_at`; facts appearing in both prose and tables are consistent.
A `[Cn]` resolving to a candidate/discarded/superseded claim is a critical finding.

**Axis 1 — Citation-usage integrity.** Existing validators (`verify_citations.py`)
catch *confabulated* references — sources that don't exist. This axis catches the
subtler failure: the source is **real** but is **used incorrectly**. For every
load-bearing citation (any claim attached to a number, a comparative claim, a date,
or a causal claim — sample at least 20 or all such claims if fewer), the subagent
opens the actual source text (from the claim's `evidence_quote` first, falling back
to re-fetching the URL) and checks:

- **Attribution mismatch:** the claim says X but the source says X-about-something-else
  (e.g., report claims "market grew 23%" citing a source whose 23% figure is about a
  *different segment*, *different year*, or *different geography* than the sentence
  implies).
- **Scope drift:** a figure from a narrow study generalized to a broad claim
  (n=47 survey → "industry-wide adoption is...").
- **Unit/magnitude errors:** billions vs millions, % vs percentage points, per-user vs
  total, revenue vs downloads, CAGR vs YoY.
- **Source-combining errors:** a number in the report was assembled by adding/averaging
  figures from 2+ sources that measure different things (incommensurate bases, different
  time windows, overlapping populations double-counted).
- **Cherry-pick direction:** the cited figure exists in the source but is the most
  favorable of several the source reports, and the report presents it as representative.
- **Quote distortion:** a direct quote trimmed so its meaning changes (qualifiers,
  negations, or uncertainty language dropped).

Every suspected misuse must cite the report line, the source's actual text, and a
verdict: `misuse` / `imprecise` / `ok`.

**Axis 2 — Numeric and analytical verification.** Every quantitative claim in the
report must survive recomputation:

- **Recompute all derived numbers.** If the report combines source figures (sums,
  averages, growth rates, market-size estimates, per-capita conversions), the subagent
  redoes the arithmetic from the cited source figures — by hand for one-liners, or by
  re-running the analysis script when the report has an `analysis/` directory (see
  "Analysis artifacts" in SKILL.md Output Contract). Discrepancies are reported with
  the recomputed value.
- **Sanity-check magnitudes.** Flag numbers that are arithmetically consistent but
  implausible against common reference points (e.g., a market size exceeding the GDP of
  the country it's measured in).
- **Date alignment.** Verify compared figures come from comparable time periods; flag
  "2024 vs 2026" comparisons presented without adjustment.
- **Statistics hygiene.** Flag percentages of percentages, survivorship-shaped samples,
  base rates omitted next to relative changes ("50% increase" from 2 to 3 users).

**Axis 3 — Reasoning audit.** Read the full report front-to-back and flag:

- Logical fallacies and unsupported inferential leaps (correlation→causation, anecdote→
  generalization, appeal-to-authority chains).
- Alternative explanations the report ignores for its central findings.
- Internal contradictions between sections (Executive Summary says X, Finding 4 says ¬X).
- Recommendation/evidence mismatch: recommendations stronger than the findings support.
- Missing-perspective check: who would dispute this framing, and is their case represented?

**Red-team output contract.** The subagent writes its audit to
`[report_dir]/redteam_report.md` with one section per axis, each finding formatted as:
`[SEVERITY: critical|major|minor] report location → issue → source/recomputed evidence →
suggested fix`. It returns only a 10-line summary (counts by severity, top 3 issues) to
the main context. **Critical findings block delivery** until resolved or explicitly
acknowledged in the report's Limitations section; major findings must be fixed or
acknowledged; minor findings are fixed at main-context discretion.

**Red-team loop (mandatory).** After the red-team report is written, the main context
fixes (or delegates fixes for) every `critical` and `major` finding — fixes needing new
facts loop back to R1-R3 of the claims pipeline, never prose-only edits — then re-runs
the red-team subagent on the updated report. This fix → re-audit cycle repeats until
either:

1. The red team returns zero `critical` and zero `major` findings, **or**
2. Three red-team passes have been completed (the initial pass plus two re-audits),
   whichever comes first.

Each re-audit is a fresh subagent (no memory of prior passes). If the third pass still
finds critical/major issues, those issues are documented in the report's Limitations
section and the loop terminates — do not keep iterating beyond three passes. The
`redteam_report.md` file is overwritten on each pass; the final version reflects the
last audit's findings.

### 6B: Persona-Based Critique (mandatory, all modes)

Simulate 2-3 critic personas relevant to the topic. Choose personas that match the
report's domain — the three defaults below are starting points, not mandates:

- "Skeptical Practitioner" — Would someone doing this daily trust these findings?
- "Adversarial Reviewer" — What would a peer reviewer reject?
- "Implementation Engineer" — Can these recommendations actually be executed?
- "Threat Modeler" — What attack surfaces or failure modes does this report ignore?
- "Domain Historian" — Has this been tried before? What happened?
- "Regulatory/Compliance Auditor" — What legal or policy constraints does this miss?

**Every persona critique is delegated to a context-restricted subagent**
(`delegate_task`). Each persona gets a fresh context containing only the report path
and the persona brief — NOT the research conversation, the outline rationale, the
drafting subagents' abstracts, or the red-team report. This mirrors scientific peer
review: the reviewer sees the paper, not the lab notebook. Personas complement the red
team: the red team checks *correctness*, personas check *credibility and usefulness*.

**Standard critique checklist (all modes — Phase 6 is mandatory):**
1. Review for logical consistency
2. Check citation completeness
3. Identify gaps or weaknesses
4. Assess balance and objectivity
5. Test alternative interpretations

**Critical Gap Loop-Back:**
If critique identifies a critical knowledge gap (not just a writing or accuracy issue),
run a targeted claims-pipeline delta (R1-R3) before proceeding to Phase 7. Time-box
to 3-5 minutes of scoping. This prevents publishing reports with known blind spots.
Citation misuses and numeric errors found by the red team are NOT loop-backs — they
are fixed in place in Phase 7.

**Output:** `redteam_report.md` persisted to the report directory + compact critique
summary in main context with severity counts

---

## Phase 7: REFINE - Iterative Improvement

**Objective:** Address gaps and strengthen weak areas

**Execution: delegated.** For each critique finding that requires new content,
spawn a targeted subagent (delta-retrieval for gaps, or section-rewrite for weak
arguments). The main context tracks which findings are resolved.

**Activities (subagents):**
1. Conduct additional research for gaps (delta-queries, persisted as in Phase 3)
2. Strengthen weak arguments (targeted section rewrites, appended via MCP)
3. Add missing perspectives
4. Resolve contradictions
5. Enhance clarity
6. Verify revised content

**Output:** Strengthened research with addressed deficiencies

---

## Phase 8: PACKAGE - Report Generation

**Objective:** Deliver professional, actionable research

**Activities:**
1. Structure report with clear hierarchy
2. Write executive summary
3. Develop detailed sections
4. Create visualizations (tables, diagrams)
5. **Commit the claim-annotated draft**, then run the mechanical conversion:
   `python scripts/claims_convert.py --report [draft] --claims claims.jsonl --sources sources.jsonl`
   replaces `[Cn]` markers with `[Sn]` citations and generates the inline bibliography.
   Run `scripts/resolve_citations.py` after; commit again (claims-pipeline.md R6)
6. Add methodology appendix
7. Prepare grimoire-ready artifacts (see report-assembly.md)
8. Generate HTML/PDF (PDF mandatory in gateway sessions — see Delivery Contract)
9. **Verify PDF text layer:** `python scripts/verify_pdf_text.py --pdf [path]` must PASS
10. Deliver in chat (never auto-open a browser)

**Output:** Complete research report ready for use

---

## Advanced Features

### Graph-of-Thoughts Reasoning

Rather than linear thinking, branch into multiple reasoning paths:
- Explore alternative framings in parallel
- Pursue tangential leads that might be relevant
- Merge insights from different branches
- Backtrack and revise as new information emerges

### Parallel Subagent Deployment

Use `delegate_task` to spawn subagents for:
- Parallel source retrieval
- Independent verification paths
- Competing hypothesis evaluation
- Specialized domain analysis

Subagent results are self-reports — anything load-bearing enters the report only as a
validated claim (see claims-pipeline.md), never directly from a subagent's summary.

### Adaptive Depth Control

Automatically adjust research depth based on:
- Information complexity
- Source availability
- Time constraints
- Confidence levels

### Citation Intelligence

Smart citation management:
- Track provenance of every claim (the claims register IS the provenance trail)
- Link to original sources (grimoire hits traced to their `source_url:`)
- Assess source credibility
- Handle conflicting sources
- Generate proper bibliographies (mechanical, via `claims_convert.py`)
