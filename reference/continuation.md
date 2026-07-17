# Auto-Continuation Protocol

## When to Use

Trigger auto-continuation when the report exceeds ~18,000 words in a single run, or when
context pressure makes it risky to keep generating in the current session.

---

## Strategy Overview (Hermes-native)

Hermes doesn't have Claude's Task-tool recursive agents, but it has two mechanisms that
cover the same ground:

1. **`delegate_task`** — spawn a subagent with an isolated context to write the next
   section batch. Bounded by `delegation.max_concurrent_children` (default 3) and NOT
   durable: if the parent session dies, the subagent's work is lost. Use for quick
   section batches within a live run.

2. **Fresh session resume (preferred for long chains)** — write a continuation state
   file, then resume in a NEW Hermes session (or a one-shot
   `hermes chat -q "continue deep-research report, state: [path]"`). Fully durable,
   no recursion depth issues, and each session gets a fresh context window. This is the
   Hermes-idiomatic replacement for recursive agent spawning.

**Default choice:** delegate_task for 1-2 continuation batches inside a live run; fresh
session resume for anything longer.

---

## Continuation State File

**Location:** inside the report folder, `continuation_state.json`

(e.g. `~/research/Topic_Research_20260717/continuation_state.json`)

Keeping state next to the artifacts (not in a global state dir) means the folder is
self-contained and the state is included if the folder is synced or archived.

```json
{
  "version": "3.0.0",
  "report_id": "[unique_id]",
  "file_path": "[absolute_path_to_report.md]",
  "mode": "[quick|standard|deep|ultradeep]",

  "progress": {
    "sections_completed": ["list of section IDs"],
    "total_planned_sections": 15,
    "word_count_so_far": 12000,
    "continuation_count": 1
  },

  "artifacts": {
    "sources_path": "[folder]/sources.jsonl",
    "evidence_path": "[folder]/evidence.jsonl",
    "claims_path": "[folder]/claims.jsonl",
    "run_manifest_path": "[folder]/run_manifest.json",
    "artifacts_dir": "[folder]/artifacts"
  },

  "research_context": {
    "research_question": "[original question]",
    "key_themes": ["theme1", "theme2"],
    "main_findings_summary": [
      "Finding 1: [100-word summary]",
      "Finding 2: [100-word summary]"
    ],
    "narrative_arc": "middle"
  },

  "quality_metrics": {
    "avg_words_per_finding": 1500,
    "citation_density": 5.2,
    "prose_vs_bullets_ratio": "85% prose",
    "writing_style": "technical-precise-data-driven"
  },

  "next_sections": [
    {"id": 11, "type": "finding", "title": "Finding X", "target_words": 1500},
    {"id": 12, "type": "synthesis", "title": "Synthesis", "target_words": 1000}
  ]
}
```

---

## Option A: Continuation via delegate_task

```
delegate_task(
  goal="Continue deep-research report: generate the next section batch",
  context="""
CONTINUATION TASK: Continue an existing deep-research report.

CRITICAL INSTRUCTIONS:
1. Read continuation state: [folder]/continuation_state.json
2. Read existing report: [file_path from state]
3. Read the LAST 3 completed sections for flow/style
4. Load research context: themes, narrative arc, writing style
5. Load the source registry from state.artifacts.sources_path — use stable
   source_ids; assign display numbers via citation_manager.py
6. Maintain quality metrics (avg words, citation density, prose ratio)

YOUR TASK:
Generate the next batch (stay under ~6,000 words total):
[List next_sections from state]

Append each section to [file_path] using the obsidian-research MCP write tool
in append mode: mcp__obsidian_research__write_note(path=[vault-relative path],
mode="append", content=...)

QUALITY GATES:
- Words per section: within +/-20% of avg_words_per_finding
- Citation density: match +/-0.5 per 1K words
- Prose ratio: maintain >=80%
- Theme alignment: each section ties to key_themes

When done, update continuation_state.json (via terminal or file tools — it is
NOT a markdown note, so MCP note tools do not apply) and report:
- sections written
- updated word count
- whether another continuation is needed
"""
)
```

The parent then verifies the appended sections (spot-check word counts and citation
numbers) before deciding whether to continue or finalize.

---

## Option B: Continuation via fresh session

1. Current session: write/update `continuation_state.json`, then tell the user:
   ```
   Report paused at N sections (X words). To continue, run:
   hermes chat -q "Continue the deep-research report at [folder]. State file:
   [folder]/continuation_state.json. Follow reference/continuation.md."
   ```
   (Or start a new TUI session and say the same thing — the skill auto-loads on the
   phrase "continue deep research".)

2. New session (with this skill loaded): read the state file, follow the same
   context-loading and per-section protocol as Option A, and repeat until done.

This works identically from cron: schedule the continuation as a one-shot cronjob if
the report should finish unattended overnight.

---

## Continuation Quality Protocol

### Context Loading (CRITICAL)

1. Read continuation_state.json -> load ALL context
2. Read existing report file -> review last 3 sections
3. Extract patterns:
   - Sentence structure complexity
   - Technical terminology used
   - Citation placement patterns
   - Paragraph transition style

### Pre-Generation Checklist

- [ ] Loaded research context (themes, question, narrative arc)
- [ ] Reviewed previous sections for flow
- [ ] Loaded source registry from artifacts (stable source_ids, not citation numbers)
- [ ] Loaded quality targets (words, density, style)
- [ ] Understand narrative position (beginning/middle/end)

### Per-Section Generation

1. Generate section content
2. Quality checks:
   - Word count within +/-20%
   - Citation density matches
   - Prose ratio >=80%
   - Theme connection verified
   - Style consistent
3. If ANY fails: regenerate
4. If passes: append to file (via obsidian-research MCP, `mode="append"`), update state

### Handoff Decision

Calculate: current words + remaining sections x avg_words_per_section
- If total < ~18K: generate all + finish
- If total > ~18K: generate partial, update state, continue via Option A or B

### Final Continuation Responsibilities

- Generate final content sections
- Generate COMPLETE bibliography (also written to `bibliography.md`)
- Generate the grimoire-ready `artifacts/` entries for any sources not yet extracted
- Read the entire assembled report
- Run validation: `python scripts/validate_report.py --report [path]` and
  `python scripts/verify_citations.py --report [path]`
- Delete continuation_state.json (cleanup)
- Deliver per the delivery contract in SKILL.md (in-chat summary + MEDIA: path)

---

## User Communication

After each continuation batch:
```
Report Generation: Part N Complete (M sections, X words)
Continuing in a fresh session / subagent...
   Next batch: [section list]
   Progress: [X%] complete
```
