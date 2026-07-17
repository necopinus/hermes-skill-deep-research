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

**Base directory:** `~/research/[TopicName]_Research_[YYYYMMDD]/`

- `~/research` is an Obsidian vault, served by the `obsidian-research` MCP server.
  ALL markdown files (report, bibliography, grimoire-ready artifacts) are written via
  `mcp__obsidian_research__*` tools — not raw file writes.
- Non-markdown files (`sources.jsonl`, `evidence.jsonl`, `claims.jsonl`,
  `run_manifest.json`, HTML, PDF) are written with normal file/terminal tools, since
  the MCP note tools only handle `.md`.
- Clean topic name: remove special chars, use underscores.

**Vault-relative paths:** the MCP tools take paths relative to the vault root, e.g.
`Quantum_Computing_Research_20260717/research_report_20260717_quantum_computing.md`.

## Sync

After the final report is written (and after any continuation finalizes), trigger an
Obsidian Sync push:

```bash
cd ~/research && npx --package=obsidian-headless --yes -- ob sync
```

Run once at the end — not per section. `ob` requires Node 22+ and is always invoked
via `npx --package=obsidian-headless --yes -- ob` (no global install). **No backup
step** — the vault itself is the canonical store, synced remotely.

---

## Progressive Section Generation

**Core Strategy:** Generate and write each section individually via the
obsidian-research MCP. This allows unlimited report length while keeping each
generation manageable.

### Phase 8.1: Setup

```bash
# Create folder (needed once so non-md artifacts have somewhere to live)
mkdir -p ~/research/[folder_name]/artifacts

# Initialize research run (persist run manifest + jsonl ledgers)
python scripts/citation_manager.py init-run --out-dir ~/research/[folder_name] \
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
  --dir ~/research/[folder_name]
# Returns stable source_id (sha256-based, survives renumbering and continuation)
```

**Assign display numbers after all sources registered:**
```bash
python scripts/citation_manager.py assign-display-numbers --dir ~/research/[folder_name]
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

Reports feed the shared wiki at `~/grimoire` (see the llm-wiki skill). Integration is
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
be dropped straight into `~/grimoire/raw/articles/` (via `cp` or a wiki move) without
reformatting. Compute the sha256 over the body only (everything after the closing
`---`) — `sha256sum` on a temp copy, or `execute_code`.

**Also emit `[folder]/bibliography.md`** — a standalone note containing the full
bibliography with, per entry: citation number, author/org, year, title, publication,
URL, retrieval date, credibility score, and `source_type`. This is the ingestion map: a
future llm-wiki session can read it to know exactly which artifacts exist and which
sources still need fetching.

**Provenance chain:** sources originally found in `~/grimoire` keep their ORIGINAL
`source_url:` (from the raw file's frontmatter), with an added
`via: "grimoire: raw/articles/[file].md"` frontmatter line so the chain stays visible.

---

## File Organization

All files use the same base name:

```
~/research/[TopicName]_Research_[YYYYMMDD]/
├── research_report_[YYYYMMDD]_[slug].md   # primary source of truth (MCP-written)
├── research_report_[YYYYMMDD]_[slug].html # optional, McKinsey style
├── research_report_[YYYYMMDD]_[slug].pdf  # optional, WeasyPrint
├── bibliography.md                        # standalone ingestion map (MCP-written)
├── artifacts/                             # grimoire-raw-ready source extracts (MCP-written)
│   └── [source-slug].md
├── sources.jsonl                          # stable source registry
├── evidence.jsonl                         # append-only evidence store
├── claims.jsonl                           # atomic claim ledger
└── run_manifest.json                      # query, mode, assumptions, provider config
```

---

## Word Count Per Section

**CRITICAL:** No single MCP write should exceed ~2,000 words.

Example: 10 findings x 1,500 words = 15,000 words total
- Each append call: 1,500 words (under limit)
- File grows to 15,000 words
- No single tool call exceeds limits
