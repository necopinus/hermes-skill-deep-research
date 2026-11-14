---
name: deep-research
description: "Use for multi-source research and citation-tracked reports."
---

# Deep Research

## Core Purpose

Deliver citation-tracked research reports through a structured pipeline with evidence
persistence, source identity management, claim-level verification, and progressive
context management.

**Before beginning a run:** `cd ~/workspace/research && git pull` to ensure the vault is up-to-date.

**Skill maintenance (REQUIRED):** Whenever you change any file in this skill repository—including `SKILL.md`, references, templates, scripts, or tests—run the relevant checks, commit the change, and push it to `origin main` before finishing the task. Review the staged diff and verify that the remote branch matches the new local commit; never leave a skill improvement only in the local working tree. Preserve unrelated pre-existing dirty work unless the user explicitly asks to include it.

**Autonomy Principle:** Operate independently. Infer assumptions from context. Only stop
for critical errors or incomprehensible queries. Surface high-materiality assumptions
explicitly in the Introduction and Methodology rather than silently defaulting.

---

## Decision Tree

```
Request Analysis
+-- Simple lookup? --> STOP: Use web_search or Kagi directly
+-- Debugging? --> STOP: Use standard tools
+-- Complex analysis needed? --> CONTINUE

Mode Selection
+-- Initial exploration --> quick (3 phases, 2-5 min)
|   +-- Decision-critical? --> ASK: include Phase 6 critique? (default: yes)
|   +-- Otherwise --> skip Phase 6
+-- Standard research --> standard (7 phases, 5-15 min) [DEFAULT]
+-- Critical decision --> deep (8 phases, 10-20 min)
+-- Comprehensive review --> ultradeep (8+ phases, 20-45 min)
```

**Default assumptions:** Technical query = technical audience. Comparison = balanced
perspective. Trend = recent 1-2 years.

---

## Workflow Overview

| Phase | Name | Quick | Std | Deep | Ultra | Execution Mode |
|-------|------|-------|-----|------|-------|----------------|
| 1 | SCOPE | Y | Y | Y | Y | **Main context** (control) |
| 2 | PLAN | - | Y | Y | Y | **Main context** (control) |
| 3 | RETRIEVE | Y | Y | Y | Y | **delegate_task** — claims pipeline R1-R2: source scouts, then deep-read claim extraction into `claims.jsonl` |
| 4 | TRIANGULATE | - | Y | Y | Y | **delegate_task** — claims pipeline R3: adversarial claim checking (independent agents fetch primaries; iterate to fixpoint) |
| 4.5 | OUTLINE REFINEMENT | - | Y | Y | Y | **Main context** — coverage check: validated claims mapped to outline; targeted deltas |
| 5 | SYNTHESIZE | - | Y | Y | Y | **delegate_task** — drafting from validated claims only (`[Cn]` markers; analysis free) |
| 6 | CRITIQUE | † | Y | Y | Y | **delegate_task** — report red team + correctness checker (citation resolution, smuggled premises, status re-verify) |
| 7 | REFINE | - | Y | Y | Y | **delegate_task** — fixes; new facts loop back to R1-R3, never prose-only edits |
| 8 | PACKAGE | Y | Y | Y | Y | **Mixed** — commit claim-annotated draft → mechanical conversion (`claims_convert.py`) → standard gates → commit |

**Claims pipeline:** Phases 3-7 follow the claims-registry pipeline — full spec in
[claims-pipeline.md](./reference/claims-pipeline.md). It governs the claims flow;
methodology.md provides the phase-level mechanics it builds on.

Do not register the report's cross-source thesis, taxonomy, or preferred framing as a
validated primary-source claim. Source-derived implications must remain tied to their
evidence; synthesis belongs in report reasoning and cites underlying factual claims,
not a self-certifying claim created to endorse the synthesis.

**Delegation principle:** Phases 3-8 are delegated to subagents whenever they involve
multi-step generation, analysis, or drafting. The main context handles only:
- Research framing (Phase 1) and strategy (Phase 2)
- Final validation and delivery decisions
- Cross-phase coordination and gap-filling when subagents return incomplete work

When parallel section writers work on one report, assign separate files under `draft_sections/`
and concatenate them in outline order before review. Concurrent appends to the report can reorder
sections or overwrite one another, and red-team reviewers need one stable report path.

For multi-report projects delivered sequentially as autonomous builder processes
(`hermes -z`, one per report, orchestrator verifies and commits between builds), see
subagent-orchestration's "Process-level nesting" section — briefs use that skill's
`templates/builder_brief.md`.

**† Quick mode Phase 6:** Skipped by default. If the research is decision-critical,
ask the user whether to include a critique pass (default suggestion: yes).

**Note:** Phases 3-5 operate as an evidence loop per section (retrieve -> evidence
store -> refine outline -> draft -> verify claims -> delta-retrieve if needed), not as
strict sequential gates. Each loop iteration is a candidate for delegation.

---

## Search Ladder (summary)

1. **`~/workspace/grimoire`** — `mcp__obsidian_grimoire__search_notes` first, always. Trace hits
   to their original `source_url:` for citations.
2. **Kagi MCP** — `mcp__kagi__kagi_search_fetch` is the primary web search.
3. **Exa (built-in `web_search`)** — semantic search and gap-filling. Exa is the
   configured `web.backend`, so the native `web_search` / `web_extract` tools ARE
   Exa — no MCP server involved.

Details in [methodology.md](./reference/methodology.md) Phase 3.

---

## Provided local sources (decks, standards, documents)

When the user supplies source material (training decks, licensed standards, PDFs), the
run is driven from those documents and web research only fills depth:

1. **Inventory first, then scope.** Survey the corpus before asking anything — per-file
   text/notes richness tells you where the substance is (thin slide text or empty speaker
   notes means diagrams carry the content and a vision pass is needed). Batch every
   scoping question into ONE `clarify` call, then begin.
2. **Extract mechanically** into `<report_dir>/source_material/` with
   `scripts/extract_office_text.py` (pptx: slide text + per-slide-mapped speaker notes;
   docx: paragraphs; pdf: `pdftotext -layout`; `--images` adds per-slide image copies,
   a full media dump, and a manifest for vision passes). Its output is heading-safe
   (extracted text cannot fake setext/ATX headings). Don't hand-extract, and don't make
   sub-agents re-extract from the binaries.
3. **Licensed or confidential provided material stays on-disk only**: add
   `source_material/` to `.git/info/exclude` (repo-local — never edit the tracked
   `.gitignore`) before committing; the vault remote is third-party. Default quote
   policy for licensed texts: brief verbatim quotes with clause/locator refs — confirm
   the user's sharing scope when it matters.
4. **Cite provided documents as primary sources** (e.g. `(Deck name, slide N)`); the
   claims registry covers EXTERNAL corroboration, not content derived from the provided
   documents themselves.
5. **Training-prep variant** (a report whose job is to teach a supplied course): the
   course's own agenda is the report skeleton and the chapters follow its arc; expand
   what the slides assume; include exactly the presenter extras the user picks from one
   batched question (exercise walkthroughs with worked answers are the default bet).

---

## Execution

**On invocation, load relevant reference files:**

1. **Phase 1-2 (scope/plan):** Load [methodology.md](./reference/methodology.md). For security-incident reconstruction, novelty claims, or cross-domain attack comparisons, also load [security-incident-analysis.md](./references/security-incident-analysis.md).
2. **Phases 3-7 (claims pipeline):** Load [claims-pipeline.md](./reference/claims-pipeline.md) — source scouting, deep-read claim extraction, adversarial claim checking, claim-grounded drafting. For parallel-batch aggregation, clause-level checking, and raw protocol-data verification, also load [claims-registry-operations.md](./references/claims-registry-operations.md).
1. **Phase 8 (Report):** Load [report-assembly.md](./reference/report-assembly.md) for progressive generation. Section order: Methodology appendix and Report Metadata BEFORE '## Bibliography' — `claims_convert.py` replaces everything from the Bibliography heading to EOF (only a '### Consulted' subsection survives), so the template's bibliography-first order silently deletes the appendix at conversion.
4. **HTML/PDF output:** Load [html-generation.md](./reference/html-generation.md)
5. **Quality checks:** Load [quality-gates.md](./reference/quality-gates.md)
6. **Long reports (>18K words):** Load [continuation.md](./reference/continuation.md)

**Templates:**
- Report structure: [report_template.md](./templates/report_template.md)
- HTML styling: [mckinsey_report_template.html](./templates/mckinsey_report_template.html)

**Scripts:**
- `python scripts/extract_office_text.py SRC [SRC ...] --out DIR [--images]` — extract
  provided Office/PDF documents into heading-safe `source_material/` markdown (pptx:
  slide text + per-slide-mapped speaker notes; docx: paragraphs; pdf: `pdftotext
  -layout`); `--images` adds per-slide image copies, a full media dump, and a manifest
- `python scripts/validate_report.py --report [path]`
- `python scripts/verify_citations.py --report [path]` — checks bibliography URLs and metadata, including post-conversion `- [Sn]` entries; `resolve_citations.py` remains the substantive body↔registry↔bibliography identity gate
- `python scripts/verify_pdf_text.py --pdf [path]` (mandatory when a PDF is generated)
- `python scripts/claims_check.py --claims [claims.jsonl]` — structural validation of the claims register (mandatory after R2/R3)
- `python scripts/claims_convert.py --report [draft.md] --claims [claims.jsonl] --sources [sources.jsonl]` — mechanical `[Cn]` → `[Sn]` conversion + inline Bibliography generation (Phase 8, after the pre-conversion commit); then collapse repeated adjacent citations for the same source (`[S1][S1]` → `[S1]`) without changing multi-source groups, and rerun `resolve_citations.py`
- For Pandoc→HTML→PDF, use `pagetitle` for the HTML document title when the Markdown already has an H1; supplying `title` also emits a visible metadata title and duplicates the report heading. Inspect both a table page and the final bibliography page, not just the text layer. For dense comparison tables, use `table-layout: fixed` and `overflow-wrap: anywhere` on cells so adjacent citation markers and long URLs wrap within their columns
- Run `verify_html.py` only for the McKinsey HTML structure it checks, not generic Pandoc standalone HTML used solely as a WeasyPrint intermediate; verify the PDF instead and remove the intermediate when HTML is not a deliverable
- `python scripts/resolve_citations.py --report [report.md]` — body↔registry↔inline-bibliography cross-check (after conversion)
- `python scripts/md_to_html.py [markdown_path]`
- `python scripts/citation_manager.py` — source registration and citation numbering
- `python scripts/evidence_store.py` — evidence persistence (add/query)
- `python scripts/source_evaluator.py` — source credibility scoring
- `python scripts/verify_html.py --html [path] --md [path]` — HTML verification

**Schemas** (structural contracts for the pipeline's JSONL/JSON files):
- `schemas/source.schema.json` — `sources.jsonl` entries
- `schemas/claim.schema.json` — `claims.jsonl` entries: the source-derived claims register (verbatim evidence quotes, lifecycle states)
- `schemas/evidence.schema.json` — `evidence.jsonl` entries
- `schemas/run_manifest.schema.json` — `run_manifest.json`

---

## Output Contract

**Required sections:**
- Executive Summary (200-400 words)
- Introduction (scope, methodology, assumptions)
- Main Analysis (4-8 findings, 600-2,000 words each, cited)
- Synthesis & Insights (patterns, implications)
- Limitations & Caveats
- Recommendations
- Bibliography (COMPLETE - every citation, no placeholders). The bibliography lives INLINE in the report itself (full titles + URLs, per the template's `## Bibliography` section): the report must be self-contained and shareable as a single file. Never satisfy this section by pointing to `bibliography.md` or any other external file.
- Methodology Appendix

**Output files (all to `~/workspace/research/[Topic]_Research_[YYYYMMDD]/`):**
- Markdown report (primary source of truth) — written via `mcp__obsidian_research__write_note`
- `bibliography.md` — standalone ingestion map for future wiki integration (MCP-written). This is a DERIVED copy of the report's inline Bibliography section, generated for tooling and wiki ingestion — never a substitute for the inline section.
- `artifacts/` — grimoire-raw-ready markdown extracts for EVERY source in
  `sources.jsonl` (not just "key" ones): every claim's evidence quote must be
  verifiable against on-disk text, not live fetches alone. Before delivery, sweep all
  claims' quotes against the extract corpus and backfill any missing extract; normalize
  whitespace and typographic variants such as curly apostrophes and dashes before
  declaring a quote missing, because extractors may alter punctuation without changing
  the evidence. For scanned PDFs, also compare a lowercase alphanumeric-only fingerprint
  of quote and artifact: line-wrap hyphens, ligatures, and OCR-collapsed spaces otherwise
  create false mismatches. Split evidence quotations containing explicit ellipses into their
  component spans and require every span to match; a literal whole-string check cannot handle
  omitted text. Use fingerprints only for verification; never rewrite the source extract or
  evidence quote to make them match. `web_extract` silently caps at 5 URLs per call and returns only the
  first batch — batch accordingly, and key results by position: returned URLs are
  post-redirect and won't match the requested strings). Recompute every declared `sha256` over the actual Markdown body after aggregation and repair mismatches; delegated scouts may hash a raw capture or a different serialization instead of the artifact they wrote)
- Treat artifact packaging as a set operation: build one canonical FULL-SOURCE extract per registry `source_id`, compare the source-ID set with the packaged set, then verify quotes and hashes before pruning scout captures. Claim-oriented excerpts are evidence aids, not canonical source archives; prefer the complete fetched document when both exist. Keep packaging idempotent by retaining or reusing canonical artifacts when raw inputs are absent; never regenerate a complete artifact index from a pruned tree and replace it with a partial one
- Rerun artifact packaging, evidence-quote verification, and old→new ID-map reconciliation after EVERY correction or delta claim, including checker-generated replacements. Report only the counts in the regenerated files, and point each replaced temporary ID at the replacement rather than the discarded claim; stale maps and pre-delta verification counts otherwise make a checked correction look unverified
- `sources.jsonl` — stable source registry with canonical IDs and provenance tiers
- `claims.jsonl` — the source-derived claims register: verbatim evidence quotes and
  lifecycle states (candidate/validated/discarded/superseded); the ONLY source of
  factual premises for drafting (claims pipeline)
- `ERRATA.md` — dated, numbered log of post-publication corrections (standing practice)
- `evidence.jsonl` — append-only evidence store with quotes and locators
- `claims.jsonl` — atomic claim ledger with support status
- `redteam_report.md` — independent adversarial audit from Phase 6A (all modes;
  persists even when clean — a clean audit is evidence the check ran)
- `analysis/` — **required whenever the report performs any data or numerical
  analysis**, omitted otherwise. Contains every script and dataset behind the report's
  derived numbers so the analysis can be re-run or tweaked later:
  - `analysis/scripts/` — the actual analysis code (Python/etc.), runnable as-is
  - `analysis/data/` — input datasets (CSV/JSON), with provenance noted per file
    (source URL + retrieval date, either in a `data/README.md` or per-file headers)
  - `analysis/README.md` — how to re-run: dependencies, command lines, and a mapping
    from each derived number in the report to the script + dataset that produced it.
    Scripts must read from `analysis/data/` (not re-fetch), so re-runs are
    reproducible even if sources go stale or offline.
- `run_manifest.json` — query, mode, assumptions, provider config
- HTML (McKinsey style, optional — NEVER auto-opened)
- PDF (**REQUIRED dual output in every session type — not just gateway**; the Markdown
  report is the source of truth and the PDF is the portable/print deliverable, and the
  pair are produced together by default. Generate via Pandoc→LaTeX when `pandoc` + a
  LaTeX engine are installed, else WeasyPrint from print-optimized HTML — see
  `reference/html-generation.md`. Must pass `verify_pdf_text.py` before attachment;
  NEVER auto-opened. Do not treat PDF as a per-surface afterthought — it has been
  missed repeatedly; generate it as part of Phase 8 packaging, every run.)

**Markdown line wrapping (NON-NEGOTIABLE):** NEVER use hard line wrapping in authored Markdown files. Write each paragraph as one logical line and each list item as one logical line, regardless of length; let the reader or renderer soft-wrap the text. Hard-wrapped source lines interact poorly with e-readers. This applies to final reports, claim-annotated drafts, bibliographies, appendices, errata, and every other authored Markdown deliverable. Preserve structural newlines for headings, separate paragraphs, list items, table rows, YAML frontmatter, code fences, and deliberate hard breaks—do not collapse those structures. Review generated files before delivery and unwrap any prose or list content produced by drafting subagents.

When retrofitting an existing report, first identify the requested final deliverables and leave claim-annotated drafts, source extracts, and other untouched files alone. Use a dry-run-capable mechanical unwrapping pass rather than manually joining thousands of lines; join only adjacent prose or list-continuation lines, never structural Markdown lines. Assert `original.split() == revised.split()` for every file so the rewrite cannot silently alter report content, rerun the pass as an idempotence check, inspect the resulting diff, and then run the required scoped lint. Use a Markdown parser or targeted edits for complex nesting, blockquotes, indented code, or deliberate hard breaks—line-based rewriting can otherwise destroy meaningful structure.

**Markdown linting (REQUIRED before commit):** the `~/workspace/research` vault is linted with
`markdownlint-cli2` and the repo config `.markdownlint-cli2.jsonc`. After all output
files are written, lint every `.md` file created or modified this run and resolve ALL
findings BEFORE the git commit — **including pre-existing findings in files you
touched** (e.g. when updating an older report's bibliography or a shared note).
Touching a file means adopting its lint debt: that is how the vault gets cleaned
piecemeal. Don't leave a finding because "it was already there", and don't keep a
new file consistent with the vault's old convention violations.

```bash
cd ~/workspace/research
markdownlint-cli2 --no-globs --config ~/workspace/research/.markdownlint-cli2.jsonc \
  "[Topic]_Research_[YYYYMMDD]/research_report_[...].md" \
  "[Topic]_Research_[YYYYMMDD]/bibliography.md" # ...plus every other .md written
```

- `--no-globs` is required — without it the config's `globs` are ADDED to the file
  arguments and you lint the whole vault per invocation.
- `markdownlint-cli2 --fix` safely handles the mechanical findings (emphasis style,
  list markers, trailing spaces) on authored report files; re-run without `--fix` to
  confirm zero findings. `analysis/` scripts and datasets aren't linted (not markdown);
  any README.md files under `analysis/` are. **Fetched source extracts in `artifacts/`
  (sha256-provenance frontmatter) are treated like grimoire `raw/`**: `--fix`
  mechanical whitespace is safe (evidence matching normalizes whitespace), but never
  rewrite extract content — structural findings scraped pages bring (heading
  increments, unlabeled code fences) get a per-file
  `<!-- markdownlint-disable MDxxx -->` line right after the frontmatter instead.
- **`--fix` without `--no-globs` is destructive, not just noisy**: the sweep rewrites
  every markdown file in the vault, violating the piecemeal policy. After ANY lint
  `--fix` run, check `git status` and `git checkout --` every file you did not
  intentionally edit, then re-run scoped to your own files with `--no-globs`.
- The pre-commit hook (`.githooks/pre-commit`) also runs this check but with
  `|| true` — it reports without blocking. The skill's lint step is the real gate.
- **Citation markers and MD052:** `[Cn]` before conversion and `[Sn]` afterward look like undefined reference links to markdownlint. Put `<!-- markdownlint-disable MD052 -->` after the report's frontmatter rather than weakening the vault config, and keep the mechanical citation resolvers as the substantive gate. An empty `## Bibliography` is expected in the claim-annotated draft because `claims_convert.py` generates it; do not let reviewers count that expected pre-conversion state as a finding.
- **Piecemeal policy (updated 2026-08-27):** fix everything the linter surfaces in
  every file you create or touch — new findings and pre-existing ones alike. Do NOT
  reformat untouched files en masse, and do NOT run whole-vault fixes. If a finding
  reveals a genuine config/house-style mismatch, fix the file AND flag the mismatch
  for Nathan so the config can be revisited.

**After completion:** update the vault remote. From `~/workspace/research`: `git pull`, then
stage the new report directory and commit with
`git -c user.name="Inaba" -c user.email="inaba@cardboard-iguana.com" -c user.signingKey="/home/exedev/.ssh/id_ed25519" commit -m "<short informative message about the new report>"`,
then `git push`. (The `ob sync` flow is deprecated — git is the sync mechanism now.)

**Quality standards:**
- 10+ sources, 3+ per major claim (cluster-independent, not just count)
- Normalize parallel claim batches before R3 with a saved aggregation script under `analysis/scripts/`: map temporary IDs to sequential `Cn` and retain an old→new ID map for checker range assignments, normalize common aliases such as `artifact`/`artifact_path` and `verbatim_evidence_quote`/`evidence_quote`, deduplicate sources by canonical locator, enforce the claim schema and allowed enums, reset checker-generated records to `candidate`, then run `claims_check.py`; hand-merging heterogeneous scout JSONL is error-prone and loses the provenance needed for independent checks. Canonicalize DOIs case-insensitively and normalize URL scheme/host casing, trailing slashes, and fragments BEFORE hashing source IDs; otherwise parallel scouts register the same work under different IDs and split its claims and artifacts
- Compare the set of `source_id`s in `sources.jsonl` against the set covered by the artifact index, not the number of artifact files or index rows; duplicate artifacts across batches can make coverage look complete while sources with different field names have no registered extract
- During the outline coverage check, compare registered `source_id`s with those used by claims; record an exclusion reason for retrieved-but-unused sources or narrow the report's claimed review scope, so the prose does not imply depth the evidence trail lacks
- After every delta retrieval wave, mechanically reconcile source, claim, lifecycle, and citation counts across the body, methodology, metadata, and run manifest; search both digits and spelled-out numbers because prose counts survive replacements aimed only at numeric metadata
- Keep one canonical packaged Markdown extract per `source_id` and remove or quarantine duplicate scout captures before final lint; duplicate raw extracts multiply lint, hashing, and review work without adding provenance
- Validate the merged registry after every R3 wave before replacing `claims.jsonl`: merge verdict-only checker output onto the original claim by `claim_id`, normalize `status`/`lifecycle` and checker verdict aliases to the schema enums, and run `claims_check.py` on a staging file; otherwise a checker can silently strip evidence fields or invalidate the whole register. Accept corrected-claim records in either flat or wrapped form, resolve the parent from `supersedes`, `parent_claim_id`, or the checker's `corrected_claim_id`, and project only schema-approved keys before merging; heterogeneous checker wrappers otherwise break parent linkage or leak non-schema fields into the registry. Preserve the parent's check reason and replacement link, and keep replacement statements substantive — editorial labels such as "corrected Cn" belong in the check metadata, not in the factual claim text
- All factual claims cited immediately [N] with evidence backing in `evidence.jsonl`
- Claim-support verification mandatory: no unsupported factual claims pass delivery
- Verify every red-team or persona finding against the current report and source artifact before applying it; independent reviewers can make false path, metadata, attribution, table-column, or arithmetic assertions too
- During R3 and R5, read the surrounding text and relevant tables, not just the claim's evidence quote. Check omitted columns and rival explanations before validating a claim, require the final interpretive clause to follow as well as the quoted number, and distinguish composition shares from causal explanations. Do not rank one hypothesis above another unless the source does so, and do not generalize a narrow measured channel into a verdict on every variable in the model
- Assemble the latest draft at the review path before dispatching red-team agents and run the citation/lifecycle check on that exact file; if it changes during review, run a targeted re-audit so reviewers never certify stale prose, and state explicitly which pre-conversion conditions are expected. Also assert the expected heading sequence and Executive Summary word count after mechanical concatenation; splitting and stripping section text can fuse a heading to its first sentence even when every citation resolves
- Audit cross-source and cross-domain analogies dimension by dimension: name the shared mechanism AND the point where the analogy reverses, especially production site, unit, motive, and direction of causation. Do not say one process "recapitulates" another when a defining feature runs in the opposite direction; formulate the narrower resemblance instead
- Map every mechanism clause to its incident before drafting comparisons; a shared wallet, vendor, or interface does not license transferring technical details between cases
- Treat a victim's architectural explanation as a causal hypothesis: test it against the same system's observed behavior and ordinary process alternatives, because a verbatim quote proves what the victim said, not what caused the delay or failure
- For protocol disputes, treat gas as corroboration only after complete intrinsic-cost and refund accounting; unexplained residue invalidates it as standalone proof
- Write "the victim has not disclosed" or "the source set does not establish" rather than "nothing published" until secondary reconstructions have also been checked; first-party silence and absence of analysis are different claims
- For novelty and trend claims, document the antecedent selection frame, include earlier canonical cases and the closest major-magnitude comparator when available, and bound conclusions to that sample; a hand-picked recent or small comparison set inflates novelty and impact
- For software product comparisons, decompose each feature into capture, local persistence, display, sync, export, and later reconciliation: a feed shown beside an entry may never enter the database or export, and an event-triggered integration may preserve stale state after the source changes
- Test reconciliation with move-out, deletion, and late-arrival cases, not only edits within the same bucket or date: a change feed that sees an item's new location may provide no evidence that the old location needs re-rendering
- Verify export scope separately from export format — readable HTML/DOCX/PDF output does not establish that imported context, metadata, or attachments are included; use official export documentation, maintainer answers, or a hands-on export test, and label unverified scope rather than inferring it from the UI
- Treat feature requests and user comments as demand or reported experience, not evidence of implementation; prefer current product docs and maintainer statements for capability claims
- Distinguish announced, shipped, and currently available capabilities; a future-tense maintainer announcement is not a shipped feature, so corroborate it against the current changelog, help pages, or store release notes before using present tense
- No placeholders, no fabricated citations
- Prose-first (>=80%), bullets sparingly
- Slop-free prose: all report prose follows the `no-ai-slop` skill's editing rules
  (load it with `skill_view(name='no-ai-slop')`). Drafting subagents write to its
  standard, and Phase 7/8 includes a final editing pass against its `eval.md`
  checks (see reference/quality-gates.md, "AI-Slop Pass").

---

## Delivery Contract

**NEVER auto-open the report in a browser** (or any other application). Delivery is:

1. **In-chat:** a compact summary — research question, mode, key findings (3-5 bullets),
   source count, validation status, and the report path.
2. **Attachment (gateway sessions):** reference the report with a `MEDIA:` line so the
   platform delivers it as a native attachment:

   ```
   MEDIA:/home/exedev/workspace/research/[Topic]_Research_[YYYYMMDD]/research_report_[...].pdf
   ```

   On Discord/Telegram this arrives as a file upload. **Generate the PDF in every
   session type** — gateway (Discord/Telegram), WebUI, and TUI/CLI alike — because it
   is the portable deliverable and has been missed when treated as gateway-only. Attach
   it via `MEDIA:` (after it passes `verify_pdf_text.py`), and also attach the markdown
   as a second `MEDIA:` line for users who want the source of truth. In TUI/CLI
   sessions, MEDIA lines are just saved paths — the summary + paths are the
   deliverable, but the PDF is still generated, not skipped. **In WebUI sessions,
   MEDIA: paths must point inside the active workspace** (the `[Workspace::v1: ...]`
   path, typically `~/workspace`) — files outside it fail
   user-side with "Path not in allowed location". The research vault is already under
   `~/workspace`, so no delivery copy is needed when that is the active workspace. If a
   different workspace is active, copy deliverables there and reference the copies; the
   `~/workspace/research` originals remain the source of truth.
3. **Wiki note:** the report lives in the `~/workspace/research` vault, so it is already
   searchable/linkable in Obsidian once committed and pushed.

---

## When to Use / NOT Use

**Use:** Comprehensive analysis, technology comparisons, state-of-the-art reviews,
multi-perspective investigation, market analysis.

**Do NOT use:** Simple lookups, debugging, 1-2 search answers, quick time-sensitive queries.
