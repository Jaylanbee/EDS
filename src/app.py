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
            with st.spinner("AI 處理中 (模擬)..."):
                processor = T2NProcessor()
                json_result = processor.simulate_llm_parsing(text_input)

                st.success("解析完成！")

                # Tabs for different outputs
                tab1, tab2, tab3 = st.tabs(["Markdown 筆記", "心智圖 (Mermaid)", "課後測驗"])

                with tab1:
                    md_text = processor.render_markdown(json_result)
                    st.markdown(md_text)

                with tab2:
                    mermaid_code = processor.generate_mindmap(json_result)
                    st.code(mermaid_code, language="mermaid")
                    st.markdown("*(可複製至 [Mermaid Live Editor](https://mermaid.live/) 查看)*")

                with tab3:
                    quiz_text = processor.generate_quiz(json_result)
                    st.markdown(quiz_text)
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

    if st.button("🎯 產出決勝圖譜"):
        with st.spinner("讀取 RDQ 資料庫與計算 ROI..."):
            try:
                # 這裡需要 generate_graph_text, 稍後修改 generate_graph.py
                result_text = generate_decision_graph_text(default_csv, available_hours=hours, target_mode=target)
                st.text_area("決策輸出：", value=result_text, height=400)
            except Exception as e:
                st.error(f"發生錯誤：{e}")

st.markdown("---")
st.caption("Ecosystem Integration: T2N Preprocessor -> RDQ Shared Schema -> EDS Decision Engine")
