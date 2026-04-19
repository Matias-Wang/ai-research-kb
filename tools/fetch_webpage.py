#!/usr/bin/env python3
"""
fetch_webpage.py — 抓取一般網頁全文並儲存為 Markdown 原文檔

用法：
    python tools/fetch_webpage.py <URL> [--output raw/YYYY-MM-DD-slug.md]

輸出：包含 frontmatter 的 .md 檔案，存放於 raw/
"""

import argparse
import sys
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: 缺少依賴套件。請執行：pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

REMOVE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]


def fetch(url: str, timeout: int = 30) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    for tag in soup(REMOVE_TAGS):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main is None:
        main = soup

    lines = []
    for elem in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "blockquote"]):
        text = elem.get_text(separator=" ", strip=True)
        if not text:
            continue
        tag = elem.name
        if tag in ("h1",):
            lines.append(f"\n# {text}\n")
        elif tag in ("h2",):
            lines.append(f"\n## {text}\n")
        elif tag in ("h3",):
            lines.append(f"\n### {text}\n")
        elif tag in ("h4",):
            lines.append(f"\n#### {text}\n")
        elif tag == "blockquote":
            lines.append(f"\n> {text}\n")
        elif tag == "pre":
            lines.append(f"\n```\n{text}\n```\n")
        else:
            lines.append(text)

    body = "\n".join(lines)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return title, body


def slugify(title: str, max_words: int = 5) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", title.lower())
    return "-".join(words[:max_words]) or "article"


def build_output_path(url: str, title: str, output: str | None) -> Path:
    if output:
        return Path(output)
    today = date.today().isoformat()
    slug = slugify(title) or slugify(urlparse(url).netloc)
    return Path("raw") / f"{today}-{slug}.md"


def build_frontmatter(url: str, title: str) -> str:
    today = date.today().isoformat()
    return f"""---
date: {today}
source_type: blog
source_url: {url}
title: "{title}"
tags:
  - ""  # 第一層：對應 opinions/ 子資料夾名稱，請手動填入
  - ""  # 第二層：子分類
  - ""  # 第三層：具體關鍵字
opinions_related: []
---

"""


def main():
    parser = argparse.ArgumentParser(description="抓取網頁全文並存為 raw/ Markdown 檔")
    parser.add_argument("url", help="目標網頁 URL")
    parser.add_argument("--output", "-o", help="輸出路徑（預設自動產生）")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP 逾時秒數（預設 30）")
    args = parser.parse_args()

    print(f"[fetch_webpage] 抓取：{args.url}")

    try:
        html = fetch(args.url, timeout=args.timeout)
    except requests.RequestException as e:
        print(f"ERROR: 抓取失敗 — {e}", file=sys.stderr)
        sys.exit(1)

    title, body = extract_text(html)
    print(f"[fetch_webpage] 標題：{title}")
    print(f"[fetch_webpage] 全文長度：{len(body)} 字元")

    output_path = build_output_path(args.url, title, args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = build_frontmatter(args.url, title) + body
    output_path.write_text(content, encoding="utf-8")

    print(f"[fetch_webpage] 已儲存：{output_path}")
    print(f"[fetch_webpage] 請執行 verify_content.py 確認完整性")


if __name__ == "__main__":
    main()
