#!/usr/bin/env python3
"""
verify_pdf_text.py — Verify that a generated PDF extracts cleanly to text
(MarkItDown-friendly): no run-together words, no missing spaces, sane character
distribution.

Rationale: PDFs generated from HTML (WeasyPrint) can produce text layers where
words run together ("wordword") when kerning/letter-spacing is applied, or where
ligatures and hyphenation break naive extraction. Downstream consumers (like
MarkItDown, or LLM ingestion pipelines) then receive corrupted text. This script
catches those issues BEFORE delivery.

Checks:
  1. Extractability — text can be extracted at all (not a scanned image)
  2. Run-together detection — flags words > MAX_WORD_LEN chars that look like
     fused words (no internal capitals/digits, all alpha, not in a whitelist of
     long technical terms)
  3. Space-density check — the ratio of spaces to alpha chars should be within
     a sane band; too low suggests missing spaces
  4. Suspicious character check — replacement chars (U+FFFD), stray control chars
  5. Ligature/hyphenation artifacts — '­' soft hyphens, 'ﬁ'/'ﬂ' ligatures
     (acceptable if few, flagged if pervasive)

Usage:
  python scripts/verify_pdf_text.py --pdf path/to/report.pdf
  python scripts/verify_pdf_text.py --pdf report.pdf --max-word-len 45 --strict

Exit codes:
  0 = pass
  1 = fail (issues found)
  2 = error (could not extract text / file missing)

Stdlib only. Uses pypdf if available, else falls back to pdftotext CLI.
"""

import argparse
import re
import shutil
import string
import subprocess
import sys
import tempfile
from pathlib import Path

# Absolute ceiling: alpha tokens longer than this are always suspicious.
# Longest common English words top out around 20 chars ('internationalization',
# 'characteristically') — above this, a lowercase alpha token is almost always a
# fusion artifact once URLs are stripped.
HARD_MAX_WORD_LEN = 20
# Words that are legitimately long (URLs already stripped; add domain terms as needed)
LONG_WORD_WHITELIST = {
    "electroencephalography", "pneumonoultramicroscopicsilicovolcanoconiosis",
}

# Common English compound words that the fused-pair heuristic would otherwise
# flag. The heuristic asks "does this token split into two common words?" — for
# genuine compounds the answer is trivially yes (health+care, under+stand,
# with+stand, out+come...), so they are whitelisted here rather than treated as
# extraction defects. Keep lowercase. Add domain/report compounds as they appear.
COMPOUND_WHITELIST = {
    # everyday compounds
    "healthcare", "standalone", "understand", "understanding", "understood",
    "alongside", "afterthought", "aftermath", "withstand", "withstanding",
    "overcome", "overcoming", "outcome", "outcomes", "overview", "oversee",
    "undertake", "undertaking", "nonetheless", "nevertheless", "insofar",
    "heretofore", "thereafter", "thereunder", "whereafter", "hereunder",
    "framework", "frameworks", "workplace", "workflow", "workflows",
    "workforce", "benchmark", "benchmarks", "touchpoint", "touchpoints",
    "whitepaper", "whitepapers", "playbook", "playbooks", "roadmap", "roadmaps",
    "cybersecurity", "cybercriminal", "cybercriminals", "cyberattack",
    "cyberattacks", "cyberthreat", "cyberthreats", "cybercrime", "cybercrimes",
    "malware", "ransomware", "phishing", "spyware", "adware", "botnet",
    "firewall", "firewalls", "backdoor", "backdoors", "keylogger", "keyloggers",
    "spearphishing", "whitelisting", "blacklisting", "greylisting",
    "threatscape", "attackscape", "riskscape", "infosec", "opsec",
    # business / research compounds frequent in reports
    "marketplace", "marketshare", "marketplaces", "shareholding", "stakeholder",
    "stakeholders", "shareholder", "shareholders", "boardroom", "boardrooms",
    "greenfield", "brownfield", "flagship", "mainstream", "upstream",
    "downstream", "midstream", "crossborder", "crossfunctional", "longstanding",
    "widespread", "wellbeing", "offshore", "onshore", "inhouse", "onboarding",
    "offboarding", "helpdesk", "databases", "dataset", "datasets", "datapoint",
    "datapoints", "metadata", "middleware", "firmware", "hardware", "software",
    "opensource", "closedsource", "singlesource", "multisource", "singlesignon",
}
# Compact common-English set for fused-pair detection. Not exhaustive — just enough
# to recognize that "thatsuperconducting" = "that"+"superconducting" is a fusion.
COMMON_WORDS = set("""
the be to of and a in that have i it for not on with he as you do at this but his by
from they we say her she or an will my one all would there their what so up out if
about who get which go me when make can like time no just him know take people into
year your good some could them see other than then now look only come its over think
also back after use two how our work first well way even new want because any these
give day most us is are was were been has had did said each more many must before
through long where much should world still own same off too does set three states
against never under while might mr between both part general during without again
place american around however home small found thought went say part once high upon
school every don does got left number course war until always away something fact
water though public put keep house point head hand group end why asked large big
such here case week company where system program question work government night
point home water room mother area money story fact month lot right study book eye
job word business issue side kind four head far black long both little house yes
after since long provide service around friend important father sit away until power
hour game often yet line political end among ever stand bad lose however member pay
law meet car city almost include continue set later community much name five once
white least president learn real change team minute best several old kid body
information nothing ago social watch together follow parent only stop face create
already speak others read level allow add office spend door health person art sure
war history party within grow result open morning walk reason low win research girl
guy early food moment himself air teacher force offer enough both education across
although remember foot second boy maybe toward able age off policy everything love
process music including consider appear actually buy probably human wait serve
market die send expect sense build stay fall oh nation plan cut college interest
death course someone experience behind reach local kill six remain effect use yeah
suggest class control raise care perhaps late hard field else pass former sell major
sometimes require along development themselves report role better economic effort
rate strong possible heart drug show leader light voice wife whole police mind
finally pull return free military price report less according decision explain son
hope even develop view relationship carry town road drive arm true federal break
difference thank receive value international building action full model join season
society because tax director early position player agree especially record pick wear
paper special space ground form support event official whose matter everyone center
couple site end project hit base activity star table need court produce eat oil half
catch industry stock figure street image itself phone either data cover quite picture
clear practice piece land recent describe product doctor wall patient worker news
movie north live culture window chance energy summer likely realize alone damage
blood rich restaurant garden election similar ok agency page capital finger challenge
machine nor pain claim hide represent accept adult scene famous secret finally sport
board natural private anyone agent working forget currently husband operation relate
apply campaign sure worker partner serious civil quite southern art ready seek above
study book job word business issue side kind four head far black both little house yes
after since long provide service around friend important father sit away until power
research shows maintain coherent period between across within without against toward
upon during before behind beyond under over again once twice always never often
seldom hardly nearly almost quite rather fairly pretty very really truly just only
even also still yet already soon later today yesterday tomorrow tonight morning
evening afternoon tonight weekend weekday monthly yearly daily weekly hourly
""".split())
LIGATURES = ["ﬁ", "ﬂ", "ﬀ", "ﬃ", "ﬄ", "ﬅ", "ﬆ"]
SOFT_HYPHEN = "­"
REPLACEMENT_CHAR = "�"


def extract_text_with_pypdf(pdf_path: Path) -> str | None:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        return None
    reader = PdfReader(str(pdf_path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts)


def extract_text_with_pdftotext(pdf_path: Path) -> str | None:
    if not shutil.which("pdftotext"):
        return None
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), str(tmp_path)],
            capture_output=True, timeout=120,
        )
        if result.returncode != 0:
            return None
        return tmp_path.read_text(encoding="utf-8", errors="replace")
    finally:
        tmp_path.unlink(missing_ok=True)


def extract_text(pdf_path: Path) -> str:
    text = extract_text_with_pypdf(pdf_path)
    if text is None:
        text = extract_text_with_pdftotext(pdf_path)
    if text is None:
        print("ERROR: no PDF text extractor available. Install pypdf (pip install pypdf) "
              "or poppler-utils (pdftotext).", file=sys.stderr)
        sys.exit(2)
    return text


def strip_urls(text: str) -> str:
    # PDF text extraction can scatter a single bibliography URL across several
    # lines when the PDF line-wraps a long link at a hyphen/slash AND the layout
    # engine (pdftotext) emits the wrapped fragments out of reading order
    # (e.g. "...culture."\n "thinkingthehumanfactor.com/ ..."\n "https://www.re-").
    # The orphan fragment then trips the fused-word detector. Rejoin scheme and
    # host fragments before stripping.
    #
    # 1. Out-of-order wrap: pdftotext can emit the host fragment BEFORE the
    #    scheme fragment (e.g. "thinkingthehumanfactor.com/ ..." appears on an
    #    earlier line than "https://www.re-"). Rejoin by deleting the dangling
    #    scheme fragment when its host-rest already appeared; then the generic
    #    URL strip removes the host. Match "scheme+host-prefix-" at end of a
    #    line that is immediately followed (after a blank line) by a new "[N]"
    #    bibliography entry or end-of-text — i.e. an orphaned scheme stub.
    text = re.sub(r"https?://[A-Za-z0-9.-]*?-\s*(?=\n\s*\n\s*\[\d+\])", " ", text)
    text = re.sub(r"https?://[A-Za-z0-9.-]*?-\s*$", " ", text)
    # 1b. In-order variant: scheme+partial-host, blank line, then host-rest.
    text = re.sub(r"(https?://[A-Za-z0-9.-]*?)\s*\n\s*\n\s*([A-Za-z0-9-]+(?:\.[A-Za-z]{2,})+\S*)",
                  r"\1\2", text)
    # 2. Rejoin in-order wraps: "https://…re-\nthinkingthehumanfactor.com/".
    text = re.sub(r"(https?://\S*?)[-/]\s*\n\s*(\S+)", r"\1\2", text)
    # 3. Collapse any remaining intra-URL newline.
    text = re.sub(r"(https?://[^\s]+)\n([^\s]+)", r"\1\2", text)
    return re.sub(r"https?://\S+|www\.\S+", " ", text)


def looks_fused(token: str) -> bool:
    """True if an all-lowercase alpha token looks like two common words fused.

    Requires a split point where BOTH halves are >= 4 chars and BOTH appear in
    COMMON_WORDS. This is deliberately precision-first: English morphology makes
    'common word + long fragment' splits appear inside genuine words constantly
    ('demonstrate' = 'demonst'+'rate', 'breakthroughs' = 'break'+'throughs'),
    so looser rules drown the signal in false positives. Fused pairs where one
    half is technical vocab ('thatsuperconducting') are caught instead by the
    HARD_MAX_WORD_LEN ceiling when long enough, and by the skill's spot-read
    step otherwise. Accept this trade-off; do NOT loosen to an OR rule.
    """
    low = token.lower()
    if len(low) < 9 or low in LONG_WORD_WHITELIST or low in COMPOUND_WHITELIST:
        return False
    for i in range(4, len(low) - 3):
        left, right = low[:i], low[i:]
        if len(right) < 4:
            break
        if left in COMMON_WORDS and right in COMMON_WORDS:
            return True
    return False


def check_run_together(text: str, hard_max_len: int = HARD_MAX_WORD_LEN) -> list[str]:
    """Find alpha tokens that look like fused words.

    Two signals:
      - HARD ceiling: alpha-only tokens longer than hard_max_len
      - FUSED-pair heuristic: tokens >= 9 chars that split into two common words
    """
    text = strip_urls(text)
    offenders: dict[str, int] = {}

    # Signal 1: hard length ceiling
    for token in re.findall(r"[A-Za-z]{" + str(hard_max_len + 1) + r",}", text):
        low = token.lower()
        if low in LONG_WORD_WHITELIST or low in COMPOUND_WHITELIST:
            continue
        # CamelCase / internal capitals -> legit identifier, skip
        if any(c.isupper() for c in token[1:]):
            continue
        offenders[token] = offenders.get(token, 0) + 1

    # Signal 2: fused-pair heuristic (all-lowercase tokens only, 9+ chars)
    for token in re.findall(r"[a-z]{9,}", text):
        if looks_fused(token):
            offenders[token] = offenders.get(token, 0) + 1

    return sorted(offenders, key=lambda w: -offenders[w])


def space_density(text: str) -> float:
    alpha = sum(1 for c in text if c.isalpha())
    spaces = sum(1 for c in text if c == " ")
    if alpha == 0:
        return 0.0
    return spaces / alpha


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify PDF text extraction quality (MarkItDown-friendly)")
    ap.add_argument("--pdf", required=True, help="Path to PDF file")
    ap.add_argument("--max-word-len", type=int, default=HARD_MAX_WORD_LEN,
                    help=f"Hard ceiling for alpha-only word length (default {HARD_MAX_WORD_LEN}; "
                         "tokens longer than this are always flagged)")
    ap.add_argument("--strict", action="store_true",
                    help="Reserved for future use (default behavior is already strict: "
                         "any fused-word candidate fails)")
    ap.add_argument("--lenient", action="store_true",
                    help="Only fail when > 10 unique fused-word candidates are found "
                         "(for PDFs with known-benign long tokens)")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        print(f"ERROR: file not found: {pdf_path}", file=sys.stderr)
        return 2

    text = extract_text(pdf_path)
    issues: list[str] = []

    # 1. Extractability
    visible = "".join(c for c in text if c in string.printable or c.isspace())
    if len(visible.strip()) < 100:
        issues.append(f"FAIL extractability: only {len(visible.strip())} printable chars "
                      "extracted — PDF may be image-only or text layer is broken")
        report(issues, text)
        return 1

    # 2. Run-together words
    run_together = check_run_together(text, args.max_word_len)
    threshold = 10 if args.lenient else 0
    if len(run_together) > threshold:
        sample = ", ".join(run_together[:10])
        issues.append(f"FAIL run-together words: {len(run_together)} unique fused-word "
                      f"candidates (e.g. {sample}). "
                      "Likely missing spaces in the PDF text layer.")

    # 3. Space density (normal English prose: ~0.15-0.20 spaces per alpha char)
    density = space_density(text)
    if density < 0.08:
        issues.append(f"FAIL space density: {density:.3f} spaces/alpha char "
                      "(expected >= 0.08) — text likely has missing spaces")

    # 4. Suspicious characters
    n_replacement = text.count(REPLACEMENT_CHAR)
    if n_replacement > 0:
        issues.append(f"FAIL encoding: {n_replacement} U+FFFD replacement characters found")

    # 5. Ligatures / soft hyphens (informational unless pervasive)
    n_lig = sum(text.count(l) for l in LIGATURES)
    n_soft = text.count(SOFT_HYPHEN)
    total_words = max(1, len(text.split()))
    if n_lig / total_words > 0.01:
        issues.append(f"WARN ligatures: {n_lig} ligature chars ({n_lig/total_words:.2%} of words) — "
                      "may break downstream search")
    if n_soft / total_words > 0.01:
        issues.append(f"WARN soft hyphens: {n_soft} U+00AD ({n_soft/total_words:.2%} of words)")

    report(issues, text)
    return 1 if any(i.startswith("FAIL") for i in issues) else 0


def report(issues: list[str], text: str) -> None:
    words = len(text.split())
    print(f"PDF text extraction report: {words} words extracted")
    if not issues:
        print("PASS: no run-together words, space density sane, no encoding artifacts")
        return
    for issue in issues:
        print(issue)


if __name__ == "__main__":
    sys.exit(main())
