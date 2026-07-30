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
| 欄位名稱 | RDQ 承諾的輸入格式 | EDS 的應用方式 |
| :--- | :--- | :--- |
| `item_id` | **(重要)** 盡可能對應 EDS Layer 1 知識矩陣的 X 軸代碼 (如 `Bc-Ⅳ-3`)，或附帶映射屬性 `eds_x_code`。 | EDS 藉此比對知識矩陣，算出該代碼的歷屆考題投資報酬率。 |
| `status` | `confirmed` (✅掌握), `uncertain` (❓待確認), `clarified` (⚠️迷思已澄清) | EDS 應將 `uncertain` 和 `clarified` 視為高優先級的弱點打擊區，給予 Priority 權重提升。 |
| `loss_reason` | `概念錯誤`、`計算錯誤`、`圖表判讀`、`推理不足`、`看錯題`。 | EDS 依此欄位客製化防錯提示與抽題類型。 |

### 協定要求：
1. **SSOT (Single Source of Truth) 共識**：RDQ 在寫入 `item_id` 時，必須**盡可能遵守** EDS 提供的《知識矩陣》代碼表，否則 EDS 將無法比對歷屆試題資料庫以計算投資報酬率。
2. **交接機制**：雙方確認 `review_index.db` 的存放路徑與更新頻率。EDS 將於每次使用者觸發「生成圖譜」時，即時讀取該檔案之最新狀態。

---

## 三、 開發推進下一步
若 RDQ 團隊同意上述資料契約，我們將在 EDS 的 `src/analyzer.py` 中新增 `AdaptiveEngine` 模組，專門用來解析貴團隊產出的 `review_index.db`，並將其數值動態混入目前的 ROI 演算法中。

期待雙方的系統對接，共同打造出無懈可擊的學習閉環！