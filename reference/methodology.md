# Deep Research Methodology: 8-Phase Pipeline

## Overview

This document contains the detailed methodology for conducting deep research. The 8 phases
represent a comprehensive approach to gathering, verifying, and synthesizing information
from multiple sources.

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
execution for maximum speed

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

#### Rung 3: Exa MCP — semantic/neural search and gap-filling

```
mcp__exa__web_search_exa(query="<semantically rich description of ideal page>", numResults=10)
```

- Exa's strength is semantic retrieval: describe the *ideal page*, not keywords
  ("blog post comparing X and Y performance", not "X vs Y").
- Use alongside Kagi for coverage, and specifically to fill gaps Kagi left:
  alternative perspectives, academic treatments, older foundational sources.
- For full content of known URLs: `mcp__exa__web_fetch_exa(urls=[...])` (batch up to
  several URLs in one call).

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
4. **Academic sources** - Papers, formal analysis (Kagi `lens_id: 2`, Exa with
   paper-oriented queries, or the arxiv skill)
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
- mcp__exa__web_search_exa(query="technical deep-dive explaining why quantum error correction is hard", numResults=10)
- mcp__exa__web_search_exa(query="critical analysis of quantum computing hype and failure modes", numResults=10)
```

**Step 2: Spawn parallel deep-dive subagents (Deep/UltraDeep, optional in Standard)**

Use `delegate_task` (batch mode, up to 3 concurrent) for multi-step investigations:

- Academic paper analysis (PDFs, detailed extraction)
- Documentation deep dives (technical specs, API docs)
- Repository analysis (code examples, implementations)
- Specialized domain research

```
delegate_task(tasks=[
  {"goal": "Analyze [papers list] and extract key findings with exact quotes + URLs",
   "context": "Return structured evidence JSON, not prose. Research question: ..."},
  {"goal": "...", "context": "..."}
])
```

**Subagent output format:** Require all subagents to return structured evidence, not
free text:

```json
{"claim": "specific claim text", "evidence_quote": "exact quote from source",
 "source_url": "https://...", "source_title": "...", "confidence": 0.85}
```

This prevents synthesis fatigue when merging results from multiple agents. Note that
subagents do NOT share your conversation context — pass everything they need in the
`context` field, and require them to return URLs/paths you can verify yourself.

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
subagents and claim-support verification the full evidence trail.

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
- Kagi MCP for web search (primary), Exa MCP for semantic/gap-filling
- Kagi extract / Exa fetch for full page content
- `web_search` (built-in) as last-resort fallback if both MCPs fail
- `delegate_task` for parallel deep-dive subagents
- `execute_code` for computational analysis (when needed)

**Output:** Organized information repository with source tracking, credibility scores,
and coverage map

---

## Phase 4: TRIANGULATE - Cross-Reference Verification

**Objective:** Validate information across multiple independent sources

**Activities:**
1. Identify claims requiring verification
2. Cross-reference facts across 3+ sources
3. Flag contradictions or uncertainties
4. Assess source credibility
5. Note consensus vs. debate areas
6. Document verification status per claim

**Quality Standards:**
- Core claims must have 3+ independent sources
- Flag any single-source information
- Note recency of information
- Identify potential biases

**Output:** Verified fact base with confidence levels

---

## Phase 4.5: OUTLINE REFINEMENT - Dynamic Evolution

**Objective:** Adapt research direction based on evidence discovered

**Problem Solved:** Prevents "locked-in" research when evidence points to different
conclusions or uncovers more important angles than initially planned.

**When to Execute:**
- **Standard/Deep/UltraDeep modes only** (Quick mode skips this)
- After Phase 4 (TRIANGULATE) completes
- Before Phase 5 (SYNTHESIZE)

**Activities:**

1. **Review Initial Scope vs. Actual Findings**
   - Compare Phase 1 scope with Phase 3-4 discoveries
   - Identify unexpected patterns or contradictions
   - Note underexplored angles that emerged as critical
   - Flag overexplored areas that proved less important

2. **Evaluate Outline Adaptation Need**

   **Signals for adaptation (ANY triggers refinement):**
   - Major findings contradict initial assumptions
   - Evidence reveals more important angle than originally scoped
   - Critical subtopic emerged that wasn't in original plan
   - Original research question was too broad/narrow based on evidence
   - Sources consistently discuss aspects not in initial outline

   **Signals to keep current outline:**
   - Evidence aligns with initial scope
   - All key angles adequately covered
   - No major gaps or surprises

3. **Refine Outline (if needed)**

   **Update structure to reflect evidence:**
   - Add sections for unexpected but important findings
   - Demote/remove sections with insufficient evidence
   - Reorder sections based on evidence strength and importance
   - Adjust scope boundaries based on what's actually discoverable

   **Example adaptation:**
   ```
   Original outline:
   1. Introduction
   2. Technical Architecture
   3. Performance Benchmarks
   4. Conclusion

   Refined after Phase 4 (evidence revealed security as critical):
   1. Introduction
   2. Technical Architecture
   3. **Security Vulnerabilities (NEW - major finding)**
   4. Performance Benchmarks (demoted - less critical than expected)
   5. **Real-World Failure Modes (NEW - pattern emerged)**
   6. Synthesis & Recommendations
   ```

4. **Targeted Gap Filling (if major gaps found)**

   If outline refinement reveals critical knowledge gaps:
   - Launch 2-3 targeted searches for newly identified angles
   - Quick retrieval only (don't restart full Phase 3)
   - Time-box to 2-5 minutes
   - Update triangulation for new evidence only

5. **Document Adaptation Rationale**

   Record in methodology appendix:
   - What changed in outline
   - Why it changed (evidence-driven reasons)
   - What additional research was conducted (if any)

**Quality Standards:**
- Adaptation must be evidence-driven (cite specific sources that prompted change)
- No more than 50% outline restructuring (if more needed, scope was severely mis-scoped)
- Retain original research question core (don't drift into different topic entirely)
- New sections must have supporting evidence already gathered

**Output:** Refined outline that accurately reflects evidence landscape, ready for synthesis

**Anti-Pattern Warning:**
- DON'T adapt outline based on speculation or "what would be interesting"
- DON'T add sections without supporting evidence already in hand
- DON'T completely abandon original research question
- DO adapt when evidence clearly indicates better structure
- DO document rationale for changes
- DO stay within original topic scope

---

## Phase 5: SYNTHESIZE - Deep Analysis

**Objective:** Connect insights and generate novel understanding

**Activities:**
1. Identify patterns across sources
2. Map relationships between concepts
3. Generate insights beyond source material
4. Create conceptual frameworks
5. Build argument structures
6. Develop evidence hierarchies

**Reasoning:** Use extended reasoning (`/reasoning high` if the session supports it) to
explore non-obvious connections and second-order implications.

**Output:** Synthesized understanding with insight generation

---

## Phase 6: CRITIQUE - Quality Assurance

**Objective:** Rigorously evaluate research quality

**Activities:**
1. Review for logical consistency
2. Check citation completeness
3. Identify gaps or weaknesses
4. Assess balance and objectivity
5. Verify claims against sources
6. Test alternative interpretations

**Red Team Questions:**
- What's missing?
- What could be wrong?
- What alternative explanations exist?
- What biases might be present?
- What counterfactuals should be considered?

**Persona-Based Critique (Deep/UltraDeep only):**
Simulate 2-3 specific critic personas relevant to the topic:
- "Skeptical Practitioner" — Would someone doing this daily trust these findings?
- "Adversarial Reviewer" — What would a peer reviewer reject?
- "Implementation Engineer" — Can these recommendations actually be executed?

For high-stakes topics, delegate one persona to a subagent (`delegate_task`) with the
draft findings as context — a fresh context with no sunk-cost in the research produces
sharper criticism.

**Critical Gap Loop-Back:**
If critique identifies a critical knowledge gap (not just a writing issue), return to
Phase 3 with targeted "delta-queries" before proceeding to Phase 7. Time-box to 3-5
minutes. This prevents publishing reports with known blind spots.

**Output:** Critique report with improvement recommendations

---

## Phase 7: REFINE - Iterative Improvement

**Objective:** Address gaps and strengthen weak areas

**Activities:**
1. Conduct additional research for gaps
2. Strengthen weak arguments
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
5. Compile full bibliography
6. Add methodology appendix
7. Prepare grimoire-ready artifacts (see report-assembly.md)
8. Deliver in chat (never auto-open a browser)

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

Subagent results are self-reports — for anything load-bearing (a quoted statistic, a
claimed URL), spot-verify with a direct fetch before it goes in the report.

### Adaptive Depth Control

Automatically adjust research depth based on:
- Information complexity
- Source availability
- Time constraints
- Confidence levels

### Citation Intelligence

Smart citation management:
- Track provenance of every claim
- Link to original sources (grimoire hits traced to their `source_url:`)
- Assess source credibility
- Handle conflicting sources
- Generate proper bibliographies
