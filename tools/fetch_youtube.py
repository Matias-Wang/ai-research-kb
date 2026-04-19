#!/usr/bin/env python3
"""
fetch_youtube.py — 抓取 YouTube 影片字幕並儲存為 Markdown 原文檔

用法：
    python tools/fetch_youtube.py <YouTube URL> [--output raw/YYYY-MM-DD-slug.md] [--lang zh-TW]

依賴：yt-dlp（pip install yt-dlp）

輸出：包含 frontmatter + 完整字幕文字的 .md 檔，存放於 raw/
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path


def check_ytdlp() -> None:
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: 找不到 yt-dlp。請執行：pip install yt-dlp", file=sys.stderr)
        sys.exit(1)


def fetch_metadata(url: str) -> dict:
    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-download", url],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp metadata 失敗：{result.stderr.strip()}")
    data = json.loads(result.stdout)
    return {
        "title": data.get("title", "Unknown Title"),
        "channel": data.get("channel", data.get("uploader", "Unknown")),
        "upload_date": data.get("upload_date", ""),  # YYYYMMDD
        "duration": data.get("duration_string", ""),
        "url": data.get("webpage_url", url),
        "video_id": data.get("id", ""),
    }


def format_upload_date(raw: str) -> str:
    if len(raw) == 8:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def download_subtitles(url: str, lang: str, tmp_dir: str) -> str | None:
    lang_priority = [lang, "en", "zh-Hant", "zh-Hans", "zh"]

    for try_lang in lang_priority:
        for sub_flag in ["--write-sub", "--write-auto-sub"]:
            result = subprocess.run(
                [
                    "yt-dlp",
                    sub_flag,
                    "--sub-lang", try_lang,
                    "--sub-format", "vtt",
                    "--skip-download",
                    "--output", f"{tmp_dir}/subtitle",
                    url,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            vtt_files = list(Path(tmp_dir).glob("*.vtt"))
            if vtt_files:
                return str(vtt_files[0])

    return None


def vtt_to_text(vtt_path: str) -> str:
    content = Path(vtt_path).read_text(encoding="utf-8")
    lines = content.split("\n")

    text_lines = []
    prev = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}", line):
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE") or re.match(r"^\d+$", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"&amp;", "&", line)
        line = re.sub(r"&lt;", "<", line)
        line = re.sub(r"&gt;", ">", line)
        if line and line != prev:
            text_lines.append(line)
            prev = line

    return " ".join(text_lines)


def slugify(title: str, max_words: int = 5) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", title.lower())
    return "-".join(words[:max_words]) or "youtube-video"


def build_frontmatter(meta: dict) -> str:
    today = date.today().isoformat()
    upload = format_upload_date(meta["upload_date"])
    return f"""---
date: {today}
source_type: youtube
source_url: {meta['url']}
title: "{meta['title']}"
channel: "{meta['channel']}"
published: {upload}
duration: {meta['duration']}
video_id: {meta['video_id']}
tags:
  - ""  # 第一層：對應 opinions/ 子資料夾名稱，請手動填入
  - ""  # 第二層：子分類
  - ""  # 第三層：具體關鍵字
opinions_related: []
---

# {meta['title']}

- 來源：YouTube
- 影片連結：{meta['url']}
- 頻道：{meta['channel']}
- 上傳日期：{upload}
- 影片長度：{meta['duration']}

## 字幕全文

"""


def main():
    parser = argparse.ArgumentParser(description="抓取 YouTube 字幕並存為 raw/ Markdown 檔")
    parser.add_argument("url", help="YouTube 影片 URL")
    parser.add_argument("--output", "-o", help="輸出路徑（預設自動產生）")
    parser.add_argument("--lang", default="zh-TW", help="字幕語言（預設 zh-TW，失敗會回落到 en）")
    args = parser.parse_args()

    check_ytdlp()

    print(f"[fetch_youtube] 抓取影片資訊：{args.url}")
    try:
        meta = fetch_metadata(args.url)
    except (RuntimeError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[fetch_youtube] 標題：{meta['title']}")
    print(f"[fetch_youtube] 頻道：{meta['channel']}")

    with tempfile.TemporaryDirectory() as tmp:
        print(f"[fetch_youtube] 下載字幕（語言優先：{args.lang}）...")
        vtt_path = download_subtitles(args.url, args.lang, tmp)

        if not vtt_path:
            print("WARNING: 找不到任何字幕，輸出檔案將只有 frontmatter", file=sys.stderr)
            transcript = "（無字幕）"
        else:
            transcript = vtt_to_text(vtt_path)
            print(f"[fetch_youtube] 字幕長度：{len(transcript)} 字元")

    if args.output:
        output_path = Path(args.output)
    else:
        today = date.today().isoformat()
        slug = slugify(meta["title"])
        output_path = Path("raw") / f"{today}-{slug}.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = build_frontmatter(meta) + transcript
    output_path.write_text(content, encoding="utf-8")

    print(f"[fetch_youtube] 已儲存：{output_path}")
    print(f"[fetch_youtube] 請執行 verify_content.py 確認完整性")


if __name__ == "__main__":
    main()
