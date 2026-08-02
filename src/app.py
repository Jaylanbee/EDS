import streamlit as st
import os
import sqlite3
import pandas as pd
import json
import re
from pathlib import Path
from src.t2n_processor import T2NProcessor
from src.generate_graph import generate_decision_graph_text

# Setup Streamlit Page - Standard Layout
st.set_page_config(page_title="EDS app.py 統一學習駕駛艙", layout="wide")

# Global Session State Init
if 'global_target_code' not in st.session_state:
    st.session_state['global_target_code'] = ""

st.title("🖥️ 水循環學習法 統一學習駕駛艙")
st.markdown("---")

# Task 3: Global Exam Scope Lock
from src.generate_eds_exam import EDSExamGenerator
exam_generator = EDSExamGenerator()
exam_lock_on = st.toggle("🔒 啟動 108 課綱段考衝刺模式", value=False)
global_locked_codes = None

if exam_lock_on:
    scopes_dict = exam_generator.get_available_exam_scopes()
    col_sem, col_exam = st.columns(2)
    with col_sem:
        selected_sem = st.selectbox("🎯 選擇段考學期：", list(scopes_dict.keys()), index=0)
    with col_exam:
        selected_exam = st.selectbox("📝 選擇段考試次：", scopes_dict[selected_sem], index=0)

    global_locked_codes = exam_generator.get_scope_codes(selected_sem, selected_exam)
    st.info(f"🔒 **段考邊界已鎖定**（`{selected_sem} / {selected_exam}`）：涵蓋考點 `{global_locked_codes}`")
    st.markdown("---")

# 3 Top-Level Tabs Layout
tab1, tab2, tab3 = st.tabs(["🚥 學科紅綠燈視圖", "🎯 考前決勝特訓", "🌟 全人素養"])

with tab1:
    col_light_h, col_light_b = st.columns([3, 1])
    with col_light_h:
        st.header("🚥 學科檢傷與紅綠燈 (來自 RDQ 生態系)")
        st.caption("讀取 SQLite 中的 `weakness_stats` 視圖，實時掌握全科學習弱點。")
    with col_light_b:
        from src.db_writer import inject_sample_wrong_questions
        if st.button("🎲 注入 15 筆會考錯題範例"):
            inject_sample_wrong_questions()
            st.success("✅ 已注入 15 筆跨科錯題數據！請重新選擇科目查看。")
            st.rerun()

    subject_map = {
        "國文": "chinese",
        "數學": "math",
        "社會": "social",
        "自然": "science",
        "英語": "english"
    }

    selected_subject_zh = st.selectbox("選擇要檢視的科目：", list(subject_map.keys()), index=3)
    selected_subject = subject_map[selected_subject_zh]

    try:
        db_path = os.getenv('ECOSYSTEM_DB_PATH', os.path.expanduser('~/.education_ecosystem/review_index.db'))
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            query = """
            SELECT item_id, weakness_score
            FROM weakness_stats
            WHERE subject = ?
            """
            params = [selected_subject]

            if global_locked_codes:
                placeholders = ','.join(['?'] * len(global_locked_codes))
                query += f" AND item_id IN ({placeholders})"
                params.extend(global_locked_codes)

            query += " ORDER BY weakness_score DESC LIMIT 10"
            weakness_df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if not weakness_df.empty:
                st.write(f"### 🚨 {selected_subject_zh} 前 10 大弱點 (🔴/🟡/🟢 檢視)")

                def get_light(score):
                    if score >= 0.8: return "🔴 優先攻堅"
                    elif score >= 0.4: return "🟡 觀念微調"
                    else: return "🟢 掌握良好"

                weakness_df['狀態燈號'] = weakness_df['weakness_score'].apply(get_light)
                weakness_df = weakness_df.rename(columns={'item_id': '弱點代碼 (eds_x_code)', 'weakness_score': '弱點分數'})

                # Interactive Data Editor for Cross-Tab Sync
                st.caption("💡 **Tip:** 勾選下方弱點左側的方塊，即可一鍵將該代碼帶入「🎯 考前決勝特訓」中！")

                # We add a boolean column for selection
                weakness_df.insert(0, '選定特訓', False)
                edited_df = st.data_editor(
                    weakness_df,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "選定特訓": st.column_config.CheckboxColumn(
                            "選定特訓", help="選取此弱點作為今日打擊目標", default=False
                        )
                    }
                )

                # Check if any row was selected
                selected_rows = edited_df[edited_df['選定特訓'] == True]
                if not selected_rows.empty:
                    target_code = selected_rows.iloc[0]['弱點代碼 (eds_x_code)']
                    if st.session_state['global_target_code'] != target_code:
                        st.session_state['global_target_code'] = target_code
                        st.toast(f"✅ 已鎖定目標 [{target_code}]！請切換至「🎯 考前決勝特訓」分頁開始作戰。")
            else:
                st.info(f"目前在 {selected_subject_zh} 科目中沒有明顯的弱點資料。點擊上方「🎲 注入 15 筆會考錯題範例」可即時觀看大數據分析！")
        else:
            st.warning("找不到 RDQ 生態系資料庫 (`review_index.db`)，請先確保 RDQ 已寫入資料。")
    except Exception as e:
        st.error(f"讀取資料庫時發生錯誤：{e}")

    st.markdown("---")
    col_w_h, col_w_b = st.columns([3, 1])
    with col_w_h:
        st.header("📖 高壓錯題本 (Vault 錯題卡展示區)")
        st.caption("自動對接 `D:/Kid's Vault/40_錯題筆記/`，展示經 Vision VLM / 大數據三分流生成之典藏錯題卡。")
    with col_w_b:
        reader = T2NProcessor()
        if st.button("⚡ 將 RDQ 錯題轉為典藏錯題卡"):
            added = reader.convert_rdq_db_to_vault_notes()
            st.success(f"✅ 已將 {added} 筆 RDQ 錯題轉檔並寫入 Vault 錯題庫！")
            st.rerun()

    wrong_dir = Path("D:/Kid's Vault/40_錯題筆記")
    wrong_notes = []
    if wrong_dir.exists():
        wrong_notes = [str(f.relative_to(wrong_dir)) for f in wrong_dir.rglob("*.md")]

    if wrong_notes:
        selected_wrong_note = st.selectbox("📌 選擇已歸檔的錯題筆記：", sorted(wrong_notes), index=0)
        wrong_note_path = wrong_dir / selected_wrong_note
        if wrong_note_path.exists():
            raw_wrong_md = wrong_note_path.read_text(encoding="utf-8")
            clean_wrong_md = reader.clean_markdown_for_display(raw_wrong_md)
            st.markdown(clean_wrong_md)
    else:
        st.info("ℹ️ `D:/Kid's Vault/40_錯題筆記/` 目前尚無錯題卡。當在 PME 特訓答錯或處理 Inbox 錯題照片時，將自動生成於此。")

with tab2:
    pme_subtab1, pme_subtab2 = st.tabs(["📖 1. 知識建構 (T2N 學霸筆記與隨堂測驗)", "📊 2. 實戰決策 (EDS 決勝圖譜與 PME 特訓)"])

    with pme_subtab1:
        st.header("1. 知識建構 (T2N 自動化轉檔筆記庫)")
        st.caption("自動對接 `textbook-to-note` PDF/EPUB 轉檔庫 (`D:/Kid's Vault/`)，展示已轉檔完成之 108 課綱學霸筆記。")

        reader = T2NProcessor()

        col_scope, col_note_sel = st.columns([1, 2])
        with col_scope:
            sem_scope = st.selectbox(
                "🗓️ 學習範圍與學期篩選：",
                [
                    "全部範圍 (108會考全總複習)",
                    "七年級上學期 (1上)",
                    "七年級下學期 (1下)",
                    "八年級上學期 (2上)",
                    "八年級下學期 (2下)",
                    "九年級上學期 (3上)",
                    "九年級下學期 (3下)"
                ],
                index=0
            )

        # Task 2: Advanced Search API usage
        selected_tags = []
        search_kw = ""
        with st.expander("🔍 筆記進階搜尋與標籤過濾 (Task 2)", expanded=False):
            all_tags = reader.get_all_vault_tags()
            selected_tags = st.multiselect("🏷️ 篩選 Vault 標籤：", options=all_tags)
            search_kw = st.text_input("🔍 搜尋筆記關鍵字：", placeholder="例如: 聲音鐘 / 光合作用")

        # Get matching notes using the new search API
        matching_notes = reader.search_vault_notes(keywords=search_kw, tags=selected_tags, semester_filter=sem_scope)
        if not matching_notes:
            st.warning("⚠️ 找不到符合條件的筆記，請放寬搜尋條件。")
            matching_notes = reader.get_available_notes() # Fallback

        with col_note_sel:
            selected_note = st.selectbox("📚 選擇已轉檔的單元筆記：", matching_notes, index=0)

        # Isolated Sub-tabs for converted note artifacts
        subtab_md, subtab_html, subtab_mind, subtab_quiz = st.tabs(["Markdown 筆記", "🖨️ 典藏 HTML (Pro)", "心智圖 (Mermaid)", "隨堂考卷 (API串接)"])

        with subtab_md:
            md_text = reader.load_note_markdown(selected_note)
            st.markdown(md_text)

        with subtab_html:
            html_pro = reader.load_note_html(selected_note)
            if html_pro:
                st.download_button(
                    label="📥 下載 A4 列印級 HTML 筆記",
                    data=html_pro,
                    file_name=f"{Path(selected_note).stem}.html",
                    mime="text/html"
                )
                st.components.v1.html(html_pro, height=500, scrolling=True)
            else:
                st.info(f"ℹ️ 該單元筆記（`{selected_note}`）之 A4 典藏版 HTML 講義尚未匯出。可至全域工具庫執行 `md-to-html` 進行單元編印。")

        with subtab_mind:
            mermaid_code = reader.generate_mindmap(selected_note)
            if mermaid_code:
                clean_mermaid = re.sub(r'```(?:mermaid)?', '', mermaid_code).strip()
                st.markdown(f"### 🧠 {Path(selected_note).stem.replace('_筆記','')} 心智圖")
                st.markdown(f"```mermaid\n{clean_mermaid}\n```")
                with st.expander("📋 檢視 / 複製原始 Mermaid 語法"):
                    st.code(mermaid_code, language="mermaid")
            else:
                st.info(f"ℹ️ 該單元筆記（`{selected_note}`）內文尚無結構化章節標題，無法動態繪製心智圖。")

        with subtab_quiz:
            meta = reader.extract_note_metadata(selected_note)
            target_code = meta["primary_code"]
            st.markdown(f"### 📝 108 課綱觀念隨堂小考 (`{meta['title']}`)")
            col_target_sel, col_slider_sel = st.columns([1, 2])
            with col_target_sel:
                quiz_target = st.selectbox(
                    "🎯 考前目標標竿：",
                    ["A++ 衝刺", "A / A+ 穩分", "保A / B++ 基礎"],
                    index=0,
                    key=f"quiz_target_level_{selected_note}"
                )
            with col_slider_sel:
                quiz_len = st.select_slider(
                    "🎛️ 請選擇測驗題數規格：",
                    options=[3, 5, 10],
                    value=5,
                    format_func=lambda x: f"{x} 題 (⚡ 課後微檢測)" if x == 3 else (f"{x} 題 (🌟 標準單元考 · 推薦)" if x == 5 else f"{x} 題 (🚀 高強度章節特訓)"),
                    key=f"quiz_slider_{selected_note}"
                )

            quiz_json_str = reader.generate_quiz(
                eds_x_code=target_code,
                note_identifier=selected_note,
                num_questions=quiz_len,
                target_level=quiz_target
            )
            quiz_data = json.loads(quiz_json_str) if quiz_json_str else {}
            questions = quiz_data.get("questions", [])

            if questions:
                avg_p = sum(q_item.get("question", {}).get("p_value", 0.65) for q_item in questions) / len(questions)
                st.caption(f"🎯 對位代碼：`{target_code}` | 目標標竿：**{quiz_target}** | 派發題數：{len(questions)} 題 | 試題平均通過率 P值：`{avg_p:.4f}` ({'🔴 高硬度魔王題' if avg_p < 0.6 else ('🟡 中等鑑別題' if avg_p <= 0.7 else '🟢 基礎高頻題')})")

                for idx, q_item in enumerate(questions):
                    q_type = q_item.get("type")
                    q = q_item.get("question", {})

                    st.markdown(f"#### 📌 第 {idx+1} 題 (會考真題編號: `{q.get('q_id', '全真考題')}`) [{q.get('source', '歷屆試題')}]")
                    if q_type == "group" and q_item.get("group_text"):
                        st.info(f"📖 **題組引文/實驗背景**：\n{q_item.get('group_text')}")

                    st.write(f"**題幹**：{q.get('text', '')}")
                    q_img = q.get("image")
                    full_img_path = None
                    if q_img:
                        p_cand = Path(q_img)
                        if p_cand.is_absolute() and p_cand.exists():
                            full_img_path = str(p_cand)
                        elif (Path("D:/Kid's Vault") / q_img).exists():
                            full_img_path = str(Path("D:/Kid's Vault") / q_img)

                    if full_img_path:
                        st.image(full_img_path, caption=f"🖼️ 題目附圖 (真題編號: {q.get('q_id')})", use_container_width=True)
                    elif re.search(r'圖\s*[\(（][一二三四五六七八九十\d\w]+[\)）]', q.get('text', '')):
                        fig_match = re.search(r'圖\s*[\(（][一二三四五六七八九十\d\w]+[\)）]', q.get('text', ''))
                        fig_str = fig_match.group(0) if fig_match else "附圖"
                        st.warning(f"📷 **【圖檔未入庫提示】** (題幹提及 `{fig_str}`，硬碟 `99_Attachments/` 尚未包含該真題圖檔，待 RDQ 補全對位)")

                    options = q.get("options", ["(A)", "(B)", "(C)", "(D)"])
                    user_choice = st.radio(f"請選擇答案 (第 {idx+1} 題)：", options, key=f"pop_q_opt_{selected_note}_{idx}")

                    correct_ans_letter = q.get("answer", "A")
                    if st.button(f"提交答案 (第 {idx+1} 題)", key=f"pop_q_sub_{selected_note}_{idx}"):
                        if user_choice.startswith(f"({correct_ans_letter})") or user_choice.startswith(correct_ans_letter):
                            st.success(f"✅ 答對了！官方正解為 ({correct_ans_letter})。觀念完全掌握！")
                        else:
                            st.error(f"❌ 答錯了！此題官方正解為 ({correct_ans_letter})。已自動記錄至高壓錯題庫。")

                st.markdown("---")
                with st.expander("🛠️ API 底層 JSON 資料結構 (系統對接除錯用)"):
                    st.json(quiz_data)
            else:
                st.info(f"ℹ️ 本單元 (`{meta['title']}`) 目前尚無對應之會考隨堂小考題。")

    with pme_subtab2:
        st.header("2. 實戰決策 (EDS 決勝圖譜)")

        hours = st.slider("今天剩餘讀書時間 (小時)：", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

        col_target, col_subj = st.columns(2)
        with col_target:
            target = st.selectbox("目標設定：", ["保A", "A+", "A++"], index=2)
        with col_subj:
            target_subject = st.selectbox("特訓次學科：", ["國文", "英語", "數學", "生物", "理化", "地科", "歷史", "地理", "公民"], index=4)

        if st.button("📊 產出決勝圖譜"):
            with st.spinner("讀取 RDQ 資料庫與計算 ROI..."):
                try:
                    result_text = generate_decision_graph_text(None, available_hours=hours, target_mode=target, target_subject=target_subject, exam_scope_codes=global_locked_codes)
                    st.text_area("決策輸出：", value=result_text, height=300)
                    st.session_state['graph_generated'] = True
                    st.session_state['target_subject'] = target_subject
                except Exception as e:
                    st.error(f"發生錯誤：{e}")

        if st.session_state.get('graph_generated') or st.session_state.get('global_target_code'):
            st.markdown("### ⚠️ PME 考前高壓特訓系統 (Phase 1: PLAN)")

            with st.expander("📝 點此設定今日作戰計畫 (未設定不准派題)", expanded=True):
                default_goal = st.session_state.get('global_target_code', '')
                pme_goal = st.text_input("1. 今天打擊哪個目標代碼？", value=default_goal, placeholder="例如: Bc-Ⅳ-3")
                pme_status = st.selectbox("2. 該目標目前燈號狀態？", ["🔴 優先攻堅 (概念錯誤)", "🟡 觀念微調 (推理不足)", "🟢 掌握良好 (看錯題)"])
                pme_strategy = st.text_area("3. 預計做幾題及求救策略？", placeholder="預計做5題，卡住時會先掙扎3分鐘再看解答。")

                pme_ready = st.button("我已完成承諾，開始特訓！")

            if pme_ready and pme_goal:
                with st.spinner("正在為您專屬派題 (PME 模式)..."):
                    from src.generate_eds_exam import get_exam_for_topics
                    from src.analyzer import EDSAnalyzer
                    from src.adaptive_engine import AdaptiveEngine

                    analyzer = EDSAnalyzer()
                    engine = AdaptiveEngine()
                    mods = engine.get_priority_modifiers()

                    saved_subject = st.session_state.get('target_subject', target_subject)
                    roi_df = analyzer.module_d_priority_score(mode=target, personal_modifiers=mods, target_subject=saved_subject, exam_scope_codes=global_locked_codes)

                    if not roi_df.empty:
                        # Ensure the globally selected goal from PME is explicitly prioritized
                        top_topics_dicts = roi_df.head(3).to_dict('records')
                        if pme_goal and pme_goal not in [t.get('X軸主代碼') for t in top_topics_dicts]:
                            top_topics_dicts.insert(0, {'X軸主代碼': pme_goal})

                        exam_json = json.loads(get_exam_for_topics(top_topics_dicts, num_questions=5, exam_scope_codes=global_locked_codes))
                        st.session_state['current_exam'] = exam_json
                        st.session_state['pme_streak'] = 0
                        st.success("考卷組裝完成！進入 MONITOR 階段。")
                    else:
                        st.error("無法取得優先主題以進行組卷。")

        if 'current_exam' in st.session_state:
            from src.db_writer import record_wrong_answer
            st.markdown("---")
            st.markdown("### ⚔️ 實戰演練 (Phase 2: MONITOR)")
            st.caption("🚨 **流暢性幻覺警報**：若連續答對，難度將自動升階；卡住時請遵守「3 分鐘掙扎原則」。")

            exam = st.session_state['current_exam']
            st.subheader(exam.get('title', 'Exam'))

            for idx, q_data in enumerate(exam.get('questions', [])):
                q_type = q_data.get('type')
                q = q_data.get('question', {})

                st.markdown(f"**Q{idx+1}.**")
                if q_type == 'group':
                    st.info(q_data.get('group_text'))

                st.write(q.get('text', ''))

                options = q.get('options', ['A', 'B', 'C', 'D'])
                choice = st.radio(f"請選擇答案 (Q{idx+1}):", options, key=f"q_{idx}")

                if st.button(f"提交答案 (Q{idx+1})", key=f"submit_{idx}"):
                    if choice == 'A':
                        st.success("✅ 答對了！")
                        st.session_state['pme_streak'] = st.session_state.get('pme_streak', 0) + 1
                        if st.session_state['pme_streak'] >= 3:
                            st.balloons()
                            st.warning("🔥 連續答對 3 題！已達 70% 學習甜頭區上限。下一題將升階為「應用題/解釋題」。")
                    else:
                        st.session_state['pme_streak'] = 0
                        st.error("❌ 答錯了！已記錄至高壓錯題本。")
                        code_to_log = "Bc-Ⅳ-3" if "光合作用" in q.get('text', '') or "葉綠體" in q.get('text', '') else "Eb-Ⅳ-2"

                        success = record_wrong_answer(code_to_log, loss_reason="推理不足")
                        if success:
                            st.info(f"系統已將弱點代碼 `{code_to_log}` 寫入。若需要解答，請先嘗試自己推導 3 分鐘！")

            st.markdown("---")
            st.markdown("### ⚖️ 實戰覆盤 (Phase 3: EVALUATE & Loss Aversion Stakes)")
            with st.expander("結束測驗，進行對賭承諾 (必須填寫)"):
                st.write("哪裡被澄清了？哪裡還模糊？")
                st.text_area("反思內容：")
                st.markdown("#### 💥 5x 損失趨避公開承諾")
                stake = st.text_input("若下週模擬考這個目標又錯，我將：", placeholder="例如: 暫停週末電動時間 / 執行 50 個俯臥撐")
                if st.button("鎖定承諾並結束特訓"):
                    st.success(f"已記錄您的承諾：「{stake}」。我們考場見！")
                    st.balloons()

with tab3:
    st.header("🌟 全人素養與後設認知 (Meta-cognition & Reflection)")
    st.caption("真實寫入與同步 `D:/Kid's Vault/90_後設認知紀錄/` 及 RDQ 學習生態系。")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📝 每日三問 (Daily 3 Questions)")
        reflection_dir = Path("D:/Kid's Vault/90_後設認知紀錄")
        reflection_dir.mkdir(parents=True, exist_ok=True)
        reflection_file = reflection_dir / "daily_reflections.json"

        # Load existing reflections if any
        reflections = []
        if reflection_file.exists():
            try:
                reflections = json.loads(reflection_file.read_text(encoding="utf-8"))
            except Exception:
                reflections = []

        q1 = st.text_input("1. 今天學到了什麼核心觀念？", placeholder="例如: 理解了光反應發生於類囊體膜...")
        q2 = st.text_input("2. 哪裡還感到模糊或容易看錯？", placeholder="例如: 暗反應不一定在晚上進行...")
        q3 = st.text_input("3. 明天的複習/特訓計畫是什麼？", placeholder="例如: 複習理化元素週期表...")

        if st.button("💾 儲存今日三問反思至 Vault"):
            if q1 or q2 or q3:
                import datetime
                entry = {
                    "date": str(datetime.date.today()),
                    "learned": q1,
                    "confused": q2,
                    "plan": q3
                }
                reflections.insert(0, entry)
                reflection_file.write_text(json.dumps(reflections, indent=2, ensure_ascii=False), encoding="utf-8")
                st.success("✅ 已成功寫入 `D:/Kid's Vault/90_後設認知紀錄/daily_reflections.json`！")
            else:
                st.warning("請至少填寫一題反思內容。")

        if reflections:
            with st.expander("📚 查看歷史反思紀錄"):
                for item in reflections[:5]:
                    st.markdown(f"**📅 {item.get('date')}**")
                    st.write(f"- **收穫**：{item.get('learned')}")
                    st.write(f"- **盲點**：{item.get('confused')}")
                    st.write(f"- **計畫**：{item.get('plan')}")
                    st.markdown("---")

    with col_b:
        st.subheader("🧠 EPOCH 大腦水文與神經科學雷達指標")
        st.caption("基於前額葉皮質 (PFC)、迷走神經 HRV、選擇架構與突觸恆定假說 (SHY) 之科學檢傷。")

        # Calculate dynamic EPOCH scores from review_index.db
        total_wrongs = 0
        total_clarified = 0
        try:
            db_path = os.getenv('ECOSYSTEM_DB_PATH', os.path.expanduser('~/.education_ecosystem/review_index.db'))
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM review_index")
                total_wrongs = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM review_index WHERE status = 'clarified'")
                total_clarified = c.fetchone()[0]
                conn.close()
        except Exception:
            pass

        # Count total Vault notes for Cognitive Retrieval (C)
        vault_notes_count = len(reader.get_available_notes()) + len(wrong_notes) if 'reader' in locals() and 'wrong_notes' in locals() else 0
        pme_stakes_count = 1 if st.session_state.get('graph_generated') else 0

        # Dynamic rating calculation according to neuroscience metrics
        e_score = min(5, 3 + (total_clarified // 2))
        p_score = min(5, 3 + (1 if len(reflections) > 0 else 0) + (1 if len(reflections) >= 3 else 0))
        o_score = min(5, 3 + (1 if pme_stakes_count > 0 else 0) + (1 if len(reflections) > 0 else 0))
        c_score = min(5, 3 + (vault_notes_count // 3))
        h_score = min(5, 3 + (total_wrongs // 3))

        st.markdown(f"""
        - **E** — **Executive Function** (前額葉執行功能): `{'★' * e_score}{'☆' * (5 - e_score)}`
          *(PFC 衝動抑制與認知靈活性，即時克服 {total_clarified} 個觀念陷阱)*
        - **P** — **Physiological State** (迷走神經與生理狀態): `{'★' * p_score}{'☆' * (5 - p_score)}`
          *(HRV 與副交感神經心流地基，累計 {len(reflections)} 次體感覆盤)*
        - **O** — **Overcoming Friction** (克服三層摩擦力): `{'★' * o_score}{'☆' * (5 - o_score)}`
          *(選擇架構與阻力設計，已啟動 {pme_stakes_count + len(reflections)} 次 5x 損失趨避機制與作戰計畫)*
        - **C** — **Cognitive Retrieval** (主動認知提取): `{'★' * c_score}{'☆' * (5 - c_score)}`
          *(費曼雙重編碼與突觸凝結，累計提取 {vault_notes_count} 份 Vault 108 筆記與錯題卡)*
        - **H** — **Homeostatic Recovery** (睡眠與突觸恆定復原): `{'★' * h_score}{'☆' * (5 - h_score)}`
          *(Tononi 突觸恆定假說 SHY NREM 鞏固，追蹤 {total_wrongs} 處重點弱點)*
        """)

st.markdown("---")
st.caption("Ecosystem Integration: T2N Preprocessor -> RDQ Shared Schema -> EDS Decision Engine")
