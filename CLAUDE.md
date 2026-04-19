# CLAUDE.md — AI Agent 工作規則

> 每次接到任務前必讀本文件。本文件是活文件，流程改善後由人類確認再更新。

---

## 0. 啟動清單

接任何任務前，依序閱讀：
1. 本文件（CLAUDE.md）
2. `ARCHITECTURE.md`（技術架構與檔案規範）
3. `opinions/INDEX.md`（永久筆記總目錄）
4. `opinions/MAP.mmd`（知識節點連結圖）
5. 確認 `tools/` 下可用腳本

---

## 1. 身分與職責

- 角色：AI Agent，負責所有抓取、整理、分類、建立連結的工作
- 人類職責：丟資料、給觀點、做判斷
- 原則：**不代替人類做判斷**，遇到需要決策的地方，先提出選項再詢問

---

## 2. 標準處理流程（收到 URL + 人類觀點）

```
1. 偵測來源類型（arxiv / blog / youtube / pdf）
2. 呼叫對應的 tools/ 腳本抓取全文
3. 執行 verify_content.py 確認完整性（不可跳過）
4. 選擇對應模板，建立 raw/ 文件
5. 結合人類觀點，建立 card/ 文件
6. 展示 card 重點摘要（3-5點），詢問是否更新永久筆記
7. 人類確認後，更新 opinions/ 對應筆記
8. 同步更新 opinions/INDEX.md 和 opinions/MAP.mmd
9. git add . && git commit && git push
```

---

## 3. 來源類型偵測規則

| 條件 | 類型 | 使用腳本 |
|------|------|---------|
| URL 含 `arxiv.org` | arxiv | fetch_arxiv.py |
| URL 含 `youtube.com` 或 `youtu.be` | youtube | fetch_youtube.py |
| 其他 HTTP/HTTPS URL | blog/web | fetch_webpage.py |
| 本地 .pdf 路徑 | pdf | fetch_arxiv.py（同流程）|

---

## 4. 檔案操作規則

### raw/ 和 card/
- 命名格式：`YYYY-MM-DD-{slug}.md`
- slug：論文標題前 3-5 個英文關鍵字，用 `-` 連接
- frontmatter 的第一層 tag 必須對應 `opinions/` 子資料夾名稱
- 建立後不得刪除，只能新增或修改

### opinions/
- **優先更新既有筆記**，不隨意新增
- 新增全新永久筆記前，必須取得人類同意
- 每次更新後，立即同步 INDEX.md 和 MAP.mmd
- 更新內容要整合改寫進正文，不只是補連結

---

## 5. arXiv 論文專用規則

- **一定要走 Gemini API**，不要用 Claude 直接讀整份 PDF
- 流程：下載 PDF → 轉文字 → 呼叫 Gemini Pro API 摘要 → 回傳結構化摘要 → Claude 結合人類觀點寫 card
- API Key 從環境變數 `GEMINI_API_KEY` 讀取，禁止寫入任何檔案

---

## 6. 永久筆記更新規則

- 每次新增 card 後，主動提示人類「建議更新哪些永久筆記」
- 直接改動 `opinions/` 前必須詢問人類確認
- 更新時整合改寫正文，並更新 `related_cards` 欄位
- 每次更新必須同步 `opinions/INDEX.md` 和 `opinions/MAP.mmd`

---

## 7. Git Commit 格式

```
[YYYY-MM-DD] {source_type}: {標題}
```

範例：
```
[2026-04-17] arxiv: LoRA: Low-Rank Adaptation of Large Language Models
[2026-04-17] blog: Andrej Karpathy - State of GPT
[2026-04-17] infra: 初始化專案結構
```

每次處理完畢後執行：`git add . && git commit && git push`

---

## 8. 禁止事項

- 禁止跳過 verify_content.py 的驗證步驟
- 禁止將 API Key 寫入任何 .md 或 .py 檔案
- 禁止未經詢問就新增 opinions/ 的子資料夾
- 禁止未經詢問就直接修改 opinions/ 的永久筆記
- 禁止自行假設規則，不確定時先詢問人類

---

## 9. 本文件更新規則

- 每次流程有改善，提出具體修改建議給人類
- 人類確認後，立即更新本文件
- 更新時保留舊規則的紀錄（可加刪除線標注），重大修改寫入 git commit message
