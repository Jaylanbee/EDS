import json
import os
import re
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class T2NProcessor:
    """
    Dynamic T2N Vault Reader & Adapter for EDS Cockpit.
    Dynamically binds selected Markdown notes from D:/Kid's Vault/ to their actual
    content, HTML exports, visual Mermaid mindmaps, and 108 CAP exam quizzes.
    """

    def __init__(self, vault_root: str = "D:/Kid's Vault"):
        self.vault_root = Path(vault_root)
        self.notes_dir = self.vault_root / "20_讀書筆記"
        self.html_dir = self.vault_root / "80_HTML網頁匯出"

    def get_all_vault_tags(self) -> list:
        """Task 2 API: Scans all Vault notes to extract a unique list of YAML tags."""
        tags_set = set()
        if self.notes_dir.exists():
            for md_file in self.notes_dir.rglob("*.md"):
                content = md_file.read_text(encoding="utf-8")
                # Very basic YAML frontmatter tag extraction
                frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                if frontmatter_match:
                    fm = frontmatter_match.group(1)
                    # Look for tags: \n  - tag1 \n  - tag2
                    if "tags:" in fm:
                        for line in fm.splitlines():
                            if line.strip().startswith("- ") and not line.strip().startswith("- 國中/"):
                                clean_tag = line.strip().replace("- ", "").replace("#", "").strip()
                                if clean_tag:
                                    tags_set.add(clean_tag)
        return sorted(list(tags_set))

    def search_vault_notes(self, keywords: str = None, tags: list = None, semester_filter: str = "全部範圍") -> list:
        """Task 2 API: Searches notes by keyword, multiple YAML tags, and semester."""
        base_notes = self.get_available_notes(semester_filter)
        if not (keywords or tags):
            return base_notes

        results = []
        kw_list = [k.strip().lower() for k in keywords.split()] if keywords else []

        for note_rel_path in base_notes:
            full_path = self.notes_dir / note_rel_path
            if not full_path.exists():
                continue

            content = full_path.read_text(encoding="utf-8")
            content_lower = content.lower()

            # Check tags if specified
            tag_match = True
            if tags:
                frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                fm = frontmatter_match.group(1) if frontmatter_match else ""
                for t in tags:
                    if f"- {t}" not in fm and f"#{t}" not in fm:
                        tag_match = False
                        break

            if not tag_match:
                continue

            # Check keywords if specified
            kw_match = True
            if kw_list:
                for kw in kw_list:
                    if kw not in content_lower and kw not in note_rel_path.lower():
                        kw_match = False
                        break

            if kw_match:
                results.append(note_rel_path)

        return results

    def get_available_notes(self, semester_filter: str = "全部範圍") -> list:
        """Lists available converted Markdown notes in the Vault, optionally filtered by semester."""
        if self.notes_dir.exists():
            notes = [str(f.relative_to(self.notes_dir)) for f in self.notes_dir.rglob("*.md")]
            if notes:
                sorted_notes = sorted(notes)
                if semester_filter == "全部範圍":
                    return sorted_notes

                tag_map = {
                    "七年級上學期 (1上)": ["1上", "七上", "7上"],
                    "七年級下學期 (1下)": ["1下", "七下", "7下"],
                    "八年級上學期 (2上)": ["2上", "八上", "8上"],
                    "八年級下學期 (2下)": ["2下", "八下", "8下"],
                    "九年級上學期 (3上)": ["3上", "九上", "9上"],
                    "九年級下學期 (3下)": ["3下", "九下", "9下"],
                }
                valid_tags = tag_map.get(semester_filter, [])
                filtered = [n for n in sorted_notes if any(tag in n for tag in valid_tags)]
                return filtered if filtered else sorted_notes
        return ["自然1上_L01_光合作用與能量轉換_筆記.md"]

    def clean_markdown_for_display(self, md_text: str) -> str:
        """Sanitizes Markdown text for clean display: strips all YAML frontmatter & metadata keys."""
        if not md_text:
            return ""

        # 1. Strip YAML frontmatter between --- and ---
        if md_text.startswith("---"):
            end_idx = md_text.find("---", 3)
            if end_idx != -1:
                md_text = md_text[end_idx + 3:].strip()

        # 2. Strip any residual frontmatter key-value pairs or list bullets under metadata
        lines = md_text.splitlines()
        clean_lines = []

        for line in lines:
            trimmed = line.strip()
            if any(trimmed.startswith(k) for k in [
                "created:", "tags:", "aliases:", "progress:", "spaced_repetition:",
                "r1_1day:", "r2_3days:", "r3_7days:", "r4_14days:", "r5_30days:", "review_status:"
            ]):
                continue
            if (trimmed.startswith("- 國中/") or trimmed.startswith("- 讀書筆記") or "progress: complete" in trimmed) and len(clean_lines) < 10:
                continue

            # Clean raw Obsidian callouts [!summary] -> bold title
            m_callout = re.match(r'^>\s*\[\!(summary|danger|warning|note|info|tip|abstract)\]\s*(.*)', line, re.IGNORECASE)
            if m_callout:
                ctype = m_callout.group(1).upper()
                ctitle = m_callout.group(2).strip() or ctype
                clean_title = re.sub(r'^[🎯⚠️📌📝\s]+', '', ctitle) or ctype
                icon = "🎯" if ctype == "DANGER" else ("⚠️" if ctype in ["WARNING", "SUMMARY"] else "📌")
                clean_lines.append(f"> **{icon} {clean_title}**")
                continue

            clean_lines.append(line)

        return "\n".join(clean_lines).strip()

    def load_note_markdown(self, note_identifier: str = None) -> str:
        """Reads a converted Markdown note from the Vault and sanitizes it."""
        raw_md = ""
        if note_identifier:
            target_path = self.notes_dir / note_identifier
            if target_path.exists():
                raw_md = target_path.read_text(encoding="utf-8")

        if not raw_md:
            raw_md = """# 國中自然1上_L01_光合作用與能量轉換_筆記.md
<教材出處：國中自然1上 p.35-42>

## 核心概念結構化拆解

### 光反應 (Light-Dependent Reaction) `108課綱: Bc-IV-3`
發生於葉綠體的葉綠餅 (類囊體膜)，吸收光能將水分子分割釋放氧氣，同時產生高能量分子 ATP 與 NADPH。

> [!danger] 🎯 迷思陷阱警示
> 常錯點：水分子分割發生在光反應而非暗反應！

### 碳反應/暗反應 (Carbon Fixation) `108課綱: Bc-IV-3`
發生於葉綠體基質，不直接需要光照，利用光反應提供的 ATP 與 NADPH 將二氧化碳 (CO2) 同化固定為葡萄糖與水。

> [!danger] 🎯 迷思陷阱警示
> 常錯點：暗反應在白天同樣進行，並非只在晚上運作！
"""
        return self.clean_markdown_for_display(raw_md)

    def extract_note_metadata(self, note_identifier: str = None, md_text: str = "") -> dict:
        """Extracts clean title, 108 curriculum codes, and section headers from the selected note."""
        if not md_text and note_identifier:
            md_text = self.load_note_markdown(note_identifier)

        title = "單元筆記"
        if note_identifier:
            base_name = Path(note_identifier).stem
            title = base_name.replace("_筆記", "").split("_")[-1]

        headers = []
        codes = []

        # Strictly find standard 108 curriculum codes (e.g. Bc-Ⅳ-3, Ba-Ⅳ-1, Ab-Ⅰ-1)
        found_codes = re.findall(r'`([A-Za-z]{1,2}-[I|V|X|Ⅳ|Ⅴ|Ⅵ]+-\d+)`|`108課綱:\s*([^`]+)`', md_text)
        for c1, c2 in found_codes:
            code_str = (c1 or c2).strip()
            if code_str and not code_str.startswith(">") and "命題熱力" not in code_str:
                codes.append(code_str)

        # Extract markdown headers ## H2 and ### H3
        for line in md_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("# ") and title == "單元筆記":
                clean_t = line_str.replace("# ", "").strip()
                clean_t = re.sub(r'^[🔴🟡🟢🎯\s]+', '', clean_t)
                title = clean_t
            elif line_str.startswith("## "):
                h_text = line_str.replace("## ", "").strip()
                h_text = re.sub(r'`[^`]+`', '', h_text).strip()
                if h_text and not h_text.startswith("!"):
                    headers.append({"level": 2, "text": h_text})
            elif line_str.startswith("### "):
                h_text = line_str.replace("### ", "").strip()
                h_text = re.sub(r'`[^`]+`', '', h_text).strip()
                if h_text and not h_text.startswith("!"):
                    headers.append({"level": 3, "text": h_text})

        primary_code = codes[0] if codes else title

        return {
            "title": title,
            "primary_code": primary_code,
            "all_codes": codes,
            "headers": headers
        }

    def load_note_html(self, note_identifier: str = None) -> str:
        """Reads matching HTML note if exported; returns None if not yet generated for this note."""
        if note_identifier:
            # Try exact HTML name matching
            html_name = Path(note_identifier).stem + ".html"
            target_path = self.html_dir / html_name
            if target_path.exists():
                return target_path.read_text(encoding="utf-8")

            # Try matching HTML by note stem
            stem = Path(note_identifier).stem
            matched_files = list(self.html_dir.rglob(f"*{stem}*.html")) if self.html_dir.exists() else []
            if matched_files:
                return matched_files[0].read_text(encoding="utf-8")

        # Return None if no matching HTML file exists
        return None

    def generate_mindmap(self, note_identifier: str = None, md_text: str = None) -> str:
        """Dynamically builds a Mermaid mindmap matching the SELECTED note's actual section headers."""
        if not md_text and note_identifier:
            md_text = self.load_note_markdown(note_identifier)

        meta = self.extract_note_metadata(note_identifier, md_text)
        title = meta["title"]
        headers = meta["headers"]

        if not headers:
            return None

        # Build dynamic Mermaid mindmap string
        lines = ["mindmap", f"  root(({title}))"]

        current_h2 = None
        for h in headers:
            text = h["text"].replace("(", "（").replace(")", "）")
            if h["level"] == 2:
                lines.append(f"    {text}")
                current_h2 = text
            elif h["level"] == 3:
                indent = "      " if current_h2 else "    "
                lines.append(f"{indent}{text}")

        return "\n".join(lines)

    def generate_quiz(self, eds_x_code: str = None, note_identifier: str = None, num_questions: int = 5, target_level: str = "A++") -> str:
        """Generates pop quiz using EDSExamGenerator."""
        from src.generate_eds_exam import get_pop_quiz

        if not eds_x_code and note_identifier:
            meta = self.extract_note_metadata(note_identifier)
            eds_x_code = meta["primary_code"]

        if not eds_x_code:
            eds_x_code = "Bc-Ⅳ-3"

        return get_pop_quiz(eds_x_code, note_identifier=note_identifier, num_questions=num_questions, target_level=target_level)

    def process_text(self, text_input: str, engine: str = "auto") -> dict:
        return self.simulate_llm_parsing(text_input)

    def simulate_llm_parsing(self, text_input: str = "") -> dict:
        return {
            "title": "單元筆記 (108課綱)",
            "is_out_of_matrix": False,
            "nodes": []
        }

    def render_markdown(self, json_data: dict = None) -> str:
        return self.load_note_markdown()

    def render_html_pro(self, json_data: dict = None) -> str:
        return self.load_note_html()

    def convert_rdq_db_to_vault_notes(self) -> int:
        """Reads wrong answer records from SQLite (review_index.db) and generates Obsidian wrong question notes into Vault."""
        db_path = os.getenv('ECOSYSTEM_DB_PATH', os.path.expanduser('~/.education_ecosystem/review_index.db'))
        if not os.path.exists(db_path):
            return 0

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT item_id, loss_reason, priority, updated_at FROM review_index")
        rows = c.fetchall()
        conn.close()

        count = 0
        for item_id, loss_reason, priority, updated_at in rows:
            subj_dir = self.vault_root / "40_錯題筆記" / "04_自然"
            if "math" in item_id:
                subj_dir = self.vault_root / "40_錯題筆記" / "03_數學"
            elif "chi" in item_id:
                subj_dir = self.vault_root / "40_錯題筆記" / "01_國文"
            elif "eng" in item_id:
                subj_dir = self.vault_root / "40_錯題筆記" / "02_英文"
            elif "soc" in item_id:
                subj_dir = self.vault_root / "40_錯題筆記" / "05_社會"

            subj_dir.mkdir(parents=True, exist_ok=True)
            note_filename = f"{item_id}_會考真題_{loss_reason or '觀念'}錯題.md"
            file_path = subj_dir / note_filename

            if not file_path.exists():
                content = f"""---
created: "{str(updated_at)[:10]}"
tags:
  - 錯題筆記
  - {item_id}
  - 108課綱
progress: complete
---

# 🔴 RDQ錯題連動卡 — {item_id}

> [!important] 🎯 錯題 2D 雙維度對位
> - **弱點代碼**：`{item_id}`
> - **失分原因**：`{loss_reason or '概念錯誤'}`
> - **攻堅燈號**：🔴 {priority or 'red'} 優先攻堅

---

## 📝 一、錯題原文與迷思陷阱

**題目**：來自 RDQ 對話練習或會考測驗之關鍵錯題。

> [!warning] ⚠️ 迷思陷阱分析
> 本題常錯點在於對 `{item_id}` 之定義理解不夠嚴密，容易受干擾選項影響。

---

## 🧠 二、觀念重導與解題步驟

1. **核對核心定義**：回到 108 課綱課本原文再次確認。
2. **三步推理法**：
   - Step 1: 圈出關鍵條件
   - Step 2: 排除魔王選項
   - Step 3: 推導正確解答

---

## 🔄 三、擬真二刷同型題

> [!tip] 💡 觀念鞏固二刷
> 考前務必於 EDS 駕駛艙進行同型題二刷！
"""
                file_path.write_text(content, encoding="utf-8")
                count += 1

        return count

if __name__ == "__main__":
    reader = T2NProcessor()
    notes = reader.get_available_notes()
    print("=== T2N Dynamic Note Binder Test ===")
    print("Notes:", notes)
    if notes:
        n0 = notes[0]
        print(f"\nMetadata for {n0}:", reader.extract_note_metadata(n0))
        print(f"\nDynamic Mindmap for {n0}:\n", reader.generate_mindmap(n0))
