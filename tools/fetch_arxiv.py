#!/usr/bin/env python3
"""
fetch_arxiv.py — 處理 arXiv 論文或本地 PDF，呼叫 Gemini Pro API 做初步摘要

用法：
    # 從 arXiv 下載（自動抓取標題/作者/日期 metadata）
    python tools/fetch_arxiv.py <arXiv URL 或 ID> [--output raw/YYYY-MM-DD-slug.md]

    # 使用本地 PDF（metadata 需手動補充或用 --title / --authors）
    python tools/fetch_arxiv.py --file /path/to/paper.pdf [--title "..." --authors "..."]

環境變數：
    GEMINI_API_KEY — 必須設定，否則腳本拒絕執行

輸出：包含 frontmatter + Gemini 初步摘要的 .md 檔，存放於 raw/
後續由 Claude 結合人類觀點完成 card/
"""

import argparse
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 缺少依賴套件。請執行：pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: 缺少 Gemini SDK。請執行：pip install google-generativeai", file=sys.stderr)
    sys.exit(1)

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: 缺少 PyMuPDF。請執行：pip install pymupdf", file=sys.stderr)
    sys.exit(1)


ARXIV_API = "https://export.arxiv.org/abs/{arxiv_id}"
ARXIV_PDF = "https://arxiv.org/pdf/{arxiv_id}.pdf"
GEMINI_MODEL = "gemini-1.5-pro"

SUMMARY_PROMPT = """你是一個 AI 研究助理。以下是一篇 arXiv 論文的全文。
請用繁體中文輸出結構化摘要，格式如下：

## 研究問題（這篇在解決什麼）
（1-2 句）

## 核心貢獻（1-3點）
1.
2.
3.

## 方法摘要
（100-200 字）

## 關鍵實驗結果（重要數字）
（列出最重要的 2-4 個數字/指標）

## 相關論文
（列出論文中引用的關鍵相關工作，3-5 篇）

---
論文全文如下：

{paper_text}
"""

LOCAL_PDF_PROMPT = """你是一個 AI 研究助理。以下是一份 PDF 文件的全文。
請用繁體中文輸出結構化摘要，格式如下：

## 文件主題（這份文件在談什麼）
（1-2 句）

## 核心重點（1-5點）
1.
2.
3.

## 內容摘要
（150-300 字，涵蓋主要論點與結論）

## 關鍵概念或術語
（列出 3-6 個重要概念，簡短說明）

## 延伸閱讀
（文件中提到的重要參考資料，若有）

---
文件全文如下：

{paper_text}
"""


def parse_arxiv_id(url_or_id: str) -> str:
    patterns = [
        r"arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)",
        r"arxiv\.org/pdf/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)",
        r"^([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)$",
    ]
    for pattern in patterns:
        m = re.search(pattern, url_or_id)
        if m:
            return m.group(1)
    raise ValueError(f"無法解析 arXiv ID：{url_or_id}")


def fetch_metadata(arxiv_id: str) -> dict:
    clean_id = re.sub(r"v\d+$", "", arxiv_id)
    api_url = f"https://export.arxiv.org/api/query?id_list={clean_id}&max_results=1"
    resp = requests.get(api_url, timeout=30)
    resp.raise_for_status()

    text = resp.text
    title = re.search(r"<title>(?!ArXiv)(.+?)</title>", text, re.DOTALL)
    authors = re.findall(r"<name>(.+?)</name>", text)
    published = re.search(r"<published>(\d{4}-\d{2}-\d{2})", text)

    return {
        "title": title.group(1).strip().replace("\n", " ") if title else "Unknown Title",
        "authors": ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
        "published": published.group(1) if published else date.today().isoformat(),
    }


def download_pdf(arxiv_id: str, dest: Path) -> None:
    pdf_url = ARXIV_PDF.format(arxiv_id=arxiv_id)
    print(f"[fetch_arxiv] 下載 PDF：{pdf_url}")
    resp = requests.get(pdf_url, timeout=120, stream=True)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"[fetch_arxiv] PDF 已儲存：{dest} ({dest.stat().st_size // 1024} KB)")


def pdf_to_text(pdf_path: Path, max_chars: int = 80000) -> str:
    doc = fitz.open(str(pdf_path))
    pages = []
    total = 0
    for page in doc:
        text = page.get_text()
        pages.append(text)
        total += len(text)
        if total >= max_chars:
            break
    doc.close()
    full = "\n".join(pages)
    if len(full) > max_chars:
        full = full[:max_chars] + "\n\n[... 超過字數上限，已截斷 ...]"
    return full


def extract_pdf_metadata(pdf_path: Path) -> dict:
    doc = fitz.open(str(pdf_path))
    meta = doc.metadata
    doc.close()
    title = (meta.get("title") or "").strip() or pdf_path.stem
    author = (meta.get("author") or "").strip() or "（請手動填入）"
    return {"title": title, "authors": author}


def call_gemini(paper_text: str, api_key: str, prompt_template: str = SUMMARY_PROMPT) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = prompt_template.format(paper_text=paper_text)
    print(f"[fetch_arxiv] 呼叫 Gemini API（{GEMINI_MODEL}）...")
    response = model.generate_content(prompt)
    return response.text


def slugify(title: str, max_words: int = 5) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", title.lower())
    return "-".join(words[:max_words]) or "arxiv-paper"


def build_frontmatter_arxiv(arxiv_id: str, meta: dict) -> str:
    today = date.today().isoformat()
    url = f"https://arxiv.org/abs/{arxiv_id}"
    return f"""---
date: {today}
source_type: arxiv
source_url: {url}
title: "{meta['title']}"
authors: "{meta['authors']}"
published: {meta['published']}
arxiv_id: {arxiv_id}
tags:
  - ""  # 第一層：對應 opinions/ 子資料夾名稱，請手動填入
  - ""  # 第二層：子分類
  - ""  # 第三層：具體技術關鍵字
opinions_related: []
---

# {meta['title']}

- 來源：arXiv
- 論文連結：{url}
- 發表日期：{meta['published']}
- 機構/作者：{meta['authors']}

"""


def build_frontmatter_local(pdf_path: Path, meta: dict) -> str:
    today = date.today().isoformat()
    return f"""---
date: {today}
source_type: pdf
source_url: local
local_file: "{pdf_path.name}"
title: "{meta['title']}"
authors: "{meta['authors']}"
published: {meta['published']}
tags:
  - ""  # 第一層：對應 opinions/ 子資料夾名稱，請手動填入
  - ""  # 第二層：子分類
  - ""  # 第三層：具體技術關鍵字
opinions_related: []
---

# {meta['title']}

- 來源：本地 PDF
- 檔案：{pdf_path.name}
- 作者：{meta['authors']}

"""


def main():
    parser = argparse.ArgumentParser(description="處理 arXiv 論文或本地 PDF，用 Gemini 產生摘要")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("arxiv", nargs="?", help="arXiv URL 或 ID（例如 2106.09685）")
    group.add_argument("--file", "-f", help="本地 PDF 檔案路徑")
    parser.add_argument("--output", "-o", help="輸出路徑（預設自動產生）")
    parser.add_argument("--title", help="手動指定標題（本地 PDF 用）")
    parser.add_argument("--authors", help="手動指定作者（本地 PDF 用）")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: 未設定環境變數 GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)

    if args.file:
        # 本地 PDF 模式
        pdf_path = Path(args.file)
        if not pdf_path.exists():
            print(f"ERROR: 找不到檔案：{pdf_path}", file=sys.stderr)
            sys.exit(1)

        print(f"[fetch_arxiv] 本地 PDF：{pdf_path}")
        paper_text = pdf_to_text(pdf_path)
        print(f"[fetch_arxiv] 擷取文字：{len(paper_text)} 字元")

        pdf_meta = extract_pdf_metadata(pdf_path)
        title = args.title or pdf_meta["title"]
        authors = args.authors or pdf_meta["authors"]
        print(f"[fetch_arxiv] 標題（PDF metadata）：{title}")
        print(f"[fetch_arxiv] 作者（PDF metadata）：{authors}")
        meta = {
            "title": title,
            "authors": authors,
            "published": date.today().isoformat(),
        }

        gemini_summary = call_gemini(paper_text, api_key, prompt_template=LOCAL_PDF_PROMPT)

        if args.output:
            output_path = Path(args.output)
        else:
            today = date.today().isoformat()
            slug = slugify(title)
            output_path = Path("raw") / f"{today}-{slug}.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = build_frontmatter_local(pdf_path, meta) + gemini_summary

    else:
        # arXiv 下載模式
        try:
            arxiv_id = parse_arxiv_id(args.arxiv)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        print(f"[fetch_arxiv] arXiv ID：{arxiv_id}")

        meta = fetch_metadata(arxiv_id)
        print(f"[fetch_arxiv] 標題：{meta['title']}")
        print(f"[fetch_arxiv] 作者：{meta['authors']}")

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / f"{arxiv_id.replace('/', '_')}.pdf"
            download_pdf(arxiv_id, pdf_path)
            paper_text = pdf_to_text(pdf_path)

        print(f"[fetch_arxiv] 擷取文字：{len(paper_text)} 字元")

        gemini_summary = call_gemini(paper_text, api_key)

        if args.output:
            output_path = Path(args.output)
        else:
            today = date.today().isoformat()
            slug = slugify(meta["title"])
            output_path = Path("raw") / f"{today}-{slug}.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = build_frontmatter_arxiv(arxiv_id, meta) + gemini_summary

    output_path.write_text(content, encoding="utf-8")
    print(f"[fetch_arxiv] 已儲存：{output_path}")
    print(f"[fetch_arxiv] 請執行 verify_content.py 確認完整性")


if __name__ == "__main__":
    main()
