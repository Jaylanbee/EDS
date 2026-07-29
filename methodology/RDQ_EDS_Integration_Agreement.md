# RDQ & EDS 雙系統協同開發與資料契約 (Integration & Data Contract)

**To:** RDQ-Learn-Student 開發團隊
**From:** EDS (Educational Decision System) 開發團隊
**Date:** 2026-07-28

收到貴團隊的《雙系統協同開發協議》。我們完全同意貴方提出的系統邊界與職責劃分。RDQ 作為「上游探勘兵」負責每日檢傷分類，EDS 作為「下游決策引擎」負責高強度實戰排程，此架構將完美補足 EDS 目前在「Engine 5 (Adaptive Engine)」缺乏個人化動態資料的缺口。

為了確保雙方平行開發順利，我們在此提出 EDS 對於交接檔案 `review_index.db` 的**資料契約（Data Contract）要求**。

---

## 一、 EDS 邊界確認與承諾
1. **完全依賴 RDQ 的動態輸入**：EDS 將不再內建評測功能，我們承諾直接讀取 RDQ 產出的 `review_index.db` 作為演算法中「個人目前能力 (Current Capability)」的唯一輸入來源。
2. **專注於決策與排程**：EDS 將專注於利用 RDQ 傳來的弱點標籤，結合 EDS 內建的歷屆試題權重，計算出「投資報酬率 (ROI)」與「優先順序 (Priority Score)」，產出最終的「決勝圖譜」。

---

## 二、 資料契約 (Data Contract)：`review_index.db` 規格要求

為了讓 EDS 能將學生的弱點精準對應到我們的「知識矩陣」與「歷屆試題資料庫」，我們需要 RDQ 在 `review_index.db` (建議採用 SQLite 或標準 JSON/CSV 格式) 中，至少提供以下欄位（Schema）：

### 核心資料表：`student_weakness_log`
| 欄位名稱 (Field) | 資料型態 | 必填 | 說明與 EDS 的用途 |
|-----------------|---------|------|----------------|
| `student_id` | String | 是 | 學生識別碼（未來若支援多帳號時備用）。 |
| `timestamp` | Datetime| 是 | RDQ 記錄此弱點的時間。EDS 會藉此給予「近期弱點」較高的權重。 |
| `x_axis_code` | String | 是 | **【最重要】** 對應 EDS 知識矩陣的代碼（如 `Bc-Ⅳ-3`）。EDS 必須靠此代碼與歷屆試題庫 JOIN，計算 ROI。若無此代碼，EDS 無法運作。 |
| `mastery_level` | Float | 是 | 學生對此知識點的掌握度（建議範圍：0.0 ~ 1.0 或 0~100）。EDS 將用此數值反向調整 Priority Score，越低分排程越優先。 |
| `error_type` | String | 否 | RDQ 探勘出的失分原因（如：`概念錯誤`、`計算錯誤`、`圖表判讀`）。若能提供，EDS 產出決勝圖譜時可直接加上對應的「防呆警告」。 |
| `misconception` | String | 否 | 具體的迷思概念文字敘述。供 EDS 輸出時提醒學生用。 |

### 協定要求：
1. **SSOT (Single Source of Truth) 共識**：RDQ 在寫入 `x_axis_code` 時，必須**絕對遵守** EDS 提供的《知識矩陣》代碼表，不可自行創設新代碼，否則系統將無法對接。
2. **交接機制**：雙方確認 `review_index.db` 的存放路徑與更新頻率。EDS 將於每次使用者觸發「生成圖譜」時，即時讀取該檔案之最新狀態。

---

## 三、 開發推進下一步
若 RDQ 團隊同意上述資料契約，我們將在 EDS 的 `src/analyzer.py` 中新增 `AdaptiveEngine` 模組，專門用來解析貴團隊產出的 `review_index.db`，並將其數值動態混入目前的 ROI 演算法中。

期待雙方的系統對接，共同打造出無懈可擊的學習閉環！