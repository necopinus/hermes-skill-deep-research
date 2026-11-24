# Report Assembly: Progressive File Generation

## Length Requirements by Mode

| Mode | Target Words | Description |
|------|--------------|-------------|
| Quick | 2,000-4,000 | Baseline quality threshold |
| Standard | 4,000-8,000 | Comprehensive analysis |
| Deep | 8,000-15,000 | Thorough investigation |
| UltraDeep | 15,000-20,000+ | Maximum rigor |

---

## Output Token Safeguard

Keep each individual generation under ~2,000 words and write sections progressively —
this keeps every response well inside model output limits regardless of provider.
Reports that will exceed ~18,000 words total use the continuation protocol
(see continuation.md).

---

## Output Location

**Base directory:** `~/workspace/research/[TopicName]_Research_[YYYYMMDD]/`

- `~/workspace/research` is an Obsidian vault, served by the `obsidian-research` MCP server.
  ALL markdown files (report, bibliography, grimoire-ready artifacts) are written via
  `mcp__obsidian_research__*` tools — not raw file writes.
- Non-markdown files (`sources.jsonl`, `evidence.jsonl`, `claims.jsonl`,
  `run_manifest.json`, HTML, PDF) are written with normal file/terminal tools, since
  the MCP note tools only handle `.md`.
- Clean topic name: remove special chars, use underscores.

**Vault-relative paths:** the MCP tools take paths relative to the vault root, e.g.
`Quantum_Computing_Research_20260717/research_report_20260717_quantum_computing.md`.

## Sync

After the final report is written (and after any continuation finalizes), sync the
vault via git:

```bash
cd ~/workspace/research && git pull
git -c user.name="Inaba" -c user.email="inaba@cardboard-iguana.com" \
  -c user.signingKey="/home/exedev/.ssh/id_ed25519" \
  add "[Topic]_Research_[YYYYMMDD]/" && \
git -c user.name="Inaba" -c user.email="inaba@cardboard-iguana.com" \
  -c user.signingKey="/home/exedev/.ssh/id_ed25519" \
  commit -m "<short informative message about the new report>" && \
git push
```

Run once at the end — not per section. The `ob sync` flow is deprecated; git is the
sync mechanism. **No backup step** — the vault itself is the canonical store, synced
remotely via git.

---

## Progressive Section Generation

**Core Strategy:** Generate and write each section individually via the
obsidian-research MCP. This allows unlimited report length while keeping each
generation manageable.

### Phase 8.1: Setup

```bash
# Create folder (needed once so non-md artifacts have somewhere to live)
mkdir -p ~/workspace/research/[folder_name]/artifacts

# Initialize research run (persist run manifest + jsonl ledgers)
python scripts/citation_manager.py init-run --out-dir ~/workspace/research/[folder_name] \
  --query "[question]" --mode [mode]
# Creates: run_manifest.json, sources.jsonl, evidence.jsonl, claims.jsonl
```

Then create the report note with frontmatter + title via MCP:

```
mcp__obsidian_research__write_note(
  path="[folder_name]/research_report_[YYYYMMDD]_[slug].md",
  content="---\ncreated: [date]\ntype: research-report\nquery: [question]\nmode: [mode]\ntags: [research-report]\n---\n\n# Research Report: [Topic]\n"
)
```

### Phase 8.2: Section Generation Loop

**Pattern:** generate section -> `mcp__obsidian_research__write_note(mode="append")` ->
next section. Each call contains ONE section (<=2,000 words per call).

**Register each source as you encounter it:**
```bash
python scripts/citation_manager.py register-source \
  --json '{"raw_url": "...", "title": "...", "source_type": "academic", "year": "2024"}' \
  --dir ~/workspace/research/[folder_name]
# Returns stable source_id (sha256-based, survives renumbering and continuation)
```

**Assign display numbers after all sources registered:**
```bash
python scripts/citation_manager.py assign-display-numbers --dir ~/workspace/research/[folder_name]
# Maps stable source_ids to [1], [2], [3]... for rendering
```

Source identity is stable across edits and continuation. Display numbers are derived at
render time, never stored in state. This survives context compaction and lets
continuation sessions pick up citation state via stable IDs.

**Section sequence:**

1. **Executive Summary** (200-400 words)
2. **Introduction** (400-800 words)
3. **Finding 1-N** (600-2,000 words each)
4. **Synthesis & Insights** — novel insights beyond source statements
5. **Limitations & Caveats** — counterevidence, gaps, uncertainties
6. **Recommendations** — immediate actions, next steps, research needs
7. **Bibliography** (CRITICAL) — EVERY citation, no ranges, no placeholders, no truncation
8. **Methodology Appendix** — research process, verification approach

---

## Grimoire-Ready Artifacts

Reports feed the shared wiki at `~/workspace/grimoire` (see the llm-wiki skill). Integration is
NEVER automatic — but the report folder must make it trivial.

**For every source whose content was fetched in full** (via kagi extract, exa fetch, or
markitdown), save the extracted markdown to `[folder]/artifacts/` via MCP:

```
mcp__obsidian_research__write_note(
  path="[folder]/artifacts/[source-slug].md",
  content="---\nsource_url: [original URL]\ningested: [YYYY-MM-DD]\nsha256: [hex of body]\n---\n\n[extracted markdown]"
)
```

This frontmatter format matches llm-wiki's `raw/` convention exactly, so artifacts can
be dropped straight into `~/workspace/grimoire/raw/articles/` (via `cp` or a wiki move) without
reformatting. Compute the sha256 over the body only (everything after the closing
`---`) — `sha256sum` on a temp copy, or `execute_code`.

**Also emit `[folder]/bibliography.md`** — a standalone note containing the full
bibliography with, per entry: citation number, author/org, year, title, publication,
URL, retrieval date, credibility score, and `source_type`. This is the ingestion map: a
future llm-wiki session can read it to know exactly which artifacts exist and which
sources still need fetching.

**Provenance chain:** sources originally found in `~/workspace/grimoire` keep their ORIGINAL
`source_url:` (from the raw file's frontmatter), with an added
`via: "grimoire: raw/articles/[file].md"` frontmatter line so the chain stays visible.

---

## File Organization

All files use the same base name:

```
~/workspace/research/[TopicName]_Research_[YYYYMMDD]/
├── research_report_[YYYYMMDD]_[slug].md   # primary source of truth (MCP-written)
├── research_report_[YYYYMMDD]_[slug].html # optional, McKinsey style
├── research_report_[YYYYMMDD]_[slug].pdf  # optional, Pandoc→LaTeX or WeasyPrint
├── bibliography.md                        # standalone ingestion map (MCP-written)
├── artifacts/                             # grimoire-raw-ready source extracts (MCP-written)
│   └── [source-slug].md
├── sources.jsonl                          # stable source registry
├── evidence.jsonl                         # append-only evidence store
├── claims.jsonl                           # source-derived claims register (claims pipeline)
└── run_manifest.json                      # query, mode, assumptions, provider config
```

---

## Math, diagrams, and the Obsidian-first PDF path

When a report needs notation or diagrams, prefer the vault's native formats before
reaching for LaTeX or external tools:

1. **Math:** Obsidian-compatible LaTeX — inline `$...$`, block `$$...$$` (the
   `aligned` grouping is allowed inside a block; do not use `align`/`align*`
   environments). Every constant in a formula must trace to a cited claim in the
   surrounding prose, and drafting agents must be told which math the section needs.
2. **Diagrams:** Mermaid fenced blocks (`sequenceDiagram` for timelines and message
   flows, `flowchart` for state machines). Keep labels plain text (no `$`, avoid
   `;`/`#`), and have a checker verify the diagram's constants against the cited
   claims — a diagram is a factual assertion rendered as pixels.
3. **PDF build:** Pandoc cannot render Mermaid. Pre-render each block with an HTTP
   call to kroki.io (`curl --data-binary @diagram.mmd https://kroki.io/mermaid/png`,
   assert HTTP 200; `npx @mermaid-js/mermaid-cli` works but is heavy), store the PNG
   under `analysis/build/`, and substitute image includes in a **build copy only** —
   never in the vault Markdown. Then `pandoc --pdf-engine=xelatex` with DejaVu fonts
   (`-V mainfont="DejaVu Serif"` etc.) so unicode arrows and dashes survive.
4. **`verify_pdf_text.py` false positives:** its fused-word heuristic can flag a
   legitimate English word (e.g. "pointless" = "point"+"less"). The gate must pass,
   so reword the prose and rebuild rather than waiving the gate.

Two counting rules for self-reported metadata (both burned a report once):

- **Citation count:** extract ALL claim ids inside EACH bracket group
  (`[C1][C2]` and `[C3, C4]` each contribute every id) — a regex like `\[C(\d+)`
  silently undercounts multi-citation groups.
- **Word count:** strip fenced code blocks, `$$...$$` and `$...$` math, and
  `[Cn]` citation markers BEFORE splitting on whitespace, and say what the count
  includes ("prose and tables; code, math, and citations excluded").

**Post-conversion edits require the full chain re-run:** any edit to a
`draft_sections/` file after `claims_convert.py` means re-running
assemble -> claims_convert -> resolve_citations -> lint -> PDF build ->
verify_pdf_text, because the assembler writes the claim-annotated draft over the
converted file.

**Artifact lint disables change the body hash.** Inserting the per-file
`<!-- markdownlint-disable MDxxx -->` line after an artifact's frontmatter puts the
comment inside the sha256-covered body — recompute the declared hash and re-run the
evidence-quote substring sweep afterwards.

## Word Count Per Section

**CRITICAL:** No single MCP write should exceed ~2,000 words.

Example: 10 findings x 1,500 words = 15,000 words total
- Each append call: 1,500 words (under limit)
- File grows to 15,000 words
- No single tool call exceeds limits
