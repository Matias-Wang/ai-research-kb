#!/usr/bin/env python3
"""
verify_content.py — 驗證抓取內容的完整性

用法：
    python tools/verify_content.py <檔案路徑> [<檔案路徑> ...]
    python tools/verify_content.py raw/*.md

檢查項目：
    1. frontmatter 存在且格式正確（YAML 頭尾 ---）
    2. 必要欄位存在（date, source_type, source_url, title, tags）
    3. 內文長度符合來源類型最低要求
    4. 開頭與結尾有實質內容（非全空白）
    5. 無常見抓取失敗特徵（403/404 頁面、JavaScript Required 等）

結果：
    PASS — 全部通過
    WARN — 有警告但不阻斷
    FAIL — 有錯誤，此檔案不應進入知識庫
"""

import re
import sys
from pathlib import Path


MIN_BODY_CHARS = {
    "arxiv": 500,
    "blog": 300,
    "youtube": 100,
    "twitter": 50,
    "pdf": 500,
}
DEFAULT_MIN_CHARS = 200

FAILURE_PATTERNS = [
    r"403 Forbidden",
    r"404 Not Found",
    r"Access Denied",
    r"JavaScript is required",
    r"Please enable JavaScript",
    r"Enable JavaScript",
    r"This page requires JavaScript",
    r"Captcha",
    r"robot or human",
    r"verify you are a human",
]

REQUIRED_FRONTMATTER_FIELDS = ["date", "source_type", "source_url", "title", "tags"]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text

    end = text.find("---", 3)
    if end == -1:
        return {}, text

    fm_raw = text[3:end].strip()
    body = text[end + 3:].strip()

    fm = {}
    for line in fm_raw.split("\n"):
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()

    return fm, body


def check_file(path: Path) -> tuple[str, list[str], list[str]]:
    errors = []
    warnings = []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return "FAIL", [f"無法讀取檔案：{e}"], []

    if len(text.strip()) == 0:
        return "FAIL", ["檔案為空"], []

    fm, body = parse_frontmatter(text)

    if not fm:
        errors.append("缺少 frontmatter（檔案應以 --- 開頭）")
    else:
        for field in REQUIRED_FRONTMATTER_FIELDS:
            if field not in fm or not fm[field]:
                errors.append(f"frontmatter 缺少必要欄位：{field}")

        if "tags" in fm and fm["tags"] in ('""', "''", ""):
            warnings.append("tags 欄位可能尚未填入（仍是空字串）")

    source_type = fm.get("source_type", "").strip('"\'') if fm else ""
    min_chars = MIN_BODY_CHARS.get(source_type, DEFAULT_MIN_CHARS)

    body_len = len(body.strip())
    if body_len < min_chars:
        errors.append(
            f"內文過短（{body_len} 字元，來源類型 '{source_type}' 最低要求 {min_chars} 字元）"
        )

    for pattern in FAILURE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            errors.append(f"偵測到抓取失敗特徵：「{pattern}」")

    first_500 = body[:500] if body else ""
    last_500 = body[-500:] if body else ""

    if first_500.strip() == "":
        warnings.append("內文開頭 500 字元為空白")
    if last_500.strip() == "":
        warnings.append("內文結尾 500 字元為空白")

    if source_type == "arxiv":
        if not re.search(r"\d{4}\.\d{4,5}", text):
            warnings.append("arXiv 來源但未找到 arXiv ID 格式（NNNN.NNNNN）")
        if body_len < 1000:
            warnings.append(f"arXiv 論文內文偏短（{body_len} 字元），可能摘要不完整")

    if source_type == "youtube" and "（無字幕）" in text:
        warnings.append("YouTube 影片無字幕，只有 frontmatter")

    if errors:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    return status, errors, warnings


def main():
    if len(sys.argv) < 2:
        print("用法：python tools/verify_content.py <檔案路徑> [<檔案路徑> ...]")
        sys.exit(1)

    paths = [Path(p) for p in sys.argv[1:]]
    overall_fail = False
    results = []

    for path in paths:
        if not path.exists():
            results.append((path, "FAIL", [f"檔案不存在：{path}"], []))
            overall_fail = True
            continue

        status, errors, warnings = check_file(path)
        results.append((path, status, errors, warnings))
        if status == "FAIL":
            overall_fail = True

    width = max(len(str(p)) for p, *_ in results) + 2

    print("\n" + "=" * (width + 10))
    print(f"  verify_content.py — 驗證 {len(results)} 個檔案")
    print("=" * (width + 10))

    for path, status, errors, warnings in results:
        icon = {"PASS": "✓", "WARN": "!", "FAIL": "✗"}.get(status, "?")
        print(f"\n  [{icon}] {status:<4}  {path}")
        for e in errors:
            print(f"         ERROR: {e}")
        for w in warnings:
            print(f"         WARN:  {w}")

    print("\n" + "=" * (width + 10))
    pass_count = sum(1 for _, s, *_ in results if s == "PASS")
    warn_count = sum(1 for _, s, *_ in results if s == "WARN")
    fail_count = sum(1 for _, s, *_ in results if s == "FAIL")
    print(f"  結果：{pass_count} PASS  {warn_count} WARN  {fail_count} FAIL")
    print("=" * (width + 10) + "\n")

    if overall_fail:
        print("有 FAIL 的檔案不應進入知識庫，請修正後重新驗證。")
        sys.exit(1)
    else:
        print("所有檔案通過驗證。")
        sys.exit(0)


if __name__ == "__main__":
    main()
