# RDQ-Shared-Schema 規劃書 (Draft)

**Date**: 2026-07-30
**Purpose**: 作為五合一生態系 (T2N, RDQ, EDS, Exam-Mock) 的「唯一真理標準 (SSOT)」，統一管理跨系統的資料表結構、環境變數與核心設定。

---

## 一、 建議的資料夾與檔案結構

`RDQ-Shared-Schema` 專案不存放任何實體資料（如 `.db` 檔），僅存放以下配置檔：

```text
RDQ-Shared-Schema/
├── schema/
│   └── 001_create_review_index.sql    # 資料庫建表語法 (DDL)
├── config/
│   ├── .env.example                   # 生態系共用環境變數範本
│   └── constants.json                 # 狀態碼與 Enum 定義 (供各系統讀取)
├── contracts/
│   └── RDQ_EDS_Integration_Agreement.md # 雙系統交接協議 (目前在 EDS 中，建議移至此處)
└── README.md
```

---

## 二、 檔案內容詳細規範

### 1. `schema/001_create_review_index.sql`
統一規定 SQLite 的建表語法。所有系統 (RDQ 寫入、EDS 讀取) 都必須遵循此結構。

```sql
CREATE TABLE IF NOT EXISTS review_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT DEFAULT 'local_user',     -- 預留多帳號擴充空間
    item_id TEXT NOT NULL,                    -- 知識矩陣代碼 (例如: Bc-Ⅳ-3)
    status TEXT NOT NULL,                     -- 掌握狀態 (見下方常數定義)
    loss_reason TEXT,                         -- 失分原因 (見下方常數定義)
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. `config/.env.example`
所有開發者在本地端建立 `.env` 時的參考範本。

```bash
# ==========================================
# 五合一生態系共用環境變數 (Ecosystem Shared Env)
# ==========================================

# 1. 資料庫共用路徑 (SQLite)
# EDS 與 RDQ 皆讀取此變數。若無設定，預設為 ~/.education_ecosystem/review_index.db
ECOSYSTEM_DB_PATH=~/.education_ecosystem/review_index.db

# 2. 知識矩陣共用路徑
# 若未來矩陣抽出成為獨立模組，各系統可透過此路徑讀取
KNOWLEDGE_MATRIX_PATH=~/projects/EDS/knowledge-matrix

# 3. 本地 LLM API 網址 (Phase 4 預留)
# 指向 Ollama 的本機位置，供 T2N 與 Quiz Generator 使用
LOCAL_LLM_API_URL=http://localhost:11434/api/generate
```

### 3. `config/constants.json`
將所有「魔法字串 (Magic Strings)」抽離出來。未來若要新增一個「失分原因」，只需修改這個 JSON，T2N、RDQ、EDS 就能同步更新，避免程式碼寫死造成的錯誤。

```json
{
  "STATUS_CODES": {
    "confirmed": "✅ 已掌握 (EDS 不會排入優先)",
    "uncertain": "❓ 待確認 (EDS 排入 1.5 倍優先權重)",
    "clarified": "⚠️ 迷思已澄清 (EDS 排入 1.5 倍優先權重)"
  },
  "LOSS_REASONS": [
    "概念錯誤",
    "計算錯誤",
    "圖表判讀",
    "推理不足",
    "看錯題"
  ]
}
```

---

## 三、 系統協作流程

1. **架構師決策**：當總架構師決定要新增一個 `loss_reason`（例如新增「粗心大意」）。
2. **修改 Schema 庫**：架構師在 `RDQ-Shared-Schema/config/constants.json` 加上此欄位，並 Commit/Push。
3. **系統同步**：
    *   **RDQ 團隊**：拉取最新的 JSON，更新他們的提示詞與寫入邏輯。
    *   **EDS 團隊**：拉取最新的 JSON，更新 `generate_graph.py` 中的防呆提示渲染邏輯。
    *   **T2N 團隊**：拉取最新設定，更新產出測驗卷時的預設干擾選項。

透過這樣的方式，就能實現真正的微服務 (Microservices) 解耦與同步。