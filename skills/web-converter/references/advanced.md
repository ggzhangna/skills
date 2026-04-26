# Advanced Usage & Edge Cases

This file is loaded only when the basic workflow in `SKILL.md` is not enough.

## Authentication / Cookies

For pages behind login, use Playwright's storage state:

```python
# 1. Run once to log in and save state
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto("https://site.example/login")
    input("Log in manually, then press Enter...")
    ctx.storage_state(path="state.json")

# 2. Reuse in scripts/url_to_pdf.py via:
#    ctx = browser.new_context(storage_state="state.json")
```

## JavaScript-Heavy SPAs

If `networkidle` triggers too early, switch to an explicit selector wait:

```python
page.goto(url)
page.wait_for_selector("article", timeout=30_000)
page.pdf(path=out, ...)
```

## Custom Page Size / Margins

In `url_to_pdf.py`, the `page.pdf(...)` call accepts:
- `format`: "A4", "Letter", "Legal", "Tabloid", etc.
- `width` / `height`: e.g. "8.5in", "297mm"
- `margin`: dict of top/right/bottom/left
- `landscape`: True/False
- `scale`: 0.1–2.0

## Stripping Navigation / Ads (Reader-Mode Output)

Best path: URL → Markdown (markitdown strips boilerplate) → DOCX/PDF.

For a PDF with reader-mode look, inject CSS before printing:

```python
page.add_style_tag(content="""
    nav, header, footer, aside, .ad, .sidebar { display: none !important; }
    article, main { max-width: 720px; margin: 0 auto; }
""")
```

## Batch Conversion

```bash
while read url; do
  slug=$(echo "$url" | sed 's|.*/||; s|[^a-zA-Z0-9]|-|g')
  python scripts/convert.py "$url" --to pdf --out "out/$slug.pdf"
done < urls.txt
```

## Embedding Images Locally

Pandoc keeps remote `<img>` URLs by default. To embed:

```bash
pandoc --extract-media=./media -f html -t docx input.html -o out.docx
```

For Markdown output with embedded base64 images, post-process with a small
script or use `pandoc --self-contained` for HTML intermediates.

## Choosing PDF Backend

| Backend         | JS support | Quality   | Install footprint  |
|-----------------|-----------|-----------|--------------------|
| Playwright      | full      | best      | ~300 MB Chromium   |
| Chrome headless | full      | best      | uses system Chrome |
| wkhtmltopdf     | legacy    | OK        | small              |

Default is Playwright. The skill scripts auto-fall-back in that order.

## Troubleshooting

- **Empty PDF / DOCX**: page likely didn't finish loading. Increase
  `timeout` or use `wait_for_selector`.
- **Garbled text**: charset detection failed. Force UTF-8 in
  `fetch_html()` or pass `--encoding utf-8` to pandoc.
- **`markitdown` produces noisy output**: try `pandoc -t gfm` instead.
- **Pandoc complains about HTML5 tags**: pre-clean with
  `pandoc -f html -t markdown | pandoc -f markdown -t docx`.