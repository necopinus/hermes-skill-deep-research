> [!note]
> Forked from [199-biotechnologies/claude-deep-research-skill](https://github.com/199-biotechnologies/claude-deep-research-skill) at commit [f2f2c0f](https://github.com/199-biotechnologies/claude-deep-research-skill/commit/f2f2c0fa4e7617ca84c86b63f4bb40f77a746933) on July 17th 2026, and rewritten for Hermes Agent.

# Deep Research Skill for Hermes

Enterprise-grade research engine for [Hermes Agent](https://github.com/NousResearch/hermes-agent).
Produces citation-backed reports with source credibility scoring, layered search
(local wiki -> Kagi -> Exa), and automated validation.

## Installation

```bash
# Clone into the Hermes skills directory
git clone https://github.com/necopinus/hermes-skill-deep-research.git ~/.hermes/skills/research/deep-research
```

No additional dependencies required for basic usage (Python 3.9+ stdlib only).

### Prerequisites (MCP servers)

The search ladder runs over MCP servers configured in the Hermes config:

| Server | Role | Setup |
|--------|------|-------|
| obsidian-grimoire | Local wiki, searched first | Obsidian MCP pointed at `~/grimoire` |
| kagi | Primary web search | Kagi MCP + API key |
| exa | Semantic/neural search | Exa MCP + API key |

Reports are written to the `~/research` Obsidian vault via the `obsidian-research`
MCP server. If that vault/server isn't configured, fall back to plain file writes
(the skill degrades gracefully, but the MCP route is the intended path).

### Optional: obsidian-headless (vault sync)

To push the research vault to Obsidian Sync after a report completes:

```bash
# Requires Node.js 22+ — invoked via npx, no global install
cd ~/research && npx --package=obsidian-headless --yes -- ob sync
```

### Optional: WeasyPrint (PDF output)

```bash
pip install weasyprint   # user-level install
```

## Usage

```
deep research on the current state of quantum computing
```

```
deep research in ultradeep mode: compare PostgreSQL vs Supabase for our stack
```

## Research Modes

| Mode | Phases | Duration | Best For |
|------|--------|----------|----------|
| Quick | 3 | 2-5 min | Initial exploration |
| Standard | 6 | 5-10 min | Most research questions |
| Deep | 8 | 10-20 min | Complex topics, critical decisions |
| UltraDeep | 8+ | 20-45 min | Comprehensive reports, maximum rigor |

## Pipeline

Scope &rarr; Plan &rarr; **Retrieve** (search ladder + parallel subagents) &rarr; Triangulate &rarr; Outline Refinement &rarr; Synthesize &rarr; Critique (with loop-back) &rarr; Refine &rarr; Package

Key features:
- **Step 0**: Retrieves current date before searches (prevents stale training-data year assumptions)
- **Search ladder**: local wiki (`~/grimoire`) &rarr; Kagi MCP &rarr; Exa MCP, with provenance tracing to original URLs
- **Parallel retrieval**: batched concurrent searches + `delegate_task` subagents returning structured evidence objects
- **First Finish Search**: Adaptive quality thresholds by mode
- **Critique loop-back**: Phase 6 can return to Phase 3 with delta-queries if critical gaps found
- **Multi-persona red teaming**: Skeptical Practitioner, Adversarial Reviewer, Implementation Engineer (Deep/UltraDeep)
- **Disk-persisted citations**: `sources.jsonl` survives context compaction and continuation sessions

## Output

Reports saved to `~/research/[Topic]_Research_[Date]/`:
- Markdown (primary source of truth, written via the obsidian-research MCP)
- `bibliography.md` — standalone ingestion map for wiki integration
- `artifacts/` — source extracts with llm-wiki `raw/` frontmatter, drop-in ready for `~/grimoire/raw/articles/`
- `sources.jsonl` / `evidence.jsonl` / `claims.jsonl` / `run_manifest.json`
- HTML (McKinsey-style, optional) and PDF (WeasyPrint, optional) — never auto-opened

Delivery is in-chat (summary + path) plus `MEDIA:` attachment on messaging gateways
(Discord/Telegram receive the report as a native file upload).

Reports >18K words continue via `delegate_task` batches or a fresh Hermes session
with a `continuation_state.json` handoff (see `reference/continuation.md`).

## Quality Standards

- 10+ sources, 3+ per major claim
- Executive summary 200-400 words
- Findings 600-2,000 words each, prose-first (>=80%)
- Full bibliography with URLs, no placeholders
- Automated validation: `validate_report.py` (9 checks) + `verify_citations.py` (DOI/URL/hallucination detection)
- Validation loop: validate &rarr; fix &rarr; retry (max 3 cycles)

## Search Tools

| Tool | Priority | Setup |
|------|----------|-------|
| obsidian-grimoire MCP | **First** — local wiki, always | MCP config |
| Kagi MCP | **Primary web search** | MCP config + API key |
| Exa MCP | **Semantic/gap-fill** | MCP config + API key |
| web_search | Last-resort fallback | None (built-in) |

## Architecture

```
deep-research/
├── SKILL.md                          # Skill entry point (lean)
├── reference/
│   ├── methodology.md                # 8-phase pipeline details + search ladder
│   ├── report-assembly.md            # Progressive generation + output/sync contract
│   ├── quality-gates.md              # Validation standards
│   ├── html-generation.md            # McKinsey HTML conversion
│   ├── continuation.md               # Continuation protocol (delegate_task / fresh session)
│   └── weasyprint_guidelines.md      # PDF generation
├── templates/
│   ├── report_template.md            # Report structure template
│   └── mckinsey_report_template.html # HTML report template
├── scripts/
│   ├── validate_report.py            # 9-check structure validator
│   ├── verify_citations.py           # DOI/URL/hallucination checker
│   ├── source_evaluator.py           # Source credibility scoring
│   ├── citation_manager.py           # Citation tracking
│   ├── md_to_html.py                 # Markdown to HTML converter
│   ├── verify_html.py                # HTML verification
│   └── research_engine.py            # State scaffold (not a runtime orchestrator)
└── tests/
    └── fixtures/                     # Test report fixtures
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.1-hermes | 2026-07-17 | Hermes port: search ladder (grimoire -> Kagi -> Exa), obsidian-research MCP writes, ~/research output + ob sync, MEDIA: delivery, grimoire-ready artifacts, continuation via delegate_task/fresh session |
| 2.3.1 | 2026-03-19 | Template/validator harmonization, structured evidence, critique loop-back, multi-persona red teaming |
| 2.3 | 2026-03-19 | Contract harmonization, search-cli integration, dynamic year detection, disk-persisted citations, validation loops |
| 2.2 | 2025-11-05 | Auto-continuation system for unlimited length |
| 2.1 | 2025-11-05 | Progressive file assembly |
| 1.0 | 2025-11-04 | Initial release |

## License

MIT - modify as needed for your workflow.
