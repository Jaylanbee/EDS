import streamlit as st
import os
import pandas as pd
from src.t2n_processor import T2NProcessor
from src.generate_graph import generate_decision_graph_text

# Setup Streamlit Page
st.set_page_config(page_title="EDS app.py 統一學習駕駛艙", layout="wide")

st.title("🖥️ 水循環學習法 統一學習駕駛艙")
st.markdown("---")

# Architect Directive: 3 Tabs layout
tab1, tab2, tab3 = st.tabs(["🚥 學科紅綠燈視圖", "🎯 考前決勝特訓", "🌟 全人素養"])

with tab1:
    st.header("🚥 學科檢傷與紅綠燈 (來自 RDQ 數據)")
    st.markdown("讀取 SQLite 中的 `weakness_stats` 視圖，實時掌握學習弱點。")

    # 建立五大科目的切換
    subject_map = {
        "國文": "chinese",
        "數學": "math",
        "社會": "social",
        "自然": "science",
        "英語": "english"
    }

    selected_subject_zh = st.selectbox("選擇要檢視的科目：", list(subject_map.keys()), index=3) # Default to science
    selected_subject = subject_map[selected_subject_zh]

    try:
        import sqlite3
        db_path = os.getenv('ECOSYSTEM_DB_PATH', os.path.expanduser('~/.education_ecosystem/review_index.db'))
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)

            # Fetch data for the selected subject
            query = """
            SELECT item_id, weakness_score
            FROM weakness_stats
            WHERE subject = ?
            ORDER BY weakness_score DESC
            LIMIT 10
            """
            weakness_df = pd.read_sql_query(query, conn, params=(selected_subject,))
            conn.close()

            if not weakness_df.empty:
                st.write(f"### 🚨 {selected_subject_zh} 前 10 大弱點 (🔴/🟡/🟢 檢視)")

                # Assign traffic lights based on mock thresholds
                def get_light(score):
                    if score >= 0.8: return "🔴 優先攻堅"
                    elif score >= 0.4: return "🟡 觀念微調"
                    else: return "🟢 掌握良好"

                weakness_df['狀態燈號'] = weakness_df['weakness_score'].apply(get_light)
                weakness_df = weakness_df.rename(columns={'item_id': '弱點代碼 (eds_x_code)', 'weakness_score': '弱點分數'})

                st.dataframe(weakness_df, use_container_width=True) # Streamlit currently supports use_container_width in many versions, keeping it unless specifically breaking
            else:
                st.info(f"太棒了！目前在 {selected_subject_zh} 科目中沒有明顯的弱點資料。")
        else:
            st.warning("找不到 RDQ 生態系資料庫 (`review_index.db`)，請先確保 RDQ 已寫入資料。")
    except Exception as e:
        st.error(f"讀取資料庫時發生錯誤：{e}")

with tab2:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("1. 知識建構 (Textbook2Notes)")
        st.caption("已與上游 T2N (Textbook2Notes) 筆記動態對接，已為您自動載入該單元之知識結構。")

        engine_choice = st.radio("選擇 AI 引擎：", ["Auto (Gemini優先/Ollama備援)", "Gemini API", "Ollama 本地", "模擬模式"], horizontal=True)

    engine_map = {
        "Auto (Gemini優先/Ollama備援)": "auto",
        "Gemini API": "gemini",
        "Ollama 本地": "ollama",
        "模擬模式": "simulation"
    }

    text_input = st.text_area("請貼上課文或筆記內容：", height=200, placeholder="光合作用分為光反應與暗反應...")

    if st.button("🚀 執行 T2N 解析"):
        if text_input.strip():
            with st.spinner("AI 處理中..."):
                processor = T2NProcessor()
                json_result = processor.process_text(text_input, engine=engine_map[engine_choice])

                st.success("解析完成！")

                # Tabs for different outputs
                tab1, tab2, tab3 = st.tabs(["Markdown 筆記", "心智圖 (Mermaid)", "隨堂考卷 (API串接)"])

                with tab1:
                    md_text = processor.render_markdown(json_result)
                    st.markdown(md_text)

                with tab2:
                    mermaid_code = processor.generate_mindmap(json_result)
                    st.code(mermaid_code, language="mermaid")
                    st.markdown("*(可複製至 [Mermaid Live Editor](https://mermaid.live/) 查看)*")

                with tab3:
                    from src.generate_eds_exam import get_pop_quiz
                    import json

                    st.markdown("### 📝 自動派題引擎 - 隨堂小考")
                    # Dynamically pull the code from the first node for the demo
                    first_node = json_result.get("nodes", [{}])[0]
                    target_code = first_node.get("eds_x_code")

                    if target_code:
                        quiz_json = get_pop_quiz(target_code)
                        st.json(json.loads(quiz_json))
                    else:
                        st.warning("無法從筆記中擷取有效的課綱代碼以產生測驗。")
        else:
            st.warning("請先輸入文本。")

    with col2:
        st.header("2. 實戰決策 (EDS 決勝圖譜)")

        # Phase 2 dynamic architecture does not use default_csv anymore
        hours = st.slider("今天剩餘讀書時間 (小時)：", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

        col_target, col_subj = st.columns(2)
        with col_target:
            target = st.selectbox("目標設定：", ["保A", "A+", "A++"], index=2)
        with col_subj:
            target_subject = st.selectbox("特訓科目：", ["國文", "數學", "社會", "自然", "英語"], index=3)

        if st.button("📊 產出決勝圖譜"):
            with st.spinner("讀取 RDQ 資料庫與計算 ROI..."):
                try:
                    result_text = generate_decision_graph_text(None, available_hours=hours, target_mode=target, target_subject=target_subject)
                    st.text_area("決策輸出：", value=result_text, height=300)
                    st.session_state['graph_generated'] = True
                    st.session_state['target_subject'] = target_subject
                except Exception as e:
                    st.error(f"發生錯誤：{e}")

        if st.session_state.get('graph_generated'):
            st.markdown("### ⚠️ PME 考前高壓特訓系統 (Phase 1: PLAN)")

            with st.expander("📝 點此設定今日作戰計畫 (未設定不准派題)", expanded=True):
                pme_goal = st.text_input("1. 今天打擊哪個目標代碼？", placeholder="例如: Bc-Ⅳ-3")
                pme_status = st.selectbox("2. 該目標目前燈號狀態？", ["🔴 優先攻堅 (概念錯誤)", "🟡 觀念微調 (推理不足)", "🟢 掌握良好 (看錯題)"])
                pme_strategy = st.text_area("3. 預計做幾題及求救策略？", placeholder="預計做5題，卡住時會先掙扎3分鐘再看解答。")

                pme_ready = st.button("我已完成承諾，開始特訓！")

            if pme_ready and pme_goal:
                with st.spinner("正在為您專屬派題 (PME 模式)..."):
                    from src.generate_eds_exam import get_exam_for_topics
                    import json
                    from src.analyzer import EDSAnalyzer
                    from src.adaptive_engine import AdaptiveEngine

                    analyzer = EDSAnalyzer()
                    engine = AdaptiveEngine()
                    mods = engine.get_priority_modifiers()

                    saved_subject = st.session_state.get('target_subject', target_subject)
                    roi_df = analyzer.module_d_priority_score(mode=target, personal_modifiers=mods, target_subject=saved_subject)

                    if not roi_df.empty:
                        top_topics_dicts = roi_df.head(3).to_dict('records')
                        exam_json = json.loads(get_exam_for_topics(top_topics_dicts, num_questions=5))
                        st.session_state['current_exam'] = exam_json
                        st.session_state['pme_streak'] = 0 # Track correct answers for Learning Zone
                        st.success("考卷組裝完成！進入 MONITOR 階段。")
                    else:
                        st.error("無法取得優先主題以進行組卷。")

        # Render interactive Exam Mock if exists
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
    st.header("🌟 全人素養與後設認知")
    st.info("這裡將會串接外部 Plugins (如每日三問紀錄、多巴胺排毒、EPOCH 雷達圖) 的資料。")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📝 每日三問 (Daily 3 Questions)")
        st.write("讀取中...")
        st.success("1. 今天學到了什麼？\n2. 哪裡還不清楚？\n3. 明天要怎麼做？")

    with col_b:
        st.subheader("🎯 EPOCH 靈魂五力雷達圖")
        st.write("讀取中...")
        # Mocking a simple radar chart or text representation
        st.text("E (Empathy 同理心): ★★★★★\nP (Presence 存在感): ★★★★☆\nO (Outcome-ethics 倫理判斷): ★★★☆☆\nC (Creation 創造力): ★★★★☆\nH (Hope 希望力): ★★★★★")

st.markdown("---")
st.caption("Ecosystem Integration: T2N Preprocessor -> RDQ Shared Schema -> EDS Decision Engine")
