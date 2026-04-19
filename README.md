# AI Research Knowledge Base

## 專案概述

這是一個基於**卡片盒筆記法（Zettelkasten）**的 AI 輔助知識管理系統，專門用於整理 AI 研究領域的資料。

**核心理念：人只負責丟資料、給觀點、做判斷；AI Agent 負責所有抓取、整理、分類、建立連結的工作。**

人類不需要操作任何筆記軟體介面。整個系統的唯一操作方式是「與 AI Agent 對話」。

---

## 專案目標

- 自動抓取網頁文章、arXiv 論文、YouTube 影片字幕，建立可追溯的原文文獻庫
- 根據人類觀點，自動產生結構化的暫時筆記卡片
- 將反覆出現的觀點與方法，累積成愈用愈強的永久筆記
- 在永久筆記之間建立知識連結與架構圖
- 根據需求，從資料庫中提取內容產生草稿、大綱、週報

---

## 知識主題範圍

本專案聚焦 AI 研究領域，分為六大主題：

| 主題 | 內容範圍 |
|------|---------|
| AI模型研究 | arXiv 論文、模型架構（Transformer/MoE/SSM）、訓練方法（Finetuning/LoRA/RLHF）、模型能力與行為 |
| AI工程實作 | 訓練與部署、推論優化、量化、容器化 |
| AI應用與Agent | Prompt 工程、Agent 設計模式（ReAct/CoT）、RAG、記憶系統 |
| AI評測 | Benchmark 方法論、評測工具與框架 |
| AI工具生態 | 模型 API 比較（Claude/GPT/Gemini）、開發框架（LangChain/LlamaIndex）|
| AI安全與對齊 | 對齊方法、Constitutional AI、安全風險與防範 |

---

## 三層知識架構

```
原文資料（raw）→ 暫時筆記（card）→ 永久筆記（opinions）
```

- **raw/**：原文全文，不可省略、不可摘要，完整保存可追溯來源
- **card/**：每篇原文一張卡，結合人類觀點的結構化摘要
- **opinions/**：主題型永久筆記，優先更新既有筆記而非新增

---

## 工具分工

| 工具 | 角色 |
|------|------|
| Claude Code | 主力 AI Agent，負責讀寫 .md 檔、執行腳本、維護知識架構 |
| Gemini Pro API | 輔助處理 arXiv PDF 長文件摘要（節省 Claude 額度）|
| Python 腳本（tools/）| 抓取網頁、PDF、YouTube 字幕，驗證內容完整性 |
| GitHub | 版本控管與雲端備份，每次處理完自動 push |

---

## 目前進度

> **Phase 1（進行中）**：基礎建設
> - [ ] 建立資料夾結構
> - [ ] 初始化 GitHub repo
> - [ ] 建立並完善 CLAUDE.md 工作規則
> - [ ] 建立 fetch_webpage.py 和 verify_content.py
> - [ ] 完成第一篇文章的 raw → card 全流程測試

Phase 2：arXiv 論文流程（未開始）
Phase 3：永久筆記系統（未開始）
Phase 4：優化與自動化（未開始）

---

## 給 AI Agent 的快速上手指引

1. 閱讀 `CLAUDE.md`（工作規則，每次處理任務前必讀）
2. 閱讀 `ARCHITECTURE.md`（了解完整技術架構與檔案規範）
3. 閱讀 `opinions/INDEX.md`（了解目前永久筆記的全貌）
4. 閱讀 `opinions/MAP.mmd`（了解知識節點之間的連結關係）
5. 確認 `tools/` 下有哪些可用腳本

接到任務後，優先查閱上述文件再開始行動，不要自行假設規則。

---

## 相關文件

- `CLAUDE.md`：AI Agent 工作規則（必讀）
- `ARCHITECTURE.md`：完整技術架構與檔案格式規範
- `opinions/INDEX.md`：永久筆記總目錄
- `opinions/MAP.mmd`：知識架構 Mermaid 流程圖
