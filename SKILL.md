---
name: deep-research
description: Use when the user needs multi-source research with citation tracking, evidence persistence, and structured report generation. Triggers on "deep research", "comprehensive analysis", "research report", "compare X vs Y", "analyze trends", or "state of the art". Not for simple lookups, debugging, or questions answerable with 1-2 searches.
---

# Deep Research

## Core Purpose

Deliver citation-tracked research reports through a structured pipeline with evidence
persistence, source identity management, claim-level verification, and progressive
context management.

**Before beginning a run:** `cd ~/research && git pull` to ensure the vault is up-to-date.

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
| 3 | RETRIEVE | Y | Y | Y | Y | **delegate_task** (subagents) |
| 4 | TRIANGULATE | - | Y | Y | Y | **delegate_task** (subagent synthesis) |
| 4.5 | OUTLINE REFINEMENT | - | Y | Y | Y | **delegate_task** (subagent analysis) |
| 5 | SYNTHESIZE | - | Y | Y | Y | **delegate_task** (subagent drafting) |
| 6 | CRITIQUE | † | Y | Y | Y | **delegate_task** (independent red team + persona subagents) |
| 7 | REFINE | - | Y | Y | Y | **delegate_task** (targeted subagents) |
| 8 | PACKAGE | Y | Y | Y | Y | **Mixed**: subagents for sections, main for validation |

**Delegation principle:** Phases 3-8 are delegated to subagents whenever they involve
multi-step generation, analysis, or drafting. The main context handles only:
- Research framing (Phase 1) and strategy (Phase 2)
- Final validation and delivery decisions
- Cross-phase coordination and gap-filling when subagents return incomplete work

**† Quick mode Phase 6:** Skipped by default. If the research is decision-critical,
ask the user whether to include a critique pass (default suggestion: yes).

**Note:** Phases 3-5 operate as an evidence loop per section (retrieve -> evidence
store -> refine outline -> draft -> verify claims -> delta-retrieve if needed), not as
strict sequential gates. Each loop iteration is a candidate for delegation.

---

## Search Ladder (summary)

1. **`~/grimoire`** — `mcp__obsidian_grimoire__search_notes` first, always. Trace hits
   to their original `source_url:` for citations.
2. **Kagi MCP** — `mcp__kagi__kagi_search_fetch` is the primary web search.
3. **Exa MCP** — `mcp__exa__web_search_exa` for semantic search and gap-filling.

Details in [methodology.md](./reference/methodology.md) Phase 3.

---

## Execution

**On invocation, load relevant reference files:**

1. **Phase 1-7:** Load [methodology.md](./reference/methodology.md) for detailed phase instructions
2. **Phase 8 (Report):** Load [report-assembly.md](./reference/report-assembly.md) for progressive generation
3. **HTML/PDF output:** Load [html-generation.md](./reference/html-generation.md)
4. **Quality checks:** Load [quality-gates.md](./reference/quality-gates.md)
5. **Long reports (>18K words):** Load [continuation.md](./reference/continuation.md)

**Templates:**
- Report structure: [report_template.md](./templates/report_template.md)
- HTML styling: [mckinsey_report_template.html](./templates/mckinsey_report_template.html)

**Scripts:**
- `python scripts/validate_report.py --report [path]`
- `python scripts/verify_citations.py --report [path]`
- `python scripts/verify_pdf_text.py --pdf [path]` (mandatory when a PDF is generated)
- `python scripts/md_to_html.py [markdown_path]`
- `python scripts/citation_manager.py` — source registration and citation numbering
- `python scripts/evidence_store.py` — evidence persistence (add/query)
- `python scripts/source_evaluator.py` — source credibility scoring
- `python scripts/verify_html.py --html [path] --md [path]` — HTML verification

**Schemas** (structural contracts for the pipeline's JSONL/JSON files):
- `schemas/source.schema.json` — `sources.jsonl` entries
- `schemas/evidence.schema.json` — `evidence.jsonl` entries
- `schemas/claim.schema.json` — `claims.jsonl` entries
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
- Bibliography (COMPLETE - every citation, no placeholders)
- Methodology Appendix

**Output files (all to `~/research/[Topic]_Research_[YYYYMMDD]/`):**
- Markdown report (primary source of truth) — written via `mcp__obsidian_research__write_note`
- `bibliography.md` — standalone ingestion map for future wiki integration (MCP-written)
- `artifacts/` — grimoire-raw-ready markdown extracts of key sources (MCP-written)
- `sources.jsonl` — stable source registry with canonical IDs
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

**Markdown linting (REQUIRED before commit):** the `~/research` vault is linted with
`markdownlint-cli2` and the repo config `.markdownlint-cli2.jsonc`. After all output
files are written, lint every `.md` file created or modified this run and resolve ALL
findings BEFORE the git commit — **including pre-existing findings in files you
touched** (e.g. when updating an older report's bibliography or a shared note).
Touching a file means adopting its lint debt: that is how the vault gets cleaned
piecemeal. Don't leave a finding because "it was already there", and don't keep a
new file consistent with the vault's old convention violations.

```bash
cd ~/research
markdownlint-cli2 --no-globs --config ~/research/.markdownlint-cli2.jsonc \
  "[Topic]_Research_[YYYYMMDD]/research_report_[...].md" \
  "[Topic]_Research_[YYYYMMDD]/bibliography.md" # ...plus every other .md written
```

- `--no-globs` is required — without it the config's `globs` are ADDED to the file
  arguments and you lint the whole vault per invocation.
- `markdownlint-cli2 --fix` (before `--no-globs`) safely handles the mechanical
  findings (emphasis style, list markers, trailing spaces) on authored report files;
  re-run without `--fix` to confirm zero findings. `analysis/` scripts and datasets
  aren't linted (not markdown); any README.md files under `analysis/` are.
- The pre-commit hook (`.githooks/pre-commit`) also runs this check but with
  `|| true` — it reports without blocking. The skill's lint step is the real gate.
- **Piecemeal policy (updated 2026-08-27):** fix everything the linter surfaces in
  every file you create or touch — new findings and pre-existing ones alike. Do NOT
  reformat untouched files en masse, and do NOT run whole-vault fixes. If a finding
  reveals a genuine config/house-style mismatch, fix the file AND flag the mismatch
  for Nathan so the config can be revisited.

**After completion:** update the vault remote. From `~/research`: `git pull`, then
stage the new report directory and commit with
`git -c user.name="Inaba" -c user.email="inaba@cardboard-iguana.com" -c user.signingKey="/home/exedev/.ssh/id_ed25519" commit -m "<short informative message about the new report>"`,
then `git push`. (The `ob sync` flow is deprecated — git is the sync mechanism now.)

**Quality standards:**
- 10+ sources, 3+ per major claim (cluster-independent, not just count)
- All factual claims cited immediately [N] with evidence backing in `evidence.jsonl`
- Claim-support verification mandatory: no unsupported factual claims pass delivery
- No placeholders, no fabricated citations
- Prose-first (>=80%), bullets sparingly

---

## Delivery Contract

**NEVER auto-open the report in a browser** (or any other application). Delivery is:

1. **In-chat:** a compact summary — research question, mode, key findings (3-5 bullets),
   source count, validation status, and the report path.
2. **Attachment (gateway sessions):** reference the report with a `MEDIA:` line so the
   platform delivers it as a native attachment:

   ```
   MEDIA:/home/exedev/research/[Topic]_Research_[YYYYMMDD]/research_report_[...].pdf
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
   user-side with "Path not in allowed location". Copy deliverables into the workspace
   (e.g. `~/workspace/[Topic]_Research_[YYYYMMDD]/`) and reference the copies; the
   `~/research` originals remain the source of truth.
3. **Wiki note:** the report lives in the `~/research` vault, so it is already
   searchable/linkable in Obsidian once committed and pushed.

---

## When to Use / NOT Use

**Use:** Comprehensive analysis, technology comparisons, state-of-the-art reviews,
multi-perspective investigation, market analysis.

**Do NOT use:** Simple lookups, debugging, 1-2 search answers, quick time-sensitive queries.
