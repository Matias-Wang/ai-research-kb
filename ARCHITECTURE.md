# ARCHITECTURE.md

> 本文件說明 AI Research Knowledge Base 的完整技術架構、檔案格式規範、工作流程與開發狀態。
> 給 AI Agent 閱讀：接手開發前請完整閱讀本文件，再閱讀 CLAUDE.md 取得操作規則。

---

## 1. 資料夾結構

```
ai-research-kb/
│
├── README.md                        ← 專案概述（人類 + AI 皆可讀）
├── ARCHITECTURE.md                  ← 本文件，技術架構詳細說明
├── CLAUDE.md                        ← AI Agent 工作規則（每次任務前必讀）
│
├── raw/                             ← 原文全文文獻（扁平，tag 分類）
├── card/                            ← 暫時筆記卡（扁平，tag 分類）
│
├── opinions/                        ← 永久筆記（子資料夾分主題）
│   ├── INDEX.md                     ← 所有永久筆記總目錄
│   ├── MAP.mmd                      ← Mermaid 知識架構圖
│   │
│   ├── AI模型研究/
│   │   ├── 模型架構/
│   │   ├── 訓練方法/                ← Finetuning、LoRA、RLHF 等放這裡
│   │   └── 模型能力與行為/
│   │
│   ├── AI工程實作/
│   │   ├── 訓練與部署/
│   │   └── 推論優化/
│   │
│   ├── AI應用與Agent/
│   │   ├── Prompt工程/
│   │   ├── Agent設計模式/
│   │   └── RAG與記憶系統/
│   │
│   ├── AI評測/
│   │   ├── Benchmark方法論/
│   │   └── 評測工具與框架/
│   │
│   ├── AI工具生態/
│   │   ├── 模型API比較/
│   │   └── 開發框架/
│   │
│   └── AI安全與對齊/
│       ├── 對齊方法/
│       └── 安全風險與防範/
│
├── digest/                          ← 週期性知識總結
└── tools/                           ← Python 抓取與驗證腳本
    ├── fetch_webpage.py
    ├── fetch_arxiv.py
    ├── fetch_youtube.py
    └── verify_content.py
```

---

## 2. 分類設計原則

### raw/ 和 card/：扁平結構 + frontmatter tag

這兩層資料量大、更新頻繁，不用子資料夾。分類透過每個 .md 檔案的 frontmatter tag 處理。

**重要規則：frontmatter 的第一層 tag 必須對應 opinions/ 的子資料夾名稱。**
這是 AI Agent 判斷「要更新哪個永久筆記」的依據。

### opinions/：子資料夾分主題

這層才做實體資料夾分類。設計時區分兩種性質：

- **AI模型研究/**：以 arXiv 論文為主，偏理論與研究（我知道某個東西「是什麼」）
- **AI工程實作/**：以自己動手做的經驗為主（我知道某個東西「怎麼做」）

兩者不互相替代，同一個主題（例如 Finetuning）可能在兩個資料夾都有筆記。

---

## 3. 檔案命名規範

### raw/ 和 card/

```
YYYY-MM-DD-{slug}.md
```

範例：
```
2026-04-17-attention-is-all-you-need.md
2026-04-17-lora-low-rank-adaptation.md
```

slug 規則：
- 論文標題取前 3-5 個英文關鍵字，用 `-` 連接
- 中文文章用拼音或英文關鍵字描述

### opinions/

```
{主題名稱}.md
```

範例：
```
opinions/AI模型研究/訓練方法/LoRA與參數高效微調.md
opinions/AI應用與Agent/Agent設計模式/ReAct框架.md
```

---

## 4. Frontmatter 規範

### raw/ 和 card/ 共用格式

```yaml
---
date: 2026-04-17
source_type: arxiv | blog | youtube | twitter | pdf
source_url: https://...
title: 原文標題
tags:
  - AI模型研究        # 第一層：對應 opinions/ 子資料夾
  - 訓練方法          # 第二層：對應子資料夾內的分類
  - LoRA              # 第三層：具體技術關鍵字
opinions_related: [] # 更新永久筆記後，由 AI 填入對應檔案路徑
---
```

### opinions/ 格式

```yaml
---
created: 2026-04-17
updated: 2026-04-17
type: METHOD | WORKFLOW | PROJECT
related_opinions:    # 連結到其他永久筆記
  - ../AI工程實作/訓練與部署/分散式訓練.md
related_cards: []    # 來源 card 清單
---
```

---

## 5. Card 模板

### 5-1. 一般文章 / 部落格

```markdown
# {標題}

- 來源：{source_type}
- 原文連結：{url}
- 原文日期：{date}
- 主題標籤：#{tag1} #{tag2} #{tag3}

## 一句話結論（≤40字）

## 重點摘要（結合人類觀點）
1.
2.
3.

## 核心概念表格
| 概念 | 原文怎麼說 | 可以怎麼用 |
|------|-----------|----------|

## 應用情境
- 情境1：
- 情境2：

## 今天能做的下一步

## 待追問關鍵字
```

### 5-2. arXiv 論文（專用模板）

```markdown
# {論文標題}

- 來源：arXiv
- 論文連結：{url}
- 發表日期：{date}
- 機構/作者：
- 主題標籤：#{tag1} #{tag2}

## 研究問題（這篇在解決什麼）

## 核心貢獻（1-3點）
1.
2.

## 方法摘要

## 關鍵實驗結果（重要數字）

## 人類觀點與評估

## 相關論文
- [[論文A]]
- [[論文B]]
```

**偵測規則：** URL 含 `arxiv.org` → 自動使用論文模板。

---

## 6. 工具分工與 API 使用

### 主要工具

| 工具 | 用途 | 備註 |
|------|------|------|
| Claude Code | 主力 Agent，讀寫 .md、執行腳本、維護架構 | VSCode extension 或 CLI 皆可 |
| Gemini Pro API | arXiv PDF 長文件摘要 | 節省 Claude 額度，適合長文 |
| Python 腳本 | 抓取與驗證 | 存放於 tools/ |
| GitHub | 版控與備份 | 每次處理完自動 push |

### tools/ 腳本說明

| 腳本 | 功能 | 狀態 |
|------|------|------|
| fetch_webpage.py | 抓取一般網頁全文（requests + BeautifulSoup）| ✅ 已建立 |
| fetch_arxiv.py | 下載 arXiv PDF 或讀取本地 PDF → 呼叫 Gemini API 摘要 | ✅ 已建立（支援 `--file` 本地 PDF）|
| fetch_youtube.py | 抓取 YouTube 字幕（yt-dlp）| ✅ 已建立 |
| verify_content.py | 驗證抓取內容完整性（檢查頭尾）| ✅ 已建立 |

### Gemini API 整合說明

fetch_arxiv.py 的處理流程：
```
下載 PDF → 轉文字 → 呼叫 Gemini Pro API 做初步摘要 → 回傳結構化摘要給 Claude → Claude 結合人類觀點寫成 card
```

API Key 存放於環境變數 `GEMINI_API_KEY`，不寫入任何 .md 或程式碼。

---

## 7. AI Agent 工作流程

### 標準處理流程（每次收到 URL + 人類觀點）

```
1. 偵測來源類型（arxiv / blog / youtube / pdf）
2. 呼叫對應的 tools/ 腳本抓取全文
3. 執行 verify_content.py 確認完整性
4. 選擇對應模板，建立 raw/ 文件
5. 結合人類觀點，建立 card/ 文件
6. 展示 card 重點摘要（3-5點），詢問是否更新永久筆記
7. 確認後，更新 opinions/ 對應筆記
8. 同步更新 opinions/INDEX.md 和 opinions/MAP.mmd
9. git add . && git commit && git push
```

### 永久筆記更新原則

- **優先更新既有筆記**，不隨意新增
- 新增全新永久筆記前，必須取得人類同意
- 每次更新後，必須同步 INDEX.md 和 MAP.mmd
- 更新內容要整合改寫進正文，不只是補連結

### GitHub commit 格式

```
[YYYY-MM-DD] {source_type}: {標題}

範例：
[2026-04-17] arxiv: LoRA: Low-Rank Adaptation of Large Language Models
[2026-04-17] blog: Andrej Karpathy - State of GPT
```

---

## 8. 開發進度

### Phase 1：基礎建設（進行中）

| 項目 | 狀態 |
|------|------|
| 建立資料夾結構 | ⬜ 未開始 |
| 初始化 GitHub repo | ⬜ 未開始 |
| 建立 CLAUDE.md | ⬜ 未開始 |
| 建立 fetch_webpage.py | ⬜ 未開始 |
| 建立 verify_content.py | ⬜ 未開始 |
| 完成第一篇 raw → card 測試 | ⬜ 未開始 |

### Phase 2：arXiv 論文流程（未開始）

| 項目 | 狀態 |
|------|------|
| 設定 Gemini API Key | ⬜ 未開始 |
| 建立 fetch_arxiv.py | ⬜ 未開始 |
| 測試論文模板流程（5篇）| ⬜ 未開始 |

### Phase 3：永久筆記系統（未開始）

| 項目 | 狀態 |
|------|------|
| 建立各主題種子筆記 | ⬜ 未開始 |
| 建立 opinions/INDEX.md | ⬜ 未開始 |
| 建立 opinions_linker.py | ⬜ 未開始 |
| 建立 MAP.mmd 初始版本 | ⬜ 未開始 |

### Phase 4：優化與自動化（未開始）

| 項目 | 狀態 |
|------|------|
| 建立 fetch_youtube.py | ⬜ 未開始 |
| 建立 digest 週報產生流程 | ⬜ 未開始 |
| CLAUDE.md 復盤機制 | ⬜ 未開始 |

---

## 9. 給接手 AI Agent 的注意事項

1. **不要自行擴充分類結構**。opinions/ 的子資料夾新增需人類同意。

2. **arxiv 論文一定要走 Gemini API**。不要用 Claude 直接讀整份 PDF，會浪費大量 context。

3. **每次新增 card 後，必須主動提示**人類「建議更新哪些永久筆記」，不要直接改動 opinions/ 沒有詢問。

4. **CLAUDE.md 是活文件**。每次流程有改善，讓人類確認後，把新規則寫回 CLAUDE.md，不要只存在對話裡。

5. **verify_content.py 不可跳過**。抓取不完整的內容存進 raw/ 會污染整個知識庫。
