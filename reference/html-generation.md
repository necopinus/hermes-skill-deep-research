# HTML Generation: McKinsey Style Report

## Design Principles

- Sharp corners (NO border-radius)
- Muted corporate colors (navy #003d5c, gray #f8f9fa)
- Ultra-compact layout
- Info-first structure
- 14px base font, compact spacing
- No decorative gradients or colors
- NO EMOJIS in final HTML

---

## Generation Steps

### Step 1: Read McKinsey Template
Load template from: `./templates/mckinsey_report_template.html`

### Step 2: Extract Key Metrics
Extract 3-4 key quantitative findings for dashboard display at top.

### Step 3: Convert MD to HTML

Use Python script (run from the skill directory):
```bash
cd ~/.hermes/skills/research/deep-research
python scripts/md_to_html.py [markdown_report_path]
```

**Script outputs two parts:**
- **Part A ({{CONTENT}}):** All sections except Bibliography
- **Part B ({{BIBLIOGRAPHY}}):** Bibliography section only

**Script handles all conversion:**
- Headers: `##` -> `<div class="section"><h2 class="section-title">`
- Headers: `###` -> `<h3 class="subsection-title">`
- Lists: Markdown bullets -> `<ul><li>` with nesting
- Tables: Markdown tables -> `<table>` with thead/tbody
- Paragraphs: Text wrapped in `<p>` tags
- Bold/italic: `**text**` -> `<strong>`, `*text*` -> `<em>`
- Citations: [N] preserved for tooltip conversion

### Step 4: Add Citation Tooltips (Optional)

Attribution Gradients - wrap each [N] citation:
```html
<span class="citation">[N]
  <span class="citation-tooltip">
    <div class="tooltip-title">[Source Title]</div>
    <div class="tooltip-source">[Author/Publisher]</div>
    <div class="tooltip-claim">
      <div class="tooltip-claim-label">Supports Claim:</div>
      [Extract sentence with this citation]
    </div>
  </span>
</span>
```
NOTE: This step is optional for speed. Basic [N] citations are sufficient.

### Step 5: Replace Template Placeholders

| Placeholder | Content |
|-------------|---------|
| {{TITLE}} | Report title (from first ## heading) |
| {{DATE}} | Generation date (YYYY-MM-DD) |
| {{SOURCE_COUNT}} | Number of unique sources |
| {{METRICS_DASHBOARD}} | Metrics HTML from step 2 |
| {{CONTENT}} | HTML from Part A |
| {{BIBLIOGRAPHY}} | HTML from Part B |

### Step 6: Verify HTML

```bash
python scripts/verify_html.py --html [html_path] --md [md_path]
```
- Pass: Proceed to open
- Fail: Fix errors and re-run

### Step 7: Deliver

Do NOT open the HTML in a browser. Report the file path to the user and, in gateway
sessions, attach it with a `MEDIA:` line (see the Delivery Contract in SKILL.md).

---

## PDF Generation

**Option A: Pandoc → LaTeX (Preferred when `pandoc` + a LaTeX engine are installed)**

Pandoc converts the report Markdown directly to PDF (via `xelatex` by default here),
so tables, headings, bold/italic, and citation lists are handled by a real parser —
no hand-rolled Markdown conversion and no intermediate HTML to keep in sync. Use it
when available:

```bash
pandoc [report].md -o [report].pdf --pdf-engine=xelatex \
  -V geometry:margin=2.2cm -V fontsize=10pt -V colorlinks=true
```

Then **verify text layer (mandatory):** `python scripts/verify_pdf_text.py --pdf [pdf_path]`
— must PASS before delivery (see quality-gates.md). Pandoc/LaTeX output typically has
a clean text layer.

**Option B: WeasyPrint Direct**

1. Create print-optimized HTML following `./reference/weasyprint_guidelines.md`
2. Critical CSS:
   - `page-break-inside: avoid` on tables, boxes
   - `page-break-after: avoid` on headings
   - `orphans: 3; widows: 3` on paragraphs
   - Use `display: table` not Flexbox/Grid
   - Font sizes in pt (10pt body, 8pt citations)
   - **NO negative or tight `letter-spacing`** — it fuses words in the text layer
3. Generate: `weasyprint [html_path] [pdf_path]`
4. **Verify text layer (mandatory):** `python scripts/verify_pdf_text.py --pdf [pdf_path]`
   — must PASS before delivery. On FAIL, fix the HTML/CSS (letter-spacing,
   justification, white-space) and regenerate.
5. Deliver: report the path / attach via `MEDIA:` — never auto-open

**Note on `md_to_html.py`:** that script prints CONTENT/BIBLIOGRAPHY HTML fragments to
stdout for the McKinsey *HTML* template above; it is NOT a full PDF pipeline. For a
standalone PDF, prefer Option A (Pandoc) or drive WeasyPrint from a complete,
print-optimized HTML document you assemble yourself (do not rely on `md_to_html.py`
stdout as the PDF source).

**Engine choice is not a text-layer fix.** Both engines produce clean text when the
source is well-formed; both can flag legitimate compound words. If `verify_pdf_text.py`
FAILs, suspect the detector's compound whitelist or a line-wrapped bibliography URL
before suspecting the PDF engine.
