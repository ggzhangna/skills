#!/usr/bin/env python3
"""Convert a URL or local HTML file to .docx via pandoc.

Strategy: clean Markdown -> DOCX gives much better results than HTML -> DOCX
because it strips navigation/ads. Fall back to direct HTML -> DOCX if needed.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


def need_pandoc() -> None:
    if not shutil.which("pandoc"):
        print("[url_to_docx] pandoc not found. Install with:\n"
              "  brew install pandoc  (or apt install pandoc)",
              file=sys.stderr)
        sys.exit(1)


def fetch_html(source: str) -> str:
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(
            source,
            headers={"User-Agent": "Mozilla/5.0 web-converter"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            charset = r.headers.get_content_charset() or "utf-8"
            return r.read().decode(charset, errors="replace")
    return Path(source).read_text(encoding="utf-8", errors="replace")


def via_markdown(source: str, out: str) -> bool:
    """Markitdown -> Markdown -> pandoc -> DOCX (best quality for articles)."""
    here = Path(__file__).parent
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        md_path = tmp.name
    try:
        result = subprocess.run(
            [sys.executable, str(here / "url_to_markdown.py"),
             source, "--out", md_path],
        )
        if result.returncode != 0 or Path(md_path).stat().st_size == 0:
            return False
        subprocess.run(
            ["pandoc", "-f", "gfm", "-t", "docx", md_path, "-o", out],
            check=True,
        )
        return True
    finally:
        Path(md_path).unlink(missing_ok=True)


def via_html_direct(source: str, out: str) -> bool:
    html = fetch_html(source)
    subprocess.run(
        ["pandoc", "-f", "html", "-t", "docx", "-o", out],
        input=html, text=True, check=True,
    )
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--out", required=True)
    p.add_argument("--direct", action="store_true",
                   help="skip the Markdown intermediate step")
    args = p.parse_args()

    need_pandoc()

    if not args.direct and via_markdown(args.source, args.out):
        return 0
    print("[url_to_docx] falling back to direct HTML -> DOCX...",
          file=sys.stderr)
    via_html_direct(args.source, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())