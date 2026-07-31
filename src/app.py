import streamlit as st
import os
import pandas as pd
from src.t2n_processor import T2NProcessor
from src.generate_graph import generate_decision_graph_text

# Setup Streamlit Page
st.set_page_config(page_title="EDS & T2N 生態系控制中心", layout="wide")

st.title("📚 五合一教育生態系 (T2N + EDS)")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.header("1. 知識建構 (Textbook2Notes)")
    text_input = st.text_area("請貼上課文或筆記內容：", height=200, placeholder="光合作用分為光反應與暗反應...")

    if st.button("🚀 執行 T2N 解析"):
        if text_input.strip():
            with st.spinner("AI 處理中..."):
                processor = T2NProcessor()
                # Try real LLM, falls back to simulation if Ollama isn't running
                json_result = processor.invoke_ollama_llm(text_input)

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

    # 檢查是否有預設的 Dataset
    default_csv = "exam-data/test_integration_data.csv"

    # 小控制面板
    hours = st.slider("今天剩餘讀書時間 (小時)：", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
    target = st.selectbox("目標設定：", ["保A", "A+", "A++"], index=2)

    # 建立一個暫時的假 CSV 供 UI 測試 (如果沒有的話)
    if not os.path.exists(default_csv):
        os.makedirs("exam-data", exist_ok=True)
        with open(default_csv, "w", encoding="utf-8") as f:
            f.write("年份,題號,科目,X軸主代碼,X軸次代碼,Y軸代碼,題型,通過率,失分原因,可救程度,預估補強時間_小時\n")
            f.write("111,2,生物,Bc-Ⅳ-3,Bc-Ⅳ-4,tr-Ⅳ-1,圖表判讀,25,推理不足,高,1.5\n")
            f.write("112,6,地科,Eb-Ⅳ-2,,po-Ⅳ-1,實驗設計,75,概念錯誤,高,1\n")

    if st.button("📊 產出決勝圖譜"):
        with st.spinner("讀取 RDQ 資料庫與計算 ROI..."):
            try:
                result_text = generate_decision_graph_text(default_csv, available_hours=hours, target_mode=target)
                st.text_area("決策輸出：", value=result_text, height=300)
                st.session_state['graph_generated'] = True
            except Exception as e:
                st.error(f"發生錯誤：{e}")

    if st.session_state.get('graph_generated'):
        if st.button("🎯 開始特訓 (API 組卷)"):
            with st.spinner("正在為您專屬派題..."):
                from src.generate_eds_exam import get_exam_for_topics
                import json
                from src.analyzer import EDSAnalyzer
                from src.adaptive_engine import AdaptiveEngine

                # Re-run analyzer briefly to get top topics (in reality, pass this from state)
                analyzer = EDSAnalyzer(default_csv)
                engine = AdaptiveEngine()
                mods = engine.get_priority_modifiers()
                roi_df = analyzer.module_d_priority_score(mode=target, personal_modifiers=mods)

                if not roi_df.empty:
                    # Take top 3 topics
                    top_topics_dicts = roi_df.head(3).to_dict('records')
                    exam_json = json.loads(get_exam_for_topics(top_topics_dicts, num_questions=5))
                    st.session_state['current_exam'] = exam_json
                    st.success("考卷組裝完成！")
                else:
                    st.error("無法取得優先主題以進行組卷。")

    # Render interactive Exam Mock if exists
    if 'current_exam' in st.session_state:
        from src.db_writer import record_wrong_answer
        st.markdown("### 📝 實戰演練 (Exam Mock)")
        exam = st.session_state['current_exam']
        st.subheader(exam.get('title', 'Exam'))

        for idx, q_data in enumerate(exam.get('questions', [])):
            q_type = q_data.get('type')
            q = q_data.get('question', {})

            st.markdown(f"**Q{idx+1}.**")
            if q_type == 'group':
                st.info(q_data.get('group_text'))

            st.write(q.get('text', ''))

            # Simple interactive radio buttons for mock
            options = q.get('options', ['A', 'B', 'C', 'D'])
            choice = st.radio(f"請選擇答案 (Q{idx+1}):", options, key=f"q_{idx}")

            # Button to submit answer
            if st.button(f"提交答案 (Q{idx+1})", key=f"submit_{idx}"):
                # Simulate grading (in a real app, check against correct answer)
                # For this demo, let's assume 'A' is correct, anything else triggers the write-back
                if choice == 'A':
                    st.success("✅ 答對了！")
                else:
                    st.error("❌ 答錯了！已記錄至錯題本。")
                    # Here we extract the eds_x_code.
                    # Assuming we map q_id back to code, or it's embedded in the question.
                    # Since our mock question generator didn't embed the code directly in the question obj,
                    # we'll simulate it for the demo.
                    code_to_log = "Bc-Ⅳ-3" if "光合作用" in q.get('text', '') or "葉綠體" in q.get('text', '') else "Eb-Ⅳ-2"

                    success = record_wrong_answer(code_to_log, loss_reason="概念錯誤")
                    if success:
                        st.info(f"系統已將弱點代碼 `{code_to_log}` 寫入 RDQ Shared DB。請重新產生圖譜查看優先級變化！")

st.markdown("---")
st.caption("Ecosystem Integration: T2N Preprocessor -> RDQ Shared Schema -> EDS Decision Engine")
