#!/usr/bin/env python3
"""Unified dispatcher: convert a URL or local HTML file to PDF/DOCX/MD.

Usage:
    python convert.py <source> --to <pdf|docx|md> [--out <path>]

The dispatcher picks the right backend based on the target format and
falls back gracefully when a tool is missing.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


def slugify(text: str, default: str = "output") -> str:
    text = re.sub(r"[^\w\-]+", "-", text).strip("-").lower()
    return text or default


def derive_output(source: str, target: str) -> str:
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        slug = slugify(parsed.path.rsplit("/", 1)[-1] or parsed.netloc)
    else:
        slug = Path(source).stem
    return f"{slug}.{target}"


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def have_python_pkg(pkg: str) -> bool:
    try:
        __import__(pkg)
        return True
    except ImportError:
        return False


def to_pdf(source: str, out: str) -> None:
    here = Path(__file__).parent
    cmd = [sys.executable, str(here / "url_to_pdf.py"), source, "--out", out]
    subprocess.run(cmd, check=True)


def to_md(source: str, out: str) -> None:
    here = Path(__file__).parent
    cmd = [sys.executable, str(here / "url_to_markdown.py"), source, "--out", out]
    subprocess.run(cmd, check=True)


def to_docx(source: str, out: str) -> None:
    here = Path(__file__).parent
    cmd = [sys.executable, str(here / "url_to_docx.py"), source, "--out", out]
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Convert URL/HTML to PDF/DOCX/MD")
    p.add_argument("source", help="URL (http/https) or local HTML file path")
    p.add_argument("--to", required=True, choices=["pdf", "docx", "md"],
                   help="target format")
    p.add_argument("--out", help="output file path (default: derived from source)")
    args = p.parse_args()

    out = args.out or derive_output(args.source, args.to)
    out = os.path.abspath(out)

    # ensure parent dir exists
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    print(f"[web-converter] {args.source} -> {out}", file=sys.stderr)

    dispatch = {"pdf": to_pdf, "md": to_md, "docx": to_docx}
    try:
        dispatch[args.to](args.source, out)
    except subprocess.CalledProcessError as e:
        print(f"[web-converter] conversion failed: {e}", file=sys.stderr)
        return e.returncode or 1

    if not os.path.exists(out) or os.path.getsize(out) == 0:
        print(f"[web-converter] output missing or empty: {out}", file=sys.stderr)
        return 2

    size_kb = os.path.getsize(out) / 1024
    print(f"[web-converter] OK  {out}  ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())