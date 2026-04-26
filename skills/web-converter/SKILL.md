---
name: web-converter
description: "Convert any web page (URL) or local HTML file into PDF, Word (.docx), or Markdown (.md) files. Use this skill whenever the user wants to save, archive, export, download, or convert a webpage / website / online article / URL into a document. Trigger phrases include: 'turn this URL into a PDF', 'save this page as Word', 'convert this article to markdown', 'export webpage to docx', 'download this site as a document', 'archive this page', or any time the user provides an http(s):// link AND mentions .pdf / .docx / .md / Word / Markdown / document. Also trigger for local .html / .htm files being converted to those formats. Do NOT use this skill when the user wants to scrape structured data, build a webapp, or only read page contents (use a fetch tool instead)."
license: MIT
---

# Web Converter

Convert URLs or local HTML into PDF, Word (.docx), or Markdown (.md). The skill picks the right tool chain for each target format, falling back gracefully when a tool is missing.

## Quick Reference

| Target  | Primary tool          | Script                          |
|---------|-----------------------|---------------------------------|
| PDF     | Playwright (Chromium) | `scripts/url_to_pdf.py`         |
| Word    | pandoc                | `scripts/url_to_docx.py`        |
| Markdown| markitdown / pandoc   | `scripts/url_to_markdown.py`    |
| Any     | unified dispatcher    | `scripts/convert.py`            |

When in doubt, use `scripts/convert.py` — it picks the right path based on the output extension.

## When to Use

Trigger this skill when the user provides:
- A URL (`http://` / `https://`) **and** mentions a target format (PDF, Word, Markdown, .docx, .md, document, export, save).
- A local `.html` / `.htm` file with the same intent.
- Phrases like "archive this page", "save this article", "make a PDF of this site".

Do **not** trigger for:
- Pure data scraping (use HTTP fetch / parsing).
- Building a web app or component (use the `frontend-design` or `web-artifacts-builder` skill).
- Editing an existing PDF / DOCX (use the `pdf` or `docx` skill).

## Workflow

1. **Parse the request** to get:
   - source: URL or local HTML path
   - target format: pdf / docx / md (infer from the requested extension or keywords)
   - output path (default: derive from URL slug or page title)
2. **Run the unified dispatcher**:
   ```bash
   python scripts/convert.py <source> --to <pdf|docx|md> [--out <path>]
   ```
3. **Verify** the output file exists and is non-empty. Report file size and path to the user.
4. **If the primary tool fails**, fall back per the table in `references/advanced.md`.

## Tool Chain Choices (and Why)

- **PDF — Playwright/Chromium headless**: Faithfully renders JavaScript-heavy pages with full CSS, web fonts, and lazy-loaded content. `wkhtmltopdf` is a fallback but doesn't run modern JS.
- **Markdown — `markitdown`** (preferred) or **`pandoc`**: `markitdown` produces clean LLM-friendly Markdown and strips boilerplate; `pandoc` preserves more structure (tables, footnotes) but keeps more chrome.
- **DOCX — `pandoc`**: Industry-standard for HTML → DOCX. For best results, first convert to clean Markdown, then Markdown → DOCX, which strips navigation/ads.

## Installation Hints

The scripts assume one or more of these are installed. Install only what's needed:

```bash
# PDF
pip install playwright && playwright install chromium

# Markdown / cleanup
pip install 'markitdown[all]'

# DOCX (and Markdown fallback)
brew install pandoc          # macOS
# apt install pandoc         # Debian/Ubuntu
```

If a tool is missing, the dispatcher prints a clear install hint instead of failing silently.

## Examples

**Example 1 — URL to PDF**
Input: "Save https://en.wikipedia.org/wiki/Pandoc as a PDF"
Action:
```bash
python scripts/convert.py https://en.wikipedia.org/wiki/Pandoc --to pdf --out pandoc.pdf
```

**Example 2 — URL to Markdown**
Input: "Convert this blog post to markdown: https://example.com/post"
Action:
```bash
python scripts/convert.py https://example.com/post --to md --out post.md
```

**Example 3 — URL to Word**
Input: "I want this article as a .docx so I can edit it: https://example.com/article"
Action:
```bash
python scripts/convert.py https://example.com/article --to docx --out article.docx
```

**Example 4 — Local HTML**
Input: "Turn report.html into a Word file"
Action:
```bash
python scripts/convert.py ./report.html --to docx --out report.docx
```

## Output Quality Notes

- For long-form articles, prefer Markdown as an intermediate step — it strips navigation chrome before producing the final DOCX/PDF.
- For pixel-perfect screenshots of the rendered page, use PDF (it preserves layout).
- Always show the user the absolute path and size of the produced file when finished.

## Advanced & Edge Cases

For:
- Authentication / cookies
- JavaScript-heavy SPAs
- Custom page sizes / margins
- Stripping navigation, headers, ads
- Batch conversion of multiple URLs
- Embedding images locally

See `references/advanced.md`.