#!/usr/bin/env python3
"""Extract provided Office/PDF documents into heading-safe markdown for source_material/.

Usage:
  extract_office_text.py SRC [SRC ...] --out DIR [--images]

- .pptx -> <out>/<stem>.md   slide text as `## Slide N`, speaker notes as
  `### Speaker notes`, mapped per slide via ppt/slides/_rels/slideN.xml.rels
- .docx -> <out>/<stem>.md   one paragraph per blank line
- .pdf  -> <out>/<stem>.txt  pdftotext -layout
- --images -> <out>/images/<stem>/slide_NNN_* (images referenced by slide N),
  <out>/images/<stem>/_all_media/ (every ppt/media asset incl. layout/master art),
  and <out>/images/MANIFEST.md (slide -> file map)

Output markdown is heading-safe: rule-like lines under 3 chars and stray '#' content
lines are escaped, full-width rules get a blank line above them (a text line directly
above a rule would parse as a setext heading), and blank runs are collapsed. Still run
the vault's `markdownlint-cli2 --fix --no-globs` + zero-findings verify over the output
before committing — extracted prose carries other mechanical findings (--fix handles
emphasis style, list markers, etc.).
"""

import argparse
import html
import os
import re
import subprocess
import sys
import urllib.parse
import zipfile

RULE = re.compile(r"^(-+|=+)\s*$")
HEADING = re.compile(r"^#+(\s.*)?$")


def _stem(path):
    base = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base)


def _paras(xml, para_re, text_re, join_sep):
    out = []
    for p in re.findall(para_re, xml, re.S):
        runs = [html.unescape(t) for t in re.findall(text_re, p, re.S)]
        line = join_sep.join(runs)
        if line.strip():
            out.append(line.strip())
    return out


def _safe_content(lines):
    """Escape content so extracted text cannot fake headings; keep real rules as HRs."""
    out = []
    for ln in lines:
        if RULE.match(ln):
            if len(ln.strip()) < 3:
                out.append("\\" + ln)  # literal; a 1-2 char rule is a setext underline
                continue
            if out and out[-1].strip() != "":
                out.append("")  # blank above so the rule stays an HR, not an underline
            out.append(ln)
        elif HEADING.match(ln):
            out.append("\\" + ln)  # '#' glyphs in content stay text
        else:
            out.append(ln)
    final = []
    for ln in out:
        if not ln.strip() and final and not final[-1].strip():
            continue  # collapse blank runs (MD012)
        final.append(ln)
    return final


def _write(out_dir, name, lines):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    with open(path, "w") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    return path


def _notes_for_slide(z, slide_n):
    rel = f"ppt/slides/_rels/slide{slide_n}.xml.rels"
    try:
        rx = z.read(rel).decode("utf-8", "replace")
    except KeyError:
        return []
    m = re.search(r'Target="\.\./notesSlides/(notesSlide\d+\.xml)"', rx)
    if not m:
        return []
    xml = z.read(f"ppt/notesSlides/{m.group(1)}").decode("utf-8", "replace")
    return _paras(xml, r"<a:p[ >].*?</a:p>", r"<a:t>(.*?)</a:t>", " ")


def _extract_images(z, out_dir, stem, slide_nums):
    img_root = os.path.join(out_dir, "images", stem)
    all_dir = os.path.join(img_root, "_all_media")
    os.makedirs(all_dir, exist_ok=True)
    manifest_path = os.path.join(out_dir, "images", "MANIFEST.md")
    header = [] if os.path.exists(manifest_path) else [
        "# Slide images", "",
        "- `slide_NNN_*` = image referenced directly by slide N.",
        "- `_all_media/` = every media asset in the deck (incl. layout/master art).", "",
    ]
    manifest = list(header) + [f"## {stem}", ""]
    for n in slide_nums:
        rel = f"ppt/slides/_rels/slide{n}.xml.rels"
        try:
            rx = z.read(rel).decode("utf-8", "replace")
        except KeyError:
            continue
        for m in re.finditer(r'Target="([^"]*?media/([^"/]+))"', rx):
            fname = urllib.parse.unquote(m.group(2))
            ext = os.path.splitext(fname)[1]
            dest = os.path.join(img_root, f"slide_{n:03d}_{os.path.splitext(fname)[0]}{ext}")
            with open(dest, "wb") as f:
                f.write(z.read(f"ppt/media/{fname}"))
            manifest.append(f"- slide {n}: `{stem}/{os.path.basename(dest)}` "
                            f"({os.path.getsize(dest):,} bytes)")
        manifest.append("")
    for name in [x for x in z.namelist() if x.startswith("ppt/media/")]:
        with open(os.path.join(all_dir, os.path.basename(urllib.parse.unquote(name))), "wb") as f:
            f.write(z.read(name))
    with open(manifest_path, "w") as f:
        f.write("\n".join(manifest).rstrip() + "\n")


def extract_pptx(path, out_dir, images=False):
    z = zipfile.ZipFile(path)
    stem = _stem(path)
    slide_nums = sorted(
        int(re.search(r"slide(\d+)\.xml", n).group(1))
        for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n))
    lines = [f"# {os.path.basename(path)} — extracted slide text", "",
             f"_Source: `{path}` — slide text and speaker notes, "
             "extracted verbatim from the pptx._", ""]
    for n in slide_nums:
        xml = z.read(f"ppt/slides/slide{n}.xml").decode("utf-8", "replace")
        paras = _paras(xml, r"<a:p[ >].*?</a:p>", r"<a:t>(.*?)</a:t>", " ")
        lines += [f"## Slide {n}", ""]
        lines += _safe_content(paras) if paras else ["(no text on slide)"]
        notes = _notes_for_slide(z, n)
        if notes:
            lines += ["", "### Speaker notes", ""] + _safe_content(notes)
        lines.append("")
    _write(out_dir, stem + ".md", lines)
    if images:
        _extract_images(z, out_dir, stem, slide_nums)
    return f"{len(slide_nums)} slides"


def extract_docx(path, out_dir):
    z = zipfile.ZipFile(path)
    stem = _stem(path)
    xml = z.read("word/document.xml").decode("utf-8", "replace")
    paras = _paras(xml, r"<w:p[ >].*?</w:p>", r"<w:t[^>]*>(.*?)</w:t>", "")
    lines = [f"# {os.path.basename(path)} — extracted text", "",
             f"_Source: `{path}` — extracted verbatim from the docx._", ""]
    lines += _safe_content(paras)
    _write(out_dir, stem + ".md", lines)
    return f"{len(paras)} paragraphs"


def extract_pdf(path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, _stem(path) + ".txt")
    subprocess.run(["pdftotext", "-layout", path, out], check=True)
    return f"{os.path.getsize(out):,} bytes text"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("srcs", nargs="+", help="pptx/docx/pdf files (or directories containing them)")
    ap.add_argument("--out", required=True, help="output directory (e.g. <report_dir>/source_material)")
    ap.add_argument("--images", action="store_true",
                    help="also extract per-slide images + full media dump + MANIFEST.md")
    args = ap.parse_args()
    files = []
    for s in args.srcs:
        if os.path.isdir(s):
            for root, _dirs, names in os.walk(s):
                files += [os.path.join(root, n) for n in sorted(names)
                          if n.lower().endswith((".pptx", ".docx", ".pdf"))]
        else:
            files.append(s)
    if not files:
        sys.exit("no .pptx/.docx/.pdf files found")
    for path in files:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pptx":
            info = extract_pptx(path, args.out, args.images)
        elif ext == ".docx":
            info = extract_docx(path, args.out)
        else:
            info = extract_pdf(path, args.out)
        print(f"{info:>18}  {os.path.basename(path)}")


if __name__ == "__main__":
    main()
