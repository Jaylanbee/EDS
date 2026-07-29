import pandas as pd
import os
from src.analyzer import EDSAnalyzer
from src.generate_graph import generate_decision_graph

def run_tests():
    print("=== 準備測試資料 ===")
    test_data = """年份,題號,科目,X軸主代碼,X軸次代碼,Y軸代碼,題型,通過率,失分原因,可救程度,預估補強時間_小時
111,1,理化,Ka-IV-6,Ka-IV-7,pa-IV-1,計算題,35,計算錯誤,中,3
111,2,生物,Bc-IV-3,Bc-IV-4,tr-IV-1,圖表判讀,25,推理不足,高,1.5
112,5,理化,Ka-IV-6,,pa-IV-2,圖表判讀,45,概念錯誤,低,5
112,6,地科,Eb-IV-2,,po-IV-1,實驗設計,75,概念錯誤,高,1
113,10,地科,Eb-IV-2,,po-IV-1,實驗設計,60,看錯題,高,1
113,15,生物,Ga-IV-3,Ga-IV-5,an-IV-1,概念辨析,80,概念錯誤,高,2
114,20,理化,Ka-IV-6,Ka-IV-7,pa-IV-1,計算題,30,計算錯誤,中,3
115,25,生物,Bc-IV-3,,tr-IV-1,圖表判讀,20,推理不足,高,1.5
"""
    os.makedirs('exam-data', exist_ok=True)
    with open('exam-data/test_dummy_data.csv', 'w', encoding='utf-8') as f:
        f.write(test_data)

    print("資料建立完成。開始測試各模組...")
    analyzer = EDSAnalyzer('exam-data/test_dummy_data.csv')

    print("\n--- Module A-1: 高頻分析 ---")
    df_a1 = analyzer.module_a_high_frequency()
    print(df_a1.to_string())

    print("\n--- Module A-2: 命題穩定度分析 ---")
    df_a2 = analyzer.module_a_stability()
    print(df_a2.to_string())

    print("\n--- Module B-1: 陷阱題分析 ---")
    df_b1 = analyzer.module_b_trap_analysis()
    print(df_b1[['年份', 'X軸主代碼', '通過率', '失分原因']].to_string())

    print("\n--- Module C-3: 題型攻略統計 ---")
    df_c3 = analyzer.module_c_type_stats()
    print(df_c3.to_string())

    print("\n--- Module D: Priority Score & ROI (目標: A++) ---")
    df_d = analyzer.module_d_priority_score(mode='A++')
    print(df_d[['X軸主代碼', 'Priority_Score', '預估補強時間', '效益_ROI', '評等']].to_string())

    print("\n--- 第五章: 決勝圖譜輸出 (Application Layer) ---")
    generate_decision_graph('exam-data/test_dummy_data.csv', 'outputs/test_daily_suggestion.txt', available_hours=2.5, target_mode='A++')

    # 清理
    os.remove('exam-data/test_dummy_data.csv')
    os.remove('outputs/test_daily_suggestion.txt')

if __name__ == "__main__":
    run_tests()
