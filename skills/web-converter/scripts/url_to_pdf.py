#!/usr/bin/env python3
"""Render a URL or local HTML file to PDF using headless Chromium (Playwright).

Falls back to `wkhtmltopdf` and `chrome --headless` if Playwright isn't available.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def with_playwright(source: str, out: str) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[url_to_pdf] playwright not installed; "
              "try: pip install playwright && playwright install chromium",
              file=sys.stderr)
        return False

    if not source.startswith(("http://", "https://")):
        source = Path(source).resolve().as_uri()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(source, wait_until="networkidle", timeout=60_000)
        page.emulate_media(media="screen")
        page.pdf(
            path=out,
            format="A4",
            print_background=True,
            margin={"top": "12mm", "right": "12mm",
                    "bottom": "12mm", "left": "12mm"},
        )
        browser.close()
    return True


def with_wkhtmltopdf(source: str, out: str) -> bool:
    if not shutil.which("wkhtmltopdf"):
        return False
    cmd = ["wkhtmltopdf", "--enable-local-file-access", source, out]
    subprocess.run(cmd, check=True)
    return True


def with_chrome_headless(source: str, out: str) -> bool:
    for binary in ("google-chrome", "chromium", "chrome"):
        if shutil.which(binary):
            cmd = [binary, "--headless", "--disable-gpu",
                   f"--print-to-pdf={out}", "--no-pdf-header-footer", source]
            subprocess.run(cmd, check=True)
            return True
    return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    if with_playwright(args.source, args.out):
        return 0
    print("[url_to_pdf] falling back to wkhtmltopdf...", file=sys.stderr)
    if with_wkhtmltopdf(args.source, args.out):
        return 0
    print("[url_to_pdf] falling back to chrome --headless...", file=sys.stderr)
    if with_chrome_headless(args.source, args.out):
        return 0

    print("[url_to_pdf] no PDF backend available. Install one of:\n"
          "  pip install playwright && playwright install chromium\n"
          "  brew install --cask wkhtmltopdf  (or apt install wkhtmltopdf)\n"
          "  Google Chrome / Chromium on PATH",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())