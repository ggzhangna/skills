#!/usr/bin/env python3
"""Convert a URL or local HTML file to Markdown.

Tries `markitdown` first (cleaner output), falls back to `pandoc`.
"""
import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


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


def with_markitdown(source: str, out: str) -> bool:
    try:
        import markitdown  # noqa: F401
    except ImportError:
        return False

    cmd = [sys.executable, "-m", "markitdown", source]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[url_to_markdown] markitdown failed: {result.stderr}",
              file=sys.stderr)
        return False
    Path(out).write_text(result.stdout, encoding="utf-8")
    return True


def with_pandoc(source: str, out: str) -> bool:
    if not shutil.which("pandoc"):
        return False
    html = fetch_html(source)
    proc = subprocess.run(
        ["pandoc", "-f", "html", "-t", "gfm", "-o", out],
        input=html, text=True, check=True,
    )
    return proc.returncode == 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    if with_markitdown(args.source, args.out):
        return 0
    print("[url_to_markdown] falling back to pandoc...", file=sys.stderr)
    if with_pandoc(args.source, args.out):
        return 0

    print("[url_to_markdown] no Markdown backend available. Install one of:\n"
          "  pip install 'markitdown[all]'\n"
          "  brew install pandoc  (or apt install pandoc)",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())