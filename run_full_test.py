import os
from src.analyzer import EDSAnalyzer
from src.generate_graph import generate_decision_graph

def run_tests():
    print("=== 開始測試 Phase 2 動態架構 ===")

    analyzer = EDSAnalyzer()

    print("\n--- Module B-1: 陷阱題分析 (Mocked) ---")
    df_b1 = analyzer.module_b_trap_analysis()
    if not df_b1.empty:
        print(df_b1[['X軸主代碼', '失分原因', 'avg_difficulty']].head().to_string())
    else:
        print("查無資料。")

    print("\n--- Module D: Priority Score & ROI (Dynamic) ---")
    df_d = analyzer.module_d_priority_score()
    if not df_d.empty:
        print(df_d[['X軸主代碼', 'Base_Priority', 'Priority_Score', '預估補強時間', '效益_ROI', '評等']].head().to_string())
    else:
        print("查無資料。")

    print("\n--- 第五章: 決勝圖譜輸出 (Application Layer) ---")
    generate_decision_graph(output_path='outputs/test_daily_suggestion.txt', available_hours=2.5)

    # 清理
    if os.path.exists('outputs/test_daily_suggestion.txt'):
        os.remove('outputs/test_daily_suggestion.txt')

if __name__ == "__main__":
    run_tests()
